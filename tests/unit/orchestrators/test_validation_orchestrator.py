"""
Unit tests for ValidationOrchestrator.

Tests cover:
- Reporter input validation
- Core analysis availability checking
- Market conditions extraction
- Market context extraction
"""

import pytest

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator


class TestValidationOrchestrator:
    """Test suite for ValidationOrchestrator."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState instance for testing."""
        return FinwizState()

    @pytest.fixture
    def orchestrator(self, state, mocker):
        """Create a ValidationOrchestrator instance with mocked dependencies."""
        integration_manager = mocker.Mock()
        data_accessor = mocker.Mock()
        return ValidationOrchestrator(
            state,
            integration_manager=integration_manager,
            data_accessor=data_accessor,
        )

    def test_should_validate_reporter_input_successfully(self, orchestrator, mocker):
        """Test successful reporter input validation."""
        # Arrange
        consolidated_data = {
            "consolidated_crew_data": {
                "stock": [{"ticker": "AAPL"}],
                "etf": [{"ticker": "SPY"}],
            },
            "market_sentiment": {"overall": "positive"},
            "ticker_validation": {"valid": True},
        }

        orchestrator.data_accessor.get_consolidated_reporter_input.return_value = consolidated_data
        orchestrator.integration_manager.get_crew_data_with_freshness_check.return_value = {"data": "test"}

        # Act
        result = orchestrator.pre_validate_reporter_input()

        # Assert
        assert result["success"] is True
        assert result["core_analysis_available"] is True
        assert result["core_analysis_count"] == 2
        assert orchestrator.state.consolidated_data == consolidated_data

    def test_should_handle_missing_data_accessor(self, orchestrator):
        """Test validation when data_accessor is None."""
        # Arrange
        orchestrator.data_accessor = None

        # Act
        result = orchestrator.pre_validate_reporter_input()

        # Assert
        assert result["success"] is True
        assert result["core_analysis_count"] == 0

    def test_should_handle_data_accessor_failure(self, orchestrator):
        """Test validation when data_accessor raises exception."""
        # Arrange
        orchestrator.data_accessor.get_consolidated_reporter_input.side_effect = Exception("Data access failed")

        # Act
        result = orchestrator.pre_validate_reporter_input()

        # Assert
        assert result["success"] is True
        assert result["core_analysis_count"] == 0

    def test_should_check_core_analysis_availability(self, orchestrator):
        """Test core analysis availability checking."""
        # Arrange
        orchestrator.integration_manager.get_crew_data_with_freshness_check.side_effect = [
            {"data": "stock"},  # stock available
            None,  # etf not available
            {"data": "crypto"},  # crypto available
        ]

        # Act
        result = orchestrator.check_core_analysis_availability()

        # Assert
        assert result["any_available"] is True
        assert result["stock_available"] is True
        assert result["etf_available"] is False
        assert result["crypto_available"] is True
        assert result["available_crews"] == ["stock", "crypto"]
        assert result["total_available"] == 2

    def test_should_fallback_to_state_flags_on_integration_failure(self, orchestrator, state):
        """Test fallback to state flags when integration manager fails."""
        # Arrange
        orchestrator.integration_manager.get_crew_data_with_freshness_check.side_effect = Exception("Integration failed")
        state.stock_analysis_success = True
        state.etf_analysis_success = False
        state.crypto_analysis_success = True

        # Act
        result = orchestrator.check_core_analysis_availability()

        # Assert
        assert result["stock_available"] is True
        assert result["etf_available"] is False
        assert result["crypto_available"] is True

    def test_should_identify_failed_crews(self, orchestrator, state):
        """Test identification of failed crews."""
        # Arrange
        state.stock_analysis_error = "Stock analysis failed"
        state.etf_analysis_error = None
        state.crypto_analysis_error = "Crypto analysis failed"

        # Act
        result = orchestrator.check_core_analysis_availability()

        # Assert
        assert "stock" in result["failed_crews"]
        assert "crypto" in result["failed_crews"]
        assert "etf" not in result["failed_crews"]
        assert result["total_failed"] == 2

    def test_should_identify_disabled_crews(self, orchestrator, state):
        """Test identification of disabled crews."""
        # Arrange
        state.stock_analysis_disabled = True
        state.etf_analysis_disabled = False
        state.crypto_analysis_disabled = True

        # Act
        result = orchestrator.check_core_analysis_availability()

        # Assert
        assert "stock" in result["disabled_crews"]
        assert "crypto" in result["disabled_crews"]
        assert "etf" not in result["disabled_crews"]
        assert result["total_disabled"] == 2

    def test_should_extract_market_conditions(self, orchestrator, state):
        """Test market conditions extraction."""
        # Arrange
        state.stock_analysis_result = {"sentiment": "positive"}
        state.etf_analysis_result = {"trends": ["tech"]}
        state.crypto_analysis_result = None

        # Act
        result = orchestrator.extract_market_conditions()

        # Assert
        assert "stock_market_sentiment" in result
        assert "sector_trends" in result
        assert "crypto_market_dynamics" not in result

    def test_should_extract_market_context_from_stock_analysis(self, orchestrator):
        """Test market context extraction from stock analysis."""
        # Arrange
        core_analysis_data = {
            "stock_analysis": {
                "market_sentiments": [
                    {"sentiment": "positive"},
                    {"sentiment": "bullish"},
                    {"sentiment": "negative"},
                ],
                "sector_analysis": {"tech": "strong"},
            }
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert result["overall_sentiment"] == "positive"
        assert result["sector_analysis"] == {"tech": "strong"}

    def test_should_extract_market_context_from_etf_analysis(self, orchestrator):
        """Test market context extraction from ETF analysis."""
        # Arrange
        core_analysis_data = {
            "etf_analysis": {
                "sector_trends": ["tech growth", "energy decline"],
            }
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert "tech growth" in result["market_trends"]
        assert "energy decline" in result["market_trends"]

    def test_should_extract_market_context_from_crypto_analysis(self, orchestrator):
        """Test market context extraction from crypto analysis."""
        # Arrange
        core_analysis_data = {
            "crypto_analysis": {
                "market_dynamics": "bullish momentum",
            }
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert any("Crypto:" in trend for trend in result["market_trends"])

    def test_should_extract_risk_factors_from_all_analyses(self, orchestrator):
        """Test risk factors extraction from multiple analyses."""
        # Arrange
        core_analysis_data = {
            "stock_analysis": {
                "risk_factors": ["market volatility", "regulatory risk"],
            },
            "etf_analysis": {
                "risk_factors": ["tracking error"],
            },
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert "market volatility" in result["risk_factors"]
        assert "regulatory risk" in result["risk_factors"]
        assert "tracking error" in result["risk_factors"]

    def test_should_extract_opportunities_from_all_analyses(self, orchestrator):
        """Test opportunities extraction from multiple analyses."""
        # Arrange
        core_analysis_data = {
            "stock_analysis": {
                "opportunities": ["AI growth", "cloud expansion"],
            },
            "crypto_analysis": {
                "opportunities": ["DeFi adoption"],
            },
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert "AI growth" in result["opportunities"]
        assert "cloud expansion" in result["opportunities"]
        assert "DeFi adoption" in result["opportunities"]

    def test_should_handle_empty_core_analysis_data(self, orchestrator):
        """Test handling of empty core analysis data."""
        # Arrange
        core_analysis_data = {}

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert
        assert result["overall_sentiment"] == "neutral"
        assert result["market_trends"] == []
        assert result["risk_factors"] == []
        assert result["opportunities"] == []

    def test_should_handle_malformed_core_analysis_data(self, orchestrator):
        """Test handling of malformed core analysis data."""
        # Arrange
        core_analysis_data = {
            "stock_analysis": "not a dict",  # Invalid format
            "etf_analysis": {
                "risk_factors": "not a list",  # Invalid format
            },
        }

        # Act
        result = orchestrator.extract_market_context_from_core_analysis(core_analysis_data)

        # Assert - Should not raise exception
        assert result is not None
        assert "overall_sentiment" in result
