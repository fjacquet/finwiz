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

    def _build_sector_lookup(self) -> dict[str, str]:
        """Build ticker→sector mapping from portfolio_review holdings."""
        sector_map: dict[str, str] = {}
        portfolio_review = getattr(self.state, "portfolio_review", None)
        if not isinstance(portfolio_review, dict):
            return sector_map
        for holding in portfolio_review.get("holdings", []):
            if not isinstance(holding, dict):
                continue
            ticker = holding.get("ticker") or holding.get("symbol", "")
            sector = holding.get("sector") or holding.get("gics_sector", "")
            if ticker and sector:
                sector_map[str(ticker)] = str(sector)
        return sector_map

    def _build_holdings_list(self) -> list[dict[str, Any]]:
        """Extract holdings from state with enrichment data.

        Beta priority: batch enrichment > DeepAnalysisResult.risk_details > 1.0
        Sector priority: batch enrichment > portfolio_review > "Unknown"
        """
        holdings: list[dict[str, Any]] = []

        # Get deep analysis results for tickers
        deep_results = getattr(self.state, "deep_analysis_results", {}) or {}
        prefetched = getattr(self.state, "prefetched_data", {}) or {}
        sector_lookup = self._build_sector_lookup()

        # Count total for equal-weight fallback
        total_count = len(deep_results) if deep_results else 0
        equal_weight = 1.0 / total_count if total_count > 0 else 0.0

        for ticker, result in deep_results.items():
            # Get enrichment from prefetched data (batch prefetch path)
            enrichment: dict[str, Any] = {}
            if prefetched and ticker in prefetched:
                enrichment = prefetched[ticker].get("enrichment", {})

            # Beta: batch enrichment → scorer risk_details → 1.0
            risk_details: dict[str, Any] = getattr(result, "risk_details", {}) or {}
            beta = enrichment.get("beta") or risk_details.get("beta", 1.0) or 1.0

            # Sector: batch enrichment → portfolio_review → "Unknown"
            sector = enrichment.get("sector") or sector_lookup.get(ticker, "Unknown")

            # Determine asset type from result or default
            asset_type = "stock"
            if hasattr(result, "asset_class"):
                asset_type = result.asset_class
            elif ticker.endswith("-USD") or ticker in ("BTC", "ETH", "SOL", "ADA"):
                asset_type = "crypto"

            holdings.append(
                {
                    "ticker": ticker,
                    "weight": equal_weight,
                    "asset_type": asset_type,
                    "sector": sector,
                    "beta": float(beta),
                }
            )

        return holdings
