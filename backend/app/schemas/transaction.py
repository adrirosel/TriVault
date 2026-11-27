"""Transaction Pydantic schemas with strict financial precision and business-rule validation."""


from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TransactionType
from app.schemas.types import UtcDatetime

_AMOUNT_CONSTRAINTS = {"gt": Decimal("0"), "max_digits": 12, "decimal_places": 2}


def validate_transaction_shape(
    tx_type: TransactionType,
    account_id: int,
    category_id: int | None,
    destination_account_id: int | None,
) -> None:
    """Enforce the rules that tie a transaction type to its category and destination account.

    Shared by create and update so both paths apply exactly the same invariants.
    Raises ValueError (mapped to 422) when the combination is invalid.
    """
    if tx_type == TransactionType.TRANSFER:
        if destination_account_id is None:
            raise ValueError("Las transferencias requieren destination_account_id.")
        if destination_account_id == account_id:
            raise ValueError("La cuenta de destino debe ser diferente a la de origen.")
        if category_id is not None:
            raise ValueError("Las transferencias no pueden tener una categoría.")
    else:
        if category_id is None:
            raise ValueError("Los ingresos y gastos requieren category_id.")
        if destination_account_id is not None:
            raise ValueError("Solo las transferencias pueden tener destination_account_id.")


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: int
    amount: Decimal = Field(**_AMOUNT_CONSTRAINTS)
    type: TransactionType
    description: str | None = Field(default=None, max_length=255)
    transaction_date: UtcDatetime

    # Required for income/expense; forbidden for transfer.
    category_id: int | None = None
    # Required for transfer; forbidden for income/expense.
    destination_account_id: int | None = None

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "TransactionCreate":
        validate_transaction_shape(
            self.type, self.account_id, self.category_id, self.destination_account_id
        )
        return self


class TransactionUpdate(BaseModel):
    """Partial update. Only fields explicitly sent are changed (see ``model_fields_set``).

    Sending ``null`` for ``category_id`` / ``destination_account_id`` clears them, which is
    required when switching between transfer and income/expense. The final shape is
    validated in the service after merging with the stored transaction.
    """

    model_config = ConfigDict(extra="forbid")

    account_id: int | None = None
    destination_account_id: int | None = None
    category_id: int | None = None
    type: TransactionType | None = None
    amount: Decimal | None = Field(default=None, **_AMOUNT_CONSTRAINTS)
    description: str | None = Field(default=None, max_length=255)
    transaction_date: UtcDatetime | None = None

    @model_validator(mode="after")
    def reject_null_required_fields(self) -> "TransactionUpdate":
        for name in ("account_id", "type", "amount", "transaction_date"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"El campo {name} no puede ser nulo.")
        return self


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
    transaction_date: UtcDatetime
    import_hash: str | None
    created_at: UtcDatetime
