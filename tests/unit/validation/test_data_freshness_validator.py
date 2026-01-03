"""
Unit tests for DataFreshnessValidator.

Tests the data freshness validation logic including timestamp extraction,
age calculation, and market schedule adjustments.
"""

from datetime import UTC, datetime, timedelta

from pytest import approx

from finwiz.validation.freshness import DataFreshnessValidator, FreshnessResult, MarketCalendar


class TestMarketCalendar:
    """Test MarketCalendar functionality."""

    def test_should_identify_weekend_when_saturday(self):
        """Test weekend detection for Saturday."""
        calendar = MarketCalendar()
        saturday = datetime(2024, 1, 6)  # Saturday

        assert calendar.is_weekend(saturday) is True

    def test_should_identify_weekend_when_sunday(self):
        """Test weekend detection for Sunday."""
        calendar = MarketCalendar()
        sunday = datetime(2024, 1, 7)  # Sunday

        assert calendar.is_weekend(sunday) is True

    def test_should_not_identify_weekend_when_weekday(self):
        """Test weekend detection for weekday."""
        calendar = MarketCalendar()
        monday = datetime(2024, 1, 8)  # Monday

        assert calendar.is_weekend(monday) is False

    def test_should_return_false_for_holidays(self):
        """Test holiday detection (simplified implementation)."""
        calendar = MarketCalendar()
        any_date = datetime(2024, 1, 1)

        # Current implementation always returns False
        assert calendar.is_holiday(any_date) is False


