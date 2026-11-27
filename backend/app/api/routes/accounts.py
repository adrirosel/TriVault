"""Account CRUD routes scoped strictly to the authenticated user."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.account import AccountCreate, AccountOut, AccountUpdate
from app.services.account_service import (
    AccountHasHistoryError,
    AccountNotFoundError,
    create_account,
    delete_account,
    get_account_for_user,
    list_accounts,
    update_account,
)

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def read_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Account]:
    """List all accounts belonging to the authenticated user."""
    return list_accounts(db, current_user.id)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_user_account(
    payload: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """Create a new account in one of the three liquidity buckets."""
    return create_account(db, current_user.id, payload)


@router.get("/{account_id}", response_model=AccountOut)
def read_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """Retrieve a single account owned by the authenticated user."""
    try:
        return get_account_for_user(db, account_id, current_user.id)
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch("/{account_id}", response_model=AccountOut)
def patch_account(
    account_id: int,
    payload: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Account:
    """Update account name or bucket type without modifying balance directly."""
    try:
        return update_account(db, account_id, current_user.id, payload)
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete an account if it has no associated transactions or fund positions."""
    try:
        delete_account(db, account_id, current_user.id)
    except AccountNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AccountHasHistoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
