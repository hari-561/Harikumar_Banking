import os

from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError


load_dotenv()


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must contain at least 32 characters."
    )

if JWT_ALGORITHM != "HS256":
    raise RuntimeError(
        "Only HS256 is supported by this application."
    )

if JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive."
    )


def create_access_token(
    user_id: int,
    username: str,
    role: str
) -> str:
    """
    Generate a signed JWT access token.
    """

    now = datetime.now(timezone.utc)

    expiration = now + timedelta(
        minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "nbf": now,
        "exp": expiration,
        "type": "access"
    }

    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

    return token


def decode_access_token(token: str) -> dict | None:
    """
    Validate the JWT signature and required claims.

    Returns the payload when valid, otherwise None.
    """

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={
                "require": [
                    "sub",
                    "iat",
                    "nbf",
                    "exp",
                    "type"
                ]
            }
        )

        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")

        if not isinstance(user_id, str) or not user_id.isdigit():
            return None

        if int(user_id) <= 0:
            return None

        return payload

    except (InvalidTokenError, TypeError, ValueError):
        return None