"""Unit tests for StockAnalyzer."""

import pytest
from pytest import approx

from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer


class TestStockAnalyzer:
    """Test suite for StockAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create StockAnalyzer instance."""
        return StockAnalyzer()

    @pytest.fixture
    def excellent_stock_data(self):
        """Create data for an excellent stock."""
        return {
            "roe": 0.25,  # 25% ROE (excellent)
            "debt_to_equity": 0.2,  # Low debt
            "revenue_growth": 0.30,  # 30% growth
            "profit_margin": 0.25,  # 25% margin
        }

    @pytest.fixture
    def poor_stock_data(self):
        """Create data for a poor stock."""
        return {
            "roe": 0.02,  # 2% ROE (poor)
            "debt_to_equity": 3.0,  # High debt
            "revenue_growth": -0.05,  # Negative growth
            "profit_margin": 0.02,  # 2% margin
        }

    def test_calculate_fundamental_score_excellent_stock(self, analyzer, excellent_stock_data):
        """Test scoring for excellent stock."""
        score, details = analyzer.calculate_fundamental_score(excellent_stock_data)

        # Should get high score
        assert score >= 0.9
        assert details["fundamental_score"] == score
        assert details["roe_score"] == approx(1.0)
        assert details["debt_score"] == approx(1.0)
        assert details["growth_score"] == approx(1.0)
        assert details["margin_score"] == approx(1.0)

    def test_calculate_fundamental_score_poor_stock(self, analyzer, poor_stock_data):
        """Test scoring for poor stock."""
        score, details = analyzer.calculate_fundamental_score(poor_stock_data)

        # Should get low score
        assert score <= 0.3
        assert details["fundamental_score"] == score
        assert details["roe_score"] == approx(0.2)
        assert details["debt_score"] == approx(0.2)

    def test_extract_metrics(self, analyzer, excellent_stock_data):
        """Test metric extraction."""
        metrics = analyzer.extract_metrics(excellent_stock_data)

        assert metrics["roe"] == approx(0.25)
        assert metrics["debt_to_equity"] == approx(0.2)
        assert metrics["revenue_growth"] == approx(0.30)
        assert metrics["profit_margin"] == approx(0.25)

    def test_validate_data_valid(self, analyzer, excellent_stock_data):
        """Test data validation with valid data."""
        assert analyzer.validate_data(excellent_stock_data) is True

    def test_validate_data_missing_fields(self, analyzer):
        """Test data validation with missing fields."""
        incomplete_data = {"roe": 0.15}  # Missing other required fields
        assert analyzer.validate_data(incomplete_data) is False

    def test_score_roe_thresholds(self, analyzer):
        """Test ROE scoring thresholds."""
        assert analyzer._score_roe(0.25) == approx(1.0)  # Excellent
        assert analyzer._score_roe(0.18) == approx(0.8)  # Very good
        assert analyzer._score_roe(0.12) == approx(0.6)  # Good
        assert analyzer._score_roe(0.07) == approx(0.4)  # Acceptable
        assert analyzer._score_roe(0.02) == approx(0.2)  # Poor

    def test_score_debt_to_equity_thresholds(self, analyzer):
        """Test debt-to-equity scoring thresholds."""
        assert analyzer._score_debt_to_equity(0.2) == approx(1.0)  # Very low
        assert analyzer._score_debt_to_equity(0.4) == approx(0.8)  # Low
        assert analyzer._score_debt_to_equity(0.8) == approx(0.6)  # Moderate
        assert analyzer._score_debt_to_equity(1.5) == approx(0.4)  # High
        assert analyzer._score_debt_to_equity(3.0) == approx(0.2)  # Very high

    def test_safe_get_float_with_valid_value(self, analyzer):
        """Test safe float extraction with valid value."""
        data = {"test_key": 123.45}
        result = analyzer._safe_get_float(data, "test_key", 0.0)
        assert result == approx(123.45)

    def test_safe_get_float_with_missing_key(self, analyzer):
        """Test safe float extraction with missing key."""
        data = {}
        result = analyzer._safe_get_float(data, "missing_key", 99.0)
        assert result == approx(99.0)

    def test_safe_get_float_with_invalid_value(self, analyzer):
        """Test safe float extraction with invalid value."""
        data = {"test_key": "not_a_number"}
        result = analyzer._safe_get_float(data, "test_key", 50.0)
        assert result == approx(50.0)
