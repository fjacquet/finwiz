"""
Cost-benefit analysis utilities for portfolio rebalancing.

This module provides functions for analyzing transaction costs and performing
cost-benefit analysis to support rebalancing decisions.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from finwiz.schemas.portfolio_rebalancing import (
    PortfolioAnalysis,
    PortfolioConfiguration,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)


@dataclass
class CostBenefitAnalysis:
    """Cost-benefit analysis result."""

    total_rebalancing_cost: float
    expected_annual_benefit: float  # From improved allocation
    break_even_days: int | None  # Days to break even
    cost_as_percentage_of_portfolio: float
    recommendation: str  # PROCEED, DELAY, MODIFY, REJECT
    rationale: str
    alternative_approaches: list[str]


def calculate_total_commission_costs(
    trade_recommendations: list[TradeRecommendation],
    calculate_commission_fn: Callable[..., Any],
) -> float:
    """
    Calculate total commission costs for all trades.

    Args:
        trade_recommendations: List of trade recommendations
        calculate_commission_fn: Function to calculate commission for a single trade

    Returns:
        float: Total commission costs

    """
    total_commission = 0.0
    for trade in trade_recommendations:
        if trade.action.value in ["BUY", "SELL"]:
            commission = calculate_commission_fn(trade.trade_value, trade.symbol, trade.quantity)
            total_commission += commission
    return total_commission


def calculate_total_spread_costs(
    trade_recommendations: list[TradeRecommendation],
    estimate_spread_fn: Callable[..., Any],
    market_data: dict[str, Any] | None,
) -> float:
    """
    Calculate total spread costs for all trades.

    Args:
        trade_recommendations: List of trade recommendations
        estimate_spread_fn: Function to estimate spread for a single trade
        market_data: Optional market data

    Returns:
        float: Total spread costs

    """
    total_spread = 0.0
    for trade in trade_recommendations:
        if trade.action.value in ["BUY", "SELL"]:
            spread_estimate = estimate_spread_fn(trade.symbol, trade.trade_value, market_data)
            total_spread += spread_estimate.estimated_spread_cost
    return total_spread


def calculate_total_market_impact_costs(
    trade_recommendations: list[TradeRecommendation],
    portfolio: PortfolioAnalysis,
    estimate_impact_fn: Callable[..., Any],
    market_data: dict[str, Any] | None,
) -> float:
    """
    Calculate total market impact costs for all trades.

    Args:
        trade_recommendations: List of trade recommendations
        portfolio: Current portfolio analysis
        estimate_impact_fn: Function to estimate market impact for a single trade
        market_data: Optional market data

    Returns:
        float: Total market impact costs

    """
    total_impact = 0.0
    for trade in trade_recommendations:
        if trade.action.value in ["BUY", "SELL"]:
            impact_estimate = estimate_impact_fn(
                trade.symbol,
                trade.trade_value,
                portfolio.total_value,
                market_data,
            )
            total_impact += impact_estimate.estimated_impact_cost
    return total_impact


def calculate_break_even_days(
    total_costs: float,
    trade_recommendations: list[TradeRecommendation],
    portfolio: PortfolioAnalysis,
) -> int | None:
    """
    Calculate break-even period in days.

    Args:
        total_costs: Total transaction costs
        trade_recommendations: List of trade recommendations
        portfolio: Current portfolio analysis

    Returns:
        int | None: Break-even days or None if no benefit

    """
    # Estimate annual benefit from improved allocation
    annual_benefit = estimate_rebalancing_benefit(trade_recommendations, portfolio, None)

    if annual_benefit <= 0:
        return None

    # Calculate days to break even
    break_even_years = total_costs / annual_benefit
    return int(break_even_years * 365)


def estimate_rebalancing_benefit(
    trade_recommendations: list[TradeRecommendation],
    portfolio: PortfolioAnalysis,
    config: PortfolioConfiguration | None,
) -> float:
    """
    Estimate annual benefit from rebalancing.

    Args:
        trade_recommendations: List of trade recommendations
        portfolio: Current portfolio analysis
        config: Portfolio configuration (optional)

    Returns:
        float: Estimated annual benefit

    """
    # Simple heuristic: benefit is proportional to deviation reduction
    # In practice, this would use more sophisticated models

    total_deviation_reduction = 0.0
    for trade in trade_recommendations:
        current_deviation = abs(trade.weight_deviation)
        projected_deviation = abs(trade.projected_weight_after_trade - trade.target_weight)
        deviation_reduction = current_deviation - projected_deviation
        total_deviation_reduction += deviation_reduction

    # Estimate benefit as percentage of portfolio value
    # Assume 1% deviation costs 0.5% annually in opportunity cost
    benefit_rate = total_deviation_reduction * 0.5
    annual_benefit = portfolio.total_value * benefit_rate

    return max(annual_benefit, 0.0)


def perform_cost_benefit_analysis(
    total_costs: float,
    trade_recommendations: list[TradeRecommendation],
    portfolio: PortfolioAnalysis,
    config: PortfolioConfiguration,
) -> CostBenefitAnalysis:
    """
    Perform cost-benefit analysis comparing rebalancing costs to benefits.

    Args:
        total_costs: Total transaction costs
        trade_recommendations: List of trade recommendations
        portfolio: Current portfolio analysis
        config: Portfolio configuration

    Returns:
        CostBenefitAnalysis: Cost-benefit analysis result

    """
    # Calculate expected annual benefit from rebalancing
    expected_benefit = estimate_rebalancing_benefit(trade_recommendations, portfolio, config)

    # Calculate break-even period
    break_even_days = None
    if expected_benefit > 0:
        break_even_days = int((total_costs / expected_benefit) * 365)

    # Calculate cost as percentage of portfolio
    cost_percentage = (total_costs / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0

    # Generate recommendation
    recommendation, rationale = generate_cost_benefit_recommendation(
        total_costs,
        expected_benefit,
        cost_percentage,
        break_even_days,
    )

    # Generate alternative approaches
    alternatives = generate_alternative_approaches(total_costs, cost_percentage, trade_recommendations)

    logger.info(f"Cost-benefit analysis: ${total_costs:.2f} cost, ${expected_benefit:.2f} annual benefit, {break_even_days} days break-even")

    return CostBenefitAnalysis(
        total_rebalancing_cost=total_costs,
        expected_annual_benefit=expected_benefit,
        break_even_days=break_even_days,
        cost_as_percentage_of_portfolio=cost_percentage,
        recommendation=recommendation,
        rationale=rationale,
        alternative_approaches=alternatives,
    )


def generate_cost_benefit_recommendation(
    total_costs: float,
    expected_benefit: float,
    cost_percentage: float,
    break_even_days: int | None,
) -> tuple[str, str]:
    """
    Generate cost-benefit recommendation and rationale.

    Args:
        total_costs: Total transaction costs
        expected_benefit: Expected annual benefit
        cost_percentage: Cost as percentage of portfolio
        break_even_days: Days to break even

    Returns:
        tuple[str, str]: Recommendation and rationale

    """
    if cost_percentage > 2.0:
        recommendation = "REJECT"
        rationale = f"Transaction costs of {cost_percentage:.1f}% are excessive. Consider alternative rebalancing approaches or delay until larger deviations occur."
    elif break_even_days and break_even_days > 365:
        recommendation = "DELAY"
        rationale = f"Break-even period of {break_even_days} days is too long. Consider waiting for larger deviations or using new contributions to rebalance."
    elif cost_percentage > 1.0:
        recommendation = "MODIFY"
        rationale = f"Transaction costs of {cost_percentage:.1f}% are moderate. Consider rebalancing only the most deviated positions or using gradual rebalancing."
    else:
        recommendation = "PROCEED"
        rationale = f"Transaction costs of {cost_percentage:.1f}% are reasonable. Expected to break even in {break_even_days or 'N/A'} days."

    return recommendation, rationale


def generate_alternative_approaches(
    total_costs: float,
    cost_percentage: float,
    trade_recommendations: list[TradeRecommendation],
) -> list[str]:
    """
    Generate alternative rebalancing approaches.

    Args:
        total_costs: Total transaction costs
        cost_percentage: Cost as percentage of portfolio
        trade_recommendations: List of trade recommendations

    Returns:
        list[str]: Alternative approaches

    """
    alternatives = []

    if cost_percentage > 1.0:
        alternatives.append("Use new contributions to gradually rebalance over time")
        alternatives.append("Rebalance only positions with highest deviations")
        alternatives.append("Wait for larger deviations before rebalancing")

    if len(trade_recommendations) > 5:
        alternatives.append("Split rebalancing into multiple sessions")
        alternatives.append("Use algorithmic execution to reduce market impact")

    high_impact_trades = [t for t in trade_recommendations if t.trade_value > 10000]  # Trades over $10k
    if high_impact_trades:
        alternatives.append("Execute large trades using TWAP or VWAP strategies")
        alternatives.append("Consider using ETFs for broad market exposure instead of individual stocks")

    return alternatives
