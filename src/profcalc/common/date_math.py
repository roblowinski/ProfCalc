# =============================================================================
# Date Mathematics and Time Calculations for Beach Profile Analysis
# =============================================================================
#
# FILE: src/profcalc/common/date_math.py
#
# PURPOSE:
# This module provides specialized date and time calculation utilities for
# beach profile monitoring and temporal analysis. It handles the complex
# time-based calculations needed for comparing survey dates, computing
# monitoring intervals, and formatting temporal information.
#
# WHAT IT'S FOR:
# - Calculating time differences between survey dates in various units
# - Date arithmetic operations (adding days, hours to datetimes)
# - Computing average dates from multiple survey timestamps
# - Rounding datetimes to nearest time intervals
# - Clipping dates within specified ranges
# - Determining leap years and days in year calculations
# - Formatting time durations as human-readable strings
#
# WORKFLOW POSITION:
# This module is essential for temporal analysis in beach profile monitoring
# workflows. It's used when comparing surveys across time, calculating
# monitoring frequencies, determining seasonal patterns, and presenting
# time-based results to users.
#
# LIMITATIONS:
# - All calculations assume Gregorian calendar
# - Timezone handling depends on input datetime objects
# - Leap year calculations follow standard Gregorian rules
# - Rounding operations are basic (nearest interval, not sophisticated)
# - Duration formatting is simplified for common use cases
#
# ASSUMPTIONS:
# - Input datetimes are valid and properly constructed
# - Users understand time units (days, hours, minutes, etc.)
# - Timezone information is consistent across related dates
# - Date ranges are reasonable (not spanning millennia)
# - Floating point precision is sufficient for time calculations
#
# =============================================================================

"""
Date math utilities for time difference and interval calculations.

Provides convenience functions for computing elapsed time between survey dates,
rounding, and formatting durations.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

# ---------------------------------------------------------------------------
# Time difference and arithmetic
# ---------------------------------------------------------------------------


def days_between(date1: datetime, date2: datetime, abs_value: bool = True) -> float:
    """Return the number of days between two datetime objects."""
    delta = date2 - date1
    days = delta.total_seconds() / 86400.0
    return abs(days) if abs_value else days


def hours_between(date1: datetime, date2: datetime, abs_value: bool = True) -> float:
    """Return the number of hours between two datetime objects."""
    delta = date2 - date1
    hours = delta.total_seconds() / 3600.0
    return abs(hours) if abs_value else hours


def minutes_between(date1: datetime, date2: datetime, abs_value: bool = True) -> float:
    """Return the number of minutes between two datetime objects."""
    delta = date2 - date1
    minutes = delta.total_seconds() / 60.0
    return abs(minutes) if abs_value else minutes


def weeks_between(date1: datetime, date2: datetime, abs_value: bool = True) -> float:
    """Return the number of weeks between two datetime objects."""
    return days_between(date1, date2, abs_value=abs_value) / 7.0


def time_difference(date1: datetime, date2: datetime) -> timedelta:
    """Return a timedelta representing the exact difference between two datetimes."""
    return date2 - date1


def add_days(date: datetime, days: float) -> datetime:
    """Return a new datetime offset by a given number of days."""
    return date + timedelta(days=days)


def add_hours(date: datetime, hours: float) -> datetime:
    """Return a new datetime offset by a given number of hours."""
    return date + timedelta(hours=hours)


# ---------------------------------------------------------------------------
# Higher-level operations
# ---------------------------------------------------------------------------


def average_datetime(dates: List[datetime]) -> datetime:
    """
    Compute the mean (average) datetime from a list of datetimes.
    """
    if not dates:
        raise ValueError("Date list cannot be empty.")
    avg_timestamp = sum(dt.timestamp() for dt in dates) / len(dates)
    return datetime.fromtimestamp(avg_timestamp, tz=dates[0].tzinfo)


def round_datetime(dt: datetime, interval: str = "hour") -> datetime:
    """
    Round a datetime to nearest 'minute', 'hour', or 'day'.
    """
    if interval == "minute":
        discard = timedelta(seconds=dt.second, microseconds=dt.microsecond)
        dt -= discard
        if discard >= timedelta(seconds=30):
            dt += timedelta(minutes=1)
    elif interval == "hour":
        discard = timedelta(
            minutes=dt.minute, seconds=dt.second, microseconds=dt.microsecond
        )
        dt -= discard
        if discard >= timedelta(minutes=30):
            dt += timedelta(hours=1)
    elif interval == "day":
        discard = timedelta(
            hours=dt.hour,
            minutes=dt.minute,
            seconds=dt.second,
            microseconds=dt.microsecond,
        )
        dt -= discard
        if discard >= timedelta(hours=12):
            dt += timedelta(days=1)
    else:
        raise ValueError("interval must be 'minute', 'hour', or 'day'")
    return dt


def clip_datetime(dt: datetime, start: datetime, end: datetime) -> datetime:
    """
    Clamp a datetime within a range [start, end].
    Returns nearest boundary if out of range.
    """
    return max(start, min(dt, end))


def days_in_year(year: int) -> int:
    """Return 365 or 366 depending on leap year."""
    return 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_duration(td: timedelta) -> str:
    """Format a timedelta as a human-readable string (e.g., '2d 5h 30m')."""
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0s"
