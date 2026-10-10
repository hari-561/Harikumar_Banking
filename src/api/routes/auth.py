from fastapi import APIRouter, HTTPException, status
from src.utils.logger import setup_logger
from src.api.security.auth_schemas import (
    LoginRequest,
    LoginResponse
)
from src.utils.logger import setup_logger

from src.api.security.jwt_handler import (
    create_access_token,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES
)

from src.api.services.auth_service import (
    authenticate_user
)

from fastapi import Depends

from src.api.security.dependencies import get_current_user

from src.api.security.auth_schemas import CurrentUserResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)
logger = setup_logger("banking.auth")



@router.post(
    "/login",
    response_model=LoginResponse
)
def login(request: LoginRequest):

    user = authenticate_user(
        username=request.username,
        password=request.password
    )

    if user is None:

        logger.warning(
            "Login failed | reason=invalid_credentials_or_inactive_account"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            }
        )

    access_token = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"]
    )

    logger.info(
        "Login successful | user_id=%s | role=%s",
        user["user_id"],
        user["role"]
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in":
            JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"]
    }



@router.get(
    "/me",
    response_model=CurrentUserResponse
)
def get_authenticated_user(
    current_user: dict = Depends(get_current_user)
):
    """
    Return the currently authenticated user's profile.
    """

    return current_user