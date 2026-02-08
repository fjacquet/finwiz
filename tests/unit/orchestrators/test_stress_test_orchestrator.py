"""Tests for StressTestOrchestrator."""

from types import SimpleNamespace

import pytest

from finwiz.orchestrators.stress_test_orchestrator import StressTestOrchestrator


def _make_state(tickers: list[str] | None = None, prefetched: dict | None = None):
    """Build a minimal state-like object."""
    results = {}
    if tickers:
        for t in tickers:
            results[t] = SimpleNamespace(asset_type="stock")

    return SimpleNamespace(
        deep_analysis_results=results,
        prefetched_data=prefetched or {},
    )


class TestStressTestOrchestrator:
    def test_runs_with_holdings(self):
        state = _make_state(tickers=["AAPL", "MSFT", "GOOGL"])
        orch = StressTestOrchestrator(state)
        results = orch.run_stress_tests()
        assert len(results) == 3  # 3 default scenarios

    def test_empty_holdings_returns_empty(self):
        state = _make_state(tickers=[])
        orch = StressTestOrchestrator(state)
        results = orch.run_stress_tests()
        assert results == []

    def test_enrichment_data_used(self):
        prefetched = {
            "AAPL": {"enrichment": {"sector": "Technology", "beta": 1.3}},
        }
        state = _make_state(tickers=["AAPL"], prefetched=prefetched)
        orch = StressTestOrchestrator(state)
        holdings = orch._build_holdings_list()
        assert holdings[0]["sector"] == "Technology"
        assert holdings[0]["beta"] == 1.3

    def test_missing_enrichment_defaults(self):
        state = _make_state(tickers=["AAPL"])
        orch = StressTestOrchestrator(state)
        holdings = orch._build_holdings_list()
        assert holdings[0]["sector"] == "Unknown"
        assert holdings[0]["beta"] == 1.0

    def test_graceful_failure(self, mocker):
        state = _make_state(tickers=["AAPL"])
        mocker.patch(
            "finwiz.orchestrators.stress_test_orchestrator.PortfolioStressTestEngine.run_all_predefined",
            side_effect=RuntimeError("engine error"),
        )
        orch = StressTestOrchestrator(state)
        results = orch.run_stress_tests()
        assert results == []

    def test_equal_weights(self):
        state = _make_state(tickers=["A", "B", "C", "D"])
        orch = StressTestOrchestrator(state)
        holdings = orch._build_holdings_list()
        assert all(h["weight"] == pytest.approx(0.25) for h in holdings)
