from datetime import datetime
from multiprocessing.dummy import connection
from multiprocessing.dummy import connection
from pathlib import Path

import pandas as pd

from extract import extract_data
from validate import validate_data, validation_passed
from transform import transform_data
from incremental import fetch_existing_customers, detect_changes
from prepare_tables import prepare_database_tables
from load import (
    get_connection,
    load_customers,
    load_credit_profiles,
    load_monthly_activity,
)


def create_audit_record(
    connection,
    source_file,
    start_time,
    source_count,
):
    cursor = connection.cursor()

    query = """
        INSERT INTO etl_batch_audit (
            source_file,
            start_time,
            source_record_count,
            status
        )
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            Path(source_file).name,
            start_time,
            source_count,
            "RUNNING",
        ),
    )

    batch_id = cursor.lastrowid

    cursor.close()

    return batch_id


def complete_audit_record(
    connection,
    batch_id,
    new_count,
    updated_count,
    unchanged_count,
    loaded_count,
):
    cursor = connection.cursor()

    query = """
        UPDATE etl_batch_audit
        SET
            end_time = %s,
            new_record_count = %s,
            updated_record_count = %s,
            unchanged_record_count = %s,
            loaded_record_count = %s,
            failed_record_count = 0,
            status = 'SUCCESS',
            error_message = NULL
        WHERE batch_id = %s
    """

    cursor.execute(
        query,
        (
            datetime.now(),
            new_count,
            updated_count,
            unchanged_count,
            loaded_count,
            batch_id,
        ),
    )

    cursor.close()


def fail_audit_record(
    connection,
    batch_id,
    error_message,
):
    cursor = connection.cursor()

    query = """
        UPDATE etl_batch_audit
        SET
            end_time = %s,
            status = 'FAILED',
            error_message = %s
        WHERE batch_id = %s
    """

    cursor.execute(
        query,
        (
            datetime.now(),
            str(error_message)[:5000],
            batch_id,
        ),
    )

    cursor.close()


def run_incremental_pipeline(file_path):

    start_time = datetime.now()

    # ========================================================
    # 1. EXTRACT
    # ========================================================

    raw_data = extract_data(file_path)

    # ========================================================
    # 2. VALIDATE
    # ========================================================

    validation_report = validate_data(raw_data)

    if not validation_passed(validation_report):
        raise ValueError(
            "Source dataset failed validation."
        )

    # ========================================================
    # 3. TRANSFORM
    # ========================================================

    transformed_data = transform_data(raw_data)

    # ========================================================
    # 4. FETCH EXISTING DATABASE STATE
    # ========================================================

    existing_data = fetch_existing_customers()

    # ========================================================
    # 5. CHANGE DETECTION
    # ========================================================

    (
        new_records,
        changed_records,
        unchanged_records,
    ) = detect_changes(
        transformed_data,
        existing_data,
    )

    source_count = len(transformed_data)
    new_count = len(new_records)
    updated_count = len(changed_records)
    unchanged_count = len(unchanged_records)

    # ========================================================
    # 6. RECONCILIATION
    # ========================================================

    classified_count = (
        new_count
        + updated_count
        + unchanged_count
    )

    if classified_count != source_count:
        raise RuntimeError(
            "Incremental classification reconciliation failed."
        )

    # ========================================================
# BUILD FULL INCREMENTAL DATASET
# ========================================================

# Change detection returns comparison-level records.
# For loading, we need the complete transformed rows,
# including monthly repayment, bill and payment columns.

    new_ids = set(
    new_records["customer_id"].tolist()
)

    changed_ids = set(
    changed_records["customer_id"].tolist()
)

    incremental_ids = new_ids | changed_ids

    incremental_data = transformed_data[
    transformed_data["customer_id"].isin(
        incremental_ids
    )
].copy()

    loaded_count = len(incremental_data)

   

    if loaded_count != new_count + updated_count:
        raise RuntimeError(
            "Incremental load reconciliation failed."
        )

    print("\n========== INCREMENTAL SUMMARY ==========")

    print("Source records   :", source_count)
    print("New records      :", new_count)
    print("Updated records  :", updated_count)
    print("Unchanged records:", unchanged_count)
    print("Records to load  :", loaded_count)

    # ========================================================
    # 7. OPEN TRANSACTION
    # ========================================================

    connection = get_connection()
    batch_id = None

    try:

        connection.start_transaction()

        # ----------------------------------------------------
        # Create audit record
        # ----------------------------------------------------

        batch_id = create_audit_record(
            connection,
            file_path,
            start_time,
            source_count,
        )

        print("\nETL batch ID:", batch_id)

        # ----------------------------------------------------
        # Only prepare/load NEW + CHANGED records
        # ----------------------------------------------------

        if not incremental_data.empty:

            (
                customers_df,
                credit_profiles_df,
                monthly_activity_df,
            ) = prepare_database_tables(
                incremental_data
            )

            load_cursor = connection.cursor()

            try:
                load_customers(
            load_cursor,
            customers_df
        )

                load_credit_profiles(
            load_cursor,
            credit_profiles_df
        )

                load_monthly_activity(
            load_cursor,
            monthly_activity_df
        )

            finally:
                    load_cursor.close()
        else:

            print(
                "\nNo new or changed records. "
                "Database load skipped."
            )

        # ----------------------------------------------------
        # Complete audit
        # ----------------------------------------------------

        complete_audit_record(
            connection=connection,
            batch_id=batch_id,
            new_count=new_count,
            updated_count=updated_count,
            unchanged_count=unchanged_count,
            loaded_count=loaded_count,
        )

        connection.commit()

        print(
            "\nIncremental transaction "
            "committed successfully."
        )

        print("INCREMENTAL LOAD RESULT: PASS")

    except Exception as error:

        connection.rollback()

        print(
            "\nIncremental transaction "
            "rolled back."
        )

        # The main transaction was rolled back, including
        # its RUNNING audit row. Record the failure separately.
        failure_connection = None

        try:
            failure_connection = get_connection()

            cursor = failure_connection.cursor()

            query = """
                INSERT INTO etl_batch_audit (
                    source_file,
                    start_time,
                    end_time,
                    source_record_count,
                    new_record_count,
                    updated_record_count,
                    unchanged_record_count,
                    loaded_record_count,
                    failed_record_count,
                    status,
                    error_message
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """

            cursor.execute(
                query,
                (
                    Path(file_path).name,
                    start_time,
                    datetime.now(),
                    source_count,
                    new_count,
                    updated_count,
                    unchanged_count,
                    0,
                    new_count + updated_count,
                    "FAILED",
                    str(error)[:5000],
                ),
            )

            failure_connection.commit()
            cursor.close()

        finally:
            if (
                failure_connection is not None
                and failure_connection.is_connected()
            ):
                failure_connection.close()

        raise

    finally:

        if connection.is_connected():
            connection.close()

            print("MySQL connection closed.")


if __name__ == "__main__":

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    run_incremental_pipeline(FILE_PATH)