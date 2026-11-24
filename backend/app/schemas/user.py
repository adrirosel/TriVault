"""User profile update schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    annual_inflation_rate: Decimal = Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
        max_digits=5,
        decimal_places=2,
    )
