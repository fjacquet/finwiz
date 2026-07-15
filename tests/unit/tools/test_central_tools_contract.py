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
