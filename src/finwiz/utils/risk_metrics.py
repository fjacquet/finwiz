"""
Risk Metrics Calculation Module.

This module provides risk calculation functions for financial analysis using
Empyrical-Reloaded for standard metrics (volatility, Sharpe, drawdown, beta)
and custom implementations for specialized metrics (VaR, CVaR).

Migrated to Empyrical-Reloaded as part of Phase 2A.3 refactoring.
See: empyrical-standards.md and financial-libraries-strategy.md

All functions accept pandas Series and return calculated metrics.
"""

import numpy as np
import pandas as pd
from empyrical import annual_volatility


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate historical volatility (standard deviation of returns).

    Uses Empyrical-Reloaded for calculation.

    Args:
        returns: Series of returns (daily, weekly, etc.)
        annualize: If True, annualize the volatility (assumes 252 trading days)

    Returns:
        Historical volatility as a float

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
        >>> vol = calculate_volatility(returns, annualize=True)
        >>> vol > 0
        True

    """
    if returns.empty:
        return 0.0

    if annualize:
        # Use Empyrical for annualized volatility
        volatility = annual_volatility(returns, period="daily")
    else:
        # Simple standard deviation for non-annualized
        volatility = returns.std()

    return float(volatility)


def calculate_var(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    Calculate Value at Risk (VaR) at a given confidence level.

    VaR represents the maximum expected loss over a given time period
    at a specified confidence level.

    Args:
        returns: Series of returns
        confidence_level: Confidence level (default 0.95 for 95%)

    Returns:
        Value at Risk as a float (negative value represents potential loss)

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
        >>> var = calculate_var(returns, confidence_level=0.95)
        >>> var < 0
        True

    """
    if returns.empty:
        return 0.0

    # Calculate the percentile corresponding to the confidence level
    # For 95% confidence, we look at the 5th percentile (worst 5% of returns)
    alpha = 1 - confidence_level
    var = np.percentile(returns, alpha * 100)

    return float(var)


def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR), also known as Expected Shortfall.

    CVaR is the expected loss given that the loss exceeds the VaR threshold.
    It provides a more comprehensive risk measure than VaR.

    Args:
        returns: Series of returns
        confidence_level: Confidence level (default 0.95 for 95%)

    Returns:
        Conditional VaR as a float (negative value represents expected loss in tail)

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02, -0.03])
        >>> cvar = calculate_cvar(returns, confidence_level=0.95)
        >>> cvar < 0
        True

    """
    if returns.empty:
        return 0.0

    # First calculate VaR
    var = calculate_var(returns, confidence_level)

    # CVaR is the mean of all returns that are worse than VaR
    tail_returns = returns[returns <= var]

    if tail_returns.empty:
        return var

    cvar = tail_returns.mean()

    return float(cvar)


def calculate_max_drawdown(prices: pd.Series) -> float:
    """
    Calculate maximum drawdown from a price series.

    Uses Empyrical-Reloaded for calculation.

    Maximum drawdown is the largest peak-to-trough decline in the price series.

    Args:
        prices: Series of prices (not returns)

    Returns:
        Maximum drawdown as a float (negative percentage, e.g., -0.25 for 25% drawdown)

    Examples:
        >>> prices = pd.Series([100, 110, 105, 95, 100, 120])
        >>> mdd = calculate_max_drawdown(prices)
        >>> mdd < 0
        True

    """
    if prices.empty or len(prices) < 2:
        return 0.0

    # Convert prices to returns for Empyrical
    returns = prices.pct_change().dropna()

    if returns.empty:
        return 0.0

    # Use Empyrical for max drawdown calculation
    from empyrical import max_drawdown as empyrical_max_drawdown

    max_dd = empyrical_max_drawdown(returns)

    return float(max_dd)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted return).

    Uses Empyrical-Reloaded for calculation.

    Sharpe ratio measures excess return per unit of risk (volatility).
    Higher values indicate better risk-adjusted performance.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 0.02 for 2%)

    Returns:
        Sharpe ratio as a float

    Examples:
        >>> returns = pd.Series([0.01, 0.02, 0.015, 0.01, 0.02])
        >>> sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0.02)
        >>> sharpe > 0
        True

    """
    if returns.empty:
        return 0.0

    # Use Empyrical for Sharpe ratio calculation
    from empyrical import sharpe_ratio as empyrical_sharpe

    sharpe = empyrical_sharpe(returns, risk_free=risk_free_rate, period="daily")

    return float(sharpe)


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sortino ratio (downside risk-adjusted return).

    Uses Empyrical-Reloaded for calculation.

    Similar to Sharpe ratio but only considers downside volatility,
    penalizing only negative returns rather than all volatility.

    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate (default 0.02 for 2%)

    Returns:
        Sortino ratio as a float

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
        >>> sortino = calculate_sortino_ratio(returns, risk_free_rate=0.02)
        >>> isinstance(sortino, float)
        True

    """
    if returns.empty:
        return 0.0

    # Use Empyrical for Sortino ratio calculation
    from empyrical import sortino_ratio as empyrical_sortino

    sortino = empyrical_sortino(returns, required_return=risk_free_rate, period="daily")

    return float(sortino)


def calculate_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta coefficient (systematic risk relative to market).

    Uses Empyrical-Reloaded for calculation.

    Beta measures how much an asset moves relative to the market.
    Beta = 1: moves with market, Beta > 1: more volatile, Beta < 1: less volatile

    Args:
        asset_returns: Series of asset returns
        market_returns: Series of market/benchmark returns

    Returns:
        Beta coefficient as a float

    Examples:
        >>> asset_returns = pd.Series([0.01, 0.02, -0.01, 0.015, 0.02])
        >>> market_returns = pd.Series([0.008, 0.015, -0.005, 0.01, 0.012])
        >>> beta = calculate_beta(asset_returns, market_returns)
        >>> beta > 0
        True

    """
    if asset_returns.empty or market_returns.empty:
        return 0.0

    # Use Empyrical for beta calculation

    # Empyrical's alpha_beta returns both, we just need beta
    from empyrical import alpha_beta

    _, beta_value = alpha_beta(asset_returns, market_returns, risk_free=0.0)

    return float(beta_value)
