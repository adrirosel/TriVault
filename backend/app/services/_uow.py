"""Shared helpers for atomic, multi-row money operations (transactions and fund contributions)."""

from collections.abc import Iterable, Iterator
from contextlib import contextmanager

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.account import Account


class AccountNotFoundOrForbiddenError(Exception):
    """Account does not exist or belongs to another user (mapped to 404, never 403)."""


@contextmanager
def unit_of_work(db: Session) -> Iterator[None]:
    """Commit on success, roll back explicitly on any failure."""
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise


def lock_accounts(db: Session, account_ids: Iterable[int | None], user_id: int) -> dict[int, Account]:
    """Lock all given accounts owned by user_id in ascending id order (no deadlocks) and return them by id."""
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
