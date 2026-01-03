"""
Price target calculation utilities for FinWiz.

This module provides valuation and price target calculation functions for
stocks and other assets. It implements multiple valuation methodologies
including DCF, P/E multiples, and technical analysis-based targets.

Key Features:
- DCF (Discounted Cash Flow) valuation
- P/E multiple-based targets
- Technical analysis targets (Fibonacci, support/resistance)
- Confidence levels for each target
- Upside/downside percentage calculations

Usage:
    from finwiz.quantitative.price_targets import (
        calculate_dcf_target,
        calculate_pe_target,
        calculate_technical_target
    )

    # DCF valuation
    target = calculate_dcf_target(
        cash_flows=[100, 110, 121, 133],
        discount_rate=0.10,
        terminal_growth=0.03
    )

    # P/E multiple target
    target = calculate_pe_target(
        earnings_per_share=5.50,
        target_pe_ratio=20.0
    )
"""

from typing import Any

import pandas as pd

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PriceTarget:
    """
    Price target result with metadata.

    Attributes:
        target_price: Calculated target price
        current_price: Current market price (if provided)
        upside_pct: Upside percentage from current price
        downside_pct: Downside percentage from current price
        confidence: Confidence level (0.0-1.0)
        method: Valuation method used
        assumptions: Key assumptions used in calculation

    """

    def __init__(
        self,
        target_price: float,
        current_price: float | None = None,
        confidence: float = 0.5,
        method: str = "unknown",
        assumptions: dict[str, Any] | None = None,
    ):
        """
        Initialize price target.

        Args:
            target_price: Calculated target price
            current_price: Current market price (optional)
            confidence: Confidence level (0.0-1.0)
            method: Valuation method used
            assumptions: Key assumptions dictionary

        """
        self.target_price = target_price
        self.current_price = current_price
        self.confidence = confidence
        self.method = method
        self.assumptions = assumptions or {}

        # Calculate upside/downside if current price provided
        if current_price and current_price > 0:
            self.upside_pct = ((target_price - current_price) / current_price) * 100
            self.downside_pct = -self.upside_pct if self.upside_pct < 0 else 0.0
        else:
            self.upside_pct = 0.0
            self.downside_pct = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "target_price": self.target_price,
            "current_price": self.current_price,
            "upside_pct": self.upside_pct,
            "downside_pct": self.downside_pct,
            "confidence": self.confidence,
            "method": self.method,
            "assumptions": self.assumptions,
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"PriceTarget(target=${self.target_price:.2f}, upside={self.upside_pct:.1f}%, confidence={self.confidence:.2f}, method={self.method})"


def calculate_dcf_target(
    cash_flows: list[float],
    discount_rate: float,
    terminal_growth: float,
    shares_outstanding: float | None = None,
    current_price: float | None = None,
) -> PriceTarget:
    """
    Calculate price target using Discounted Cash Flow (DCF) valuation.

    This function implements a standard DCF model with terminal value
    calculation using the Gordon Growth Model. It discounts projected
    free cash flows to present value and adds a terminal value.

    Args:
        cash_flows: List of projected annual free cash flows
        discount_rate: Discount rate (WACC) as decimal (e.g., 0.10 for 10%)
        terminal_growth: Terminal growth rate as decimal (e.g., 0.03 for 3%)
        shares_outstanding: Number of shares outstanding (optional, for per-share value)
        current_price: Current market price for upside calculation (optional)

    Returns:
        PriceTarget: DCF-based price target with confidence and assumptions

    Example:
        >>> target = calculate_dcf_target(
        ...     cash_flows=[100, 110, 121, 133],
        ...     discount_rate=0.10,
        ...     terminal_growth=0.03,
        ...     shares_outstanding=1000,
        ...     current_price=50.0,
        ... )
        >>> print(f"Target: ${target.target_price:.2f}, Upside: {target.upside_pct:.1f}%")

    Notes:
        - Terminal value = Final CF * (1 + g) / (r - g)
        - Enterprise value = PV(cash flows) + PV(terminal value)
        - Confidence decreases with longer projection periods
        - Assumes constant discount rate and terminal growth

    """
    try:
        if not cash_flows or len(cash_flows) == 0:
            logger.warning("No cash flows provided for DCF calculation")
            return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="dcf", assumptions={})

        if discount_rate <= terminal_growth:
            logger.warning(f"Discount rate ({discount_rate}) must be > terminal growth ({terminal_growth})")
            return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="dcf", assumptions={})

        # Calculate present value of projected cash flows
        pv_cash_flows = 0.0
        for i, cf in enumerate(cash_flows, start=1):
            pv_cash_flows += cf / ((1 + discount_rate) ** i)

        # Calculate terminal value using Gordon Growth Model
        final_cf = cash_flows[-1]
        terminal_value = (final_cf * (1 + terminal_growth)) / (discount_rate - terminal_growth)

        # Discount terminal value to present
        n_years = len(cash_flows)
        pv_terminal_value = terminal_value / ((1 + discount_rate) ** n_years)

        # Enterprise value
        enterprise_value = pv_cash_flows + pv_terminal_value

        # Convert to per-share value if shares outstanding provided
        if shares_outstanding and shares_outstanding > 0:
            target_price = enterprise_value / shares_outstanding
        else:
            target_price = enterprise_value

        # Calculate confidence (decreases with longer projections)
        # Base confidence 0.7, reduced by 0.05 per year beyond 3 years
        base_confidence = 0.7
        confidence = max(0.3, base_confidence - (max(0, n_years - 3) * 0.05))

        assumptions = {
            "discount_rate": discount_rate,
            "terminal_growth": terminal_growth,
            "projection_years": n_years,
            "pv_cash_flows": pv_cash_flows,
            "pv_terminal_value": pv_terminal_value,
            "enterprise_value": enterprise_value,
            "shares_outstanding": shares_outstanding,
        }

        logger.debug(f"DCF target calculated: ${target_price:.2f} (confidence: {confidence:.2f})")

        return PriceTarget(
            target_price=target_price,
            current_price=current_price,
            confidence=confidence,
            method="dcf",
            assumptions=assumptions,
        )

    except Exception as e:
        logger.error(f"DCF calculation failed: {e}")
        return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="dcf", assumptions={})


