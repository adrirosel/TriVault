"""Transaction Pydantic schemas with strict financial precision and business-rule validation."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import TransactionType


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: int
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    type: TransactionType
    description: str | None = Field(default=None, max_length=255)
    transaction_date: datetime

    # Required for income/expense; forbidden for transfer.
    category_id: int | None = None
    # Required for transfer; forbidden for income/expense.
    destination_account_id: int | None = None

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "TransactionCreate":
        """Enforce business rules that tie type to category and destination account."""
        if self.type == TransactionType.TRANSFER:
            if self.destination_account_id is None:
                raise ValueError(
                    "Las transferencias requieren destination_account_id."
                )
            if self.destination_account_id == self.account_id:
                raise ValueError(
                    "La cuenta de destino debe ser diferente a la de origen."
                )
            if self.category_id is not None:
                raise ValueError(
                    "Las transferencias no pueden tener una categoría."
                )
        else:
            if self.category_id is None:
                raise ValueError(
                    "Los ingresos y gastos requieren category_id."
                )
            if self.destination_account_id is not None:
                raise ValueError(
                    "Solo las transferencias pueden tener destination_account_id."
                )
        return self


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(default=None, max_length=255)
    transaction_date: datetime | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    account_id: int
    destination_account_id: int | None
    category_id: int | None
    amount: Decimal
    type: TransactionType
    description: str | None
    transaction_date: datetime
    import_hash: str | None
    created_at: datetime
