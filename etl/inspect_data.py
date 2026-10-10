import pandas as pd

FILE_PATH = "../data/raw/default_of_credit_card_clients.xls"
# Use .xlsx instead if that is your actual extension


# ============================================================
# 1. LOAD RAW DATA
# ============================================================

df = pd.read_excel(FILE_PATH, header=1)


# ============================================================
# 2. BASIC STRUCTURE
# ============================================================

print("\n========== DATASET SHAPE ==========")
print("Rows   :", df.shape[0])
print("Columns:", df.shape[1])


print("\n========== COLUMN NAMES ==========")

for i, column in enumerate(df.columns, start=1):
    print(f"{i:2}. {column}")


print("\n========== FIRST 5 ROWS ==========")
print(df.head().to_string())


# ============================================================
# 3. DATA TYPES
# ============================================================

print("\n========== DATA TYPES ==========")
print(df.dtypes)


# ============================================================
# 4. MISSING VALUES
# ============================================================

print("\n========== MISSING VALUES ==========")

missing = df.isnull().sum()
missing = missing[missing > 0]

if len(missing) == 0:
    print("No missing values found.")
else:
    print(missing)


# ============================================================
# 5. DUPLICATES
# ============================================================

print("\n========== DUPLICATE ROWS ==========")
print("Duplicate rows:", df.duplicated().sum())


# ============================================================
# 6. ID VALIDATION
# ============================================================

print("\n========== ID CHECK ==========")

print("Total IDs     :", df["ID"].count())
print("Unique IDs    :", df["ID"].nunique())
print("Duplicate IDs :", df["ID"].duplicated().sum())
print("Missing IDs   :", df["ID"].isnull().sum())


# ============================================================
# 7. NUMERIC SUMMARY
# ============================================================

print("\n========== NUMERIC SUMMARY ==========")

print(
    df.describe()
      .T
      .to_string()
)


# ============================================================
# 8. DEMOGRAPHIC CATEGORIES
# ============================================================

print("\n========== SEX VALUES ==========")
print(df["SEX"].value_counts(dropna=False).sort_index())


print("\n========== EDUCATION VALUES ==========")
print(df["EDUCATION"].value_counts(dropna=False).sort_index())


print("\n========== MARRIAGE VALUES ==========")
print(df["MARRIAGE"].value_counts(dropna=False).sort_index())


# ============================================================
# 9. AGE CHECK
# ============================================================

print("\n========== AGE CHECK ==========")

print("Minimum age :", df["AGE"].min())
print("Maximum age :", df["AGE"].max())
print("Average age :", round(df["AGE"].mean(), 2))


# ============================================================
# 10. CREDIT LIMIT CHECK
# ============================================================

print("\n========== CREDIT LIMIT CHECK ==========")

print("Minimum LIMIT_BAL :", df["LIMIT_BAL"].min())
print("Maximum LIMIT_BAL :", df["LIMIT_BAL"].max())
print("Average LIMIT_BAL :", round(df["LIMIT_BAL"].mean(), 2))

print(
    "Zero/negative LIMIT_BAL:",
    (df["LIMIT_BAL"] <= 0).sum()
)


# ============================================================
# 11. REPAYMENT STATUS
# ============================================================

repayment_columns = [
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6"
]

print("\n========== REPAYMENT STATUS VALUES ==========")

for column in repayment_columns:

    print(f"\n--- {column} ---")

    print(
        df[column]
        .value_counts(dropna=False)
        .sort_index()
    )


# ============================================================
# 12. BILL AMOUNT RANGE
# ============================================================

bill_columns = [
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6"
]

print("\n========== BILL AMOUNT RANGE ==========")

for column in bill_columns:

    print(
        f"{column}: "
        f"min={df[column].min()}, "
        f"max={df[column].max()}, "
        f"negative={(df[column] < 0).sum()}"
    )


# ============================================================
# 13. PAYMENT AMOUNT RANGE
# ============================================================

payment_columns = [
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6"
]

print("\n========== PAYMENT AMOUNT RANGE ==========")

for column in payment_columns:

    print(
        f"{column}: "
        f"min={df[column].min()}, "
        f"max={df[column].max()}, "
        f"negative={(df[column] < 0).sum()}"
    )


# ============================================================
# 14. TARGET DISTRIBUTION
# ============================================================

TARGET = "default payment next month"

print("\n========== TARGET DISTRIBUTION ==========")

print(df[TARGET].value_counts(dropna=False).sort_index())


print("\nPercentage:")

print(
    df[TARGET]
    .value_counts(normalize=True, dropna=False)
    .sort_index()
    .mul(100)
    .round(2)
)


print("\n========== ADDITIONAL QUALITY CHECKS ==========")


# -----------------------------------------
# Education unusual codes
# -----------------------------------------

unusual_education = df[
    ~df["EDUCATION"].isin([1, 2, 3, 4])
]

print(
    "Education codes outside documented 1-4:",
    len(unusual_education)
)


# -----------------------------------------
# Marriage unusual codes
# -----------------------------------------

unusual_marriage = df[
    ~df["MARRIAGE"].isin([1, 2, 3])
]

print(
    "Marriage codes outside documented 1-3:",
    len(unusual_marriage)
)


# -----------------------------------------
# Invalid target
# -----------------------------------------

invalid_target = df[
    ~df["default payment next month"].isin([0, 1])
]

print(
    "Invalid target values:",
    len(invalid_target)
)


# -----------------------------------------
# Customers with all six bill amounts = 0
# -----------------------------------------

bill_columns = [
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6"
]

all_bill_zero = (df[bill_columns] == 0).all(axis=1)

print(
    "Customers with all bill amounts = 0:",
    all_bill_zero.sum()
)


# -----------------------------------------
# Customers with all six payment amounts = 0
# -----------------------------------------

payment_columns = [
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6"
]

all_payment_zero = (df[payment_columns] == 0).all(axis=1)

print(
    "Customers with all payment amounts = 0:",
    all_payment_zero.sum()
)


# -----------------------------------------
# Customers with at least one delayed month
# -----------------------------------------

repayment_columns = [
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6"
]

has_delay = (df[repayment_columns] > 0).any(axis=1)

print(
    "Customers with at least one delayed month:",
    has_delay.sum()
)


# -----------------------------------------
# Customers with repeated delays
# 2 or more months with positive delay
# -----------------------------------------

delay_month_count = (df[repayment_columns] > 0).sum(axis=1)

print(
    "Customers delayed in 2 or more months:",
    (delay_month_count >= 2).sum()
)


# -----------------------------------------
# Customers with bill amount above credit limit
# using latest bill
# -----------------------------------------

bill_above_limit = df["BILL_AMT1"] > df["LIMIT_BAL"]

print(
    "Latest bill greater than credit limit:",
    bill_above_limit.sum()
)


print("\n========== ADDITIONAL CHECKS COMPLETE ==========")

# ============================================================
# 15. COMPLETE
# ============================================================

print("\n========== INSPECTION COMPLETE ==========")