def calculate_pe_target(
    earnings_per_share: float,
    target_pe_ratio: float,
    current_price: float | None = None,
    sector_avg_pe: float | None = None,
) -> PriceTarget:
    """
    Calculate price target using P/E multiple valuation.

    This function applies a target P/E ratio to earnings per share to
    derive a price target. Confidence is higher when target P/E is close
    to sector average.

    Args:
        earnings_per_share: Projected EPS (trailing or forward)
        target_pe_ratio: Target P/E multiple to apply
        current_price: Current market price for upside calculation (optional)
        sector_avg_pe: Sector average P/E for confidence adjustment (optional)

    Returns:
        PriceTarget: P/E-based price target with confidence and assumptions

    Example:
        >>> target = calculate_pe_target(earnings_per_share=5.50, target_pe_ratio=20.0, current_price=95.0, sector_avg_pe=18.5)
        >>> print(f"Target: ${target.target_price:.2f}")

    Notes:
        - Target Price = EPS * Target P/E
        - Confidence higher when target P/E near sector average
        - Assumes EPS projections are accurate
        - Does not account for growth rate differences

    """
    try:
        if earnings_per_share <= 0:
            logger.warning(f"Invalid EPS: {earnings_per_share}")
            return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="pe_multiple", assumptions={})

        if target_pe_ratio <= 0:
            logger.warning(f"Invalid P/E ratio: {target_pe_ratio}")
            return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="pe_multiple", assumptions={})

        # Calculate target price
        target_price = earnings_per_share * target_pe_ratio

        # Calculate confidence based on sector comparison
        base_confidence = 0.65
        if sector_avg_pe and sector_avg_pe > 0:
            # Confidence decreases as target P/E deviates from sector average
            pe_deviation = abs(target_pe_ratio - sector_avg_pe) / sector_avg_pe
            confidence = max(0.3, base_confidence - (pe_deviation * 0.5))
        else:
            confidence = base_confidence

        assumptions = {
            "earnings_per_share": earnings_per_share,
            "target_pe_ratio": target_pe_ratio,
            "sector_avg_pe": sector_avg_pe,
        }

        logger.debug(f"P/E target calculated: ${target_price:.2f} (confidence: {confidence:.2f})")

        return PriceTarget(
            target_price=target_price,
            current_price=current_price,
            confidence=confidence,
            method="pe_multiple",
            assumptions=assumptions,
        )

    except Exception as e:
        logger.error(f"P/E calculation failed: {e}")
        return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method="pe_multiple", assumptions={})


