"""
Performance tests for the caching system.

This module tests cache effectiveness, hit rates, TTL behavior, and performance
improvements to ensure the caching system meets the requirements for reducing
API costs and improving response times.
"""

import asyncio
import time

import pytest

from finwiz.utils.cache_manager import (
    CacheBackend,
    CacheConfig,
    CacheManager,
    CacheStrategy,
    cache_key,
    cached,
    get_cache_manager,
)


class TestCachePerformance:
    """Performance tests for cache system."""

    @pytest.fixture
    def cache_manager(self):
        """Create a cache manager for testing."""
        config = CacheConfig(
            backend=CacheBackend.MEMORY,
            default_ttl=60,
            max_memory_items=100,
            auto_cleanup=False,  # Disable auto cleanup for tests
        )
        return CacheManager(config)

    @pytest.mark.asyncio
    async def test_should_improve_response_time_with_caching(self, cache_manager, mocker):
        """Test that caching significantly improves response times."""
        # Arrange
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        call_count = 0

        async def slow_function(value: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate slow API call
            return f"result_{value}"

        key = "performance_test_slow_function_test_value"

        # Act - First call (cache miss)
        start_time = time.time()
        result1 = await cached(key, slow_function, "test_value")
        first_call_time = time.time() - start_time

        # Second call (cache hit)
        start_time = time.time()
        result2 = await cached(key, slow_function, "test_value")
        second_call_time = time.time() - start_time

        # Assert
        assert result1 == result2 == "result_test_value"
        assert call_count == 1  # Function called only once
        assert second_call_time < first_call_time * 0.1  # Cache should be much faster
        assert second_call_time < 0.01  # Cache hit should be very fast

    @pytest.mark.asyncio
    async def test_should_achieve_high_hit_rate_with_repeated_requests(self, cache_manager, mocker):
        """Test that cache achieves high hit rates with repeated requests."""
        # Arrange
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        call_count = 0

        async def api_function(symbol: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {"symbol": symbol, "price": 100.0, "timestamp": time.time()}

        symbols = ["AAPL", "GOOGL", "MSFT", "AAPL", "GOOGL", "AAPL"]  # Repeated symbols

        # Act
        results = []
        for symbol in symbols:
            key = f"stock_data_{symbol}"
            result = await cached(key, api_function, symbol, ttl=300)
            results.append(result)

        stats = cache_manager.get_stats()

        # Assert
        assert call_count == 3  # Only unique symbols should trigger API calls
        assert len(results) == 6  # All requests should return results
        assert stats["hit_rate"] >= 0.5  # Should have at least 50% hit rate
        assert stats["hits"] >= 3  # Should have multiple cache hits

    @pytest.mark.asyncio
    async def test_should_respect_ttl_and_refresh_expired_entries(self, cache_manager):
        """Test that cache respects TTL and refreshes expired entries."""
        # Arrange
        call_count = 0

        async def time_sensitive_function(key: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"result_{key}_{time.time()}"

        cache_key_str = cache_key("ttl_test", "function", "test_key")

        # Act - First call
        result1 = await cached(cache_key_str, time_sensitive_function, "test_key", ttl=1)

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # Second call after expiration
        result2 = await cached(cache_key_str, time_sensitive_function, "test_key", ttl=1)

        # Assert
        assert call_count == 2  # Function should be called twice due to expiration
        assert result1 != result2  # Results should be different due to timestamp
        assert result1.startswith("result_test_key_")
        assert result2.startswith("result_test_key_")

    @pytest.mark.asyncio
    async def test_should_handle_concurrent_requests_efficiently(self, cache_manager, mocker):
        """Test cache performance under concurrent load."""
        # Arrange
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        call_count = 0

        async def concurrent_function(request_id: int) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)  # Simulate API delay
            return f"result_{request_id % 3}"  # Only 3 unique results

        # Pre-populate cache to ensure hits
        for i in range(3):
            key = f"concurrent_test_{i}"
            await cache_manager.set(key, f"result_{i}")

        # Act - Launch 20 concurrent requests with only 3 unique keys
        tasks = []
        for i in range(20):
            key = f"concurrent_test_{i % 3}"  # Only 3 unique cache keys
            task = cached(key, concurrent_function, i)
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Assert
        assert len(results) == 20
        assert call_count == 0  # Should not call function due to pre-populated cache
        assert total_time < 0.5  # Should complete quickly due to caching

        # Check that we got the expected unique results
        unique_results = set(results)
        assert len(unique_results) == 3

    @pytest.mark.asyncio
    async def test_should_provide_accurate_performance_metrics(self, cache_manager, mocker):
        """Test that cache provides accurate performance metrics."""
        # Arrange
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        async def metric_test_function(value: int) -> int:
            return value * 2

        # Act - Generate some cache activity
        for i in range(10):
            key = f"metrics_test_{i % 5}"  # 5 unique keys, 10 requests
            await cached(key, metric_test_function, i)

        stats = cache_manager.get_stats()

        # Assert
        assert stats["hits"] + stats["misses"] == 10  # Total requests
        assert stats["hits"] == 5  # 5 cache hits from repeated keys
        assert stats["misses"] == 5  # 5 cache misses from unique keys
        assert stats["hit_rate"] == 0.5  # 50% hit rate
        assert stats["entry_count"] == 5  # 5 unique entries in cache
        assert "total_size_mb" in stats
        assert "average_age_seconds" in stats

    @pytest.mark.asyncio
    async def test_should_handle_cache_eviction_under_memory_pressure(self, cache_manager):
        """Test cache eviction behavior when memory limits are reached."""
        # Arrange - Use small cache for testing eviction
        small_cache_config = CacheConfig(backend=CacheBackend.MEMORY, max_memory_items=5, strategy=CacheStrategy.LRU, auto_cleanup=False)
        small_cache = CacheManager(small_cache_config)

        async def eviction_test_function(value: int) -> str:
            return f"cached_value_{value}"

        # Act - Add more items than cache capacity
        for i in range(10):
            key = cache_key("eviction_test", i)
            await small_cache.set(key, f"value_{i}")

        stats = small_cache.get_stats()

        # Assert
        assert stats["entry_count"] <= 5  # Should not exceed max capacity
        assert stats["evictions"] > 0  # Should have evicted some entries

        # Verify that recent items are still cached (LRU behavior)
        recent_key = cache_key("eviction_test", 9)
        recent_value = await small_cache.get(recent_key)
        assert recent_value == "value_9"

        # Verify that old items were evicted
        old_key = cache_key("eviction_test", 0)
        old_value = await small_cache.get(old_key)
        assert old_value is None

    @pytest.mark.asyncio
    async def test_should_support_cache_warming_for_frequently_accessed_data(self, cache_manager):
        """Test cache warming functionality for performance optimization."""
        # Arrange
        warm_call_count = 0

        async def warm_function_1():
            nonlocal warm_call_count
            warm_call_count += 1
            key = cache_key("warm_data", "popular_stock")
            await cache_manager.set(key, {"symbol": "AAPL", "price": 150.0})

        def warm_function_2():
            nonlocal warm_call_count
            warm_call_count += 1
            # Sync function for testing mixed function types
            pass

        warm_functions = [warm_function_1, warm_function_2]

        # Act
        await cache_manager.warm_cache(warm_functions)

        # Verify warmed data is available
        warmed_key = cache_key("warm_data", "popular_stock")
        warmed_value = await cache_manager.get(warmed_key)

        # Assert
        assert warm_call_count == 2  # Both warm functions should be called
        assert warmed_value is not None
        assert warmed_value["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_should_cleanup_expired_entries_automatically(self, cache_manager):
        """Test automatic cleanup of expired cache entries."""
        # Arrange - Add entries with short TTL
        for i in range(5):
            key = f"cleanup_test_{i}"
            await cache_manager.set(key, f"value_{i}", ttl=1)

        initial_count = cache_manager.get_stats()["entry_count"]

        # Wait for entries to expire
        await asyncio.sleep(1.1)

        # Act - Trigger cleanup
        cleaned_count = await cache_manager.cleanup_expired()

        final_count = cache_manager.get_stats()["entry_count"]

        # Assert
        assert initial_count == 5
        assert cleaned_count >= 5  # All entries should be cleaned up (might be more due to other tests)
        assert final_count == 0  # Cache should be empty after cleanup

    def test_should_generate_consistent_cache_keys(self):
        """Test that cache key generation is consistent and deterministic."""
        # Arrange - Create cache manager without auto cleanup
        config = CacheConfig(auto_cleanup=False)
        cache_manager = CacheManager(config)

        # Act
        key1 = cache_manager._generate_key(["api", "stock", "AAPL", {"param": "value"}])
        key2 = cache_manager._generate_key(["api", "stock", "AAPL", {"param": "value"}])
        key3 = cache_manager._generate_key(["api", "stock", "GOOGL", {"param": "value"}])

        # Assert
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
        assert isinstance(key1, str)
        assert len(key1) > 0


class TestCacheIntegration:
    """Integration tests for cache system with API tools."""

    @pytest.mark.asyncio
    async def test_should_integrate_with_api_rate_limiting(self, mocker):
        """Test that caching works correctly with rate limiting."""
        # Arrange
        config = CacheConfig(auto_cleanup=False)
        cache_manager = CacheManager(config)
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        # Create a proper async mock function that tracks calls
        call_count = 0

        async def mock_api_function():
            nonlocal call_count
            call_count += 1
            return "api_result"

        # Act - Make multiple calls to the same cached function
        key = "integration_test_api_call"

        # Clear any existing cache for this key
        await cache_manager.delete(key)

        result1 = await cached(key, mock_api_function)
        result2 = await cached(key, mock_api_function)  # Should hit cache
        result3 = await cached(key, mock_api_function)  # Should hit cache

        # Assert
        assert result1 == result2 == result3 == "api_result"
        assert call_count == 1  # API called only once

    @pytest.mark.asyncio
    async def test_should_handle_cache_failures_gracefully(self, mocker):
        """Test that cache failures don't break the application."""
        # Arrange
        call_count = 0

        async def fallback_function():
            nonlocal call_count
            call_count += 1
            return "fallback_result"

        # Create a cache manager that will fail
        config = CacheConfig(auto_cleanup=False)
        cache_manager = CacheManager(config)

        # Mock cache.get to raise an exception
        mocker.patch.object(cache_manager, "get", side_effect=Exception("Cache error"))

        # Mock the global cache manager
        mocker.patch("finwiz.utils.cache_manager.get_cache_manager", return_value=cache_manager)

        # Act
        key = "error_test_function"
        result = await cached(key, fallback_function)

        # Assert
        assert result == "fallback_result"
        assert call_count == 1  # Function should still be called despite cache error

    def test_global_cache_manager_singleton(self):
        """Test that global cache manager is a singleton."""
        # Act
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        # Assert
        assert manager1 is manager2


@pytest.fixture
def performance_cache_config():
    """Cache configuration optimized for performance testing."""
    return CacheConfig(
        backend=CacheBackend.HYBRID,
        default_ttl=3600,  # 1 hour
        max_memory_items=1000,
        strategy=CacheStrategy.LRU,
        auto_cleanup=True,
        cleanup_interval=300,  # 5 minutes
    )


class TestCacheStrategies:
    """Test different cache strategies and their performance characteristics."""

    @pytest.mark.asyncio
    async def test_lru_strategy_evicts_least_recently_used(self):
        """Test that LRU strategy correctly evicts least recently used items."""
        # Arrange
        config = CacheConfig(backend=CacheBackend.MEMORY, max_memory_items=3, strategy=CacheStrategy.LRU, auto_cleanup=False)
        cache = CacheManager(config)

        # Act - Add items and access them in specific order
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add another item to trigger eviction
        await cache.set("key4", "value4")

        # Assert - key2 should be evicted (least recently used)
        assert await cache.get("key1") == "value1"  # Recently accessed
        assert await cache.get("key2") is None  # Should be evicted
        assert await cache.get("key3") == "value3"  # Still in cache
        assert await cache.get("key4") == "value4"  # Newly added

    @pytest.mark.asyncio
    async def test_ttl_strategy_respects_expiration_times(self):
        """Test that TTL strategy correctly handles different expiration times."""
        # Arrange
        config = CacheConfig(backend=CacheBackend.MEMORY, strategy=CacheStrategy.TTL, auto_cleanup=False)
        cache = CacheManager(config)

        # Act - Add items with different TTLs
        await cache.set("short_ttl", "value1", ttl=1)
        await cache.set("long_ttl", "value2", ttl=10)

        # Wait for short TTL to expire
        await asyncio.sleep(1.1)

        # Assert
        assert await cache.get("short_ttl") is None  # Should be expired
        assert await cache.get("long_ttl") == "value2"  # Should still be valid
