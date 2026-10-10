import getpass

from mysql.connector import IntegrityError

from src.api.database import get_db_connection
from src.api.security.password import hash_password


def create_admin():
    print("\nBanking Application - Initial Admin Setup")
    print("-----------------------------------------")

    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()

    password = getpass.getpass("Admin password: ")
    confirm_password = getpass.getpass(
        "Confirm password: "
    )

    if not username or not email:
        print("Username and email are required.")
        return

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    password_hash = hash_password(password)

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM app_users
            WHERE role = 'ADMIN'
            """
        )

        existing_admins = cursor.fetchone()[0]

        if existing_admins > 0:
            print(
                "An admin account already exists. "
                "Initial admin setup is disabled."
            )
            return

        cursor.execute(
            """
            INSERT INTO app_users (
                username,
                email,
                password_hash,
                role,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                username,
                email,
                password_hash,
                "ADMIN",
                True
            )
        )

        connection.commit()

        print("\nAdmin account created successfully.")
        print(f"Username: {username}")
        print("Role: ADMIN")

    except IntegrityError:
        if connection:
            connection.rollback()
        print("Username or email already exists.")

    except Exception as error:
        if connection:
            connection.rollback()
        print(f"Admin creation failed: {error}")

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


if __name__ == "__main__":
    create_admin()