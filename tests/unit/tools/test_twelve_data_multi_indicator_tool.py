"""Unit tests for TwelveDataMultiIndicatorTool."""

import pytest

from finwiz.tools.twelve_data_multi_indicator_tool import TwelveDataMultiIndicatorTool


class TestTwelveDataMultiIndicatorTool:
    """Test suite for TwelveDataMultiIndicatorTool."""

    @pytest.fixture
    def tool(self, monkeypatch):
        """Create tool instance with test API key."""
        monkeypatch.setenv("TWELVE_DATA_API_KEY", "test-key")
        return TwelveDataMultiIndicatorTool()

    def test_should_have_correct_name_and_description(self, tool):
        """Test that tool has correct name and description."""
        assert tool.name == "Twelve Data Multi-Indicator"
        assert "multiple technical indicators" in tool.description.lower()
        assert "rsi" in tool.description.lower()
        assert "macd" in tool.description.lower()

    def test_should_determine_asset_type_for_crypto(self, tool):
        """Test asset type detection for crypto symbols."""
        assert tool._determine_asset_type("BTC/USD") == "crypto"
        assert tool._determine_asset_type("ETH-USD") == "crypto"
        assert tool._determine_asset_type("BTCUSDT") == "crypto"

    def test_should_determine_asset_type_for_etf(self, tool):
        """Test asset type detection for ETF symbols."""
        assert tool._determine_asset_type("SPY") == "etf"
        assert tool._determine_asset_type("QQQ") == "etf"
        assert tool._determine_asset_type("VTI") == "etf"

    def test_should_determine_asset_type_for_stock(self, tool):
        """Test asset type detection for stock symbols."""
        assert tool._determine_asset_type("AAPL") == "stock"
        assert tool._determine_asset_type("MSFT") == "stock"
        assert tool._determine_asset_type("GOOGL") == "stock"

    def test_should_fetch_indicator_with_correct_params(self, tool, mocker):
        """Test that indicator fetching uses correct parameters."""
        mock_get = mocker.patch("requests.get")
        mock_response = mocker.Mock()
        mock_response.text = '{"status": "ok"}'
        mock_get.return_value = mock_response

        result = tool._fetch_indicator(
            symbol="AAPL",
            interval="1day",
            indicator="rsi",
            api_key="test_key",
            params={"time_period": 14, "outputsize": 100},
        )

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://api.twelvedata.com/rsi"
        assert call_args[1]["params"]["symbol"] == "AAPL"
        assert call_args[1]["params"]["interval"] == "1day"
        assert call_args[1]["params"]["time_period"] == 14
        assert result == '{"status": "ok"}'

    def test_should_fetch_all_indicators_when_requested(self, tool, mocker):
        """Test fetching all indicators in one call."""
        mocker.patch.dict("os.environ", {"TWELVE_DATA_API_KEY": "test_key"})
        mock_fetch = mocker.patch.object(tool, "_fetch_indicator")
        mock_fetch.return_value = '{"status": "ok"}'

        results = tool._fetch_all_indicators(
            symbol="AAPL",
            interval="1day",
            indicators=["rsi", "macd", "bbands"],
            rsi_period=14,
            macd_fast=12,
            macd_slow=26,
            macd_signal=9,
            bbands_period=20,
            bbands_stddev=2,
            outputsize=100,
        )

        # Verify all indicators were fetched
        assert "rsi" in results
        assert "macd" in results
        assert "bbands" in results
        assert mock_fetch.call_count == 3

    def test_should_handle_missing_api_key(self, mocker):
        """Test fail-fast when API key is missing."""
        mocker.patch.dict("os.environ", {}, clear=True)

        with pytest.raises(ValueError, match="TWELVE_DATA_API_KEY"):
            TwelveDataMultiIndicatorTool()

    def test_should_format_multi_indicator_response(self, tool):
        """Test response formatting with multiple indicators."""
        indicator_results = {
            "rsi": '{"values": [{"datetime": "2025-01-01", "rsi": 65.5}]}',
            "macd": '{"values": [{"datetime": "2025-01-01", "macd": 1.2}]}',
        }

        response = tool._format_multi_indicator_response(symbol="AAPL", interval="1day", indicator_results=indicator_results, perplexity_insights=[])

        # Verify response structure
        assert "AAPL" in response
        assert "1day" in response
        assert "RSI" in response
        assert "MACD" in response
        assert "Multi-Indicator Technical Analysis" in response

    def test_should_include_perplexity_insights_when_available(self, tool, mocker):
        """Test that Perplexity insights are included when available."""
        mock_article = mocker.Mock()
        mock_article.title = "Technical Analysis Article"
        mock_article.publisher = "Test Publisher"
        mock_article.relevance_score = 0.95
        mock_article.summary = "Test summary"
        mock_article.url = "https://example.com"
        mock_article.content_type = "analysis"

        response = tool._format_multi_indicator_response(
            symbol="AAPL",
            interval="1day",
            indicator_results={"rsi": '{"status": "ok"}'},
            perplexity_insights=[mock_article],
        )

        # Verify Perplexity section is included
        assert "Market Analysis Insights" in response
        assert "Technical Analysis Article" in response
        assert "Test Publisher" in response
        assert "0.95" in response
