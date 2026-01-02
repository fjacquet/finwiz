"""
ETF-specific metrics calculation utilities for FinWiz.

This module provides calculation functions specific to ETF analysis,
including tracking error, correlation, expense impact, liquidity scoring,
and concentration risk assessment.

Key Features:
- Tracking error calculation vs benchmark
- Correlation coefficient with benchmark
- Expense ratio impact on returns
- Liquidity scoring based on volume, spread, market cap
- Concentration risk from top holdings

Usage:
    from finwiz.utils.etf_metrics import (
        calculate_tracking_error,
        calculate_correlation,
        calculate_expense_impact
    )

    # Tracking error
    te = calculate_tracking_error(etf_returns, benchmark_returns)

    # Correlation
    corr = calculate_correlation(etf_returns, benchmark_returns)
"""

import numpy as np
import pandas as pd

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def calculate_tracking_error(etf_returns: pd.Series, benchmark_returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate tracking error between ETF and benchmark returns.

    Tracking error measures how closely an ETF follows its benchmark index.
    It's calculated as the standard deviation of the difference between
    ETF returns and benchmark returns.

    Args:
        etf_returns: ETF return series (daily, weekly, or monthly)
        benchmark_returns: Benchmark return series (same frequency as ETF)
        annualize: Whether to annualize the tracking error (default: True)

    Returns:
        Tracking error as a decimal (e.g., 0.02 for 2%)

    Example:
        >>> etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015])
        >>> benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014])
        >>> te = calculate_tracking_error(etf_returns, benchmark_returns)
        >>> print(f"Tracking Error: {te * 100:.2f}%")

    Notes:
        - Lower tracking error indicates closer tracking
        - Typical range: 0.1% - 2% for index ETFs
        - Higher for actively managed or leveraged ETFs
        - Annualization assumes 252 trading days

    """
    try:
        # Align series by index
        aligned = pd.DataFrame({"etf": etf_returns, "benchmark": benchmark_returns}).dropna()

        if len(aligned) < 2:
            logger.warning(f"Insufficient data for tracking error: {len(aligned)} points")
            return 0.0

        # Calculate return differences
        return_diff = aligned["etf"] - aligned["benchmark"]

        # Calculate tracking error (std dev of differences)
        tracking_error = float(return_diff.std())

        # Annualize if requested (assuming daily returns)
        if annualize:
            tracking_error = tracking_error * np.sqrt(252)

        logger.debug(f"Tracking error calculated: {tracking_error * 100:.3f}%")

        return tracking_error

    except Exception as e:
        logger.error(f"Tracking error calculation failed: {e}")
        return 0.0


def calculate_correlation(etf_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Calculate correlation coefficient between ETF and benchmark returns.

    Correlation measures the linear relationship between ETF and benchmark
    returns. A correlation of 1.0 indicates perfect positive correlation.

    Args:
        etf_returns: ETF return series
        benchmark_returns: Benchmark return series

    Returns:
        Correlation coefficient (-1.0 to 1.0)

    Example:
        >>> etf_returns = pd.Series([0.01, 0.02, -0.01, 0.015])
        >>> benchmark_returns = pd.Series([0.011, 0.019, -0.009, 0.014])
        >>> corr = calculate_correlation(etf_returns, benchmark_returns)
        >>> print(f"Correlation: {corr:.3f}")

    Notes:
        - 1.0 = Perfect positive correlation
        - 0.0 = No correlation
        - -1.0 = Perfect negative correlation
        - Index ETFs typically have correlation > 0.95
        - Lower correlation may indicate tracking issues or active management

    """
    try:
        # Align series by index
        aligned = pd.DataFrame({"etf": etf_returns, "benchmark": benchmark_returns}).dropna()

        if len(aligned) < 2:
            logger.warning(f"Insufficient data for correlation: {len(aligned)} points")
            return 0.0

        # Calculate Pearson correlation
        correlation = float(aligned["etf"].corr(aligned["benchmark"]))

        logger.debug(f"Correlation calculated: {correlation:.3f}")

        return correlation

    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}")
        return 0.0


