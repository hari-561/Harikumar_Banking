import mysql.connector
from mysql.connector import Error
import pandas as pd


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "banking_loan_db",
}


BATCH_SIZE = 5000


def get_connection():
    """
    Create and return a MySQL database connection.
    """

    try:
        connection = mysql.connector.connect(**DB_CONFIG)

        if connection.is_connected():
            return connection

    except Error as exc:
        raise ConnectionError(
            f"Unable to connect to MySQL: {exc}"
        ) from exc


def load_customers(cursor, customers: pd.DataFrame):
    """
    Insert/update customer demographic records.
    """

    sql = """
        INSERT INTO customers (
            customer_id,
            gender_code,
            education_code,
            marital_status_code,
            age
        )
        VALUES (%s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            gender_code = VALUES(gender_code),
            education_code = VALUES(education_code),
            marital_status_code = VALUES(marital_status_code),
            age = VALUES(age)
    """

    records = list(
        customers.itertuples(index=False, name=None)
    )

    cursor.executemany(sql, records)


def load_credit_profiles(cursor, credit_profiles: pd.DataFrame):
    """
    Insert/update credit profile records.
    """

    sql = """
        INSERT INTO credit_profiles (
            customer_id,
            credit_limit,
            delay_month_count,
            max_delay_status,
            has_payment_delay,
            total_bill_amount_6m,
            average_bill_amount_6m,
            total_payment_amount_6m,
            average_payment_amount_6m,
            latest_utilization_ratio,
            default_next_month
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )

        ON DUPLICATE KEY UPDATE
            credit_limit = VALUES(credit_limit),
            delay_month_count = VALUES(delay_month_count),
            max_delay_status = VALUES(max_delay_status),
            has_payment_delay = VALUES(has_payment_delay),
            total_bill_amount_6m = VALUES(total_bill_amount_6m),
            average_bill_amount_6m = VALUES(average_bill_amount_6m),
            total_payment_amount_6m = VALUES(total_payment_amount_6m),
            average_payment_amount_6m = VALUES(average_payment_amount_6m),
            latest_utilization_ratio = VALUES(latest_utilization_ratio),
            default_next_month = VALUES(default_next_month)
    """

    records = list(
        credit_profiles.itertuples(index=False, name=None)
    )

    cursor.executemany(sql, records)


def load_monthly_activity(
    cursor,
    monthly_activity: pd.DataFrame,
    batch_size: int = BATCH_SIZE
):
    """
    Insert/update monthly activity in batches.
    """

    sql = """
        INSERT INTO monthly_credit_activity (
            customer_id,
            activity_month,
            repayment_status,
            bill_amount,
            payment_amount
        )
        VALUES (%s, %s, %s, %s, %s)

        ON DUPLICATE KEY UPDATE
            repayment_status = VALUES(repayment_status),
            bill_amount = VALUES(bill_amount),
            payment_amount = VALUES(payment_amount)
    """

    data = monthly_activity.copy()

    # Convert pandas Timestamp into Python date objects
    data["activity_month"] = (
        pd.to_datetime(data["activity_month"]).dt.date
    )

    records = list(
        data.itertuples(index=False, name=None)
    )

    for start in range(0, len(records), batch_size):

        batch = records[start:start + batch_size]

        cursor.executemany(sql, batch)

        print(
            f"Monthly activity processed: "
            f"{min(start + batch_size, len(records))}"
            f"/{len(records)}"
        )


def get_database_counts(cursor):
    """
    Return row counts from the main database tables.
    """

    tables = [
        "customers",
        "credit_profiles",
        "monthly_credit_activity",
    ]

    counts = {}

    for table in tables:

        cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        counts[table] = cursor.fetchone()[0]

    return counts


