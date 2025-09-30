"""
Calculation utilities for portfolio rebalancing reports.

This module contains calculation and analysis functions for portfolio
rebalancing operations, including risk calculations and cost analysis.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RebalancingCalculations:
    """Calculation utilities for rebalancing analysis."""

    @staticmethod
    def calculate_risk_improvement(current_risk: float, projected_risk: float) -> float:
        """
        Calculate risk improvement from rebalancing.

        Args:
            current_risk: Current portfolio risk score
            projected_risk: Projected portfolio risk score after rebalancing

        Returns:
            Risk improvement (positive = improvement, negative = deterioration)

        """
        return current_risk - projected_risk

    @staticmethod
    def calculate_deviation_severity(deviation: float) -> str:
        """
        Calculate deviation severity level.

        Args:
            deviation: Deviation from target allocation

        Returns:
            Severity level string

        """
        abs_deviation = abs(deviation)
        if abs_deviation > 0.05:
            return "high"
        elif abs_deviation > 0.02:
            return "medium"
        else:
            return "low"

    @staticmethod
    def calculate_total_transaction_costs(
        commission_costs: float,
        spread_costs: float,
        market_impact_costs: float,
    ) -> float:
        """
        Calculate total transaction costs.

        Args:
            commission_costs: Commission fees
            spread_costs: Bid-ask spread costs
            market_impact_costs: Market impact costs

        Returns:
            Total transaction costs

        """
        return commission_costs + spread_costs + market_impact_costs

    @staticmethod
    def calculate_cost_percentage(total_costs: float, portfolio_value: float) -> float:
        """
        Calculate costs as percentage of portfolio value.

        Args:
            total_costs: Total transaction costs
            portfolio_value: Total portfolio value

        Returns:
            Cost percentage

        """
        if portfolio_value <= 0:
            return 0.0
        return (total_costs / portfolio_value) * 100

    @staticmethod
    def calculate_break_even_days(
        total_costs: float,
        expected_daily_return_improvement: float,
        portfolio_value: float,
    ) -> int | None:
        """
        Calculate break-even days for rebalancing costs.

        Args:
            total_costs: Total transaction costs
            expected_daily_return_improvement: Expected daily return improvement
            portfolio_value: Total portfolio value

        Returns:
            Number of days to break even, or None if not applicable

        """
        if expected_daily_return_improvement <= 0 or portfolio_value <= 0:
            return None

        daily_improvement_value = (expected_daily_return_improvement / 100) * portfolio_value
        if daily_improvement_value <= 0:
            return None

        return int(total_costs / daily_improvement_value)

    @staticmethod
    def calculate_urgency_score(
        deviation: float,
        volatility: float,
        market_conditions: str = "normal",
    ) -> float:
        """
        Calculate urgency score for rebalancing action.

        Args:
            deviation: Deviation from target allocation
            volatility: Asset volatility
            market_conditions: Current market conditions

        Returns:
            Urgency score (0-10, higher = more urgent)

        """
        base_score = abs(deviation) * 10  # Base score from deviation

        # Adjust for volatility
        volatility_multiplier = 1 + (volatility / 100)
        score = base_score * volatility_multiplier

        # Adjust for market conditions
        market_multipliers = {
            "volatile": 1.5,
            "bearish": 1.3,
            "normal": 1.0,
            "bullish": 0.8,
            "stable": 0.7,
        }
        market_multiplier = market_multipliers.get(market_conditions.lower(), 1.0)
        score *= market_multiplier

        # Cap at 10
        return min(score, 10.0)

    @staticmethod
    def determine_action_priority(urgency_score: float) -> str:
        """
        Determine action priority based on urgency score.

        Args:
            urgency_score: Calculated urgency score

        Returns:
            Priority level string

        """
        if urgency_score >= 8.0:
            return "urgent"
        elif urgency_score >= 6.0:
            return "high"
        elif urgency_score >= 3.0:
            return "medium"
        else:
            return "low"

    @staticmethod
    def calculate_scenario_impact(
        base_costs: float,
        base_risk: float,
        scenario_parameters: dict[str, Any],
    ) -> dict[str, float]:
        """
        Calculate impact of alternative scenario parameters.

        Args:
            base_costs: Base scenario costs
            base_risk: Base scenario risk
            scenario_parameters: Modified parameters for scenario

        Returns:
            Dictionary with cost and risk differences

        """
        # This is a simplified calculation - in practice, this would involve
        # complex portfolio optimization algorithms
        cost_multiplier = 1.0
        risk_multiplier = 1.0

        # Adjust based on common scenario parameters
        if "tolerance" in scenario_parameters:
            tolerance = scenario_parameters["tolerance"]
            # Higher tolerance = fewer trades = lower costs but potentially higher risk
            cost_multiplier *= 1 - tolerance * 0.5
            risk_multiplier *= 1 + tolerance * 0.2

        if "transaction_cost_rate" in scenario_parameters:
            cost_rate = scenario_parameters["transaction_cost_rate"]
            cost_multiplier *= 1 + cost_rate

        if "rebalancing_method" in scenario_parameters:
            method = scenario_parameters["rebalancing_method"]
            if method == "threshold":
                cost_multiplier *= 0.8  # Fewer trades
                risk_multiplier *= 1.1  # Slightly higher risk
            elif method == "calendar":
                cost_multiplier *= 1.2  # More regular trades
                risk_multiplier *= 0.9  # Lower risk

        scenario_costs = base_costs * cost_multiplier
        scenario_risk = base_risk * risk_multiplier

        return {
            "cost_difference": scenario_costs - base_costs,
            "risk_difference": scenario_risk - base_risk,
            "cost_multiplier": cost_multiplier,
            "risk_multiplier": risk_multiplier,
        }

    @staticmethod
    def calculate_portfolio_metrics(
        weightings: dict[str, float],
        values: dict[str, float],
        target_weights: dict[str, float],
    ) -> dict[str, Any]:
        """
        Calculate comprehensive portfolio metrics.

        Args:
            weightings: Current portfolio weightings
            values: Portfolio position values
            target_weights: Target allocation weights

        Returns:
            Dictionary with calculated metrics

        """
        total_value = sum(values.values())

        # Calculate deviations
        deviations = {}
        for asset in weightings:
            current_weight = weightings[asset]
            target_weight = target_weights.get(asset, 0.0)
            deviations[asset] = current_weight - target_weight

        # Calculate summary statistics
        max_deviation = max(abs(d) for d in deviations.values()) if deviations else 0.0
        avg_deviation = sum(abs(d) for d in deviations.values()) / len(deviations) if deviations else 0.0

        # Count positions outside tolerance (assuming 2% tolerance)
        tolerance = 0.02
        positions_outside_tolerance = sum(1 for d in deviations.values() if abs(d) > tolerance)

        # Calculate concentration risk (Herfindahl index)
        concentration_index = sum(w**2 for w in weightings.values()) if weightings else 0.0

        return {
            "total_value": total_value,
            "deviations": deviations,
            "max_deviation": max_deviation,
            "avg_deviation": avg_deviation,
            "positions_outside_tolerance": positions_outside_tolerance,
            "concentration_index": concentration_index,
            "number_of_positions": len(weightings),
        }
