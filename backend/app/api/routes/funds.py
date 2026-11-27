"""Fund positions and contributions, scoped to the authenticated user."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.fund import FundContribution, FundPosition
from app.models.user import User
from app.schemas.fund import (
    FundContributionCreate,
    FundContributionOut,
    FundPositionCreate,
    FundPositionOut,
    FundPositionUpdate,
)
from app.services import fund_service
from app.services._uow import AccountNotFoundOrForbiddenError
from app.services.fund_service import (
    ContributionNotFoundError,
    FundConflictError,
    FundNotFoundError,
    FundRuleError,
)

router = APIRouter(prefix="/funds", tags=["funds"])

_DOMAIN_ERRORS = (
    FundNotFoundError,
    ContributionNotFoundError,
    AccountNotFoundOrForbiddenError,
    FundRuleError,
    FundConflictError,
)


def _to_http(exc: Exception) -> HTTPException:
    """Foreign or missing -> 404 (never 403); rule violation -> 422; duplicate/blocked -> 409."""
    if isinstance(exc, FundRuleError):
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, FundConflictError):
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_404_NOT_FOUND
    return HTTPException(status_code=code, detail=str(exc))


@router.get("", response_model=list[FundPositionOut])
def read_positions(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FundPosition]:
    return fund_service.list_positions(db, current_user.id)


@router.post("", response_model=FundPositionOut, status_code=status.HTTP_201_CREATED)
def create_position(
    payload: FundPositionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FundPosition:
    try:
        return fund_service.create_position(db, current_user.id, payload)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc


@router.get("/{position_id}", response_model=FundPositionOut)
def read_position(
    position_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FundPosition:
    try:
        return fund_service.get_position(db, position_id, current_user.id)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc


@router.patch("/{position_id}", response_model=FundPositionOut)
def update_position(
    position_id: int,
    payload: FundPositionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FundPosition:
    try:
        return fund_service.update_position(db, position_id, current_user.id, payload)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    try:
        fund_service.delete_position(db, position_id, current_user.id)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{position_id}/contributions", response_model=list[FundContributionOut])
def read_contributions(
    position_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[FundContribution]:
    try:
        return fund_service.list_contributions(db, position_id, current_user.id)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc


@router.post(
    "/{position_id}/contributions",
    response_model=FundContributionOut,
    status_code=status.HTTP_201_CREATED,
)
def add_contribution(
    position_id: int,
    payload: FundContributionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FundContribution:
    try:
        return fund_service.add_contribution(db, position_id, current_user.id, payload)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc


@router.delete("/{position_id}/contributions/{contribution_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contribution(
    position_id: int,
    contribution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        fund_service.delete_contribution(db, position_id, contribution_id, current_user.id)
    except _DOMAIN_ERRORS as exc:
        raise _to_http(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
