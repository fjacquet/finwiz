"""Tests for ChartImgTool."""

from unittest.mock import Mock, patch

from finwiz.tools.chart_img_tool import ChartImgTool


class TestChartImgTool:
    def setup_method(self):
        self.tool = ChartImgTool()

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("CHART_IMG_API_KEY", raising=False)
        out = self.tool._run(symbol="AAPL")
        assert out.startswith("Error: CHART_IMG_API_KEY")

    @patch("requests.get")
    def test_success_returns_data_url(self, mock_get, monkeypatch):
        monkeypatch.setenv("CHART_IMG_API_KEY", "key")
        resp = Mock()
        resp.raise_for_status = Mock()
        resp.headers = {"Content-Type": "image/png"}
        resp.content = b"\x89PNG..."  # minimal bytes
        mock_get.return_value = resp

        out = self.tool._run(
            symbol="AAPL", interval="1day", range="6mo", width=800, height=400, theme="light"
        )
        assert out.startswith("data:image/png;base64,")

        called_url = mock_get.call_args[0][0]
        called_headers = mock_get.call_args[1]["headers"]
        called_params = mock_get.call_args[1]["params"]
        assert "chart-img" in called_url
        assert called_headers["x-api-key"] == "key"
        assert called_params["symbol"] == "AAPL"
        assert called_params["interval"] == "1day"
        assert called_params["range"] == "6mo"
        assert called_params["width"] == 800
        assert called_params["height"] == 400
        assert called_params["theme"] == "light"

    @patch("requests.get")
    def test_request_error(self, mock_get, monkeypatch):
        monkeypatch.setenv("CHART_IMG_API_KEY", "key")
        mock_get.side_effect = Exception("boom")
        out = self.tool._run(symbol="AAPL")
        assert out.startswith("Error generating chart image for AAPL:")
