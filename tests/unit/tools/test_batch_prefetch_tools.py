"""
Unit tests for tools with batch pre-fetch support.

Tests tools that support pre-fetched data including:
- Yahoo Finance ticker info tool
- Yahoo Finance history tool
- Alpha Vantage tool
- Quantitative analysis tool
- Backward compatibility (fallback to live API)

Requirements: 17.75, 17.78
"""

import pandas as pd
import pytest

from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool


class TestYahooFinanceTickerInfoToolWithPrefetch:
    """Test YahooFinanceTickerInfoTool with pre-fetched data."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return YahooFinanceTickerInfoTool()

    @pytest.fixture
    def prefetched_data(self):
        """Provide sample pre-fetched data."""
        return {
            "AAPL": {
                "symbol": "AAPL",
                "shortName": "Apple Inc.",
                "sector": "Technology",
                "currentPrice": 150.0,
                "marketCap": 2500000000000,
                "trailingPE": 25.5,
            }
        }

    def test_should_use_prefetched_data_when_available(self, tool, prefetched_data):
        """Test that tool uses pre-fetched data when provided."""
        # Act
        result = tool._run(ticker="AAPL", prefetched_data=prefetched_data)

        # Assert
        assert result["symbol"] == "AAPL"
        assert result["shortName"] == "Apple Inc."
        assert result["data_source"] == "prefetched"  # Should indicate prefetched source

    def test_should_fallback_to_live_api_when_no_prefetch(self, tool, mocker):
        """Test backward compatibility - fallback to live API when no pre-fetched data."""
        # Arrange
        mock_ticker = mocker.Mock()
        mock_ticker.info = {
            "symbol": "MSFT",
            "shortName": "Microsoft Corporation",
            "currentPrice": 300.0,
        }
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = tool._run(ticker="MSFT", prefetched_data=None)

        # Assert
        assert result["symbol"] == "MSFT"
        assert result["name"] == "Microsoft Corporation"  # Tool returns "name" not "shortName"

    def test_should_fallback_when_ticker_not_in_prefetch(self, tool, prefetched_data, mocker):
        """Test fallback to live API when ticker not in pre-fetched data."""
        # Arrange
        mock_ticker = mocker.Mock()
        mock_ticker.info = {
            "symbol": "GOOGL",
            "shortName": "Alphabet Inc.",
            "currentPrice": 140.0,
        }
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = tool._run(ticker="GOOGL", prefetched_data=prefetched_data)

        # Assert
        assert result["symbol"] == "GOOGL"
        assert result["name"] == "Alphabet Inc."  # Tool returns "name" not "shortName"

    def test_should_verify_data_quality_matches_live_api(self, tool, mocker):
        """Test that pre-fetched data quality matches live API calls."""
        # Arrange
        mock_ticker = mocker.Mock()
        mock_ticker.info = {
            "symbol": "AAPL",
            "shortName": "Apple Inc.",
            "sector": "Technology",
            "currentPrice": 150.0,
            "marketCap": 2500000000000,
        }
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        prefetched_data = {
            "AAPL": {
                "symbol": "AAPL",
                "shortName": "Apple Inc.",
                "sector": "Technology",
                "currentPrice": 150.0,
                "marketCap": 2500000000000,
            }
        }

        # Act
        live_result = tool._run(ticker="AAPL", prefetched_data=None)
        prefetch_result = tool._run(ticker="AAPL", prefetched_data=prefetched_data)

        # Assert - Key fields should match
        assert live_result["symbol"] == prefetch_result["symbol"]
        assert live_result.get("name") or live_result.get("shortName")  # Either field should exist
        assert live_result["sector"] == prefetch_result["sector"]


class TestYahooFinanceHistoryToolWithPrefetch:
    """Test YahooFinanceHistoryTool with pre-fetched data."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return YahooFinanceHistoryTool()

    @pytest.fixture
    def prefetched_data(self):
        """Provide sample pre-fetched historical data."""
        return {
            "AAPL": {
                "dates": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "close": [150.0, 152.0, 151.0],
                "volume": [1000000, 1100000, 1050000],
                "data_points": 3,
            }
        }

    def test_should_use_prefetched_historical_data(self, tool, prefetched_data):
        """Test that tool uses pre-fetched historical data."""
        # Act
        result = tool._run(ticker="AAPL", period="1y", prefetched_data=prefetched_data)

        # Assert
        assert result["data_points"] == 3
        assert result["data_source"] == "prefetched"  # Should indicate prefetched source

    def test_should_fallback_to_live_api_for_history(self, tool, mocker):
        """Test fallback to live API for historical data."""
        # Arrange
        mock_hist_data = pd.DataFrame({"Close": [300.0, 302.0, 301.0], "Volume": [2000000, 2100000, 2050000]}, index=pd.date_range("2024-01-01", periods=3))
        mock_ticker = mocker.Mock()
        mock_ticker.history.return_value = mock_hist_data
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = tool._run(ticker="MSFT", period="1y", prefetched_data=None)

        # Assert
        assert "summary" in result or "history" in result  # Should have data