def calculate_expense_impact(returns: pd.Series, expense_ratio: float, years: int = 10) -> dict[str, float]:
    """
    Calculate the impact of expense ratio on investment returns over time.

    This function shows how expense ratios compound over time and reduce
    total returns. It's useful for comparing ETFs with different expense ratios.

    Args:
        returns: Historical return series (used to estimate average return)
        expense_ratio: Annual expense ratio as decimal (e.g., 0.0020 for 0.20%)
        years: Number of years to project (default: 10)

    Returns:
        Dictionary with impact metrics:
        - 'annual_drag': Annual return drag from expenses
        - 'cumulative_cost': Total cost over projection period
        - 'return_reduction_pct': Percentage reduction in total return

    Example:
        >>> returns = pd.Series([0.08, 0.10, 0.12, 0.09])
        >>> impact = calculate_expense_impact(returns, expense_ratio=0.0050, years=10)
        >>> print(f"Annual drag: {impact['annual_drag'] * 100:.2f}%")
        >>> print(f"10-year cost: {impact['cumulative_cost'] * 100:.1f}%")

    Notes:
        - Expense ratios are deducted daily from NAV
        - Impact compounds over time
        - Even small differences (0.10% vs 0.50%) matter long-term
        - Does not include trading costs or bid-ask spreads

    """
    try:
        if len(returns) < 1:
            logger.warning("No returns provided for expense impact calculation")
            return {"annual_drag": 0.0, "cumulative_cost": 0.0, "return_reduction_pct": 0.0}

        # Calculate average annual return
        avg_return = float(returns.mean())

        # Annual drag is simply the expense ratio
        annual_drag = expense_ratio

        # Calculate cumulative impact over time
        # Without expenses: (1 + r)^n
        # With expenses: (1 + r - e)^n
        # Cost = [(1 + r)^n - (1 + r - e)^n] / (1 + r)^n

        gross_return = (1 + avg_return) ** years
        net_return = (1 + avg_return - expense_ratio) ** years
        cumulative_cost = (gross_return - net_return) / gross_return

        # Return reduction percentage
        return_reduction_pct = cumulative_cost * 100

        result = {
            "annual_drag": annual_drag,
            "cumulative_cost": cumulative_cost,
            "return_reduction_pct": return_reduction_pct,
            "years": years,
            "avg_annual_return": avg_return,
        }

        logger.debug(f"Expense impact calculated: {annual_drag * 100:.2f}% annual, {cumulative_cost * 100:.1f}% over {years} years")

        return result

    except Exception as e:
        logger.error(f"Expense impact calculation failed: {e}")
        return {"annual_drag": 0.0, "cumulative_cost": 0.0, "return_reduction_pct": 0.0}


def calculate_liquidity_score(avg_daily_volume: float, bid_ask_spread_pct: float, market_cap: float) -> dict[str, float | str]:
    """
    Calculate liquidity score for an ETF based on multiple factors.

    Liquidity is crucial for ETF investors as it affects trading costs
    and ease of entry/exit. This function combines volume, spread, and
    market cap into a composite liquidity score.

    Args:
        avg_daily_volume: Average daily trading volume (shares)
        bid_ask_spread_pct: Bid-ask spread as percentage (e.g., 0.05 for 0.05%)
        market_cap: Market capitalization in dollars

    Returns:
        Dictionary with liquidity metrics:
        - 'liquidity_score': Composite score (0-100, higher is better)
        - 'volume_score': Volume component (0-100)
        - 'spread_score': Spread component (0-100)
        - 'size_score': Market cap component (0-100)
        - 'liquidity_rating': Text rating (Excellent/Good/Fair/Poor)

    Example:
        >>> score = calculate_liquidity_score(avg_daily_volume=5_000_000, bid_ask_spread_pct=0.05, market_cap=10_000_000_000)
        >>> print(f"Liquidity Score: {score['liquidity_score']:.0f}/100")
        >>> print(f"Rating: {score['liquidity_rating']}")

    Notes:
        - Volume: Higher is better (>1M shares/day is good)
        - Spread: Lower is better (<0.10% is excellent)
        - Market cap: Larger is generally more liquid
        - Score weights: Volume 40%, Spread 40%, Size 20%

    """
    try:
        # Volume score (0-100)
        # Excellent: >5M shares/day, Poor: <100K shares/day
        if avg_daily_volume >= 5_000_000:
            volume_score = 100.0
        elif avg_daily_volume >= 1_000_000:
            volume_score = 80.0
        elif avg_daily_volume >= 500_000:
            volume_score = 60.0
        elif avg_daily_volume >= 100_000:
            volume_score = 40.0
        else:
            volume_score = 20.0

        # Spread score (0-100)
        # Excellent: <0.05%, Poor: >0.50%
        if bid_ask_spread_pct <= 0.05:
            spread_score = 100.0
        elif bid_ask_spread_pct <= 0.10:
            spread_score = 80.0
        elif bid_ask_spread_pct <= 0.20:
            spread_score = 60.0
        elif bid_ask_spread_pct <= 0.50:
            spread_score = 40.0
        else:
            spread_score = 20.0

        # Size score (0-100)
        # Excellent: >$10B, Poor: <$100M
        if market_cap >= 10_000_000_000:
            size_score = 100.0
        elif market_cap >= 1_000_000_000:
            size_score = 80.0
        elif market_cap >= 500_000_000:
            size_score = 60.0
        elif market_cap >= 100_000_000:
            size_score = 40.0
        else:
            size_score = 20.0

        # Composite liquidity score (weighted average)
        liquidity_score = (volume_score * 0.4) + (spread_score * 0.4) + (size_score * 0.2)

        # Liquidity rating
        if liquidity_score >= 80:
            liquidity_rating = "Excellent"
        elif liquidity_score >= 60:
            liquidity_rating = "Good"
        elif liquidity_score >= 40:
            liquidity_rating = "Fair"
        else:
            liquidity_rating = "Poor"

        result: dict[str, float | str] = {
            "liquidity_score": liquidity_score,
            "volume_score": volume_score,
            "spread_score": spread_score,
            "size_score": size_score,
            "liquidity_rating": liquidity_rating,
        }

        logger.debug(f"Liquidity score calculated: {liquidity_score:.0f}/100 ({liquidity_rating})")

        return result

    except Exception as e:
        logger.error(f"Liquidity score calculation failed: {e}")
        return {
            "liquidity_score": 0.0,
            "volume_score": 0.0,
            "spread_score": 0.0,
            "size_score": 0.0,
            "liquidity_rating": "Unknown",
        }


