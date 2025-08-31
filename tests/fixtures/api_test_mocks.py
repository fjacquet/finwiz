"""
Standardized mock setups for external APIs using pytest-mock.

This module provides a centralized APITestMocks class with standardized mock
configurations for all external API integrations, ensuring consistent behavior
and explicit return values across the test suite.
"""

from datetime import datetime
from typing import Any


class APITestMocks:
    """Centralized mock configurations for external API testing."""

    @staticmethod
    def setup_yahoo_finance_mock(mocker, ticker: str = "AAPL", **kwargs) -> Any:
        """
        Setup comprehensive Yahoo Finance API mock with explicit behavior.

        Args:
            mocker: pytest-mock fixture
            ticker: Stock ticker symbol for mock data
            **kwargs: Override default mock return values

        Returns:
            Mock object with configured behavior

        """
        mock_ticker = mocker.patch("yfinance.Ticker")
        mock_ticker_instance = mocker.Mock()

        # Default mock data - can be overridden via kwargs
        default_info = {
            "symbol": ticker,
            "longName": f"{ticker} Inc.",
            "currentPrice": kwargs.get("price", 150.25),
            "marketCap": kwargs.get("market_cap", 2500000000),
            "trailingPE": kwargs.get("pe_ratio", 18.5),
            "dividendYield": kwargs.get("dividend_yield", 0.015),
            "beta": kwargs.get("beta", 1.2),
            "fiftyTwoWeekHigh": kwargs.get("week_52_high", 180.0),
            "fiftyTwoWeekLow": kwargs.get("week_52_low", 120.0),
            "volume": kwargs.get("volume", 50000000),
            "averageVolume": kwargs.get("avg_volume", 45000000),
            "sector": kwargs.get("sector", "Technology"),
            "industry": kwargs.get("industry", "Consumer Electronics"),
        }

        # News data
        default_news = kwargs.get(
            "news",
            [
                {
                    "title": f"{ticker} Reports Strong Quarterly Results",
                    "summary": "Company exceeds earnings expectations with strong revenue growth",
                    "link": "https://finance.yahoo.com/news/sample1",
                    "publisher": "Yahoo Finance",
                    "providerPublishTime": int(datetime.now().timestamp()),
                },
                {
                    "title": f"{ticker} Announces New Product Launch",
                    "summary": "Innovation drives future growth prospects",
                    "link": "https://finance.yahoo.com/news/sample2",
                    "publisher": "MarketWatch",
                    "providerPublishTime": int(datetime.now().timestamp()) - 3600,
                },
            ],
        )

        # Historical data
        default_history = kwargs.get("history", mocker.Mock())
        if hasattr(default_history, "Close"):
            default_history.Close = [145.0, 148.0, 150.25, 152.0, 149.5]

        # Configure mock instance
        mock_ticker_instance.info = default_info
        mock_ticker_instance.news = default_news
        mock_ticker_instance.history.return_value = default_history

        # ETF-specific data
        if kwargs.get("is_etf", False):
            mock_ticker_instance.info.update(
                {
                    "fundFamily": kwargs.get("fund_family", "SPDR"),
                    "totalAssets": kwargs.get("total_assets", 400000000000),
                    "yield": kwargs.get("etf_yield", 0.018),
                    "expenseRatio": kwargs.get("expense_ratio", 0.0009),
                    "category": kwargs.get("category", "Large Blend"),
                }
            )

        mock_ticker.return_value = mock_ticker_instance
        return mock_ticker

    @staticmethod
    def setup_alpha_vantage_mock(mocker, ticker: str = "AAPL", **kwargs) -> Any:
        """
        Setup Alpha Vantage API mock with explicit news and sentiment data.

        Args:
            mocker: pytest-mock fixture
            ticker: Stock ticker symbol
            **kwargs: Override default mock return values

        Returns:
            Mock aiohttp response with configured behavior

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = kwargs.get("status_code", 200)

        # Default news feed response
        default_feed = kwargs.get(
            "feed",
            [
                {
                    "title": f"{ticker} Earnings Beat Expectations",
                    "summary": "Strong quarterly performance drives positive sentiment",
                    "url": "https://example.com/news1",
                    "time_published": "20240101T120000",
                    "source": "Reuters",
                    "overall_sentiment_score": kwargs.get("sentiment_1", "0.6"),
                    "ticker_sentiment": [
                        {
                            "ticker": ticker,
                            "relevance_score": "0.8",
                            "ticker_sentiment_score": kwargs.get("ticker_sentiment_1", "0.7"),
                        }
                    ],
                },
                {
                    "title": f"{ticker} Faces Market Headwinds",
                    "summary": "Analysts express caution about near-term challenges",
                    "url": "https://example.com/news2",
                    "time_published": "20240101T100000",
                    "source": "Bloomberg",
                    "overall_sentiment_score": kwargs.get("sentiment_2", "-0.2"),
                    "ticker_sentiment": [
                        {
                            "ticker": ticker,
                            "relevance_score": "0.7",
                            "ticker_sentiment_score": kwargs.get("ticker_sentiment_2", "-0.3"),
                        }
                    ],
                },
            ],
        )

        mock_response.json.return_value = {"feed": default_feed}
        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_twelve_data_mock(mocker, indicator: str = "rsi", **kwargs) -> Any:
        """
        Setup Twelve Data API mock for technical indicators.

        Args:
            mocker: pytest-mock fixture
            indicator: Technical indicator type (rsi, macd, bbands, stoch)
            **kwargs: Override default mock return values

        Returns:
            Mock aiohttp response with configured indicator data

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = kwargs.get("status_code", 200)

        # Generate indicator-specific mock data
        if indicator == "rsi":
            mock_data = {
                "meta": {
                    "symbol": kwargs.get("symbol", "AAPL"),
                    "interval": kwargs.get("interval", "1day"),
                    "time_period": kwargs.get("time_period", 14),
                },
                "values": kwargs.get(
                    "values",
                    [
                        {"datetime": "2024-01-15", "rsi": "65.5"},
                        {"datetime": "2024-01-14", "rsi": "62.3"},
                        {"datetime": "2024-01-13", "rsi": "58.7"},
                    ],
                ),
            }
        elif indicator == "macd":
            mock_data = {
                "meta": {"symbol": kwargs.get("symbol", "AAPL"), "interval": kwargs.get("interval", "1day")},
                "values": kwargs.get(
                    "values",
                    [
                        {"datetime": "2024-01-15", "macd": "2.45", "macd_signal": "2.12", "macd_hist": "0.33"},
                        {"datetime": "2024-01-14", "macd": "2.18", "macd_signal": "2.25", "macd_hist": "-0.07"},
                    ],
                ),
            }
        elif indicator == "bbands":
            mock_data = {
                "meta": {"symbol": kwargs.get("symbol", "AAPL"), "interval": kwargs.get("interval", "1day")},
                "values": kwargs.get(
                    "values",
                    [
                        {"datetime": "2024-01-15", "upper_band": "185.50", "middle_band": "180.00", "lower_band": "174.50"},
                        {"datetime": "2024-01-14", "upper_band": "184.20", "middle_band": "179.50", "lower_band": "174.80"},
                    ],
                ),
            }
        elif indicator == "stoch":
            mock_data = {
                "meta": {"symbol": kwargs.get("symbol", "AAPL"), "interval": kwargs.get("interval", "1day")},
                "values": kwargs.get(
                    "values",
                    [
                        {"datetime": "2024-01-15", "slow_k": "75.5", "slow_d": "72.3"},
                        {"datetime": "2024-01-14", "slow_k": "68.2", "slow_d": "70.1"},
                    ],
                ),
            }
        else:
            mock_data = kwargs.get("custom_data", {})

        mock_response.json.return_value = mock_data
        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_coinmarketcap_mock(mocker, crypto_symbol: str = "BTC", **kwargs) -> Any:
        """
        Setup CoinMarketCap API mock for cryptocurrency data.

        Args:
            mocker: pytest-mock fixture
            crypto_symbol: Cryptocurrency symbol
            **kwargs: Override default mock return values

        Returns:
            Mock aiohttp response with configured crypto data

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")

        # Mock responses for both map and news endpoints
        map_response = mocker.AsyncMock()
        map_response.status = kwargs.get("map_status", 200)
        map_response.json.return_value = {
            "data": kwargs.get("map_data", [{"id": 1, "symbol": crypto_symbol, "name": f"{crypto_symbol} Name"}])
        }

        news_response = mocker.AsyncMock()
        news_response.status = kwargs.get("news_status", 200)
        news_response.json.return_value = {
            "data": kwargs.get(
                "news_data",
                [
                    {
                        "title": f"{crypto_symbol} Adoption Increases",
                        "description": "Growing institutional interest drives adoption",
                        "url": "https://coinmarketcap.com/news1",
                        "source": "CoinDesk",
                        "published_at": "2024-01-01T12:00:00Z",
                    },
                    {
                        "title": f"{crypto_symbol} Price Volatility Analysis",
                        "description": "Market analysis shows continued volatility patterns",
                        "url": "https://coinmarketcap.com/news2",
                        "source": "CoinTelegraph",
                        "published_at": "2024-01-01T11:00:00Z",
                    },
                ],
            )
        }

        # Return different responses based on URL
        mock_get.return_value.__aenter__.side_effect = [map_response, news_response]

        return mock_get

    @staticmethod
    def setup_chart_img_mock(mocker, **kwargs) -> Any:
        """
        Setup Chart-img API mock for chart generation.

        Args:
            mocker: pytest-mock fixture
            **kwargs: Override default mock return values

        Returns:
            Mock aiohttp response with chart data

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = kwargs.get("status_code", 200)

        # Mock binary chart data
        chart_data = kwargs.get("chart_data", b"fake_chart_image_data")
        mock_response.read.return_value = chart_data

        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_sec_edgar_mock(mocker, ticker: str = "AAPL", **kwargs) -> Any:
        """
        Setup SEC EDGAR API mock for filing data.

        Args:
            mocker: pytest-mock fixture
            ticker: Stock ticker symbol
            **kwargs: Override default mock return values

        Returns:
            Mock aiohttp response with SEC filing data

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = kwargs.get("status_code", 200)

        # Default SEC filing response
        default_filings = kwargs.get(
            "filings",
            {
                "filings": {
                    "recent": {
                        "form": ["10-K", "10-Q"],
                        "filingDate": ["2024-01-15", "2024-01-10"],
                        "accessionNumber": ["0000320193-24-000001", "0000320193-24-000002"],
                        "primaryDocument": ["aapl-20231230.htm", "aapl-20231231.htm"],
                    }
                }
            },
        )

        mock_response.json.return_value = default_filings
        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_http_error_mock(mocker, status_code: int = 500, error_message: str = "Internal Server Error") -> Any:
        """
        Setup mock for HTTP error responses.

        Args:
            mocker: pytest-mock fixture
            status_code: HTTP status code to return
            error_message: Error message text

        Returns:
            Mock that raises appropriate HTTP error

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = status_code
        mock_response.text.return_value = error_message

        if status_code >= 400:
            mock_response.raise_for_status.side_effect = Exception(f"HTTP {status_code}: {error_message}")

        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_timeout_mock(mocker, timeout_error: bool = True) -> Any:
        """
        Setup mock for timeout scenarios.

        Args:
            mocker: pytest-mock fixture
            timeout_error: Whether to raise TimeoutError

        Returns:
            Mock that simulates timeout behavior

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")

        if timeout_error:
            mock_get.side_effect = TimeoutError("Request timed out")
        else:
            # Simulate slow response
            async def slow_response():
                import asyncio

                await asyncio.sleep(0.1)
                mock_response = mocker.AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                return mock_response

            mock_get.return_value.__aenter__ = slow_response

        return mock_get

    @staticmethod
    def setup_rate_limit_mock(mocker, retry_after: int = 60) -> Any:
        """
        Setup mock for rate limit scenarios.

        Args:
            mocker: pytest-mock fixture
            retry_after: Seconds to wait before retry

        Returns:
            Mock that simulates rate limiting

        """
        mock_get = mocker.patch("aiohttp.ClientSession.get")
        mock_response = mocker.AsyncMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": str(retry_after)}
        mock_response.text.return_value = "Rate limit exceeded"

        mock_get.return_value.__aenter__.return_value = mock_response

        return mock_get

    @staticmethod
    def setup_file_system_mock(mocker, file_content: str = "", file_exists: bool = True) -> Any:
        """
        Setup file system operation mocks.

        Args:
            mocker: pytest-mock fixture
            file_content: Content to return when reading files
            file_exists: Whether files should exist

        Returns:
            Mock file system operations

        """
        # Mock pathlib.Path operations
        mock_path = mocker.patch("pathlib.Path")
        mock_path_instance = mocker.Mock()

        mock_path_instance.exists.return_value = file_exists
        mock_path_instance.read_text.return_value = file_content
        mock_path_instance.write_text.return_value = None
        mock_path_instance.is_file.return_value = file_exists

        mock_path.return_value = mock_path_instance

        # Also mock built-in open function
        mock_open = mocker.mock_open(read_data=file_content)
        mocker.patch("builtins.open", mock_open)

        return {"path": mock_path, "open": mock_open, "path_instance": mock_path_instance}

    @staticmethod
    def setup_environment_mock(mocker, env_vars: dict[str, str]) -> Any:
        """
        Setup environment variable mocks.

        Args:
            mocker: pytest-mock fixture
            env_vars: Dictionary of environment variables to set

        Returns:
            Mock environment configuration

        """
        return mocker.patch.dict("os.environ", env_vars, clear=False)

    @staticmethod
    def setup_database_mock(mocker, **kwargs) -> Any:
        """
        Setup database operation mocks.

        Args:
            mocker: pytest-mock fixture
            **kwargs: Database-specific configuration

        Returns:
            Mock database operations

        """
        # Mock common database operations
        mock_connection = mocker.Mock()
        mock_cursor = mocker.Mock()

        mock_cursor.fetchall.return_value = kwargs.get("fetch_results", [])
        mock_cursor.fetchone.return_value = kwargs.get("fetch_one_result", None)
        mock_cursor.execute.return_value = None

        mock_connection.cursor.return_value = mock_cursor
        mock_connection.commit.return_value = None
        mock_connection.rollback.return_value = None

        return {"connection": mock_connection, "cursor": mock_cursor}
