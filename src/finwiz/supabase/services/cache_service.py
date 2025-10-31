"""
Cache service for high-level caching logic.

Provides transparent caching layer with:
- Cache check with TTL validation
- Automatic crew execution fallback on cache miss
- Non-blocking storage after crew execution
- Cache hit/miss logging and metrics tracking
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for analysis caching with transparent fallback.

    Provides high-level caching logic that:
    - Checks cache for recent analysis (within TTL)
    - Falls back to crew execution on cache miss/timeout
    - Stores results asynchronously after execution
    - Tracks cache hit/miss metrics

    Attributes:
        repository: AnalysisRepository for database operations
        ttl_hours: Cache TTL in hours (from environment or default 24)
        cache_hits: Counter for cache hits (for metrics)
        cache_misses: Counter for cache misses (for metrics)

    """

    def __init__(self, repository: AnalysisRepository) -> None:
        """
        Initialize cache service.

        Args:
            repository: AnalysisRepository instance for database operations

        """
        self.repository = repository
        self.ttl_hours = int(os.getenv("ANALYSIS_CACHE_TTL_HOURS", "24"))
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(f"CacheService initialized with TTL: {self.ttl_hours} hours")

    async def get_or_execute(
        self,
        ticker: str,
        asset_class: str,
        execute_fn: Callable[[], Any],
    ) -> tuple[dict[str, Any], bool]:
        """
        Get cached analysis or execute crew.

        Attempts to retrieve cached analysis within TTL. On cache miss or timeout,
        executes the provided function (typically crew execution) and stores the
        result asynchronously.

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

        logger.debug(f"Cache check for {ticker_upper} ({asset_class_lower}), TTL: {self.ttl_hours}h")

        # Try cache first (with timeout)
        try:
            cached = await self.repository.get_cached_analysis(
                ticker=ticker_upper,
                asset_class=asset_class_lower,
                ttl_hours=self.ttl_hours,
            )

            if cached:
                # Cache hit - return cached data
                self.cache_hits += 1
                logger.info(f"✅ Cache HIT for {ticker_upper} ({asset_class_lower}) [Hit rate: {self.get_hit_rate():.1%}]")
                return cached.export_json, True

        except Exception as e:
            # Cache check failed - log and proceed with execution
            logger.warning(f"Cache check failed for {ticker_upper}: {e}")

        # Cache miss or timeout - execute crew
        self.cache_misses += 1
        logger.info(f"❌ Cache MISS for {ticker_upper} ({asset_class_lower}), executing crew [Hit rate: {self.get_hit_rate():.1%}]")

        # Execute crew (this may take time)
        result = await execute_fn()

        # Ensure result is a dict
        if not isinstance(result, dict):
            logger.error(f"execute_fn returned {type(result)}, expected dict. Converting to dict for storage.")
            result = {"raw_result": str(result)}

        # Store result asynchronously (non-blocking)
        try:
            await self.repository.store_analysis(
                ticker=ticker_upper,
                asset_class=asset_class_lower,
                export_data=result,
            )
            logger.debug(f"Scheduled async storage for {ticker_upper} ({asset_class_lower})")
        except Exception as e:
            # Storage failure should not fail the analysis
            logger.error(f"Failed to schedule storage for {ticker_upper}: {e}")

        return result, False

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
