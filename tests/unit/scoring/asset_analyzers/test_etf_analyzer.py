"""Unit tests for ETFAnalyzer."""

import pytest
from pytest import approx

from finwiz.scoring.asset_analyzers.etf_analyzer import ETFAnalyzer


class TestETFAnalyzer:
    """Test suite for ETFAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create ETFAnalyzer instance."""
        return ETFAnalyzer()

    @pytest.fixture
    def excellent_etf_data(self):
        """Create data for an excellent ETF."""
        return {
            "expense_ratio": 0.0005,  # 0.05% (excellent)
            "tracking_error": 0.001,  # 0.10% (excellent)
            "aum": 10e9,  # $10B (large)
        }

    @pytest.fixture
    def poor_etf_data(self):
        """Create data for a poor ETF."""
        return {
            "expense_ratio": 0.02,  # 2.00% (high)
            "tracking_error": 0.05,  # 5.00% (high)
            "aum": 50e6,  # $50M (small)
        }

    def test_calculate_fundamental_score_excellent_etf(self, analyzer, excellent_etf_data):
        """Test scoring for excellent ETF."""
        score, details = analyzer.calculate_fundamental_score(excellent_etf_data)

        # Should get high score
        assert score >= 0.9
        assert details["fundamental_score"] == score
        assert details["expense_score"] == approx(1.0)
        assert details["tracking_score"] == approx(1.0)
        assert details["aum_score"] == approx(1.0)

    def test_calculate_fundamental_score_poor_etf(self, analyzer, poor_etf_data):
        """Test scoring for poor ETF."""
        score, details = analyzer.calculate_fundamental_score(poor_etf_data)

        # Should get low score
        assert score <= 0.3
        assert details["fundamental_score"] == score
        assert details["expense_score"] == approx(0.2)
        assert details["tracking_score"] == approx(0.2)

    def test_calculate_fundamental_score_missing_tracking_error(self, analyzer):
        """Test scoring with missing tracking error."""
        data = {
            "expense_ratio": 0.001,
            "aum": 5e9,
        }
        score, details = analyzer.calculate_fundamental_score(data)

        # Should use neutral score for tracking error
        assert details["tracking_error"] is None
        assert details["tracking_error_available"] is False
        assert details["tracking_score"] == approx(0.5)

    def test_extract_metrics(self, analyzer, excellent_etf_data):
        """Test metric extraction."""
        metrics = analyzer.extract_metrics(excellent_etf_data)

        assert metrics["expense_ratio"] == approx(0.0005)
        assert metrics["tracking_error"] == approx(0.001)
        assert metrics["aum"] == 10e9

    def test_validate_data_valid(self, analyzer, excellent_etf_data):
        """Test data validation with valid data."""
        assert analyzer.validate_data(excellent_etf_data) is True

    def test_validate_data_missing_expense_ratio(self, analyzer):
        """Test data validation with missing expense ratio."""
        incomplete_data = {"tracking_error": 0.001}
        assert analyzer.validate_data(incomplete_data) is False

    def test_score_expense_ratio_thresholds(self, analyzer):
        """Test expense ratio scoring thresholds."""
        assert analyzer._score_expense_ratio(0.0005) == approx(1.0)  # Excellent
        assert analyzer._score_expense_ratio(0.002) == approx(0.8)  # Very good
        assert analyzer._score_expense_ratio(0.004) == approx(0.6)  # Good
        assert analyzer._score_expense_ratio(0.008) == approx(0.4)  # Acceptable
        assert analyzer._score_expense_ratio(0.02) == approx(0.2)  # Poor

    def test_score_tracking_error_thresholds(self, analyzer):
        """Test tracking error scoring thresholds."""
        assert analyzer._score_tracking_error(0.001) == approx(1.0)  # Excellent
        assert analyzer._score_tracking_error(0.003) == approx(0.8)  # Very good
        assert analyzer._score_tracking_error(0.008) == approx(0.6)  # Good
        assert analyzer._score_tracking_error(0.015) == approx(0.4)  # Acceptable
        assert analyzer._score_tracking_error(0.05) == approx(0.2)  # Poor

    def test_score_aum_thresholds(self, analyzer):
        """Test AUM scoring thresholds."""
        assert analyzer._score_aum(10e9) == approx(1.0)  # $10B+
        assert analyzer._score_aum(2e9) == approx(0.8)  # $2B
        assert analyzer._score_aum(700e6) == approx(0.6)  # $700M
        assert analyzer._score_aum(200e6) == approx(0.4)  # $200M
        assert analyzer._score_aum(50e6) == approx(0.2)  # $50M
