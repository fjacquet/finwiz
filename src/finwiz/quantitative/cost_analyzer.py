"""
Transaction cost analysis module for portfolio rebalancing.

This module provides comprehensive transaction cost modeling including commission
calculation, bid-ask spread estimation, market impact modeling, and cost-benefit
analysis for rebalancing decisions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    PortfolioAnalysis,
    PortfolioConfiguration,
    TradeRecommendation,
)

logger = logging.getLogger(__name__)


class BrokerType(str, Enum):
    """Broker fee structure types."""

    DISCOUNT = "DISCOUNT"  # Low-cost brokers (e.g., Schwab, Fidelity)
    FULL_SERVICE = "FULL_SERVICE"  # Traditional brokers with higher fees
    ROBO_ADVISOR = "ROBO_ADVISOR"  # Automated platforms
    COMMISSION_FREE = "COMMISSION_FREE"  # Zero-commission brokers


class MarketCapCategory(str, Enum):
    """Market capitalization categories for spread estimation."""

    LARGE_CAP = "LARGE_CAP"  # > $10B
    MID_CAP = "MID_CAP"  # $2B - $10B
    SMALL_CAP = "SMALL_CAP"  # $300M - $2B
    MICRO_CAP = "MICRO_CAP"  # < $300M


@dataclass
class BrokerFeeStructure:
    """Broker fee structure configuration."""

    broker_type: BrokerType
    base_commission: float  # Fixed commission per trade
    per_share_fee: float  # Fee per share (if applicable)
    percentage_fee: float  # Percentage of trade value
    minimum_commission: float  # Minimum commission per trade
    maximum_commission: float  # Maximum commission per trade
    options_fee: float  # Fee for options trades
    foreign_stock_fee: float  # Additional fee for foreign stocks
    regulatory_fees: float  # SEC/FINRA fees (typically 0.0000221 * trade_value)


@dataclass
class SpreadEstimate:
    """Bid-ask spread estimation result."""

    symbol: str
    estimated_spread_bps: float  # Spread in basis points
    estimated_spread_percentage: float  # Spread as percentage
    estimated_spread_cost: float  # Cost for the specific trade
    confidence_level: str  # HIGH, MEDIUM, LOW
    factors_considered: list[str]  # Factors used in estimation


@dataclass
class MarketImpactEstimate:
    """Market impact estimation result."""

    symbol: str
    trade_size_percentage: float  # Trade size as % of average daily volume
    estimated_impact_bps: float  # Impact in basis points
    estimated_impact_cost: float  # Cost for the specific trade
    impact_category: str  # NEGLIGIBLE, LOW, MODERATE, HIGH, SEVERE
    mitigation_suggestions: list[str]  # Suggestions to reduce impact


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
        self.fee_structure = self._get_broker_fee_structure(broker_type)
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
        total_commission = self._calculate_total_commission_costs(trade_recommendations)
        total_spread = self._calculate_total_spread_costs(trade_recommendations, market_data)
        total_market_impact = self._calculate_total_market_impact_costs(trade_recommendations, portfolio, market_data)

        total_costs = total_commission + total_spread + total_market_impact
        cost_percentage = (total_costs / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0

        # Calculate break-even analysis
        break_even_days = self._calculate_break_even_days(total_costs, trade_recommendations, portfolio)

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
        fee_structure = self.fee_structure

        # Calculate base commission components
        base_commission = fee_structure.base_commission
        per_share_cost = share_count * fee_structure.per_share_fee
        percentage_cost = trade_value * fee_structure.percentage_fee

        # Sum all components
        total_commission = base_commission + per_share_cost + percentage_cost

        # Apply minimum and maximum limits
        total_commission = max(total_commission, fee_structure.minimum_commission)
        total_commission = min(total_commission, fee_structure.maximum_commission)

        # Add regulatory fees (SEC/FINRA)
        regulatory_fees = trade_value * fee_structure.regulatory_fees
        total_commission += regulatory_fees

        # Add foreign stock fees if applicable
        if self._is_foreign_stock(symbol):
            total_commission += fee_structure.foreign_stock_fee

        self.logger.debug(f"Commission for {symbol}: ${total_commission:.2f}")
        return total_commission

    def estimate_bid_ask_spread(self, symbol: str, trade_value: float, market_data: dict[str, Any] | None = None) -> SpreadEstimate:
        """
        Estimate bid-ask spread cost using market data and heuristics.

        Args:
            symbol: Stock symbol
            trade_value: Value of the trade
            market_data: Optional market data

        Returns:
            SpreadEstimate: Spread estimation result

        """
        factors_considered = []

        # Default spread estimates based on symbol characteristics
        if self._is_etf(symbol):
            # ETFs typically have tighter spreads
            base_spread_bps = 2.0  # 2 basis points
            factors_considered.append("ETF classification")
        elif self._is_large_cap(symbol, market_data):
            # Large cap stocks have tight spreads
            base_spread_bps = 3.0  # 3 basis points
            factors_considered.append("Large cap classification")
        elif self._is_mid_cap(symbol, market_data):
            # Mid cap stocks have moderate spreads
            base_spread_bps = 8.0  # 8 basis points
            factors_considered.append("Mid cap classification")
        else:
            # Small/micro cap stocks have wider spreads
            base_spread_bps = 15.0  # 15 basis points
            factors_considered.append("Small/micro cap classification")

        # Adjust for market conditions if data available
        if market_data and symbol in market_data:
            symbol_data = market_data[symbol]

            # Adjust for volatility
            if "volatility" in symbol_data:
                volatility = symbol_data["volatility"]
                if volatility > 0.3:  # High volatility
                    base_spread_bps *= 1.5
                    factors_considered.append("High volatility adjustment")
                elif volatility < 0.15:  # Low volatility
                    base_spread_bps *= 0.8
                    factors_considered.append("Low volatility adjustment")

            # Adjust for volume
            if "avg_daily_volume" in symbol_data:
                volume = symbol_data["avg_daily_volume"]
                if volume > 1_000_000:  # High volume
                    base_spread_bps *= 0.8
                    factors_considered.append("High volume adjustment")
                elif volume < 100_000:  # Low volume
                    base_spread_bps *= 1.3
                    factors_considered.append("Low volume adjustment")

        # Convert to percentage and calculate cost
        spread_percentage = base_spread_bps / 10000  # Convert basis points to percentage
        spread_cost = trade_value * spread_percentage

        # Determine confidence level
        confidence = "HIGH" if market_data and symbol in market_data else "MEDIUM"
        if not factors_considered:
            confidence = "LOW"

        self.logger.debug(f"Spread estimate for {symbol}: {base_spread_bps:.1f} bps, cost: ${spread_cost:.2f}")

        return SpreadEstimate(
            symbol=symbol,
            estimated_spread_bps=base_spread_bps,
            estimated_spread_percentage=spread_percentage,
            estimated_spread_cost=spread_cost,
            confidence_level=confidence,
            factors_considered=factors_considered,
        )

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
        # Calculate trade size as percentage of average daily volume
        avg_daily_volume_value = self._estimate_avg_daily_volume_value(symbol, market_data)
        trade_size_percentage = (trade_value / avg_daily_volume_value * 100) if avg_daily_volume_value > 0 else 0.0

        # Estimate impact based on trade size
        if trade_size_percentage < 0.1:  # < 0.1% of daily volume
            impact_bps = 0.0
            impact_category = "NEGLIGIBLE"
            mitigation_suggestions = []
        elif trade_size_percentage < 0.5:  # 0.1-0.5% of daily volume
            impact_bps = 1.0
            impact_category = "LOW"
            mitigation_suggestions = ["Consider timing execution during high volume periods"]
        elif trade_size_percentage < 2.0:  # 0.5-2% of daily volume
            impact_bps = 3.0
            impact_category = "MODERATE"
            mitigation_suggestions = [
                "Consider splitting into smaller orders",
                "Use limit orders to control execution price",
            ]
        elif trade_size_percentage < 5.0:  # 2-5% of daily volume
            impact_bps = 8.0
            impact_category = "HIGH"
            mitigation_suggestions = [
                "Split into multiple smaller orders over time",
                "Use TWAP (Time-Weighted Average Price) strategy",
                "Consider executing during high volume periods",
            ]
        else:  # > 5% of daily volume
            impact_bps = 20.0
            impact_category = "SEVERE"
            mitigation_suggestions = [
                "Strongly consider splitting into multiple sessions",
                "Use algorithmic execution strategies",
                "Consider alternative rebalancing approaches",
                "Evaluate if rebalancing is necessary at this time",
            ]

        # Adjust for market cap and liquidity
        if self._is_large_cap(symbol, market_data):
            impact_bps *= 0.7  # Large caps have better liquidity
        elif self._is_small_cap(symbol, market_data):
            impact_bps *= 1.5  # Small caps have worse liquidity

        # Calculate impact cost
        impact_percentage = impact_bps / 10000
        impact_cost = trade_value * impact_percentage

        self.logger.debug(
            f"Market impact for {symbol}: {impact_bps:.1f} bps "
            f"({trade_size_percentage:.2f}% of daily volume), cost: ${impact_cost:.2f}"
        )

        return MarketImpactEstimate(
            symbol=symbol,
            trade_size_percentage=trade_size_percentage,
            estimated_impact_bps=impact_bps,
            estimated_impact_cost=impact_cost,
            impact_category=impact_category,
            mitigation_suggestions=mitigation_suggestions,
        )

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
        # Calculate expected annual benefit from rebalancing
        expected_benefit = self._estimate_rebalancing_benefit(trade_recommendations, portfolio, config)

        # Calculate break-even period
        break_even_days = None
        if expected_benefit > 0:
            break_even_days = int((total_costs / expected_benefit) * 365)

        # Calculate cost as percentage of portfolio
        cost_percentage = (total_costs / portfolio.total_value * 100) if portfolio.total_value > 0 else 0.0

        # Generate recommendation
        recommendation, rationale = self._generate_cost_benefit_recommendation(
            total_costs, expected_benefit, cost_percentage, break_even_days
        )

        # Generate alternative approaches
        alternatives = self._generate_alternative_approaches(total_costs, cost_percentage, trade_recommendations)

        self.logger.info(
            f"Cost-benefit analysis: ${total_costs:.2f} cost, "
            f"${expected_benefit:.2f} annual benefit, "
            f"{break_even_days} days break-even"
        )

        return CostBenefitAnalysis(
            total_rebalancing_cost=total_costs,
            expected_annual_benefit=expected_benefit,
            break_even_days=break_even_days,
            cost_as_percentage_of_portfolio=cost_percentage,
            recommendation=recommendation,
            rationale=rationale,
            alternative_approaches=alternatives,
        )

    def _get_broker_fee_structure(self, broker_type: BrokerType) -> BrokerFeeStructure:
        """Get fee structure for broker type."""
        fee_structures = {
            BrokerType.COMMISSION_FREE: BrokerFeeStructure(
                broker_type=broker_type,
                base_commission=0.0,
                per_share_fee=0.0,
                percentage_fee=0.0,
                minimum_commission=0.0,
                maximum_commission=0.0,
                options_fee=0.65,
                foreign_stock_fee=0.0,
                regulatory_fees=0.0000221,  # SEC fee
            ),
            BrokerType.DISCOUNT: BrokerFeeStructure(
                broker_type=broker_type,
                base_commission=0.0,
                per_share_fee=0.0,
                percentage_fee=0.0,
                minimum_commission=0.0,
                maximum_commission=0.0,
                options_fee=0.65,
                foreign_stock_fee=15.0,
                regulatory_fees=0.0000221,
            ),
            BrokerType.FULL_SERVICE: BrokerFeeStructure(
                broker_type=broker_type,
                base_commission=25.0,
                per_share_fee=0.02,
                percentage_fee=0.001,
                minimum_commission=25.0,
                maximum_commission=250.0,
                options_fee=25.0,
                foreign_stock_fee=50.0,
                regulatory_fees=0.0000221,
            ),
            BrokerType.ROBO_ADVISOR: BrokerFeeStructure(
                broker_type=broker_type,
                base_commission=0.0,
                per_share_fee=0.0,
                percentage_fee=0.0025,  # 0.25% annual fee
                minimum_commission=0.0,
                maximum_commission=float("inf"),
                options_fee=0.0,
                foreign_stock_fee=0.0,
                regulatory_fees=0.0000221,
            ),
        }
        return fee_structures[broker_type]

    def _calculate_total_commission_costs(self, trade_recommendations: list[TradeRecommendation]) -> float:
        """Calculate total commission costs for all trades."""
        total_commission = 0.0
        for trade in trade_recommendations:
            if trade.action.value in ["BUY", "SELL"]:
                commission = self.calculate_commission_cost(trade.trade_value, trade.symbol, trade.quantity)
                total_commission += commission
        return total_commission

    def _calculate_total_spread_costs(
        self, trade_recommendations: list[TradeRecommendation], market_data: dict[str, Any] | None
    ) -> float:
        """Calculate total spread costs for all trades."""
        total_spread = 0.0
        for trade in trade_recommendations:
            if trade.action.value in ["BUY", "SELL"]:
                spread_estimate = self.estimate_bid_ask_spread(trade.symbol, trade.trade_value, market_data)
                total_spread += spread_estimate.estimated_spread_cost
        return total_spread

    def _calculate_total_market_impact_costs(
        self,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
        market_data: dict[str, Any] | None,
    ) -> float:
        """Calculate total market impact costs for all trades."""
        total_impact = 0.0
        for trade in trade_recommendations:
            if trade.action.value in ["BUY", "SELL"]:
                impact_estimate = self.estimate_market_impact(trade.symbol, trade.trade_value, portfolio.total_value, market_data)
                total_impact += impact_estimate.estimated_impact_cost
        return total_impact

    def _calculate_break_even_days(
        self,
        total_costs: float,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
    ) -> int | None:
        """Calculate break-even period in days."""
        # Estimate annual benefit from improved allocation
        annual_benefit = self._estimate_rebalancing_benefit(trade_recommendations, portfolio, None)

        if annual_benefit <= 0:
            return None

        # Calculate days to break even
        break_even_years = total_costs / annual_benefit
        return int(break_even_years * 365)

    def _estimate_rebalancing_benefit(
        self,
        trade_recommendations: list[TradeRecommendation],
        portfolio: PortfolioAnalysis,
        config: PortfolioConfiguration | None,
    ) -> float:
        """Estimate annual benefit from rebalancing."""
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

    def _generate_cost_benefit_recommendation(
        self,
        total_costs: float,
        expected_benefit: float,
        cost_percentage: float,
        break_even_days: int | None,
    ) -> tuple[str, str]:
        """Generate cost-benefit recommendation and rationale."""
        if cost_percentage > 2.0:
            recommendation = "REJECT"
            rationale = (
                f"Transaction costs of {cost_percentage:.1f}% are excessive. "
                "Consider alternative rebalancing approaches or delay until larger deviations occur."
            )
        elif break_even_days and break_even_days > 365:
            recommendation = "DELAY"
            rationale = (
                f"Break-even period of {break_even_days} days is too long. "
                "Consider waiting for larger deviations or using new contributions to rebalance."
            )
        elif cost_percentage > 1.0:
            recommendation = "MODIFY"
            rationale = (
                f"Transaction costs of {cost_percentage:.1f}% are moderate. "
                "Consider rebalancing only the most deviated positions or using gradual rebalancing."
            )
        else:
            recommendation = "PROCEED"
            rationale = (
                f"Transaction costs of {cost_percentage:.1f}% are reasonable. "
                f"Expected to break even in {break_even_days or 'N/A'} days."
            )

        return recommendation, rationale

    def _generate_alternative_approaches(
        self,
        total_costs: float,
        cost_percentage: float,
        trade_recommendations: list[TradeRecommendation],
    ) -> list[str]:
        """Generate alternative rebalancing approaches."""
        alternatives = []

        if cost_percentage > 1.0:
            alternatives.append("Use new contributions to gradually rebalance over time")
            alternatives.append("Rebalance only positions with highest deviations")
            alternatives.append("Wait for larger deviations before rebalancing")

        if len(trade_recommendations) > 5:
            alternatives.append("Split rebalancing into multiple sessions")
            alternatives.append("Use algorithmic execution to reduce market impact")

        high_impact_trades = [
            t
            for t in trade_recommendations
            if t.trade_value > 10000  # Trades over $10k
        ]
        if high_impact_trades:
            alternatives.append("Execute large trades using TWAP or VWAP strategies")
            alternatives.append("Consider using ETFs for broad market exposure instead of individual stocks")

        return alternatives

    def _is_etf(self, symbol: str) -> bool:
        """Check if symbol is likely an ETF."""
        etf_indicators = ["ETF", "SPDR", "VTI", "VOO", "QQQ", "IWM", "EFA", "EEM"]
        return any(indicator in symbol.upper() for indicator in etf_indicators) or len(symbol) <= 3

    def _is_foreign_stock(self, symbol: str) -> bool:
        """Check if symbol is a foreign stock."""
        # Simple heuristic - foreign stocks often have longer symbols or specific patterns
        return len(symbol) > 4 or "." in symbol or symbol.endswith("F")

    def _is_large_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is large cap."""
        if market_data and symbol in market_data:
            market_cap = market_data[symbol].get("market_cap", 0)
            return market_cap > 10_000_000_000  # > $10B

        # Fallback heuristics
        large_cap_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK"]
        return any(symbol.startswith(lc) for lc in large_cap_symbols)

    def _is_mid_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is mid cap."""
        if market_data and symbol in market_data:
            market_cap = market_data[symbol].get("market_cap", 0)
            return 2_000_000_000 <= market_cap <= 10_000_000_000  # $2B - $10B

        # Default to mid cap if not clearly large or small
        return not self._is_large_cap(symbol, market_data) and not self._is_small_cap(symbol, market_data)

    def _is_small_cap(self, symbol: str, market_data: dict[str, Any] | None) -> bool:
        """Check if symbol is small cap."""
        if market_data and symbol in market_data:
            market_cap = market_data[symbol].get("market_cap", 0)
            return market_cap < 2_000_000_000  # < $2B

        # Fallback - assume small cap for longer symbols
        return len(symbol) > 4

    def _estimate_avg_daily_volume_value(self, symbol: str, market_data: dict[str, Any] | None) -> float:
        """Estimate average daily volume value."""
        if market_data and symbol in market_data:
            volume = market_data[symbol].get("avg_daily_volume", 0)
            price = market_data[symbol].get("price", 0)
            return volume * price

        # Fallback estimates based on symbol characteristics
        if self._is_large_cap(symbol, market_data):
            return 100_000_000  # $100M daily volume
        elif self._is_mid_cap(symbol, market_data):
            return 20_000_000  # $20M daily volume
        else:
            return 5_000_000  # $5M daily volume