def calculate_technical_target(prices: pd.Series, method: str = "fibonacci", current_price: float | None = None) -> PriceTarget:
    """
    Calculate price target using technical analysis methods.

    Supports multiple technical analysis approaches:
    - Fibonacci retracement/extension levels
    - Moving average projections
    - Trend channel projections

    Args:
        prices: Historical price series (pandas Series)
        method: Technical method ('fibonacci', 'ma_projection', 'trend_channel')
        current_price: Current market price (optional, uses last price if not provided)

    Returns:
        PriceTarget: Technical analysis-based price target

    Example:
        >>> prices = pd.Series([100, 105, 110, 108, 115, 120])
        >>> target = calculate_technical_target(prices, method="fibonacci")
        >>> print(f"Target: ${target.target_price:.2f}")

    Notes:
        - Fibonacci: Uses 1.618 extension from recent swing
        - MA projection: Projects based on moving average trend
        - Trend channel: Projects upper channel boundary
        - Confidence moderate (0.5) due to technical nature

    """
    try:
        if len(prices) < 10:
            logger.warning(f"Insufficient price data: {len(prices)} points")
            return PriceTarget(target_price=0.0, current_price=current_price, confidence=0.0, method=f"technical_{method}", assumptions={})

        if current_price is None:
            current_price = float(prices.iloc[-1])

        if method == "fibonacci":
            # Find recent swing high and low
            recent_prices = prices.tail(20)
            swing_high = float(recent_prices.max())
            swing_low = float(recent_prices.min())

            # Calculate Fibonacci extension (1.618 level)
            price_range = swing_high - swing_low
            target_price = swing_high + (price_range * 0.618)

            assumptions = {
                "swing_high": swing_high,
                "swing_low": swing_low,
                "fibonacci_level": 1.618,
            }

        elif method == "ma_projection":
            # Project based on 20-period MA trend
            ma_20 = prices.rolling(window=20).mean()
            recent_ma = ma_20.tail(10)

            # Calculate MA slope
            if len(recent_ma) >= 2:
                ma_slope = (float(recent_ma.iloc[-1]) - float(recent_ma.iloc[0])) / len(recent_ma)
                # Project 10 periods forward
                target_price = float(recent_ma.iloc[-1]) + (ma_slope * 10)
            else:
                target_price = current_price

            assumptions = {
                "ma_period": 20,
                "projection_periods": 10,
                "ma_slope": ma_slope if len(recent_ma) >= 2 else 0,
            }

        elif method == "trend_channel":
            # Calculate upper trend channel
            recent_prices = prices.tail(30)
            highs = recent_prices.rolling(window=5).max()
            upper_channel = float(highs.mean() * 1.05)  # 5% above average highs

            target_price = upper_channel

            assumptions = {
                "channel_period": 30,
                "upper_channel_multiplier": 1.05,
            }

        else:
            logger.warning(f"Unknown technical method: {method}")
            return PriceTarget(
                target_price=current_price,
                current_price=current_price,
                confidence=0.0,
                method=f"technical_{method}",
                assumptions={},
            )

        # Technical analysis has moderate confidence
        confidence = 0.5

        logger.debug(f"Technical target ({method}) calculated: ${target_price:.2f}")

        return PriceTarget(
            target_price=target_price,
            current_price=current_price,
            confidence=confidence,
            method=f"technical_{method}",
            assumptions=assumptions,
        )

    except Exception as e:
        logger.error(f"Technical target calculation failed: {e}")
        return PriceTarget(
            target_price=current_price or 0.0,
            current_price=current_price,
            confidence=0.0,
            method=f"technical_{method}",
            assumptions={},
        )


