from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.api.database import get_db_connection
from src.api.security.jwt_handler import decode_access_token


bearer_scheme = HTTPBearer(auto_error=False)


def authentication_error():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    )
) -> dict:
    """
    Validate JWT and retrieve the current active user.

    User permissions are determined from the database,
    not from the role stored in the JWT.
    """

    if credentials is None:
        raise authentication_error()

    if credentials.scheme.lower() != "bearer":
        raise authentication_error()

    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise authentication_error()

    user_id = int(payload["sub"])

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
                role,
                is_active
            FROM app_users
            WHERE user_id = %s
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user is None or not user["is_active"]:
            raise authentication_error()

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