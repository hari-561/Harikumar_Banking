from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [
    "ID",
    "LIMIT_BAL",
    "SEX",
    "EDUCATION",
    "MARRIAGE",
    "AGE",
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6",
    "default payment next month",
]


def extract_data(file_path: str) -> pd.DataFrame:
    """
    Extract the banking credit-risk dataset from Excel.

    The source workbook contains an additional first header row
    (X1-X23/Y), so the actual banking field names are located
    in the second row.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {file_path}"
        )

    if path.suffix.lower() not in {".xls", ".xlsx"}:
        raise ValueError(
            "Unsupported file type. Expected .xls or .xlsx"
        )

    try:
        df = pd.read_excel(
            path,
            header=1
        )

    except Exception as exc:
        raise RuntimeError(
            f"Failed to read Excel file: {exc}"
        ) from exc

    if df.empty:
        raise ValueError(
            "The input dataset contains no records."
        )

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing: {missing_columns}"
        )

    return df


if __name__ == "__main__":

    FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"

    data = extract_data(FILE_PATH)

    print("Extraction successful.")
    print("Rows   :", len(data))
    print("Columns:", len(data.columns))

    print("\nFirst 3 records:")
    print(data.head(3).to_string())