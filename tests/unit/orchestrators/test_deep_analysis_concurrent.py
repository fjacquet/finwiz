"""Tests for deep analysis concurrent execution mechanics.

Tests ONLY deterministic Python mechanics:
- Semaphore behavior
- Async wrapper mechanics
- Concurrent task coordination

Does NOT test AI agent outputs (non-deterministic).
"""

import asyncio

import pytest
from faker import Faker

from finwiz.flow_state import DeepAnalysisResult, FinwizState

fake = Faker()


@pytest.fixture
def mock_finwiz_state(mocker):
    """Create a mock FinwizState for testing."""
    state = mocker.MagicMock(spec=FinwizState)
    state.failed_holdings = []
    state.prefetched_data = {}
    state.batch_prefetch_metrics = None
    state.current_day = "Monday"
    state.current_month = "January"
    state.current_year = "2025"
    state.current_date = "2025-01-15"
    state.full_date = "January 15, 2025"
    state.timestamp = "2025-01-15T10:00:00"
    state.report_language = "English"
    return state


@pytest.fixture
def mock_batch_config(mocker):
    """Create a mock batch config."""
    config = mocker.MagicMock()
    config.enabled = True
    config.min_holdings_for_batch = 5
    config.batch_size = 5
    return config


@pytest.fixture
def orchestrator(mocker, mock_finwiz_state, mock_batch_config):
    """Create a DeepAnalysisOrchestrator with mocked dependencies."""
    # Mock the imports at their source modules
    mocker.patch("finwiz.flows.hybrid_analysis_flow.HybridAnalysisFlow")
    mocker.patch("finwiz.data.data_source_orchestrator.DataSourceOrchestrator")

    from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator

    orch = DeepAnalysisOrchestrator(
        state=mock_finwiz_state,
        batch_prefetch_config=mock_batch_config,
    )
    return orch


