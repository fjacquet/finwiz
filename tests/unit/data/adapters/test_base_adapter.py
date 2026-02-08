"""Unit tests for base adapter and FundamentalData."""

from datetime import datetime

import pytest

from finwiz.data.adapters.base_adapter import (
    DataAcquisitionError,
    FundamentalData,
    InvalidDataError,
    TimeoutError,
)


class TestFundamentalData:
    """Test FundamentalData validation and methods."""

    def test_should_create_valid_fundamental_data(self):
        """Test creating valid FundamentalData object."""
        data = FundamentalData(
            ticker="AAPL",
            source="TestSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )

        assert data.ticker == "AAPL"
        assert data.source == "TestSource"
        assert data.confidence == 0.9
        assert data.return_on_equity == 0.25

    def test_should_reject_invalid_confidence(self):
        """Test that invalid confidence raises error."""
        with pytest.raises(InvalidDataError, match="Confidence must be between"):
            FundamentalData(
                ticker="AAPL",
                source="TestSource",
                timestamp=datetime.now(),
                confidence=1.5,  # Invalid: > 1.0
            )

    def test_should_validate_roe_range(self):
        """Test ROE validation (-1.0 to 2.0)."""
        # Valid ROE
        data_valid = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
        )
        assert data_valid.is_valid()

        # Invalid ROE (too high)
        data_invalid_high = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=2.5,  # > 2.0
        )
        assert not data_invalid_high.is_valid()

        # Invalid ROE (too low)
        data_invalid_low = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=-1.5,  # < -1.0
        )
        assert not data_invalid_low.is_valid()

    def test_should_validate_debt_to_equity_range(self):
        """Test Debt/Equity validation (>= 0 and < 10.0)."""
        # Valid D/E
        data_valid = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            debt_to_equity=0.5,
        )
        assert data_valid.is_valid()

        # Invalid D/E (negative)
        data_invalid_neg = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            debt_to_equity=-0.1,
        )
        assert not data_invalid_neg.is_valid()

        # Invalid D/E (too high)
        data_invalid_high = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            debt_to_equity=10.5,  # >= 10.0
        )
        assert not data_invalid_high.is_valid()

    def test_should_validate_revenue_growth_range(self):
        """Test Revenue Growth validation (-0.5 to 5.0)."""
        # Valid growth
        data_valid = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            revenue_growth=0.15,
        )
        assert data_valid.is_valid()

        # Invalid growth (too low)
        data_invalid_low = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            revenue_growth=-0.6,  # < -0.5
        )
        assert not data_invalid_low.is_valid()

        # Invalid growth (too high)
        data_invalid_high = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            revenue_growth=5.5,  # > 5.0
        )
        assert not data_invalid_high.is_valid()

    def test_should_validate_profit_margin_range(self):
        """Test Profit Margin validation (-1.0 to 1.0)."""
        # Valid margin
        data_valid = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            profit_margin=0.20,
        )
        assert data_valid.is_valid()

        # Invalid margin (too low)
        data_invalid_low = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            profit_margin=-1.5,  # < -1.0
        )
        assert not data_invalid_low.is_valid()

        # Invalid margin (too high)
        data_invalid_high = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            profit_margin=1.5,  # > 1.0
        )
        assert not data_invalid_high.is_valid()

    def test_should_get_available_fields(self):
        """Test getting list of populated fields."""
        data = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            profit_margin=0.20,
            # debt_to_equity and revenue_growth are None
        )

        fields = data.get_available_fields()
        assert "return_on_equity" in fields
        assert "profit_margin" in fields
        assert "debt_to_equity" not in fields
        assert "revenue_growth" not in fields

    def test_should_initialize_warnings_list(self):
        """Test that warnings list is initialized."""
        data = FundamentalData(
            ticker="AAPL",
            source="Test",
            timestamp=datetime.now(),
            confidence=0.9,
        )

        assert data.warnings is not None
        assert isinstance(data.warnings, list)
        assert len(data.warnings) == 0


class TestExceptions:
    """Test custom exception classes."""

    def test_should_raise_data_acquisition_error(self):
        """Test DataAcquisitionError can be raised."""
        with pytest.raises(DataAcquisitionError, match="Test error"):
            raise DataAcquisitionError("Test error")

    def test_should_raise_invalid_data_error(self):
        """Test InvalidDataError can be raised."""
        with pytest.raises(InvalidDataError, match="Invalid data"):
            raise InvalidDataError("Invalid data")

    def test_should_raise_timeout_error(self):
        """Test TimeoutError can be raised."""
        with pytest.raises(TimeoutError, match="Timeout"):
            raise TimeoutError("Timeout")

    def test_should_inherit_from_data_acquisition_error(self):
        """Test that InvalidDataError and TimeoutError inherit from DataAcquisitionError."""
        assert issubclass(InvalidDataError, DataAcquisitionError)
        assert issubclass(TimeoutError, DataAcquisitionError)
