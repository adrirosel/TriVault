"""Fund positions and contributions.

Design:
- A position's ``shares`` and ``total_invested`` are never written by the client: they are always
  rebuilt by replaying every contribution in chronological order (average-cost method), so
  back-dated operations and deletions stay exact and a sell can never exceed the shares held.
- The investment account balance is the broker's cash: a buy debits ``gross + fee`` and a sell
  credits ``gross - fee`` (unless ``affects_cash`` is False for historical positions).
- Everything runs in one unit of work with the account and position rows locked.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import BucketType, OrderType
from app.models.fund import FundContribution, FundPosition
from app.schemas.fund import FundContributionCreate, FundPositionCreate, FundPositionUpdate
from app.services._uow import AccountNotFoundOrForbiddenError, lock_accounts, unit_of_work

CENT = Decimal("0.01")
ZERO = Decimal("0")


class FundNotFoundError(Exception):
    pass


class ContributionNotFoundError(Exception):
    pass


class FundRuleError(Exception):
    """Business-rule violation -> 422."""


class FundConflictError(Exception):
    """Duplicate position or deletion blocked by history -> 409."""


@dataclass(frozen=True)
class PositionState:
    shares: Decimal
    total_invested: Decimal


def replay_contributions(contributions: list[FundContribution]) -> PositionState:
    """Rebuild a position from its contributions (oldest first, average-cost method)."""
    shares = ZERO
    invested = ZERO
    for c in sorted(contributions, key=lambda item: (item.operation_date, item.id or 0)):
        if c.order_type == OrderType.BUY:
            shares += c.shares
            invested += c.gross_amount + c.fee
        else:
            if c.shares > shares:
                raise FundRuleError(
                    f"La venta del {c.operation_date:%d/%m/%Y} supera las participaciones disponibles en esa fecha."
                )
            cost_removed = (invested * c.shares / shares).quantize(CENT, ROUND_HALF_EVEN)
            shares -= c.shares
            invested = ZERO if shares == 0 else invested - cost_removed
    return PositionState(shares=shares, total_invested=invested)


def cash_effect(contribution: FundContribution | FundContributionCreate) -> Decimal:
    """Signed change to the investment account cash for this contribution."""
    if not contribution.affects_cash:
        return ZERO
    if contribution.order_type == OrderType.BUY:
        return -(contribution.gross_amount + contribution.fee)
    return contribution.gross_amount - contribution.fee


# --------------------------------------------------------------------------- positions

def list_positions(db: Session, user_id: int) -> list[FundPosition]:
    stmt = select(FundPosition).where(FundPosition.user_id == user_id).order_by(FundPosition.id)
    return list(db.scalars(stmt).all())


def get_position(db: Session, position_id: int, user_id: int, *, lock: bool = False) -> FundPosition:
    stmt = select(FundPosition).where(FundPosition.id == position_id, FundPosition.user_id == user_id)
    if lock:
        stmt = stmt.with_for_update()
    position = db.scalar(stmt)
    if position is None:
        raise FundNotFoundError("Fondo no encontrado.")
    return position


def create_position(db: Session, user_id: int, payload: FundPositionCreate) -> FundPosition:
    account = db.scalar(select(Account).where(Account.id == payload.account_id, Account.user_id == user_id))
    if account is None:
        raise AccountNotFoundOrForbiddenError("Cuenta no encontrada o no pertenece al usuario.")
    if account.bucket_type != BucketType.INVESTMENT:
        raise FundRuleError("Los fondos solo pueden asociarse a cuentas de tipo inversión.")

    position = FundPosition(
        user_id=user_id,
        account_id=payload.account_id,
        isin=payload.isin,
        fund_name=payload.fund_name,
        current_nav=payload.current_nav,
    )
    db.add(position)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FundConflictError("Ya existe una posición con ese ISIN en esta cuenta.") from exc
    db.refresh(position)
    return position


def update_position(db: Session, position_id: int, user_id: int, payload: FundPositionUpdate) -> FundPosition:
    position = get_position(db, position_id, user_id)
    if payload.fund_name is not None:
        position.fund_name = payload.fund_name
    if payload.current_nav is not None:
        position.current_nav = payload.current_nav
        position.last_updated = datetime.now(UTC)
    db.commit()
    db.refresh(position)
    return position


def delete_position(db: Session, position_id: int, user_id: int) -> None:
    position = get_position(db, position_id, user_id)
    has_history = db.scalar(
        select(FundContribution.id).where(FundContribution.fund_position_id == position.id).limit(1)
    )
    if has_history is not None:
        raise FundConflictError("No se puede eliminar un fondo con aportaciones registradas.")
    db.delete(position)
    db.commit()


# --------------------------------------------------------------------------- contributions

def _contributions_of(db: Session, position_id: int) -> list[FundContribution]:
    stmt = select(FundContribution).where(FundContribution.fund_position_id == position_id)
    return list(db.scalars(stmt).all())


def list_contributions(db: Session, position_id: int, user_id: int) -> list[FundContribution]:
    get_position(db, position_id, user_id)
    stmt = (
        select(FundContribution)
        .where(FundContribution.fund_position_id == position_id, FundContribution.user_id == user_id)
        .order_by(FundContribution.operation_date.desc(), FundContribution.id.desc())
    )
    return list(db.scalars(stmt).all())


def _apply_position_state(position: FundPosition, contributions: list[FundContribution]) -> None:
    state = replay_contributions(contributions)
    position.shares = state.shares
    position.total_invested = state.total_invested


def add_contribution(
    db: Session, position_id: int, user_id: int, payload: FundContributionCreate
) -> FundContribution:
    if payload.order_type == OrderType.SELL and payload.fee > payload.gross_amount:
        raise FundRuleError("La comisión de una venta no puede superar el importe bruto.")

    with unit_of_work(db):
        position = get_position(db, position_id, user_id, lock=True)
        account = lock_accounts(db, [position.account_id], user_id)[position.account_id]

        delta = cash_effect(payload)
        if delta < 0 and account.current_balance + delta < 0:
            raise FundRuleError(
                "Saldo insuficiente en la cuenta de inversión para esta compra "
                "(marca 'posición histórica' si ya la tenías antes de usar TriVault)."
            )

        contribution = FundContribution(user_id=user_id, fund_position_id=position.id, **payload.model_dump())
        db.add(contribution)
        db.flush()  # assign id for deterministic ordering in the replay

        _apply_position_state(position, _contributions_of(db, position.id))
        account.current_balance += delta
        if position.current_nav == 0:
            position.current_nav = payload.purchase_nav
            position.last_updated = datetime.now(UTC)

    db.refresh(contribution)
    return contribution


def delete_contribution(db: Session, position_id: int, contribution_id: int, user_id: int) -> None:
    with unit_of_work(db):
        position = get_position(db, position_id, user_id, lock=True)
        contribution = db.scalar(
            select(FundContribution).where(
                FundContribution.id == contribution_id,
                FundContribution.fund_position_id == position.id,
                FundContribution.user_id == user_id,
            )
        )
        if contribution is None:
            raise ContributionNotFoundError("Aportación no encontrada.")
        account = lock_accounts(db, [position.account_id], user_id)[position.account_id]

        remaining = [c for c in _contributions_of(db, position.id) if c.id != contribution.id]
        _apply_position_state(position, remaining)  # raises if a later sell becomes uncovered
        account.current_balance -= cash_effect(contribution)
        db.delete(contribution)
