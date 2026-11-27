"""Authentication and user Pydantic schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import normalize_email, validate_password_byte_length
from app.schemas.types import UtcDatetime


class UserRegister(BaseModel):
    """Payload to register a new TriVault user."""

    email: EmailStr
    password: str = Field(min_length=8)
    annual_inflation_rate: Decimal = Field(
        default=Decimal("2.50"),
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
    )

    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower_email(cls, value: object) -> object:
        """Trim surrounding spaces and lowercase email before EmailStr validation."""
        if isinstance(value, str):
            return normalize_email(value)
        return value

    @field_validator("password")
    @classmethod
    def check_bcrypt_byte_limit(cls, value: str) -> str:
        """Reject passwords exceeding bcrypt's 72-byte UTF-8 limit."""
        validate_password_byte_length(value)
        return value


class UserLogin(BaseModel):
    """Payload to authenticate an existing user."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email", mode="before")
    @classmethod
    def strip_and_lower_email(cls, value: object) -> object:
        """Trim surrounding spaces and lowercase email before lookup."""
        if isinstance(value, str):
            return normalize_email(value)
        return value


class UserOut(BaseModel):
    """Public user representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    annual_inflation_rate: Decimal
    created_at: UtcDatetime


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
