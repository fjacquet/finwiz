"""Tests for data adapter fallback scenarios in DataSourceOrchestrator.

Tests failure and degradation scenarios: complete adapter failure, fallback chain
exhaustion, partial data degradation with lineage tracking, and timeout handling.
"""

import asyncio
from datetime import datetime

import pytest

from finwiz.data.adapters.base_adapter import (
    DataAcquisitionError,
    FundamentalData,
    TimeoutError,
)
from finwiz.data.data_source_orchestrator import (
    DataSourceOrchestrator,
)


class TestAdapterFallbackScenarios:
    """Test adapter fallback and degradation scenarios."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return DataSourceOrchestrator(
            total_timeout=10.0,
            per_source_timeout=3.0,
            enable_validation=True,
        )

    def _make_mock_adapter(self, mocker, name, available=True):
        """Create a mock adapter with the given source_name and availability."""
        adapter = mocker.Mock()
        adapter.source_name = name
        adapter.is_available.return_value = available
        adapter.get_fundamental_data = mocker.AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_all_adapters_unavailable_falls_to_industry_averages(
        self, orchestrator, mocker
    ):
        """When ALL adapters are unavailable, IndustryAverages is used."""
        for adapter in orchestrator.adapters:
            mocker.patch.object(adapter, "is_available", return_value=False)

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        assert result.used_fallback is True
        assert "IndustryAverages" in result.sources_succeeded
        assert result.is_complete()
        assert result.confidence < 0.6

    @pytest.mark.asyncio
    async def test_primary_adapter_raises_data_acquisition_error(
        self, orchestrator, mocker
    ):
        """When primary adapter raises DataAcquisitionError, next adapter is tried."""
        adapter1 = self._make_mock_adapter(mocker, "FailSource")
        adapter1.get_fundamental_data.side_effect = DataAcquisitionError(
            "Connection refused"
        )

        complete_data = FundamentalData(
            ticker="AAPL",
            source="BackupSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        adapter2 = self._make_mock_adapter(mocker, "BackupSource")
        adapter2.get_fundamental_data.return_value = complete_data

        orchestrator.adapters = [adapter1, adapter2]

        result = await orchestrator.get_fundamental_data("AAPL")

        assert "FailSource" in result.sources_failed
        assert "BackupSource" in result.sources_succeeded
        assert result.is_complete()
        assert any("Connection refused" in w for w in result.warnings)

    @pytest.mark.asyncio
    async def test_primary_adapter_raises_timeout_error(self, orchestrator, mocker):
        """When primary adapter raises TimeoutError, it is recorded and next tried."""
        adapter1 = self._make_mock_adapter(mocker, "SlowSource")
        adapter1.get_fundamental_data.side_effect = TimeoutError(
            "3s timeout exceeded"
        )

        complete_data = FundamentalData(
            ticker="AAPL",
            source="FastSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        adapter2 = self._make_mock_adapter(mocker, "FastSource")
        adapter2.get_fundamental_data.return_value = complete_data

        orchestrator.adapters = [adapter1, adapter2]

        result = await orchestrator.get_fundamental_data("AAPL")

        assert "SlowSource" in result.sources_failed
        assert any("timeout" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_primary_adapter_returns_invalid_data_rejected(
        self, orchestrator, mocker
    ):
        """When primary adapter returns invalid data, it is rejected."""
        invalid_data = FundamentalData(
            ticker="AAPL",
            source="BadDataSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=5.0,  # Invalid: > 2.0 threshold
        )
        adapter1 = self._make_mock_adapter(mocker, "BadDataSource")
        adapter1.get_fundamental_data.return_value = invalid_data

        valid_data = FundamentalData(
            ticker="AAPL",
            source="GoodDataSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        adapter2 = self._make_mock_adapter(mocker, "GoodDataSource")
        adapter2.get_fundamental_data.return_value = valid_data

        orchestrator.adapters = [adapter1, adapter2]

        result = await orchestrator.get_fundamental_data("AAPL")

        assert "BadDataSource" in result.sources_failed
        assert result.return_on_equity == 0.25  # Uses second adapter's data
        assert any("failed validation" in w.lower() or "validation" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_all_adapters_fail_and_fallback_fails(self, orchestrator, mocker):
        """When ALL adapters + fallback fail, result is partial with warnings."""
        for adapter in orchestrator.adapters:
            mocker.patch.object(adapter, "is_available", return_value=False)

        mocker.patch.object(
            orchestrator.fallback_adapter,
            "get_fundamental_data",
            new=mocker.AsyncMock(
                side_effect=Exception("IndustryAverages DB corrupted")
            ),
        )

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Should NOT raise; graceful degradation
        assert result.is_complete() is False
        assert any("Fallback failed" in w for w in result.warnings)
        assert result.get_completeness_score() == 0.0

    @pytest.mark.asyncio
    async def test_partial_data_degradation_with_lineage_tracking(
        self, orchestrator, mocker
    ):
        """Partial data from one adapter is filled by IndustryAverages with lineage."""
        partial_data = FundamentalData(
            ticker="AAPL",
            source="PartialSource",
            timestamp=datetime.now(),
            confidence=0.9,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            # revenue_growth and profit_margin are None
        )
        adapter = self._make_mock_adapter(mocker, "PartialSource")
        adapter.get_fundamental_data.return_value = partial_data

        orchestrator.adapters = [adapter]

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        # Data from mock adapter
        assert result.return_on_equity == 0.25
        assert result.debt_to_equity == 0.5
        # Filled by IndustryAverages
        assert result.revenue_growth is not None
        assert result.profit_margin is not None
        # Lineage tracking
        assert result.lineage.return_on_equity_source == "PartialSource"
        assert result.lineage.revenue_growth_source == "IndustryAverages"
        assert result.used_fallback is True

    @pytest.mark.asyncio
    async def test_total_timeout_exceeded_graceful_degradation(self, mocker):
        """When total timeout is exceeded, result still has data from fallback."""
        orchestrator = DataSourceOrchestrator(
            total_timeout=0.01,
            per_source_timeout=3.0,
            enable_validation=True,
        )

        async def slow_fetch(_ticker):
            await asyncio.sleep(1.0)
            return FundamentalData(
                ticker=_ticker,
                source="SlowSource",
                timestamp=datetime.now(),
                confidence=0.9,
                return_on_equity=0.25,
                debt_to_equity=0.5,
                revenue_growth=0.15,
                profit_margin=0.20,
            )

        adapter = self._make_mock_adapter(mocker, "SlowSource")
        adapter.get_fundamental_data = slow_fetch

        orchestrator.adapters = [adapter]

        result = await orchestrator.get_fundamental_data("AAPL", sector="Technology")

        assert any("timeout" in w.lower() for w in result.warnings)
        # Fallback fills data after timeout
        assert result.is_complete()

    @pytest.mark.asyncio
    async def test_first_source_complete_stops_waterfall(self, orchestrator, mocker):
        """When first source returns complete data, second is never called."""
        complete_data = FundamentalData(
            ticker="AAPL",
            source="PrimarySource",
            timestamp=datetime.now(),
            confidence=0.95,
            return_on_equity=0.25,
            debt_to_equity=0.5,
            revenue_growth=0.15,
            profit_margin=0.20,
        )
        adapter1 = self._make_mock_adapter(mocker, "PrimarySource")
        adapter1.get_fundamental_data.return_value = complete_data

        adapter2 = self._make_mock_adapter(mocker, "SecondarySource")

        orchestrator.adapters = [adapter1, adapter2]

        result = await orchestrator.get_fundamental_data("AAPL")

        assert adapter2.get_fundamental_data.call_count == 0
        assert result.is_complete()
        assert result.used_fallback is False
