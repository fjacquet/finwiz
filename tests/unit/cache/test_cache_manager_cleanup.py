"""Unit tests for CacheManager incremental cleanup behavior.

Validates that CacheManager uses event-driven eviction (lazy on get, incremental on set)
instead of a blocking asyncio.sleep(3600) background cleanup loop.
"""

import time

import pytest

from finwiz.infrastructure.caching.manager import CacheConfig, CacheEntry, CacheManager


@pytest.mark.asyncio
async def test_no_background_cleanup_task():
    """CacheManager should not create a background cleanup task."""
    cm = CacheManager(config=CacheConfig(auto_cleanup=True))
    # No _cleanup_task attribute or it's None
    assert not hasattr(cm, "_cleanup_task") or cm._cleanup_task is None
    await cm.close()


@pytest.mark.asyncio
async def test_incremental_cleanup_on_set(mocker):
    """Incremental cleanup triggers on set() every _cleanup_every_n insertions."""
    cm = CacheManager(config=CacheConfig(auto_cleanup=True, backend="memory"))
    cm._cleanup_every_n = 3  # Override for fast testing

    # Insert 2 entries with TTL=0 so they expire immediately
    now = time.time()
    cm.memory_cache["expired_1"] = CacheEntry(
        key="expired_1",
        value="old1",
        created_at=now - 100,
        last_accessed=now - 100,
        ttl=1,
    )
    cm.memory_cache["expired_2"] = CacheEntry(
        key="expired_2",
        value="old2",
        created_at=now - 100,
        last_accessed=now - 100,
        ttl=1,
    )

    # Set entries to get insertion_count to 3 (triggers cleanup)
    await cm.set("key1", "val1", ttl=3600)
    await cm.set("key2", "val2", ttl=3600)
    # At this point _insertion_count == 2, no cleanup yet
    assert "expired_1" in cm.memory_cache or "expired_2" in cm.memory_cache

    await cm.set("key3", "val3", ttl=3600)
    # Now _insertion_count == 3, cleanup should have run

    assert "expired_1" not in cm.memory_cache
    assert "expired_2" not in cm.memory_cache
    # Fresh entries should still be present
    assert "key1" in cm.memory_cache
    assert "key2" in cm.memory_cache
    assert "key3" in cm.memory_cache

    await cm.close()


@pytest.mark.asyncio
async def test_lazy_eviction_on_get():
    """Expired entries are lazily evicted on get() when accessed."""
    cm = CacheManager(config=CacheConfig(backend="memory"))

    # Insert an entry with very short TTL
    now = time.time()
    cm.memory_cache["lazy_key"] = CacheEntry(
        key="lazy_key",
        value="some_value",
        created_at=now - 100,
        last_accessed=now - 100,
        ttl=1,
    )

    # get() should return default (None) and evict the expired entry
    result = await cm.get("lazy_key")
    assert result is None
    assert "lazy_key" not in cm.memory_cache

    await cm.close()


@pytest.mark.asyncio
async def test_incremental_cleanup_respects_batch_size():
    """_incremental_cleanup removes at most _cleanup_batch_size entries per call."""
    cm = CacheManager(config=CacheConfig(backend="memory"))
    cm._cleanup_batch_size = 5

    # Create 20 expired entries
    now = time.time()
    for i in range(20):
        key = f"expired_{i}"
        cm.memory_cache[key] = CacheEntry(
            key=key,
            value=f"val_{i}",
            created_at=now - 200,
            last_accessed=now - 200,
            ttl=1,
        )

    # Run incremental cleanup once
    removed = await cm._incremental_cleanup()

    assert removed == 5
    # 15 expired entries should remain
    remaining = sum(1 for e in cm.memory_cache.values() if e.is_expired)
    assert remaining == 15

    await cm.close()


@pytest.mark.asyncio
async def test_close_runs_final_cleanup():
    """close() runs a final batch cleanup of expired entries."""
    cm = CacheManager(config=CacheConfig(backend="memory"))
    cm._cleanup_batch_size = 5  # Final cleanup does batch_size * 10 = 50

    # Create 8 expired entries
    now = time.time()
    for i in range(8):
        key = f"expired_{i}"
        cm.memory_cache[key] = CacheEntry(
            key=key,
            value=f"val_{i}",
            created_at=now - 200,
            last_accessed=now - 200,
            ttl=1,
        )

    # Also add 2 fresh entries
    for i in range(2):
        key = f"fresh_{i}"
        cm.memory_cache[key] = CacheEntry(
            key=key,
            value=f"fresh_val_{i}",
            created_at=now,
            last_accessed=now,
            ttl=3600,
        )

    await cm.close()

    # All expired entries should be cleaned up
    for i in range(8):
        assert f"expired_{i}" not in cm.memory_cache

    # Fresh entries should still be there
    for i in range(2):
        assert f"fresh_{i}" in cm.memory_cache


@pytest.mark.asyncio
async def test_auto_cleanup_disabled_skips_incremental():
    """With auto_cleanup=False, set() does not run incremental cleanup."""
    cm = CacheManager(config=CacheConfig(auto_cleanup=False, backend="memory"))
    cm._cleanup_every_n = 1  # Would trigger on every set if auto_cleanup were True

    # Insert an expired entry
    now = time.time()
    cm.memory_cache["expired_key"] = CacheEntry(
        key="expired_key",
        value="old",
        created_at=now - 100,
        last_accessed=now - 100,
        ttl=1,
    )

    # Insert several entries -- none should trigger cleanup
    await cm.set("a", "1", ttl=3600)
    await cm.set("b", "2", ttl=3600)
    await cm.set("c", "3", ttl=3600)

    # Insertion count should remain 0 since auto_cleanup is off
    assert cm._insertion_count == 0

    # Expired entry should still be present (no cleanup ran)
    assert "expired_key" in cm.memory_cache

    await cm.close()
