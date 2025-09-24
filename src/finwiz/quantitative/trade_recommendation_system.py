"""
Trade recommendation system for portfolio rebalancing.

This module provides comprehensive trade recommendation generation with priority scoring,
quantity calculations, cost estimation, and validation logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from finwiz.quantitative.cost_analyzer import BrokerType, CostAnalyzer
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingNeed,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class TradeCalculationResult:
    """Result of trade quantity and cost calculations."""

    symbol: str
    action: TradeAction
    quantity: float
    fractional_quantity: float
    trade_value: float
    commission_cost: float
    spread_cost: float
    market_impact_cost: float
    total_cost: float
    is_valid: bool
    validation_errors: list[str]


@dataclass
class PriorityScore:
    """Priority scoring components for trade recommendations."""

    urgency_score: float  # 0.0 to 1.0
    deviation_score: float  # 0.0 to 1.0
    risk_score: float  # 0.0 to 1.0
    cost_efficiency_score: float  # 0.0 to 1.0
    overall_priority: float  # 0.0 to 1.0
    priority_rank: int  # 1 = highest priority


class TradeRecommendationSystem:
    """
    Comprehensive trade recommendation system for portfolio rebalancing.

    Handles priority scoring, quantity calculations, cost estimation,
    rationale generation, and trade validation.
    """

    def __init__(self, broker_type: BrokerType = BrokerType.DISCOUNT) -> None:
        """Initialize the trade recommendation system."""
        self.logger = logging.getLogger(__name__)
        self.cost_analyzer = CostAnalyzer(broker_type)
        self.logger.info(f"TradeRecommendationSystem initialized with {broker_type} broker")

    def generate_trade_recommendations(
        self,
        rebalancing_needs: list[RebalancingNeed],
        current_portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        prices: dict[str, float],
        config: PortfolioConfiguration,
        holdings: list[Holding],
    ) -> list[TradeRecommendation]:
        """
        Generate comprehensive trade recommendations with priority scoring.

        Args:
            rebalancing_needs: Positions requiring rebalancing
            current_portfolio: Current portfolio analysis
            target_weights: Target weight allocations
            prices: Current market prices
            config: Portfolio configuration
            holdings: Current holdings

        Returns:
            list[TradeRecommendation]: Prioritized trade recommendations

        """
        self.logger.info(f"Generating trade recommendations for {len(rebalancing_needs)} positions")

        # Filter to positions that exceed tolerance
        actionable_needs = [need for need in rebalancing_needs if need.exceeds_tolerance]

        if not actionable_needs:
            self.logger.info("No positions require rebalancing")
            return []

        # Calculate trade details for each position
        trade_calculations = []
        for need in actionable_needs:
            calculation = self._calculate_trade_details(need, current_portfolio, prices, config, holdings)
            if calculation.is_valid:
                trade_calculations.append(calculation)
            else:
                self.logger.warning(f"Invalid trade calculation for {need.symbol}: {calculation.validation_errors}")

        if not trade_calculations:
            self.logger.warning("No valid trade calculations generated")
            return []

        # Calculate priority scores
        priority_scores = self._calculate_priority_scores(trade_calculations, actionable_needs, current_portfolio, config)

        # Generate trade recommendations
        recommendations = []
        for i, (calculation, priority) in enumerate(zip(trade_calculations, priority_scores)):
            recommendation = self._create_trade_recommendation(calculation, priority, current_portfolio, target_weights, config)
            recommendations.append(recommendation)

        # Sort by priority (highest first)
        recommendations.sort(key=lambda x: x.priority)

        self.logger.info(f"Generated {len(recommendations)} trade recommendations")
        return recommendations

    def _calculate_trade_details(
        self,
        need: RebalancingNeed,
        portfolio: PortfolioAnalysis,
        prices: dict[str, float],
        config: PortfolioConfiguration,
        holdings: list[Holding],
    ) -> TradeCalculationResult:
        """Calculate detailed trade quantities and costs."""
        symbol = need.symbol
        current_price = prices.get(symbol, 0.0)
        validation_errors = []

        # Validate price data
        if current_price <= 0:
            validation_errors.append(f"Invalid or missing price for {symbol}")
            return TradeCalculationResult(
                symbol=symbol,
                action=TradeAction.HOLD,
                quantity=0.0,
                fractional_quantity=0.0,
                trade_value=0.0,
                commission_cost=0.0,
                spread_cost=0.0,
                market_impact_cost=0.0,
                total_cost=0.0,
                is_valid=False,
                validation_errors=validation_errors,
            )

        # Calculate trade value needed
        current_value = portfolio.total_value * need.current_weight
        target_value = portfolio.total_value * need.target_weight
        trade_value_needed = target_value - current_value

        # Determine action
        if abs(trade_value_needed) < config.min_trade_size:
            validation_errors.append(f"Trade value ${abs(trade_value_needed):.2f} below minimum ${config.min_trade_size}")
            action = TradeAction.HOLD
            quantity = 0.0
        elif trade_value_needed > 0:
            action = TradeAction.BUY
            quantity = trade_value_needed / current_price
        else:
            action = TradeAction.SELL
            quantity = abs(trade_value_needed) / current_price

        # Calculate fractional and whole share quantities
        fractional_quantity = quantity
        int(quantity)  # For brokers that don't support fractional shares

        # Use fractional shares if supported, otherwise whole shares
        final_quantity = fractional_quantity
        final_trade_value = abs(final_quantity * current_price)

        # Validate minimum trade size after quantity adjustment
        if final_trade_value < config.min_trade_size and action != TradeAction.HOLD:
            validation_errors.append(f"Final trade value ${final_trade_value:.2f} below minimum")

        # Calculate costs using CostAnalyzer
        commission_cost = self.cost_analyzer.calculate_commission_cost(final_trade_value, symbol, final_quantity)
        spread_estimate = self.cost_analyzer.estimate_bid_ask_spread(symbol, final_trade_value)
        spread_cost = spread_estimate.estimated_spread_cost
        impact_estimate = self.cost_analyzer.estimate_market_impact(symbol, final_trade_value, portfolio.total_value)
        market_impact_cost = impact_estimate.estimated_impact_cost
        total_cost = commission_cost + spread_cost + market_impact_cost

        # Validate against available capital for buy orders
        if action == TradeAction.BUY:
            required_capital = final_trade_value + total_cost
            if required_capital > config.available_capital and config.available_capital > 0:
                validation_errors.append(
                    f"Required capital ${required_capital:.2f} exceeds available ${config.available_capital:.2f}"
                )

        # Validate against current holdings for sell orders
        if action == TradeAction.SELL:
            current_holding = next((h for h in holdings if h.symbol == symbol), None)
            if current_holding and final_quantity > current_holding.shares:
                validation_errors.append(f"Cannot sell {final_quantity:.2f} shares, only {current_holding.shares:.2f} available")

        is_valid = len(validation_errors) == 0

        return TradeCalculationResult(
            symbol=symbol,
            action=action,
            quantity=final_quantity,
            fractional_quantity=fractional_quantity,
            trade_value=final_trade_value,
            commission_cost=commission_cost,
            spread_cost=spread_cost,
            market_impact_cost=market_impact_cost,
            total_cost=total_cost,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

    def _calculate_priority_scores(
        self,
        calculations: list[TradeCalculationResult],
        needs: list[RebalancingNeed],
        portfolio: PortfolioAnalysis,
        config: PortfolioConfiguration,
    ) -> list[PriorityScore]:
        """Calculate priority scores for trade recommendations."""
        priority_scores = []

        # Create lookup for needs by symbol
        needs_lookup = {need.symbol: need for need in needs}

        for calc in calculations:
            need = needs_lookup[calc.symbol]

            # Urgency score (from rebalancing need)
            urgency_score = need.urgency_score

            # Deviation score (higher deviation = higher priority)
            max_deviation = max(abs(n.deviation) for n in needs) if needs else 1.0
            deviation_score = abs(need.deviation) / max_deviation if max_deviation > 0 else 0.0

            # Risk score (positions with high concentration get higher priority)
            risk_score = min(need.current_weight * 5, 1.0)  # Scale current weight to 0-1

            # Cost efficiency score (benefit per dollar of cost)
            benefit = abs(need.deviation) * portfolio.total_value
            cost_efficiency_score = benefit / calc.total_cost if calc.total_cost > 0 else 1.0
            # Normalize to 0-1 scale
            cost_efficiency_score = min(cost_efficiency_score / 1000, 1.0)

            # Calculate overall priority (weighted average)
            overall_priority = urgency_score * 0.3 + deviation_score * 0.3 + risk_score * 0.2 + cost_efficiency_score * 0.2

            priority_scores.append(
                PriorityScore(
                    urgency_score=urgency_score,
                    deviation_score=deviation_score,
                    risk_score=risk_score,
                    cost_efficiency_score=cost_efficiency_score,
                    overall_priority=overall_priority,
                    priority_rank=0,  # Will be set after sorting
                )
            )

        # Sort by overall priority and assign ranks
        sorted_indices = sorted(range(len(priority_scores)), key=lambda i: priority_scores[i].overall_priority, reverse=True)

        for rank, idx in enumerate(sorted_indices, 1):
            priority_scores[idx].priority_rank = rank

        return priority_scores

    def _create_trade_recommendation(
        self,
        calculation: TradeCalculationResult,
        priority: PriorityScore,
        portfolio: PortfolioAnalysis,
        target_weights: dict[str, float],
        config: PortfolioConfiguration,
    ) -> TradeRecommendation:
        """Create a complete trade recommendation."""
        symbol = calculation.symbol
        current_weight = portfolio.weightings.get(symbol, 0.0)
        target_weight = target_weights.get(symbol, 0.0)
        weight_deviation = current_weight - target_weight

        # Calculate projected weight after trade
        if calculation.action == TradeAction.BUY:
            new_value = (portfolio.total_value * current_weight) + calculation.trade_value
            projected_weight = new_value / portfolio.total_value
        elif calculation.action == TradeAction.SELL:
            new_value = (portfolio.total_value * current_weight) - calculation.trade_value
            projected_weight = new_value / portfolio.total_value
        else:
            projected_weight = current_weight

        # Determine urgency level
        urgency = self._determine_urgency_level(priority.urgency_score)

        # Generate rationale
        rationale = self._generate_trade_rationale(symbol, calculation, current_weight, target_weight, priority)

        # Check for tax implications and market impact warnings
        tax_implications = self._assess_tax_implications(calculation, config)
        market_impact_warning = self._assess_market_impact_warning(calculation, portfolio)

        return TradeRecommendation(
            symbol=symbol,
            action=calculation.action,
            quantity=calculation.quantity,
            current_price=calculation.trade_value / calculation.quantity if calculation.quantity > 0 else 0.0,
            trade_value=calculation.trade_value,
            estimated_commission=calculation.commission_cost,
            estimated_spread_cost=calculation.spread_cost + calculation.market_impact_cost,  # Combine spread and market impact
            total_estimated_cost=calculation.total_cost,
            current_weight=current_weight,
            target_weight=target_weight,
            weight_deviation=weight_deviation,
            projected_weight_after_trade=projected_weight,
            priority=priority.priority_rank,
            urgency=urgency,
            rationale=rationale,
            tax_implications=tax_implications,
            market_impact_warning=market_impact_warning,
        )

    def _determine_urgency_level(self, urgency_score: float) -> UrgencyLevel:
        """Determine urgency level from numeric score."""
        if urgency_score >= 0.8:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 0.6:
            return UrgencyLevel.HIGH
        elif urgency_score >= 0.3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _generate_trade_rationale(
        self,
        symbol: str,
        calculation: TradeCalculationResult,
        current_weight: float,
        target_weight: float,
        priority: PriorityScore,
    ) -> str:
        """Generate detailed rationale for trade recommendation."""
        action_verb = "Buy" if calculation.action == TradeAction.BUY else "Sell"

        # Base rationale
        rationale = (
            f"{action_verb} {calculation.quantity:.2f} shares of {symbol} to rebalance "
            f"from {current_weight:.1%} to {target_weight:.1%} target allocation. "
        )

        # Add priority context
        if priority.urgency_score >= 0.7:
            rationale += "High urgency due to significant deviation from target. "
        elif priority.deviation_score >= 0.8:
            rationale += "Large deviation from target allocation requires attention. "

        # Add cost context
        cost_percentage = (calculation.total_cost / calculation.trade_value * 100) if calculation.trade_value > 0 else 0
        if cost_percentage > 2.0:
            rationale += f"Transaction costs are {cost_percentage:.1f}% of trade value. "
        elif cost_percentage < 0.5:
            rationale += "Low transaction costs make this trade cost-effective. "

        # Add risk context
        if priority.risk_score >= 0.6:
            rationale += "Helps reduce portfolio concentration risk. "

        return rationale.strip()

    def _assess_tax_implications(self, calculation: TradeCalculationResult, config: PortfolioConfiguration) -> str | None:
        """Assess potential tax implications of the trade."""
        if calculation.action != TradeAction.SELL:
            return None

        # For sell orders, note potential tax implications
        # In a full implementation, this would use cost basis and holding period
        if calculation.trade_value > 5000:
            return "Large sale may trigger significant capital gains tax. Consider tax-loss harvesting opportunities."
        elif calculation.trade_value > 1000:
            return "Moderate sale may have tax implications. Review cost basis and holding period."

        return None

    def _assess_market_impact_warning(self, calculation: TradeCalculationResult, portfolio: PortfolioAnalysis) -> str | None:
        """Assess potential market impact warnings."""
        trade_percentage = calculation.trade_value / portfolio.total_value if portfolio.total_value > 0 else 0

        if trade_percentage > 0.1:  # More than 10% of portfolio
            return "Large trade relative to portfolio size. Consider splitting into smaller orders."
        elif trade_percentage > 0.05:  # More than 5% of portfolio
            return "Moderate-sized trade. Monitor market conditions before execution."

        return None

    def validate_trade_recommendations(
        self, recommendations: list[TradeRecommendation], config: PortfolioConfiguration
    ) -> tuple[list[TradeRecommendation], list[str]]:
        """
        Validate trade recommendations to prevent invalid trades.

        Args:
            recommendations: List of trade recommendations to validate
            config: Portfolio configuration

        Returns:
            tuple: (valid_recommendations, validation_errors)

        """
        valid_recommendations = []
        validation_errors = []

        total_capital_required = 0.0

        for rec in recommendations:
            errors = []

            # Validate basic trade parameters
            if rec.quantity <= 0 and rec.action != TradeAction.HOLD:
                errors.append(f"{rec.symbol}: Invalid quantity {rec.quantity}")

            if rec.current_price <= 0:
                errors.append(f"{rec.symbol}: Invalid price {rec.current_price}")

            if rec.trade_value < 0:
                errors.append(f"{rec.symbol}: Invalid trade value {rec.trade_value}")

            # Validate weight constraints
            if not (0 <= rec.current_weight <= 1):
                errors.append(f"{rec.symbol}: Invalid current weight {rec.current_weight}")

            if not (0 <= rec.target_weight <= 1):
                errors.append(f"{rec.symbol}: Invalid target weight {rec.target_weight}")

            if not (0 <= rec.projected_weight_after_trade <= 1):
                errors.append(f"{rec.symbol}: Invalid projected weight {rec.projected_weight_after_trade}")

            # Validate cost calculations
            expected_total_cost = rec.estimated_commission + rec.estimated_spread_cost
            if abs(rec.total_estimated_cost - expected_total_cost) > 0.01:
                errors.append(f"{rec.symbol}: Cost calculation mismatch")

            # Check capital requirements
            if rec.action == TradeAction.BUY:
                required_capital = rec.trade_value + rec.total_estimated_cost
                total_capital_required += required_capital

                if total_capital_required > config.available_capital and config.available_capital > 0:
                    errors.append(f"{rec.symbol}: Insufficient capital for all buy orders")

            # Validate minimum trade size
            if rec.trade_value < config.min_trade_size and rec.action != TradeAction.HOLD:
                errors.append(f"{rec.symbol}: Trade value below minimum size")

            # Validate priority and urgency
            if not (1 <= rec.priority <= len(recommendations)):
                errors.append(f"{rec.symbol}: Invalid priority {rec.priority}")

            if rec.urgency not in UrgencyLevel:
                errors.append(f"{rec.symbol}: Invalid urgency level {rec.urgency}")

            if errors:
                validation_errors.extend([f"{rec.symbol}: {error}" for error in errors])
            else:
                valid_recommendations.append(rec)

        self.logger.info(
            f"Validation complete: {len(valid_recommendations)}/{len(recommendations)} valid, {len(validation_errors)} errors"
        )

        return valid_recommendations, validation_errors
