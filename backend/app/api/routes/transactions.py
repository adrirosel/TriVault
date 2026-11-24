"""Transaction CRUD routes with atomic balance updates."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionCreate, TransactionOut, TransactionUpdate
from app.services.transaction_service import (
    AccountNotFoundOrForbiddenError,
    CategoryForbiddenError,
    TransactionNotFoundError,
    create_transaction,
    delete_transaction,
    get_transaction_for_user,
    list_transactions,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def read_transactions(
    account_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Transaction]:
    return list_transactions(db, current_user.id, account_id=account_id)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_user_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return create_transaction(db, current_user.id, payload)
    except (AccountNotFoundOrForbiddenError, CategoryForbiddenError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{tx_id}", response_model=TransactionOut)
def read_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return get_transaction_for_user(db, tx_id, current_user.id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{tx_id}", response_model=TransactionOut)
def patch_transaction(
    tx_id: int,
    payload: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Transaction:
    try:
        return update_transaction(db, tx_id, current_user.id, payload)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(
    tx_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_transaction(db, tx_id, current_user.id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except AccountNotFoundOrForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
