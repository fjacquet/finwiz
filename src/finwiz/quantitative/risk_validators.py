"""
Risk validation and warning generation for portfolio rebalancing.

This module provides methods for checking various risk conditions and
generating appropriate warnings.
"""

from __future__ import annotations

from datetime import datetime

from finwiz.quantitative.risk_metrics import (
    RiskLevel,
    RiskWarning,
    RiskWarningType,
)
from finwiz.schemas.portfolio_rebalancing import (
    PortfolioConfiguration,
    RebalancingResult,
)


def check_concentration_limits(
    portfolio_config: PortfolioConfiguration,
    rebalancing_result: RebalancingResult,
    max_single_position: float,
    max_top_5_positions: float,
    min_number_positions: int,
) -> list[RiskWarning]:
    """Check for concentration limit violations."""
    warnings: list[RiskWarning] = []

    # Check projected weights after rebalancing
    projected_weights = rebalancing_result.projected_portfolio.weightings

    # Check single position limits
    for symbol, weight in projected_weights.items():
        if weight > max_single_position:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.CONCENTRATION,
                    risk_level=RiskLevel.HIGH if weight > 0.30 else RiskLevel.MEDIUM,
                    symbol=symbol,
                    message=f"Position {symbol} would represent {weight:.1%} of portfolio, exceeding {max_single_position:.1%} limit",
                    recommendation=f"Consider reducing target weight for {symbol} or increasing portfolio diversification",
                    impact_score=min(weight * 20, 10.0),
                )
            )

    # Check top 5 positions concentration
    sorted_weights = sorted(projected_weights.values(), reverse=True)
    top_5_weight = sum(sorted_weights[:5])
    if top_5_weight > max_top_5_positions:
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.CONCENTRATION,
                risk_level=RiskLevel.MEDIUM,
                symbol=None,
                message=f"Top 5 positions would represent {top_5_weight:.1%} of portfolio, exceeding {max_top_5_positions:.1%} limit",
                recommendation="Consider increasing diversification across more positions",
                impact_score=min((top_5_weight - 0.6) * 25, 10.0),
            )
        )

    # Check minimum number of positions
    num_positions = len([w for w in projected_weights.values() if w > 0.01])
    if num_positions < min_number_positions:
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.CONCENTRATION,
                risk_level=RiskLevel.HIGH,
                symbol=None,
                message=f"Portfolio has only {num_positions} significant positions, below minimum of {min_number_positions}",
                recommendation="Consider adding more positions to improve diversification",
                impact_score=8.0,
            )
        )

    return warnings


def check_turnover_limits(
    rebalancing_result: RebalancingResult,
    max_monthly_turnover: float,
    warning_threshold: float,
) -> list[RiskWarning]:
    """Check for excessive portfolio turnover."""
    warnings: list[RiskWarning] = []

    # Calculate turnover from trade recommendations
    total_trade_value = sum(abs(trade.trade_value) for trade in rebalancing_result.trade_recommendations)
    portfolio_value = rebalancing_result.current_portfolio.total_value
    turnover_ratio = total_trade_value / (2 * portfolio_value)  # Divide by 2 for one-way turnover

    # Check against limits
    if turnover_ratio > max_monthly_turnover:
        risk_level = RiskLevel.HIGH if turnover_ratio > 0.5 else RiskLevel.MEDIUM
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.TURNOVER,
                risk_level=risk_level,
                symbol=None,
                message=f"Rebalancing would result in {turnover_ratio:.1%} portfolio turnover, exceeding {max_monthly_turnover:.1%} monthly limit",
                recommendation="Consider phased rebalancing over multiple periods or increasing tolerance bands to reduce turnover",
                impact_score=min(turnover_ratio * 20, 10.0),
            )
        )
    elif turnover_ratio > warning_threshold:
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.TURNOVER,
                risk_level=RiskLevel.LOW,
                symbol=None,
                message=f"Rebalancing would result in {turnover_ratio:.1%} portfolio turnover, above {warning_threshold:.1%} warning threshold",
                recommendation="Monitor turnover frequency to avoid excessive trading costs",
                impact_score=turnover_ratio * 10,
            )
        )

    return warnings


