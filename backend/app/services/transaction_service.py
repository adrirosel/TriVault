"""Transaction service: atomic balance updates inside a single DB transaction.

Every write path (create / update / delete) follows the same pattern:
1. Lock every affected account in ascending id order (deterministic -> no deadlocks
   between concurrent opposite transfers).
2. Revert and/or apply the balance effect of the movement.
3. Commit once. Any exception rolls the whole unit of work back explicitly.
"""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.category import Category
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    validate_transaction_shape,
)


class TransactionNotFoundError(Exception):
    pass


class AccountNotFoundOrForbiddenError(Exception):
    pass


class CategoryForbiddenError(Exception):
    pass


class TransactionRuleError(Exception):
    """Business-rule violation (category type mismatch, currency mismatch, invalid shape)."""


@contextmanager
def _unit_of_work(db: Session) -> Iterator[None]:
    """Commit on success, roll back explicitly on any failure."""
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise


def _lock_accounts(db: Session, account_ids: Iterable[int | None], user_id: int) -> dict[int, Account]:
    """Lock all given accounts owned by user_id (ordered by id) and return them by id."""
    ids = sorted({account_id for account_id in account_ids if account_id is not None})
    stmt = (
        select(Account)
        .where(Account.id.in_(ids), Account.user_id == user_id)
        .order_by(Account.id)
        .with_for_update()
    )
    accounts = {account.id: account for account in db.scalars(stmt).all()}
    missing = [account_id for account_id in ids if account_id not in accounts]
    if missing:
        raise AccountNotFoundOrForbiddenError(
            f"Cuenta {missing[0]} no encontrada o no pertenece al usuario."
        )
    return accounts


def _verify_category(db: Session, category_id: int, user_id: int, tx_type: TransactionType) -> None:
    """Category must belong to the user and match the movement direction (income/expense)."""
    stmt = select(Category.type).where(Category.id == category_id, Category.user_id == user_id)
    category_type = db.scalar(stmt)
    if category_type is None:
        raise CategoryForbiddenError(
            f"Categoría {category_id} no encontrada o no pertenece al usuario."
        )
    if category_type.value != tx_type.value:
        raise TransactionRuleError(
            "El tipo de la categoría no coincide con el tipo del movimiento."
        )


def _verify_same_currency(accounts: dict[int, Account], account_id: int, destination_id: int) -> None:
    if accounts[account_id].currency != accounts[destination_id].currency:
        raise TransactionRuleError("No se permiten transferencias entre cuentas de distinta divisa.")


def _apply_effect(
    accounts: dict[int, Account],
    tx_type: TransactionType,
    account_id: int,
    destination_id: int | None,
    amount: Decimal,
    sign: int,
) -> None:
    """Apply (sign=+1) or revert (sign=-1) the balance effect of a movement."""
    delta = amount * sign
    source = accounts[account_id]
    if tx_type == TransactionType.INCOME:
        source.current_balance += delta
    elif tx_type == TransactionType.EXPENSE:
        source.current_balance -= delta
    elif tx_type == TransactionType.TRANSFER:
        assert destination_id is not None
        source.current_balance -= delta
        accounts[destination_id].current_balance += delta


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
    stmt = select(Transaction).where(Transaction.id == tx_id, Transaction.user_id == user_id)
    tx = db.scalar(stmt)
    if tx is None:
        raise TransactionNotFoundError("Transacción no encontrada.")
    return tx


def create_transaction(db: Session, user_id: int, payload: TransactionCreate) -> Transaction:
    """Create a transaction and atomically update account balances inside one commit."""
    with _unit_of_work(db):
        accounts = _lock_accounts(db, [payload.account_id, payload.destination_account_id], user_id)
        if payload.category_id is not None:
            _verify_category(db, payload.category_id, user_id, payload.type)
        if payload.type == TransactionType.TRANSFER:
            _verify_same_currency(accounts, payload.account_id, payload.destination_account_id)

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
        _apply_effect(
            accounts, payload.type, payload.account_id, payload.destination_account_id, payload.amount, +1
        )

    db.refresh(tx)
    return tx


def update_transaction(
    db: Session, tx_id: int, user_id: int, payload: TransactionUpdate
) -> Transaction:
    """Update any field of a movement, reverting the old balance effect and applying the new one atomically."""
    tx = get_transaction_for_user(db, tx_id, user_id)
    changes = payload.model_dump(include=payload.model_fields_set)

    new_type: TransactionType = changes.get("type", tx.type)
    new_account_id: int = changes.get("account_id", tx.account_id)
    new_amount: Decimal = changes.get("amount", tx.amount)
    new_category_id: int | None = changes.get("category_id", tx.category_id)
    new_destination_id: int | None = changes.get("destination_account_id", tx.destination_account_id)

    try:
        validate_transaction_shape(new_type, new_account_id, new_category_id, new_destination_id)
    except ValueError as exc:
        raise TransactionRuleError(str(exc)) from exc

    with _unit_of_work(db):
        accounts = _lock_accounts(
            db,
            [tx.account_id, tx.destination_account_id, new_account_id, new_destination_id],
            user_id,
        )
        if new_category_id is not None:
            _verify_category(db, new_category_id, user_id, new_type)
        if new_type == TransactionType.TRANSFER:
            _verify_same_currency(accounts, new_account_id, new_destination_id)

        _apply_effect(accounts, tx.type, tx.account_id, tx.destination_account_id, tx.amount, -1)
        _apply_effect(accounts, new_type, new_account_id, new_destination_id, new_amount, +1)

        tx.type = new_type
        tx.account_id = new_account_id
        tx.amount = new_amount
        tx.category_id = new_category_id
        tx.destination_account_id = new_destination_id
        if "description" in changes:
            tx.description = changes["description"]
        if "transaction_date" in changes:
            tx.transaction_date = changes["transaction_date"]

    db.refresh(tx)
    return tx


def delete_transaction(db: Session, tx_id: int, user_id: int) -> None:
    """Delete a transaction and reverse its balance impact atomically."""
    tx = get_transaction_for_user(db, tx_id, user_id)
    with _unit_of_work(db):
        accounts = _lock_accounts(db, [tx.account_id, tx.destination_account_id], user_id)
        _apply_effect(accounts, tx.type, tx.account_id, tx.destination_account_id, tx.amount, -1)
        db.delete(tx)
