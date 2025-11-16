"""
Test fixtures for FinWiz test suite.

Provides reusable test data, mocks, and factories to reduce duplication
and speed up test development.

IMPORTANT: Mock fixtures (mock_api_response, mock_crew_result, etc.) are now
pytest fixtures defined in mock_factories.py. They are automatically available
via conftest.py and should be used as fixture arguments in test functions.
"""

from tests.fixtures.asset_data import (
    create_crypto_data,
    create_etf_data,
    create_risk_data,
    create_stock_data,
    create_technical_data,
)
from tests.fixtures.market_data import (
    create_market_context,
    create_price_history,
    create_returns_series,
)
from tests.fixtures.mock_factories import (
    create_mock_tool_result,
)
from tests.fixtures.schema_fixtures import (
    create_deep_analysis_result,
    create_holding_decision,
    create_portfolio_review,
    create_risk_assessment,
)

__all__ = [
    # Asset data
    "create_stock_data",
    "create_etf_data",
    "create_crypto_data",
    "create_technical_data",
    "create_risk_data",
    # Market data
    "create_market_context",
    "create_price_history",
    "create_returns_series",
    # Mock factories (plain data)
    "create_mock_tool_result",
    # NOTE: mock_api_response, mock_crew_result, mock_yfinance_ticker,
    # and mock_supabase_client are pytest fixtures - use them as test arguments
    # Schema fixtures
    "create_deep_analysis_result",
    "create_portfolio_review",
    "create_risk_assessment",
    "create_holding_decision",
]
