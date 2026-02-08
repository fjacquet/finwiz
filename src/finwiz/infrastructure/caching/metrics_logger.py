"""Cache metrics aggregation and logging.

Collects statistics from all registered cache instances and logs a summary
at the end of each analysis run for observability (CACHE-03).
"""

from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CacheMetricsLogger:
    """Aggregates and logs cache metrics from multiple cache instances."""

    def __init__(self) -> None:
        self._caches: dict[str, Any] = {}

    def register_cache(self, name: str, cache: Any) -> None:
        """Register a cache instance for metrics collection.

        Args:
            name: Human-readable name for the cache (e.g. "main", "crew").
            cache: Any object with a get_stats() -> dict method.
        """
        self._caches[name] = cache
        logger.debug(f"Registered cache '{name}' for metrics tracking")

    def get_aggregated_stats(self) -> dict[str, Any]:
        """Collect stats from all registered caches.

        Returns:
            Dict with per-cache and total statistics.
        """
        per_cache: dict[str, dict[str, Any]] = {}
        total_hits = 0
        total_misses = 0
        total_evictions = 0

        for name, cache in self._caches.items():
            try:
                stats = cache.get_stats()
                per_cache[name] = stats
                total_hits += stats.get("hits", 0)
                total_misses += stats.get("misses", 0)
                total_evictions += stats.get("evictions", 0)
            except Exception as e:
                logger.warning(f"Failed to get stats from cache '{name}': {e}")
                per_cache[name] = {"error": str(e)}

        total_requests = total_hits + total_misses
        total_hit_rate = total_hits / total_requests if total_requests > 0 else 0.0

        return {
            "per_cache": per_cache,
            "total": {
                "hits": total_hits,
                "misses": total_misses,
                "evictions": total_evictions,
                "hit_rate": total_hit_rate,
            },
        }

    def log_summary(self) -> None:
        """Log a formatted cache metrics summary."""
        if not self._caches:
            logger.debug("No caches registered for metrics logging")
            return

        stats = self.get_aggregated_stats()
        lines = ["Cache Metrics Summary:"]

        for name, cache_stats in stats["per_cache"].items():
            if "error" in cache_stats:
                lines.append(f"  {name}: error - {cache_stats['error']}")
                continue

            hits = cache_stats.get("hits", 0)
            misses = cache_stats.get("misses", 0)
            hit_rate = cache_stats.get("hit_rate", 0.0)
            evictions = cache_stats.get("evictions", 0)
            tiers = cache_stats.get("tiers", {})

            tier_str = ""
            if tiers:
                tier_str = f" | hot:{tiers.get('hot', 0)} warm:{tiers.get('warm', 0)} cold:{tiers.get('cold', 0)}"

            lines.append(f"  {name}: {hits} hits / {misses} misses ({hit_rate:.1%} hit rate){tier_str} | {evictions} evictions")

        total = stats["total"]
        lines.append(f"  TOTAL: {total['hits']} hits / {total['misses']} misses ({total['hit_rate']:.1%} hit rate)")

        logger.info("\n".join(lines))


# Module-level singleton
_metrics_logger: CacheMetricsLogger | None = None


def get_cache_metrics_logger() -> CacheMetricsLogger:
    """Get the global cache metrics logger singleton."""
    global _metrics_logger
    if _metrics_logger is None:
        _metrics_logger = CacheMetricsLogger()
    return _metrics_logger
