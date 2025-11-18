"""Crew testing fixtures."""

import pytest


@pytest.fixture
def mock_crew_config(mocker):
    """Mock crew configuration."""
    return {
        "analyst": {
            "role": "Financial Analyst",
            "goal": "Analyze financial data",
            "backstory": "Expert financial analyst",
        },
        "researcher": {
            "role": "Research Specialist",
            "goal": "Research market data",
            "backstory": "Expert researcher",
        },
    }


@pytest.fixture
def mock_task_config(mocker):
    """Mock task configuration."""
    return {
        "analysis_task": {
            "description": "Analyze {ticker}",
            "expected_output": "Comprehensive analysis",
            "agent": "analyst",
        },
        "research_task": {
            "description": "Research {ticker}",
            "expected_output": "Research findings",
            "agent": "researcher",
        },
    }


@pytest.fixture
def sample_crew_inputs():
    """Sample crew input data."""
    return {
        "ticker": "AAPL",
        "asset_class": "stock",
        "analysis_type": "comprehensive",
    }
