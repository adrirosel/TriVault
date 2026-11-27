"""Analytics response schemas. Money is Decimal quantized to cents; percentages to 2 decimals."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import BucketType, CategoryType
from app.schemas.types import UtcDatetime


class BucketTotal(BaseModel):
    bucket_type: BucketType
    total: Decimal
    cash: Decimal
    funds_value: Decimal
    accounts: int


class SummaryOut(BaseModel):
    net_worth: Decimal
    buckets: list[BucketTotal]


class CategoryTotal(BaseModel):
    category_id: int
    name: str
    type: CategoryType
    is_fixed: bool
    total: Decimal


class MonthTotal(BaseModel):
    month: str  # YYYY-MM in the requested timezone
    income: Decimal
    expense: Decimal
    net: Decimal


class CashflowOut(BaseModel):
    date_from: UtcDatetime
    date_to: UtcDatetime  # exclusive
    timezone: str
    income: Decimal
    expense: Decimal
    net: Decimal
    savings_rate: Decimal | None  # None when there is no income in the period
    fixed_expense: Decimal
    variable_expense: Decimal
    by_category: list[CategoryTotal]
    monthly: list[MonthTotal]


class InflationOut(BaseModel):
    annual_inflation_rate: Decimal
    liquid_balance: Decimal  # daily + emergency
    annual_loss: Decimal
    monthly_loss: Decimal


class FundPerformance(BaseModel):
    position_id: int
    isin: str
    fund_name: str
    shares: Decimal
    current_nav: Decimal
    market_value: Decimal
    invested: Decimal
    nominal_gain: Decimal
    nominal_return_pct: Decimal | None
    inflation_adjusted_cost: Decimal
    accumulated_inflation_pct: Decimal | None
    real_gain: Decimal
    real_return_pct: Decimal | None
    beats_inflation: bool | None
    first_operation: date | None


class FundsOut(BaseModel):
    annual_inflation_rate: Decimal
    positions: list[FundPerformance]
    market_value: Decimal
    invested: Decimal
    nominal_gain: Decimal
    nominal_return_pct: Decimal | None
    inflation_adjusted_cost: Decimal
    real_gain: Decimal
    real_return_pct: Decimal | None
    beats_inflation: bool | None
