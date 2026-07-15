"""Tests for centralized API endpoint configuration."""

from finwiz.config import endpoints


class TestEndpointDefaults:
    """Verify all endpoints have sensible defaults."""

    def test_alpha_vantage_base(self):
        assert endpoints.ALPHA_VANTAGE_BASE == "https://www.alphavantage.co/query"

    def test_twelve_data_base(self):
        assert endpoints.TWELVE_DATA_BASE == "https://api.twelvedata.com"

    def test_coingecko_base(self):
        assert endpoints.COINGECKO_BASE == "https://api.coingecko.com/api/v3"

    def test_perplexity_search(self):
        assert endpoints.PERPLEXITY_SEARCH == "https://api.perplexity.ai/search"

    def test_openai_base(self):
        assert endpoints.OPENAI_BASE == "https://api.openai.com/v1"

    def test_sec_edgar_base(self):
        assert endpoints.SEC_EDGAR_BASE == "https://www.sec.gov"

    def test_sec_efts_base(self):
        assert endpoints.SEC_EFTS_BASE == "https://efts.sec.gov/LATEST"

    def test_sec_data_base(self):
        assert endpoints.SEC_DATA_BASE == "https://data.sec.gov"

    def test_chart_img_base(self):
        assert endpoints.CHART_IMG_BASE == "https://api.chart-img.com/v1/stock"

    def test_yahoo_finance_web(self):
        assert endpoints.YAHOO_FINANCE_WEB == "https://finance.yahoo.com"


class TestEndpointEnvOverrides:
    """Verify environment variable overrides work."""

    def test_alpha_vantage_override(self, monkeypatch):
        monkeypatch.setenv("AV_BASE_URL", "https://custom.av.example.com")
        # Module-level constants are set at import time, so we reload
        import importlib

        importlib.reload(endpoints)
        assert endpoints.ALPHA_VANTAGE_BASE == "https://custom.av.example.com"
        # Clean up
        monkeypatch.delenv("AV_BASE_URL", raising=False)
        importlib.reload(endpoints)

    def test_twelve_data_override(self, monkeypatch):
        monkeypatch.setenv("TD_BASE_URL", "https://custom.td.example.com")
        import importlib

        importlib.reload(endpoints)
        assert endpoints.TWELVE_DATA_BASE == "https://custom.td.example.com"
        monkeypatch.delenv("TD_BASE_URL", raising=False)
        importlib.reload(endpoints)

    def test_unset_env_uses_default(self, monkeypatch):
        monkeypatch.delenv("AV_BASE_URL", raising=False)
        import importlib

        importlib.reload(endpoints)
        assert endpoints.ALPHA_VANTAGE_BASE == "https://www.alphavantage.co/query"
