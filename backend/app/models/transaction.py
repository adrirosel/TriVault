"""Transaction ORM model."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import TransactionType, portable_enum


class Transaction(Base):
    """Income, expense, or internal transfer movement."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
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
    destination_account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[TransactionType] = mapped_column(
        portable_enum(TransactionType, "transaction_type_enum"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    import_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user = relationship("User", back_populates="transactions")
    account = relationship(
        "Account",
        foreign_keys=[account_id],
        back_populates="outgoing_transactions",
    )
    destination_account = relationship(
        "Account",
        foreign_keys=[destination_account_id],
        back_populates="incoming_transactions",
    )
    category = relationship("Category", back_populates="transactions")
