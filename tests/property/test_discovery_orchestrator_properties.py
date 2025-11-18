"""
Property-based tests for DiscoveryOrchestrator.

Tests verify universal properties using Hypothesis with minimum 100 iterations.

NOTE: Property tests cannot use pytest-mock's mocker fixture due to Hypothesis limitations.
The error handling property test has been moved to unit tests where pytest-mock can be used.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator


class TestDiscoveryOrchestratorProperties:
    """Property-based tests for DiscoveryOrchestrator."""

    @given(
        crypto_count=st.integers(min_value=0, max_value=10),
        stock_count=st.integers(min_value=0, max_value=10),
        etf_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100)
    def test_property_discovery_result_consolidation(self, crypto_count, stock_count, etf_count):
        """
        Property 16: Discovery Result Consolidation.

        For any set of discovery results from multiple asset classes, the DiscoveryOrchestrator
        should consolidate all results.
        """
        # Arrange
        state = FinwizState()
        orchestrator = DiscoveryOrchestrator(state)

        # Create opportunities for each asset class
        state.crypto_opportunities = [{"ticker": f"CRYPTO{i}", "grade": "A+"} for i in range(crypto_count)]
        state.stock_opportunities = [{"ticker": f"STOCK{i}", "grade": "A+"} for i in range(stock_count)]
        state.etf_opportunities = [{"ticker": f"ETF{i}", "grade": "A+"} for i in range(etf_count)]

        # Act
        result = orchestrator.check_investment_discovery()

        # Assert - Should consolidate all opportunities
        expected_total = crypto_count + stock_count + etf_count
        assert result["investment_discovery_complete"] is True
        assert result["total_opportunities"] == expected_total
        assert result["discovery_available"] == (expected_total > 0)
        assert len(state.all_discovery_opportunities) == expected_total

        # Verify all opportunities are included
        all_tickers = {opp["ticker"] for opp in state.all_discovery_opportunities}
        expected_tickers = {f"CRYPTO{i}" for i in range(crypto_count)} | {f"STOCK{i}" for i in range(stock_count)} | {f"ETF{i}" for i in range(etf_count)}
        assert all_tickers == expected_tickers
