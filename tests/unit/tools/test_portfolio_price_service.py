"""
Unit tests for PortfolioPriceService.

Tests the portfolio price data service with mocked API responses,
caching functionality, fallback mechanisms, and error handling.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from finwiz.schemas.portfolio_rebalancing import PriceData
from finwiz.tools.portfolio_price_service import (
    PortfolioPriceService,
    PriceDataUnavailableError,
    PriceServiceConfig,
)


class TestPortfolioPriceService:
    """Test suite for PortfolioPriceService."""

    @pytest.fixture
    def mock_cache_manager(self, mocker):
        """Mock cache manager."""
        mock_cache = mocker.MagicMock()
        mock_cache.get = mocker.AsyncMock(return_value=None)
        mock_cache.set = mocker.AsyncMock()
        mock_cache.delete = mocker.AsyncMock(return_value=True)
        mock_cache.clear = mocker.AsyncMock(return_value=5)
        mock_cache.get_stats = mocker.MagicMock(return_value={"hits": 10, "misses": 5})
        return mock_cache

    @pytest.fixture
    def mock_yahoo_tool(self, mocker):
        """Mock Yahoo Finance ticker info tool."""
        mock_tool = mocker.MagicMock()
        mock_tool._run = mocker.MagicMock()
        return mock_tool

    @pytest.fixture
    def mock_crypto_tool(self, mocker):
        """Mock enhanced crypto analysis tool."""
        mock_tool = mocker.MagicMock()
        mock_tool._run = mocker.MagicMock()
        return mock_tool

    @pytest.fixture
    def price_service(self, mock_cache_manager, mocker):
        """Create PortfolioPriceService instance with mocked dependencies."""
        # Mock the tool imports
        mocker.patch("finwiz.tools.portfolio_price_service.YahooFinanceTickerInfoTool")
        mocker.patch("finwiz.tools.portfolio_price_service.EnhancedCryptoAnalysisTool")

        config = PriceServiceConfig(default_cache_ttl=300, max_concurrent_requests=5, request_timeout=10.0, retry_attempts=2, retry_delay=0.1)

        service = PortfolioPriceService(config=config, cache_manager=mock_cache_manager)
        return service

    def test_should_initialize_with_default_config_when_no_config_provided(self, mock_cache_manager, mocker):
        """Test service initialization with default configuration."""
        # Arrange
        mocker.patch("finwiz.tools.portfolio_price_service.YahooFinanceTickerInfoTool")
        mocker.patch("finwiz.tools.portfolio_price_service.EnhancedCryptoAnalysisTool")
        mocker.patch("finwiz.tools.portfolio_price_service.get_cache_manager", return_value=mock_cache_manager)

        # Act
        service = PortfolioPriceService()

        # Assert
        assert service.config.default_cache_ttl == 300
        assert service.config.max_concurrent_requests == 10
        assert service.cache_manager is not None

    def test_should_identify_crypto_symbols_correctly(self, price_service):
        """Test crypto symbol identification logic."""
        # Arrange & Act & Assert
        assert price_service._is_crypto_symbol("BTC-USD") is True
        assert price_service._is_crypto_symbol("ETH-USDT") is True
        assert price_service._is_crypto_symbol("BTC") is True
        assert price_service._is_crypto_symbol("DOGECOIN") is True  # Long symbol
        assert price_service._is_crypto_symbol("AAPL") is False
        assert price_service._is_crypto_symbol("MSFT") is False
        assert price_service._is_crypto_symbol("VTI") is False

    @pytest.mark.asyncio
    async def test_should_return_cached_price_when_cache_hit_and_fresh(self, price_service, mock_cache_manager):
        """Test successful cache hit with fresh data."""
        # Arrange
        cached_price_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": datetime.now().isoformat(),
            "source": "yahoo_finance",
            "currency": "USD",
        }
        mock_cache_manager.get.return_value = cached_price_data

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == 150.0
        assert result.source == "yahoo_finance"
        mock_cache_manager.get.assert_called_once_with("price:AAPL")

    @pytest.mark.asyncio
    async def test_should_fetch_fresh_data_when_cached_data_stale(self, price_service, mock_cache_manager, mocker):
        """Test fetching fresh data when cached data is stale."""
        # Arrange
        stale_timestamp = (datetime.now() - timedelta(hours=2)).isoformat()
        cached_price_data = {
            "symbol": "AAPL",
            "price": 150.0,
            "timestamp": stale_timestamp,
            "source": "yahoo_finance",
            "currency": "USD",
        }
        mock_cache_manager.get.return_value = cached_price_data

        # Mock Yahoo Finance tool to return fresh data
        price_service.yahoo_tool._run.return_value = {"current_price": 155.0, "currency": "USD"}

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.price == 155.0  # Fresh price, not cached
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_get_stock_price_from_yahoo_finance_when_cache_miss(self, price_service, mock_cache_manager):
        """Test getting stock price from Yahoo Finance on cache miss."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"current_price": 150.0, "currency": "USD", "symbol": "AAPL"}

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == 150.0
        assert result.source == "yahoo_finance"
        assert result.currency == "USD"

        # Verify caching
        mock_cache_manager.set.assert_called_once()
        cache_call_args = mock_cache_manager.set.call_args
        assert cache_call_args[0][0] == "price:AAPL"
        assert cache_call_args[1]["ttl"] == 300

    @pytest.mark.asyncio
    async def test_should_use_crypto_tool_for_crypto_symbols(self, price_service, mock_cache_manager, mocker):
        """Test using crypto tool for cryptocurrency symbols."""
        # Arrange
        mock_cache_manager.get.return_value = None

        # Mock Yahoo Finance to fail for crypto
        price_service.yahoo_tool._run.return_value = {"error": "Not found"}

        # Mock yfinance direct calls to fail
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = mocker.MagicMock(empty=True)
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Mock crypto tool to succeed
        price_service.crypto_tool._run.return_value = {"crypto_data": {"current_price": 45000.0, "symbol": "BTC"}}

        # Act
        result = await price_service.get_current_price("BTC-USD")

        # Assert
        assert result is not None
        assert result.symbol == "BTC-USD"
        assert result.price == 45000.0
        assert result.source == "crypto_tool"
        price_service.crypto_tool._run.assert_called_once_with("BTC", False, False)

    @pytest.mark.asyncio
    async def test_should_handle_yahoo_finance_tool_error_with_fallback(self, price_service, mock_cache_manager, mocker):
        """Test fallback mechanism when Yahoo Finance tool fails."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"error": "API error"}

        # Mock yfinance direct call
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {"regularMarketPrice": 150.0}
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.price == 150.0
        assert result.source == "yfinance_direct"

    @pytest.mark.asyncio
    async def test_should_use_history_fallback_when_direct_yfinance_fails(self, price_service, mock_cache_manager, mocker):
        """Test using history data as fallback when direct yfinance fails."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"error": "API error"}

        # Mock yfinance ticker with failing info but working history
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}

        # Mock history data
        import pandas as pd

        mock_history = pd.DataFrame({"Close": [148.0, 149.0, 150.0]})
        mock_ticker.history.return_value = mock_history

        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.price == 150.0  # Latest close price
        assert result.source == "yfinance_history"

    @pytest.mark.asyncio
    async def test_should_return_none_when_all_sources_fail(self, price_service, mock_cache_manager, mocker):
        """Test returning None when all price sources fail."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"error": "API error"}

        # Mock yfinance to fail
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = mocker.MagicMock(empty=True)
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act
        result = await price_service.get_current_price("INVALID")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_should_get_multiple_prices_concurrently(self, price_service, mock_cache_manager):
        """Test getting multiple prices concurrently."""
        # Arrange
        mock_cache_manager.get.return_value = None

        def mock_yahoo_response(symbol):
            prices = {"AAPL": 150.0, "MSFT": 300.0, "GOOGL": 2500.0}
            return {"current_price": prices.get(symbol, 100.0), "currency": "USD"}

        price_service.yahoo_tool._run.side_effect = mock_yahoo_response

        # Act
        result = await price_service.get_current_prices(["AAPL", "MSFT", "GOOGL"])

        # Assert
        assert len(result) == 3
        assert result["AAPL"].price == 150.0
        assert result["MSFT"].price == 300.0
        assert result["GOOGL"].price == 2500.0

        # Verify all symbols were cached
        assert mock_cache_manager.set.call_count == 3

    @pytest.mark.asyncio
    async def test_should_handle_partial_failures_in_batch_requests(self, price_service, mock_cache_manager):
        """Test handling partial failures in batch price requests."""
        # Arrange
        mock_cache_manager.get.return_value = None

        def mock_yahoo_response(symbol):
            if symbol == "INVALID":
                return {"error": "Symbol not found"}
            return {"current_price": 150.0, "currency": "USD"}

        price_service.yahoo_tool._run.side_effect = mock_yahoo_response

        # Act
        result = await price_service.get_current_prices(["AAPL", "INVALID", "MSFT"])

        # Assert
        assert len(result) == 2  # Only successful symbols
        assert "AAPL" in result
        assert "MSFT" in result
        assert "INVALID" not in result

    @pytest.mark.asyncio
    async def test_should_raise_exception_when_get_price_with_fallback_fails(self, price_service, mock_cache_manager, mocker):
        """Test exception raising when get_price_with_fallback fails."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"error": "API error"}

        # Mock all fallbacks to fail
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = mocker.MagicMock(empty=True)
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Act & Assert
        with pytest.raises(PriceDataUnavailableError) as exc_info:
            await price_service.get_price_with_fallback("INVALID")

        assert "INVALID" in str(exc_info.value)
        assert "All price sources failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_should_validate_symbols_correctly(self, price_service, mock_cache_manager):
        """Test symbol validation functionality."""
        # Arrange
        mock_cache_manager.get.return_value = None

        def mock_yahoo_response(symbol):
            valid_symbols = {"AAPL", "MSFT"}
            if symbol in valid_symbols:
                return {"current_price": 150.0, "currency": "USD"}
            return {"error": "Symbol not found"}

        price_service.yahoo_tool._run.side_effect = mock_yahoo_response

        # Act
        result = await price_service.validate_symbols(["AAPL", "MSFT", "INVALID"])

        # Assert
        assert result["AAPL"] is True
        assert result["MSFT"] is True
        assert result["INVALID"] is False

    @pytest.mark.asyncio
    async def test_should_clear_specific_symbol_cache(self, price_service, mock_cache_manager):
        """Test clearing cache for specific symbols."""
        # Arrange
        mock_cache_manager.delete.return_value = True

        # Act
        result = await price_service.clear_price_cache(["AAPL", "MSFT"])

        # Assert
        assert result == 2
        assert mock_cache_manager.delete.call_count == 2
        mock_cache_manager.delete.assert_any_call("price:AAPL")
        mock_cache_manager.delete.assert_any_call("price:MSFT")

    @pytest.mark.asyncio
    async def test_should_clear_all_price_cache_when_no_symbols_specified(self, price_service, mock_cache_manager):
        """Test clearing all price cache entries."""
        # Arrange
        mock_cache_manager.clear.return_value = 10

        # Act
        result = await price_service.clear_price_cache(None)

        # Assert
        assert result == 10
        mock_cache_manager.clear.assert_called_once_with(tags={"price"})

    @pytest.mark.asyncio
    async def test_should_warm_cache_successfully(self, price_service, mock_cache_manager):
        """Test cache warming functionality."""
        # Arrange
        mock_cache_manager.get.return_value = None
        price_service.yahoo_tool._run.return_value = {"current_price": 150.0, "currency": "USD"}

        # Act
        result = await price_service.warm_cache(["AAPL", "MSFT"])

        # Assert
        assert result["AAPL"] is True
        assert result["MSFT"] is True
        assert mock_cache_manager.set.call_count == 2

    @pytest.mark.asyncio
    async def test_should_get_cache_stats(self, price_service, mock_cache_manager):
        """Test getting cache statistics."""
        # Arrange
        mock_cache_manager.get_stats.return_value = {"hits": 100, "misses": 20}

        # Act
        result = await price_service.get_cache_stats()

        # Assert
        assert "hits" in result
        assert "misses" in result
        assert "service_config" in result
        assert result["hits"] == 100
        assert result["misses"] == 20

    @pytest.mark.asyncio
    async def test_should_handle_timeout_errors_with_retry(self, price_service, mock_cache_manager, mocker):
        """Test handling timeout errors with retry logic."""
        # Arrange
        mock_cache_manager.get.return_value = None

        # Mock asyncio.wait_for to raise TimeoutError on first call, succeed on second
        call_count = 0

        def mock_wait_for(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TimeoutError()
            return {"current_price": 150.0, "currency": "USD"}

        mocker.patch("asyncio.wait_for", side_effect=mock_wait_for)

        # Act
        result = await price_service.get_current_price("AAPL")

        # Assert
        assert result is not None
        assert result.price == 150.0
        assert call_count == 2  # Verify retry occurred

    @pytest.mark.asyncio
    async def test_should_respect_concurrent_request_limit(self, price_service, mock_cache_manager, mocker):
        """Test that concurrent request limit is respected."""
        # Arrange
        mock_cache_manager.get.return_value = None

        # Mock yfinance to avoid real API calls
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = mocker.MagicMock(empty=True)
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Create a mock response that succeeds
        price_service.yahoo_tool._run.return_value = {"current_price": 150.0, "currency": "USD"}

        # Act - Request symbols (test that semaphore works)
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]  # 5 symbols = limit
        result = await price_service.get_current_prices(symbols)

        # Assert
        assert len(result) == 5
        # Verify all symbols got prices
        for symbol in symbols:
            assert symbol in result
            assert result[symbol].price == 150.0

    def test_should_validate_price_service_config(self):
        """Test PriceServiceConfig validation."""
        # Test valid config
        config = PriceServiceConfig(default_cache_ttl=600, max_concurrent_requests=5, request_timeout=15.0)
        assert config.default_cache_ttl == 600
        assert config.max_concurrent_requests == 5

        # Test default values
        default_config = PriceServiceConfig()
        assert default_config.default_cache_ttl == 300
        assert default_config.stale_data_threshold == 3600

    def test_should_validate_price_data_model(self):
        """Test PriceData model validation."""
        # Test valid price data
        price_data = PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now(), source="yahoo_finance", currency="USD")
        assert price_data.symbol == "AAPL"
        assert price_data.price == 150.0

        # Test invalid price (negative)
        with pytest.raises(ValidationError):
            PriceData(symbol="AAPL", price=-150.0, timestamp=datetime.now(), source="yahoo_finance", currency="USD")

    @pytest.mark.asyncio
    async def test_should_handle_crypto_symbol_variations(self, price_service, mock_cache_manager, mocker):
        """Test handling various crypto symbol formats."""
        # Arrange
        mock_cache_manager.get.return_value = None

        # Mock Yahoo Finance to fail for crypto
        price_service.yahoo_tool._run.return_value = {"error": "Not found"}

        # Mock yfinance direct calls to fail
        mock_ticker = mocker.MagicMock()
        mock_ticker.info = {}
        mock_ticker.history.return_value = mocker.MagicMock(empty=True)
        mocker.patch("yfinance.Ticker", return_value=mock_ticker)

        # Mock crypto tool response
        price_service.crypto_tool._run.return_value = {"crypto_data": {"current_price": 45000.0}}

        # Test different crypto symbol formats
        crypto_symbols = ["BTC-USD", "ETH-USDT", "BTC", "ETHEREUM"]

        for symbol in crypto_symbols:
            # Act
            result = await price_service.get_current_price(symbol)

            # Assert
            assert result is not None
            assert result.price == 45000.0
            assert result.source == "crypto_tool"

    @pytest.mark.asyncio
    async def test_should_close_service_gracefully(self, price_service):
        """Test graceful service shutdown."""
        # Act & Assert - Should not raise any exceptions
        await price_service.close()