def load_database(
    customers: pd.DataFrame,
    credit_profiles: pd.DataFrame,
    monthly_activity: pd.DataFrame
):
    """
    Load prepared datasets into MySQL using one transaction.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()

        cursor = connection.cursor()

        print("\n========== MYSQL LOAD STARTED ==========")

        print("\nLoading customers...")
        load_customers(cursor, customers)

        print(
            f"Customers processed: {len(customers)}"
        )

        print("\nLoading credit profiles...")
        load_credit_profiles(
            cursor,
            credit_profiles
        )

        print(
            f"Credit profiles processed: "
            f"{len(credit_profiles)}"
        )

        print("\nLoading monthly activity...")
        load_monthly_activity(
            cursor,
            monthly_activity
        )

        # Commit only after all three tables succeed
        connection.commit()

        print("\nTransaction committed successfully.")

        counts = get_database_counts(cursor)

        print("\n========== DATABASE COUNTS ==========")

        for table, count in counts.items():
            print(f"{table}: {count}")

        return counts

    except Exception as exc:

        if connection is not None:
            connection.rollback()

        print("\nTransaction rolled back.")

        raise RuntimeError(
            f"Database load failed: {exc}"
        ) from exc

    finally:

        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()

        print("\nMySQL connection closed.")


def load_risk_assessments(cursor, risk_df):
    """
    Insert or update customer risk assessments.
    """

    if risk_df.empty:
        print("No risk assessments to load.")
        return

    sql = """
        INSERT INTO customer_risk_assessment (
            customer_id,
            payment_to_bill_ratio,
            delay_frequency_score,
            delay_severity_score,
            utilization_score,
            payment_behavior_score,
            risk_score,
            risk_band,
            rule_version
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE

            payment_to_bill_ratio =
                VALUES(payment_to_bill_ratio),

            delay_frequency_score =
                VALUES(delay_frequency_score),

            delay_severity_score =
                VALUES(delay_severity_score),

            utilization_score =
                VALUES(utilization_score),

            payment_behavior_score =
                VALUES(payment_behavior_score),

            risk_score =
                VALUES(risk_score),

            risk_band =
                VALUES(risk_band),

            rule_version =
                VALUES(rule_version)
    """

    records = []

    for row in risk_df.itertuples(index=False):

        payment_ratio = (
            None
            if pd.isna(row.payment_to_bill_ratio)
            else float(row.payment_to_bill_ratio)
        )

        records.append(
            (
                int(row.customer_id),
                payment_ratio,
                int(row.delay_frequency_score),
                int(row.delay_severity_score),
                int(row.utilization_score),
                int(row.payment_behavior_score),
                int(row.risk_score),
                str(row.risk_band),
                str(row.rule_version)
            )
        )

    cursor.executemany(
        sql,
        records
    )

    print(
        f"Risk assessments processed: {len(records)}"
    )


if __name__ == "__main__":

    from extract import extract_data
    from validate import validate_data, validation_passed
    from transform import transform_data
    from prepare_tables import prepare_database_tables

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    # -----------------------------------------
    # Extract
    # -----------------------------------------

    raw_data = extract_data(FILE_PATH)

    # -----------------------------------------
    # Validate
    # -----------------------------------------

    validation_report = validate_data(raw_data)

    if not validation_passed(validation_report):
        raise ValueError(
            "Dataset failed validation. Load stopped."
        )

    # -----------------------------------------
    # Transform
    # -----------------------------------------

    transformed_data = transform_data(raw_data)

    # -----------------------------------------
    # Prepare relational tables
    # -----------------------------------------

    (
        customers,
        credit_profiles,
        monthly_activity,
    ) = prepare_database_tables(
        transformed_data
    )

    # -----------------------------------------
    # Load
    # -----------------------------------------

    counts = load_database(
        customers,
        credit_profiles,
        monthly_activity
    )

    # -----------------------------------------
    # Reconciliation
    # -----------------------------------------

    print("\n========== LOAD RECONCILIATION ==========")

    checks = {
        "customers": (
            len(customers),
            counts["customers"]
        ),

        "credit_profiles": (
            len(credit_profiles),
            counts["credit_profiles"]
        ),

        "monthly_credit_activity": (
            len(monthly_activity),
            counts["monthly_credit_activity"]
        ),
    }

    reconciliation_passed = True

    for table, (expected, actual) in checks.items():

        status = (
            "PASS"
            if expected == actual
            else "FAIL"
        )

        if status == "FAIL":
            reconciliation_passed = False

        print(
            f"{table}: "
            f"expected={expected}, "
            f"actual={actual}, "
            f"{status}"
        )

    if not reconciliation_passed:
        raise RuntimeError(
            "Database reconciliation failed."
        )

    print("\nLOAD RESULT: PASS")