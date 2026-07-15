"""Tests for Twelve Data Indicator Tool."""

import pytest
from crewai_custom_tools.core.results import err, ok

from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool


class TestTwelveDataIndicatorTool:
    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "test-key")
        self.tool = TwelveDataIndicatorTool()

    def test_missing_api_key(self, monkeypatch):
        """Fail-fast: missing TWELVE_DATA_API_KEY raises ValueError at construction."""
        monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)

        with pytest.raises(ValueError, match="TWELVE_DATA_API_KEY"):
            TwelveDataIndicatorTool()

    def test_rsi_success(self, mocker):
        mock_central_run = mocker.patch(
            "crewai_custom_tools.tools.finance.indicators.TwelveDataIndicatorTool._run",
            return_value=ok({"values": [{"datetime": "2025-01-01", "rsi": 65.5}]}),
        )

        out = self.tool._run(symbol="AAPL", interval="1day", indicator="rsi", length=14, outputsize=50)

        assert "values" in out
        assert "rsi" in out.lower()

        _, kwargs = mock_central_run.call_args
        assert kwargs["symbol"] == "AAPL"
        assert kwargs["indicator"] == "rsi"
        assert kwargs["interval"] == "1day"
        assert kwargs["length"] == 14
        assert kwargs["outputsize"] == 50

    def test_macd_parameters(self, mocker):
        mock_central_run = mocker.patch(
            "crewai_custom_tools.tools.finance.indicators.TwelveDataIndicatorTool._run",
            return_value=ok({"values": [{"datetime": "2025-01-01", "macd": 1.2}]}),
        )

        out = self.tool._run(
            symbol="AAPL",
            interval="1day",
            indicator="macd",
            fast_period=12,
            slow_period=26,
            signal_period=9,
        )

        assert "values" in out

        _, kwargs = mock_central_run.call_args
        assert kwargs["indicator"] == "macd"
        assert kwargs["fast_period"] == 12
        assert kwargs["slow_period"] == 26
        assert kwargs["signal_period"] == 9

    def test_request_error(self, mocker):
        """Central envelope failure surfaces via the existing outer catch-all."""
        mocker.patch(
            "crewai_custom_tools.tools.finance.indicators.TwelveDataIndicatorTool._run",
            return_value=err("Twelve Data: Network down"),
        )

        out = self.tool._run(symbol="AAPL", indicator="rsi")

        assert out.startswith("Error performing enhanced technical analysis for AAPL:")
        assert "Network down" in out
