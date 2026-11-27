"""Fund position and contribution ORM models."""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import OrderType, portable_enum


class FundPosition(Base):
    """Indexed fund holding linked to an investment account."""

    __tablename__ = "fund_positions"
    __table_args__ = (
        UniqueConstraint("user_id", "account_id", "isin", name="uq_fund_positions_user_account_isin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    fund_name: Mapped[str] = mapped_column(String(150), nullable=False)
    shares: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0.0000",
    )
    total_invested: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    current_nav: Mapped[Decimal] = mapped_column(
        Numeric(12, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0.0000",
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user = relationship("User", back_populates="fund_positions")
    account = relationship("Account", back_populates="fund_positions")
    contributions = relationship(
        "FundContribution",
        back_populates="fund_position",
        cascade="all, delete-orphan",
    )


class FundContribution(Base):
    """Individual buy/sell contribution for accurate fund performance and inflation tracking."""

    __tablename__ = "fund_contributions"
    __table_args__ = (
        CheckConstraint("shares > 0", name="ck_fund_contributions_shares_positive"),
        CheckConstraint("purchase_nav > 0", name="ck_fund_contributions_nav_positive"),
        CheckConstraint("gross_amount > 0", name="ck_fund_contributions_gross_positive"),
        CheckConstraint("fee >= 0", name="ck_fund_contributions_fee_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fund_position_id: Mapped[int] = mapped_column(
        ForeignKey("fund_positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_date: Mapped[date] = mapped_column(Date, nullable=False)
    order_type: Mapped[OrderType] = mapped_column(
        portable_enum(OrderType, "order_type_enum"),
        nullable=False,
    )
    shares: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    purchase_nav: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fee: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # False for historical positions bought before using TriVault: no cash is moved.
    affects_cash: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user = relationship("User", back_populates="fund_contributions")
    fund_position = relationship("FundPosition", back_populates="contributions")
