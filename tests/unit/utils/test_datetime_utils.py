"""Tests for datetime utility functions."""

from datetime import datetime, timezone, timedelta
import pytest
from finwiz.utils.datetime_utils import normalize_to_naive, ensure_utc_aware


class TestNormalizeToNaive:
    """Test suite for normalize_to_naive function."""

    def test_should_convert_aware_utc_datetime_to_naive(self):
        """Test converting UTC-aware datetime to naive."""
        # Arrange
        aware_dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)

        # Act
        result = normalize_to_naive(aware_dt)

        # Assert
        assert result.tzinfo is None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_should_convert_aware_non_utc_datetime_to_naive_utc(self):
        """Test converting non-UTC aware datetime to naive UTC."""
        # Arrange - EST is UTC-5
        est = timezone(timedelta(hours=-5))
        aware_dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=est)

        # Act
        result = normalize_to_naive(aware_dt)

        # Assert
        assert result.tzinfo is None
        # 12:00 EST = 17:00 UTC
        assert result.hour == 17
        assert result.day == 15

    def test_should_return_naive_datetime_unchanged(self):
        """Test that naive datetime is returned as-is."""
        # Arrange
        naive_dt = datetime(2025, 1, 15, 12, 30, 45)

        # Act
        result = normalize_to_naive(naive_dt)

        # Assert
        assert result.tzinfo is None
        assert result == naive_dt

    def test_should_handle_various_timezones(self):
        """Test handling of various timezone offsets."""
        # Arrange - JST is UTC+9
        jst = timezone(timedelta(hours=9))
        aware_dt = datetime(2025, 1, 15, 21, 0, 0, tzinfo=jst)

        # Act
        result = normalize_to_naive(aware_dt)

        # Assert
        assert result.tzinfo is None
        # 21:00 JST = 12:00 UTC
        assert result.hour == 12
        assert result.day == 15


class TestEnsureUtcAware:
    """Test suite for ensure_utc_aware function."""

    def test_should_make_naive_datetime_utc_aware(self):
        """Test making naive datetime UTC-aware."""
        # Arrange
        naive_dt = datetime(2025, 1, 15, 12, 30, 45)

        # Act
        result = ensure_utc_aware(naive_dt)

        # Assert
        assert result.tzinfo == timezone.utc
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 12
        assert result.minute == 30
        assert result.second == 45

    def test_should_convert_non_utc_aware_to_utc(self):
        """Test converting non-UTC aware datetime to UTC."""
        # Arrange - PST is UTC-8
        pst = timezone(timedelta(hours=-8))
        aware_dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=pst)

        # Act
        result = ensure_utc_aware(aware_dt)

        # Assert
        assert result.tzinfo == timezone.utc
        # 12:00 PST = 20:00 UTC
        assert result.hour == 20
        assert result.day == 15

    def test_should_keep_utc_aware_datetime_unchanged(self):
        """Test that UTC-aware datetime remains UTC."""
        # Arrange
        utc_dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=timezone.utc)

        # Act
        result = ensure_utc_aware(utc_dt)

        # Assert
        assert result.tzinfo == timezone.utc
        assert result == utc_dt

    def test_should_handle_various_timezones(self):
        """Test handling of various timezone offsets."""
        # Arrange - CET is UTC+1
        cet = timezone(timedelta(hours=1))
        aware_dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=cet)

        # Act
        result = ensure_utc_aware(aware_dt)

        # Assert
        assert result.tzinfo == timezone.utc
        # 13:00 CET = 12:00 UTC
        assert result.hour == 12
        assert result.day == 15
