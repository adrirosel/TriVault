"""Transaction service: atomic balance updates inside a single DB transaction."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionNotFoundError(Exception):
    pass


class AccountNotFoundOrForbiddenError(Exception):
    pass


class CategoryForbiddenError(Exception):
    pass


def _fetch_account_owned_by(db: Session, account_id: int, user_id: int) -> Account:
    """Return account only if it belongs to user_id, else raise."""
    stmt = select(Account).where(Account.id == account_id, Account.user_id == user_id).with_for_update()
    account = db.scalar(stmt)
    if account is None:
        raise AccountNotFoundOrForbiddenError(
            f"Cuenta {account_id} no encontrada o no pertenece al usuario."
        )
    return account


def _verify_category_owned_by(db: Session, category_id: int, user_id: int) -> None:
    from app.models.category import Category
    stmt = select(Category.id).where(Category.id == category_id, Category.user_id == user_id)
    if db.scalar(stmt) is None:
        raise CategoryForbiddenError(
            f"Categoría {category_id} no encontrada o no pertenece al usuario."
        )


def _apply_balance_delta(account: Account, delta: Decimal) -> None:
    account.current_balance = (account.current_balance or Decimal("0.00")) + delta


def list_transactions(
    db: Session,
    user_id: int,
    account_id: int | None = None,
) -> list[Transaction]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    stmt = stmt.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    return list(db.scalars(stmt).all())


def get_transaction_for_user(db: Session, tx_id: int, user_id: int) -> Transaction:
    stmt = select(Transaction).where(
        Transaction.id == tx_id, Transaction.user_id == user_id
    )
    tx = db.scalar(stmt)
    if tx is None:
        raise TransactionNotFoundError("Transacción no encontrada.")
    return tx


def create_transaction(db: Session, user_id: int, payload: TransactionCreate) -> Transaction:
    """Create a transaction and atomically update account balances inside one commit."""
    source = _fetch_account_owned_by(db, payload.account_id, user_id)

    if payload.category_id is not None:
        _verify_category_owned_by(db, payload.category_id, user_id)

    tx = Transaction(
        user_id=user_id,
        account_id=payload.account_id,
        amount=payload.amount,
        type=payload.type,
        description=payload.description,
        transaction_date=payload.transaction_date,
        category_id=payload.category_id,
        destination_account_id=payload.destination_account_id,
    )
    db.add(tx)

    if payload.type == TransactionType.INCOME:
        _apply_balance_delta(source, payload.amount)
    elif payload.type == TransactionType.EXPENSE:
        _apply_balance_delta(source, -payload.amount)
    elif payload.type == TransactionType.TRANSFER:
        dest = _fetch_account_owned_by(db, payload.destination_account_id, user_id)
        _apply_balance_delta(source, -payload.amount)
        _apply_balance_delta(dest, payload.amount)

    db.commit()
    db.refresh(tx)
    return tx


def update_transaction(
    db: Session, tx_id: int, user_id: int, payload: TransactionUpdate
) -> Transaction:
    """Update only metadata fields (description, date). Amount changes must go through delete+create."""
    tx = get_transaction_for_user(db, tx_id, user_id)
    if payload.description is not None:
        tx.description = payload.description
    if payload.transaction_date is not None:
        tx.transaction_date = payload.transaction_date
    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, tx_id: int, user_id: int) -> None:
    """Delete a transaction and reverse its balance impact atomically."""
    tx = get_transaction_for_user(db, tx_id, user_id)

    source = _fetch_account_owned_by(db, tx.account_id, user_id)

    if tx.type == TransactionType.INCOME:
        _apply_balance_delta(source, -tx.amount)
    elif tx.type == TransactionType.EXPENSE:
        _apply_balance_delta(source, tx.amount)
    elif tx.type == TransactionType.TRANSFER:
        dest = _fetch_account_owned_by(db, tx.destination_account_id, user_id)
        _apply_balance_delta(source, tx.amount)
        _apply_balance_delta(dest, -tx.amount)

    db.delete(tx)
    db.commit()
