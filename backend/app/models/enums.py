"""Domain enums stored portably across MySQL and PostgreSQL."""

from enum import Enum

from sqlalchemy import Enum as SAEnum


class BucketType(str, Enum):
    """Capital segmentation buckets."""

    DAILY = "daily"
    EMERGENCY = "emergency"
    INVESTMENT = "investment"


class CategoryType(str, Enum):
    """Cashflow category direction."""

    INCOME = "income"
    EXPENSE = "expense"


class TransactionType(str, Enum):
    """Financial movement types."""

    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"


class OrderType(str, Enum):
    """Fund contribution operation direction."""

    BUY = "buy"
    SELL = "sell"


def portable_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """Create a non-native VARCHAR+CHECK enum portable between MySQL and PostgreSQL."""
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        length=32,
        values_callable=lambda obj: [member.value for member in obj],
    )
