from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from etl.extract import extract_data
from etl.transform import transform_data
from etl.prepare_tables import prepare_risk_assessments
from etl.load import get_connection, load_risk_assessments
from rules.risk_rules import apply_risk_rules


FILE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "default_of_credit_card_clients.xls"
)


def main():

    connection = None
    cursor = None

    try:
        print("Loading source data...")
        raw_data = extract_data(FILE_PATH)

        print("Transforming data...")
        transformed_data = transform_data(raw_data)

        print("Applying risk rules...")
        risk_data = apply_risk_rules(
            transformed_data
        )

        print("Preparing risk assessments...")
        risk_assessments = prepare_risk_assessments(
            risk_data
        )

        print(
            "Risk assessments prepared:",
            len(risk_assessments)
        )

        connection = get_connection()
        cursor = connection.cursor()

        print("Loading risk assessments...")

        load_risk_assessments(
            cursor,
            risk_assessments
        )

        connection.commit()

        print(
            "Risk assessment transaction committed."
        )

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "Risk assessment transaction rolled back."
        )

        print(
            f"ERROR: {error}"
        )

        raise

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

            print(
                "MySQL connection closed."
            )


if __name__ == "__main__":
    main()