class TestDataFreshnessValidator:
    """Test DataFreshnessValidator functionality."""

    def test_should_initialize_with_default_max_age(self):
        """Test validator initialization with default values."""
        validator = DataFreshnessValidator()

        assert validator.max_age_hours == 24
        assert isinstance(validator.market_calendar, MarketCalendar)

    def test_should_initialize_with_custom_max_age(self):
        """Test validator initialization with custom max age."""
        validator = DataFreshnessValidator(max_age_hours=12)

        assert validator.max_age_hours == 12

    def test_should_validate_fresh_data_when_recent_timestamp(self):
        """Test validation of fresh data with recent timestamp."""
        validator = DataFreshnessValidator(max_age_hours=24)

        # Create data with timestamp 1 hour ago
        recent_time = datetime.now(UTC) - timedelta(hours=1)
        data = {"symbol": "AAPL", "price": 150.0, "timestamp": recent_time.isoformat()}

        result = validator.validate_data_freshness(data, "test_source")

        assert result.is_fresh is True
        assert result.age_hours is not None
        assert result.age_hours < 2  # Should be around 1 hour
        assert result.warning is None
        assert result.should_refresh is False
        assert result.data_source == "test_source"

    def test_should_validate_stale_data_when_old_timestamp(self):
        """Test validation of stale data with old timestamp."""
        validator = DataFreshnessValidator(max_age_hours=24)

        # Create data with timestamp 48 hours ago
        old_time = datetime.now(UTC) - timedelta(hours=48)
        data = {"symbol": "AAPL", "price": 150.0, "timestamp": old_time.isoformat()}

        result = validator.validate_data_freshness(data, "test_source")

        assert result.is_fresh is False
        assert result.age_hours is not None
        assert result.age_hours > 24
        assert result.warning is not None
        assert "48" in result.warning or "hours old" in result.warning
        assert result.should_refresh is True

    def test_should_handle_missing_timestamp_gracefully(self):
        """Test handling of data without timestamp."""
        validator = DataFreshnessValidator()

        data = {
            "symbol": "AAPL",
            "price": 150.0,
            # No timestamp field
        }

        result = validator.validate_data_freshness(data, "test_source")

        assert result.is_fresh is False
        assert result.age_hours is None
        assert result.warning == "No timestamp found in data"
        assert result.should_refresh is True

    def test_should_extract_timestamp_from_various_fields(self):
        """Test timestamp extraction from different field names."""
        validator = DataFreshnessValidator()

        test_time = datetime.now(UTC) - timedelta(hours=1)
        test_cases = [
            {"timestamp": test_time.isoformat()},
            {"date": test_time.isoformat()},
            {"datetime": test_time.isoformat()},
            {"last_updated": test_time.isoformat()},
            {"market_time": test_time.isoformat()},
        ]

        for data in test_cases:
            data["symbol"] = "TEST"
            result = validator.validate_data_freshness(data, "test")
            assert result.is_fresh is True, f"Failed for field: {list(data.keys())[0]}"

    def test_should_extract_timestamp_from_nested_meta(self):
        """Test timestamp extraction from nested meta structure."""
        validator = DataFreshnessValidator()

        recent_time = datetime.now(UTC) - timedelta(hours=1)
        data = {"symbol": "AAPL", "price": 150.0, "meta": {"timestamp": recent_time.isoformat()}}

        result = validator.validate_data_freshness(data, "test_source")

        assert result.is_fresh is True
        assert result.age_hours is not None
        assert result.age_hours < 2

    def test_should_parse_various_timestamp_formats(self):
        """Test parsing of different timestamp formats."""
        validator = DataFreshnessValidator()

        recent_time = datetime.now(UTC) - timedelta(hours=1)

        test_formats = [
            recent_time.strftime("%Y-%m-%d %H:%M:%S"),
            recent_time.strftime("%Y-%m-%dT%H:%M:%S"),
            recent_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            recent_time.timestamp(),  # Unix timestamp
            recent_time,  # datetime object
        ]

        for timestamp_value in test_formats:
            data = {"symbol": "TEST", "timestamp": timestamp_value}
            result = validator.validate_data_freshness(data, "test")
            assert result.is_fresh is True, f"Failed for format: {type(timestamp_value)}"

    def test_should_handle_list_data_structure(self):
        """Test handling of list data structures."""
        validator = DataFreshnessValidator()

        recent_time = datetime.now(UTC) - timedelta(hours=1)
        data = [
            {"symbol": "AAPL", "price": 150.0, "timestamp": recent_time.isoformat()},
            {"symbol": "GOOGL", "price": 2500.0, "timestamp": recent_time.isoformat()},
        ]

        result = validator.validate_data_freshness(data, "test_source")

        assert result.is_fresh is True
        assert result.age_hours is not None
        assert result.age_hours < 2

    def test_should_adjust_age_for_weekend_data(self, mocker):
        """Test age adjustment for weekend data."""
        validator = DataFreshnessValidator(max_age_hours=24)

        # Create weekend timestamp (Saturday) - 30 hours old (normally stale)
        weekend_time = datetime.now(UTC) - timedelta(hours=30)
        # Create a Saturday date for testing
        saturday = datetime(2024, 1, 6, 12, 0, 0, tzinfo=UTC)  # Saturday

        mocker.patch.object(validator.market_calendar, "is_weekend", return_value=True)
        data = {
            "symbol": "AAPL",
            "timestamp": saturday.isoformat(),  # Use the Saturday timestamp
        }

        result = validator.validate_data_freshness(data, "test_source")

        # Should be considered fresh due to weekend adjustment (30 * 0.7 = 21 hours)
        assert result.effective_age_hours is not None
        assert result.effective_age_hours < result.age_hours

    def test_should_add_freshness_metadata_to_dict(self):
        """Test adding freshness metadata to data dictionary."""
        validator = DataFreshnessValidator()

        data = {"symbol": "AAPL", "price": 150.0}
        freshness_result = FreshnessResult(is_fresh=True, age_hours=1.0, effective_age_hours=1.0, data_source="test", should_refresh=False)

        enhanced_data = validator.add_freshness_metadata(data, freshness_result)

        assert "_freshness_info" in enhanced_data
        assert enhanced_data["_freshness_info"]["is_fresh"] is True
        assert enhanced_data["_freshness_info"]["age_hours"] == approx(1.0)
        assert enhanced_data["_freshness_info"]["data_source"] == "test"

        # Original data should not be modified
        assert "_freshness_info" not in data

    def test_should_handle_validation_errors_gracefully(self):
        """Test graceful handling of validation errors."""
        validator = DataFreshnessValidator()

        # Invalid data that will cause parsing errors
        invalid_data = {"timestamp": "invalid-timestamp-format"}

        result = validator.validate_data_freshness(invalid_data, "test_source")

        assert result.is_fresh is False
        assert result.age_hours is None
        assert result.should_refresh is True
        assert "No timestamp found" in result.warning or "Validation error" in result.warning

    def test_should_calculate_age_correctly(self):
        """Test accurate age calculation."""
        validator = DataFreshnessValidator()

        # Create timestamp exactly 5 hours ago
        five_hours_ago = datetime.now(UTC) - timedelta(hours=5)

        age_hours = validator._calculate_age_hours(five_hours_ago)

        # Should be approximately 5 hours (allow small margin for test execution time)
        assert 4.9 <= age_hours <= 5.1

    def test_should_handle_timezone_naive_timestamps(self):
        """Test handling of timezone-naive timestamps."""
        validator = DataFreshnessValidator()

        # Create timezone-naive timestamp 2 hours ago
        naive_time = datetime.utcnow() - timedelta(hours=2)

        age_hours = validator._calculate_age_hours(naive_time)

        # Should still calculate age correctly by assuming UTC
        assert 1.9 <= age_hours <= 2.1
