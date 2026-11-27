"""Account ORM model representing the three liquidity buckets."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BucketType, portable_enum


class Account(Base):
    """User financial account assigned to a liquidity bucket."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bucket_type: Mapped[BucketType] = mapped_column(
        portable_enum(BucketType, "bucket_type_enum"),
        nullable=False,
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="EUR",
        server_default="EUR",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user = relationship("User", back_populates="accounts")
    outgoing_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.account_id",
        back_populates="account",
    )
    incoming_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.destination_account_id",
        back_populates="destination_account",
    )
    fund_positions = relationship("FundPosition", back_populates="account")
