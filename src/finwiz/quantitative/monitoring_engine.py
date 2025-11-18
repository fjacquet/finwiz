"""
Portfolio monitoring engine for continuous drift monitoring.

This module provides the core monitoring loop and drift checking functionality
for portfolio monitoring systems.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from finwiz.quantitative.portfolio_analyzer import PortfolioAnalyzer
from finwiz.quantitative.rebalancing_engine import RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingNeed,
    UrgencyLevel,
)
from finwiz.tools.portfolio_price_service import PortfolioPriceService

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """Core monitoring engine for portfolio drift detection."""

    def __init__(
        self,
        price_service: PortfolioPriceService | None = None,
        portfolio_analyzer: PortfolioAnalyzer | None = None,
        rebalancing_engine: RebalancingEngine | None = None,
    ) -> None:
        """Initialize monitoring engine."""
        self.price_service = price_service or PortfolioPriceService()
        self.portfolio_analyzer = portfolio_analyzer or PortfolioAnalyzer()
        self.rebalancing_engine = rebalancing_engine or RebalancingEngine()

        # Internal state
        self._last_check_times: dict[str, datetime] = {}

        logger.info("Monitoring engine initialized")

    async def check_portfolio_drift(self, portfolio_id: str, portfolio_config: PortfolioConfiguration) -> list[RebalancingNeed]:
        """Check current portfolio drift against targets."""
        try:
            # Get current prices
            symbols = [holding.symbol for holding in portfolio_config.holdings]
            prices = await self.price_service.get_current_prices(symbols)

            # Analyze current portfolio
            current_analysis = self.portfolio_analyzer.analyze_current_portfolio(portfolio_config.holdings, prices)

            # Identify rebalancing needs
            rebalancing_needs = self.portfolio_analyzer.identify_rebalancing_needs(
                current_analysis.weightings,
                portfolio_config.target_weights,
                portfolio_config.tolerance_bands,
                portfolio_config.global_tolerance,
            )

            # Update last check time
            self._last_check_times[portfolio_id] = datetime.now()

            return rebalancing_needs

        except Exception as e:
            logger.error(f"Failed to check portfolio drift for {portfolio_id}: {e}")
            raise

    def _calculate_health_score(self, rebalancing_needs: list[RebalancingNeed], portfolio_config: PortfolioConfiguration) -> float:
        """Calculate overall portfolio health score (1-10 scale)."""
        if not rebalancing_needs:
            return 10.0

        # Calculate weighted deviation score
        total_deviation = sum([abs(need.deviation) for need in rebalancing_needs])
        avg_deviation = total_deviation / len(rebalancing_needs)

        # Calculate positions out of tolerance ratio
        positions_out_of_tolerance = len([need for need in rebalancing_needs if need.needs_rebalancing])
        out_of_tolerance_ratio = positions_out_of_tolerance / len(rebalancing_needs)

        # Health score calculation (higher deviations and more positions out of tolerance = lower score)
        base_score = 10.0
        deviation_penalty = min(avg_deviation * 50, 5.0)  # Max 5 points penalty for deviation
        tolerance_penalty = out_of_tolerance_ratio * 3.0  # Max 3 points penalty for positions out of tolerance

        health_score = max(base_score - deviation_penalty - tolerance_penalty, 1.0)

        return round(health_score, 1)

    def _determine_rebalancing_urgency(self, positions_needing_attention: list[RebalancingNeed], max_deviation: float) -> UrgencyLevel:
        """Determine overall rebalancing urgency level."""
        if not positions_needing_attention:
            return UrgencyLevel.LOW

        if max_deviation > 0.20:  # 20%+ deviation
            return UrgencyLevel.CRITICAL
        elif max_deviation > 0.15:  # 15%+ deviation
            return UrgencyLevel.HIGH
        elif len(positions_needing_attention) >= 3:  # Multiple positions
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _get_health_status_description(self, health_score: float) -> str:
        """Get health status description based on score."""
        if health_score >= 9.0:
            return "Excellent - Portfolio is well-balanced"
        elif health_score >= 7.0:
            return "Good - Minor deviations within acceptable range"
        elif health_score >= 5.0:
            return "Fair - Some positions may need attention"
        elif health_score >= 3.0:
            return "Poor - Multiple positions need rebalancing"
        else:
            return "Critical - Immediate rebalancing recommended"

    def _get_days_since_last_rebalance(self, portfolio_id: str) -> int | None:
        """Get days since last rebalancing (would typically query database)."""
        # This would typically query a database for the last rebalancing date
        # For now, return None to indicate no data available
        return None

    def get_last_check_time(self, portfolio_id: str) -> datetime | None:
        """Get the last check time for a portfolio."""
        return self._last_check_times.get(portfolio_id)

    def get_monitoring_statistics(self) -> dict[str, Any]:
        """Get overall monitoring engine statistics."""
        return {
            "total_portfolios_checked": len(self._last_check_times),
            "last_system_check": datetime.now().isoformat(),
        }
