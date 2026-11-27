"""Fund position and contribution schemas (Decimal precision matches the SQL columns)."""

import re
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import OrderType
from app.schemas.types import UtcDatetime

_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
_SHARES = {"max_digits": 12, "decimal_places": 4}
_NAV = {"max_digits": 12, "decimal_places": 4}
_MONEY = {"max_digits": 12, "decimal_places": 2}


def isin_is_valid(isin: str) -> bool:
    """ISO 6166: format + Luhn check digit over the letters-to-digits expansion."""
    if not _ISIN_RE.match(isin):
        return False
    digits = "".join(str(int(ch, 36)) for ch in isin[:-1])
    total = 0
    for index, ch in enumerate(reversed(digits)):
        value = int(ch)
        if index % 2 == 0:  # rightmost digit of the payload gets doubled
            value *= 2
            if value > 9:
                value -= 9
        total += value
    return (10 - total % 10) % 10 == int(isin[-1])


def _clean_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("El nombre del fondo no puede estar vacío.")
    return cleaned


class FundPositionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: int
    isin: str = Field(min_length=12, max_length=12)
    fund_name: str = Field(min_length=1, max_length=150)
    current_nav: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), **_NAV)

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not isin_is_valid(cleaned):
            raise ValueError("ISIN no válido (formato o dígito de control incorrecto).")
        return cleaned

    @field_validator("fund_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return _clean_name(value)


class FundPositionUpdate(BaseModel):
    """Only metadata and the manually updated NAV. Shares and invested capital derive from contributions."""

    model_config = ConfigDict(extra="forbid")

    fund_name: str | None = Field(default=None, min_length=1, max_length=150)
    current_nav: Decimal | None = Field(default=None, gt=Decimal("0"), **_NAV)

    @field_validator("fund_name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        return None if value is None else _clean_name(value)


class FundPositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    isin: str
    fund_name: str
    shares: Decimal
    total_invested: Decimal
    current_nav: Decimal
    last_updated: UtcDatetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def market_value(self) -> Decimal:
        return (self.shares * self.current_nav).quantize(Decimal("0.01"))


class FundContributionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_date: date
    order_type: OrderType
    shares: Decimal = Field(gt=Decimal("0"), **_SHARES)
    purchase_nav: Decimal = Field(gt=Decimal("0"), **_NAV)
    gross_amount: Decimal = Field(gt=Decimal("0"), **_MONEY)
    fee: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), **_MONEY)
    notes: str | None = Field(default=None, max_length=255)
    affects_cash: bool = True

    @field_validator("operation_date")
    @classmethod
    def not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La fecha de la operación no puede ser futura.")
        return value


class FundContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fund_position_id: int
    operation_date: date
    order_type: OrderType
    shares: Decimal
    purchase_nav: Decimal
    gross_amount: Decimal
    fee: Decimal
    notes: str | None
    affects_cash: bool
    created_at: UtcDatetime
