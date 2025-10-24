"""
Date parsing, formatting, and validation utilities for general use.

Supports both naive and timezone-aware datetime operations.
By default, returns naive datetimes (no tzinfo) unless a timezone is specified.

Example usage:
    >>> from profile_analysis.common.date_utils import parse_date
    >>> parse_date("2025-01-01")
    datetime.datetime(2025, 1, 1, 0, 0)
    >>> parse_date("30d", tz=timezone.utc)
    datetime.datetime(2024, 12, 2, 0, 0, tzinfo=datetime.timezone.utc)
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

# ---------------------------------------------------------------------------
# Core date parsing
# ---------------------------------------------------------------------------

def parse_date(date_str: str, tz: Optional[timezone] = None) -> datetime:
    """
    Parse a date string into a datetime object.

    Supports absolute dates (YYYY-MM-DD, YYYY-MM, YYYY, ISO8601)
    and relative dates ("30d", "6m", "1y" ago). Optionally attaches a timezone.
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError(f"Invalid date string: {date_str}")

    date_str = date_str.strip()

    # --- Relative date (e.g., "30d", "6m", "1y")
    match = re.match(r'^(\d+)([dmy])$', date_str.lower())
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        return calculate_relative_date(datetime.now(tz=tz), f"{amount}{unit}")

    # --- ISO 8601 (e.g., 2025-01-01T12:00:00Z)
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.astimezone(tz) if tz else dt
    except ValueError:
        pass

    # --- Absolute date formats
    for fmt in ['%Y-%m-%d', '%Y-%m', '%Y']:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.replace(tzinfo=tz) if tz else dt
        except ValueError:
            continue

    raise ValueError(
        f"Unable to parse date string: '{date_str}'. "
        "Supported: YYYY-MM-DD, YYYY-MM, YYYY, ISO8601, or Nd/Nm/Ny."
    )


# ---------------------------------------------------------------------------
# Relative date handling
# ---------------------------------------------------------------------------

def calculate_relative_date(base_date: datetime, offset: str) -> datetime:
    """Calculate a date relative to a base date (e.g., '30d', '2m', '1y')."""
    offset = offset.strip().lower()
    match = re.match(r'^(\d+)([dmy])$', offset)
    if not match:
        raise ValueError(f"Invalid offset format: '{offset}' (use Nd/Nm/Ny)")

    amount, unit = int(match[1]), match[2]
    if unit == 'd':
        return base_date - timedelta(days=amount)
    elif unit == 'm':
        return base_date - timedelta(days=amount * 30)
    elif unit == 'y':
        return base_date - timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported unit: {unit}")


# ---------------------------------------------------------------------------
# Validation and range utilities
# ---------------------------------------------------------------------------

def validate_date_range(start_date: Optional[datetime], end_date: Optional[datetime]) -> bool:
    """Validate that a date range is logical (start <= end)."""
    if start_date is None or end_date is None:
        return True

    if start_date.tzinfo and end_date.tzinfo:
        start_date = start_date.astimezone(timezone.utc)
        end_date = end_date.astimezone(timezone.utc)

    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")
    return True


def is_within_range(dt: datetime, start: datetime, end: datetime) -> bool:
    """Return True if dt is between start and end (inclusive)."""
    return start <= dt <= end


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def ensure_naive(dt: datetime) -> datetime:
    """Return a naive (timezone-free) datetime."""
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def ensure_utc(dt: datetime) -> datetime:
    """Return a timezone-aware datetime in UTC."""
    if dt.tzinfo:
        return dt.astimezone(timezone.utc)
    return dt.replace(tzinfo=timezone.utc)


def datetime_to_str(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convert datetime to a formatted string."""
    return dt.strftime(fmt)


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def now_local() -> datetime:
    """Return current local datetime."""
    return datetime.now()


# ---------------------------------------------------------------------------
# Quick, safe converters
# ---------------------------------------------------------------------------

def to_datetime_safe(date_str: str, tz: Optional[timezone] = None) -> datetime | None:
    """Safely convert a date string to a datetime, returning None on failure."""
    try:
        return parse_date(date_str, tz=tz)
    except ValueError:
        return None


def parse_date_range(
    start_str: str | None,
    end_str: str | None,
    tz: Optional[timezone] = None,
    allow_none: bool = True
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse and validate a date range (start, end) from string inputs.
    Returns a tuple of datetimes or None if missing.
    """
    start_dt = to_datetime_safe(start_str, tz=tz) if start_str else None
    end_dt = to_datetime_safe(end_str, tz=tz) if end_str else None

    if not allow_none and (start_dt is None or end_dt is None):
        raise ValueError("Both start and end dates are required.")

    if start_dt and end_dt:
        validate_date_range(start_dt, end_dt)

    return start_dt, end_dt
