"""
Shared caching service for portfolio analysis and rebalancing operations.

This module provides intelligent caching specifically designed for portfolio
operations, with cache warming, invalidation strategies, and performance
optimization for financial data.
"""

import asyncio
from collections.abc import Callable
from typing import Any

from finwiz.tools.logger import get_logger
from finwiz.utils.cache_manager import CacheManager, get_cache_manager

logger = get_logger(__name__)


class PortfolioCacheService:
    """
    Specialized caching service for portfolio operations.

    Provides intelligent caching for price data, portfolio analysis results,
    and rebalancing calculations with appropriate TTL and invalidation strategies.
    """

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        """Initialize the portfolio cache service."""
        self.cache_manager = cache_manager or get_cache_manager()

        # Cache TTL settings (in seconds)
        self.price_data_ttl = 300  # 5 minutes for price data
        self.portfolio_analysis_ttl = 1800  # 30 minutes for portfolio analysis
        self.rebalancing_analysis_ttl = 3600  # 1 hour for rebalancing analysis
        self.validation_ttl = 86400  # 24 hours for ticker validation

    async def get_price_data(self, symbol: str) -> dict[str, Any] | None:
        """
        Get cached price data for a symbol.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Cached price data or None if not found

        """
        cache_key = ["price_data", symbol]
        result: dict[str, Any] | None = await self.cache_manager.get(cache_key)
        return result

    async def set_price_data(self, symbol: str, price_data: dict[str, Any]) -> None:
        """
        Cache price data for a symbol.

        Args:
            symbol: Stock/ETF symbol
            price_data: Price data to cache

        """
        cache_key = ["price_data", symbol]
        await self.cache_manager.set(cache_key, price_data, ttl=self.price_data_ttl, tags={"price_data", "market_data"})
        logger.debug(f"Cached price data for {symbol}")

    async def get_portfolio_analysis(self, portfolio_hash: str) -> dict[str, Any] | None:
        """
        Get cached portfolio analysis result.

        Args:
            portfolio_hash: Hash of portfolio configuration

        Returns:
            Cached analysis result or None if not found

        """
        cache_key = ["portfolio_analysis", portfolio_hash]
        result: dict[str, Any] | None = await self.cache_manager.get(cache_key)
        return result

    async def set_portfolio_analysis(self, portfolio_hash: str, analysis_result: dict[str, Any]) -> None:
        """
        Cache portfolio analysis result.

        Args:
            portfolio_hash: Hash of portfolio configuration
            analysis_result: Analysis result to cache

        """
        cache_key = ["portfolio_analysis", portfolio_hash]
        await self.cache_manager.set(cache_key, analysis_result, ttl=self.portfolio_analysis_ttl, tags={"portfolio_analysis", "analysis"})
        logger.debug(f"Cached portfolio analysis for hash {portfolio_hash[:8]}...")

    async def get_rebalancing_analysis(self, portfolio_hash: str, target_weights_hash: str) -> dict[str, Any] | None:
        """
        Get cached rebalancing analysis result.

        Args:
            portfolio_hash: Hash of portfolio configuration
            target_weights_hash: Hash of target weights

        Returns:
            Cached rebalancing result or None if not found

        """
        cache_key = ["rebalancing_analysis", portfolio_hash, target_weights_hash]
        result: dict[str, Any] | None = await self.cache_manager.get(cache_key)
        return result

    async def set_rebalancing_analysis(self, portfolio_hash: str, target_weights_hash: str, rebalancing_result: dict[str, Any]) -> None:
        """
        Cache rebalancing analysis result.

        Args:
            portfolio_hash: Hash of portfolio configuration
            target_weights_hash: Hash of target weights
            rebalancing_result: Rebalancing result to cache

        """
        cache_key = ["rebalancing_analysis", portfolio_hash, target_weights_hash]
        await self.cache_manager.set(cache_key, rebalancing_result, ttl=self.rebalancing_analysis_ttl, tags={"rebalancing_analysis", "analysis"})
        logger.debug(f"Cached rebalancing analysis for portfolio {portfolio_hash[:8]}...")

    async def get_ticker_validation(self, symbol: str, asset_class: str) -> dict[str, Any] | None:
        """
        Get cached ticker validation result.

        Args:
            symbol: Stock/ETF symbol
            asset_class: Asset class (stock/etf)

        Returns:
            Cached validation result or None if not found

        """
        cache_key = ["ticker_validation", symbol, asset_class]
        result: dict[str, Any] | None = await self.cache_manager.get(cache_key)
        return result

    async def set_ticker_validation(self, symbol: str, asset_class: str, validation_result: dict[str, Any]) -> None:
        """
        Cache ticker validation result.

        Args:
            symbol: Stock/ETF symbol
            asset_class: Asset class (stock/etf)
            validation_result: Validation result to cache

        """
        cache_key = ["ticker_validation", symbol, asset_class]
        await self.cache_manager.set(cache_key, validation_result, ttl=self.validation_ttl, tags={"ticker_validation", "validation"})
        logger.debug(f"Cached ticker validation for {symbol}")

    async def warm_portfolio_cache(self, symbols: list[str]) -> None:
        """
        Warm cache with price data for portfolio symbols.

        Args:
            symbols: List of symbols to warm cache for

        """
        logger.info(f"Warming cache for {len(symbols)} symbols")

        # Import here to avoid circular imports
        from finwiz.tools.portfolio_price_service import PortfolioPriceService

        price_service = PortfolioPriceService()

        # Fetch prices in parallel
        tasks = []
        for symbol in symbols:
            task = self._warm_symbol_cache(price_service, symbol)
            tasks.append(task)

        # Execute with limited concurrency to avoid rate limits
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

        async def limited_task(task: Any) -> Any:
            async with semaphore:
                return await task

        results = await asyncio.gather(*[limited_task(task) for task in tasks], return_exceptions=True)

        successful_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Cache warming completed: {successful_count}/{len(symbols)} successful")

    async def _warm_symbol_cache(self, price_service: Any, symbol: str) -> None:
        """Warm cache for a single symbol."""
        try:
            # Check if already cached
            cached_price = await self.get_price_data(symbol)
            if cached_price is not None:
                return

            # Fetch and cache price data
            price_data = await price_service.get_price_with_fallback(symbol)
            await self.set_price_data(symbol, price_data.model_dump())

        except Exception as e:
            logger.warning(f"Failed to warm cache for {symbol}: {e}")

    async def invalidate_market_data(self) -> int:
        """
        Invalidate all market data caches (price data, etc.).

        Returns:
            Number of entries invalidated

        """
        logger.info("Invalidating market data caches")
        return await self.cache_manager.clear(tags={"price_data", "market_data"})

    async def invalidate_analysis_cache(self) -> int:
        """
        Invalidate all analysis caches.

        Returns:
            Number of entries invalidated

        """
        logger.info("Invalidating analysis caches")
        return await self.cache_manager.clear(tags={"portfolio_analysis", "rebalancing_analysis"})

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Cache statistics

        """
        base_stats = self.cache_manager.get_stats()

        # Add portfolio-specific metrics
        portfolio_stats = {
            **base_stats,
            "cache_ttl_settings": {
                "price_data_ttl": self.price_data_ttl,
                "portfolio_analysis_ttl": self.portfolio_analysis_ttl,
                "rebalancing_analysis_ttl": self.rebalancing_analysis_ttl,
                "validation_ttl": self.validation_ttl,
            },
            "cache_effectiveness": {
                "hit_rate_good": base_stats["hit_rate"] >= 0.7,
                "recommendation": self._get_cache_recommendation(base_stats["hit_rate"]),
            },
        }

        return portfolio_stats

    def _get_cache_recommendation(self, hit_rate: float) -> str:
        """Get cache performance recommendation."""
        if hit_rate >= 0.8:
            return "Excellent cache performance"
        elif hit_rate >= 0.6:
            return "Good cache performance"
        elif hit_rate >= 0.4:
            return "Consider cache warming or longer TTL"
        else:
            return "Poor cache performance - review caching strategy"

    async def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up

        """
        return await self.cache_manager.cleanup_expired()


