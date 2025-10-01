"""
Trade generation and post-processing utilities for portfolio rebalancing.

This module handles the generation, optimization, and validation of trade recommendations
including cost minimization and tax implications analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    TradeAction,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)


class TradeGenerator:
    """Handles trade generation and post-processing operations."""

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
