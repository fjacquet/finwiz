"""
Pytest configuration and shared fixtures.

Makes test fixtures available to all test modules.
"""

from datetime import datetime
from typing import Any

import pytest
from faker import Faker

# Import all fixtures to make them available
from tests.fixtures import (
    create_crypto_data,
    create_deep_analysis_result,
    create_etf_data,
    create_market_context,
    create_portfolio_review,
    create_price_history,
    create_risk_assessment,
    create_stock_data,
)


# Make fixtures available as pytest fixtures
@pytest.fixture
def stock_data():
    """Fixture providing sample stock data."""
    return create_stock_data()


@pytest.fixture
def etf_data():
    """Fixture providing sample ETF data."""
    return create_etf_data()


@pytest.fixture
def crypto_data():
    """Fixture providing sample crypto data."""
    return create_crypto_data()


@pytest.fixture
def market_context():
    """Fixture providing sample market context."""
    return create_market_context()


@pytest.fixture
def price_history():
    """Fixture providing sample price history."""
    return create_price_history()


@pytest.fixture
def risk_assessment():
    """Fixture providing sample risk assessment."""
    return create_risk_assessment()


@pytest.fixture
def deep_analysis_result():
    """Fixture providing sample deep analysis result."""
    return create_deep_analysis_result()


@pytest.fixture
def portfolio_review():
    """Fixture providing sample portfolio review."""
    return create_portfolio_review()


# ===== Faker-based fixtures =====


@pytest.fixture(scope="session")
def fake():
    """Faker instance for generating test data."""
    return Faker()


@pytest.fixture
def fake_client_profile(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic client profile data."""
    return {
        "name": fake.name(),
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address(),
        "city": fake.city(),
        "country": fake.country(),
        "date_of_birth": fake.date_of_birth(minimum_age=25, maximum_age=70).isoformat(),
        "risk_tolerance": fake.random_element(elements=("conservative", "moderate", "aggressive")),
        "investment_goals": fake.sentence(nb_words=10),
        "annual_income": fake.random_int(min=30000, max=500000),
        "net_worth": fake.random_int(min=50000, max=5000000),
    }


@pytest.fixture
def fake_timestamps(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic timestamp data."""
    return {
        "created_at": fake.past_datetime(start_date="-30d").isoformat(),
        "updated_at": fake.date_time_between(start_date="-7d", end_date="now").isoformat(),
        "last_analysis": fake.date_time_between(start_date="-3d", end_date="now").isoformat(),
    }


@pytest.fixture
def fake_portfolio_holdings(fake: Faker) -> list[dict[str, Any]]:
    """Fixture providing realistic portfolio holdings data."""
    holdings = []
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]
    for ticker in fake.random_elements(elements=tickers, length=5, unique=True):
        holdings.append(
            {
                "ticker": ticker,
                "shares": fake.random_int(min=1, max=1000),
                "purchase_price": round(fake.random.uniform(10.0, 500.0), 2),
                "current_price": round(fake.random.uniform(10.0, 500.0), 2),
                "purchase_date": fake.past_date(start_date="-2y").isoformat(),
            }
        )
    return holdings


@pytest.fixture
def fake_investment_recommendations(fake: Faker) -> list[dict[str, Any]]:
    """Fixture providing realistic investment recommendations."""
    recommendations = []
    for _ in range(3):
        recommendations.append(
            {
                "ticker": fake.random_element(elements=("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA")),
                "action": fake.random_element(elements=("BUY", "HOLD", "SELL")),
                "target_price": round(fake.random.uniform(100.0, 500.0), 2),
                "confidence": fake.random.uniform(0.6, 0.95),
                "rationale": fake.sentence(nb_words=15),
            }
        )
    return recommendations


@pytest.fixture
def fake_financial_data(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic financial data."""
    return {
        "revenue": fake.random_int(min=1000000, max=100000000),
        "net_income": fake.random_int(min=100000, max=10000000),
        "total_assets": fake.random_int(min=5000000, max=500000000),
        "total_liabilities": fake.random_int(min=2000000, max=200000000),
        "eps": round(fake.random.uniform(1.0, 50.0), 2),
        "pe_ratio": round(fake.random.uniform(10.0, 40.0), 2),
        "dividend_yield": round(fake.random.uniform(0.0, 5.0), 2),
    }


@pytest.fixture
def fake_stock_data(fake: Faker) -> dict[str, Any]:
    """Fixture providing realistic stock data."""
    return {
        "ticker": fake.random_element(elements=("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA")),
        "company_name": fake.company(),
        "sector": fake.random_element(elements=("Technology", "Finance", "Healthcare", "Energy")),
        "market_cap": fake.random_int(min=1000000000, max=3000000000000),
        "price": round(fake.random.uniform(10.0, 500.0), 2),
        "volume": fake.random_int(min=1000000, max=100000000),
        "change_percent": round(fake.random.uniform(-10.0, 10.0), 2),
    }


@pytest.fixture
def fake_data_generator(fake: Faker):
    """Fixture providing a data generator function."""

    def generate(data_type: str, count: int = 1):
        if data_type == "stock":
            return [fake_stock_data.__wrapped__(fake) for _ in range(count)]
        elif data_type == "client":
            return [fake_client_profile.__wrapped__(fake) for _ in range(count)]
        else:
            return []

    return generate


@pytest.fixture
def sample_output() -> dict[str, Any]:
    """Fixture providing sample crew output data."""
    return {
        "crew_name": "stock_crew",
        "timestamp": datetime.now().isoformat(),
        "status": "success",
        "raw_output": "Comprehensive stock analysis completed successfully.",
        "pydantic": {
            "ticker": "AAPL",
            "composite_score": 0.85,
            "grade": "A-",
            "recommendation": "BUY",
        },
        "tasks_output": [
            {
                "name": "analysis_task",
                "description": "Analyze stock fundamentals",
                "raw": "Apple Inc. shows strong fundamentals with consistent revenue growth.",
            }
        ],
    }
