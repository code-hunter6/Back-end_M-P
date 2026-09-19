import re
import uuid

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import CamelModel


class UserOut(CamelModel):
    id: uuid.UUID
    name: str
    email: EmailStr


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return cleaned

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        # Mirrors the frontend rule (8+, letters and digits) so a user can't
        # bypass it by calling the API directly.
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain at least one letter and one number.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    """
    Field names stay snake_case here on purpose: the frontend's api.js reads
    data.access_token / data.refresh_token.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
