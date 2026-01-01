"""Portfolio review orchestrator module with rebalancing integration."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.orchestrators.review_decisions import (
    add_portfolio_review_sections,
    add_rebalancing_sections,
)
from finwiz.orchestrators.review_engine import (
    build_portfolio_review,
    get_csv_paths,
    run,
    run_with_rebalancing,
    save_review_json,
)
from finwiz.utils.cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

# Re-export main functions for backward compatibility
__all__ = [
    "build_portfolio_review",
    "get_csv_paths",
    "run",
    "run_with_rebalancing",
    "save_review_json",
    "EnhancedPortfolioReviewOrchestrator",
]


class EnhancedPortfolioReviewOrchestrator:
    """
    Enhanced portfolio review orchestrator with integrated rebalancing capabilities.

    Provides seamless integration between portfolio review and rebalancing analysis,
    with shared caching and unified reporting.
    """

    def __init__(self) -> None:
        """Initialize the enhanced orchestrator."""
        self.cache_manager = get_cache_manager()

    async def run_comprehensive_analysis(
        self,
        target_weights: dict[str, float] | None = None,
        available_capital: float = 0.0,
        enable_caching: bool = True,
    ) -> dict[str, Any]:
        """
        Run comprehensive portfolio analysis including review and rebalancing.

        Args:
            target_weights: Target allocation weights for rebalancing
            available_capital: Available capital for rebalancing
            enable_caching: Whether to use caching for expensive operations

        Returns:
            Comprehensive analysis results

        """
        cache_key = ["portfolio_analysis", str(target_weights), str(available_capital)]

        if enable_caching:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                result: dict[str, Any] = cached_result
                return result

        # Run portfolio review
        review_path, rebalancing_result = await run_with_rebalancing(
            target_weights=target_weights,
            available_capital=available_capital,
            include_rebalancing=target_weights is not None,
        )

        # Load review data
        review_data = json.loads(Path(review_path).read_text(encoding="utf-8"))

        # Combine results
        comprehensive_result = {
            "portfolio_review": review_data,
            "rebalancing_analysis": rebalancing_result.model_dump() if rebalancing_result else None,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "has_rebalancing_recommendations": rebalancing_result is not None,
        }

        # Cache the result for 30 minutes
        if enable_caching:
            await self.cache_manager.set(cache_key, comprehensive_result, ttl=1800)

        return comprehensive_result

    async def generate_unified_report(
        self,
        analysis_result: dict[str, Any],
        language: str = "en",
    ) -> str:
        """
        Generate unified HTML report combining portfolio review and rebalancing.

        Args:
            analysis_result: Comprehensive analysis result
            language: Report language (en/fr)

        Returns:
            HTML report content

        """
        from finwiz.tools.html_report_generator import HTMLReportGenerator

        generator = HTMLReportGenerator()

        # Add portfolio review sections
        self._add_portfolio_review_sections(generator, analysis_result["portfolio_review"])

        # Add rebalancing sections if available
        if analysis_result["rebalancing_analysis"]:
            self._add_rebalancing_sections(generator, analysis_result["rebalancing_analysis"])

        # Generate report using unified template
        title = f"Comprehensive Portfolio Analysis - {datetime.now().strftime('%Y-%m-%d')}"

        # Try to use unified HTML generator if available
        if hasattr(generator, "generate_unified_html"):
            return generator.generate_unified_html(title=title, language=language)
        else:
            return generator.generate_html_fallback(title=title, language=language)

    def _add_portfolio_review_sections(self, generator: Any, review_data: dict[str, Any]) -> None:
        """Add portfolio review sections to the report."""
        add_portfolio_review_sections(generator, review_data)

    def _add_rebalancing_sections(self, generator: Any, rebalancing_data: dict[str, Any]) -> None:
        """Add rebalancing sections to the report."""
        add_rebalancing_sections(generator, rebalancing_data)


if __name__ == "__main__":
    import asyncio
    import json

    async def main() -> None:
        """Run portfolio review demonstration."""
        # Run standard portfolio review
        path = run()
        print(f"Portfolio review saved to: {path}")

        # Example of enhanced analysis with rebalancing
        orchestrator = EnhancedPortfolioReviewOrchestrator()

        # Example target weights (adjust as needed)
        target_weights = {
            "AAPL": 0.20,
            "GOOGL": 0.15,
            "MSFT": 0.15,
            "TSLA": 0.10,
            "NVDA": 0.10,
            "SPY": 0.30,  # ETF allocation
        }

        try:
            comprehensive_result = await orchestrator.run_comprehensive_analysis(
                target_weights=target_weights,
                available_capital=10000.0,
            )

            # Save comprehensive result
            project_root = Path(__file__).resolve().parents[3]
            comprehensive_out = project_root / "output" / "portfolio" / "comprehensive_analysis.json"
            comprehensive_out.parent.mkdir(parents=True, exist_ok=True)
            comprehensive_out.write_text(json.dumps(comprehensive_result, indent=2, default=str), encoding="utf-8")
            print(f"Comprehensive analysis saved to: {comprehensive_out}")

            # Generate unified report
            html_report = await orchestrator.generate_unified_report(comprehensive_result)
            report_out = project_root / "output" / "portfolio" / "comprehensive_report.html"
            report_out.write_text(html_report, encoding="utf-8")
            print(f"Unified report saved to: {report_out}")

        except Exception as e:
            print(f"Enhanced analysis failed: {e}")

    asyncio.run(main())