def calculate_concentration_risk(holdings: list[dict[str, float]], top_n: int = 10) -> dict[str, float | str | int]:
    """
    Calculate concentration risk from ETF top holdings.

    Concentration risk measures how much of the ETF's assets are concentrated
    in a small number of holdings. Higher concentration means higher risk
    from individual position performance.

    Args:
        holdings: List of holdings with 'weight' key (as decimal, e.g., 0.05 for 5%)
        top_n: Number of top holdings to analyze (default: 10)

    Returns:
        Dictionary with concentration metrics:
        - 'top_n_concentration': Sum of top N holdings weights
        - 'herfindahl_index': Herfindahl-Hirschman Index (HHI)
        - 'effective_n_holdings': Effective number of holdings
        - 'concentration_rating': Text rating (Low/Moderate/High/Very High)

    Example:
        >>> holdings = [
        ...     {"ticker": "AAPL", "weight": 0.07},
        ...     {"ticker": "MSFT", "weight": 0.06},
        ...     {"ticker": "GOOGL", "weight": 0.04},
        ...     # ... more holdings
        ... ]
        >>> risk = calculate_concentration_risk(holdings, top_n=10)
        >>> print(f"Top 10 concentration: {risk['top_n_concentration'] * 100:.1f}%")
        >>> print(f"Rating: {risk['concentration_rating']}")

    Notes:
        - Top 10 concentration >50% is high risk
        - HHI: Sum of squared weights (higher = more concentrated)
        - Effective N: 1 / HHI (lower = more concentrated)
        - Broad market ETFs typically have low concentration
        - Sector/thematic ETFs may have higher concentration

    """
    try:
        if not holdings or len(holdings) == 0:
            logger.warning("No holdings provided for concentration risk calculation")
            return {
                "top_n_concentration": 0.0,
                "herfindahl_index": 0.0,
                "effective_n_holdings": 0.0,
                "concentration_rating": "Unknown",
            }

        # Extract weights
        weights = [h.get("weight", 0.0) for h in holdings]
        weights = [w for w in weights if w > 0]  # Filter out zero weights

        if not weights:
            logger.warning("No valid weights in holdings")
            return {
                "top_n_concentration": 0.0,
                "herfindahl_index": 0.0,
                "effective_n_holdings": 0.0,
                "concentration_rating": "Unknown",
            }

        # Sort weights in descending order
        weights_sorted = sorted(weights, reverse=True)

        # Top N concentration
        top_n_weights = weights_sorted[:top_n]
        top_n_concentration = sum(top_n_weights)

        # Herfindahl-Hirschman Index (HHI)
        # Sum of squared weights
        herfindahl_index = sum(w**2 for w in weights)

        # Effective number of holdings
        # 1 / HHI (represents the equivalent number of equal-weighted holdings)
        effective_n_holdings = 1.0 / herfindahl_index if herfindahl_index > 0 else 0.0

        # Concentration rating based on top N concentration
        if top_n_concentration >= 0.60:
            concentration_rating = "Very High"
        elif top_n_concentration >= 0.40:
            concentration_rating = "High"
        elif top_n_concentration >= 0.25:
            concentration_rating = "Moderate"
        else:
            concentration_rating = "Low"

        result = {
            "top_n_concentration": top_n_concentration,
            "herfindahl_index": herfindahl_index,
            "effective_n_holdings": effective_n_holdings,
            "concentration_rating": concentration_rating,
            "top_n": top_n,
            "total_holdings": len(weights),
        }

        logger.debug(f"Concentration risk calculated: Top {top_n} = {top_n_concentration * 100:.1f}%, Effective N = {effective_n_holdings:.1f}, Rating = {concentration_rating}")

        return result

    except Exception as e:
        logger.error(f"Concentration risk calculation failed: {e}")
        return {
            "top_n_concentration": 0.0,
            "herfindahl_index": 0.0,
            "effective_n_holdings": 0.0,
            "concentration_rating": "Unknown",
        }


