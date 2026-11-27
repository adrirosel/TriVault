"""Account service with strict user_id ownership isolation and deletion guards."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.fund import FundPosition
from app.models.transaction import Transaction
from app.schemas.account import AccountCreate, AccountUpdate


class AccountNotFoundError(Exception):
    """Raised when an account does not exist or does not belong to the user."""


class AccountHasHistoryError(Exception):
    """Raised when attempting to delete an account with linked movements or positions."""


def list_accounts(db: Session, user_id: int) -> list[Account]:
    """Return all accounts owned by the authenticated user."""
    stmt = (
        select(Account)
        .where(Account.user_id == user_id)
        .order_by(Account.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_account_for_user(db: Session, account_id: int, user_id: int) -> Account:
    """Fetch a single account scoped strictly to user_id."""
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id)
    account = db.scalar(stmt)
    if account is None:
        raise AccountNotFoundError("Cuenta no encontrada.")
    return account


def create_account(db: Session, user_id: int, payload: AccountCreate) -> Account:
    """Create a new liquidity bucket account with Decimal initial balance."""
    account = Account(
        user_id=user_id,
        name=payload.name,
        bucket_type=payload.bucket_type,
        current_balance=payload.initial_balance,
        currency=payload.currency,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(
    db: Session,
    account_id: int,
    user_id: int,
    payload: AccountUpdate,
) -> Account:
    """Update allowed account attributes (name, bucket_type) for the owning user."""
    account = get_account_for_user(db, account_id, user_id)
    if payload.name is not None:
        account.name = payload.name
    if payload.bucket_type is not None:
        account.bucket_type = payload.bucket_type

    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: int, user_id: int) -> None:
    """Delete an account only if owned by the user and free of historical records."""
    account = get_account_for_user(db, account_id, user_id)

    has_transactions = db.scalar(
        select(Transaction.id)
        .where(
            Transaction.user_id == user_id,
            or_(
                Transaction.account_id == account_id,
                Transaction.destination_account_id == account_id,
            ),
        )
        .limit(1)
    )
    has_positions = db.scalar(
        select(FundPosition.id)
        .where(
            FundPosition.user_id == user_id,
            FundPosition.account_id == account_id,
        )
        .limit(1)
    )
    if has_transactions is not None or has_positions is not None:
        raise AccountHasHistoryError(
            "No se puede eliminar una cuenta con movimientos o posiciones asociadas."
        )

    db.delete(account)
    db.commit()
