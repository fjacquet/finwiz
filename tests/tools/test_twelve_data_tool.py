"""Tests for Twelve Data Indicator Tool."""

from unittest.mock import Mock, patch

from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool


class TestTwelveDataIndicatorTool:
    def setup_method(self):
        self.tool = TwelveDataIndicatorTool()

    def test_missing_api_key(self, monkeypatch):
        # Ensure API key is not set
        monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
        out = self.tool._run(symbol="AAPL", indicator="rsi", length=14)
        assert out.startswith("Error: TWELVE_DATA_API_KEY")

    @patch("requests.get")
    def test_rsi_success(self, mock_get, monkeypatch):
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.text = '{"values": []}'
        mock_get.return_value = resp

        out = self.tool._run(symbol="AAPL", interval="1day", indicator="rsi", length=14, outputsize=50)
        assert "values" in out

        # Verify request parameters
        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        assert called_url.endswith("/rsi")
        assert called_params["symbol"] == "AAPL"
        assert called_params["interval"] == "1day"
        assert called_params["time_period"] == 14
        assert called_params["outputsize"] == 50
        assert called_params["apikey"] == "testkey"

    @patch("requests.get")
    def test_macd_parameters(self, mock_get, monkeypatch):
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.text = '{"values": []}'
        mock_get.return_value = resp

        out = self.tool._run(
            symbol="AAPL",
            interval="1day",
            indicator="macd",
            fast_period=12,
            slow_period=26,
            signal_period=9,
        )
        assert "values" in out

        called_url = mock_get.call_args[0][0]
        called_params = mock_get.call_args[1]["params"]
        assert called_url.endswith("/macd")
        assert called_params["fast"] == 12
        assert called_params["slow"] == 26
        assert called_params["signal"] == 9

    @patch("requests.get")
    def test_request_error(self, mock_get, monkeypatch):
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        mock_get.side_effect = Exception("Network down")
        out = self.tool._run(symbol="AAPL", indicator="rsi")
        assert out.startswith("Error fetching Twelve Data rsi for AAPL:")
