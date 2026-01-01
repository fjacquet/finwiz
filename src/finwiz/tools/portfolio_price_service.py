"""
Portfolio price data service for FinWiz.

This module provides a centralized service for retrieving current market prices
for portfolio holdings with caching, fallback mechanisms, and support for
multiple asset classes (stocks, ETFs, crypto).
"""

import asyncio
from datetime import datetime
from typing import Any

import yfinance as yf  # yfinance has no official type stubs
from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_rebalancing import PriceData
from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_cache_service import get_portfolio_cache_service
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool
from finwiz.utils.cache_manager import CacheManager, get_cache_manager

logger = get_logger(__name__)


class PriceServiceError(Exception):
    """Base exception for price service errors."""

    pass


class PriceDataUnavailableError(PriceServiceError):
    """Raised when price data cannot be retrieved from any source."""

    def __init__(self, symbol: str, reason: str) -> None:
        """Initialize the exception with symbol and reason."""
        super().__init__(f"Price data unavailable for {symbol}: {reason}")
        self.symbol = symbol
        self.reason = reason


class StaleDataWarning(UserWarning):
    """Warning for stale price data."""

    pass


class PriceServiceConfig(BaseModel):
    """Configuration for portfolio price service."""

    default_cache_ttl: int = Field(default=300, description="Default cache TTL in seconds (5 minutes)")
    stale_data_threshold: int = Field(default=3600, description="Stale data threshold in seconds (1 hour)")
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent price requests")
    request_timeout: float = Field(default=30.0, description="Request timeout in seconds")
    enable_crypto_fallback: bool = Field(default=True, description="Enable crypto-specific fallback sources")
    retry_attempts: int = Field(default=3, description="Number of retry attempts for failed requests")
    retry_delay: float = Field(default=1.0, description="Delay between retry attempts in seconds")


