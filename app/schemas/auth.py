from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if not all(c.isalnum() or c in ("-", "_", ".") for c in cleaned):
            raise ValueError("Username may only contain letters, numbers, hyphens, underscores, and dots")
        return cleaned

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: int
    username: str
    role: str
    full_name: str | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=16)
