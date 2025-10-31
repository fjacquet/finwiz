"""
Portfolio rebalancing optimization utilities.

This module contains optimization algorithms and trade generation logic
for portfolio rebalancing operations.
"""

from typing import Any

from finwiz.quantitative.rebalancing_engine import OptimizationConstraint, RebalancingEngine
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class OptimizationFailedError(Exception):
    """Raised when portfolio optimization fails."""

    def __init__(self, reason: str) -> None:
        """Initialize with failure reason."""
        super().__init__(f"Portfolio optimization failed: {reason}")
        self.reason = reason


class RebalancingOptimizer:
    """Handles portfolio rebalancing optimization operations."""

    def __init__(self, rebalancing_engine: RebalancingEngine | None = None) -> None:
        """
        Initialize the rebalancing optimizer.

        Args:
            rebalancing_engine: Rebalancing optimization engine instance

        """
        self.rebalancing_engine = rebalancing_engine or RebalancingEngine()
        self.logger = logger

    async def optimize_trades(self, config: PortfolioConfiguration, current_analysis: Any, rebalancing_needs: list[Any], price_data: dict[str, Any]) -> Any:
        """
        Optimize trade recommendations.

        Args:
            config: Portfolio configuration
            current_analysis: Current portfolio analysis
            rebalancing_needs: List of rebalancing needs
            price_data: Current price data

        Returns:
            Optimized trades result

        Raises:
            OptimizationFailedError: If optimization fails

        """
        try:
            # Convert price data to simple dict
            price_dict = {symbol: price_data.price for symbol, price_data in price_data.items()}

            # Build constraints
            constraints = self.build_optimization_constraints(config)

            # Optimize trades
            optimized_trades = self.rebalancing_engine.optimize_rebalancing_trades(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_analysis,
                target_weights=config.target_weights,
                prices=price_dict,
                config=config,
                constraints=constraints,
            )

            if not optimized_trades.trades:
                self.logger.info("No trades required - portfolio is within tolerance")
            else:
                self.logger.info(f"Optimized {len(optimized_trades.trades)} trade recommendations")

            return optimized_trades

        except Exception as e:
            self.logger.error(f"Trade optimization failed: {e}")
            raise OptimizationFailedError(str(e)) from e

    async def generate_enhanced_recommendations(
        self, config: PortfolioConfiguration, current_analysis: Any, rebalancing_needs: list[Any], price_data: dict[str, Any]
    ) -> tuple[list[Any], list[str]]:
        """
        Generate enhanced trade recommendations using the trade recommendation system.

        Args:
            config: Portfolio configuration
            current_analysis: Current portfolio analysis
            rebalancing_needs: List of rebalancing needs
            price_data: Current price data

        Returns:
            Tuple of (recommendations, validation_errors)

        Raises:
            OptimizationFailedError: If recommendation generation fails

        """
        try:
            # Convert price data to simple dict
            price_dict = {}
            for symbol, price_data_item in price_data.items():
                if hasattr(price_data_item, "price"):
                    price_dict[symbol] = price_data_item.price
                else:
                    # Handle case where price_data is already a float
                    price_dict[symbol] = float(price_data_item)

            # Generate enhanced recommendations
            recommendations, validation_errors = self.rebalancing_engine.generate_enhanced_trade_recommendations(
                rebalancing_needs=rebalancing_needs,
                current_portfolio=current_analysis,
                target_weights=config.target_weights,
                prices=price_dict,
                config=config,
                holdings=config.holdings,
            )

            self.logger.info(f"Generated {len(recommendations)} enhanced trade recommendations")
            return recommendations, validation_errors

        except Exception as e:
            self.logger.error(f"Enhanced recommendation generation failed: {e}")
            raise OptimizationFailedError(f"Enhanced recommendation generation failed: {e}") from e

    def build_optimization_constraints(self, config: PortfolioConfiguration) -> list[OptimizationConstraint]:
        """
        Build optimization constraints from configuration.

        Args:
            config: Portfolio configuration

        Returns:
            List of optimization constraints

        """
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

    def create_optimized_trades_from_recommendations(self, recommendations: list[Any]) -> Any:
        """
        Create OptimizedTrades structure from trade recommendations for compatibility.

        Args:
            recommendations: List of trade recommendations

        Returns:
            OptimizedTrades structure

        """
        from finwiz.quantitative.rebalancing_engine import OptimizedTrades

        # Calculate total capital used
        capital_used = sum(abs(rec.trade_value) for rec in recommendations if hasattr(rec, "trade_value"))

        return OptimizedTrades(
            trades=recommendations,
            capital_used=capital_used,
            optimization_metadata={
                "algorithm": "enhanced_trade_recommendation_system",
                "total_recommendations": len(recommendations),
                "capital_efficiency": capital_used / max(1, len(recommendations)),
            },
        )

    def validate_optimization_constraints(self, config: PortfolioConfiguration, trades: list[Any], current_analysis: Any) -> tuple[bool, list[str]]:
        """
        Validate that proposed trades meet optimization constraints.

        Args:
            config: Portfolio configuration
            trades: List of proposed trades
            current_analysis: Current portfolio analysis

        Returns:
            Tuple of (is_valid, list_of_violations)

        """
        violations = []

        try:
            # Check minimum trade size constraint
            small_trades = [trade for trade in trades if hasattr(trade, "trade_value") and abs(trade.trade_value) < config.min_trade_size]
            if small_trades:
                violations.append(f"Found {len(small_trades)} trades below minimum size of ${config.min_trade_size}")

            # Check maximum position size constraint
            max_position_limit = 0.25  # 25%
            large_positions = []
            for trade in trades:
                if hasattr(trade, "projected_weight_after_trade"):
                    if trade.projected_weight_after_trade > max_position_limit:
                        large_positions.append(trade.symbol)

            if large_positions:
                violations.append(f"Positions exceed 25% limit: {', '.join(large_positions)}")

            # Check turnover constraint
            total_turnover = (
                sum(abs(trade.trade_value) for trade in trades if hasattr(trade, "trade_value")) / current_analysis.total_value if current_analysis.total_value > 0 else 0
            )

            if total_turnover > 0.5:  # 50% maximum turnover
                violations.append(f"Portfolio turnover {total_turnover:.1%} exceeds 50% limit")

            # Check available capital constraint
            if config.available_capital != 0:
                required_capital = sum(max(0, trade.trade_value) for trade in trades if hasattr(trade, "trade_value"))
                if required_capital > abs(config.available_capital):
                    violations.append(f"Required capital ${required_capital:,.2f} exceeds available ${abs(config.available_capital):,.2f}")

            is_valid = len(violations) == 0
            return is_valid, violations

        except Exception as e:
            self.logger.error(f"Error validating optimization constraints: {e}")
            return False, [f"Constraint validation error: {str(e)}"]

    def calculate_optimization_metrics(self, trades: list[Any], current_analysis: Any) -> dict[str, Any]:
        """
        Calculate optimization performance metrics.

        Args:
            trades: List of optimized trades
            current_analysis: Current portfolio analysis

        Returns:
            Dictionary of optimization metrics

        """
        try:
            metrics = {
                "total_trades": len(trades),
                "total_trade_value": sum(abs(trade.trade_value) for trade in trades if hasattr(trade, "trade_value")),
                "portfolio_turnover": 0.0,
                "capital_efficiency": 0.0,
                "optimization_score": 0.0,
            }

            if current_analysis.total_value > 0:
                metrics["portfolio_turnover"] = metrics["total_trade_value"] / current_analysis.total_value

            if len(trades) > 0:
                metrics["capital_efficiency"] = metrics["total_trade_value"] / len(trades)

            # Calculate optimization score (0-100)
            # Based on: trade efficiency, constraint compliance, risk reduction
            efficiency_score = min(100, (1 - metrics["portfolio_turnover"]) * 100)
            trade_count_penalty = max(0, (len(trades) - 5) * 5)  # Penalty for too many trades
            metrics["optimization_score"] = max(0, efficiency_score - trade_count_penalty)

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating optimization metrics: {e}")
            return {
                "total_trades": len(trades),
                "total_trade_value": 0.0,
                "portfolio_turnover": 0.0,
                "capital_efficiency": 0.0,
                "optimization_score": 0.0,
                "error": str(e),
            }

    def suggest_optimization_improvements(self, trades: list[Any], constraints: list[OptimizationConstraint], current_analysis: Any) -> list[str]:
        """
        Suggest improvements to optimization results.

        Args:
            trades: List of optimized trades
            constraints: List of optimization constraints
            current_analysis: Current portfolio analysis

        Returns:
            List of improvement suggestions

        """
        suggestions = []

        try:
            # Check if too many small trades
            small_trades = [trade for trade in trades if hasattr(trade, "trade_value") and abs(trade.trade_value) < 1000]
            if len(small_trades) > 3:
                suggestions.append("Consider consolidating small trades to reduce transaction costs")

            # Check for high turnover
            if current_analysis.total_value > 0:
                turnover = sum(abs(trade.trade_value) for trade in trades if hasattr(trade, "trade_value")) / current_analysis.total_value

                if turnover > 0.3:
                    suggestions.append("High portfolio turnover detected - consider phased rebalancing")

            # Check for concentration risk
            large_trades = [trade for trade in trades if hasattr(trade, "projected_weight_after_trade") and trade.projected_weight_after_trade > 0.2]
            if large_trades:
                suggestions.append("Large position sizes detected - monitor concentration risk")

            # Check timing considerations
            if len(trades) > 10:
                suggestions.append("Consider splitting execution across multiple sessions")

            return suggestions

        except Exception as e:
            self.logger.error(f"Error generating optimization suggestions: {e}")
            return ["Error generating suggestions - review optimization manually"]
