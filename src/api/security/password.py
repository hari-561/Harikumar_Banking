from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Generate a secure Argon2 password hash."""

    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty")

    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """Verify a plaintext password against its hash."""

    try:
        return password_hasher.verify(
            plain_password,
            hashed_password
        )
    except (ValueError, TypeError):
        return False