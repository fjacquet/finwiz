"""
Transaction cost analysis module for portfolio rebalancing.

This module provides comprehensive transaction cost modeling including commission
calculation, bid-ask spread estimation, market impact modeling, and cost-benefit
analysis for rebalancing decisions.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.quantitative.cost_analysis import (
    CostBenefitAnalysis,
    calculate_break_even_days,
    calculate_total_commission_costs,
    calculate_total_market_impact_costs,
    calculate_total_spread_costs,
    perform_cost_benefit_analysis,
)
from finwiz.quantitative.cost_calculators import (
    BrokerFeeStructure,
    BrokerType,
    MarketCapCategory,
    MarketImpactEstimate,
    SpreadEstimate,
    calculate_commission_cost,
    estimate_bid_ask_spread,
    estimate_market_impact,
    get_broker_fee_structure,
)
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    PortfolioAnalysis,
    PortfolioConfiguration,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
__all__ = [
    "BrokerType",
    "MarketCapCategory",
    "BrokerFeeStructure",
    "SpreadEstimate",
    "MarketImpactEstimate",
    "CostBenefitAnalysis",
    "CostAnalyzer",
]


class CostAnalyzer:
    """
    Comprehensive transaction cost analyzer for portfolio rebalancing.

    Provides detailed cost modeling including commissions, spreads, market impact,
    and cost-benefit analysis to support rebalancing decisions.
    """

    def __init__(self, broker_type: BrokerType = BrokerType.DISCOUNT) -> None:
        """
        Initialize the cost analyzer.

        Args:
            broker_type: Type of broker for fee structure

        """
        self.logger = logging.getLogger(__name__)
        self.broker_type = broker_type
        self.fee_structure = get_broker_fee_structure(broker_type)
        self.logger.info(f"CostAnalyzer initialized with {broker_type} broker type")

    def analyze_transaction_costs(
        self,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
        config: PortfolioConfiguration,
        market_data: dict[str, Any] | None = None,
    ) -> CostAnalysis:
        """
        Perform comprehensive transaction cost analysis.

        Args:
            trade_recommendations: List of recommended trades
            portfolio: Current portfolio analysis
            config: Portfolio configuration
            market_data: Optional market data for enhanced analysis

        Returns:
            CostAnalysis: Comprehensive cost analysis result

        """
        self.logger.info(f"Analyzing transaction costs for {len(trade_recommendations)} trades")

        if not trade_recommendations:
            return CostAnalysis(
                total_transaction_costs=0.0,
                commission_costs=0.0,
                spread_costs=0.0,
                market_impact_costs=0.0,
                cost_as_percentage=0.0,
                break_even_days=None,
            )

        # Calculate individual cost components
        total_commission = calculate_total_commission_costs(
            trade_recommendations,
            self.calculate_commission_cost,
        )
        total_spread = calculate_total_spread_costs(
            trade_recommendations,
            self.estimate_bid_ask_spread,
            market_data,
        )
        total_market_impact = calculate_total_market_impact_costs(
            trade_recommendations,
            portfolio,
            self.estimate_market_impact,
            market_data,
        )

        total_costs = total_commission + total_spread + total_market_impact
        cost_percentage = (total_costs / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0

        # Calculate break-even analysis
        break_even_days = calculate_break_even_days(total_costs, trade_recommendations, portfolio)

        self.logger.info(f"Total transaction costs: ${total_costs:.2f} ({cost_percentage:.2f}% of portfolio)")

        return CostAnalysis(
            total_transaction_costs=total_costs,
            commission_costs=total_commission,
            spread_costs=total_spread,
            market_impact_costs=total_market_impact,
            cost_as_percentage=cost_percentage,
            break_even_days=break_even_days,
        )

    def calculate_commission_cost(self, trade_value: float, symbol: str, share_count: float) -> float:
        """
        Calculate commission cost based on broker fee structure.

        Args:
            trade_value: Total value of the trade
            symbol: Stock symbol
            share_count: Number of shares

        Returns:
            float: Commission cost

        """
        return calculate_commission_cost(self.fee_structure, trade_value, symbol, share_count)

    def estimate_bid_ask_spread(
        self,
        symbol: str,
        trade_value: float,
        market_data: dict[str, Any] | None = None,
    ) -> SpreadEstimate:
        """
        Estimate bid-ask spread cost using market data and heuristics.

        Args:
            symbol: Stock symbol
            trade_value: Value of the trade
            market_data: Optional market data

        Returns:
            SpreadEstimate: Spread estimation result

        """
        return estimate_bid_ask_spread(symbol, trade_value, market_data)

    def estimate_market_impact(
        self,
        symbol: str,
        trade_value: float,
        portfolio_value: float,
        market_data: dict[str, Any] | None = None,
    ) -> MarketImpactEstimate:
        """
        Estimate market impact cost for large trades.

        Args:
            symbol: Stock symbol
            trade_value: Value of the trade
            portfolio_value: Total portfolio value
            market_data: Optional market data

        Returns:
            MarketImpactEstimate: Market impact estimation result

        """
        return estimate_market_impact(symbol, trade_value, portfolio_value, market_data)

    def perform_cost_benefit_analysis(
        self,
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
        return perform_cost_benefit_analysis(total_costs, trade_recommendations, portfolio, config)

    # Private helper methods for backward compatibility
    def _get_broker_fee_structure(self, broker_type: BrokerType) -> BrokerFeeStructure:
        """Get fee structure for broker type."""
        return get_broker_fee_structure(broker_type)

    def _calculate_total_commission_costs(self, trade_recommendations: list[TradeRecommendation]) -> float:
        """Calculate total commission costs for all trades."""
        return calculate_total_commission_costs(trade_recommendations, self.calculate_commission_cost)

    def _calculate_total_spread_costs(
        self,
        trade_recommendations: list[TradeRecommendation],
        market_data: dict[str, Any] | None,
    ) -> float:
        """Calculate total spread costs for all trades."""
        return calculate_total_spread_costs(trade_recommendations, self.estimate_bid_ask_spread, market_data)

    def _calculate_total_market_impact_costs(
        self,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
        market_data: dict[str, Any] | None,
    ) -> float:
        """Calculate total market impact costs for all trades."""
        return calculate_total_market_impact_costs(
            trade_recommendations,
            portfolio,
            self.estimate_market_impact,
            market_data,
        )

    def _calculate_break_even_days(
        self,
        total_costs: float,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
    ) -> int | None:
        """Calculate break-even period in days."""
        return calculate_break_even_days(total_costs, trade_recommendations, portfolio)

    def _estimate_rebalancing_benefit(
        self,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
        config: PortfolioConfiguration | None,
    ) -> float:
        """Estimate annual benefit from rebalancing."""
        from finwiz.quantitative.cost_analysis import estimate_rebalancing_benefit

        return estimate_rebalancing_benefit(trade_recommendations, portfolio, config)

    def _generate_cost_benefit_recommendation(
        self,
        total_costs: float,
        expected_benefit: float,
        cost_percentage: float,
        break_even_days: int | None,
    ) -> tuple[str, str]:
        """Generate cost-benefit recommendation and rationale."""
        from finwiz.quantitative.cost_analysis import generate_cost_benefit_recommendation

        return generate_cost_benefit_recommendation(total_costs, expected_benefit, cost_percentage, break_even_days)

    def _generate_alternative_approaches(
        self,
        total_costs: float,
        cost_percentage: float,
        trade_recommendations: list[TradeRecommendation],
    ) -> list[str]:
        """Generate alternative rebalancing approaches."""
        from finwiz.quantitative.cost_analysis import generate_alternative_approaches

        return generate_alternative_approaches(total_costs, cost_percentage, trade_recommendations)

    def _is_etf(self, symbol: str) -> bool:
        """Check if symbol is likely an ETF."""
        from finwiz.quantitative.cost_calculators import is_etf

        return is_etf(symbol)

    def _is_foreign_stock(self, symbol: str) -> bool:
        """Check if symbol is a foreign stock."""
        from finwiz.quantitative.cost_calculators import is_foreign_stock

        return is_foreign_stock(symbol)

    def _is_large_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is large cap."""
        from finwiz.quantitative.cost_calculators import is_large_cap

        return is_large_cap(symbol, market_data)

    def _is_mid_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is mid cap."""
        from finwiz.quantitative.cost_calculators import is_mid_cap

        return is_mid_cap(symbol, market_data)

    def _is_small_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is small cap."""
        from finwiz.quantitative.cost_calculators import is_small_cap

        return is_small_cap(symbol, market_data)

    def _estimate_avg_daily_volume_value(self, symbol: str, market_data: dict[str, Any] | None) -> float:
        """Estimate average daily volume value."""
        from finwiz.quantitative.cost_calculators import estimate_avg_daily_volume_value

        return estimate_avg_daily_volume_value(symbol, market_data)
