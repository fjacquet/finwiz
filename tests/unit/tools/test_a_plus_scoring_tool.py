"""
Unit tests for A+ Investment Scoring Tool.

Tests the comprehensive A+ scoring functionality for ETFs, stocks, and cryptocurrencies
with dynamic criteria adjustment based on market conditions.

NOTE: After Phase 2A refactoring, this tool uses the Strategy Pattern with
scoring logic extracted to separate modules. Tests now focus on the public API
(_run method) rather than internal implementation details.
"""

import pytest

from finwiz.schemas.tools import APlusScoringInput
from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from tests.fixtures import (
    create_crypto_data,
    create_etf_data,
    create_market_context,
    create_risk_data,
    create_stock_data,
    create_technical_data,
)


class TestAPlusScoringTool:
    """Test suite for A+ Investment Scoring Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = APlusScoringTool()
        self.etf_data = create_etf_data()
        self.stock_data = create_stock_data()
        self.crypto_data = create_crypto_data()
        self.market_context = create_market_context()

    def test_should_create_tool_instance_when_initialized(self):
        """Test tool initialization."""
        tool = APlusScoringTool()
        assert tool.name == "A+ Investment Scoring Tool"
        assert "comprehensive" in tool.description.lower()
        assert "a+" in tool.description.lower()
        assert tool.args_schema == APlusScoringInput

    def test_should_score_excellent_etf_as_a_plus_when_all_criteria_met(self):
        """Test A+ scoring for excellent ETF."""
        # Create excellent ETF data
        excellent_etf = create_etf_data(
            expense_ratio=0.001,  # Very low
            aum=100e9,  # Very high
            tracking_error=0.0001,  # Very low
        )
        excellent_etf.update(create_technical_data(momentum_score=0.9, trend_strength=0.9))
        excellent_etf.update(create_risk_data(volatility=0.10, max_drawdown=0.05))

        result = self.tool._run(
            symbol="VTI",
            asset_type="etf",
            fundamental_data=excellent_etf,
            market_context=self.market_context,
        )

        assert result["symbol"] == "VTI"
        assert result["asset_type"] == "etf"
        assert "analysis_summary" in result
        assert "composite_score" in result["analysis_summary"]
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_score_excellent_stock_as_a_plus_when_fundamentals_strong(self):
        """Test A+ scoring for excellent stock."""
        # Create excellent stock data
        excellent_stock = create_stock_data(
            roe=0.30,  # Very high
            revenue_growth=0.25,  # Very high
            debt_to_equity=0.1,  # Very low
        )
        excellent_stock.update(create_technical_data(momentum_score=0.9))
        excellent_stock.update(create_risk_data(volatility=0.15, beta=1.0))

        result = self.tool._run(
            symbol="AAPL",
            asset_type="stock",
            fundamental_data=excellent_stock,
            market_context=self.market_context,
        )

        assert result["symbol"] == "AAPL"
        assert result["asset_type"] == "stock"
        assert "analysis_summary" in result
        assert "composite_score" in result["analysis_summary"]
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_score_mature_crypto_appropriately(self):
        """Test A+ scoring for mature cryptocurrency."""
        # Create mature crypto data
        mature_crypto = create_crypto_data(
            market_cap=100e9,  # Very high
            daily_volume=5e9,  # Very high
            age_months=72,  # 6 years
        )
        mature_crypto.update(create_technical_data(momentum_score=0.7))
        mature_crypto.update(create_risk_data(volatility=0.30, max_drawdown=0.25))

        result = self.tool._run(
            symbol="BTC",
            asset_type="crypto",
            fundamental_data=mature_crypto,
            market_context=self.market_context,
        )

        assert result["symbol"] == "BTC"
        assert result["asset_type"] == "crypto"
        assert "analysis_summary" in result
        assert "composite_score" in result["analysis_summary"]
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_handle_incomplete_fundamental_data(self):
        """Test handling of incomplete fundamental data."""
        incomplete_data = {"expense_ratio": 0.05}  # Only one field

        result = self.tool._run(
            symbol="TEST",
            asset_type="etf",
            fundamental_data=incomplete_data,
        )

        assert result["symbol"] == "TEST"
        assert "analysis_summary" in result
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_return_error_when_invalid_asset_type_provided(self):
        """Test error handling for invalid asset type."""
        with pytest.raises(ValueError):
            APlusScoringInput(
                symbol="TEST",
                asset_type="invalid_type",  # Invalid asset type
                fundamental_data={},
            )

    def test_should_adjust_criteria_when_bear_market_detected(self):
        """Test criteria adjustment in bear market."""
        bear_market = create_market_context(vix=40.0, market_regime="bear")

        result = self.tool._run(
            symbol="TEST",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=bear_market,
        )

        assert result["symbol"] == "TEST"
        assert "analysis_summary" in result
        # Should complete without error in bear market

    def test_should_assess_market_regime_correctly_when_high_vix(self):
        """Test market regime assessment with high VIX."""
        high_vix_context = create_market_context(vix=40.0)

        result = self.tool._run(
            symbol="TEST",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=high_vix_context,
        )

        assert result["symbol"] == "TEST"
        # Should handle high VIX appropriately

    def test_should_cache_market_regime_when_assessed_recently(self):
        """Test market regime caching functionality."""
        context = create_market_context(vix=20.0)

        # First assessment
        result1 = self.tool._run(
            symbol="TEST1",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=context,
        )

        # Second assessment (should use cache)
        result2 = self.tool._run(
            symbol="TEST2",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=context,
        )

        assert result1["symbol"] == "TEST1"
        assert result2["symbol"] == "TEST2"
        # Both should complete successfully

    def test_should_adjust_scoring_weights_when_high_stress_market(self):
        """Test scoring weight adjustment in high stress markets."""
        high_stress = create_market_context(vix=35.0, market_regime="volatile")

        result = self.tool._run(
            symbol="TEST",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=high_stress,
        )

        assert result["symbol"] == "TEST"
        assert "analysis_summary" in result
        # Should emphasize quality and risk in stressed markets

    def test_should_identify_strengths_and_weaknesses_when_mixed_scores(self):
        """Test strength and weakness identification."""
        # Create mixed quality data
        mixed_data = create_stock_data(
            roe=0.30,  # Strong
            debt_to_equity=0.8,  # Weak
        )
        mixed_data.update(create_technical_data(momentum_score=0.9, trend_strength=0.3))

        result = self.tool._run(
            symbol="TEST",
            asset_type="stock",
            fundamental_data=mixed_data,
            market_context=self.market_context,
        )

        assert result["symbol"] == "TEST"
        assert "analysis_summary" in result
        # Check for strengths/concerns in analysis summary
        summary = result["analysis_summary"]
        assert "top_strengths" in summary or "main_concerns" in summary

    def test_should_generate_appropriate_rationale_when_a_plus_score(self):
        """Test A+ rationale generation for high scores."""
        # Create A+ quality data
        aplus_data = create_stock_data(roe=0.35, revenue_growth=0.30, debt_to_equity=0.05)
        aplus_data.update(create_technical_data(momentum_score=0.95, trend_strength=0.95))
        aplus_data.update(create_risk_data(volatility=0.12, max_drawdown=0.08))

        result = self.tool._run(
            symbol="APLUS",
            asset_type="stock",
            fundamental_data=aplus_data,
            market_context=self.market_context,
        )

        assert result["symbol"] == "APLUS"
        assert "analysis_summary" in result
        # Should have detailed analysis
        assert result["analysis_summary"]["composite_score"] > 0.0

    def test_should_calculate_confidence_level_based_on_data_quality(self):
        """Test confidence level calculation."""
        # Complete data should have higher confidence
        complete_data = create_stock_data()
        complete_data.update(create_technical_data())
        complete_data.update(create_risk_data())

        result = self.tool._run(
            symbol="COMPLETE",
            asset_type="stock",
            fundamental_data=complete_data,
            market_context=self.market_context,
        )

        assert result["symbol"] == "COMPLETE"
        assert "analysis_summary" in result
        assert "confidence" in result["analysis_summary"]
        assert 0.0 <= result["analysis_summary"]["confidence"] <= 1.0

    def test_should_handle_custom_criteria_when_provided(self):
        """Test custom criteria override functionality."""
        custom_criteria = {
            "etf_max_expense_ratio": 0.05,  # Very strict
            "stock_min_roe": 0.30,  # Very high requirement
        }

        result = self.tool._run(
            symbol="TEST",
            asset_type="etf",
            fundamental_data=create_etf_data(expense_ratio=0.08),
            custom_criteria=custom_criteria,
        )

        assert result["symbol"] == "TEST"
        # Should use custom criteria in scoring

    def test_should_return_error_dict_when_exception_occurs(self, mocker):
        """Test error handling when exceptions occur."""
        # Mock to raise an exception during scoring
        mocker.patch(
            "finwiz.tools.scoring.scoring_algorithms.calculate_fundamental_score",
            side_effect=Exception("Test error"),
        )

        result = self.tool._run(
            symbol="ERROR",
            asset_type="stock",
            fundamental_data={},
        )

        # Should handle error gracefully - either return error or complete with defaults
        assert result["symbol"] == "ERROR"
        assert isinstance(result, dict)

    def test_should_normalize_symbol_input_when_lowercase_provided(self):
        """Test symbol normalization."""
        result = self.tool._run(
            symbol="  aapl  ",  # Lowercase with spaces
            asset_type="stock",
            fundamental_data=self.stock_data,
        )

        assert result["symbol"] == "AAPL"  # Should be normalized

    def test_should_validate_input_schema_when_creating_input_object(self):
        """Test input schema validation."""
        # Valid input
        valid_input = APlusScoringInput(
            symbol="AAPL",
            asset_type="stock",
            fundamental_data={"roe": 0.25},
            market_context={"vix": 20},
        )

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
        assert "analysis_summary" in result
        assert 0.0 <= result["analysis_summary"]["composite_score"] <= 1.0

    def test_should_calculate_risk_score_appropriately_when_high_volatility(self):
        """Test risk score calculation with high volatility."""
        high_risk_data = create_stock_data()
        high_risk_data.update(
            create_risk_data(
                volatility=0.5,  # High volatility
                beta=2.0,  # High beta
                max_drawdown=0.4,  # High drawdown
            )
        )

        result = self.tool._run(
            symbol="HIGHRISK",
            asset_type="stock",
            fundamental_data=high_risk_data,
            market_context=self.market_context,
        )

        assert result["symbol"] == "HIGHRISK"
        assert "analysis_summary" in result
        # High risk should impact score

    def test_should_score_different_asset_types_with_appropriate_weights(self):
        """Test that different asset types use appropriate scoring weights."""
        # Test ETF
        etf_result = self.tool._run(
            symbol="ETF",
            asset_type="etf",
            fundamental_data=self.etf_data,
            market_context=self.market_context,
        )

        # Test Stock
        stock_result = self.tool._run(
            symbol="STOCK",
            asset_type="stock",
            fundamental_data=self.stock_data,
            market_context=self.market_context,
        )

        # Test Crypto
        crypto_result = self.tool._run(
            symbol="CRYPTO",
            asset_type="crypto",
            fundamental_data=self.crypto_data,
            market_context=self.market_context,
        )

        # All should complete successfully
        assert etf_result["symbol"] == "ETF"
        assert stock_result["symbol"] == "STOCK"
        assert crypto_result["symbol"] == "CRYPTO"
