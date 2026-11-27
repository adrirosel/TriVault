"""Financial analytics (CONTEXT.md §6). Read-only; every query is scoped to user_id.

- Cash flow and savings rate exclude internal transfers.
- Inflation erosion applies the user's annual rate to liquid money (daily + emergency).
- Fund real return compares market value with the invested capital grown by inflation
  from each contribution date (average-cost method, same as the position replay).
"""

from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import BucketType, OrderType, TransactionType
from app.models.fund import FundContribution, FundPosition
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.analytics import (
    BucketTotal,
    CashflowOut,
    CategoryTotal,
    FundPerformance,
    FundsOut,
    InflationOut,
    MonthTotal,
    SummaryOut,
)

CENT = Decimal("0.01")
ZERO = Decimal("0")
HUNDRED = Decimal("100")
DAYS_PER_YEAR = Decimal("365.25")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, ROUND_HALF_EVEN)


def pct(part: Decimal, whole: Decimal) -> Decimal | None:
    return None if whole == 0 else money(part / whole * HUNDRED)


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None)


def month_start(moment: datetime, tz: ZoneInfo) -> datetime:
    local = moment.astimezone(tz)
    return local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def add_months(start: datetime, months: int) -> datetime:
    """Shift a local month start by N months (keeps tzinfo, recomputes DST offset)."""
    index = start.year * 12 + (start.month - 1) + months
    return start.replace(year=index // 12, month=index % 12 + 1)


# --------------------------------------------------------------------------- summary

def _market_values_by_account(db: Session, user_id: int) -> dict[int, Decimal]:
    values: dict[int, Decimal] = defaultdict(lambda: ZERO)
    for position in db.scalars(select(FundPosition).where(FundPosition.user_id == user_id)):
        values[position.account_id] += position.shares * position.current_nav
    return {account_id: money(value) for account_id, value in values.items()}


def summary(db: Session, user_id: int) -> SummaryOut:
    accounts = list(db.scalars(select(Account).where(Account.user_id == user_id)))
    funds_by_account = _market_values_by_account(db, user_id)
    buckets: list[BucketTotal] = []
    for bucket in BucketType:
        in_bucket = [a for a in accounts if a.bucket_type == bucket]
        cash = sum((a.current_balance for a in in_bucket), ZERO)
        funds = sum((funds_by_account.get(a.id, ZERO) for a in in_bucket), ZERO)
        buckets.append(
            BucketTotal(
                bucket_type=bucket,
                total=money(cash + funds),
                cash=money(cash),
                funds_value=money(funds),
                accounts=len(in_bucket),
            )
        )
    return SummaryOut(net_worth=money(sum((b.total for b in buckets), ZERO)), buckets=buckets)


# --------------------------------------------------------------------------- cash flow

def cashflow(
    db: Session,
    user_id: int,
    *,
    tz: ZoneInfo,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    months: int = 6,
    now: datetime | None = None,
) -> CashflowOut:
    now = now or datetime.now(UTC)
    current_month = month_start(now, tz)
    start = date_from or current_month
    end = date_to or add_months(current_month, 1)

    base = (
        Transaction.user_id == user_id,
        Transaction.type.in_([TransactionType.INCOME, TransactionType.EXPENSE]),
    )
    in_period = (Transaction.transaction_date >= _naive_utc(start), Transaction.transaction_date < _naive_utc(end))

    totals = {
        tx_type: amount or ZERO
        for tx_type, amount in db.execute(
            select(Transaction.type, func.sum(Transaction.amount)).where(*base, *in_period).group_by(Transaction.type)
        )
    }
    income = money(totals.get(TransactionType.INCOME, ZERO))
    expense = money(totals.get(TransactionType.EXPENSE, ZERO))

    by_category = [
        CategoryTotal(category_id=cid, name=name, type=ctype, is_fixed=is_fixed, total=money(total))
        for cid, name, ctype, is_fixed, total in db.execute(
            select(Category.id, Category.name, Category.type, Category.is_fixed, func.sum(Transaction.amount))
            .join(Category, Category.id == Transaction.category_id)
            .where(*base, *in_period, Category.user_id == user_id)
            .group_by(Category.id, Category.name, Category.type, Category.is_fixed)
            .order_by(func.sum(Transaction.amount).desc())
        )
    ]
    fixed = sum((c.total for c in by_category if c.type.value == "expense" and c.is_fixed), ZERO)

    # Monthly series: group in Python by local month (portable, no DB-specific date functions).
    series_start = add_months(current_month, -(months - 1))
    rows = db.execute(
        select(Transaction.transaction_date, Transaction.type, Transaction.amount).where(
            *base,
            Transaction.transaction_date >= _naive_utc(series_start),
            Transaction.transaction_date < _naive_utc(add_months(current_month, 1)),
        )
    )
    buckets: dict[str, dict[TransactionType, Decimal]] = {
        add_months(series_start, i).strftime("%Y-%m"): defaultdict(lambda: ZERO) for i in range(months)
    }
    for moment, tx_type, amount in rows:
        key = moment.replace(tzinfo=UTC).astimezone(tz).strftime("%Y-%m")
        if key in buckets:
            buckets[key][tx_type] += amount
    monthly = [
        MonthTotal(
            month=key,
            income=money(values[TransactionType.INCOME]),
            expense=money(values[TransactionType.EXPENSE]),
            net=money(values[TransactionType.INCOME] - values[TransactionType.EXPENSE]),
        )
        for key, values in buckets.items()
    ]

    return CashflowOut(
        date_from=start,
        date_to=end,
        timezone=tz.key,
        income=income,
        expense=expense,
        net=money(income - expense),
        savings_rate=pct(income - expense, income),
        fixed_expense=money(fixed),
        variable_expense=money(expense - fixed),
        by_category=by_category,
        monthly=monthly,
    )


# --------------------------------------------------------------------------- inflation

def inflation(db: Session, user: User) -> InflationOut:
    liquid = db.scalar(
        select(func.sum(Account.current_balance)).where(
            Account.user_id == user.id,
            Account.bucket_type.in_([BucketType.DAILY, BucketType.EMERGENCY]),
        )
    ) or ZERO
    rate = user.annual_inflation_rate
    annual = liquid * rate / HUNDRED
    return InflationOut(
        annual_inflation_rate=rate,
        liquid_balance=money(liquid),
        annual_loss=money(annual),
        monthly_loss=money(annual / 12),
    )


# --------------------------------------------------------------------------- funds

def inflation_factor(rate: Decimal, start: date, today: date) -> Decimal:
    """(1 + r)^(years held), years with fractional precision."""
    years = Decimal(max((today - start).days, 0)) / DAYS_PER_YEAR
    return (Decimal(1) + rate / HUNDRED) ** years


def _performance(position: FundPosition, contributions: list[FundContribution], rate: Decimal, today: date) -> FundPerformance:
    shares = ZERO
    invested = ZERO
    adjusted = ZERO
    for c in sorted(contributions, key=lambda item: (item.operation_date, item.id)):
        if c.order_type == OrderType.BUY:
            cost = c.gross_amount + c.fee
            shares += c.shares
            invested += cost
            adjusted += cost * inflation_factor(rate, c.operation_date, today)
        elif shares > 0:
            fraction = c.shares / shares
            invested -= invested * fraction
            adjusted -= adjusted * fraction
            shares -= c.shares

    market_value = money(position.shares * position.current_nav)
    invested_m = money(position.total_invested)
    adjusted_m = money(adjusted)
    real_gain = market_value - adjusted_m
    return FundPerformance(
        position_id=position.id,
        isin=position.isin,
        fund_name=position.fund_name,
        shares=position.shares,
        current_nav=position.current_nav,
        market_value=market_value,
        invested=invested_m,
        nominal_gain=market_value - invested_m,
        nominal_return_pct=pct(market_value - invested_m, invested_m),
        inflation_adjusted_cost=adjusted_m,
        accumulated_inflation_pct=pct(adjusted_m - invested_m, invested_m),
        real_gain=real_gain,
        real_return_pct=pct(real_gain, adjusted_m),
        beats_inflation=None if adjusted_m == 0 else market_value > adjusted_m,
        first_operation=min((c.operation_date for c in contributions), default=None),
    )


def funds(db: Session, user: User, today: date | None = None) -> FundsOut:
    today = today or date.today()
    rate = user.annual_inflation_rate
    positions = list(db.scalars(select(FundPosition).where(FundPosition.user_id == user.id).order_by(FundPosition.id)))
    contributions: dict[int, list[FundContribution]] = defaultdict(list)
    for c in db.scalars(select(FundContribution).where(FundContribution.user_id == user.id)):
        contributions[c.fund_position_id].append(c)

    perf = [_performance(p, contributions[p.id], rate, today) for p in positions]
    market = sum((p.market_value for p in perf), ZERO)
    invested = sum((p.invested for p in perf), ZERO)
    adjusted = sum((p.inflation_adjusted_cost for p in perf), ZERO)
    return FundsOut(
        annual_inflation_rate=rate,
        positions=perf,
        market_value=market,
        invested=invested,
        nominal_gain=market - invested,
        nominal_return_pct=pct(market - invested, invested),
        inflation_adjusted_cost=adjusted,
        real_gain=market - adjusted,
        real_return_pct=pct(market - adjusted, adjusted),
        beats_inflation=None if adjusted == 0 else market > adjusted,
    )
