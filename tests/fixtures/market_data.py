"""
Market data fixtures for testing.

Provides market context and price history data.
"""

from datetime import datetime
from typing import Any

import pandas as pd


def create_market_context(
    vix: float = 15.0,
    inflation: float = 2.5,
    interest_rate: float = 4.5,
    **overrides: Any,
) -> dict[str, Any]:
    """
    Create sample market context data.

    Args:
        vix: VIX volatility index (default: 15.0)
        inflation: Inflation rate % (default: 2.5)
        interest_rate: Risk-free rate % (default: 4.5)
        **overrides: Additional fields or overrides

    Returns:
        Dictionary with market context

    """
    data = {
        "vix": vix,
        "inflation": inflation,
        "interest_rate": interest_rate,
        "market_regime": "normal",
        "sentiment": "neutral",
        "economic_cycle": "expansion",
    }
    data.update(overrides)
    return data


def create_price_history(
    ticker: str = "AAPL",
    days: int = 252,
    start_price: float = 100.0,
    volatility: float = 0.20,
) -> pd.DataFrame:
    """
    Create sample price history DataFrame.

    Args:
        ticker: Ticker symbol (default: "AAPL")
        days: Number of trading days (default: 252 = 1 year)
        start_price: Starting price (default: 100.0)
        volatility: Daily volatility (default: 0.20)

    Returns:
        DataFrame with OHLCV data

    """
    import numpy as np

    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")

    # Generate random returns
    np.random.seed(42)
    returns = np.random.normal(0.0005, volatility / np.sqrt(252), days)

    # Calculate prices
    prices = start_price * (1 + returns).cumprod()

    # Generate OHLCV data
    df = pd.DataFrame(
        {
            "open": prices * (1 + np.random.uniform(-0.01, 0.01, days)),
            "high": prices * (1 + np.random.uniform(0.0, 0.02, days)),
            "low": prices * (1 + np.random.uniform(-0.02, 0.0, days)),
            "close": prices,
            "volume": np.random.randint(1e6, 10e6, days),
        },
        index=dates,
    )

    return df


def create_returns_series(
    days: int = 252,
    mean_return: float = 0.10,
    volatility: float = 0.20,
) -> pd.Series:
    """
    Create sample returns series.

    Args:
        days: Number of trading days (default: 252 = 1 year)
        mean_return: Annualized mean return (default: 0.10 = 10%)
        volatility: Annualized volatility (default: 0.20 = 20%)

    Returns:
        Series with daily returns

    """
    import numpy as np

    dates = pd.date_range(end=datetime.now(), periods=days, freq="B")

    # Generate random returns
    np.random.seed(42)
    daily_mean = mean_return / 252
    daily_vol = volatility / np.sqrt(252)
    returns = np.random.normal(daily_mean, daily_vol, days)

    return pd.Series(returns, index=dates)
