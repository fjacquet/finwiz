"""Unit tests for batch_prefetch_runner.

Tests that batch prefetch is correctly wired into the deep analysis flow.
"""

from types import SimpleNamespace

import pytest

from finwiz.orchestrators.batch_prefetch_runner import run_batch_prefetch


@pytest.fixture
def state():
    """Create minimal state object."""
    return SimpleNamespace(
        session_id="test-session",
        batch_prefetch_enabled=False,
        prefetched_data={},
        batch_prefetch_metrics={},
    )


@pytest.fixture
def holdings():
    """Create sample holdings list."""
    return [
        {"ticker": "AAPL", "asset_class": "stock", "name": "Apple"},
        {"ticker": "MSFT", "asset_class": "stock", "name": "Microsoft"},
        {"ticker": "GOOGL", "asset_class": "stock", "name": "Alphabet"},
        {"ticker": "AMZN", "asset_class": "stock", "name": "Amazon"},
        {"ticker": "META", "asset_class": "stock", "name": "Meta"},
        {"ticker": "NVDA", "asset_class": "stock", "name": "Nvidia"},
        {"ticker": "TSLA", "asset_class": "stock", "name": "Tesla"},
        {"ticker": "JPM", "asset_class": "stock", "name": "JPMorgan"},
        {"ticker": "V", "asset_class": "stock", "name": "Visa"},
        {"ticker": "JNJ", "asset_class": "stock", "name": "J&J"},
    ]


@pytest.fixture
def prefetched_result():
    """Simulated BatchDataPreFetcher output."""
    return {
        "AAPL": {
            "ticker": "AAPL",
            "yahoo_finance": {"symbol": "AAPL", "current_price": 150.0, "failed": False},
            "failed": False,
        },
        "MSFT": {
            "ticker": "MSFT",
            "yahoo_finance": {"symbol": "MSFT", "current_price": 400.0, "failed": False},
            "failed": False,
        },
    }


class TestRunBatchPrefetch:
    """Tests for run_batch_prefetch function."""

    def test_should_prefetch_and_update_state(self, mocker, state, holdings, prefetched_result):
        """Prefetch populates state fields when enabled."""
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.load_batch_prefetch_config",
            return_value=SimpleNamespace(enabled=True, min_holdings_for_batch=5, alpha_vantage_rate_limit=5),
        )
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.should_use_alpha_vantage",
            return_value=False,
        )
        mock_prefetcher = mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.BatchDataPreFetcher",
        )
        mock_prefetcher.return_value.prefetch_all_data.return_value = prefetched_result

        import logging

        logger = logging.getLogger("test")
        result = run_batch_prefetch(state, holdings, logger)

        assert state.batch_prefetch_enabled is True
        assert state.prefetched_data is not None
        assert state.batch_prefetch_metrics["tickers_requested"] == 10
        assert state.batch_prefetch_metrics["tickers_fetched"] == 2
        assert result == prefetched_result

    def test_should_skip_when_disabled(self, mocker, state, holdings):
        """Returns empty dict when batch prefetch is disabled."""
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.load_batch_prefetch_config",
            return_value=SimpleNamespace(enabled=False, min_holdings_for_batch=5, alpha_vantage_rate_limit=5),
        )

        import logging

        logger = logging.getLogger("test")
        result = run_batch_prefetch(state, holdings, logger)

        assert result == {}
        assert state.batch_prefetch_enabled is False

    def test_should_skip_below_min_holdings(self, mocker, state):
        """Returns empty dict when holdings count is below threshold."""
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.load_batch_prefetch_config",
            return_value=SimpleNamespace(enabled=True, min_holdings_for_batch=10, alpha_vantage_rate_limit=5),
        )

        small_holdings = [{"ticker": "AAPL", "asset_class": "stock"}]
        import logging

        logger = logging.getLogger("test")
        result = run_batch_prefetch(state, small_holdings, logger)

        assert result == {}
        assert state.batch_prefetch_enabled is False

    def test_should_handle_prefetch_failure_gracefully(self, mocker, state, holdings):
        """Returns empty dict and does not crash on prefetch failure."""
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.load_batch_prefetch_config",
            return_value=SimpleNamespace(enabled=True, min_holdings_for_batch=5, alpha_vantage_rate_limit=5),
        )
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.should_use_alpha_vantage",
            return_value=False,
        )
        mock_prefetcher = mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.BatchDataPreFetcher",
        )
        mock_prefetcher.return_value.prefetch_all_data.side_effect = RuntimeError("Network error")

        import logging

        logger = logging.getLogger("test")
        result = run_batch_prefetch(state, holdings, logger)

        assert result == {}
        assert state.batch_prefetch_enabled is False

    def test_should_skip_empty_tickers(self, mocker, state):
        """Returns empty dict when no valid tickers in holdings."""
        mocker.patch(
            "finwiz.orchestrators.batch_prefetch_runner.load_batch_prefetch_config",
            return_value=SimpleNamespace(enabled=True, min_holdings_for_batch=1, alpha_vantage_rate_limit=5),
        )

        empty_holdings = [{"asset_class": "stock"}, {"ticker": "", "asset_class": "stock"}]
        import logging

        logger = logging.getLogger("test")
        result = run_batch_prefetch(state, empty_holdings, logger)

        assert result == {}