def check_volatility_risks(
    market_volatility: float,
    high_volatility_threshold: float,
    extreme_volatility_threshold: float,
) -> list[RiskWarning]:
    """Check volatility-based rebalancing risks."""
    warnings: list[RiskWarning] = []

    if market_volatility > extreme_volatility_threshold:
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.VOLATILITY,
                risk_level=RiskLevel.CRITICAL,
                symbol=None,
                message=f"Market volatility is extremely high at {market_volatility:.1%}, above {extreme_volatility_threshold:.1%} threshold",
                recommendation="Consider delaying rebalancing until volatility subsides or using wider tolerance bands to avoid whipsaw trading",
                impact_score=9.0,
            )
        )
    elif market_volatility > high_volatility_threshold:
        warnings.append(
            RiskWarning(
                warning_type=RiskWarningType.VOLATILITY,
                risk_level=RiskLevel.HIGH,
                symbol=None,
                message=f"Market volatility is high at {market_volatility:.1%}, above {high_volatility_threshold:.1%} threshold",
                recommendation="Consider using wider tolerance bands or phased rebalancing to reduce timing risk",
                impact_score=6.0,
            )
        )

    return warnings


def check_tax_implications(
    portfolio_config: PortfolioConfiguration,
    rebalancing_result: RebalancingResult,
    enable_tax_awareness: bool,
    short_term_threshold_days: int,
    minimum_loss_threshold: float,
) -> list[RiskWarning]:
    """Check for significant tax implications."""
    warnings: list[RiskWarning] = []

    if not enable_tax_awareness:
        return warnings

    current_date = datetime.now()

    for trade in rebalancing_result.trade_recommendations:
        if trade.action.value == "SELL":
            # Find corresponding holding
            holding = next((h for h in portfolio_config.holdings if h.symbol == trade.symbol), None)

            if holding and holding.cost_basis and holding.acquisition_date:
                # Calculate potential gain/loss
                cost_basis_total = holding.cost_basis * trade.quantity
                current_value = trade.current_price * trade.quantity
                gain_loss = current_value - cost_basis_total

                # Check holding period
                holding_days = (current_date - holding.acquisition_date).days
                is_short_term = holding_days < short_term_threshold_days

                if gain_loss > 0 and is_short_term:
                    warnings.append(
                        RiskWarning(
                            warning_type=RiskWarningType.TAX_IMPLICATIONS,
                            risk_level=RiskLevel.MEDIUM,
                            symbol=trade.symbol,
                            message=f"Selling {trade.symbol} would trigger short-term capital gains of ${gain_loss:,.2f} (held {holding_days} days)",
                            recommendation="Consider waiting until long-term holding period or using tax-loss harvesting opportunities",
                            impact_score=min(gain_loss / 1000, 8.0),
                        )
                    )
                elif gain_loss < -minimum_loss_threshold * cost_basis_total:
                    # Tax-loss harvesting opportunity
                    warnings.append(
                        RiskWarning(
                            warning_type=RiskWarningType.TAX_IMPLICATIONS,
                            risk_level=RiskLevel.LOW,
                            symbol=trade.symbol,
                            message=f"Selling {trade.symbol} would realize tax loss of ${abs(gain_loss):,.2f}",
                            recommendation="Consider tax-loss harvesting benefits and wash sale rule implications",
                            impact_score=2.0,
                        )
                    )

    return warnings


def check_position_size_warnings(
    rebalancing_result: RebalancingResult,
    enable_position_size_warnings: bool,
    enable_market_impact_warnings: bool,
) -> list[RiskWarning]:
    """Check for position size and market impact warnings."""
    warnings: list[RiskWarning] = []

    if not enable_position_size_warnings:
        return warnings

    portfolio_value = rebalancing_result.current_portfolio.total_value

    for trade in rebalancing_result.trade_recommendations:
        trade_percentage = abs(trade.trade_value) / portfolio_value

        # Large trade warning
        if trade_percentage > 0.10:  # 10% of portfolio
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.POSITION_SIZE,
                    risk_level=RiskLevel.MEDIUM,
                    symbol=trade.symbol,
                    message=f"Trade in {trade.symbol} represents {trade_percentage:.1%} of total portfolio value (${trade.trade_value:,.2f})",
                    recommendation="Consider splitting large trades across multiple periods to reduce market impact",
                    impact_score=min(trade_percentage * 50, 8.0),
                )
            )

        # Market impact warning for large trades
        if enable_market_impact_warnings and abs(trade.quantity) > 1000:
            warnings.append(
                RiskWarning(
                    warning_type=RiskWarningType.MARKET_IMPACT,
                    risk_level=RiskLevel.LOW,
                    symbol=trade.symbol,
                    message=f"Large quantity trade in {trade.symbol} ({trade.quantity:,.0f} shares) may have market impact",
                    recommendation="Consider using limit orders or splitting into smaller blocks",
                    impact_score=3.0,
                )
            )

    return warnings
