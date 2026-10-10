import pandas as pd

from load import get_connection


COMPARE_COLUMNS = [
    "customer_id",
    "credit_limit",
    "gender_code",
    "education_code",
    "marital_status_code",
    "age",
    "delay_month_count",
    "max_delay_status",
    "has_payment_delay",
    "total_bill_amount_6m",
    "average_bill_amount_6m",
    "total_payment_amount_6m",
    "average_payment_amount_6m",
    "latest_utilization_ratio",
    "default_next_month",
]


def fetch_existing_customers() -> pd.DataFrame:
    """
    Read the current customer and credit-profile state from MySQL.

    Used only for incremental change detection.
    """

    connection = None
    cursor = None

    try:
        connection = get_connection()

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                c.customer_id,
                cp.credit_limit,
                c.gender_code,
                c.education_code,
                c.marital_status_code,
                c.age,
                cp.delay_month_count,
                cp.max_delay_status,
                cp.has_payment_delay,
                cp.total_bill_amount_6m,
                cp.average_bill_amount_6m,
                cp.total_payment_amount_6m,
                cp.average_payment_amount_6m,
                cp.latest_utilization_ratio,
                cp.default_next_month
            FROM customers c
            INNER JOIN credit_profiles cp
                ON c.customer_id = cp.customer_id
        """

        cursor.execute(query)

        rows = cursor.fetchall()

        return pd.DataFrame(rows)

    finally:
        if cursor is not None:
            cursor.close()

        if (
            connection is not None
            and connection.is_connected()
        ):
            connection.close()


def normalize_for_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize values so Pandas and MySQL representations
    can be compared reliably.
    """

    normalized = df[COMPARE_COLUMNS].copy()

    integer_columns = [
        "customer_id",
        "gender_code",
        "education_code",
        "marital_status_code",
        "age",
        "delay_month_count",
        "max_delay_status",
        "default_next_month",
    ]

    for column in integer_columns:
        normalized[column] = (
            pd.to_numeric(normalized[column])
            .astype("int64")
        )

    normalized["has_payment_delay"] = (
        normalized["has_payment_delay"]
        .astype(bool)
    )

    decimal_columns = [
        "credit_limit",
        "total_bill_amount_6m",
        "average_bill_amount_6m",
        "total_payment_amount_6m",
        "average_payment_amount_6m",
        "latest_utilization_ratio",
    ]

    for column in decimal_columns:
        normalized[column] = (
            pd.to_numeric(normalized[column])
            .astype(float)
            .round(6)
        )

    return normalized


def detect_changes(
    incoming: pd.DataFrame,
    existing: pd.DataFrame
):
    """
    Classify incoming customer records as:

    NEW
    CHANGED
    UNCHANGED
    """

    incoming = normalize_for_comparison(incoming)
    existing = normalize_for_comparison(existing)

    incoming = incoming.set_index(
        "customer_id",
        drop=False
    )

    existing = existing.set_index(
        "customer_id",
        drop=False
    )

    existing_ids = set(existing.index)

    new_ids = [
        customer_id
        for customer_id in incoming.index
        if customer_id not in existing_ids
    ]

    common_ids = [
        customer_id
        for customer_id in incoming.index
        if customer_id in existing_ids
    ]

    changed_ids = []
    unchanged_ids = []

    columns_to_compare = [
        column
        for column in COMPARE_COLUMNS
        if column != "customer_id"
    ]

    for customer_id in common_ids:

        incoming_row = incoming.loc[
            customer_id,
            columns_to_compare
        ]

        existing_row = existing.loc[
            customer_id,
            columns_to_compare
        ]

        if incoming_row.equals(existing_row):
            unchanged_ids.append(customer_id)
        else:
            changed_ids.append(customer_id)

    new_records = (
        incoming.loc[new_ids]
        .reset_index(drop=True)
    )

    changed_records = (
        incoming.loc[changed_ids]
        .reset_index(drop=True)
    )

    unchanged_records = (
        incoming.loc[unchanged_ids]
        .reset_index(drop=True)
    )

    return (
        new_records,
        changed_records,
        unchanged_records,
    )

