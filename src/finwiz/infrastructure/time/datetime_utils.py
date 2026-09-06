"""
Datetime utility functions for timezone handling.

This module provides utilities for normalizing datetime objects to ensure
consistent timezone handling across the FinWiz codebase.
"""

from datetime import UTC, datetime


def normalize_to_naive(dt: datetime) -> datetime:
    """
    Normalize a datetime object to a naive UTC datetime.

    This function handles both timezone-aware and naive datetime objects:
    - Aware datetimes are converted to UTC and made naive
    - Naive datetimes are assumed to be UTC and returned as-is

    Args:
        dt: The datetime object to normalize

    Returns:
        A naive datetime in UTC

    Examples:
        >>> from datetime import datetime, timezone
        >>> # Aware datetime
        >>> aware_dt = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> naive_dt = normalize_to_naive(aware_dt)
        >>> naive_dt.tzinfo is None
        True

        >>> # Naive datetime (assumed UTC)
        >>> naive_dt = datetime(2025, 1, 1, 12, 0)
        >>> result = normalize_to_naive(naive_dt)
        >>> result == naive_dt
        True

    """
    if dt.tzinfo is not None:
        # Aware datetime - convert to UTC and remove timezone info
        utc_dt = dt.astimezone(UTC)
        return utc_dt.replace(tzinfo=None)
    else:
        # Naive datetime - assume it's already UTC
        return dt


def ensure_utc_aware(dt: datetime) -> datetime:
    """
    Ensure a datetime object is timezone-aware in UTC.

    This function handles both timezone-aware and naive datetime objects:
    - Aware datetimes are converted to UTC
    - Naive datetimes are assumed to be UTC and made aware

    Args:
        dt: The datetime object to make UTC-aware

    Returns:
        A timezone-aware datetime in UTC

    Examples:
        >>> from datetime import datetime, timezone
        >>> # Naive datetime
        >>> naive_dt = datetime(2025, 1, 1, 12, 0)
        >>> aware_dt = ensure_utc_aware(naive_dt)
        >>> aware_dt.tzinfo == timezone.utc
        True

        >>> # Already aware datetime
        >>> aware_dt = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
        >>> result = ensure_utc_aware(aware_dt)
        >>> result.tzinfo == timezone.utc
        True

    """
    if dt.tzinfo is None:
        # Naive datetime - assume it's UTC and make it aware
        return dt.replace(tzinfo=UTC)
    else:
        # Aware datetime - convert to UTC
        return dt.astimezone(UTC)


def assume_local_aware(dt: datetime) -> datetime:
    """Make a datetime aware by reading a naive value as **local** wall clock.

    This is the sibling of :func:`ensure_utc_aware`, and the difference between
    them is the whole point of it existing. Everything else in this module
    follows the convention "naive means UTC". One value in the codebase does
    not: ``FinwizState.timestamp`` is written by ``datetime.now().strftime(...)``
    (``flow_state_models.py``), so its naive value means *local* time.

    Passing that stamp to :func:`ensure_utc_aware` silently mislabels it as UTC.
    Subtracting the result from a real UTC instant then yields a duration wrong
    by the local offset -- negative anywhere east of UTC, which is how a 23
    minute run was once measured as -5819 seconds and judged un-gradeable.

    A naive value is given the offset that was in force *at that moment*, not
    today's, so a span crossing a DST boundary is still correct in absolute
    time. An aware value is returned unchanged.
    """
    return dt.astimezone() if dt.tzinfo is None else dt
