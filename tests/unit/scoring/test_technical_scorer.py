"""
Unit tests for TechnicalScorer.

Tests the technical analysis scoring logic.
"""

from pytest import approx
import pytest

from finwiz.scoring.technical_scorer import TechnicalScorer


class TestTechnicalScorer:
    """Test suite for TechnicalScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a TechnicalScorer instance."""
        return TechnicalScorer()

    def test_technical_score_strong_uptrend(self, scorer):
        """Test technical scoring with strong uptrend."""
        data = {
            "rsi": 50,  # Neutral RSI (excellent)
            "current_price": 150,
            "moving_avg_50": 140,
            "moving_avg_200": 130,  # Strong uptrend
            "macd": 2.0,
            "macd_signal": 1.0,  # Bullish momentum
        }

        score, details = scorer.calculate_technical_score(data)

        assert score > 0.9  # Should be very high
        assert details["rsi_score"] == approx(1.0)
        assert details["trend_score"] == approx(1.0)
        assert details["trend_direction"] == "strong_uptrend"
        assert details["momentum_score"] == approx(1.0)

    def test_technical_score_strong_downtrend(self, scorer):
        """Test technical scoring with strong downtrend."""
        data = {
            "rsi": 95,  # Extreme overbought (poor)
            "current_price": 100,
            "moving_avg_50": 110,
            "moving_avg_200": 120,  # Strong downtrend
            "macd": -2.0,
            "macd_signal": -1.0,  # Bearish momentum
        }

        score, details = scorer.calculate_technical_score(data)

        assert score < 0.3  # Should be low
        assert details["rsi_score"] == approx(0.2)
        assert details["trend_score"] == approx(0.2)
        assert details["trend_direction"] == "strong_downtrend"
        assert details["momentum_score"] == approx(0.4)  # Bearish (not strong bearish)

    def test_technical_score_neutral(self, scorer):
        """Test technical scoring with neutral conditions."""
        data = {
            "rsi": 50,  # Neutral RSI
            "current_price": 100,
            "moving_avg_50": 100,
            "moving_avg_200": 100,  # Sideways
            "macd": 0.05,
            "macd_signal": 0.04,  # Neutral momentum
        }

        score, details = scorer.calculate_technical_score(data)

        assert 0.5 < score <= 0.8  # Should be moderate (inclusive upper bound)
        assert details["rsi_score"] == approx(1.0)
        assert details["trend_direction"] == "sideways"

    def test_rsi_scoring_ranges(self, scorer):
        """Test RSI scoring across different ranges."""
        # Neutral zone (40-60)
        data = {"rsi": 50, "current_price": 100, "moving_avg_50": 100, "moving_avg_200": 100, "macd": 0, "macd_signal": 0}
        score, details = scorer.calculate_technical_score(data)
        assert details["rsi_score"] == approx(1.0)

        # Good range (30-70)
        data["rsi"] = 35
        score, details = scorer.calculate_technical_score(data)
        assert details["rsi_score"] == approx(0.8)

        # Acceptable range (20-80)
        data["rsi"] = 75
        score, details = scorer.calculate_technical_score(data)
        assert details["rsi_score"] == approx(0.6)

        # Warning range (10-90)
        data["rsi"] = 85
        score, details = scorer.calculate_technical_score(data)
        assert details["rsi_score"] == approx(0.4)

        # Extreme
        data["rsi"] = 95
        score, details = scorer.calculate_technical_score(data)
        assert details["rsi_score"] == approx(0.2)

    def test_trend_direction_detection(self, scorer):
        """Test trend direction detection logic."""
        # Strong uptrend
        data = {"rsi": 50, "current_price": 150, "moving_avg_50": 140, "moving_avg_200": 130, "macd": 0, "macd_signal": 0}
        score, details = scorer.calculate_technical_score(data)
        assert details["trend_direction"] == "strong_uptrend"
        assert details["trend_score"] == approx(1.0)

        # Uptrend (price > ma_50 and price > ma_200, but not ma_50 > ma_200)
        data["current_price"] = 145
        data["moving_avg_50"] = 135
        data["moving_avg_200"] = 140  # ma_50 < ma_200
        score, details = scorer.calculate_technical_score(data)
        assert details["trend_direction"] == "uptrend"
        assert details["trend_score"] == approx(0.8)

        # Weak uptrend (price > ma_200 but price < ma_50)
        data["current_price"] = 130
        data["moving_avg_50"] = 135
        data["moving_avg_200"] = 125  # price > ma_200 but price < ma_50
        score, details = scorer.calculate_technical_score(data)
        assert details["trend_direction"] == "weak_uptrend"
        assert details["trend_score"] == approx(0.6)

        # Sideways
        data["current_price"] = 100
        data["moving_avg_50"] = 100
        data["moving_avg_200"] = 100
        score, details = scorer.calculate_technical_score(data)
        assert details["trend_direction"] == "sideways"
        assert details["trend_score"] == approx(0.5)

    def test_macd_momentum_scoring(self, scorer):
        """Test MACD momentum scoring."""
        # Strong bullish
        data = {"rsi": 50, "current_price": 100, "moving_avg_50": 100, "moving_avg_200": 100, "macd": 2.0, "macd_signal": 1.0}
        score, details = scorer.calculate_technical_score(data)
        assert details["momentum_score"] == approx(1.0)

        # Bullish (macd_diff > 0 but macd not > 0)
        data["macd"] = -0.5
        data["macd_signal"] = -1.0
        score, details = scorer.calculate_technical_score(data)
        assert details["momentum_score"] == approx(0.8)

        # Neutral (abs(macd_diff) < 0.1, but macd_diff not > 0 and not < 0, so exactly 0)
        data["macd"] = 0.05
        data["macd_signal"] = 0.05
        score, details = scorer.calculate_technical_score(data)
        assert details["momentum_score"] == approx(0.6)

        # Bearish
        data["macd"] = -1.0
        data["macd_signal"] = -0.5
        score, details = scorer.calculate_technical_score(data)
        assert details["momentum_score"] == approx(0.4)

    def test_safe_get_float_with_defaults(self, scorer):
        """Test _safe_get_float with missing values."""
        data = {}
        result = scorer._safe_get_float(data, "missing_key", 123.45)
        assert result == approx(123.45)