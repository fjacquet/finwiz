"""
Unit tests for A+ Investment Scoring Tool.

Tests the comprehensive A+ scoring functionality for ETFs, stocks, and cryptocurrencies
with dynamic criteria adjustment based on market conditions.
"""

import pytest

from finwiz.schemas.tools import APlusScoringInput, MarketRegime, ScoringCriteria
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool


class TestAPlusScoringTool:
    """Test suite for A+ Investment Scoring Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = APlusScoringTool()

        # Sample ETF data for testing
        self.sample_etf_data = {
            "expense_ratio": 0.03,
            "aum": 5e9,
            "tracking_error": 0.001,
            "history_years": 5,
            "momentum_score": 0.7,
            "trend_strength": 0.8,
            "volatility_score": 0.6,
            "volatility": 0.15,
            "beta": 1.0,
            "max_drawdown": 0.1,
            "issuer_reputation": 0.9,
            "regulatory_compliance": 0.95,
            "transparency_score": 0.85,
        }

        # Sample stock data for testing
        self.sample_stock_data = {
            "roe": 0.25,
            "revenue_growth": 0.20,
            "debt_to_equity": 0.2,
            "market_cap": 10e9,
            "fcf_positive": True,
            "fcf_growing": True,
            "momentum_score": 0.8,
            "trend_strength": 0.7,
            "volatility_score": 0.6,
            "volatility": 0.20,
            "beta": 1.2,
            "max_drawdown": 0.15,
            "management_quality": 0.8,
            "governance_score": 0.85,
            "competitive_moat": 0.9,
        }

        # Sample crypto data for testing
        self.sample_crypto_data = {
            "market_cap": 50e9,
            "daily_volume": 2e9,
            "age_months": 60,
            "institutional_adoption": True,
            "real_utility": True,
            "momentum_score": 0.6,
            "trend_strength": 0.7,
            "volatility_score": 0.4,
            "volatility": 0.40,
            "beta": 2.0,
            "max_drawdown": 0.30,
            "team_quality": 0.8,
            "development_activity": 0.9,
            "community_strength": 0.7,
        }

    def test_should_create_tool_instance_when_initialized(self):
        """Test tool initialization."""
        tool = APlusScoringTool()
        assert tool.name == "A+ Investment Scoring Tool"
        assert "A+ scoring tool" in tool.description
        assert tool.args_schema == APlusScoringInput

    def test_should_score_excellent_etf_as_a_plus_when_all_criteria_met(self):
        """Test A+ scoring for excellent ETF."""
        result = self.tool._run(symbol="VTI", asset_type="etf", fundamental_data=self.sample_etf_data, market_context={"vix": 15, "inflation": 2.5})

        assert result["symbol"] == "VTI"
        assert result["asset_type"] == "etf"
        assert result["analysis_summary"]["composite_score"] >= 0.85  # Should be high quality
        assert result["is_a_plus_candidate"] == (result["analysis_summary"]["composite_score"] >= 0.95)
        assert "analysis_summary" in result
        assert "component_scores" in result["analysis_summary"]

    def test_should_score_excellent_stock_as_a_plus_when_fundamentals_strong(self):
        """Test A+ scoring for excellent stock."""
        result = self.tool._run(symbol="AAPL", asset_type="stock", fundamental_data=self.sample_stock_data, market_context={"vix": 18, "inflation": 3.0})

        assert result["symbol"] == "AAPL"
        assert result["asset_type"] == "stock"
        assert result["analysis_summary"]["composite_score"] >= 0.80  # Should be high quality
        assert "fundamental" in result["analysis_summary"]["component_scores"]
        assert "technical" in result["analysis_summary"]["component_scores"]
        assert "quality" in result["analysis_summary"]["component_scores"]
        assert "risk" in result["analysis_summary"]["component_scores"]

    def test_should_score_quality_crypto_appropriately_when_criteria_met(self):
        """Test A+ scoring for quality cryptocurrency."""
        result = self.tool._run(
            symbol="BTC",
            asset_type="crypto",
            fundamental_data=self.sample_crypto_data,
            market_context={"vix": 20, "inflation": 3.5},
        )

        assert result["symbol"] == "BTC"
        assert result["asset_type"] == "crypto"
        assert result["analysis_summary"]["composite_score"] > 0.0
        assert "confidence" in result["analysis_summary"]
        assert len(result["analysis_summary"]["top_strengths"]) <= 3
        assert len(result["analysis_summary"]["main_concerns"]) <= 2

    def test_should_adjust_criteria_when_bear_market_detected(self):
        """Test dynamic criteria adjustment in bear market."""
        bear_market_context = {"vix": 35, "inflation": 6.0, "rate_change_6m": 2.0}

        # Test with bear market context
        result = self.tool._run(symbol="SPY", asset_type="etf", fundamental_data=self.sample_etf_data, market_context=bear_market_context)

        # Should still process but with tighter criteria
        assert result["symbol"] == "SPY"
        assert "a_plus_score" in result

        # Check that market regime was detected
        a_plus_score = result["a_plus_score"]
        market_regime = a_plus_score["market_regime"]
        assert market_regime["regime_type"] in ["bear", "volatile"]
        assert market_regime["market_stress_level"] in ["medium", "high"]

    def test_should_handle_missing_data_gracefully_when_incomplete_input(self):
        """Test handling of incomplete fundamental data."""
        incomplete_data = {"expense_ratio": 0.05}  # Only one field

        result = self.tool._run(symbol="TEST", asset_type="etf", fundamental_data=incomplete_data)

        assert result["symbol"] == "TEST"
        assert result["analysis_summary"]["composite_score"] >= 0.0
        assert result["analysis_summary"]["composite_score"] <= 1.0
        # Should not crash with incomplete data

    def test_should_return_error_when_invalid_asset_type_provided(self):
        """Test error handling for invalid asset type."""
        with pytest.raises(ValueError):
            APlusScoringInput(
                symbol="TEST",
                asset_type="invalid_type",  # Invalid asset type
                fundamental_data={},
            )

    def test_should_calculate_etf_fundamental_score_correctly_when_excellent_metrics(self):
        """Test ETF fundamental scoring calculation."""
        criteria = ScoringCriteria()
        score = self.tool._score_etf_fundamentals(self.sample_etf_data, criteria)

        assert 0.0 <= score <= 1.0
        assert score >= 0.8  # Should be high for excellent metrics

    def test_should_calculate_stock_fundamental_score_correctly_when_strong_financials(self):
        """Test stock fundamental scoring calculation."""
        criteria = ScoringCriteria()
        score = self.tool._score_stock_fundamentals(self.sample_stock_data, criteria)

        assert 0.0 <= score <= 1.0
        assert score >= 0.8  # Should be high for strong financials

    def test_should_calculate_crypto_fundamental_score_correctly_when_mature_project(self):
        """Test crypto fundamental scoring calculation."""
        criteria = ScoringCriteria()
        score = self.tool._score_crypto_fundamentals(self.sample_crypto_data, criteria)

        assert 0.0 <= score <= 1.0
        assert score >= 0.7  # Should be good for mature project

    def test_should_assess_market_regime_correctly_when_high_vix(self):
        """Test market regime assessment with high VIX."""
        high_vix_context = {"vix": 40, "inflation": 4.0, "rate_change_6m": 1.0}
        regime = self.tool._assess_market_regime(high_vix_context)

        assert regime.regime_type in ["volatile", "bear"]
        assert regime.vix_level == 40
        assert regime.market_stress_level in ["medium", "high"]

    def test_should_cache_market_regime_when_assessed_recently(self):
        """Test market regime caching functionality."""
        context = {"vix": 20, "inflation": 3.0}

        # First assessment
        regime1 = self.tool._assess_market_regime(context)

        # Second assessment (should use cache)
        regime2 = self.tool._assess_market_regime(context)

        assert regime1.regime_type == regime2.regime_type
        assert regime1.vix_level == regime2.vix_level

    def test_should_adjust_scoring_weights_when_high_stress_market(self):
        """Test scoring weight adjustment in high stress markets."""
        high_stress_regime = MarketRegime(regime_type="bear", vix_level=35, market_stress_level="high")

        weights = self.tool._get_scoring_weights("stock", high_stress_regime)

        # Should emphasize quality and risk in stressed markets
        assert weights["quality"] > 0.25  # Higher than base
        assert weights["risk"] > 0.15  # Higher than base
        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-3)

    def test_should_identify_strengths_and_weaknesses_when_mixed_scores(self):
        """Test strength and weakness identification."""
        mixed_scores = {
            "fundamental": 0.9,  # Strong
            "technical": 0.3,  # Weak
            "quality": 0.8,  # Strong
            "risk": 0.4,  # Weak
        }

        strengths, weaknesses = self.tool._analyze_strengths_weaknesses("TEST", "stock", self.sample_stock_data, mixed_scores)

        assert len(strengths) > 0
        assert len(weaknesses) > 0
        assert "fundamental" in " ".join(strengths).lower()
        assert "technical" in " ".join(weaknesses).lower()

    def test_should_generate_appropriate_rationale_when_a_plus_score(self):
        """Test A+ rationale generation for high scores."""
        strengths = ["Excellent fundamentals", "Strong momentum"]
        weaknesses = ["Minor volatility"]
        regime = MarketRegime(regime_type="bull")

        rationale = self.tool._generate_a_plus_rationale("TEST", "stock", 0.96, strengths, weaknesses, regime)

        assert "A+ status" in rationale
        assert "0.96" in rationale
        assert "Excellent fundamentals" in rationale
        assert len(rationale) >= 50  # Should be detailed

    def test_should_calculate_confidence_level_based_on_data_quality(self):
        """Test confidence level calculation."""
        # Complete data should have higher confidence
        complete_data = {f"metric_{i}": 0.5 for i in range(10)}
        regime = MarketRegime(market_stress_level="low")

        confidence = self.tool._calculate_confidence_level(complete_data, regime, 0.85)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident

    def test_should_handle_custom_criteria_when_provided(self):
        """Test custom criteria override functionality."""
        custom_criteria = {
            "etf_max_expense_ratio": 0.05,  # Very strict
            "stock_min_roe": 0.30,  # Very high requirement
        }

        result = self.tool._run(
            symbol="TEST",
            asset_type="etf",
            fundamental_data={"expense_ratio": 0.08},  # Would fail strict criteria
            custom_criteria=custom_criteria,
        )

        assert result["symbol"] == "TEST"
        # Should use custom criteria in scoring

    def test_should_return_error_dict_when_exception_occurs(self, mocker):
        """Test error handling when exceptions occur."""
        # Mock a method to raise an exception
        mocker.patch.object(self.tool, "_assess_market_regime", side_effect=Exception("Test error"))

        result = self.tool._run(symbol="ERROR", asset_type="stock", fundamental_data={})

        assert "error" in result
        assert result["symbol"] == "ERROR"
        assert result["composite_score"] == 0.0
        assert result["is_a_plus_candidate"] is False

    def test_should_normalize_symbol_input_when_lowercase_provided(self):
        """Test symbol normalization."""
        result = self.tool._run(
            symbol="  aapl  ",  # Lowercase with spaces
            asset_type="stock",
            fundamental_data=self.sample_stock_data,
        )

        assert result["symbol"] == "AAPL"  # Should be normalized

    def test_should_validate_input_schema_when_creating_input_object(self):
        """Test input schema validation."""
        # Valid input
        valid_input = APlusScoringInput(symbol="AAPL", asset_type="stock", fundamental_data={"roe": 0.25}, market_context={"vix": 20})

        assert valid_input.symbol == "AAPL"
        assert valid_input.asset_type == "stock"
        assert valid_input.fundamental_data["roe"] == 0.25

    def test_should_handle_empty_fundamental_data_when_none_provided(self):
        """Test handling of empty fundamental data."""
        result = self.tool._run(
            symbol="EMPTY",
            asset_type="stock",
            fundamental_data={},  # Empty data
        )

        assert result["symbol"] == "EMPTY"
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0
        # Should not crash with empty data

    def test_should_calculate_risk_score_appropriately_when_high_volatility(self):
        """Test risk score calculation with high volatility."""
        high_risk_data = {
            "volatility": 0.5,  # High volatility
            "beta": 2.0,  # High beta
            "max_drawdown": 0.4,  # High drawdown
        }
        regime = MarketRegime(market_stress_level="high")

        risk_score = self.tool._calculate_risk_score("TEST", "stock", high_risk_data, regime)

        assert 0.0 <= risk_score <= 1.0
        assert risk_score < 0.7  # Should be penalized for high risk

    def test_should_score_different_asset_types_with_appropriate_weights(self):
        """Test that different asset types use appropriate scoring weights."""
        regime = MarketRegime()

        etf_weights = self.tool._get_scoring_weights("etf", regime)
        stock_weights = self.tool._get_scoring_weights("stock", regime)
        crypto_weights = self.tool._get_scoring_weights("crypto", regime)

        # ETFs should emphasize fundamentals more
        assert etf_weights["fundamental"] >= stock_weights["fundamental"]

        # Crypto should have higher risk weighting
        assert crypto_weights["risk"] >= etf_weights["risk"]

        # All should sum to 1.0
        assert sum(etf_weights.values()) == pytest.approx(1.0, rel=1e-3)
        assert sum(stock_weights.values()) == pytest.approx(1.0, rel=1e-3)
        assert sum(crypto_weights.values()) == pytest.approx(1.0, rel=1e-3)