def diagnose_changes(
    incoming: pd.DataFrame,
    existing: pd.DataFrame,
    changed_records: pd.DataFrame
):
    """
    Show which fields caused records to be classified as changed.
    """

    if changed_records.empty:
        print("\nNo changed records to diagnose.")
        return

    incoming_normalized = normalize_for_comparison(incoming)
    existing_normalized = normalize_for_comparison(existing)

    incoming_normalized = incoming_normalized.set_index("customer_id")
    existing_normalized = existing_normalized.set_index("customer_id")

    changed_ids = changed_records["customer_id"].tolist()

    difference_counts = {}

    print("\n========== CHANGE DIAGNOSTIC ==========")

    for column in COMPARE_COLUMNS:

        if column == "customer_id":
            continue

        count = 0

        for customer_id in changed_ids:

            incoming_value = incoming_normalized.loc[
                customer_id, column
            ]

            existing_value = existing_normalized.loc[
                customer_id, column
            ]

            if incoming_value != existing_value:
                count += 1

        if count > 0:
            difference_counts[column] = count

    print("\nFields causing differences:")

    for column, count in difference_counts.items():
        print(
            f"{column}: {count}"
        )

    print("\nSample differences:")

    for customer_id in changed_ids[:5]:

        print(f"\nCustomer {customer_id}")

        for column in COMPARE_COLUMNS:

            if column == "customer_id":
                continue

            incoming_value = incoming_normalized.loc[
                customer_id, column
            ]

            existing_value = existing_normalized.loc[
                customer_id, column
            ]

            if incoming_value != existing_value:

                print(
                    f"  {column}: "
                    f"incoming={incoming_value}, "
                    f"database={existing_value}"
                )

if __name__ == "__main__":

    from extract import extract_data
    from validate import validate_data, validation_passed
    from transform import transform_data

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
            "Dataset failed validation."
        )

    # -----------------------------------------
    # Transform incoming source
    # -----------------------------------------

    transformed_data = transform_data(raw_data)

    

    # -----------------------------------------
    # Read existing database state
    # -----------------------------------------

    existing_data = fetch_existing_customers()

    print("\n========== EXISTING DATABASE STATE ==========")

    print(
        "Existing customers:",
        len(existing_data)
    )

    # -----------------------------------------
    # Detect changes
    # -----------------------------------------

    (
        new_records,
        changed_records,
        unchanged_records,
    ) = detect_changes(
        transformed_data,
        existing_data
    )

    print("\n========== INCREMENTAL DETECTION ==========")

    print(
        "Incoming records :",
        len(transformed_data)
    )

    print(
        "New records      :",
        len(new_records)
    )

    print(
        "Changed records  :",
        len(changed_records)
    )

    print(
        "Unchanged records:",
        len(unchanged_records)
    )

    # -----------------------------------------
    # Reconciliation
    # -----------------------------------------

    classified_count = (
        len(new_records)
        + len(changed_records)
        + len(unchanged_records)
    )

    print("\n========== RECONCILIATION ==========")

    print(
        "Incoming records  :",
        len(transformed_data)
    )

    print(
        "Classified records:",
        classified_count
    )

    if classified_count != len(transformed_data):
        raise RuntimeError(
            "Incremental classification reconciliation failed."
        )

    print("Classification reconciliation: PASS")

    # -----------------------------------------
    # Optional samples
    # -----------------------------------------

    if not new_records.empty:
        print("\nNew customer IDs:")
        print(
            new_records["customer_id"]
            .head(10)
            .tolist()
        )

    if not changed_records.empty:
        print("\nChanged customer IDs:")
        print(
            changed_records["customer_id"]
            .head(10)
            .tolist()
        )

    diagnose_changes(
    transformed_data,
    existing_data,
    changed_records
)