"""Tests for YFinanceAdapter data normalization."""

import pytest

from finwiz.data.adapters.yfinance_adapter import YFinanceAdapter


class TestYFinanceDebtToEquityNormalization:
    """Verify debt_to_equity is normalized from percentage to ratio."""

    @pytest.fixture
    def adapter(self):
        return YFinanceAdapter()

    def test_should_normalize_debt_to_equity_from_percentage(self, adapter):
        """yfinance returns debtToEquity as percentage; adapter must divide by 100."""
        data = {
            "symbol": "AAPL",
            "returnOnEquity": 0.25,
            "debtToEquity": 102.63,
            "revenueGrowth": 0.08,
            "profitMargins": 0.25,
        }
        result = adapter._parse_yfinance_data("AAPL", data)
        assert result.debt_to_equity == pytest.approx(1.0263, rel=1e-4)
        assert result.is_valid()

    def test_should_normalize_low_debt_to_equity(self, adapter):
        """Low debtToEquity like GOOGL=16.13 should become 0.1613."""
        data = {
            "symbol": "GOOGL",
            "debtToEquity": 16.13,
        }
        result = adapter._parse_yfinance_data("GOOGL", data)
        assert result.debt_to_equity == pytest.approx(0.1613, rel=1e-4)
        assert result.is_valid()

    def test_should_handle_none_debt_to_equity(self, adapter):
        """None debt_to_equity should remain None."""
        data = {"symbol": "TEST"}
        result = adapter._parse_yfinance_data("TEST", data)
        assert result.debt_to_equity is None

    def test_should_handle_zero_debt_to_equity(self, adapter):
        """Zero debtToEquity should normalize to 0.0."""
        data = {"symbol": "TEST", "debtToEquity": 0.0}
        result = adapter._parse_yfinance_data("TEST", data)
        assert result.debt_to_equity == 0.0
        assert result.is_valid()
