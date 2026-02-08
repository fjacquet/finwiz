"""Unit tests for DataSourceOrchestrator."""

from datetime import datetime

import pytest

from finwiz.data.adapters.base_adapter import (
    FundamentalData,
    TimeoutError,
)
from finwiz.data.data_source_orchestrator import (
    DataSourceOrchestrator,
    OrchestrationResult,
)


class TestOrchestrationResult:
    """Test OrchestrationResult class."""

    def test_should_check_completeness(self):
        """Test completeness check."""
        # Complete result
        complete = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        assert complete.is_complete()

        # Incomplete result
        incomplete = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=0.25,
            # Missing other fields
        )
        assert not incomplete.is_complete()

    def test_should_calculate_completeness_score(self):
        """Test completeness score calculation."""
        # 50% complete
        partial = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=0.25,
            debt_to_equity=0.5,
            # 2 out of 4 fields
        )
        assert partial.get_completeness_score() == 0.5

        # 100% complete
        complete = OrchestrationResult(
            ticker="AAPL",
            timestamp=datetime.now(),
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        assert complete.get_completeness_score() == 1.0


class TestDataSourceOrchestrator:
    """Test DataSourceOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

    def test_should_initialize_with_adapters(self, orchestrator):
        """Test that orchestrator initializes with all adapters."""
        assert len(orchestrator.adapters) >= 1  # At least YFinance
        assert orchestrator.fallback_adapter is not None

    def test_should_get_available_adapters(self, orchestrator):
        """Test getting list of available adapters."""
        available = orchestrator.get_available_adapters()

        assert "IndustryAverages" in available  # Always available
        # Other adapters depend on API keys

    def test_should_get_adapter_info(self, orchestrator):
        """Test getting adapter information."""
        info = orchestrator.get_adapter_info()

        # Currently only YFinance + IndustryAverages (fallback)
        # TODO: Will be 6 adapters once all are migrated to async
        assert len(info) >= 2  # At least YFinance + fallback
        assert all("name" in i for i in info)
        assert all("timeout_seconds" in i for i in info)

    @pytest.mark.asyncio
    async def test_should_use_fallback_when_all_sources_fail(self, orchestrator, mocker):
        """Test that industry averages are used when all sources fail."""
        # Mock all adapters to fail
        for adapter in orchestrator.adapters:
            mocker.patch.object(adapter, "is_available", return_value=False)

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        assert result.ticker == "AAPL"
        assert result.used_fallback is True
        assert "IndustryAverages" in result.sources_succeeded
        assert result.is_complete()  # Fallback provides all fields

    @pytest.mark.asyncio
    async def test_should_track_data_lineage(self, orchestrator, mocker):
        """Test that data lineage is tracked correctly."""
        # Mock first adapter to provide partial data
        mock_data = FundamentalData(
            ticker="AAPL",
            source="MockSource1",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            # Missing revenue_growth and profit_margin
        )

        mock_adapter = orchestrator.adapters[0]
        mocker.patch.object(mock_adapter, "is_available", return_value=True)
        mocker.patch.object(mock_adapter, "get_fundamental_data", return_value=mock_data)

        # Mock other adapters to fail
        for adapter in orchestrator.adapters[1:]:
            mocker.patch.object(adapter, "is_available", return_value=False)

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Check lineage
        assert result.lineage.return_on_equity_source == "MockSource1"
        assert result.lineage.debt_to_equity_source == "MockSource1"
        # Fallback should provide missing fields
        assert result.lineage.revenue_growth_source == "IndustryAverages"
        assert result.lineage.profit_margin_source == "IndustryAverages"

    @pytest.mark.asyncio
    async def test_should_reject_invalid_data(self, orchestrator, mocker):
        """Test that invalid data is rejected and next source is tried."""
        # Mock first adapter to return invalid data
        invalid_data = FundamentalData(
            ticker="AAPL",
            source="InvalidSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=5.0,  # Invalid: > 2.0
        )

        mock_adapter = orchestrator.adapters[0]
        mocker.patch.object(mock_adapter, "is_available", return_value=True)
        mocker.patch.object(mock_adapter, "get_fundamental_data", return_value=invalid_data)

        # Mock other adapters to fail
        for adapter in orchestrator.adapters[1:]:
            mocker.patch.object(adapter, "is_available", return_value=False)

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Invalid source should be in failed list
        assert mock_adapter.source_name in result.sources_failed
        # Should use fallback
        assert result.used_fallback is True

    @pytest.mark.asyncio
    async def test_should_handle_timeout_per_source(self, orchestrator, mocker):
        """Test that per-source timeout is enforced."""
        # Mock adapter to timeout
        mock_adapter = orchestrator.adapters[0]
        mocker.patch.object(mock_adapter, "is_available", return_value=True)
        mocker.patch.object(mock_adapter, "get_fundamental_data", side_effect=TimeoutError("Timeout"))

        # Mock other adapters to fail
        for adapter in orchestrator.adapters[1:]:
            mocker.patch.object(adapter, "is_available", return_value=False)

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Timeout source should be in failed list
        assert mock_adapter.source_name in result.sources_failed
        assert any("Timeout" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_should_stop_when_complete(self, orchestrator, mocker):
        """Test that orchestration stops when all fields are populated."""
        # Mock first adapter to provide complete data
        complete_data = FundamentalData(
            ticker="AAPL",
            source="CompleteSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )

        mock_adapter = orchestrator.adapters[0]
        mocker.patch.object(mock_adapter, "is_available", return_value=True)
        mock_get_data = mocker.patch.object(mock_adapter, "get_fundamental_data", return_value=complete_data)

        result = await orchestrator.get_fundamental_data("AAPL")

        # Should be complete from first source
        assert result.is_complete()
        assert result.used_fallback is False
        # First adapter should have been called exactly once
        mock_get_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_calculate_confidence_based_on_sources(self, orchestrator, mocker):
        """Test confidence calculation based on data sources."""
        # Test with YFinance (primary source)
        yfinance_data = FundamentalData(
            ticker="AAPL",
            source="YFinance",
            timestamp=datetime.now(),
            confidence=1.0,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )

        # Create mock adapter with source_name as attribute (not patching property)
        mock_adapter = mocker.Mock(spec=orchestrator.adapters[0])
        mock_adapter.source_name = "YFinance"
        mock_adapter.is_available.return_value = True
        mock_adapter.get_fundamental_data = mocker.AsyncMock(return_value=yfinance_data)

        # Replace adapters list with our mock
        orchestrator.adapters = [mock_adapter]

        result = await orchestrator.get_fundamental_data("AAPL")

        # High confidence for primary source
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_should_merge_data_from_multiple_sources(self, orchestrator, mocker):
        """Test merging data from multiple sources (waterfall).

        Note: Currently only YFinance is available. This test simulates
        multiple sources by adding a mock adapter to the list.
        """
        # First source provides partial data
        partial_data_1 = FundamentalData(
            ticker="AAPL",
            source="Source1",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
        )

        # Second source provides remaining data
        partial_data_2 = FundamentalData(
            ticker="AAPL",
            source="Source2",
            timestamp=datetime.now(),
            confidence=0.8,
            revenue_growth=0.15,
            profit_margin=0.20,
        )

        # Create mock adapters
        mock_adapter_1 = mocker.Mock(spec=orchestrator.adapters[0])
        mock_adapter_1.source_name = "Source1"
        mock_adapter_1.is_available.return_value = True
        mock_adapter_1.get_fundamental_data = mocker.AsyncMock(return_value=partial_data_1)

        mock_adapter_2 = mocker.Mock(spec=orchestrator.adapters[0])
        mock_adapter_2.source_name = "Source2"
        mock_adapter_2.is_available.return_value = True
        mock_adapter_2.get_fundamental_data = mocker.AsyncMock(return_value=partial_data_2)

        # Replace adapters list with our mocks
        orchestrator.adapters = [mock_adapter_1, mock_adapter_2]

        result = await orchestrator.get_fundamental_data("AAPL")

        # Should have data from both sources
        assert result.return_on_equity == 0.25  # From Source1
        assert result.debt_to_equity == 0.5  # From Source1
        assert result.revenue_growth == 0.15  # From Source2
        assert result.profit_margin == 0.20  # From Source2
        assert result.is_complete()
