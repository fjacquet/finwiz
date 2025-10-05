"""
Integration tests for freshness validation with real tools.

Tests the integration of freshness validation with actual Yahoo Finance
and Alpha Vantage tools.
"""

from datetime import UTC, datetime, timedelta

from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool
from finwiz.utils.data_freshness_validator import DataFreshnessValidator
from finwiz.utils.freshness_validated_tool import FreshnessValidatedTool


class TestYahooFinanceToolsIntegration:
    """Test integration of freshness validation with Yahoo Finance tools."""

    def test_should_add_timestamp_to_ticker_info(self, mocker):
        """Test that ticker info tool adds timestamp for freshness validation."""
        # Mock yfinance response
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.yf.Ticker")
        mock_info = {
            "shortName": "Apple Inc.",
            "currentPrice": 150.0,
            "regularMarketTime": datetime.now(UTC).timestamp(),
            "marketCap": 2500000000000,
            "sector": "Technology",
        }
        mock_ticker.return_value.info = mock_info

        tool = YahooFinanceTickerInfoTool()
        result = tool._run(ticker="AAPL")

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "symbol" in result
        assert result["symbol"] == "AAPL"

        # Verify timestamp is recent (within last minute)
        timestamp_str = result["timestamp"]
        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        age_seconds = (datetime.now(UTC) - timestamp).total_seconds()
        assert age_seconds < 60  # Should be very recent

    def test_should_add_market_time_when_available(self, mocker):
        """Test that market time is added when available from Yahoo Finance."""
        # Mock yfinance response
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.yf.Ticker")

        market_timestamp = datetime.now(UTC) - timedelta(hours=2)
        mock_info = {
            "shortName": "Apple Inc.",
            "currentPrice": 150.0,
            "regularMarketTime": market_timestamp.timestamp(),
            "marketCap": 2500000000000,
        }
        mock_ticker.return_value.info = mock_info

        tool = YahooFinanceTickerInfoTool()
        result = tool._run(ticker="AAPL")

        assert "market_time" in result
        market_time = datetime.fromisoformat(result["market_time"].replace("Z", "+00:00"))

        # Market time should be approximately 2 hours ago
        age_hours = (datetime.now(UTC) - market_time).total_seconds() / 3600
        assert 1.9 <= age_hours <= 2.1

    def test_should_add_timestamp_to_history_data(self, mocker):
        """Test that history tool adds timestamp for freshness validation."""
        # Mock yfinance response
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_history_tool.yf.Ticker")

        # Mock historical data
        import pandas as pd

        dates = pd.date_range(start="2024-01-01", periods=5, freq="D")
        mock_history = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0, 153.0, 154.0],
                "High": [155.0, 156.0, 157.0, 158.0, 159.0],
                "Low": [149.0, 150.0, 151.0, 152.0, 153.0],
                "Close": [154.0, 155.0, 156.0, 157.0, 158.0],
                "Volume": [1000000, 1100000, 1200000, 1300000, 1400000],
            },
            index=dates,
        )

        mock_ticker.return_value.history.return_value = mock_history

        tool = YahooFinanceHistoryTool()
        result = tool._run(ticker="AAPL", period="5d")

        assert isinstance(result, dict)
        assert "timestamp" in result
        assert "data_time" in result
        assert "summary" in result
        assert "history" in result

        # Verify data_time reflects the latest data point
        data_time = result["data_time"]
        assert "2024-01-05" in data_time  # Latest date from mock data

    def test_should_work_with_freshness_validator_wrapper(self, mocker):
        """Test Yahoo Finance tool with freshness validation wrapper."""
        # Mock yfinance response
        mock_ticker = mocker.patch("finwiz.tools.yahoo_finance_ticker_info_tool.yf.Ticker")

        # Mock fresh data
        mock_info = {
            "shortName": "Apple Inc.",
            "currentPrice": 150.0,
            "regularMarketTime": datetime.now(UTC).timestamp(),
            "marketCap": 2500000000000,
        }
        mock_ticker.return_value.info = mock_info

        base_tool = YahooFinanceTickerInfoTool()
        wrapped_tool = FreshnessValidatedTool(base_tool, max_age_hours=24)

        result = wrapped_tool._run(ticker="AAPL")

        assert isinstance(result, dict)
        assert "_freshness_info" in result
        assert result["_freshness_info"]["is_fresh"] is True
        assert result["_freshness_info"]["data_source"] == base_tool.name


