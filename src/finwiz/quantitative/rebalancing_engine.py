"""
Portfolio rebalancing optimization engine for FinWiz.

This module provides the core optimization algorithms for portfolio rebalancing,
including multiple strategies for minimizing trades, costs, and risk while
respecting capital and size constraints.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from finwiz.quantitative.trade_recommendation_system import TradeRecommendationSystem
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingMethod,
    RebalancingNeed,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class OptimizationConstraint:
    """Constraint for rebalancing optimization."""

    name: str
    constraint_type: str  # 'capital', 'min_trade_size', 'max_position', 'turnover'
    value: float
    description: str


@dataclass
class OptimizedTrades:
    """Result of trade optimization."""

    trades: list[TradeRecommendation]
    total_cost: float
    capital_used: float
    constraints_violated: list[str]
    optimization_score: float
    method_used: str


class OptimizationStrategy(ABC):
    """Abstract base class for optimization strategies."""

    @abstractmethod
    def optimize(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        available_capital: float,
        constraints: list[OptimizationConstraint],
        config: PortfolioConfiguration,
    ) -> OptimizedTrades:
        """Optimize trades based on strategy."""
        pass


class MinimizeTradesStrategy(OptimizationStrategy):
    """Strategy that minimizes the number of trades required."""

    def optimize(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        available_capital: float,
        constraints: list[OptimizationConstraint],
        config: PortfolioConfiguration,
    ) -> OptimizedTrades:
        """Optimize to minimize number of trades."""
        logger.info("Optimizing trades using minimize-trades strategy")

        # Sort by urgency and deviation magnitude
        sorted_needs = sorted(
            [need for need in rebalancing_needs if need.exceeds_tolerance],
            key=lambda x: (x.urgency_score, abs(x.deviation)),
            reverse=True,
        )

        trades = []
        capital_used = 0.0
        total_cost = 0.0
        constraints_violated = []

        # Get constraints
        min_trade_size = next((c.value for c in constraints if c.constraint_type == "min_trade_size"), config.min_trade_size)
        max_turnover = next((c.value for c in constraints if c.constraint_type == "turnover"), 0.5)

        current_turnover = 0.0

        for need in sorted_needs:
            symbol = need.symbol
            current_price = prices.get(symbol, 0.0)

            if current_price <= 0:
                logger.warning(f"Invalid price for {symbol}, skipping")
                continue

            # Calculate required trade
            current_value = current_portfolio.total_value * need.current_weight
            target_value = current_portfolio.total_value * need.target_weight
            trade_value = target_value - current_value

            # Determine action and quantity
            if abs(trade_value) < min_trade_size:
                continue  # Skip trades below minimum size

            if trade_value > 0:
                action = TradeAction.BUY
                quantity = trade_value / current_price
                required_capital = trade_value
            else:
                action = TradeAction.SELL
                quantity = abs(trade_value) / current_price
                required_capital = 0.0  # Selling frees up capital

            # Check capital constraint
            if required_capital > 0 and capital_used + required_capital > available_capital:
                # Try partial trade if possible
                remaining_capital = available_capital - capital_used
                if remaining_capital >= min_trade_size:
                    quantity = remaining_capital / current_price
                    trade_value = remaining_capital
                    required_capital = remaining_capital
                else:
                    constraints_violated.append(f"Insufficient capital for {symbol}")
                    continue

            # Check turnover constraint
            trade_turnover = abs(trade_value) / current_portfolio.total_value
            if current_turnover + trade_turnover > max_turnover:
                constraints_violated.append(f"Turnover limit exceeded for {symbol}")
                continue

            # Calculate costs
            commission = abs(trade_value) * config.transaction_cost_rate
            spread_cost = abs(trade_value) * 0.001  # Assume 0.1% spread
            total_trade_cost = commission + spread_cost

            # Create trade recommendation
            trade = TradeRecommendation(
                symbol=symbol,
                action=action,
                quantity=quantity,
                current_price=current_price,
                trade_value=abs(trade_value),
                estimated_commission=commission,
                estimated_spread_cost=spread_cost,
                total_estimated_cost=total_trade_cost,
                current_weight=need.current_weight,
                target_weight=need.target_weight,
                weight_deviation=need.deviation,
                projected_weight_after_trade=need.target_weight,  # Simplified
                priority=len(trades) + 1,
                urgency=self._calculate_urgency(need.urgency_score),
                rationale=f"Rebalance {symbol} from {need.current_weight:.1%} to {need.target_weight:.1%}",
            )

            trades.append(trade)
            capital_used += required_capital
            total_cost += total_trade_cost
            current_turnover += trade_turnover

        optimization_score = self._calculate_optimization_score(trades, rebalancing_needs)

        return OptimizedTrades(
            trades=trades,
            total_cost=total_cost,
            capital_used=capital_used,
            constraints_violated=constraints_violated,
            optimization_score=optimization_score,
            method_used="MINIMIZE_TRADES",
        )

    def _calculate_urgency(self, urgency_score: float) -> UrgencyLevel:
        """Calculate urgency level from score."""
        if urgency_score >= 0.8:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 0.6:
            return UrgencyLevel.HIGH
        elif urgency_score >= 0.3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _calculate_optimization_score(self, trades: list[TradeRecommendation], needs: list[RebalancingNeed]) -> float:
        """Calculate optimization score (higher is better)."""
        if not needs:
            return 1.0

        # Score based on how many high-priority needs were addressed
        addressed_needs = {trade.symbol for trade in trades}
        high_priority_needs = [need for need in needs if need.urgency_score >= 0.5]

        if not high_priority_needs:
            return 1.0

        addressed_high_priority = len([need for need in high_priority_needs if need.symbol in addressed_needs])
        return addressed_high_priority / len(high_priority_needs)


class MinimizeCostsStrategy(OptimizationStrategy):
    """Strategy that minimizes total transaction costs."""

    def optimize(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        available_capital: float,
        constraints: list[OptimizationConstraint],
        config: PortfolioConfiguration,
    ) -> OptimizedTrades:
        """Optimize to minimize transaction costs."""
        logger.info("Optimizing trades using minimize-costs strategy")

        # Calculate cost-efficiency ratio for each potential trade
        trade_candidates = []

        for need in rebalancing_needs:
            if not need.exceeds_tolerance:
                continue

            symbol = need.symbol
            current_price = prices.get(symbol, 0.0)

            if current_price <= 0:
                continue

            # Calculate trade details
            current_value = current_portfolio.total_value * need.current_weight
            target_value = current_portfolio.total_value * need.target_weight
            trade_value = abs(target_value - current_value)

            # Calculate costs
            commission = trade_value * config.transaction_cost_rate
            spread_cost = trade_value * 0.001
            total_cost = commission + spread_cost

            # Calculate benefit (reduction in deviation)
            benefit = abs(need.deviation) * current_portfolio.total_value

            # Cost-efficiency ratio (benefit per dollar of cost)
            efficiency = benefit / total_cost if total_cost > 0 else 0

            trade_candidates.append(
                {
                    "need": need,
                    "trade_value": trade_value,
                    "total_cost": total_cost,
                    "efficiency": efficiency,
                    "symbol": symbol,
                    "current_price": current_price,
                }
            )

        # Sort by efficiency (highest first)
        trade_candidates.sort(key=lambda x: x["efficiency"], reverse=True)

        # Execute trades in order of efficiency
        trades = []
        capital_used = 0.0
        total_cost = 0.0
        constraints_violated = []

        min_trade_size = next((c.value for c in constraints if c.constraint_type == "min_trade_size"), config.min_trade_size)

        for candidate in trade_candidates:
            need = candidate["need"]
            symbol = candidate["symbol"]
            current_price = candidate["current_price"]
            trade_value = candidate["trade_value"]

            if trade_value < min_trade_size:
                continue

            # Determine action
            current_value = current_portfolio.total_value * need.current_weight
            target_value = current_portfolio.total_value * need.target_weight
            net_trade_value = target_value - current_value

            if net_trade_value > 0:
                action = TradeAction.BUY
                required_capital = net_trade_value
            else:
                action = TradeAction.SELL
                required_capital = 0.0

            # Check capital constraint
            if required_capital > 0 and capital_used + required_capital > available_capital:
                constraints_violated.append(f"Insufficient capital for {symbol}")
                continue

            quantity = trade_value / current_price
            commission = trade_value * config.transaction_cost_rate
            spread_cost = trade_value * 0.001

            trade = TradeRecommendation(
                symbol=symbol,
                action=action,
                quantity=quantity,
                current_price=current_price,
                trade_value=trade_value,
                estimated_commission=commission,
                estimated_spread_cost=spread_cost,
                total_estimated_cost=commission + spread_cost,
                current_weight=need.current_weight,
                target_weight=need.target_weight,
                weight_deviation=need.deviation,
                projected_weight_after_trade=need.target_weight,
                priority=len(trades) + 1,
                urgency=self._calculate_urgency(need.urgency_score),
                rationale=f"Cost-efficient rebalancing of {symbol} (efficiency: {candidate['efficiency']:.2f})",
            )

            trades.append(trade)
            capital_used += required_capital
            total_cost += commission + spread_cost

        optimization_score = 1.0 - (total_cost / current_portfolio.total_value) if current_portfolio.total_value > 0 else 0.0

        return OptimizedTrades(
            trades=trades,
            total_cost=total_cost,
            capital_used=capital_used,
            constraints_violated=constraints_violated,
            optimization_score=optimization_score,
            method_used="MINIMIZE_COSTS",
        )

    def _calculate_urgency(self, urgency_score: float) -> UrgencyLevel:
        """Calculate urgency level from score."""
        if urgency_score >= 0.8:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 0.6:
            return UrgencyLevel.HIGH
        elif urgency_score >= 0.3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW


class RiskAwareStrategy(OptimizationStrategy):
    """Strategy that considers portfolio risk metrics in optimization."""

    def optimize(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        available_capital: float,
        constraints: list[OptimizationConstraint],
        config: PortfolioConfiguration,
    ) -> OptimizedTrades:
        """Optimize considering risk metrics."""
        logger.info("Optimizing trades using risk-aware strategy")

        # Calculate risk-adjusted priority for each trade
        risk_adjusted_needs = []

        for need in rebalancing_needs:
            if not need.exceeds_tolerance:
                continue

            # Calculate risk contribution (simplified)
            current_weight = need.current_weight
            target_weight = need.target_weight

            # Higher weight positions contribute more to concentration risk
            concentration_risk = max(current_weight, target_weight) ** 2

            # Risk-adjusted urgency (higher for positions that reduce concentration)
            risk_adjustment = 1.0
            if current_weight > 0.2:  # High concentration
                risk_adjustment = 1.5 if target_weight < current_weight else 0.8

            adjusted_urgency = need.urgency_score * risk_adjustment

            risk_adjusted_needs.append(
                {
                    "need": need,
                    "adjusted_urgency": adjusted_urgency,
                    "concentration_risk": concentration_risk,
                }
            )

        # Sort by risk-adjusted urgency
        risk_adjusted_needs.sort(key=lambda x: x["adjusted_urgency"], reverse=True)

        trades = []
        capital_used = 0.0
        total_cost = 0.0
        constraints_violated = []

        min_trade_size = next((c.value for c in constraints if c.constraint_type == "min_trade_size"), config.min_trade_size)
        max_position_weight = next((c.value for c in constraints if c.constraint_type == "max_position"), 0.25)

        for item in risk_adjusted_needs:
            need = item["need"]
            symbol = need.symbol
            current_price = prices.get(symbol, 0.0)

            if current_price <= 0:
                continue

            # Check position size constraint
            if need.target_weight > max_position_weight:
                constraints_violated.append(f"Target weight for {symbol} exceeds maximum position size")
                continue

            # Calculate trade
            current_value = current_portfolio.total_value * need.current_weight
            target_value = current_portfolio.total_value * need.target_weight
            trade_value = target_value - current_value

            if abs(trade_value) < min_trade_size:
                continue

            if trade_value > 0:
                action = TradeAction.BUY
                quantity = trade_value / current_price
                required_capital = trade_value
            else:
                action = TradeAction.SELL
                quantity = abs(trade_value) / current_price
                required_capital = 0.0

            # Check capital constraint
            if required_capital > 0 and capital_used + required_capital > available_capital:
                constraints_violated.append(f"Insufficient capital for {symbol}")
                continue

            commission = abs(trade_value) * config.transaction_cost_rate
            spread_cost = abs(trade_value) * 0.001

            trade = TradeRecommendation(
                symbol=symbol,
                action=action,
                quantity=quantity,
                current_price=current_price,
                trade_value=abs(trade_value),
                estimated_commission=commission,
                estimated_spread_cost=spread_cost,
                total_estimated_cost=commission + spread_cost,
                current_weight=need.current_weight,
                target_weight=need.target_weight,
                weight_deviation=need.deviation,
                projected_weight_after_trade=need.target_weight,
                priority=len(trades) + 1,
                urgency=self._calculate_urgency(item["adjusted_urgency"]),
                rationale=f"Risk-aware rebalancing of {symbol} (risk-adjusted urgency: {item['adjusted_urgency']:.2f})",
            )

            trades.append(trade)
            capital_used += required_capital
            total_cost += commission + spread_cost

        # Calculate risk-based optimization score
        optimization_score = self._calculate_risk_score(trades, current_portfolio)

        return OptimizedTrades(
            trades=trades,
            total_cost=total_cost,
            capital_used=capital_used,
            constraints_violated=constraints_violated,
            optimization_score=optimization_score,
            method_used="RISK_AWARE",
        )

    def _calculate_urgency(self, urgency_score: float) -> UrgencyLevel:
        """Calculate urgency level from score."""
        if urgency_score >= 0.8:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 0.6:
            return UrgencyLevel.HIGH
        elif urgency_score >= 0.3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _calculate_risk_score(self, trades: list[TradeRecommendation], portfolio: PortfolioAnalysis) -> float:
        """Calculate risk-based optimization score."""
        if not trades:
            return 0.0

        # Score based on risk reduction (simplified)
        # Higher score for trades that reduce concentration
        risk_reduction = 0.0
        for trade in trades:
            if trade.current_weight > 0.2 and trade.target_weight < trade.current_weight:
                risk_reduction += (trade.current_weight - trade.target_weight) * 10

        return min(risk_reduction, 1.0)


class RebalancingEngine:
    """Core optimization engine for portfolio rebalancing."""

    def __init__(self) -> None:
        """Initialize the rebalancing engine."""
        self.strategies = {
            RebalancingMethod.MINIMIZE_TRADES: MinimizeTradesStrategy(),
            RebalancingMethod.MINIMIZE_COSTS: MinimizeCostsStrategy(),
            RebalancingMethod.RISK_AWARE: RiskAwareStrategy(),
        }
        self.trade_recommendation_system = TradeRecommendationSystem()
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
        logger.info("Post-processing trades to minimize transaction costs")

        if not trades:
            return trades

        # Group trades by symbol to potentially combine them
        symbol_trades = {}
        for trade in trades:
            if trade.symbol not in symbol_trades:
                symbol_trades[trade.symbol] = []
            symbol_trades[trade.symbol].append(trade)

        optimized_trades = []

        for symbol, symbol_trade_list in symbol_trades.items():
            if len(symbol_trade_list) == 1:
                optimized_trades.append(symbol_trade_list[0])
                continue

            # Combine multiple trades for the same symbol
            net_quantity = 0.0
            total_cost = 0.0

            for trade in symbol_trade_list:
                if trade.action == TradeAction.BUY:
                    net_quantity += trade.quantity
                elif trade.action == TradeAction.SELL:
                    net_quantity -= trade.quantity
                total_cost += trade.total_estimated_cost

            if abs(net_quantity) > 0.01:  # Only create trade if significant quantity
                # Use the first trade as template
                template = symbol_trade_list[0]

                combined_trade = TradeRecommendation(
                    symbol=symbol,
                    action=TradeAction.BUY if net_quantity > 0 else TradeAction.SELL,
                    quantity=abs(net_quantity),
                    current_price=template.current_price,
                    trade_value=abs(net_quantity) * template.current_price,
                    estimated_commission=total_cost * 0.7,  # Reduced due to combining
                    estimated_spread_cost=total_cost * 0.3,
                    total_estimated_cost=total_cost * 0.8,  # 20% savings from combining
                    current_weight=template.current_weight,
                    target_weight=template.target_weight,
                    weight_deviation=template.weight_deviation,
                    projected_weight_after_trade=template.projected_weight_after_trade,
                    priority=template.priority,
                    urgency=template.urgency,
                    rationale=f"Combined {len(symbol_trade_list)} trades for {symbol}",
                )

                optimized_trades.append(combined_trade)

        logger.info(f"Cost optimization complete: {len(trades)} -> {len(optimized_trades)} trades")
        return optimized_trades

    def calculate_tax_implications(self, trades: list[TradeRecommendation], holdings: list[Holding]) -> dict[str, Any]:
        """
        Calculate tax implications of proposed trades.

        Args:
            trades: Proposed trade recommendations
            holdings: Current holdings with cost basis

        Returns:
            dict: Tax analysis results

        """
        logger.info("Calculating tax implications for trades")

        # Create lookup for cost basis
        cost_basis_lookup = {holding.symbol: holding.cost_basis for holding in holdings if holding.cost_basis}

        tax_analysis = {
            "total_realized_gains": 0.0,
            "total_realized_losses": 0.0,
            "short_term_gains": 0.0,
            "long_term_gains": 0.0,
            "tax_efficient_trades": [],
            "tax_inefficient_trades": [],
        }

        for trade in trades:
            if trade.action != TradeAction.SELL:
                continue

            cost_basis = cost_basis_lookup.get(trade.symbol)
            if not cost_basis:
                continue

            # Calculate realized gain/loss
            proceeds = trade.quantity * trade.current_price
            cost = trade.quantity * cost_basis
            realized_gain_loss = proceeds - cost

            if realized_gain_loss > 0:
                tax_analysis["total_realized_gains"] += realized_gain_loss
                # Assume long-term for simplicity (would need acquisition date for accuracy)
                tax_analysis["long_term_gains"] += realized_gain_loss

                if realized_gain_loss > 1000:  # Arbitrary threshold
                    tax_analysis["tax_inefficient_trades"].append(
                        {
                            "symbol": trade.symbol,
                            "gain": realized_gain_loss,
                            "recommendation": "Consider tax-loss harvesting opportunities",
                        }
                    )
                else:
                    tax_analysis["tax_efficient_trades"].append(trade.symbol)
            else:
                tax_analysis["total_realized_losses"] += abs(realized_gain_loss)
                tax_analysis["tax_efficient_trades"].append(trade.symbol)

        return tax_analysis

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
