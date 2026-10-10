from src.api.database import get_db_connection


def test_connection():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT DATABASE();"
        )

        database_name = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM customers;"
        )

        customer_count = cursor.fetchone()[0]

        print("Database connection: SUCCESS")
        print("Database:", database_name)
        print("Customers:", customer_count)

    except Exception as error:

        print("Database connection: FAILED")
        print("Error:", error)

        raise

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

            print("Database connection closed.")


if __name__ == "__main__":
    test_connection()