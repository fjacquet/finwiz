"""
Cost calculation utilities for transaction cost analysis.

This module provides functions for calculating commissions, bid-ask spreads,
and market impact costs for portfolio rebalancing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

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


def get_broker_fee_structure(broker_type: BrokerType) -> BrokerFeeStructure:
    """
    Get fee structure for broker type.

    Args:
        broker_type: Type of broker

    Returns:
        BrokerFeeStructure: Fee structure configuration

    """
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


def calculate_commission_cost(
    fee_structure: BrokerFeeStructure,
    trade_value: float,
    symbol: str,
    share_count: float,
) -> float:
    """
    Calculate commission cost based on broker fee structure.

    Args:
        fee_structure: Broker fee structure
        trade_value: Total value of the trade
        symbol: Stock symbol
        share_count: Number of shares

    Returns:
        float: Commission cost

    """
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
    if is_foreign_stock(symbol):
        total_commission += fee_structure.foreign_stock_fee

    logger.debug(f"Commission for {symbol}: ${total_commission:.2f}")
    return total_commission


def estimate_bid_ask_spread(
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
    factors_considered = []

    # Default spread estimates based on symbol characteristics
    if is_etf(symbol):
        # ETFs typically have tighter spreads
        base_spread_bps = 2.0  # 2 basis points
        factors_considered.append("ETF classification")
    elif is_large_cap(symbol, market_data):
        # Large cap stocks have tight spreads
        base_spread_bps = 3.0  # 3 basis points
        factors_considered.append("Large cap classification")
    elif is_mid_cap(symbol, market_data):
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

    logger.debug(f"Spread estimate for {symbol}: {base_spread_bps:.1f} bps, cost: ${spread_cost:.2f}")

    return SpreadEstimate(
        symbol=symbol,
        estimated_spread_bps=base_spread_bps,
        estimated_spread_percentage=spread_percentage,
        estimated_spread_cost=spread_cost,
        confidence_level=confidence,
        factors_considered=factors_considered,
    )


def estimate_market_impact(
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
    avg_daily_volume_value = estimate_avg_daily_volume_value(symbol, market_data)
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
    if is_large_cap(symbol, market_data):
        impact_bps *= 0.7  # Large caps have better liquidity
    elif is_small_cap(symbol, market_data):
        impact_bps *= 1.5  # Small caps have worse liquidity

    # Calculate impact cost
    impact_percentage = impact_bps / 10000
    impact_cost = trade_value * impact_percentage

    logger.debug(f"Market impact for {symbol}: {impact_bps:.1f} bps ({trade_size_percentage:.2f}% of daily volume), cost: ${impact_cost:.2f}")

    return MarketImpactEstimate(
        symbol=symbol,
        trade_size_percentage=trade_size_percentage,
        estimated_impact_bps=impact_bps,
        estimated_impact_cost=impact_cost,
        impact_category=impact_category,
        mitigation_suggestions=mitigation_suggestions,
    )


# Helper functions for symbol classification


def is_etf(symbol: str) -> bool:
    """Check if symbol is likely an ETF."""
    etf_indicators = ["ETF", "SPDR", "VTI", "VOO", "QQQ", "IWM", "EFA", "EEM"]
    return any(indicator in symbol.upper() for indicator in etf_indicators) or len(symbol) <= 3


def is_foreign_stock(symbol: str) -> bool:
    """Check if symbol is a foreign stock."""
    # Simple heuristic - foreign stocks often have longer symbols or specific patterns
    return len(symbol) > 4 or "." in symbol or symbol.endswith("F")


def is_large_cap(symbol: str, market_data: dict[str, Any] | None) -> bool:
    """Check if symbol is large cap."""
    if market_data and symbol in market_data:
        market_cap = market_data[symbol].get("market_cap", 0)
        return bool(market_cap > 10_000_000_000)  # > $10B

    # Fallback heuristics
    large_cap_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK"]
    return any(symbol.startswith(lc) for lc in large_cap_symbols)


def is_mid_cap(symbol: str, market_data: dict[str, Any] | None) -> bool:
    """Check if symbol is mid cap."""
    if market_data and symbol in market_data:
        market_cap = market_data[symbol].get("market_cap", 0)
        return bool(2_000_000_000 <= market_cap <= 10_000_000_000)  # $2B - $10B

    # Default to mid cap if not clearly large or small
    return not is_large_cap(symbol, market_data) and not is_small_cap(symbol, market_data)


def is_small_cap(symbol: str, market_data: dict[str, Any] | None) -> bool:
    """Check if symbol is small cap."""
    if market_data and symbol in market_data:
        market_cap = market_data[symbol].get("market_cap", 0)
        return bool(market_cap < 2_000_000_000)  # < $2B

    # Fallback - assume small cap for longer symbols
    return len(symbol) > 4


def estimate_avg_daily_volume_value(symbol: str, market_data: dict[str, Any] | None) -> float:
    """Estimate average daily volume value."""
    if market_data and symbol in market_data:
        volume = market_data[symbol].get("avg_daily_volume", 0)
        price = market_data[symbol].get("price", 0)
        return float(volume * price)

    # Fallback estimates based on symbol characteristics
    if is_large_cap(symbol, market_data):
        return 100_000_000  # $100M daily volume
    elif is_mid_cap(symbol, market_data):
        return 20_000_000  # $20M daily volume
    else:
        return 5_000_000  # $5M daily volume
