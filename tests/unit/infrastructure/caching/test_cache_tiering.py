"""Tests for CacheEntry tiering and tiered eviction."""

import time

import pytest

from finwiz.infrastructure.caching.manager import CacheConfig, CacheEntry, CacheManager, CacheTier


class TestCacheEntryTier:
    def _make_entry(self, access_count: int = 0, last_accessed_ago: float = 0) -> CacheEntry:
        now = time.time()
        return CacheEntry(
            key="test",
            value="data",
            created_at=now - 7200,
            last_accessed=now - last_accessed_ago,
            access_count=access_count,
            ttl=86400,
        )

    def test_hot_tier(self):
        entry = self._make_entry(access_count=5, last_accessed_ago=300)  # 5 accesses, 5min ago
        assert entry.calculate_tier() == CacheTier.HOT

    def test_warm_tier(self):
        entry = self._make_entry(access_count=3, last_accessed_ago=7200)  # 3 accesses, 2h ago
        assert entry.calculate_tier() == CacheTier.WARM

    def test_cold_tier_low_access(self):
        entry = self._make_entry(access_count=1, last_accessed_ago=14400)  # 1 access, 4h ago
        assert entry.calculate_tier() == CacheTier.COLD

    def test_cold_tier_old_access(self):
        entry = self._make_entry(access_count=10, last_accessed_ago=14400)  # many accesses but 4h ago
        assert entry.calculate_tier() == CacheTier.COLD

    def test_warm_boundary(self):
        # Exactly 2 accesses, within 3h
        entry = self._make_entry(access_count=2, last_accessed_ago=10799)
        assert entry.calculate_tier() == CacheTier.WARM

    def test_hot_boundary(self):
        # Exactly 5 accesses, within 1h
        entry = self._make_entry(access_count=5, last_accessed_ago=3599)
        assert entry.calculate_tier() == CacheTier.HOT


class TestTieredEviction:
    @pytest.mark.asyncio
    async def test_evicts_cold_before_hot(self):
        config = CacheConfig(max_memory_items=2)
        cache = CacheManager(config=config)

        now = time.time()
        # Hot entry
        cache.memory_cache["hot"] = CacheEntry(key="hot", value="h", created_at=now - 100, last_accessed=now - 10, access_count=10, ttl=86400)
        # Cold entry
        cache.memory_cache["cold"] = CacheEntry(key="cold", value="c", created_at=now - 5000, last_accessed=now - 5000, access_count=0, ttl=86400)

        await cache._ensure_memory_capacity()

        # Cold should be evicted, hot should remain
        assert "hot" in cache.memory_cache
        assert "cold" not in cache.memory_cache

    @pytest.mark.asyncio
    async def test_no_eviction_under_capacity(self):
        config = CacheConfig(max_memory_items=10)
        cache = CacheManager(config=config)

        now = time.time()
        cache.memory_cache["a"] = CacheEntry(key="a", value="v", created_at=now, last_accessed=now, access_count=0, ttl=86400)

        await cache._ensure_memory_capacity()
        assert "a" in cache.memory_cache

    @pytest.mark.asyncio
    async def test_stats_include_tiers(self):
        cache = CacheManager()
        now = time.time()
        cache.memory_cache["hot"] = CacheEntry(key="hot", value="h", created_at=now - 100, last_accessed=now - 10, access_count=10, ttl=86400)
        cache.memory_cache["cold"] = CacheEntry(key="cold", value="c", created_at=now - 5000, last_accessed=now - 5000, access_count=0, ttl=86400)

        stats = cache.get_stats()
        assert "tiers" in stats
        assert stats["tiers"]["hot"] == 1
        assert stats["tiers"]["cold"] == 1