def calculate_support_resistance_targets(prices: pd.Series, current_price: float | None = None) -> dict[str, PriceTarget]:
    """
    Calculate price targets based on support and resistance levels.

    Identifies key support and resistance levels from historical prices
    and provides upside/downside targets.

    Args:
        prices: Historical price series (pandas Series)
        current_price: Current market price (optional, uses last price if not provided)

    Returns:
        Dictionary with 'resistance' and 'support' PriceTarget objects

    Example:
        >>> prices = pd.Series([100, 105, 110, 108, 115, 120, 118])
        >>> targets = calculate_support_resistance_targets(prices)
        >>> print(f"Resistance: ${targets['resistance'].target_price:.2f}")
        >>> print(f"Support: ${targets['support'].target_price:.2f}")

    Notes:
        - Resistance: Nearest significant price level above current
        - Support: Nearest significant price level below current
        - Uses local maxima/minima for level identification
        - Confidence moderate (0.55) for established levels

    """
    try:
        if len(prices) < 20:
            logger.warning(f"Insufficient price data for S/R: {len(prices)} points")
            return {
                "resistance": PriceTarget(0.0, current_price, 0.0, "support_resistance", {}),
                "support": PriceTarget(0.0, current_price, 0.0, "support_resistance", {}),
            }

        if current_price is None:
            current_price = float(prices.iloc[-1])

        # Find local maxima (resistance) and minima (support)
        window = 5
        local_max = prices.rolling(window=window, center=True).max()
        local_min = prices.rolling(window=window, center=True).min()

        # Identify resistance levels (local maxima above current price)
        resistance_levels = prices[(prices == local_max) & (prices > current_price)]
        if len(resistance_levels) > 0:
            resistance_price = float(resistance_levels.min())  # Nearest resistance
        else:
            resistance_price = current_price * 1.10  # Default 10% above

        # Identify support levels (local minima below current price)
        support_levels = prices[(prices == local_min) & (prices < current_price)]
        if len(support_levels) > 0:
            support_price = float(support_levels.max())  # Nearest support
        else:
            support_price = current_price * 0.90  # Default 10% below

        # Confidence based on how established the levels are
        confidence = 0.55

        resistance_target = PriceTarget(
            target_price=resistance_price,
            current_price=current_price,
            confidence=confidence,
            method="support_resistance",
            assumptions={"level_type": "resistance", "window": window},
        )

        support_target = PriceTarget(
            target_price=support_price,
            current_price=current_price,
            confidence=confidence,
            method="support_resistance",
            assumptions={"level_type": "support", "window": window},
        )

        logger.debug(f"S/R targets calculated - Resistance: ${resistance_price:.2f}, Support: ${support_price:.2f}")

        return {"resistance": resistance_target, "support": support_target}

    except Exception as e:
        logger.error(f"S/R target calculation failed: {e}")
        return {
            "resistance": PriceTarget(0.0, current_price, 0.0, "support_resistance", {}),
            "support": PriceTarget(0.0, current_price, 0.0, "support_resistance", {}),
        }


def calculate_consensus_target(targets: list[PriceTarget], weights: list[float] | None = None) -> PriceTarget:
    """
    Calculate consensus price target from multiple valuation methods.

    Combines multiple price targets using weighted average, with weights
    based on confidence levels if not explicitly provided.

    Args:
        targets: List of PriceTarget objects from different methods
        weights: Optional weights for each target (defaults to confidence-based)

    Returns:
        PriceTarget: Consensus target with combined confidence

    Example:
        >>> dcf_target = calculate_dcf_target(...)
        >>> pe_target = calculate_pe_target(...)
        >>> consensus = calculate_consensus_target([dcf_target, pe_target])
        >>> print(f"Consensus: ${consensus.target_price:.2f}")

    Notes:
        - Default weights based on confidence levels
        - Consensus confidence is weighted average of individual confidences
        - Useful for combining fundamental and technical targets

    """
    try:
        if not targets or len(targets) == 0:
            logger.warning("No targets provided for consensus calculation")
            return PriceTarget(0.0, None, 0.0, "consensus", {})

        # Filter out zero targets
        valid_targets = [t for t in targets if t.target_price > 0]
        if not valid_targets:
            logger.warning("No valid targets for consensus")
            return PriceTarget(0.0, None, 0.0, "consensus", {})

        # Use confidence-based weights if not provided
        if weights is None:
            weights = [t.confidence for t in valid_targets]

        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            weights = [1.0 / len(valid_targets)] * len(valid_targets)
        else:
            weights = [w / total_weight for w in weights]

        # Calculate weighted average target
        consensus_price = sum(t.target_price * w for t, w in zip(valid_targets, weights))

        # Calculate weighted average confidence
        consensus_confidence = sum(t.confidence * w for t, w in zip(valid_targets, weights))

        # Get current price from first target
        current_price = valid_targets[0].current_price

        assumptions = {
            "methods": [t.method for t in valid_targets],
            "individual_targets": [t.target_price for t in valid_targets],
            "weights": weights,
        }

        logger.debug(f"Consensus target calculated: ${consensus_price:.2f} (confidence: {consensus_confidence:.2f})")

        return PriceTarget(
            target_price=consensus_price,
            current_price=current_price,
            confidence=consensus_confidence,
            method="consensus",
            assumptions=assumptions,
        )

    except Exception as e:
        logger.error(f"Consensus calculation failed: {e}")
        return PriceTarget(0.0, None, 0.0, "consensus", {})
