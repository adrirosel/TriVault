"""Category service with strict user_id isolation."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryNotFoundError(Exception):
    """Raised when a category does not exist or does not belong to the user."""


class CategoryConflictError(Exception):
    """Raised when a duplicate name+type combination is detected."""


class CategoryHasTransactionsError(Exception):
    """Raised when attempting to delete a category that has linked transactions."""


def list_categories(db: Session, user_id: int) -> list[Category]:
    stmt = select(Category).where(Category.user_id == user_id).order_by(Category.id.asc())
    return list(db.scalars(stmt).all())


def get_category_for_user(db: Session, category_id: int, user_id: int) -> Category:
    stmt = select(Category).where(Category.id == category_id, Category.user_id == user_id)
    category = db.scalar(stmt)
    if category is None:
        raise CategoryNotFoundError("Categoría no encontrada.")
    return category


def create_category(db: Session, user_id: int, payload: CategoryCreate) -> Category:
    category = Category(
        user_id=user_id,
        name=payload.name,
        type=payload.type,
        is_fixed=payload.is_fixed,
    )
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryConflictError(
            "Ya existe una categoría con ese nombre y tipo."
        ) from exc
    db.refresh(category)
    return category


def update_category(
    db: Session, category_id: int, user_id: int, payload: CategoryUpdate
) -> Category:
    category = get_category_for_user(db, category_id, user_id)
    if payload.name is not None:
        category.name = payload.name
    if payload.is_fixed is not None:
        category.is_fixed = payload.is_fixed
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CategoryConflictError(
            "Ya existe una categoría con ese nombre y tipo."
        ) from exc
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int, user_id: int) -> None:
    category = get_category_for_user(db, category_id, user_id)
    has_transactions = db.scalar(
        select(Transaction.id)
        .where(Transaction.user_id == user_id, Transaction.category_id == category_id)
        .limit(1)
    )
    if has_transactions is not None:
        raise CategoryHasTransactionsError(
            "No se puede eliminar una categoría con transacciones asociadas."
        )
    db.delete(category)
    db.commit()
