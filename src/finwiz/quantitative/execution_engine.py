"""
Portfolio rebalancing execution engine.

This module provides the main execution engine that coordinates optimization strategies,
trade generation, and enhanced recommendation systems for portfolio rebalancing.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.quantitative.optimization_algorithms import (
    MinimizeCostsStrategy,
    MinimizeTradesStrategy,
    OptimizationConstraint,
    OptimizedTrades,
    RiskAwareStrategy,
)
from finwiz.quantitative.trade_generation import TradeGenerator
from finwiz.quantitative.trade_recommendation_system import TradeRecommendationSystem
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingMethod,
    RebalancingNeed,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)


class RebalancingEngine:
    """Core execution engine for portfolio rebalancing."""

    def __init__(self) -> None:
        """Initialize the rebalancing engine."""
        self.strategies = {
            RebalancingMethod.MINIMIZE_TRADES: MinimizeTradesStrategy(),
            RebalancingMethod.MINIMIZE_COSTS: MinimizeCostsStrategy(),
            RebalancingMethod.RISK_AWARE: RiskAwareStrategy(),
        }
        self.trade_recommendation_system = TradeRecommendationSystem()
        self.trade_generator = TradeGenerator()
        logger.info("RebalancingEngine initialized")

    def optimize_rebalancing_trades(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        config: PortfolioConfiguration,
        constraints: list[OptimizationConstraint] | None = None,
    ) -> OptimizedTrades:
        """
        Optimize rebalancing trades based on configuration.

        Args:
            rebalancing_needs: List of positions needing rebalancing
            current_portfolio: Current portfolio analysis
            target_weights: Target weight allocations
            prices: Current market prices
            config: Portfolio configuration
            constraints: Additional optimization constraints

        Returns:
            OptimizedTrades: Optimized trade recommendations

        """
        logger.info(f"Optimizing rebalancing trades using {config.rebalancing_method}")

        if constraints is None:
            constraints = self._build_default_constraints(config)

        strategy = self.strategies.get(config.rebalancing_method)
        if not strategy:
            raise ValueError(f"Unknown rebalancing method: {config.rebalancing_method}")

        try:
            result = strategy.optimize(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_portfolio,
                target_weights=target_weights,
                prices=prices,
                available_capital=config.available_capital,
                constraints=constraints,
                config=config,
            )

            logger.info(f"Optimization complete: {len(result.trades)} trades, ${result.total_cost:.2f} cost")
            return result

        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

    def minimize_transaction_costs(self, trades: list[TradeRecommendation]) -> list[TradeRecommendation]:
        """
        Post-process trades to minimize transaction costs.

        Args:
            trades: Initial trade recommendations

        Returns:
            list[TradeRecommendation]: Cost-optimized trades

        """
        return self.trade_generator.minimize_transaction_costs(trades)

    def calculate_tax_implications(self, trades: list[TradeRecommendation], holdings: list[Holding]) -> dict[str, Any]:
        """
        Calculate tax implications of proposed trades.

        Args:
            trades: Proposed trade recommendations
            holdings: Current holdings with cost basis

        Returns:
            dict: Tax analysis results

        """
        return self.trade_generator.calculate_tax_implications(trades, holdings)

    def generate_enhanced_trade_recommendations(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        config: PortfolioConfiguration,
        holdings: list[Holding],
    ) -> tuple[list[TradeRecommendation], list[str]]:
        """
        Generate enhanced trade recommendations using the trade recommendation system.

        Args:
            rebalancing_needs: List of positions needing rebalancing
            current_portfolio: Current portfolio analysis
            target_weights: Target weight allocations
            prices: Current market prices
            config: Portfolio configuration
            holdings: Current holdings

        Returns:
            tuple: (trade_recommendations, validation_errors)

        """
        logger.info("Generating enhanced trade recommendations")

        try:
            # Generate recommendations using the trade recommendation system
            recommendations = self.trade_recommendation_system.generate_trade_recommendations(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_portfolio,
                target_weights=target_weights,
                prices=prices,
                config=config,
                holdings=holdings,
            )

            # Validate recommendations
            valid_recommendations, validation_errors = self.trade_recommendation_system.validate_trade_recommendations(
                recommendations, config
            )

            logger.info(
                f"Enhanced recommendations generated: {len(valid_recommendations)} valid, "
                f"{len(validation_errors)} validation errors"
            )

            return valid_recommendations, validation_errors

        except Exception as e:
            logger.error(f"Enhanced trade recommendation generation failed: {e}")
            raise

    def _build_default_constraints(self, config: PortfolioConfiguration) -> list[OptimizationConstraint]:
        """Build default optimization constraints from configuration."""
        constraints = [
            OptimizationConstraint(
                name="min_trade_size",
                constraint_type="min_trade_size",
                value=config.min_trade_size,
                description="Minimum trade size to execute",
            ),
            OptimizationConstraint(
                name="max_position",
                constraint_type="max_position",
                value=0.25,  # 25% maximum position size
                description="Maximum position size as percentage of portfolio",
            ),
            OptimizationConstraint(
                name="turnover",
                constraint_type="turnover",
                value=0.5,  # 50% maximum turnover
                description="Maximum portfolio turnover",
            ),
        ]

        if config.available_capital != 0:
            constraints.append(
                OptimizationConstraint(
                    name="capital",
                    constraint_type="capital",
                    value=abs(config.available_capital),
                    description="Available capital constraint",
                )
            )

        return constraints