def calculate_etf_efficiency_score(tracking_error: float, expense_ratio: float, liquidity_score: float) -> dict[str, float | str]:
    """
    Calculate overall ETF efficiency score combining multiple factors.

    This composite score helps compare ETFs by combining tracking accuracy,
    cost efficiency, and liquidity into a single metric.

    Args:
        tracking_error: Annualized tracking error (decimal, e.g., 0.02 for 2%)
        expense_ratio: Annual expense ratio (decimal, e.g., 0.0020 for 0.20%)
        liquidity_score: Liquidity score (0-100)

    Returns:
        Dictionary with efficiency metrics:
        - 'efficiency_score': Composite score (0-100, higher is better)
        - 'tracking_score': Tracking component (0-100)
        - 'cost_score': Cost component (0-100)
        - 'liquidity_component': Liquidity component (0-100)
        - 'efficiency_rating': Text rating (Excellent/Good/Fair/Poor)

    Example:
        >>> score = calculate_etf_efficiency_score(tracking_error=0.0015, expense_ratio=0.0020, liquidity_score=85.0)
        >>> print(f"Efficiency Score: {score['efficiency_score']:.0f}/100")
        >>> print(f"Rating: {score['efficiency_rating']}")

    Notes:
        - Tracking: Lower error = higher score
        - Cost: Lower expense ratio = higher score
        - Liquidity: Already scored 0-100
        - Weights: Tracking 40%, Cost 30%, Liquidity 30%

    """
    try:
        # Tracking score (0-100)
        # Excellent: <0.20%, Poor: >2.00%
        if tracking_error <= 0.0020:
            tracking_score = 100.0
        elif tracking_error <= 0.0050:
            tracking_score = 80.0
        elif tracking_error <= 0.0100:
            tracking_score = 60.0
        elif tracking_error <= 0.0200:
            tracking_score = 40.0
        else:
            tracking_score = 20.0

        # Cost score (0-100)
        # Excellent: <0.10%, Poor: >1.00%
        if expense_ratio <= 0.0010:
            cost_score = 100.0
        elif expense_ratio <= 0.0025:
            cost_score = 80.0
        elif expense_ratio <= 0.0050:
            cost_score = 60.0
        elif expense_ratio <= 0.0100:
            cost_score = 40.0
        else:
            cost_score = 20.0

        # Composite efficiency score (weighted average)
        efficiency_score = (tracking_score * 0.4) + (cost_score * 0.3) + (liquidity_score * 0.3)

        # Efficiency rating
        if efficiency_score >= 80:
            efficiency_rating = "Excellent"
        elif efficiency_score >= 60:
            efficiency_rating = "Good"
        elif efficiency_score >= 40:
            efficiency_rating = "Fair"
        else:
            efficiency_rating = "Poor"

        result: dict[str, float | str] = {
            "efficiency_score": efficiency_score,
            "tracking_score": tracking_score,
            "cost_score": cost_score,
            "liquidity_component": liquidity_score,
            "efficiency_rating": efficiency_rating,
        }

        logger.debug(f"ETF efficiency score calculated: {efficiency_score:.0f}/100 ({efficiency_rating})")

        return result

    except Exception as e:
        logger.error(f"ETF efficiency score calculation failed: {e}")
        return {
            "efficiency_score": 0.0,
            "tracking_score": 0.0,
            "cost_score": 0.0,
            "liquidity_component": 0.0,
            "efficiency_rating": "Unknown",
        }
