"""
Unit tests for FundamentalScorer.

Tests the fundamental scoring logic for stocks, ETFs, and cryptocurrencies.
"""

import pytest

from finwiz.scoring.fundamental_scorer import FundamentalScorer


class TestFundamentalScorer:
    """Test suite for FundamentalScorer."""

    @pytest.fixture
    def scorer(self):
        """Create a FundamentalScorer instance."""
        return FundamentalScorer()

    def test_stock_fundamental_score_excellent(self, scorer):
        """Test stock scoring with excellent fundamentals."""
        data = {
            "roe": 0.25,  # 25% ROE (excellent)
            "debt_to_equity": 0.2,  # Low debt (excellent)
            "revenue_growth": 0.30,  # 30% growth (excellent)
            "profit_margin": 0.25,  # 25% margin (excellent)
        }

        score, details = scorer.calculate_fundamental_score("stock", data)

        assert score > 0.9  # Should be very high
        assert details["roe_score"] == 1.0
        assert details["debt_score"] == 1.0
        assert details["growth_score"] == 1.0
        assert details["margin_score"] == 1.0

    def test_stock_fundamental_score_poor(self, scorer):
        """Test stock scoring with poor fundamentals."""
        data = {
            "roe": 0.02,  # 2% ROE (poor)
            "debt_to_equity": 3.0,  # High debt (poor)
            "revenue_growth": -0.03,  # -3% growth (declining, poor)
            "profit_margin": 0.02,  # 2% margin (poor)
        }

        score, details = scorer.calculate_fundamental_score("stock", data)

        assert score < 0.3  # Should be low
        assert details["roe_score"] == 0.2
        assert details["debt_score"] == 0.2
        assert details["growth_score"] == 0.2  # Negative growth below acceptable threshold
        assert details["margin_score"] == 0.2

    def test_etf_fundamental_score_excellent(self, scorer):
        """Test ETF scoring with excellent metrics."""
        scorer.set_context("TEST", None)
        data = {
            "expense_ratio": 0.0005,  # 0.05% (excellent)
            "tracking_error": 0.001,  # 0.10% (excellent)
            "aum": 10e9,  # $10B (excellent)
        }

        score, details = scorer.calculate_fundamental_score("etf", data)

        assert score > 0.9  # Should be very high
        assert details["expense_score"] == 1.0
        assert details["tracking_score"] == 1.0
        assert details["aum_score"] == 1.0

    def test_etf_fundamental_score_missing_tracking_error(self, scorer):
        """Test ETF scoring with missing tracking error."""
        scorer.set_context("TEST", None)
        data = {
            "expense_ratio": 0.0005,  # 0.05% (excellent)
            "aum": 10e9,  # $10B (excellent)
        }

        score, details = scorer.calculate_fundamental_score("etf", data)

        assert details["tracking_error"] is None
        assert details["tracking_error_available"] is False
        assert details["tracking_score"] == 0.5  # Neutral score

    def test_crypto_fundamental_score_excellent(self, scorer):
        """Test crypto scoring with excellent metrics."""
        data = {
            "market_cap": 150e9,  # $150B (excellent)
            "volume_24h": 2e9,  # $2B (excellent)
            "age_years": 6,  # 6 years (excellent)
            "circulating_supply": 90e6,  # High circulation
            "max_supply": 100e6,
        }

        score, details = scorer.calculate_fundamental_score("crypto", data)

        # Score calculation: 0.40 * 1.0 + 0.30 * 0.8 + 0.20 * 1.0 + 0.10 * 1.0 = 0.90
        assert score >= 0.89  # Should be very high (adjusted for actual weights)
        assert details["market_cap_score"] == 1.0
        assert details["volume_score"] == 0.8  # $2B is "high" not "very high"
        assert details["age_score"] == 1.0

    def test_crypto_fundamental_score_poor(self, scorer):
        """Test crypto scoring with poor metrics."""
        data = {
            "market_cap": 50e6,  # $50M (poor)
            "volume_24h": 5e6,  # $5M (poor)
            "age_years": 0.5,  # 6 months (poor)
            "circulating_supply": 10e6,  # Low circulation
            "max_supply": 100e6,
        }

        score, details = scorer.calculate_fundamental_score("crypto", data)

        assert score < 0.3  # Should be low
        assert details["market_cap_score"] == 0.2
        assert details["volume_score"] == 0.2
        assert details["age_score"] == 0.2

    def test_unknown_asset_class(self, scorer):
        """Test handling of unknown asset class."""
        data = {"some_field": 123}

        score, details = scorer.calculate_fundamental_score("unknown", data)

        assert score == 0.5  # Default score
        assert "error" in details

    def test_safe_get_float_with_valid_value(self, scorer):
        """Test _safe_get_float with valid float value (via analyzer)."""
        # FundamentalScorer delegates to analyzers, test through them
        from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer

        analyzer = StockAnalyzer()
        data = {"value": 123.45}
        result = analyzer._safe_get_float(data, "value", 0.0)
        assert result == 123.45

    def test_safe_get_float_with_missing_value(self, scorer):
        """Test _safe_get_float with missing value (via analyzer)."""
        from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer

        analyzer = StockAnalyzer()
        data = {}
        result = analyzer._safe_get_float(data, "value", 99.0)
        assert result == 99.0

    def test_safe_get_float_with_invalid_value(self, scorer):
        """Test _safe_get_float with invalid value (via analyzer)."""
        from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer

        analyzer = StockAnalyzer()
        data = {"value": "not_a_number"}
        result = analyzer._safe_get_float(data, "value", 50.0)
        assert result == 50.0
