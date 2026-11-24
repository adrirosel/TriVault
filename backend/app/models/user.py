"""User ORM model."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Registered TriVault user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    annual_inflation_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("2.50"),
        server_default="2.50",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    fund_positions = relationship("FundPosition", back_populates="user", cascade="all, delete-orphan")
    fund_contributions = relationship(
        "FundContribution", back_populates="user", cascade="all, delete-orphan"
    )
