"""
Portfolio rebalancing calculation utilities.

This module contains calculation logic for cost analysis, risk scores,
execution summaries, and projected portfolio states.
"""

from typing import Any

from finwiz.exceptions.orchestrator import PortfolioRebalancingError
from finwiz.schemas.portfolio_rebalancing import CostAnalysis, ExecutionSummary, PortfolioConfiguration
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class RebalancingCalculator:
    """Handles calculations for portfolio rebalancing operations."""

    def __init__(self) -> None:
        """Initialize the rebalancing calculator."""
        self.logger = logger

    async def calculate_projected_portfolio(self, config: PortfolioConfiguration, current_analysis: Any, trades: list[Any], price_data: dict[str, Any]) -> Any:
        """
        Calculate projected portfolio state after executing trades.

        Args:
            config: Portfolio configuration
            current_analysis: Current portfolio analysis
            trades: List of proposed trades
            price_data: Current price data

        Returns:
            Projected portfolio analysis

        Raises:
            PortfolioRebalancingError: If calculation fails

        """
        try:
            # For now, return a simplified projected analysis
            # In a full implementation, this would simulate the portfolio after trades
            projected_analysis = current_analysis.model_copy()

            # Update weightings based on trades (simplified)
            for trade in trades:
                if trade.symbol in config.target_weights:
                    projected_analysis.weightings[trade.symbol] = trade.projected_weight_after_trade

            # Recalculate deviations
            projected_analysis.deviations_from_target = {
                symbol: projected_analysis.weightings.get(symbol, 0.0) - config.target_weights.get(symbol, 0.0) for symbol in config.target_weights
            }

            # Update positions needing rebalancing
            projected_analysis.positions_needing_rebalancing = [
                symbol for symbol, deviation in projected_analysis.deviations_from_target.items() if abs(deviation) > config.tolerance_bands.get(symbol, config.global_tolerance)
            ]

            return projected_analysis

        except Exception as e:
            self.logger.error(f"Error calculating projected portfolio: {e}")
            raise PortfolioRebalancingError(f"Failed to calculate projected portfolio: {e}") from e

    def calculate_cost_analysis(self, optimized_trades: Any, portfolio_value: float) -> CostAnalysis:
        """
        Calculate comprehensive cost analysis.

        Args:
            optimized_trades: Optimized trades result
            portfolio_value: Current portfolio value

        Returns:
            CostAnalysis: Comprehensive cost analysis

        Raises:
            PortfolioRebalancingError: If calculation fails

        """
        try:
            total_commission = sum(trade.estimated_commission for trade in optimized_trades.trades)
            total_spread = sum(trade.estimated_spread_cost for trade in optimized_trades.trades)
            total_costs = total_commission + total_spread

            cost_percentage = (total_costs / portfolio_value * 100) if portfolio_value > 0 else 0.0

            # Estimate break-even days (simplified calculation)
            # Assume 7% annual return, so daily return is ~0.019%
            daily_return_rate = 0.07 / 365
            break_even_days = int(cost_percentage / (daily_return_rate * 100)) if daily_return_rate > 0 else None

            return CostAnalysis(
                total_transaction_costs=total_costs,
                commission_costs=total_commission,
                spread_costs=total_spread,
                market_impact_costs=0.0,  # Simplified - would need more complex calculation
                cost_as_percentage=cost_percentage,
                break_even_days=break_even_days,
            )

        except Exception as e:
            self.logger.error(f"Error calculating cost analysis: {e}")
            raise PortfolioRebalancingError(f"Cost analysis failed: {e}") from e

    def calculate_risk_scores(self, current_analysis: Any, projected_analysis: Any) -> tuple[float, float]:
        """
        Calculate current and projected risk scores.

        Args:
            current_analysis: Current portfolio analysis
            projected_analysis: Projected portfolio analysis

        Returns:
            Tuple of (current_risk_score, projected_risk_score)

        """
        try:
            # Use concentration risk as primary risk metric (0-10 scale)
            current_risk = current_analysis.risk_metrics.get("concentration_risk", 5.0)
            projected_risk = projected_analysis.risk_metrics.get("concentration_risk", 5.0)

            # Ensure scores are within valid range
            current_risk = max(0.0, min(10.0, current_risk))
            projected_risk = max(0.0, min(10.0, projected_risk))

            return current_risk, projected_risk

        except Exception as e:
            self.logger.warning(f"Error calculating risk scores, using defaults: {e}")
            return 5.0, 5.0  # Default moderate risk

    def generate_execution_summary(self, optimized_trades: Any, config: PortfolioConfiguration) -> ExecutionSummary:
        """
        Generate execution summary.

        Args:
            optimized_trades: Optimized trades result
            config: Portfolio configuration

        Returns:
            ExecutionSummary: Summary of execution requirements

        Raises:
            PortfolioRebalancingError: If generation fails

        """
        try:
            total_trades = len([t for t in optimized_trades.trades if t.action.value != "HOLD"])
            positions_with_action = len(set(t.symbol for t in optimized_trades.trades if t.action.value != "HOLD"))
            total_positions = len(config.holdings)
            positions_within_tolerance = total_positions - positions_with_action

            # Estimate execution time (simplified)
            if total_trades == 0:
                execution_time = "No trades required"
            elif total_trades <= 3:
                execution_time = "5-10 minutes"
            elif total_trades <= 10:
                execution_time = "15-30 minutes"
            else:
                execution_time = "30-60 minutes"

            return ExecutionSummary(
                total_trades_required=total_trades,
                positions_requiring_action=positions_with_action,
                positions_within_tolerance=positions_within_tolerance,
                estimated_execution_time=execution_time,
                capital_required=optimized_trades.capital_used,
            )

        except Exception as e:
            self.logger.error(f"Error generating execution summary: {e}")
            raise PortfolioRebalancingError(f"Execution summary generation failed: {e}") from e

    def calculate_portfolio_metrics(self, analysis: Any) -> dict[str, Any]:
        """
        Calculate additional portfolio metrics.

        Args:
            analysis: Portfolio analysis

        Returns:
            Dictionary of portfolio metrics

        """
        try:
            metrics = {
                "total_value": analysis.total_value,
                "position_count": len(analysis.weightings),
                "largest_position": max(analysis.weightings.values()) if analysis.weightings else 0.0,
                "smallest_position": min(analysis.weightings.values()) if analysis.weightings else 0.0,
                "concentration_ratio": self._calculate_concentration_ratio(analysis.weightings),
                "diversification_score": self._calculate_diversification_score(analysis.weightings),
            }

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}")
            return {
                "total_value": getattr(analysis, "total_value", 0.0),
                "position_count": 0,
                "largest_position": 0.0,
                "smallest_position": 0.0,
                "concentration_ratio": 0.0,
                "diversification_score": 0.0,
                "error": str(e),
            }

    def _calculate_concentration_ratio(self, weightings: dict[str, float]) -> float:
        """Calculate concentration ratio (sum of squares of weights)."""
        if not weightings:
            return 0.0

        return sum(weight**2 for weight in weightings.values())

    def _calculate_diversification_score(self, weightings: dict[str, float]) -> float:
        """Calculate diversification score (1 - concentration ratio)."""
        concentration = self._calculate_concentration_ratio(weightings)
        return max(0.0, 1.0 - concentration)

    def calculate_rebalancing_efficiency(self, trades: list[Any], current_analysis: Any, projected_analysis: Any) -> dict[str, Any]:
        """
        Calculate rebalancing efficiency metrics.

        Args:
            trades: List of proposed trades
            current_analysis: Current portfolio analysis
            projected_analysis: Projected portfolio analysis

        Returns:
            Dictionary of efficiency metrics

        """
        try:
            # Calculate trade efficiency
            total_trade_value = sum(abs(trade.trade_value) for trade in trades if hasattr(trade, "trade_value"))
            portfolio_turnover = total_trade_value / current_analysis.total_value if current_analysis.total_value > 0 else 0

            # Calculate deviation reduction
            current_deviations = sum(abs(dev) for dev in current_analysis.deviations_from_target.values())
            projected_deviations = sum(abs(dev) for dev in projected_analysis.deviations_from_target.values())
            deviation_reduction = current_deviations - projected_deviations

            # Calculate efficiency score
            efficiency_score = 0.0
            if portfolio_turnover > 0:
                efficiency_score = deviation_reduction / portfolio_turnover

            return {
                "total_trade_value": total_trade_value,
                "portfolio_turnover": portfolio_turnover,
                "current_total_deviation": current_deviations,
                "projected_total_deviation": projected_deviations,
                "deviation_reduction": deviation_reduction,
                "efficiency_score": efficiency_score,
                "trade_count": len(trades),
            }

        except Exception as e:
            self.logger.error(f"Error calculating rebalancing efficiency: {e}")
            return {
                "total_trade_value": 0.0,
                "portfolio_turnover": 0.0,
                "current_total_deviation": 0.0,
                "projected_total_deviation": 0.0,
                "deviation_reduction": 0.0,
                "efficiency_score": 0.0,
                "trade_count": len(trades),
                "error": str(e),
            }

    def estimate_market_impact(self, trades: list[Any], market_conditions: dict[str, Any] | None = None) -> dict[str, float]:
        """
        Estimate market impact of trades.

        Args:
            trades: List of proposed trades
            market_conditions: Current market conditions (optional)

        Returns:
            Dictionary of market impact estimates

        """
        try:
            # Simplified market impact calculation
            # In practice, this would use more sophisticated models

            total_impact = 0.0
            large_trade_count = 0

            for trade in trades:
                if hasattr(trade, "trade_value"):
                    trade_size = abs(trade.trade_value)

                    # Estimate impact based on trade size
                    if trade_size > 10000:  # Large trade threshold
                        impact = trade_size * 0.001  # 0.1% impact for large trades
                        large_trade_count += 1
                    else:
                        impact = trade_size * 0.0005  # 0.05% impact for smaller trades

                    total_impact += impact

            # Adjust for market conditions if provided
            volatility_multiplier = 1.0
            if market_conditions and "volatility" in market_conditions:
                volatility = market_conditions["volatility"]
                if volatility > 0.3:  # High volatility
                    volatility_multiplier = 1.5
                elif volatility > 0.2:  # Medium volatility
                    volatility_multiplier = 1.2

            total_impact *= volatility_multiplier

            return {
                "total_market_impact": total_impact,
                "large_trade_count": large_trade_count,
                "volatility_multiplier": volatility_multiplier,
                "average_impact_per_trade": total_impact / len(trades) if trades else 0.0,
            }

        except Exception as e:
            self.logger.error(f"Error estimating market impact: {e}")
            return {
                "total_market_impact": 0.0,
                "large_trade_count": 0,
                "volatility_multiplier": 1.0,
                "average_impact_per_trade": 0.0,
                "error": str(e),
            }
