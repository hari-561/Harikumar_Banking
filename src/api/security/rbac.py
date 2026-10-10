from fastapi import Depends, HTTPException, status

from src.api.security.dependencies import get_current_user
from src.utils.logger import setup_logger

VALID_ROLES = frozenset({
    "ADMIN",
    "ANALYST",
    "VIEWER"
})
logger = setup_logger("banking.security")

def require_roles(*allowed_roles: str):
    """
    Reusable FastAPI dependency for role-based access control.

    Example:
        Depends(require_roles("ADMIN"))
    """

    if not allowed_roles:
        raise ValueError(
            "At least one allowed role must be specified."
        )

    if not set(allowed_roles).issubset(VALID_ROLES):
        raise ValueError(
            "One or more unsupported roles were specified."
        )

    def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:

        if current_user["role"] not in allowed_roles:

            logger.warning(
        "Access denied | user_id=%s | role=%s | required_roles=%s",
        current_user["user_id"],
        current_user["role"],
        ",".join(allowed_roles)
    )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action."
            )

        return current_user

    return role_checker