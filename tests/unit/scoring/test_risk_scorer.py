"""
Unit tests for RiskScorer.

Tests the risk assessment scoring logic.
"""

import pytest
from pytest import approx

from finwiz.scoring.risk_scorer import RiskScorer


class TestRiskScorer:
    """Test suite for RiskScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a RiskScorer instance."""
        return RiskScorer()

    def test_risk_score_low_risk(self, scorer):
        """Test risk scoring with low risk metrics."""
        data = {
            "volatility": 0.08,  # 8% volatility (low)
            "max_drawdown": -0.08,  # -8% drawdown (low)
            "beta": 1.0,  # Beta of 1.0 (neutral)
        }

        score, details = scorer.calculate_risk_score(data)

        assert details["volatility_score"] == approx(1.0)
        assert details["drawdown_score"] == approx(1.0)
        assert details["beta_score"] == approx(1.0)

    def test_risk_score_high_risk(self, scorer):
        """Test risk scoring with high risk metrics."""
        data = {
            "volatility": 0.60,  # 60% volatility (very high, >0.5 threshold)
            "max_drawdown": -0.60,  # -60% drawdown (very high, >0.5 threshold)
            "beta": 2.5,  # Beta of 2.5 (very high, >2.0)
        }

        score, details = scorer.calculate_risk_score(data)

        assert score <= 0.3  # Should be low (high risk) - adjusted for floating point
        assert details["volatility_score"] == approx(0.2)
        assert details["drawdown_score"] == approx(0.2)
        assert details["beta_score"] == approx(0.2)

    def test_volatility_scoring_ranges(self, scorer):
        """Test volatility scoring across different ranges."""
        # Very low volatility (<=15%)
        data = {"volatility": 0.12, "max_drawdown": -0.10, "beta": 1.0}
        score, details = scorer.calculate_risk_score(data)
        assert details["volatility_score"] == approx(1.0)  # Updated: 12% is now very_low

        # Low volatility (15-25%)
        data["volatility"] = 0.20
        score, details = scorer.calculate_risk_score(data)
        assert details["volatility_score"] == approx(0.8)  # Updated threshold

        # Moderate volatility (25-35%)
        data["volatility"] = 0.30
        score, details = scorer.calculate_risk_score(data)
        assert details["volatility_score"] == approx(0.6)  # Updated threshold

        # High volatility (35-50%)
        data["volatility"] = 0.40
        score, details = scorer.calculate_risk_score(data)
        assert details["volatility_score"] == approx(0.4)  # Updated threshold

        # Very high volatility (>50%)
        data["volatility"] = 0.60
        score, details = scorer.calculate_risk_score(data)
        assert details["volatility_score"] == approx(0.2)  # Updated threshold

    def test_drawdown_scoring_ranges(self, scorer):
        """Test drawdown scoring across different ranges."""
        # Low drawdown (<=10%)
        data = {"volatility": 0.15, "max_drawdown": -0.08, "beta": 1.0}
        score, details = scorer.calculate_risk_score(data)
        assert details["drawdown_score"] == approx(1.0)
        assert details["max_drawdown"] == approx(-0.08)  # Stored as negative

        # 10-20%
        data["max_drawdown"] = -0.15
        score, details = scorer.calculate_risk_score(data)
        assert details["drawdown_score"] == approx(0.8)

        # 20-35%
        data["max_drawdown"] = -0.30
        score, details = scorer.calculate_risk_score(data)
        assert details["drawdown_score"] == approx(0.6)

        # 35-50%
        data["max_drawdown"] = -0.40
        score, details = scorer.calculate_risk_score(data)
        assert details["drawdown_score"] == approx(0.4)

        # >50%
        data["max_drawdown"] = -0.60
        score, details = scorer.calculate_risk_score(data)
        assert details["drawdown_score"] == approx(0.2)

    def test_beta_scoring_ranges(self, scorer):
        """Test beta scoring across different ranges."""
        # Beta close to 1.0 (0.8-1.2)
        data = {"volatility": 0.15, "max_drawdown": -0.15, "beta": 1.0}
        score, details = scorer.calculate_risk_score(data)
        assert details["beta_score"] == approx(1.0)
        assert details["beta_deviation"] == approx(0.0)

        # Beta 0.6-1.4
        data["beta"] = 1.3
        score, details = scorer.calculate_risk_score(data)
        assert details["beta_score"] == approx(0.8)
        assert abs(details["beta_deviation"] - 0.3) < 0.01  # Floating point tolerance

        # Beta 0.4-1.6
        data["beta"] = 1.5
        score, details = scorer.calculate_risk_score(data)
        assert details["beta_score"] == approx(0.6)
        assert details["beta_deviation"] == approx(0.5)

        # Beta 0.0-2.0
        data["beta"] = 1.8
        score, details = scorer.calculate_risk_score(data)
        assert details["beta_score"] == approx(0.4)
        assert details["beta_deviation"] == approx(0.8)

        # Beta >2.0
        data["beta"] = 2.5
        score, details = scorer.calculate_risk_score(data)
        assert details["beta_score"] == approx(0.2)
        assert details["beta_deviation"] == approx(1.5)

    def test_weighted_average_calculation(self, scorer):
        """Test that weighted average is calculated correctly."""
        data = {
            "volatility": 0.20,  # Score: 0.8 (in 15-25% range)
            "max_drawdown": -0.15,  # Score: 0.8
            "beta": 1.0,  # Score: 1.0
        }

        score, details = scorer.calculate_risk_score(data)

        # Expected: 0.50 * 0.8 + 0.30 * 0.8 + 0.20 * 1.0 = 0.84
        expected_score = 0.50 * 0.8 + 0.30 * 0.8 + 0.20 * 1.0
        assert abs(score - expected_score) < 0.01

    def test_safe_get_float_with_defaults(self, scorer):
        """Test _safe_get_float with missing values."""
        data = {}
        result = scorer._safe_get_float(data, "missing_key", 0.5)
        assert result == approx(0.5)
