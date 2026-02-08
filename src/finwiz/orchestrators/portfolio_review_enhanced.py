"""
Enhanced portfolio review orchestrator with integrated rebalancing.

This module contains the EnhancedPortfolioReviewOrchestrator class that provides
unified portfolio analysis combining review and rebalancing capabilities.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.infrastructure.caching.manager import get_cache_manager
from finwiz.orchestrators.portfolio_review_orchestrator import run_with_rebalancing
from finwiz.reporting.portfolio_review_html import (
    add_portfolio_review_sections,
    add_rebalancing_sections,
)

logger = logging.getLogger(__name__)


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

        review_path, rebalancing_result = await run_with_rebalancing(
            target_weights=target_weights,
            available_capital=available_capital,
            include_rebalancing=target_weights is not None,
        )

        review_data = json.loads(Path(review_path).read_text(encoding="utf-8"))

        comprehensive_result = {
            "portfolio_review": review_data,
            "rebalancing_analysis": rebalancing_result,
            "analysis_timestamp": datetime.now(UTC).isoformat(),
            "has_rebalancing_recommendations": rebalancing_result is not None,
        }

        if enable_caching:
            await self.cache_manager.set(cache_key, comprehensive_result, ttl=1800)

        return comprehensive_result

    async def generate_unified_report(
        self,
        analysis_result: dict[str, Any],
        language: str = "en",
    ) -> str:
        """Generate unified HTML report combining portfolio review and rebalancing."""
        from finwiz.tools.html_report_generator import HTMLReportGenerator

        generator = HTMLReportGenerator()

        add_portfolio_review_sections(generator, analysis_result["portfolio_review"])

        if analysis_result["rebalancing_analysis"]:
            add_rebalancing_sections(generator, analysis_result["rebalancing_analysis"])

        title = f"Comprehensive Portfolio Analysis - {datetime.now().strftime('%Y-%m-%d')}"

        if hasattr(generator, "generate_unified_html"):
            return generator.generate_unified_html(title=title, language=language)
        else:
            return generator.generate_html_fallback(title=title, language=language)


__all__ = [
    "EnhancedPortfolioReviewOrchestrator",
]
