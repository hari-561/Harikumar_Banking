import pandas as pd


REPAYMENT_COLUMNS = [
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
]

BILL_COLUMNS = [
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
]

PAYMENT_COLUMNS = [
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
]

TARGET_COLUMN = "default payment next month"


def add_result(results, check, status, count, message):
    """
    Add one validation result to the validation report.
    """

    results.append({
        "check": check,
        "status": status,
        "count": int(count),
        "message": message,
    })


def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run reusable data-quality checks against the banking dataset.

    Returns a DataFrame containing:
        check
        status
        count
        message
    """

    results = []

    # ---------------------------------------------------------
    # DQ01 - Missing values
    # ---------------------------------------------------------

    missing_count = df.isnull().sum().sum()

    add_result(
        results,
        "DQ01_MISSING_VALUES",
        "PASS" if missing_count == 0 else "FAIL",
        missing_count,
        "Dataset should not contain missing values.",
    )

    # ---------------------------------------------------------
    # DQ02 - Duplicate rows
    # ---------------------------------------------------------

    duplicate_rows = df.duplicated().sum()

    add_result(
        results,
        "DQ02_DUPLICATE_ROWS",
        "PASS" if duplicate_rows == 0 else "FAIL",
        duplicate_rows,
        "Complete duplicate records are not allowed.",
    )

    # ---------------------------------------------------------
    # DQ03 - Missing customer IDs
    # ---------------------------------------------------------

    missing_ids = df["ID"].isnull().sum()

    add_result(
        results,
        "DQ03_MISSING_CUSTOMER_ID",
        "PASS" if missing_ids == 0 else "FAIL",
        missing_ids,
        "Customer ID must not be null.",
    )

    # ---------------------------------------------------------
    # DQ04 - Duplicate customer IDs
    # ---------------------------------------------------------

    duplicate_ids = df["ID"].duplicated().sum()

    add_result(
        results,
        "DQ04_DUPLICATE_CUSTOMER_ID",
        "PASS" if duplicate_ids == 0 else "FAIL",
        duplicate_ids,
        "Customer ID must be unique.",
    )

    # ---------------------------------------------------------
    # DQ05 - Credit limit
    # ---------------------------------------------------------

    invalid_credit_limit = (df["LIMIT_BAL"] <= 0).sum()

    add_result(
        results,
        "DQ05_INVALID_CREDIT_LIMIT",
        "PASS" if invalid_credit_limit == 0 else "FAIL",
        invalid_credit_limit,
        "Credit limit must be greater than zero.",
    )

    # ---------------------------------------------------------
    # DQ06 - Gender
    # ---------------------------------------------------------

    invalid_gender = (~df["SEX"].isin([1, 2])).sum()

    add_result(
        results,
        "DQ06_INVALID_GENDER",
        "PASS" if invalid_gender == 0 else "FAIL",
        invalid_gender,
        "SEX must contain only documented codes 1 or 2.",
    )

    # ---------------------------------------------------------
    # DQ07 - Education
    # ---------------------------------------------------------

    unusual_education = (~df["EDUCATION"].isin([1, 2, 3, 4])).sum()

    add_result(
        results,
        "DQ07_UNDOCUMENTED_EDUCATION",
        "PASS" if unusual_education == 0 else "WARNING",
        unusual_education,
        "Education codes outside documented 1-4 will be mapped "
        "to Others during transformation while preserving source codes.",
    )

    # ---------------------------------------------------------
    # DQ08 - Marriage
    # ---------------------------------------------------------

    unusual_marriage = (~df["MARRIAGE"].isin([1, 2, 3])).sum()

    add_result(
        results,
        "DQ08_UNDOCUMENTED_MARRIAGE",
        "PASS" if unusual_marriage == 0 else "WARNING",
        unusual_marriage,
        "Marriage codes outside documented 1-3 will be mapped "
        "to Others during transformation while preserving source codes.",
    )

    # ---------------------------------------------------------
    # DQ09 - Age
    # ---------------------------------------------------------

    invalid_age = (df["AGE"] <= 0).sum()

    add_result(
        results,
        "DQ09_INVALID_AGE",
        "PASS" if invalid_age == 0 else "FAIL",
        invalid_age,
        "Age must be greater than zero.",
    )

    # ---------------------------------------------------------
    # DQ10 - Repayment status
    #
    # Observed source values are -2 through 8.
    # We preserve these values rather than converting them.
    # ---------------------------------------------------------

    invalid_repayment = (
        ~df[REPAYMENT_COLUMNS]
        .isin(range(-2, 9))
    ).sum().sum()

    add_result(
        results,
        "DQ10_INVALID_REPAYMENT_STATUS",
        "PASS" if invalid_repayment == 0 else "FAIL",
        invalid_repayment,
        "Repayment status must be within the accepted source range -2 to 8.",
    )

    # ---------------------------------------------------------
    # DQ11 - Negative bill balances
    #
    # These are warnings, not failures.
    # Values are preserved.
    # ---------------------------------------------------------

    negative_bills = (df[BILL_COLUMNS] < 0).sum().sum()

    add_result(
        results,
        "DQ11_NEGATIVE_BILL_BALANCE",
        "PASS" if negative_bills == 0 else "WARNING",
        negative_bills,
        "Negative bill balances are preserved and flagged for analysis.",
    )

    # ---------------------------------------------------------
    # DQ12 - Negative payments
    # ---------------------------------------------------------

    negative_payments = (df[PAYMENT_COLUMNS] < 0).sum().sum()

    add_result(
        results,
        "DQ12_NEGATIVE_PAYMENT",
        "PASS" if negative_payments == 0 else "FAIL",
        negative_payments,
        "Previous payment amounts must not be negative.",
    )

    # ---------------------------------------------------------
    # DQ13 - Target
    # ---------------------------------------------------------

    invalid_target = (~df[TARGET_COLUMN].isin([0, 1])).sum()

    add_result(
        results,
        "DQ13_INVALID_DEFAULT_TARGET",
        "PASS" if invalid_target == 0 else "FAIL",
        invalid_target,
        "Default target must contain only 0 or 1.",
    )

    return pd.DataFrame(results)


def validation_passed(report: pd.DataFrame) -> bool:
    """
    Return True when the dataset contains no FAIL checks.

    WARNING checks are permitted.
    """

    return not (report["status"] == "FAIL").any()


if __name__ == "__main__":

    from extract import extract_data

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    data = extract_data(FILE_PATH)

    report = validate_data(data)

    print("\n========== DATA QUALITY REPORT ==========")

    print(
        report.to_string(index=False)
    )

    print("\n=========================================")

    if validation_passed(report):
        print("VALIDATION RESULT: PASS")
        print("Dataset may proceed to transformation.")
    else:
        print("VALIDATION RESULT: FAIL")
        print("Dataset must not proceed to transformation.")