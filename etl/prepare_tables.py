import pandas as pd


MONTH_MAPPING = [
    {
        "month": "2005-09-01",
        "repayment": "repayment_status_sep",
        "bill": "bill_amount_sep",
        "payment": "payment_amount_sep",
    },
    {
        "month": "2005-08-01",
        "repayment": "repayment_status_aug",
        "bill": "bill_amount_aug",
        "payment": "payment_amount_aug",
    },
    {
        "month": "2005-07-01",
        "repayment": "repayment_status_jul",
        "bill": "bill_amount_jul",
        "payment": "payment_amount_jul",
    },
    {
        "month": "2005-06-01",
        "repayment": "repayment_status_jun",
        "bill": "bill_amount_jun",
        "payment": "payment_amount_jun",
    },
    {
        "month": "2005-05-01",
        "repayment": "repayment_status_may",
        "bill": "bill_amount_may",
        "payment": "payment_amount_may",
    },
    {
        "month": "2005-04-01",
        "repayment": "repayment_status_apr",
        "bill": "bill_amount_apr",
        "payment": "payment_amount_apr",
    },
]


def prepare_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare customer demographic records for the customers table.
    """

    customers = df[
        [
            "customer_id",
            "gender_code",
            "education_code",
            "marital_status_code",
            "age",
        ]
    ].copy()

    return customers


def prepare_credit_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare customer credit summary records.
    """

    credit_profiles = df[
        [
            "customer_id",
            "credit_limit",
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
    ].copy()

    return credit_profiles


def prepare_monthly_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert six monthly columns per customer into six rows per customer.
    """

    monthly_frames = []

    for mapping in MONTH_MAPPING:

        monthly = pd.DataFrame({
            "customer_id": df["customer_id"],
            "activity_month": pd.to_datetime(mapping["month"]),
            "repayment_status": df[mapping["repayment"]],
            "bill_amount": df[mapping["bill"]],
            "payment_amount": df[mapping["payment"]],
        })

        monthly_frames.append(monthly)

    monthly_activity = pd.concat(
        monthly_frames,
        ignore_index=True
    )

    monthly_activity = monthly_activity.sort_values(
        ["customer_id", "activity_month"]
    ).reset_index(drop=True)

    return monthly_activity


def prepare_database_tables(df: pd.DataFrame):
    """
    Prepare all DataFrames required for database loading.
    """

    customers = prepare_customers(df)

    credit_profiles = prepare_credit_profiles(df)

    monthly_activity = prepare_monthly_activity(df)

    return customers, credit_profiles, monthly_activity

def prepare_risk_assessments(risk_data):
    """
    Prepare rule-based customer risk results for MySQL.
    """

    required_columns = [
        "customer_id",
        "payment_to_bill_ratio",
        "delay_frequency_score",
        "delay_severity_score",
        "utilization_score",
        "payment_behavior_score",
        "risk_score",
        "risk_band"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in risk_data.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing risk assessment columns: {missing_columns}"
        )

    risk_assessments = risk_data[
        required_columns
    ].copy()

    risk_assessments["rule_version"] = "1.0"

    return risk_assessments

if __name__ == "__main__":

    from extract import extract_data
    from validate import validate_data, validation_passed
    from transform import transform_data

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    # Extract
    raw_data = extract_data(FILE_PATH)

    # Validate
    validation_report = validate_data(raw_data)

    if not validation_passed(validation_report):
        raise ValueError(
            "Dataset failed validation."
        )

    # Transform
    transformed_data = transform_data(raw_data)

    # Prepare database tables
    (
        customers,
        credit_profiles,
        monthly_activity,
    ) = prepare_database_tables(transformed_data)

    print("\n========== DATABASE TABLE PREPARATION ==========")

    print("\nCustomers:")
    print("Rows:", len(customers))
    print(customers.head().to_string(index=False))

    print("\nCredit Profiles:")
    print("Rows:", len(credit_profiles))
    print(credit_profiles.head().to_string(index=False))

    print("\nMonthly Credit Activity:")
    print("Rows:", len(monthly_activity))
    print(monthly_activity.head(12).to_string(index=False))

    print("\n========== RECONCILIATION ==========")

    print(
        "Source customers:",
        len(transformed_data)
    )

    print(
        "Customer table rows:",
        len(customers)
    )

    print(
        "Credit profile rows:",
        len(credit_profiles)
    )

    print(
        "Monthly activity rows:",
        len(monthly_activity)
    )

    expected_monthly_rows = len(transformed_data) * 6

    print(
        "Expected monthly rows:",
        expected_monthly_rows
    )

    # Duplicate customer/month check
    duplicate_customer_month = monthly_activity.duplicated(
        subset=["customer_id", "activity_month"]
    ).sum()

    print(
        "Duplicate customer/month combinations:",
        duplicate_customer_month
    )

    # Customer ID reconciliation
    print(
        "Unique customers in monthly activity:",
        monthly_activity["customer_id"].nunique()
    )

    # Month reconciliation
    print("\nMonthly row counts:")

    print(
        monthly_activity["activity_month"]
        .value_counts()
        .sort_index()
    )