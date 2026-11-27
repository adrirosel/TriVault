"""Read-only analytics endpoints for the dashboard."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import CashflowOut, FundsOut, InflationOut, SummaryOut
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Zona horaria no válida.") from exc


@router.get("/summary", response_model=SummaryOut)
def read_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> SummaryOut:
    return analytics_service.summary(db, current_user.id)


@router.get("/cashflow", response_model=CashflowOut)
def read_cashflow(
    date_from: datetime | None = Query(default=None, description="Inclusivo; por defecto inicio del mes local"),
    date_to: datetime | None = Query(default=None, description="Exclusivo; por defecto inicio del mes siguiente"),
    tz: str = Query(default="Europe/Madrid", description="Zona IANA para agrupar por mes"),
    months: int = Query(default=6, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CashflowOut:
    zone = _zone(tz)
    for value in (date_from, date_to):
        if value is not None and value.tzinfo is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="date_from/date_to deben incluir zona horaria (ISO 8601).",
            )
    if date_from and date_to and date_from >= date_to:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_from debe ser anterior a date_to.")
    return analytics_service.cashflow(db, current_user.id, tz=zone, date_from=date_from, date_to=date_to, months=months)


@router.get("/inflation", response_model=InflationOut)
def read_inflation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> InflationOut:
    return analytics_service.inflation(db, current_user)


@router.get("/funds", response_model=FundsOut)
def read_funds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FundsOut:
    return analytics_service.funds(db, current_user)
