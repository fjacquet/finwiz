"""
Cache service for high-level caching logic.

Provides transparent caching layer with:
- Cache check with TTL validation
- Automatic crew execution fallback on cache miss
- Non-blocking storage after crew execution
- Cache hit/miss logging and metrics tracking
- Graceful degradation when Supabase is unavailable
- Comprehensive monitoring and observability
"""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.utils.monitoring import CacheMetrics

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for analysis caching with transparent fallback.

    Provides high-level caching logic that:
    - Checks cache for recent analysis (within TTL)
    - Falls back to crew execution on cache miss/timeout
    - Stores results asynchronously after execution
    - Tracks cache hit/miss metrics
    - Gracefully degrades when Supabase is unavailable

    Attributes:
        repository: AnalysisRepository for database operations
        client: SupabaseClient for connectivity testing
        ttl_hours: Cache TTL in hours (from environment or default 24)
        is_enabled: Whether caching is enabled (set by connectivity test)
        cache_hits: Counter for cache hits (for metrics)
        cache_misses: Counter for cache misses (for metrics)

    """

    def __init__(
        self,
        repository: AnalysisRepository,
        client: SupabaseClient,
        cache_metrics: CacheMetrics | None = None,
    ) -> None:
        """
        Initialize cache service.

        Args:
            repository: AnalysisRepository instance for database operations
            client: SupabaseClient instance for connectivity testing
            cache_metrics: Optional CacheMetrics instance for tracking

        """
        self.repository = repository
        self.client = client
        self.ttl_hours = int(os.getenv("ANALYSIS_CACHE_TTL_HOURS", "24"))
        self.is_enabled = False  # Set by initialize()
        self.cache_metrics = cache_metrics or CacheMetrics()

        # Keep legacy counters for backward compatibility
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"CacheService initialized with TTL: {self.ttl_hours} hours")

    async def initialize(self) -> bool:
        """
        Initialize cache service with connectivity test.

        Tests Supabase connectivity and sets is_enabled flag based on result.
        Should be called before using the cache service.

        Returns:
            True if connectivity test passed and caching is enabled, False otherwise

        """
        if not self.client:
            logger.info("ℹ️ No Supabase client - caching disabled")
            self.is_enabled = False
            return False

        # Test connectivity - will raise ConnectionError if Supabase is enabled but misconfigured
        try:
            self.is_enabled = await self.client.test_connectivity()

            if self.is_enabled:
                logger.info("✅ Cache service initialized successfully")
            else:
                logger.info("ℹ️ Cache service disabled - analysis will proceed without cache")

            return self.is_enabled
        except ConnectionError:
            # Re-raise to fail fast on misconfiguration
            raise

    async def health_check(self) -> bool:
        """
        Check cache service health without reinitialization.

        Tests connectivity to Supabase without modifying the is_enabled flag.
        Suitable for periodic health checks after initialization.

        Returns:
            True if cache service is healthy and available, False otherwise

        """
        if not self.client:
            logger.debug("Health check: No Supabase client configured")
            return False

        if not self.is_enabled:
            logger.debug("Health check: Cache service is disabled")
            return False

        try:
            is_healthy = await self.client.test_connectivity()
            if is_healthy:
                logger.debug("✅ Cache service health check passed")
            else:
                logger.debug("⚠️ Cache service health check failed")
            return is_healthy
        except Exception as e:
            logger.debug(f"⚠️ Cache service health check error: {e}")
            return False

    async def get_or_execute(
        self,
        ticker: str,
        asset_class: str,
        execute_fn: Callable[[], Any],
    ) -> tuple[dict[str, Any], bool]:
        """
        Get cached analysis or execute crew with graceful fallback.

        Attempts to retrieve cached analysis within TTL. On cache miss, timeout,
        or when cache is disabled, executes the provided function (typically crew
        execution) and stores the result asynchronously.

        Args:
            ticker: Asset ticker symbol
            asset_class: Asset class (stock, etf, crypto)
            execute_fn: Function to execute on cache miss (returns analysis dict)

        Returns:
            Tuple of (analysis_dict, is_cached) where:
            - analysis_dict: Complete analysis export data
            - is_cached: True if from cache, False if freshly executed

        """
        # Normalize inputs
        ticker_upper = ticker.upper()
        asset_class_lower = asset_class.lower()

        # Skip cache if not enabled
        if not self.is_enabled:
            logger.debug(f"Cache DISABLED for {ticker_upper} ({asset_class_lower}) - executing fresh analysis")
            result = await execute_fn()

            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.error(f"execute_fn returned {type(result)}, expected dict. Converting to dict.")
                result = {"raw_result": str(result)}

            return result, False

        logger.debug(f"Cache check for {ticker_upper} ({asset_class_lower}), TTL: {self.ttl_hours}h")

        # Try cache read with timeout
        try:
            cached = await asyncio.wait_for(
                self.repository.get_cached_analysis(
                    ticker=ticker_upper,
                    asset_class=asset_class_lower,
                    ttl_hours=self.ttl_hours,
                ),
                timeout=self.client.read_timeout,
            )

            if cached:
                # Cache hit - return cached data
                self.cache_hits += 1
                self.cache_metrics.record_hit()
                logger.info(f"✅ Cache HIT for {ticker_upper} ({asset_class_lower}) [Hit rate: {self.get_hit_rate():.1%}]")
                return cached.export_json, True

        except TimeoutError:
            self.cache_metrics.record_timeout()
            logger.warning(f"⚠️ Cache read timeout for {ticker_upper} (>{self.client.read_timeout}s) - proceeding with fresh analysis")
        except Exception as e:
            # Cache check failed - log and proceed with execution
            self.cache_metrics.record_error()
            logger.warning(f"⚠️ Cache read failed for {ticker_upper}: {e}")

        # Cache miss or timeout - execute crew
        self.cache_misses += 1
        self.cache_metrics.record_miss()
        logger.info(f"❌ Cache MISS for {ticker_upper} ({asset_class_lower}), executing crew [Hit rate: {self.get_hit_rate():.1%}]")

        # Execute crew (this may take time)
        result = await execute_fn()

        # Ensure result is a dict
        if not isinstance(result, dict):
            logger.error(f"execute_fn returned {type(result)}, expected dict. Converting to dict for storage.")
            result = {"raw_result": str(result)}

        # Store result asynchronously (non-blocking) if cache is enabled
        if self.is_enabled:
            asyncio.create_task(self._store_async(ticker_upper, asset_class_lower, result))

        return result, False

    async def _store_async(self, ticker: str, asset_class: str, export_data: dict[str, Any]) -> None:
        """
        Store analysis result asynchronously without blocking.

        Wraps cache write in try/except with timeout to ensure it doesn't
        block the analysis workflow. Logs failures as warnings.

        Args:
            ticker: Asset ticker symbol (already normalized to uppercase)
            asset_class: Asset class (already normalized to lowercase)
            export_data: Analysis export data to store

        """
        try:
            await asyncio.wait_for(
                self.repository.store_analysis(
                    ticker=ticker,
                    asset_class=asset_class,
                    export_data=export_data,
                ),
                timeout=self.client.write_timeout,
            )
            logger.debug(f"✅ Cached {ticker} ({asset_class})")
        except TimeoutError:
            logger.warning(f"⚠️ Cache write timeout for {ticker} (>{self.client.write_timeout}s)")
        except Exception as e:
            logger.warning(f"⚠️ Cache write failed for {ticker}: {e}")

    def get_hit_rate(self) -> float:
        """
        Calculate cache hit rate.

        Returns:
            Cache hit rate as float between 0.0 and 1.0

        """
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def get_metrics(self) -> dict[str, Any]:
        """
        Get cache metrics.

        Returns:
            Dictionary with cache metrics:
            - cache_hits: Number of cache hits
            - cache_misses: Number of cache misses
            - hit_rate: Cache hit rate (0.0 to 1.0)
            - total_requests: Total cache requests
            - ttl_hours: Configured TTL in hours

        """
        total = self.cache_hits + self.cache_misses
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.get_hit_rate(),
            "total_requests": total,
            "ttl_hours": self.ttl_hours,
        }

    def reset_metrics(self) -> None:
        """
        Reset cache metrics.

        Useful for testing or periodic metric resets.
        """
        self.cache_hits = 0
        self.cache_misses = 0
        logger.debug("Cache metrics reset")

    def log_metrics(self) -> None:
        """
        Log current cache metrics.

        Logs cache performance metrics at INFO level.
        """
        metrics = self.get_metrics()
        logger.info(
            f"Cache Metrics: "
            f"Hits={metrics['cache_hits']}, "
            f"Misses={metrics['cache_misses']}, "
            f"Hit Rate={metrics['hit_rate']:.1%}, "
            f"Total={metrics['total_requests']}, "
            f"TTL={metrics['ttl_hours']}h"
        )
