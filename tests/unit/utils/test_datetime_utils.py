"""Tests for datetime utility functions."""

from datetime import UTC, datetime, timedelta, timezone

from finwiz.infrastructure.time.datetime_utils import ensure_utc_aware, normalize_to_naive


class TestNormalizeToNaive:
    """Test suite for normalize_to_naive function."""

    def test_should_convert_aware_utc_datetime_to_naive(self):
        """Test converting UTC-aware datetime to naive."""
        # Arrange
        aware_dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)

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
        assert result.tzinfo == UTC
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
        assert result.tzinfo == UTC
        # 12:00 PST = 20:00 UTC
        assert result.hour == 20
        assert result.day == 15

    def test_should_keep_utc_aware_datetime_unchanged(self):
        """Test that UTC-aware datetime remains UTC."""
        # Arrange
        utc_dt = datetime(2025, 1, 15, 12, 30, 45, tzinfo=UTC)

        # Act
        result = ensure_utc_aware(utc_dt)

        # Assert
        assert result.tzinfo == UTC
        assert result == utc_dt

    def test_should_handle_various_timezones(self):
        """Test handling of various timezone offsets."""
        # Arrange - CET is UTC+1
        cet = timezone(timedelta(hours=1))
        aware_dt = datetime(2025, 1, 15, 13, 0, 0, tzinfo=cet)

        # Act
        result = ensure_utc_aware(aware_dt)

        # Assert
        assert result.tzinfo == UTC
        # 13:00 CET = 12:00 UTC
        assert result.hour == 12
        assert result.day == 15


class TestAssumeLocalAware:
    """The sibling of ensure_utc_aware, and the reason it exists.

    Everything else in this module reads a naive datetime as UTC.
    ``FinwizState.timestamp`` is naive *local* wall clock, so passing it to
    ``ensure_utc_aware`` mislabels it and the resulting duration is wrong by the
    local offset -- negative east of UTC. That is how a 23-minute run was once
    measured as -5819 seconds and judged un-gradeable.
    """

    def test_a_naive_value_is_read_as_local_not_utc(self) -> None:
        import os
        import time
        from datetime import datetime

        from finwiz.infrastructure.time.datetime_utils import assume_local_aware, ensure_utc_aware

        previous = os.environ.get("TZ")
        os.environ["TZ"] = "Europe/Paris"
        time.tzset()
        try:
            naive = datetime(2026, 1, 15, 12, 0, 0)  # winter: Paris is UTC+1

            local = assume_local_aware(naive)
            utc = ensure_utc_aware(naive)

            assert local.utcoffset().total_seconds() == 3600
            assert utc.utcoffset().total_seconds() == 0
            # The whole point: the two helpers disagree by the local offset.
            assert local != utc
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_it_uses_the_offset_in_force_then_not_today(self) -> None:
        """A span crossing a DST boundary must stay correct in absolute time."""
        import os
        import time
        from datetime import datetime

        from finwiz.infrastructure.time.datetime_utils import assume_local_aware

        previous = os.environ.get("TZ")
        os.environ["TZ"] = "Europe/Paris"
        time.tzset()
        try:
            winter = assume_local_aware(datetime(2026, 1, 15, 12, 0, 0))
            summer = assume_local_aware(datetime(2026, 7, 15, 12, 0, 0))

            assert winter.utcoffset().total_seconds() == 3600  # CET
            assert summer.utcoffset().total_seconds() == 7200  # CEST
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_an_aware_value_is_returned_unchanged(self) -> None:
        from datetime import UTC, datetime

        from finwiz.infrastructure.time.datetime_utils import assume_local_aware

        aware = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

        assert assume_local_aware(aware) is aware
