"""
Orchestrator state integration tests.

Tests verify that orchestrator methods mutate FinwizState fields correctly,
not just return values. Covers DiscoveryOrchestrator and DeepAnalysisOrchestrator.

Uses pytest-mock exclusively (unittest.mock is BANNED per project rules).
"""

import pytest

from finwiz.flow_state import DeepAnalysisResult, FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator


class TestOrchestratorStateIntegration:
    """Integration tests verifying orchestrator state mutations."""

    @pytest.fixture
    def state(self):
        """Create a FinwizState with portfolio data for integration tests."""
        return FinwizState(
            session_id="test_integration",
            current_date="2025-11-17",
            portfolio_review={
                "holdings": [
                    {"ticker": "AAPL", "asset_class": "stock", "name": "Apple Inc."},
                    {"ticker": "SPY", "asset_class": "etf", "name": "SPDR S&P 500"},
                ]
            },
        )

    @pytest.fixture
    def discovery_orchestrator(self, state, mocker):
        """Create a DiscoveryOrchestrator with file I/O mocked out."""
        orch = DiscoveryOrchestrator(state, availability_tracker=mocker.Mock())
        mocker.patch.object(orch, "_save_discovery_results")
        return orch

    # ---- DiscoveryOrchestrator: crypto ----

    def test_discovery_check_crypto_sets_state_on_success(
        self, discovery_orchestrator, state, mocker
    ):
        """Crypto success path sets crypto_analysis_success and crypto_opportunities on state."""
        mocker.patch(
            "finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities",
            return_value={
                "analysis_summary": "3 opportunities found",
                "opportunities": [{"ticker": "BTC"}, {"ticker": "ETH"}],
                "performance_metrics": {"total": 2},
            },
        )

        result = discovery_orchestrator.check_crypto()

        # Return value assertions
        assert result["crypto_analysis_complete"] is True
        assert "3 opportunities found" in result["crypto_result"]

        # State mutation assertions
        assert state.crypto_analysis_success is True
        assert "3 opportunities found" in state.crypto_result
        assert isinstance(state.crypto_opportunities, list)
        assert len(state.crypto_opportunities) == 2

    def test_discovery_check_crypto_sets_state_on_failure(
        self, discovery_orchestrator, state, mocker
    ):
        """Crypto failure path sets crypto_analysis_success=False and crypto_analysis_error."""
        mocker.patch(
            "finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities",
            side_effect=RuntimeError("API down"),
        )

        result = discovery_orchestrator.check_crypto()

        # Return value: always marks complete
        assert result["crypto_analysis_complete"] is True

        # State mutation: error fields populated
        assert state.crypto_analysis_success is False
        assert "API down" in state.crypto_analysis_error

    # ---- DiscoveryOrchestrator: stock ----

    def test_discovery_check_stock_sets_state_on_success(
        self, discovery_orchestrator, state, mocker
    ):
        """Stock success path sets stock_analysis_success and stock_opportunities on state."""
        mocker.patch(
            "finwiz.scoring.stock_analyzer.analyze_stock_opportunities",
            return_value={
                "analysis_summary": "5 stocks found",
                "opportunities": [{"ticker": "NVDA"}],
                "performance_metrics": {},
            },
        )

        result = discovery_orchestrator.check_stock()

        assert result["stock_analysis_complete"] is True
        assert state.stock_analysis_success is True
        assert "5 stocks found" in state.stock_result
        assert len(state.stock_opportunities) == 1

    # ---- DiscoveryOrchestrator: etf ----

    def test_discovery_check_etf_sets_state_on_success(
        self, discovery_orchestrator, state, mocker
    ):
        """ETF success path sets etf_analysis_success and etf_opportunities on state."""
        mocker.patch(
            "finwiz.scoring.etf_analyzer.analyze_etf_opportunities",
            return_value={
                "analysis_summary": "2 ETFs found",
                "opportunities": [{"ticker": "QQQ"}],
                "performance_metrics": {},
            },
        )

        result = discovery_orchestrator.check_etf()

        assert result["etf_analysis_complete"] is True
        assert state.etf_analysis_success is True
        assert "2 ETFs found" in state.etf_result
        assert len(state.etf_opportunities) == 1

    # ---- DeepAnalysisOrchestrator ----

    @pytest.mark.asyncio
    async def test_deep_analysis_sets_state_on_success(self, state, mocker):
        """Deep analysis success sets deep_analysis_results and deep_analysis_success on state."""
        mocker.patch("os.getenv", side_effect=lambda k, d="": "true" if k == "DEEP_PORTFOLIO_ANALYSIS" else d)

        mock_deep_result = DeepAnalysisResult(
            ticker="AAPL",
            asset_class="stock",
            crew_name="test",
            grade="A",
            composite_score=0.82,
            recommendation="BUY",
            rationale="Strong",
            data_freshness_hours=0.5,
            confidence_level=0.85,
            risk_score=2.0,
        )

        orch = DeepAnalysisOrchestrator(
            state,
            crew_factory=mocker.Mock(),
            integration_manager=mocker.Mock(),
            error_handler=mocker.Mock(),
        )

        mocker.patch.object(
            orch,
            "run_deep_analysis_concurrent",
            new_callable=mocker.AsyncMock,
            return_value={"AAPL": mock_deep_result},
        )
        mocker.patch.object(orch, "_match_alternatives", return_value={})
        mocker.patch.object(orch, "_update_portfolio_review_with_enriched_data")

        await orch.analyze_and_update_portfolio()

        assert state.deep_analysis_success is True
        assert "AAPL" in state.deep_analysis_results
        assert state.deep_analysis_results["AAPL"].grade == "A"

    @pytest.mark.asyncio
    async def test_deep_analysis_sets_error_state_on_failure(self, state, mocker):
        """Deep analysis failure sets deep_analysis_success=False and deep_analysis_error."""
        mocker.patch("os.getenv", side_effect=lambda k, d="": "true" if k == "DEEP_PORTFOLIO_ANALYSIS" else d)

        orch = DeepAnalysisOrchestrator(
            state,
            crew_factory=mocker.Mock(),
            integration_manager=mocker.Mock(),
            error_handler=mocker.Mock(),
        )

        mocker.patch.object(
            orch,
            "run_deep_analysis_concurrent",
            new_callable=mocker.AsyncMock,
            side_effect=RuntimeError("Analysis timeout"),
        )

        result = await orch.analyze_and_update_portfolio()

        assert state.deep_analysis_success is False
        assert "Analysis timeout" in state.deep_analysis_error
        assert "error" in result

    # ---- Discovery consolidation ----

    def test_discovery_consolidation_aggregates_all_opportunities(
        self, state, mocker
    ):
        """Consolidation gathers opportunities from all 3 asset classes into state."""
        orch = DiscoveryOrchestrator(state)
        mocker.patch.object(orch, "_save_discovery_results")

        state.crypto_opportunities = [{"ticker": "BTC"}]
        state.stock_opportunities = [{"ticker": "NVDA"}, {"ticker": "TSLA"}]
        state.etf_opportunities = [{"ticker": "QQQ"}]

        result = orch.check_investment_discovery()

        assert state.investment_discovery_available is True
        assert len(state.all_discovery_opportunities) == 4
        assert result["total_opportunities"] == 4

    # ---- Error propagation across boundaries ----

    def test_error_propagation_across_orchestrator_boundaries(
        self, state, mocker
    ):
        """Failed crypto leaves state without crypto_opportunities; consolidation handles it."""
        orch1 = DiscoveryOrchestrator(state, availability_tracker=mocker.Mock())
        mocker.patch.object(orch1, "_save_discovery_results")
        mocker.patch(
            "finwiz.scoring.crypto_analyzer.analyze_crypto_opportunities",
            side_effect=ValueError("bad data"),
        )

        orch1.check_crypto()
        assert state.crypto_analysis_success is False

        # A separate orchestrator sharing the same state sees the error
        orch2 = DiscoveryOrchestrator(state)
        mocker.patch.object(orch2, "_save_discovery_results")

        # crypto_opportunities was never set (error path does not set it)
        # consolidation should NOT crash
        result = orch2.check_investment_discovery()

        assert result["investment_discovery_complete"] is True
        # crypto_opportunities is not set, so 0 total
        assert result["total_opportunities"] == 0