class PortfolioPriceService:
    """
    Centralized service for retrieving current market prices for portfolio holdings.

    Provides price data with caching, fallback mechanisms, and support for
    multiple asset classes including stocks, ETFs, and cryptocurrencies.
    """

    def __init__(self, config: PriceServiceConfig | None = None, cache_manager: CacheManager | None = None) -> None:
        """Initialize the portfolio price service."""
        self.config = config or PriceServiceConfig()
        self.cache_manager = cache_manager or get_cache_manager()
        self.portfolio_cache = get_portfolio_cache_service()

        # Initialize tools
        self.yahoo_tool = YahooFinanceTickerInfoTool()
        self.crypto_tool = EnhancedCryptoAnalysisTool()

        # Semaphore for controlling concurrent requests
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)

        logger.info("Portfolio price service initialized with shared caching")

    async def get_current_prices(self, symbols: list[str]) -> dict[str, PriceData]:
        """
        Get current prices for multiple symbols concurrently.

        Args:
            symbols: List of symbols to get prices for

        Returns:
            Dictionary mapping symbols to PriceData objects

        Raises:
            PriceServiceError: If critical errors occur during price retrieval

        """
        logger.info(f"Retrieving prices for {len(symbols)} symbols: {symbols}")

        # Create tasks for concurrent price retrieval
        tasks = [self.get_current_price(symbol) for symbol in symbols]

        try:
            # Execute all price requests concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results - explicitly typed since we filter out exceptions below
            price_data: dict[str, PriceData] = {}
            failed_symbols: list[str] = []

            for symbol, result in zip(symbols, results):
                if isinstance(result, BaseException):
                    logger.warning(f"Failed to get price for {symbol}: {result}")
                    failed_symbols.append(symbol)
                elif result is not None:
                    price_data[symbol] = result
                else:
                    failed_symbols.append(symbol)

            if failed_symbols:
                logger.warning(f"Failed to retrieve prices for symbols: {failed_symbols}")

            logger.info(f"Successfully retrieved prices for {len(price_data)} out of {len(symbols)} symbols")
            return price_data

        except Exception as e:
            logger.error(f"Critical error in batch price retrieval: {e}")
            raise PriceServiceError(f"Batch price retrieval failed: {e}") from e

    async def get_current_price(self, symbol: str) -> PriceData | None:
        """
        Get current price for a single symbol with caching and fallback.

        Args:
            symbol: Symbol to get price for

        Returns:
            PriceData object or None if price cannot be retrieved

        """
        async with self._semaphore:
            return await self._get_price_with_cache(symbol)

    async def _get_price_with_cache(self, symbol: str) -> PriceData | None:
        """Get price with shared portfolio caching logic."""
        symbol = symbol.upper()

        try:
            # Try to get from portfolio cache first
            cached_data = await self.portfolio_cache.get_price_data(symbol)
            if cached_data is not None:
                # Check if cached data is still fresh
                if isinstance(cached_data, dict) and "timestamp" in cached_data:
                    cached_time = datetime.fromisoformat(cached_data["timestamp"])
                    age_seconds = (datetime.now() - cached_time).total_seconds()

                    if age_seconds < self.config.stale_data_threshold:
                        logger.debug(f"Using cached price for {symbol} (age: {age_seconds:.0f}s)")
                        return PriceData(**cached_data)
                    else:
                        logger.warning(f"Cached price for {symbol} is stale (age: {age_seconds:.0f}s)")

            # Get fresh price data
            price_data = await self._fetch_price_with_fallback(symbol)

            if price_data is not None:
                # Cache the result using portfolio cache service
                await self.portfolio_cache.set_price_data(symbol, price_data.model_dump())
                logger.debug(f"Cached fresh price for {symbol}")

            return price_data

        except Exception as e:
            logger.error(f"Error in price caching logic for {symbol}: {e}")
            # Try to get price without caching
            return await self._fetch_price_with_fallback(symbol)

    async def _fetch_price_with_fallback(self, symbol: str) -> PriceData | None:
        """Fetch price with fallback mechanisms."""
        symbol = symbol.upper().strip()

        # Determine asset class and try appropriate sources
        if self._is_crypto_symbol(symbol):
            return await self._get_crypto_price(symbol)
        else:
            return await self._get_stock_etf_price(symbol)

    def _is_crypto_symbol(self, symbol: str) -> bool:
        """Determine if symbol is likely a cryptocurrency."""
        # Common crypto patterns
        crypto_patterns = [
            "-USD",
            "-USDT",
            "-BTC",
            "-ETH",  # Crypto pairs
            "BTC",
            "ETH",
            "ADA",
            "DOT",
            "SOL",
            "AVAX",
            "MATIC",
            "LINK",  # Major cryptos
        ]

        return any(pattern in symbol for pattern in crypto_patterns) or len(symbol) > 5

    async def _get_stock_etf_price(self, symbol: str) -> PriceData | None:
        """Get price for stocks/ETFs using Yahoo Finance with fallback."""
        for attempt in range(self.config.retry_attempts):
            try:
                # Primary: Use Yahoo Finance ticker info tool
                result = await asyncio.wait_for(asyncio.to_thread(self.yahoo_tool._run, symbol), timeout=self.config.request_timeout)

                if isinstance(result, dict) and "error" not in result:
                    current_price = result.get("current_price")
                    if current_price and current_price != "N/A":
                        return PriceData(
                            symbol=symbol,
                            price=float(current_price),
                            timestamp=datetime.now(),
                            source="yahoo_finance",
                            currency=result.get("currency", "USD"),
                        )

                # Fallback: Direct yfinance call
                logger.debug(f"Yahoo Finance tool failed for {symbol}, trying direct yfinance")
                ticker = yf.Ticker(symbol)
                info = await asyncio.to_thread(ticker.info.get, "regularMarketPrice")

                if info and info > 0:
                    return PriceData(symbol=symbol, price=float(info), timestamp=datetime.now(), source="yfinance_direct", currency="USD")

                # Second fallback: Try history data
                logger.debug(f"Direct yfinance failed for {symbol}, trying history data")
                hist = await asyncio.to_thread(ticker.history, period="1d")

                if not hist.empty and "Close" in hist.columns:
                    latest_price = hist["Close"].iloc[-1]
                    if latest_price > 0:
                        return PriceData(
                            symbol=symbol,
                            price=float(latest_price),
                            timestamp=datetime.now(),
                            source="yfinance_history",
                            currency="USD",
                        )

            except TimeoutError:
                logger.warning(f"Timeout getting price for {symbol} (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Error getting price for {symbol} (attempt {attempt + 1}): {e}")

            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        logger.error(f"All attempts failed to get price for stock/ETF {symbol}")
        return None

    async def _get_crypto_price(self, symbol: str) -> PriceData | None:
        """Get price for cryptocurrencies with crypto-specific fallbacks."""
        if not self.config.enable_crypto_fallback:
            return await self._get_stock_etf_price(symbol)

        for attempt in range(self.config.retry_attempts):
            try:
                # Primary: Try Yahoo Finance first (works for major crypto pairs)
                if "-USD" in symbol or symbol in ["BTC-USD", "ETH-USD"]:
                    price_data = await self._get_stock_etf_price(symbol)
                    if price_data is not None:
                        return price_data

                # Fallback: Use enhanced crypto tool
                logger.debug(f"Trying crypto tool for {symbol}")
                crypto_symbol = symbol.replace("-USD", "").replace("-USDT", "")

                result = await asyncio.wait_for(asyncio.to_thread(self.crypto_tool._run, crypto_symbol, False, False), timeout=self.config.request_timeout)

                if isinstance(result, dict) and "error" not in result:
                    crypto_data = result.get("crypto_data", {})
                    current_price = crypto_data.get("current_price")

                    if current_price and current_price > 0:
                        return PriceData(
                            symbol=symbol,
                            price=float(current_price),
                            timestamp=datetime.now(),
                            source="crypto_tool",
                            currency="USD",
                        )

                # Last resort: Try yfinance with common crypto suffixes
                for suffix in ["-USD", "-USDT"]:
                    try:
                        test_symbol = f"{crypto_symbol}{suffix}"
                        ticker = yf.Ticker(test_symbol)
                        info = await asyncio.to_thread(ticker.info.get, "regularMarketPrice")

                        if info and info > 0:
                            return PriceData(symbol=symbol, price=float(info), timestamp=datetime.now(), source="yfinance_crypto", currency="USD")
                    except Exception:
                        continue

            except TimeoutError:
                logger.warning(f"Timeout getting crypto price for {symbol} (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"Error getting crypto price for {symbol} (attempt {attempt + 1}): {e}")

            if attempt < self.config.retry_attempts - 1:
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        logger.error(f"All attempts failed to get price for crypto {symbol}")
        return None

    async def get_price_with_fallback(self, symbol: str) -> PriceData:
        """
        Get price with fallback, raising exception if all sources fail.

        Args:
            symbol: Symbol to get price for

        Returns:
            PriceData object

        Raises:
            PriceDataUnavailableError: If price cannot be retrieved from any source

        """
        price_data = await self.get_current_price(symbol)

        if price_data is None:
            raise PriceDataUnavailableError(symbol, "All price sources failed")

        return price_data

    async def validate_symbols(self, symbols: list[str]) -> dict[str, bool]:
        """
        Validate that symbols exist and have available price data.

        Args:
            symbols: List of symbols to validate

        Returns:
            Dictionary mapping symbols to validation status (True/False)

        """
        logger.info(f"Validating {len(symbols)} symbols")

        validation_results = {}

        # Try to get prices for all symbols
        price_data = await self.get_current_prices(symbols)

        for symbol in symbols:
            validation_results[symbol] = symbol in price_data

        valid_count = sum(validation_results.values())
        logger.info(f"Validated {valid_count} out of {len(symbols)} symbols")

        return validation_results

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for price data."""
        stats = self.cache_manager.get_stats()

        # Add price-specific stats
        price_cache_keys = 0
        try:
            # This is a simplified way to count price cache keys
            # In a real implementation, you might want to track this more precisely
            all_stats = stats.copy()
            all_stats["price_cache_keys"] = price_cache_keys
            all_stats["service_config"] = self.config.model_dump()
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            all_stats = stats

        return all_stats

    async def clear_price_cache(self, symbols: list[str] | None = None) -> int:
        """
        Clear price cache for specific symbols or all price data.

        Args:
            symbols: List of symbols to clear cache for, or None to clear all

        Returns:
            Number of cache entries cleared

        """
        if symbols is None:
            # Clear all price cache entries
            logger.info("Clearing all price cache entries")
            return await self.cache_manager.clear(tags={"price"})
        else:
            # Clear specific symbols
            logger.info(f"Clearing price cache for symbols: {symbols}")
            cleared_count = 0

            for symbol in symbols:
                cache_key = f"price:{symbol.upper()}"
                if await self.cache_manager.delete(cache_key):
                    cleared_count += 1

            return cleared_count

    async def warm_cache(self, symbols: list[str]) -> dict[str, bool]:
        """
        Warm the cache by pre-loading price data for symbols.

        Args:
            symbols: List of symbols to warm cache for

        Returns:
            Dictionary mapping symbols to success status

        """
        logger.info(f"Warming price cache for {len(symbols)} symbols")

        # Get prices for all symbols (this will cache them)
        price_data = await self.get_current_prices(symbols)

        # Return success status for each symbol
        return {symbol: symbol in price_data for symbol in symbols}

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing portfolio price service")
        # The cache manager cleanup is handled by the cache manager itself
