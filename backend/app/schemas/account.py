"""Account Pydantic schemas enforcing Decimal precision and balance invariants."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BucketType


class AccountCreate(BaseModel):
    """Payload to create a new bucket account."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    bucket_type: BucketType
    initial_balance: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
    )
    currency: str = Field(default="EUR", min_length=3, max_length=3)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Trim surrounding whitespace and reject blank account names."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El nombre de la cuenta no puede estar vacío.")
        return cleaned

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize ISO currency code to uppercase."""
        cleaned = value.strip().upper()
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("La divisa debe ser un código ISO de 3 letras (p. ej. EUR).")
        return cleaned


class AccountUpdate(BaseModel):
    """Payload to update mutable account metadata without altering balances directly."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    bucket_type: BucketType | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        """Trim surrounding whitespace and reject blank account names."""
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("El nombre de la cuenta no puede estar vacío.")
        return cleaned


class AccountOut(BaseModel):
    """Account representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    bucket_type: BucketType
    current_balance: Decimal
    currency: str
    created_at: datetime
