"""Unit tests for v4 endpoint constants (Finnhub, Fear & Greed)."""

from finwiz.config import endpoints


class TestV4Endpoints:
    """Verify new endpoint constants exist and have correct defaults."""

    def test_finnhub_base_default(self):
        assert endpoints.FINNHUB_BASE == "https://finnhub.io/api/v1"

    def test_fear_greed_base_default(self):
        assert endpoints.FEAR_GREED_BASE == "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    def test_finnhub_base_env_override(self, mocker):
        mocker.patch.dict("os.environ", {"FINNHUB_BASE_URL": "https://custom.finnhub.io"})
        # Endpoints are module-level, so we reload to test env override
        import importlib

        importlib.reload(endpoints)
        assert endpoints.FINNHUB_BASE == "https://custom.finnhub.io"
        # Reload again to restore default
        mocker.patch.dict("os.environ", {}, clear=True)
        importlib.reload(endpoints)
