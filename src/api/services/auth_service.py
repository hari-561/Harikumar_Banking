from src.api.database import get_db_connection
from src.api.security.password import verify_password


def authenticate_user(username: str, password: str):
    """
    Authenticate an active application user.

    Returns user information if valid.
    Returns None for invalid credentials or inactive accounts.
    """

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                user_id,
                username,
                email,
                password_hash,
                role,
                is_active
            FROM app_users
            WHERE username = %s
            LIMIT 1
            """,
            (username,)
        )

        user = cursor.fetchone()

        if user is None:
            return None

        if not verify_password(
            password,
            user["password_hash"]
        ):
            return None

        if not user["is_active"]:
            return None

        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()