# Global portfolio cache service instance
_portfolio_cache_service: PortfolioCacheService | None = None


def get_portfolio_cache_service() -> PortfolioCacheService:
    """Get the global portfolio cache service instance."""
    global _portfolio_cache_service
    if _portfolio_cache_service is None:
        _portfolio_cache_service = PortfolioCacheService()
    return _portfolio_cache_service


async def with_portfolio_cache(cache_key: str | list[Any], compute_func: Callable[..., Any], ttl: int | None = None, *args: Any, **kwargs: Any) -> Any:
    """
    Execute function with portfolio-specific caching.

    Args:
        cache_key: Cache key or key parts
        compute_func: Function to execute if not cached
        ttl: Time-to-live for cache entry
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Cached or computed result

    """
    cache_service = get_portfolio_cache_service()

    # Try to get from cache first
    try:
        result = await cache_service.cache_manager.get(cache_key)
        if result is not None:
            return result
    except Exception as e:
        logger.warning(f"Cache get failed for key {cache_key}: {e}")

    # Execute function and cache result
    if asyncio.iscoroutinefunction(compute_func):
        result = await compute_func(*args, **kwargs)
    else:
        result = compute_func(*args, **kwargs)

    # Try to cache the result
    try:
        await cache_service.cache_manager.set(cache_key, result, ttl=ttl)
    except Exception as e:
        logger.warning(f"Cache set failed for key {cache_key}: {e}")

    return result
