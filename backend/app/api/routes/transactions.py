"""Transaction CRUD routes with atomic balance updates."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from app.services.transaction_service import (
    AccountNotFoundOrForbiddenError,
    CategoryForbiddenError,
    TransactionNotFoundError,
    TransactionRuleError,
    create_transaction,
    delete_transaction,
    get_transaction_for_user,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])

_NOT_FOUND_ERRORS = (TransactionNotFoundError, AccountNotFoundOrForbiddenError, CategoryForbiddenError)


def _to_http(exc: Exception) -> HTTPException:
    """Map domain errors to HTTP: foreign/missing resources -> 404 (never 403), rule violations -> 422."""
    if isinstance(exc, _NOT_FOUND_ERRORS):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("", response_model=list[TransactionOut])
def read_transactions(
    account_id: int | None = Query(default=None, description="Origen o destino"),
    date_from: datetime | None = Query(default=None, description="Inclusivo (ISO 8601, con zona)"),
    date_to: datetime | None = Query(default=None, description="Exclusivo (ISO 8601, con zona)"),
    type: TransactionType | None = Query(default=None),
    category_id: int | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    return list_transactions(
        db,
        current_user.id,
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        tx_type=type,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_user_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return create_transaction(db, current_user.id, payload)
    except (*_NOT_FOUND_ERRORS, TransactionRuleError) as exc:
        raise _to_http(exc) from exc


@router.get("/{tx_id}", response_model=TransactionOut)
def read_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return get_transaction_for_user(db, tx_id, current_user.id)
    except TransactionNotFoundError as exc:
        raise _to_http(exc) from exc


@router.patch("/{tx_id}", response_model=TransactionOut)
def patch_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return update_transaction(db, tx_id, current_user.id, payload)
    except (*_NOT_FOUND_ERRORS, TransactionRuleError) as exc:
        raise _to_http(exc) from exc


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_transaction(db, tx_id, current_user.id)
    except _NOT_FOUND_ERRORS as exc:
        raise _to_http(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
