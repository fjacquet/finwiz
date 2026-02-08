"""Tests for CacheMetricsLogger."""

import pytest

from finwiz.infrastructure.caching.metrics_logger import CacheMetricsLogger


class FakeCache:
    """Minimal cache mock with get_stats()."""

    def __init__(self, hits: int = 10, misses: int = 5, evictions: int = 1):
        self._hits = hits
        self._misses = misses
        self._evictions = evictions

    def get_stats(self) -> dict:
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
            "evictions": self._evictions,
            "tiers": {"hot": 2, "warm": 3, "cold": 5},
        }


class BrokenCache:
    def get_stats(self) -> dict:
        raise RuntimeError("stats unavailable")


class TestCacheMetricsLogger:
    def test_register_and_aggregate(self):
        ml = CacheMetricsLogger()
        ml.register_cache("main", FakeCache(hits=10, misses=5, evictions=1))
        ml.register_cache("crew", FakeCache(hits=3, misses=2, evictions=0))

        stats = ml.get_aggregated_stats()
        assert stats["total"]["hits"] == 13
        assert stats["total"]["misses"] == 7
        assert stats["total"]["evictions"] == 1
        assert stats["total"]["hit_rate"] == pytest.approx(13 / 20)

    def test_empty_no_caches(self):
        ml = CacheMetricsLogger()
        stats = ml.get_aggregated_stats()
        assert stats["total"]["hits"] == 0
        assert stats["total"]["hit_rate"] == 0.0

    def test_broken_cache_handled(self):
        ml = CacheMetricsLogger()
        ml.register_cache("broken", BrokenCache())
        stats = ml.get_aggregated_stats()
        assert "error" in stats["per_cache"]["broken"]
        assert stats["total"]["hits"] == 0

    def test_log_summary_no_error(self):
        ml = CacheMetricsLogger()
        ml.register_cache("main", FakeCache())
        ml.log_summary()  # Should not raise

    def test_log_summary_empty(self):
        ml = CacheMetricsLogger()
        ml.log_summary()  # Should not raise with no caches
