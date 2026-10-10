from typing import Literal

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    password: str = Field(
        ...,
        min_length=1
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user_id: int
    username: str
    role: Literal["ADMIN", "ANALYST", "VIEWER"]


class CurrentUserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: Literal["ADMIN", "ANALYST", "VIEWER"]