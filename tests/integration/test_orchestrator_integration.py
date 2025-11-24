"""Integration tests for DataSourceOrchestrator with DeepAnalysisOrchestrator."""

import pytest
from pytest import approx

from finwiz.data.adapters.base_adapter import FundamentalData
from finwiz.data.data_source_orchestrator import DataSourceOrchestrator


class TestOrchestratorIntegration:
    """Test DataSourceOrchestrator integration with DeepAnalysisOrchestrator."""

    @pytest.mark.asyncio
    async def test_should_integrate_with_deep_analysis_orchestrator(self, mocker):
        """Test that DataSourceOrchestrator integrates correctly with DeepAnalysisOrchestrator."""
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Mock the YFinanceAdapter to return fundamental data
        from datetime import datetime

        mock_adapter = mocker.AsyncMock()
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(
            return_value=FundamentalData(
                ticker="AAPL",
                source="YFinance",
                timestamp=datetime.now(),
                confidence=1.0,
                return_on_equity=0.25,
                debt_to_equity=0.5,
                revenue_growth=0.15,
                profit_margin=0.20,
            )
        )

        orchestrator.adapters = [mock_adapter]

        # Act
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Assert
        assert result.ticker == "AAPL"
        assert result.return_on_equity == approx(0.25)
        assert result.debt_to_equity == approx(0.5)
        assert result.revenue_growth == approx(0.15)
        assert result.profit_margin == approx(0.20)
        assert result.is_complete()
        assert result.confidence > 0.9  # High confidence for primary source
        assert "YFinance" in result.sources_succeeded
        assert result.lineage.return_on_equity_source == "YFinance"

    @pytest.mark.asyncio
    async def test_should_handle_partial_data_from_orchestrator(self, mocker):
        """Test handling of partial data from DataSourceOrchestrator."""
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Mock adapter returns partial data
        from datetime import datetime

        mock_adapter = mocker.AsyncMock()
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(
            return_value=FundamentalData(
                ticker="AAPL",
                source="YFinance",
                timestamp=datetime.now(),
                confidence=1.0,
                return_on_equity=0.25,
                debt_to_equity=None,  # Missing
                revenue_growth=0.15,
                profit_margin=None,  # Missing
            )
        )

        orchestrator.adapters = [mock_adapter]

        # Act
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Assert
        assert result.return_on_equity == approx(0.25)
        assert result.revenue_growth == approx(0.15)
        # Fallback should fill missing fields
        assert result.debt_to_equity is not None  # Filled by industry averages
        assert result.profit_margin is not None  # Filled by industry averages
        assert result.used_fallback is True
        assert result.confidence < 0.9  # Lower confidence due to fallback

    @pytest.mark.asyncio
    async def test_should_track_data_lineage_in_integration(self, mocker):
        """Test that data lineage is properly tracked through integration."""
        # Arrange
        orchestrator = DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        # Mock adapter
        from datetime import datetime

        mock_adapter = mocker.AsyncMock()
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(
            return_value=FundamentalData(
                ticker="AAPL",
                source="YFinance",
                timestamp=datetime.now(),
                confidence=1.0,
                return_on_equity=0.25,
                debt_to_equity=0.5,
                revenue_growth=0.15,
                profit_margin=0.20,
            )
        )

        orchestrator.adapters = [mock_adapter]

        # Act
        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Assert - verify lineage tracking
        lineage_dict = result.lineage.to_dict()
        assert lineage_dict["return_on_equity"] == "YFinance"
        assert lineage_dict["debt_to_equity"] == "YFinance"
        assert lineage_dict["revenue_growth"] == "YFinance"
        assert lineage_dict["profit_margin"] == "YFinance"

        # Verify metadata
        assert result.confidence > 0.9
        assert result.sources_attempted == ["YFinance"]
        assert result.sources_succeeded == ["YFinance"]
        assert result.sources_failed == []
