"""Category CRUD routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.category_service import (
    CategoryConflictError,
    CategoryHasTransactionsError,
    CategoryNotFoundError,
    create_category,
    delete_category,
    get_category_for_user,
    list_categories,
    update_category,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def read_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Category]:
    return list_categories(db, current_user.id)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_user_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Category:
    try:
        return create_category(db, current_user.id, payload)
    except CategoryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{category_id}", response_model=CategoryOut)
def read_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Category:
    try:
        return get_category_for_user(db, category_id, current_user.id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{category_id}", response_model=CategoryOut)
def patch_category(
    category_id: int,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Category:
    try:
        return update_category(db, category_id, current_user.id, payload)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_category(db, category_id, current_user.id)
    except CategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CategoryHasTransactionsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
