import pandas as pd
from decimal import Decimal, ROUND_HALF_UP



COLUMN_MAPPING = {
    "ID": "customer_id",
    "LIMIT_BAL": "credit_limit",
    "SEX": "gender_code",
    "EDUCATION": "education_code",
    "MARRIAGE": "marital_status_code",
    "AGE": "age",

    "PAY_0": "repayment_status_sep",
    "PAY_2": "repayment_status_aug",
    "PAY_3": "repayment_status_jul",
    "PAY_4": "repayment_status_jun",
    "PAY_5": "repayment_status_may",
    "PAY_6": "repayment_status_apr",

    "BILL_AMT1": "bill_amount_sep",
    "BILL_AMT2": "bill_amount_aug",
    "BILL_AMT3": "bill_amount_jul",
    "BILL_AMT4": "bill_amount_jun",
    "BILL_AMT5": "bill_amount_may",
    "BILL_AMT6": "bill_amount_apr",

    "PAY_AMT1": "payment_amount_sep",
    "PAY_AMT2": "payment_amount_aug",
    "PAY_AMT3": "payment_amount_jul",
    "PAY_AMT4": "payment_amount_jun",
    "PAY_AMT5": "payment_amount_may",
    "PAY_AMT6": "payment_amount_apr",

    "default payment next month": "default_next_month",
}


GENDER_MAPPING = {
    1: "Male",
    2: "Female",
}


EDUCATION_MAPPING = {
    0: "Others",
    1: "Graduate School",
    2: "University",
    3: "High School",
    4: "Others",
    5: "Others",
    6: "Others",
}


MARITAL_STATUS_MAPPING = {
    0: "Others",
    1: "Married",
    2: "Single",
    3: "Others",
}


REPAYMENT_COLUMNS = [
    "repayment_status_sep",
    "repayment_status_aug",
    "repayment_status_jul",
    "repayment_status_jun",
    "repayment_status_may",
    "repayment_status_apr",
]


BILL_COLUMNS = [
    "bill_amount_sep",
    "bill_amount_aug",
    "bill_amount_jul",
    "bill_amount_jun",
    "bill_amount_may",
    "bill_amount_apr",
]


PAYMENT_COLUMNS = [
    "payment_amount_sep",
    "payment_amount_aug",
    "payment_amount_jul",
    "payment_amount_jun",
    "payment_amount_may",
    "payment_amount_apr",
]

def calculate_utilization_ratio(row):
    """
    Calculate utilization using the same six-decimal
    precision stored in MySQL DECIMAL(12,6).
    """

    bill_amount = Decimal(str(row["bill_amount_sep"]))
    credit_limit = Decimal(str(row["credit_limit"]))

    return float(
        (bill_amount / credit_limit).quantize(
            Decimal("0.000001"),
            rounding=ROUND_HALF_UP
        )
    )



