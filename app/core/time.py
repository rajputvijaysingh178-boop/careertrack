"""OWNER: ALL - UTC timestamps stored as naive datetimes for existing DB compatibility."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_utc(value: datetime | None) -> datetime | None:
    """Normalize incoming aware timestamps to the project's naive UTC DB convention."""
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)