class TestConcurrentExecutionMechanics:
    """Tests for concurrent execution mechanics (deterministic Python code only)."""

    def test_empty_holdings_returns_empty_dict(self, orchestrator):
        """Test that empty holdings list returns empty results."""
        result = orchestrator.run_deep_analysis_on_holdings([])
        assert result == {}

    def test_concurrent_execution_respects_env_toggle(self, orchestrator, mocker):
        """Test that DEEP_ANALYSIS_CONCURRENT env var controls execution mode."""
        mocker.patch.dict("os.environ", {"DEEP_ANALYSIS_CONCURRENT": "false"})

        # Mock sequential method on executor to track if it's called
        sequential_mock = mocker.patch.object(orchestrator.executor, "_run_deep_analysis_sequential", return_value={})

        holdings = [{"ticker": "AAPL", "asset_class": "stock"}]
        orchestrator.run_deep_analysis_on_holdings(holdings)

        sequential_mock.assert_called_once_with(holdings)

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self, mocker):
        """Test that semaphore properly limits concurrent executions."""
        concurrent_count = 0
        max_concurrent = 0
        limit = 3

        semaphore = asyncio.Semaphore(limit)

        async def track_concurrency(idx: int) -> int:
            nonlocal concurrent_count, max_concurrent

            async with semaphore:
                concurrent_count += 1
                max_concurrent = max(max_concurrent, concurrent_count)

                # Simulate work
                await asyncio.sleep(0.05)

                concurrent_count -= 1
                return idx

        # Run 10 tasks with limit of 3
        tasks = [track_concurrency(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # Should never exceed semaphore limit
        assert max_concurrent <= limit

    @pytest.mark.asyncio
    async def test_process_single_holding_async_executes_in_threadpool(self, orchestrator, mocker):
        """Test that async wrapper properly executes sync code in thread pool."""
        # Create a mock result
        mock_result = mocker.MagicMock(spec=DeepAnalysisResult)

        # Mock the synchronous method on executor
        mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding",
            return_value=mock_result,
        )

        # Mock cache manager
        cache_mgr = mocker.MagicMock()

        result = await orchestrator.executor._process_single_holding_async(
            ticker="AAPL",
            asset_class="stock",
            cache_mgr=cache_mgr,
            cache_ttl=24,
            batch_enabled=False,
        )

        # Should return the result from the synchronous method
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_concurrent_method_returns_results_dict(self, orchestrator, mocker):
        """Test that run_deep_analysis_concurrent returns proper results dictionary."""
        # Mock dependencies at their source module
        mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mocker.patch.object(orchestrator, "execute_deep_analysis_with_prefetch")

        # Create mock results
        mock_result = mocker.MagicMock(spec=DeepAnalysisResult)

        # Mock async method to return results
        async def mock_async_process(*args, **kwargs):
            return mock_result

        mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding_async",
            side_effect=mock_async_process,
        )

        holdings = [
            {"ticker": "AAPL", "asset_class": "stock"},
            {"ticker": "GOOGL", "asset_class": "stock"},
        ]

        results = await orchestrator.run_deep_analysis_concurrent(holdings)

        # Should have results for both tickers
        assert "AAPL" in results
        assert "GOOGL" in results
        assert results["AAPL"] == mock_result
        assert results["GOOGL"] == mock_result

    @pytest.mark.asyncio
    async def test_concurrent_method_handles_failed_holdings(self, orchestrator, mocker):
        """Test that failed holdings are tracked in state."""
        # Mock dependencies at their source module
        mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mocker.patch.object(orchestrator, "execute_deep_analysis_with_prefetch")

        # Mock async method to raise exception
        async def mock_async_fail(*args, **kwargs):
            raise ValueError("Mock error")

        mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding_async",
            side_effect=mock_async_fail,
        )

        holdings = [{"ticker": "AAPL", "asset_class": "stock"}]

        results = await orchestrator.run_deep_analysis_concurrent(holdings)

        # Should have empty results
        assert len(results) == 0

        # Should have tracked failed holding
        assert "AAPL" in orchestrator.state.failed_holdings

    @pytest.mark.asyncio
    async def test_concurrent_method_skips_invalid_holdings(self, orchestrator, mocker):
        """Test that holdings without ticker or asset_class are skipped."""
        mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mocker.patch.object(orchestrator, "execute_deep_analysis_with_prefetch")

        # Mock should not be called for invalid holdings
        async_mock = mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding_async",
            return_value=mocker.MagicMock(spec=DeepAnalysisResult),
        )

        holdings = [
            {"ticker": None, "asset_class": "stock"},  # Missing ticker
            {"ticker": "AAPL", "asset_class": None},  # Missing asset_class
            {},  # Empty
        ]

        await orchestrator.run_deep_analysis_concurrent(holdings)

        # Should not process any invalid holdings
        async_mock.assert_not_called()


class TestSequentialFallback:
    """Tests for sequential execution fallback."""

    def test_sequential_method_processes_all_holdings(self, orchestrator, mocker):
        """Test that sequential method processes all valid holdings."""
        mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mocker.patch.object(orchestrator, "execute_deep_analysis_with_prefetch")

        mock_result = mocker.MagicMock(spec=DeepAnalysisResult)
        process_mock = mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding",
            return_value=mock_result,
        )

        holdings = [
            {"ticker": "AAPL", "asset_class": "stock"},
            {"ticker": "GOOGL", "asset_class": "stock"},
        ]

        results = orchestrator.executor._run_deep_analysis_sequential(holdings)

        # Should process both holdings
        assert process_mock.call_count == 2
        assert "AAPL" in results
        assert "GOOGL" in results

    def test_sequential_method_handles_exceptions(self, orchestrator, mocker):
        """Test that sequential method handles processing exceptions gracefully."""
        mocker.patch("finwiz.cache.analysis_cache_manager.get_analysis_cache_manager")
        mocker.patch.object(orchestrator, "execute_deep_analysis_with_prefetch")

        # First call succeeds, second fails
        mock_result = mocker.MagicMock(spec=DeepAnalysisResult)
        mocker.patch.object(
            orchestrator.executor,
            "_process_single_holding",
            side_effect=[mock_result, ValueError("Processing failed")],
        )

        holdings = [
            {"ticker": "AAPL", "asset_class": "stock"},
            {"ticker": "FAIL", "asset_class": "stock"},
        ]

        results = orchestrator.executor._run_deep_analysis_sequential(holdings)

        # Should have partial results
        assert "AAPL" in results
        assert "FAIL" not in results
        assert "FAIL" in orchestrator.state.failed_holdings
