"""Tests for Alpha Vantage Company Overview Tool."""

import json

import pytest
from crewai_custom_tools.core.results import err, ok

from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool

_CENTRAL_RUN_PATH = "crewai_custom_tools.tools.finance.market_data.AlphaVantageOverviewTool._run"


class TestAlphaVantageCompanyOverviewTool:
    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")
        self.tool = AlphaVantageCompanyOverviewTool()

    def test_missing_api_key(self, monkeypatch):
        """Fail-fast: missing ALPHA_VANTAGE_API_KEY raises ValueError at construction."""
        monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)

        with pytest.raises(ValueError, match="ALPHA_VANTAGE_API_KEY"):
            AlphaVantageCompanyOverviewTool()

    def test_fetch_company_overview_maps_central_payload(self, mocker):
        """Central's lowercase overview keys are remapped onto the PascalCase
        keys `_format_enhanced_overview_response` reads."""
        mock_central_run = mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "return_on_equity_ttm": 1.5,
                    "debt_to_equity_ratio": 1.9,
                    "quarterly_revenue_growth_yoy": 0.08,
                    "profit_margin": 0.25,
                    "pe_ratio": 30.2,
                    "dividend_yield": 0.005,
                    "source": "AlphaVantage",
                }
            ),
        )

        out = self.tool._fetch_company_overview("AAPL")
        data = json.loads(out)

        assert data["Symbol"] == "AAPL"
        assert data["Name"] == "Apple Inc"
        assert data["PERatio"] == 30.2
        assert data["ProfitMargin"] == 0.25
        assert data["DividendYield"] == 0.005
        assert data["ReturnOnEquityTTM"] == 1.5
        assert data["DebtToEquityRatio"] == 1.9

        _, kwargs = mock_central_run.call_args
        assert kwargs["ticker"] == "AAPL"

    def test_run_formats_markdown_from_central_data(self, mocker):
        mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "pe_ratio": 30.2,
                    "profit_margin": 0.25,
                    "dividend_yield": 0.005,
                }
            ),
        )
        mocker.patch.object(self.tool, "_get_perplexity_integration", return_value=None)

        out = self.tool._run(ticker="AAPL", include_perplexity=False)

        assert "Enhanced Company Overview for AAPL" in out
        assert "**Company**: Apple Inc" in out
        assert "**P/E Ratio**: 30.2" in out
        assert "**Profit Margin**: 0.25" in out
        # Fields central does not fetch fall back to the renderer's own "N/A" default.
        assert "**Sector**: N/A" in out
        assert "**Industry**: N/A" in out
        assert "**Market Cap**: N/A" in out
        assert "**EPS**: N/A" in out

    def test_run_formats_markdown_with_v051_overview_fields(self, mocker):
        """v0.5.1: central fetches Sector, Industry, MarketCapitalization, EPS,
        RevenueTTM, and Description — the renderer must surface them instead
        of falling back to "N/A"."""
        mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc",
                    "pe_ratio": 30.2,
                    "profit_margin": 0.25,
                    "dividend_yield": 0.005,
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "market_cap": 2800000000000,
                    "eps": 6.13,
                    "revenue_ttm": 383285000000,
                    "description": "Apple Inc designs, manufactures, and markets smartphones.",
                }
            ),
        )
        mocker.patch.object(self.tool, "_get_perplexity_integration", return_value=None)

        out = self.tool._run(ticker="AAPL", include_perplexity=False)

        assert "**Sector**: Technology" in out
        assert "**Industry**: Consumer Electronics" in out
        assert "**Market Cap**: 2800000000000" in out
        assert "**EPS**: 6.13" in out
        assert "**Revenue (TTM)**: 383285000000" in out
        assert "**Description**: Apple Inc designs" in out

    def test_run_formats_markdown_handles_sparse_payload_without_literal_none(self, mocker):
        """Sparse AV data (central returns explicit None for nullable fields, not
        the raw "None"/"-" sentinel). The renderer must coalesce every mapped
        nullable field to "N/A" and never render the literal substring "None"."""
        mocker.patch(
            _CENTRAL_RUN_PATH,
            return_value=ok(
                {
                    "symbol": "SPARSE",
                    "name": "Sparse Corp",
                    "pe_ratio": None,
                    "profit_margin": None,
                    "dividend_yield": None,
                    "sector": None,
                    "industry": None,
                    "market_cap": None,
                    "eps": None,
                    "revenue_ttm": None,
                    "description": None,
                }
            ),
        )
        mocker.patch.object(self.tool, "_get_perplexity_integration", return_value=None)

        out = self.tool._run(ticker="SPARSE", include_perplexity=False)

        assert "**P/E Ratio**: N/A" in out
        assert "**Profit Margin**: N/A" in out
        assert "**Dividend Yield**: N/A" in out
        assert "**Sector**: N/A" in out
        assert "**Industry**: N/A" in out
        assert "**Market Cap**: N/A" in out
        assert "**EPS**: N/A" in out
        assert "**Revenue (TTM)**: N/A" in out
        assert "None" not in out

    def test_run_surfaces_central_failure_via_outer_catch_all(self, mocker):
        """Central envelope failure surfaces via the existing outer catch-all,
        matching the TwelveData wrapper's established error-propagation pattern."""
        mocker.patch(_CENTRAL_RUN_PATH, return_value=err("No data returned for ticker BADTICKER"))
        mocker.patch.object(self.tool, "_get_perplexity_integration", return_value=None)

        out = self.tool._run(ticker="BADTICKER", include_perplexity=False)

        assert out.startswith("Error performing enhanced company overview analysis for BADTICKER:")
        assert "No data returned for ticker BADTICKER" in out

    def test_run_uses_prefetched_data_short_circuit(self, mocker):
        """The prefetched_data batch short-circuit bypasses the central delegation entirely."""
        mock_central_run = mocker.patch(_CENTRAL_RUN_PATH)
        mocker.patch.object(self.tool, "_get_perplexity_integration", return_value=None)

        prefetched = {"AAPL": {"Symbol": "AAPL", "Name": "Apple Inc", "PERatio": "28.5"}}
        out = self.tool._run(ticker="AAPL", include_perplexity=False, prefetched_data=prefetched)

        assert "**Company**: Apple Inc" in out
        mock_central_run.assert_not_called()
