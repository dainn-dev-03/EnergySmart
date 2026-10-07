"""Local business timezone helpers. Timestamps are stored in UTC; days follow APP_TIMEZONE."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings

APP_TIMEZONE = ZoneInfo(settings.app_timezone)


def ensure_aware(moment: datetime) -> datetime:
    """Interpret naive datetimes as local business time."""
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=APP_TIMEZONE)


def local_date(moment: datetime) -> date:
    return ensure_aware(moment).astimezone(APP_TIMEZONE).date()


def local_day_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=APP_TIMEZONE)


def local_day_end_exclusive(day: date) -> datetime:
    return local_day_start(day + timedelta(days=1))
