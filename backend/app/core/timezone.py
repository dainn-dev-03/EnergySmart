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


def local_now() -> datetime:
    return datetime.now(APP_TIMEZONE)


def month_start(day: date) -> date:
    return day.replace(day=1)


def add_months(day: date, months: int) -> date:
    """First day of the month `months` away from `day`'s month."""
    month_index = day.year * 12 + day.month - 1 + months
    return date(month_index // 12, month_index % 12 + 1, 1)
