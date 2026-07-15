"""Contract tests for the crewai-custom-tools seam (Wave 1).

These pin the parts of the central package finwiz depends on: factory
composition, the ToolResult envelope, and fail-fast key validation.
"""

import pytest
from crewai_custom_tools import PerplexitySearchTool
from crewai_custom_tools.core.results import ToolResultError, err, ok, parse_tool_result

from finwiz.tools.finance_tools import get_etf_research_tools, get_stock_research_tools


def test_stock_bundle_contains_central_yahoo_tools():
    names = {tool.name for tool in get_stock_research_tools()}
    assert {"Yahoo Finance Ticker Info Tool", "Yahoo Finance History Tool", "Yahoo Finance Company Info Tool", "Yahoo Finance News Tool"} <= names


def test_etf_bundle_contains_holdings_tool():
    names = {tool.name for tool in get_etf_research_tools()}
    assert "Yahoo Finance ETF Holdings Tool" in names


def test_envelope_roundtrip():
    assert parse_tool_result(ok({"price": 1.5})) == {"price": 1.5}
    with pytest.raises(ToolResultError, match="boom"):
        parse_tool_result(err("boom"))


def test_perplexity_fails_fast_without_key(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    with pytest.raises(ValueError):
        PerplexitySearchTool()


def test_safe_init_skips_keyless_tools(monkeypatch):
    from finwiz.tools.finance_tools import _safe_init

    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    assert _safe_init(PerplexitySearchTool) is None


def test_crypto_bundle_has_real_defi_tool():
    from finwiz.tools.finance_tools import get_crypto_research_tools

    # Central's DeFiMetricsTool.name is the lowercase "defi_metrics" (v0.5.1);
    # matched case-insensitively so this doesn't pin to that exact casing.
    names = {tool.name for tool in get_crypto_research_tools()}
    assert any("defi" in name.lower() for name in names)


def test_risk_scoring_is_central():
    from crewai_custom_tools import StandardizedRiskScoringTool

    from finwiz.tools.finance_tools import get_stock_research_tools

    assert any(isinstance(tool, StandardizedRiskScoringTool) for tool in get_stock_research_tools())


def test_stock_crew_bundle_contains_central_valuation_tool():
    from crewai_custom_tools import ValuationTool

    from finwiz.tools.tool_factories import get_stock_crew_tools

    assert any(isinstance(tool, ValuationTool) for tool in get_stock_crew_tools())


def test_discovery_bundle_contains_central_aplus_screening_tool():
    from crewai_custom_tools.tools.analytics.aplus_screening import APlusScreeningTool

    from finwiz.tools.finance_tools import get_investment_discovery_tools

    assert any(isinstance(tool, APlusScreeningTool) for tool in get_investment_discovery_tools())


def test_file_tools_come_from_central_package():
    from crewai_custom_tools import DirectoryReadTool, FileReadTool

    assert FileReadTool().name
    assert DirectoryReadTool().name


def test_central_require_api_key_raises_on_missing_env(monkeypatch):
    """Pins Task 2's key-validation dependency: require_api_key is importable
    and fails fast with ValueError when none of its env vars are set."""
    from crewai_custom_tools.core.keys import require_api_key

    monkeypatch.delenv("SOME_MISSING_API_KEY", raising=False)
    with pytest.raises(ValueError, match="SOME_MISSING_API_KEY"):
        require_api_key("SOME_MISSING_API_KEY", tool_name="TestTool")


def test_central_require_api_key_returns_first_set_value(monkeypatch):
    from crewai_custom_tools.core.keys import require_api_key

    monkeypatch.setenv("SOME_TEST_API_KEY", "secret-value")
    assert require_api_key("SOME_TEST_API_KEY", tool_name="TestTool") == "secret-value"


def test_central_rate_limiter_registry_has_yahoo_and_alpha_vantage():
    """Pins Task 1's rate-limiter dependency: the central registry knows about
    the providers finwiz relies on for throttling."""
    from crewai_custom_tools.core.rate_limiter import DEFAULT_RATE_LIMITS

    assert "YahooFinance" in DEFAULT_RATE_LIMITS
    assert "AlphaVantage" in DEFAULT_RATE_LIMITS
    assert DEFAULT_RATE_LIMITS["YahooFinance"].requests_per_minute > 0
    assert DEFAULT_RATE_LIMITS["AlphaVantage"].requests_per_minute > 0
