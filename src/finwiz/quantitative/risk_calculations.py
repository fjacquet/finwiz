"""
Risk calculation utilities for portfolio rebalancing.

This module provides core risk calculation functions including concentration,
turnover, volatility, and tax efficiency calculations.
"""

from __future__ import annotations

import logging
from datetime import datetime

from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingResult,
)

logger = logging.getLogger(__name__)


def calculate_concentration_risk(rebalancing_result: RebalancingResult) -> float:
    """
    Calculate concentration risk score.

    Uses Herfindahl-Hirschman Index (HHI) for concentration measurement.
    Higher HHI indicates higher concentration and higher risk.

    Args:
        rebalancing_result: Rebalancing analysis result

    Returns:
        Concentration risk score (0-10 scale)

    """
    weights = list(rebalancing_result.projected_portfolio.weightings.values())

    # Herfindahl-Hirschman Index for concentration
    hhi = sum(w**2 for w in weights)

    # Convert to risk score (0-10 scale)
    # HHI ranges from 1/n (perfectly diversified) to 1 (single asset)
    # Higher HHI = higher concentration = higher risk
    risk_score = min(hhi * 10, 10.0)

    return risk_score


def calculate_turnover_risk(rebalancing_result: RebalancingResult) -> float:
    """
    Calculate turnover risk score.

    Measures portfolio turnover as a percentage of total portfolio value.

    Args:
        rebalancing_result: Rebalancing analysis result

    Returns:
        Turnover risk score (0-10 scale)

    """
    total_trade_value = sum(abs(trade.trade_value) for trade in rebalancing_result.trade_recommendations)
    portfolio_value = rebalancing_result.current_portfolio.total_value
    turnover_ratio = total_trade_value / (2 * portfolio_value)

    # Convert to risk score (0-10 scale)
    risk_score = min(turnover_ratio * 20, 10.0)

    return risk_score


def calculate_volatility_risk(market_volatility: float) -> float:
    """
    Calculate volatility risk score.

    Normalizes market volatility to 0-10 scale:
    - 15% volatility = low risk (2)
    - 30% volatility = medium risk (5)
    - 50%+ volatility = high risk (8+)

    Args:
        market_volatility: Current market volatility (as decimal, e.g., 0.20 for 20%)

    Returns:
        Volatility risk score (0-10 scale)

    """
    if market_volatility <= 0.15:
        return 2.0
    elif market_volatility <= 0.30:
        return 2.0 + (market_volatility - 0.15) * 20  # Scale from 2 to 5
    else:
        return 5.0 + min((market_volatility - 0.30) * 15, 5.0)  # Scale from 5 to 10


def calculate_tax_efficiency_score(
    portfolio_config: PortfolioConfiguration,
    rebalancing_result: RebalancingResult,
    enable_tax_awareness: bool = True,
    short_term_threshold_days: int = 365,
) -> float:
    """
    Calculate tax efficiency score.

    Evaluates the tax impact of proposed trades, considering holding periods
    and capital gains/losses.

    Args:
        portfolio_config: Portfolio configuration
        rebalancing_result: Rebalancing analysis result
        enable_tax_awareness: Whether to consider tax implications
        short_term_threshold_days: Days threshold for short-term capital gains

    Returns:
        Tax efficiency score (0-10 scale, higher is better)

    """
    if not enable_tax_awareness:
        return 5.0  # Neutral score if tax awareness disabled

    total_tax_impact = 0.0
    total_trade_value = 0.0

    current_date = datetime.now()

    for trade in rebalancing_result.trade_recommendations:
        if trade.action.value == "SELL":
            holding = next((h for h in portfolio_config.holdings if h.symbol == trade.symbol), None)

            if holding and holding.cost_basis and holding.acquisition_date:
                cost_basis_total = holding.cost_basis * trade.quantity
                current_value = trade.current_price * trade.quantity
                gain_loss = current_value - cost_basis_total

                holding_days = (current_date - holding.acquisition_date).days
                is_short_term = holding_days < short_term_threshold_days

                # Penalize short-term gains, reward tax-loss harvesting
                if gain_loss > 0 and is_short_term:
                    total_tax_impact += gain_loss * 0.3  # Assume 30% short-term rate
                elif gain_loss > 0:
                    total_tax_impact += gain_loss * 0.15  # Assume 15% long-term rate
                else:
                    total_tax_impact += gain_loss * 0.25  # Tax benefit from losses

                total_trade_value += abs(current_value)

    if total_trade_value == 0:
        return 10.0  # Perfect score if no taxable trades

    # Calculate tax efficiency (higher is better)
    tax_rate = abs(total_tax_impact) / total_trade_value
    efficiency_score = max(10.0 - tax_rate * 50, 0.0)

    return efficiency_score
