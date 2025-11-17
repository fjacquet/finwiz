"""
Mock factories for testing.

Provides pytest fixtures to create mock objects for common test scenarios.
Uses pytest-mock exclusively (NO unit test mock allowed per FinWiz standards).
"""

from typing import Any

import pytest


@pytest.fixture
def mock_api_response(mocker):
    """
    Fixture factory for creating mock API responses.

    Returns:
        Factory function that creates mock API response objects

    Example:
        def test_api_call(mock_api_response):
            response = mock_api_response(data={"result": "success"})
            assert response.status_code == 200

    """

    def _factory(
        data: dict[str, Any] | None = None,
        status_code: int = 200,
        error: str | None = None,
    ):
        """
        Create a mock API response.

        Args:
            data: Response data (default: empty dict)
            status_code: HTTP status code (default: 200)
            error: Error message if any (default: None)

        Returns:
            Mock API response object

        """
        mock_response = mocker.Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data or {}
        mock_response.text = str(data or {})

        if error:
            mock_response.raise_for_status.side_effect = Exception(error)
        else:
            mock_response.raise_for_status.return_value = None

        return mock_response

    return _factory


def create_mock_tool_result(
    success: bool = True,
    data: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """
    Create a mock tool execution result.

    Args:
        success: Whether tool execution succeeded (default: True)
        data: Tool output data (default: empty dict)
        error: Error message if any (default: None)

    Returns:
        Dictionary with tool result

    """
    result = {
        "success": success,
        "data": data or {},
    }

    if error:
        result["error"] = error

    return result


@pytest.fixture
def mock_crew_result(mocker):
    """
    Fixture factory for creating mock CrewAI crew results.

    Returns:
        Factory function that creates mock crew result objects

    Example:
        def test_crew(mock_crew_result):
            result = mock_crew_result(raw="Analysis complete")
            assert result.raw == "Analysis complete"

    """

    def _factory(
        raw: str = "Analysis complete",
        pydantic: Any | None = None,
        json_dict: dict[str, Any] | None = None,
    ):
        """
        Create a mock CrewAI crew result.

        Args:
            raw: Raw output string (default: "Analysis complete")
            pydantic: Pydantic model instance (default: None)
            json_dict: JSON dictionary output (default: None)

        Returns:
            Mock crew result object

        """
        mock_result = mocker.Mock()
        mock_result.raw = raw
        mock_result.pydantic = pydantic
        mock_result.json_dict = json_dict or {}

        return mock_result

    return _factory


@pytest.fixture
def mock_yfinance_ticker(mocker):
    """
    Fixture factory for creating mock yfinance Ticker objects.

    Returns:
        Factory function that creates mock yfinance Ticker objects

    Example:
        def test_ticker(mock_yfinance_ticker):
            ticker = mock_yfinance_ticker(ticker="AAPL")
            assert ticker.info["symbol"] == "AAPL"

    """

    def _factory(
        ticker: str = "AAPL",
        info: dict[str, Any] | None = None,
        history: Any | None = None,
    ):
        """
        Create a mock yfinance Ticker object.

        Args:
            ticker: Ticker symbol (default: "AAPL")
            info: Ticker info dictionary (default: basic info)
            history: Price history DataFrame (default: None)

        Returns:
            Mock yfinance Ticker object

        """
        mock_ticker = mocker.Mock()
        mock_ticker.ticker = ticker

        # Default info
        default_info = {
            "symbol": ticker,
            "longName": f"{ticker} Inc.",
            "currentPrice": 150.0,
            "marketCap": 2.5e12,
            "trailingPE": 25.0,
            "forwardPE": 22.0,
            "dividendYield": 0.005,
            "beta": 1.2,
            "fiftyTwoWeekHigh": 180.0,
            "fiftyTwoWeekLow": 120.0,
        }
        mock_ticker.info = info or default_info

        if history is not None:
            mock_ticker.history.return_value = history

        return mock_ticker

    return _factory


@pytest.fixture
def mock_supabase_client(mocker):
    """
    Fixture for creating mock Supabase client.

    Returns:
        Mock Supabase client with common methods

    Example:
        def test_supabase(mock_supabase_client):
            client = mock_supabase_client
            result = client.table("test").select("*").execute()
            assert result.data == []

    """
    mock_client = mocker.Mock()

    # Mock table operations
    mock_table = mocker.Mock()
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.execute.return_value = mocker.Mock(data=[], error=None)

    mock_client.table.return_value = mock_table
    mock_client.from_.return_value = mock_table

    return mock_client