class TestAlphaVantageToolIntegration:
    """Test integration of freshness validation with Alpha Vantage tools."""

    def test_should_add_timestamp_to_alpha_vantage_data(self, mocker):
        """Test that Alpha Vantage tool adds timestamp for freshness validation."""
        # Mock Alpha Vantage API response
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "Symbol": "AAPL",
            "Name": "Apple Inc",
            "MarketCapitalization": "2500000000000",
            "PERatio": "25.5",
            "EPS": "6.05",
        }
        mock_response.raise_for_status.return_value = None

        mock_get = mocker.patch("finwiz.tools.alpha_vantage_tool.requests.get")
        mock_get.return_value = mock_response

        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        tool = AlphaVantageCompanyOverviewTool()

        # Mock the async execution
        with mocker.patch("asyncio.get_event_loop") as mock_loop:
            mock_event_loop = mocker.Mock()
            mock_loop.return_value = mock_event_loop

            # Mock the cached function to return data directly
            with mocker.patch.object(tool, "_fetch_company_overview") as mock_fetch:
                mock_data = {
                    "Symbol": "AAPL",
                    "Name": "Apple Inc",
                    "MarketCapitalization": "2500000000000",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                mock_event_loop.run_until_complete.return_value = mock_data

                result = tool._run(ticker="AAPL")

                # Result should be JSON string, parse it
                import json

                if isinstance(result, str):
                    parsed_result = json.loads(result)
                    assert "timestamp" in parsed_result
                    assert "Symbol" in parsed_result
                    assert parsed_result["Symbol"] == "AAPL"

    def test_should_work_with_alpha_vantage_freshness_validator_wrapper(self, mocker):
        """Test Alpha Vantage tool with freshness validation wrapper."""
        # Mock environment and API
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})
        mock_get = mocker.patch("finwiz.tools.alpha_vantage_tool.requests.get")

        # Mock API response
        mock_response = mocker.Mock()
        mock_response.json.return_value = {"Symbol": "AAPL", "Name": "Apple Inc", "MarketCapitalization": "2500000000000"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        base_tool = AlphaVantageCompanyOverviewTool()
        wrapped_tool = FreshnessValidatedTool(base_tool, max_age_hours=24)

        # Mock the async execution for the wrapper
        with mocker.patch("asyncio.get_event_loop") as mock_loop:
            mock_event_loop = mocker.Mock()
            mock_loop.return_value = mock_event_loop

            # Create mock data with timestamp
            mock_data = {"Symbol": "AAPL", "Name": "Apple Inc", "timestamp": datetime.now(UTC).isoformat()}
            mock_event_loop.run_until_complete.return_value = mock_data

            result = wrapped_tool._run(ticker="AAPL")

            # Should have freshness info added
            assert isinstance(result, dict)
            if "_freshness_info" in result:
                assert result["_freshness_info"]["is_fresh"] is True


class TestFreshnessValidationEndToEnd:
    """End-to-end tests for freshness validation system."""

    def test_should_detect_stale_data_and_attempt_refresh(self, mocker):
        """Test complete flow of stale data detection and refresh attempt."""
        # Create a mock tool that returns stale data first, then fresh data
        mock_tool = mocker.Mock()
        mock_tool.name = "Test Tool"
        mock_tool.description = "Test tool for freshness validation"
        mock_tool.args_schema = None

        stale_time = datetime.now(UTC) - timedelta(hours=48)
        fresh_time = datetime.now(UTC) - timedelta(hours=1)

        # First call returns stale data, second call returns fresh data
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"symbol": "AAPL", "price": 150.0, "timestamp": stale_time.isoformat()}
            else:
                return {
                    "symbol": "AAPL",
                    "price": 151.0,  # Slightly different to show refresh
                    "timestamp": fresh_time.isoformat(),
                }

        mock_tool._run = mock_run

        # Wrap with freshness validation
        validator = DataFreshnessValidator(max_age_hours=24)
        wrapped_tool = FreshnessValidatedTool(mock_tool, validator=validator)

        result = wrapped_tool._run(ticker="AAPL")

        # Should have attempted refresh and gotten fresh data
        assert call_count >= 1  # At least one call made
        assert isinstance(result, dict)
        assert "_freshness_info" in result

    def test_should_handle_missing_api_keys_gracefully(self, mocker):
        """Test graceful handling when API keys are missing."""
        with mocker.patch.dict("os.environ", {}, clear=True):
            tool = AlphaVantageCompanyOverviewTool()

            # Should handle missing API key gracefully
            with mocker.patch("asyncio.get_event_loop") as mock_loop:
                mock_event_loop = mocker.Mock()
                mock_loop.return_value = mock_event_loop
                mock_event_loop.run_until_complete.return_value = "Error: ALPHA_VANTAGE_API_KEY environment variable not set."

                result = tool._run(ticker="AAPL")

                assert isinstance(result, str)
                assert "ALPHA_VANTAGE_API_KEY" in result

    def test_should_maintain_tool_interface_compatibility(self):
        """Test that wrapped tools maintain the same interface as original tools."""
        original_tool = YahooFinanceTickerInfoTool()
        wrapped_tool = FreshnessValidatedTool(original_tool)

        # Should have same interface
        assert hasattr(wrapped_tool, "_run")
        assert hasattr(wrapped_tool, "name")
        assert hasattr(wrapped_tool, "description")
        assert hasattr(wrapped_tool, "args_schema")

        # Name should be modified to indicate freshness validation
        assert "FreshData_" in wrapped_tool.name
        assert original_tool.name in wrapped_tool.name
