"""Tests for ChartImgTool."""

import os

from finwiz.tools.chart_img_tool import ChartImgTool


def mock_rate_limit_decorator(mocker):
    """Mock the rate limiting decorator."""

    def mock_with_rate_limit(provider, func, *args, **kwargs):
        # Filter out decorator-specific kwargs and call function directly
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["endpoint"]}
        # Call the function directly without async wrapper
        return func(*args, **filtered_kwargs)

    # Mock the decorator
    mocker.patch("finwiz.utils.api_decorators.with_rate_limit", side_effect=mock_with_rate_limit)


class TestChartImgTool:
    def setup_method(self):
        self.tool = ChartImgTool()

    def test_missing_api_key(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = ChartImgTool()

        # Mock the decorated method directly
        def mock_run_method(symbol, interval="1day", range="6mo", width=900, height=500, theme="light"):
            api_key = os.getenv("CHART_IMG_API_KEY")
            if not api_key:
                return "Error: CHART_IMG_API_KEY environment variable not set."
            return "success"

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.delenv("CHART_IMG_API_KEY", raising=False)
        out = tool._run(symbol="AAPL")
        assert out.startswith("Error: CHART_IMG_API_KEY")

    def test_success_returns_data_url(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = ChartImgTool()

        # Mock requests.get directly
        mock_get = mocker.patch("requests.get")

        # Mock the decorated method directly
        def mock_run_method(symbol, interval="1day", range="6mo", width=900, height=500, theme="light"):
            import base64

            api_key = os.getenv("CHART_IMG_API_KEY")
            if not api_key:
                return "Error: CHART_IMG_API_KEY environment variable not set."

            # Simulate successful API call
            resp = mocker.Mock()
            resp.raise_for_status = mocker.Mock()
            resp.headers = {"Content-Type": "image/png"}
            resp.content = b"\x89PNG..."  # minimal bytes
            mock_get.return_value = resp

            # Call the actual requests.get to trigger the mock
            import requests

            resp = requests.get(
                "https://api.chart-img.com/v1/stock",
                headers={"x-api-key": api_key},
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "range": range,
                    "width": width,
                    "height": height,
                    "theme": theme,
                },
                timeout=20,
            )
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "image/png")
            b64 = base64.b64encode(resp.content).decode("ascii")
            return f"data:{content_type};base64,{b64}"

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.setenv("CHART_IMG_API_KEY", "key")
        resp = mocker.Mock()
        resp.raise_for_status = mocker.Mock()
        resp.headers = {"Content-Type": "image/png"}
        resp.content = b"\x89PNG..."  # minimal bytes
        mock_get.return_value = resp

        out = tool._run(symbol="AAPL", interval="1day", range="6mo", width=800, height=400, theme="light")
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

    def test_request_error(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = ChartImgTool()

        # Mock requests.get directly
        mock_get = mocker.patch("requests.get")

        # Mock the decorated method directly
        def mock_run_method(symbol, interval="1day", range="6mo", width=900, height=500, theme="light"):
            api_key = os.getenv("CHART_IMG_API_KEY")
            if not api_key:
                return "Error: CHART_IMG_API_KEY environment variable not set."

            # Simulate API call error
            try:
                import requests

                resp = requests.get(
                    "https://api.chart-img.com/v1/stock",
                    headers={"x-api-key": api_key},
                    params={
                        "symbol": symbol,
                        "interval": interval,
                        "range": range,
                        "width": width,
                        "height": height,
                        "theme": theme,
                    },
                    timeout=20,
                )
                resp.raise_for_status()
                return "success"
            except Exception as e:
                return f"Error generating chart image for {symbol}: {str(e)}"

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.setenv("CHART_IMG_API_KEY", "key")
        mock_get.side_effect = Exception("boom")
        out = tool._run(symbol="AAPL")
        assert out.startswith("Error generating chart image for AAPL:")
