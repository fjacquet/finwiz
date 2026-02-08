"""Orchestrator for portfolio stress testing.

Builds holdings list from flow state, runs predefined stress scenarios,
and stores results back into state for report generation.
"""

from typing import Any

from finwiz.quantitative.stress_testing.engine import PortfolioStressTestEngine
from finwiz.schemas.stress_test import PortfolioStressTestResult
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class StressTestOrchestrator:
    """Orchestrates stress tests using portfolio data from flow state."""

    def __init__(self, state: Any) -> None:
        self.state = state

    def run_stress_tests(self) -> list[PortfolioStressTestResult]:
        """Build holdings from state and run all default stress scenarios."""
        try:
            holdings = self._build_holdings_list()
            if not holdings:
                logger.warning("No holdings available for stress testing")
                return []

            logger.info(f"Running stress tests on {len(holdings)} holdings")
            engine = PortfolioStressTestEngine(holdings)
            return engine.run_all_predefined()

        except Exception as e:
            logger.error(f"Stress testing failed: {e}")
            return []

    def _build_holdings_list(self) -> list[dict[str, Any]]:
        """Extract holdings from state with enrichment data."""
        holdings: list[dict[str, Any]] = []

        # Get deep analysis results for tickers
        deep_results = getattr(self.state, "deep_analysis_results", {}) or {}
        prefetched = getattr(self.state, "prefetched_data", {}) or {}

        # Count total for equal-weight fallback
        total_count = len(deep_results) if deep_results else 0
        equal_weight = 1.0 / total_count if total_count > 0 else 0.0

        for ticker, result in deep_results.items():
            # Get enrichment from prefetched data
            enrichment = {}
            if prefetched and ticker in prefetched:
                enrichment = prefetched[ticker].get("enrichment", {})

            # Determine asset type from result or default
            asset_type = "stock"
            if hasattr(result, "asset_type"):
                asset_type = result.asset_type
            elif ticker in ("BTC", "ETH", "SOL", "ADA"):
                asset_type = "crypto"

            holdings.append(
                {
                    "ticker": ticker,
                    "weight": equal_weight,
                    "asset_type": asset_type,
                    "sector": enrichment.get("sector", "Unknown"),
                    "beta": enrichment.get("beta", 1.0),
                }
            )

        return holdings
