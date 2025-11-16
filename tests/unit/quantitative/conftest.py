"""Quantitative testing fixtures."""

import pandas as pd
import pytest


@pytest.fixture
def sample_returns():
    """Sample return series for quantitative tests."""
    return pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])


@pytest.fixture
def sample_prices(fake):
    """Generate realistic price data using Faker."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    returns = [
        fake.random_element([0.01, -0.01, 0.02, -0.02, 0.00]) for _ in range(100)
    ]
    prices = 100 * (1 + pd.Series(returns)).cumprod()
    return pd.Series(prices.values, index=dates)


@pytest.fixture
def mock_backtrader_cerebro(mocker):
    """Mock Backtrader Cerebro instance."""
    cerebro = mocker.Mock()
    cerebro.run.return_value = [mocker.Mock()]
    cerebro.broker.getvalue.return_value = 110000.0
    return cerebro


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "holdings": [
            {"ticker": "AAPL", "shares": 100, "cost_basis": 150.0},
            {"ticker": "MSFT", "shares": 50, "cost_basis": 250.0},
            {"ticker": "GOOGL", "shares": 25, "cost_basis": 2000.0},
        ],
        "cash": 10000.0,
        "total_value": 60000.0,
    }
