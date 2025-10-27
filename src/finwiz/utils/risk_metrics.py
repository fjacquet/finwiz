"""
Risk Metrics Calculation Module.

This module provides risk calculation functions for financial analysis including
volatility, Value at Risk (VaR), Conditional VaR (CVaR), Sharpe ratio, Sortino ratio,
maximum drawdown, and beta coefficient.

All functions accept pandas Series and return calculated metrics.
"""

import numpy as np
import pandas as pd


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate historical volatility (standard deviation of returns).

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

    volatility = returns.std()

    if annualize:
        # Assume 252 trading days per year
        volatility = volatility * np.sqrt(252)

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

    # Calculate cumulative maximum (running peak)
    cumulative_max = prices.expanding().max()

    # Calculate drawdown at each point
    drawdown = (prices - cumulative_max) / cumulative_max

    # Maximum drawdown is the minimum value (most negative)
    max_drawdown = drawdown.min()

    return float(max_drawdown)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted return).

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

    # Calculate annualized return
    mean_return = returns.mean() * 252  # Annualize daily returns

    # Calculate annualized volatility
    volatility = calculate_volatility(returns, annualize=True)

    if volatility == 0:
        return 0.0

    # Sharpe ratio = (return - risk_free_rate) / volatility
    sharpe_ratio = (mean_return - risk_free_rate) / volatility

    return float(sharpe_ratio)


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sortino ratio (downside risk-adjusted return).

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

    # Calculate annualized return
    mean_return = returns.mean() * 252

    # Calculate downside deviation (only negative returns)
    downside_returns = returns[returns < 0]

    if downside_returns.empty:
        # No downside risk - return a high value
        return float("inf") if mean_return > risk_free_rate else 0.0

    downside_deviation = downside_returns.std() * np.sqrt(252)

    if downside_deviation == 0:
        return 0.0

    # Sortino ratio = (return - risk_free_rate) / downside_deviation
    sortino_ratio = (mean_return - risk_free_rate) / downside_deviation

    return float(sortino_ratio)


def calculate_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta coefficient (systematic risk relative to market).

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

    # Align the series (in case they have different indices)
    aligned_data = pd.DataFrame({"asset": asset_returns, "market": market_returns}).dropna()

    if len(aligned_data) < 2:
        return 0.0

    # Calculate covariance and variance
    covariance = aligned_data["asset"].cov(aligned_data["market"])
    market_variance = aligned_data["market"].var()

    if market_variance == 0:
        return 0.0

    # Beta = Cov(asset, market) / Var(market)
    beta = covariance / market_variance

    return float(beta)
