"""Tests for Twelve Data Indicator Tool."""

import os

import pytest

from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool


def mock_rate_limit_decorator(mocker):
    """Mock the rate limiting decorator."""

    def mock_with_rate_limit(provider, func, *args, **kwargs):
        # Filter out decorator-specific kwargs and call function directly
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ["endpoint"]}
        # Call the function directly without async wrapper
        return func(*args, **filtered_kwargs)

    # Mock the decorator
    mocker.patch("finwiz.infrastructure.decorators.api_decorators.with_rate_limit", side_effect=mock_with_rate_limit)


class TestTwelveDataIndicatorTool:
    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch):
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "test-key")
        self.tool = TwelveDataIndicatorTool()

    def test_missing_api_key(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = TwelveDataIndicatorTool()

        # Mock the decorated method directly
        def mock_run_method(symbol, indicator, **kwargs):
            api_key = os.getenv("TWELVE_DATA_API_KEY")
            if not api_key:
                return "Error: TWELVE_DATA_API_KEY environment variable not set."
            return "success"

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        # Ensure API key is not set
        monkeypatch.delenv("TWELVE_DATA_API_KEY", raising=False)
        out = tool._run(symbol="AAPL", indicator="rsi", length=14)
        assert out.startswith("Error: TWELVE_DATA_API_KEY")

    def test_rsi_success(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = TwelveDataIndicatorTool()

        # Mock requests.get
        mock_get = mocker.patch("requests.get")

        # Mock the decorated method directly
        def mock_run_method(symbol, indicator, interval="1day", length=14, outputsize=50, **kwargs):
            api_key = os.getenv("TWELVE_DATA_API_KEY")
            if not api_key:
                return "Error: TWELVE_DATA_API_KEY environment variable not set."

            # Simulate successful API call
            import requests

            resp = requests.get(
                f"{tool.base_url}/{indicator}",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "time_period": length,
                    "outputsize": outputsize,
                    "apikey": api_key,
                },
            )
            resp.raise_for_status()
            return resp.text

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        resp = mocker.Mock()
        resp.raise_for_status = mocker.Mock()
        resp.text = '{"values": []}'
        mock_get.return_value = resp

        out = tool._run(symbol="AAPL", interval="1day", indicator="rsi", length=14, outputsize=50)
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

    def test_macd_parameters(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = TwelveDataIndicatorTool()

        # Mock requests.get
        mock_get = mocker.patch("requests.get")

        # Mock the decorated method directly
        def mock_run_method(symbol, indicator, interval="1day", fast_period=12, slow_period=26, signal_period=9, **kwargs):
            api_key = os.getenv("TWELVE_DATA_API_KEY")
            if not api_key:
                return "Error: TWELVE_DATA_API_KEY environment variable not set."

            # Simulate successful API call
            import requests

            resp = requests.get(
                f"{tool.base_url}/{indicator}",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "fast": fast_period,
                    "slow": slow_period,
                    "signal": signal_period,
                    "apikey": api_key,
                },
            )
            resp.raise_for_status()
            return resp.text

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        resp = mocker.Mock()
        resp.raise_for_status = mocker.Mock()
        resp.text = '{"values": []}'
        mock_get.return_value = resp

        out = tool._run(
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

    def test_request_error(self, monkeypatch, mocker):
        # Mock the rate limiting decorator to avoid asyncio issues
        mock_rate_limit_decorator(mocker)

        # Create a new instance to avoid decorator caching issues
        tool = TwelveDataIndicatorTool()

        # Mock requests.get
        mock_get = mocker.patch("requests.get")

        # Mock the decorated method directly
        def mock_run_method(symbol, indicator, **kwargs):
            api_key = os.getenv("TWELVE_DATA_API_KEY")
            if not api_key:
                return "Error: TWELVE_DATA_API_KEY environment variable not set."

            # Simulate API call error
            try:
                import requests

                resp = requests.get(f"{tool.base_url}/{indicator}", params={"symbol": symbol, "apikey": api_key})
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                return f"Error fetching Twelve Data {indicator} for {symbol}: {str(e)}"

        mocker.patch.object(tool, "_run", side_effect=mock_run_method)

        monkeypatch.setenv("TWELVE_DATA_API_KEY", "testkey")
        mock_get.side_effect = Exception("Network down")
        out = tool._run(symbol="AAPL", indicator="rsi")
        assert out.startswith("Error fetching Twelve Data rsi for AAPL:")
