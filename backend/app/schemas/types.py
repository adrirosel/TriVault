"""Shared Pydantic field types."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator


def _as_utc(value: datetime) -> datetime:
    """Normalize to timezone-aware UTC.

    MySQL DATETIME stores no timezone, so values read back are naive but represent UTC.
    Incoming values with an offset are converted to UTC; naive inputs are assumed UTC.
    Serializing with an explicit offset prevents browsers from reading them as local time.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
