"""Tools testing fixtures."""

import pytest


@pytest.fixture
def mock_tool_context(mocker):
    """Mock tool execution context."""
    context = mocker.Mock()
    context.config = mocker.Mock()
    context.config.get.return_value = None
    return context


@pytest.fixture
def sample_ticker():
    """Standard test ticker."""
    return "AAPL"


@pytest.fixture
def sample_tool_input():
    """Sample tool input data."""
    return {
        "ticker": "AAPL",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
    }
