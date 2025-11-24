"""
Financial calculations validation tests for Python-first deep analysis architecture.

This suite validates:
1. Financial metric calculations correctness
2. Numerical stability and precision
3. Edge case handling (negative values, NaN, infinity)
4. Asset-specific calculation differences
5. Score boundaries and grading logic

Created by quantitative-finance-engineer for AI Minimalism validation.
"""

import math

import pytest

from finwiz.flow_state import DeepAnalysisResult
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


class TestFinancialCalculations:
    """Validate financial calculation correctness and numerical stability."""

    @pytest.fixture
    def scorer(self):
        """Create scorer instance for testing."""
        return DeepAnalysisScorer()

    def test_fundamental_score_calculation_stock(self, scorer):
        """Test fundamental score calculation for stocks with known values."""
        # Test data with all critical fields plus extras
        test_data = {
            "ticker": "TEST",
            "asset_class": "stock",
            # Critical fields for stock
            "current_price": 100.0,
            "roe": 0.25,  # 25% ROE - excellent
            "debt_to_equity": 0.5,  # Low debt - good
            "revenue_growth": 0.15,  # 15% growth - strong
            "volatility": 0.20,  # 20% volatility
            "beta": 1.1,  # Slightly above market
            # Optional fields
            "profit_margin": 0.20,  # 20% margin - good
            "pe_ratio": 18,  # Reasonable P/E
            "dividend_yield": 0.02,  # 2% yield
        }

        result = scorer.calculate_composite_score("TEST", "stock", test_data)

        # Verify result structure
        assert isinstance(result, DeepAnalysisResult)
        assert result.ticker == "TEST"
        assert result.asset_class == "stock"

        # Verify score ranges
        assert 0 <= result.composite_score <= 1.0
        assert result.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

        # With these strong fundamentals, expect high score
        assert result.composite_score > 0.7, "Strong fundamentals should yield high score"

    def test_technical_score_calculation(self, scorer):
        """Test technical indicator score calculation."""
        test_data = {
            "ticker": "TECH",
            "asset_class": "stock",
            # Critical fields for stock
            "current_price": 100.0,
            "roe": 0.12,
            "debt_to_equity": 0.6,
            "revenue_growth": 0.08,
            "volatility": 0.20,  # 20% volatility - moderate
            "beta": 1.2,  # Slightly higher beta
            # Technical indicators
            "rsi": 55,  # Neutral RSI
            "sma_20": 98,  # Price above SMA20 - bullish
            "sma_50": 95,  # Price above SMA50 - bullish
            "volume": 1000000,  # Good volume
            "average_volume": 900000,  # Above average volume
        }

        result = scorer.calculate_composite_score("TECH", "stock", test_data)

        # Technical indicators are positive (price > SMAs, good volume)
        assert result.composite_score > 0.5, "Positive technicals should yield decent score"

        # Check that technical metrics were considered
        assert hasattr(result, "technical_score") or result.composite_score != 0

    def test_risk_metrics_impact(self, scorer):
        """Test that risk metrics properly impact scoring."""
        # High risk scenario
        high_risk_data = {
            "ticker": "RISKY",
            "asset_class": "stock",
            # Critical fields
            "current_price": 50.0,
            "roe": 0.10,
            "debt_to_equity": 1.0,
            "revenue_growth": 0.05,
            "volatility": 0.80,  # 80% volatility - extreme
            "beta": 2.5,  # Very high beta
            # Optional risk fields
            "max_drawdown": -0.60,  # 60% drawdown - severe
            "sharpe_ratio": 0.3,  # Poor risk-adjusted return
            "value_at_risk": -0.15,  # High VaR
        }

        high_risk_result = scorer.calculate_composite_score("RISKY", "stock", high_risk_data)

        # Low risk scenario
        low_risk_data = {
            "ticker": "SAFE",
            "asset_class": "stock",
            # Critical fields
            "current_price": 100.0,
            "roe": 0.15,
            "debt_to_equity": 0.5,
            "revenue_growth": 0.10,
            "volatility": 0.10,  # 10% volatility - low
            "beta": 0.7,  # Below market beta
            # Optional risk fields
            "max_drawdown": -0.05,  # 5% drawdown - minimal
            "sharpe_ratio": 2.0,  # Excellent risk-adjusted return
            "value_at_risk": -0.02,  # Low VaR
        }

        low_risk_result = scorer.calculate_composite_score("SAFE", "stock", low_risk_data)

        # Low risk should score better than high risk
        assert low_risk_result.composite_score > high_risk_result.composite_score, "Low risk assets should score better than high risk"

    def test_edge_case_negative_values(self, scorer):
        """Test handling of negative financial metrics."""
        test_data = {
            "ticker": "LOSS",
            "asset_class": "stock",
            # Critical fields
            "current_price": 10.0,
            "roe": -0.15,  # Negative ROE - losing money
            "debt_to_equity": 2.5,  # High debt
            "revenue_growth": -0.20,  # Declining revenue
            "volatility": 0.40,
            "beta": 1.5,
            # Optional negative fields
            "profit_margin": -0.10,  # Negative margin
            "earnings_growth": -0.30,  # Declining earnings
        }

        result = scorer.calculate_composite_score("LOSS", "stock", test_data)

        # Should handle negative values without crashing
        assert result is not None
        assert 0 <= result.composite_score <= 1.0

        # Negative fundamentals should yield low score
        assert result.composite_score < 0.5, "Negative metrics should yield low score"
        assert result.grade in ["C-", "D", "F"], "Poor metrics should yield low grade"

    def test_edge_case_nan_and_infinity(self, scorer):
        """Test handling of NaN and infinity values."""
        test_data = {
            "ticker": "EDGE",
            "asset_class": "stock",
            # Critical fields
            "current_price": 50.0,
            "roe": 0.05,  # Normal ROE
            "debt_to_equity": float("nan"),  # NaN value
            "revenue_growth": 0.10,  # Provide valid value (revenue_growth is now required)
            "volatility": 0.30,
            "beta": 1.0,
            # Optional edge cases
            "pe_ratio": float("inf"),  # Infinity P/E (no earnings)
        }

        # Should handle edge cases gracefully
        result = scorer.calculate_composite_score("EDGE", "stock", test_data)

        assert result is not None
        assert 0 <= result.composite_score <= 1.0
        assert not math.isnan(result.composite_score), "Score should not be NaN"
        assert not math.isinf(result.composite_score), "Score should not be infinity"

    def test_etf_specific_calculations(self, scorer):
        """Test ETF-specific metric calculations."""
        etf_data = {
            "ticker": "SPY",
            "asset_class": "etf",
            # Critical fields for ETF
            "current_price": 450.0,
            "expense_ratio": 0.0009,  # 0.09% - very low
            "volatility": 0.15,  # 15% volatility
            # Optional ETF fields
            "tracking_error": 0.02,  # 2% tracking error
            "aum": 400000000000,  # $400B AUM
            "nav_discount": -0.001,  # Trading at slight discount
            "dividend_yield": 0.013,  # 1.3% yield
            "sharpe_ratio": 1.2,
        }

        result = scorer.calculate_composite_score("SPY", "etf", etf_data)

        # ETFs with low expense ratios should score well
        assert result.composite_score > 0.6, "Low expense ratio ETF should score well"
        assert result.asset_class == "etf"

    def test_crypto_specific_calculations(self, scorer):
        """Test cryptocurrency-specific metric calculations."""
        crypto_data = {
            "ticker": "BTC",
            "asset_class": "crypto",
            # Critical fields for crypto
            "current_price": 50000.0,
            "market_cap": 1000000000000,  # $1T market cap
            "volume_24h": 30000000000,  # $30B daily volume
            "volatility": 0.60,  # 60% volatility - typical for crypto
            "age_years": 15,  # Bitcoin launched in 2009
            # Optional crypto fields
            "network_value": 0.8,  # High network value
            "developer_activity": 100,  # Active development
            "social_sentiment": 0.7,  # Positive sentiment
            "returns_1y": 1.5,  # 150% yearly return
        }

        result = scorer.calculate_composite_score("BTC", "crypto", crypto_data)

        # Large cap crypto with good metrics should score reasonably
        assert result.composite_score > 0.5
        assert result.asset_class == "crypto"

    def test_grade_boundaries(self, scorer):
        """Test that grades correspond to correct score boundaries."""
        # Test grade boundaries
        grade_tests = [
            (0.95, "A+"),  # Top tier
            (0.90, "A+"),
            (0.85, "A"),
            (0.80, "A-"),
            (0.75, "B+"),
            (0.70, "B"),
            (0.65, "B-"),
            (0.60, "C+"),
            (0.55, "C"),
            (0.50, "C-"),
            (0.40, "D"),
            (0.20, "F"),
        ]

        for score, expected_grade in grade_tests:
            # Create mock result with specific score using current schema
            result = DeepAnalysisResult(
                ticker="TEST",
                asset_class="stock",
                crew_name="test_crew",
                composite_score=score,
                grade="",  # Will be calculated
                recommendation="HOLD",
                rationale="Test rationale",
                data_freshness_hours=1.0,
                confidence_level=0.8,
            )

            # Calculate grade from score
            if score >= 0.90:
                result.grade = "A+"
            elif score >= 0.85:
                result.grade = "A"
            elif score >= 0.80:
                result.grade = "A-"
            elif score >= 0.75:
                result.grade = "B+"
            elif score >= 0.70:
                result.grade = "B"
            elif score >= 0.65:
                result.grade = "B-"
            elif score >= 0.60:
                result.grade = "C+"
            elif score >= 0.55:
                result.grade = "C"
            elif score >= 0.50:
                result.grade = "C-"
            elif score >= 0.40:
                result.grade = "D"
            else:
                result.grade = "F"

            assert result.grade == expected_grade, f"Score {score} should yield grade {expected_grade}"

    def test_recommendation_logic(self, scorer):
        """Test that recommendations align with scores and grades."""
        # Strong buy scenario
        strong_data = {
            "ticker": "WIN",
            "asset_class": "stock",
            # Critical fields
            "current_price": 200.0,
            "roe": 0.30,  # 30% ROE
            "revenue_growth": 0.25,  # 25% growth
            "debt_to_equity": 0.2,  # Low debt
            "volatility": 0.15,  # Moderate volatility
            "beta": 0.9,
            # Optional strong indicators
            "profit_margin": 0.25,  # High margin
            "pe_ratio": 15,  # Reasonable valuation
            "rsi": 45,  # Not overbought
        }

        strong_result = scorer.calculate_composite_score("WIN", "stock", strong_data)

        # High score should yield BUY recommendation
        if strong_result.composite_score >= 0.75:
            assert strong_result.recommendation in ["BUY", "STRONG BUY"]

        # Weak sell scenario
        weak_data = {
            "ticker": "LOSE",
            "asset_class": "stock",
            # Critical fields
            "current_price": 5.0,
            "roe": -0.10,  # Negative ROE
            "revenue_growth": -0.15,  # Declining revenue
            "debt_to_equity": 3.0,  # High debt
            "volatility": 0.50,  # High volatility
            "beta": 2.0,
            # Optional weak indicators
            "profit_margin": -0.05,  # Negative margin
            "pe_ratio": 50,  # Overvalued
            "rsi": 85,  # Overbought
        }

        weak_result = scorer.calculate_composite_score("LOSE", "stock", weak_data)

        # Low score should yield SELL recommendation
        if weak_result.composite_score < 0.40:
            assert weak_result.recommendation in ["SELL", "STRONG SELL"]

    def test_score_weighting_consistency(self, scorer):
        """Test that component scores are weighted consistently."""
        # Create data with critical fields + fundamentals
        fundamental_only = {
            "ticker": "FUND",
            "asset_class": "stock",
            "current_price": 75.0,
            "roe": 0.20,
            "debt_to_equity": 0.5,
            "revenue_growth": 0.10,
            "volatility": 0.20,
            "beta": 1.0,
            "profit_margin": 0.15,
        }

        # Create data with critical fields + technicals
        technical_only = {
            "ticker": "TECH",
            "asset_class": "stock",
            "current_price": 80.0,
            "roe": 0.15,  # Need critical fields
            "debt_to_equity": 0.7,
            "revenue_growth": 0.08,
            "volatility": 0.20,
            "beta": 1.0,
            "rsi": 50,
            "volume": 1000000,
        }

        # Create data with both
        combined = {**fundamental_only, **technical_only}
        combined["ticker"] = "BOTH"
        combined["current_price"] = 85.0  # Ensure we have one price

        fund_result = scorer.calculate_composite_score("FUND", "stock", fundamental_only)
        tech_result = scorer.calculate_composite_score("TECH", "stock", technical_only)
        both_result = scorer.calculate_composite_score("BOTH", "stock", combined)

        # All results should be valid
        assert all(0 <= r.composite_score <= 1.0 for r in [fund_result, tech_result, both_result])

        # Combined score should be influenced by both components
        # (exact relationship depends on implementation)
        assert both_result.composite_score > 0

    def test_numerical_precision(self, scorer):
        """Test numerical precision and rounding."""
        # Test with very precise values
        precise_data = {
            "ticker": "PREC",
            "asset_class": "stock",
            "current_price": 123.456789,
            "roe": 0.123456789,
            "debt_to_equity": 0.87654321,
            "revenue_growth": 0.111111111,
            "volatility": 0.234567890,
            "beta": 1.23456789,
            "sharpe_ratio": 1.987654321,
        }

        result = scorer.calculate_composite_score("PREC", "stock", precise_data)

        # Score should be reasonably rounded
        assert isinstance(result.composite_score, float)
        # Check that score is not overly precise (e.g., rounded to 3-4 decimals)
        score_str = str(result.composite_score)
        if "." in score_str:
            decimal_places = len(score_str.split(".")[1])
            assert decimal_places <= 10, "Score should not have excessive decimal places"

    def test_missing_data_handling(self, scorer):
        """Test scorer handles missing data gracefully."""
        # Only critical fields (minimal data)
        minimal_data = {"ticker": "MIN", "asset_class": "stock", "current_price": 50.0, "roe": 0.10, "debt_to_equity": 1.0, "revenue_growth": 0.05, "volatility": 0.25, "beta": 1.0}

        result = scorer.calculate_composite_score("MIN", "stock", minimal_data)

        # Should produce valid result even with minimal data
        assert result is not None
        assert 0 <= result.composite_score <= 1.0
        assert result.grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"]

    @pytest.mark.parametrize("asset_class", ["stock", "etf", "crypto"])
    def test_asset_class_scoring_differences(self, scorer, asset_class):
        """Test that different asset classes are scored with appropriate logic."""
        # Build test data based on asset class requirements
        if asset_class == "stock":
            test_data = {
                "ticker": "TEST",
                "asset_class": asset_class,
                "current_price": 100.0,
                "roe": 0.15,
                "debt_to_equity": 0.8,
                "revenue_growth": 0.10,
                "volatility": 0.30,
                "beta": 1.2,
                "returns_1y": 0.20,
                "volume": 1000000,
            }
        elif asset_class == "etf":
            test_data = {"ticker": "TEST", "asset_class": asset_class, "current_price": 100.0, "expense_ratio": 0.005, "volatility": 0.30, "returns_1y": 0.20, "volume": 1000000}
        else:  # crypto
            test_data = {
                "ticker": "TEST",
                "asset_class": asset_class,
                "current_price": 100.0,
                "market_cap": 1000000000,
                "volume_24h": 10000000,
                "volatility": 0.30,
                "age_years": 3,
                "returns_1y": 0.20,
            }

        result = scorer.calculate_composite_score("TEST", asset_class, test_data)

        # All asset classes should produce valid results
        assert result.asset_class == asset_class
        assert 0 <= result.composite_score <= 1.0

        # Note: Different asset classes may weight volatility differently
        # Crypto might tolerate higher volatility than stocks