def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform validated raw banking data into an
    application-friendly curated dataset.

    Raw financial values and source category codes are preserved.
    """

    transformed = df.copy()

    # ---------------------------------------------------------
    # 1. Rename source columns
    # ---------------------------------------------------------

    transformed = transformed.rename(
        columns=COLUMN_MAPPING
    )

    # ---------------------------------------------------------
    # 2. Add readable demographic labels
    # ---------------------------------------------------------

    transformed["gender"] = (
        transformed["gender_code"]
        .map(GENDER_MAPPING)
    )

    transformed["education"] = (
        transformed["education_code"]
        .map(EDUCATION_MAPPING)
    )

    transformed["marital_status"] = (
        transformed["marital_status_code"]
        .map(MARITAL_STATUS_MAPPING)
    )

    # ---------------------------------------------------------
    # 3. Repayment behaviour
    #
    # Positive repayment status indicates a recorded delay.
    # Non-positive values are not treated as delayed months.
    # ---------------------------------------------------------

    transformed["delay_month_count"] = (
        transformed[REPAYMENT_COLUMNS] > 0
    ).sum(axis=1)

    transformed["max_delay_status"] = (
        transformed[REPAYMENT_COLUMNS]
        .clip(lower=0)
        .max(axis=1)
    )

    transformed["has_payment_delay"] = (
        transformed["delay_month_count"] > 0
    )

    # ---------------------------------------------------------
    # 4. Six-month bill metrics
    # ---------------------------------------------------------

    transformed["total_bill_amount_6m"] = (
        transformed[BILL_COLUMNS]
        .sum(axis=1)
    )

    transformed["average_bill_amount_6m"] = (
        transformed[BILL_COLUMNS]
        .mean(axis=1)
        .round(2)
    )

    # ---------------------------------------------------------
    # 5. Six-month payment metrics
    # ---------------------------------------------------------

    transformed["total_payment_amount_6m"] = (
        transformed[PAYMENT_COLUMNS]
        .sum(axis=1)
    )

    transformed["average_payment_amount_6m"] = (
        transformed[PAYMENT_COLUMNS]
        .mean(axis=1)
        .round(2)
    )

    # ---------------------------------------------------------
    # 6. Latest utilization
    #
    # credit_limit > 0 has already been guaranteed by validation.
    # Do NOT cap ratios greater than 1.
    # ---------------------------------------------------------

    transformed["latest_utilization_ratio"] = transformed.apply(
    calculate_utilization_ratio,
    axis=1
)

    # ---------------------------------------------------------
    # 7. Reorder important columns
    # ---------------------------------------------------------

    first_columns = [
        "customer_id",
        "credit_limit",

        "gender_code",
        "gender",

        "education_code",
        "education",

        "marital_status_code",
        "marital_status",

        "age",
    ]

    remaining_columns = [
        column
        for column in transformed.columns
        if column not in first_columns
    ]

    transformed = transformed[
        first_columns + remaining_columns
    ]

    return transformed


if __name__ == "__main__":

    from extract import extract_data
    from validate import validate_data, validation_passed

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    raw_data = extract_data(FILE_PATH)

    validation_report = validate_data(raw_data)

    if not validation_passed(validation_report):
        raise ValueError(
            "Dataset failed validation. Transformation stopped."
        )

    curated_data = transform_data(raw_data)

    print("\n========== TRANSFORMATION COMPLETE ==========")

    print("Input rows :", len(raw_data))
    print("Output rows:", len(curated_data))

    print("\nInput columns :", len(raw_data.columns))
    print("Output columns:", len(curated_data.columns))

    print("\n========== CURATED COLUMNS ==========")

    for i, column in enumerate(curated_data.columns, start=1):
        print(f"{i:2}. {column}")

    print("\n========== SAMPLE TRANSFORMED DATA ==========")

    sample_columns = [
        "customer_id",
        "credit_limit",
        "gender",
        "education",
        "marital_status",
        "age",
        "delay_month_count",
        "max_delay_status",
        "has_payment_delay",
        "total_bill_amount_6m",
        "total_payment_amount_6m",
        "latest_utilization_ratio",
        "default_next_month",
    ]

    print(
        curated_data[sample_columns]
        .head(10)
        .to_string(index=False)
    )

    print("\n========== TRANSFORMATION CHECKS ==========")

    print(
        "Missing gender labels:",
        curated_data["gender"].isnull().sum()
    )

    print(
        "Missing education labels:",
        curated_data["education"].isnull().sum()
    )

    print(
        "Missing marital labels:",
        curated_data["marital_status"].isnull().sum()
    )

    print(
        "Customers with payment delay:",
        curated_data["has_payment_delay"].sum()
    )

    print(
        "Customers with 2+ delayed months:",
        (curated_data["delay_month_count"] >= 2).sum()
    )

    print(
        "Customers with utilization > 1:",
        (curated_data["latest_utilization_ratio"] > 1).sum()
    )