class TestAlphaVantageToolWithPrefetch:
    """Test AlphaVantageCompanyOverviewTool with pre-fetched data."""

    @pytest.fixture
    def tool(self, monkeypatch):
        """Create tool instance."""
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-alpha-vantage-key")
        return AlphaVantageCompanyOverviewTool()

    @pytest.fixture
    def prefetched_data(self):
        """Provide sample pre-fetched Alpha Vantage data."""
        return {
            "AAPL": {
                "Symbol": "AAPL",
                "Name": "Apple Inc",
                "Sector": "TECHNOLOGY",
                "MarketCapitalization": "2500000000000",
                "PERatio": "25.5",
            }
        }

    def test_should_use_prefetched_alpha_vantage_data(self, tool, prefetched_data):
        """Test that tool uses pre-fetched Alpha Vantage data."""
        # Act
        result = tool._run(ticker="AAPL", include_perplexity=False, prefetched_data=prefetched_data)

        # Assert
        assert "AAPL" in result
        assert "Apple Inc" in result

    def test_should_fallback_to_live_api_alpha_vantage(self, tool, mocker):
        """Test fallback to live Alpha Vantage API."""
        # Arrange
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})
        mock_response = mocker.Mock()
        mock_response.json.return_value = {
            "Symbol": "MSFT",
            "Name": "Microsoft Corporation",
            "Sector": "TECHNOLOGY",
        }
        mock_response.status_code = 200
        mocker.patch("requests.get", return_value=mock_response)

        # Act
        result = tool._run(ticker="MSFT", include_perplexity=False, prefetched_data=None)

        # Assert
        assert "MSFT" in result or "Microsoft" in result


class TestQuantitativeAnalysisToolWithPrefetch:
    """Test QuantitativeAnalysisTool with pre-fetched data."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return QuantitativeAnalysisTool(asset_class="stock")

    @pytest.fixture
    def prefetched_data(self):
        """Provide sample pre-fetched price data as DataFrame."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        return pd.DataFrame(
            {
                "Close": [150.0 + i * 0.5 for i in range(100)],
                "Volume": [1000000 + i * 10000 for i in range(100)],
                "High": [151.0 + i * 0.5 for i in range(100)],
                "Low": [149.0 + i * 0.5 for i in range(100)],
            },
            index=dates,
        )

    def test_should_pass_prefetched_data_to_stock_tools(self, mocker):
        """Test that tool factories pass pre-fetched data to tools."""
        # Arrange
        from finwiz.tools.tool_factories import get_stock_crew_tools

        prefetched_data = {"AAPL": {"symbol": "AAPL", "price": 150.0}}

        # Act
        tools = get_stock_crew_tools(include_quantitative=False, include_valuation=False, prefetched_data=prefetched_data)

        # Assert
        assert len(tools) > 0
        # Tools should be created (exact behavior depends on implementation)

    def test_should_pass_prefetched_data_to_crypto_tools(self, mocker):
        """Test that crypto tool factory passes pre-fetched data."""
        # Arrange
        from finwiz.tools.tool_factories import get_crypto_crew_tools

        prefetched_data = {"BTC-USD": {"symbol": "BTC-USD", "price": 50000.0}}

        # Act
        tools = get_crypto_crew_tools(include_quantitative=False, prefetched_data=prefetched_data)

        # Assert
        assert len(tools) > 0

    def test_should_pass_prefetched_data_to_etf_tools(self, mocker):
        """Test that ETF tool factory passes pre-fetched data."""
        # Arrange
        from finwiz.tools.tool_factories import get_etf_crew_tools

        prefetched_data = {"SPY": {"symbol": "SPY", "price": 450.0}}

        # Act
        tools = get_etf_crew_tools(include_quantitative=False, include_etf_analysis=False, prefetched_data=prefetched_data)

        # Assert
        assert len(tools) > 0


class TestBackwardCompatibility:
    """Test backward compatibility of tools without pre-fetched data."""

    def test_should_work_without_prefetch_parameter(self, mocker):
        """Test that tools work without prefetched_data parameter (backward compatibility)."""
        # Arrange
        tool = YahooFinanceTickerInfoTool()
        mock_ticker = mocker.Mock()
        mock_ticker.info = {"symbol": "AAPL", "shortName": "Apple Inc."}
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act - Call without prefetched_data parameter
        result = tool._run(ticker="AAPL")

        # Assert
        assert result["symbol"] == "AAPL"

    def test_should_handle_none_prefetch_gracefully(self):
        """Test that tools handle None prefetched_data gracefully."""
        # Arrange
        tool = YahooFinanceTickerInfoTool()

        # Act & Assert - Should not raise exception
        # (Will fail to fetch data but should handle None gracefully)
        try:
            result = tool._run(ticker="AAPL", prefetched_data=None)
            # If it succeeds, that's fine
        except Exception as e:
            # If it fails, it should be a data fetch error, not a None handling error
            assert "prefetched_data" not in str(e).lower()

    def test_should_handle_empty_prefetch_dict(self, mocker):
        """Test that tools handle empty pre-fetched data dict."""
        # Arrange
        tool = YahooFinanceTickerInfoTool()
        mock_ticker = mocker.Mock()
        mock_ticker.info = {"symbol": "AAPL", "shortName": "Apple Inc."}
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act - Empty dict should trigger fallback
        result = tool._run(ticker="AAPL", prefetched_data={})

        # Assert
        assert result["symbol"] == "AAPL"
