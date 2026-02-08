"""
Intelligent caching system for API responses and expensive computations.

This module provides a comprehensive caching layer with TTL support, cache warming,
invalidation strategies, and performance monitoring to reduce API costs and
improve system responsiveness.
"""

import asyncio
import builtins
import hashlib
import json
import pickle
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class CacheBackend(str, Enum):
    """Supported cache backend types."""

    MEMORY = "memory"
    FILE = "file"
    HYBRID = "hybrid"


class CacheStrategy(str, Enum):
    """Cache invalidation and refresh strategies."""

    TTL = "ttl"  # Time-to-live based
    LRU = "lru"  # Least recently used
    LFU = "lfu"  # Least frequently used
    ADAPTIVE = "adaptive"  # Adaptive based on access patterns


@dataclass
class CacheConfig:
    """Configuration for cache behavior."""

    backend: CacheBackend = CacheBackend.HYBRID
    default_ttl: int = 2700  # 45 minutes in seconds
    max_memory_items: int = 1000
    max_file_size_mb: int = 100
    cache_directory: str = "cache"
    strategy: CacheStrategy = CacheStrategy.TTL
    enable_compression: bool = True
    enable_encryption: bool = False
    auto_cleanup: bool = True
    cleanup_interval: int = 3600  # 1 hour
    hit_rate_threshold: float = 0.7  # Minimum hit rate for cache effectiveness


@dataclass
class CacheEntry:
    """Individual cache entry with metadata."""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: int = 2700
    size_bytes: int = 0
    tags: set[str] = field(default_factory=set)

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at

    def touch(self) -> None:
        """Update last accessed time and increment access count."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    hit_rate: float = 0.0
    average_age: float = 0.0
    memory_usage_mb: float = 0.0

    def update_hit_rate(self) -> None:
        """Update hit rate calculation."""
        total_requests = self.hits + self.misses
        self.hit_rate = self.hits / total_requests if total_requests > 0 else 0.0


class CacheManager:
    """
    Intelligent cache manager with multiple backends and strategies.

    Provides caching for API responses with TTL support, intelligent eviction,
    cache warming, and comprehensive performance monitoring.
    """

    def __init__(self, config: CacheConfig | None = None) -> None:
        """Initialize cache manager with configuration."""
        self.config = config or CacheConfig()
        self.memory_cache: dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.cache_dir = Path(self.config.cache_directory)
        self.cache_dir.mkdir(exist_ok=True)
        self._lock = asyncio.Lock()
        self._insertion_count: int = 0
        self._cleanup_every_n: int = 100  # Run incremental cleanup every 100 insertions
        self._cleanup_batch_size: int = 10  # Remove up to 10 expired entries per cleanup

    async def _incremental_cleanup(self, max_entries: int | None = None) -> int:
        """Remove a small batch of expired entries from memory cache.

        Called periodically during set() operations to prevent unbounded growth.
        This replaces the blocking asyncio.sleep(3600) cleanup loop.

        Args:
            max_entries: Maximum entries to remove (default: self._cleanup_batch_size)

        Returns:
            Number of entries removed
        """
        max_entries = max_entries or self._cleanup_batch_size
        expired_keys: list[str] = []

        for key, entry in self.memory_cache.items():
            if entry.is_expired:
                expired_keys.append(key)
                if len(expired_keys) >= max_entries:
                    break

        for key in expired_keys:
            await self._remove_entry(key)

        if expired_keys:
            logger.debug(f"Incremental cleanup: removed {len(expired_keys)} expired entries")

        return len(expired_keys)

    def _generate_key(self, key_parts: str | list[Any]) -> str:
        """Generate a consistent cache key from input parts."""
        if isinstance(key_parts, str):
            return key_parts

        # Create deterministic key from parts
        key_str = json.dumps(key_parts, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{key}.cache"

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        data = pickle.dumps(value)

        if self.config.enable_compression:
            import gzip

            data = gzip.compress(data)

        return data

    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self.config.enable_compression:
            import gzip

            data = gzip.decompress(data)

        return pickle.loads(data)  # nosec B301

    async def get(self, key: str | list[Any], default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key or key parts
            default: Default value if not found

        Returns:
            Cached value or default

        """
        cache_key = self._generate_key(key)

        async with self._lock:
            # Check memory cache first
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]

                if entry.is_expired:
                    await self._remove_entry(cache_key)
                    self.stats.misses += 1
                    return default

                entry.touch()
                self.stats.hits += 1
                return entry.value

            # Check file cache if using hybrid or file backend
            if self.config.backend in [CacheBackend.FILE, CacheBackend.HYBRID]:
                file_path = self._get_file_path(cache_key)

                if file_path.exists():
                    try:
                        data = file_path.read_bytes()
                        entry_data = self._deserialize_value(data)

                        # Reconstruct cache entry
                        entry = CacheEntry(**entry_data)

                        if entry.is_expired:
                            file_path.unlink(missing_ok=True)
                            self.stats.misses += 1
                            return default

                        entry.touch()

                        # Load into memory cache if using hybrid
                        if self.config.backend == CacheBackend.HYBRID:
                            await self._ensure_memory_capacity()
                            self.memory_cache[cache_key] = entry

                        self.stats.hits += 1
                        return entry.value

                    except Exception as e:
                        logger.warning(f"Error reading cache file {file_path}: {e}")
                        file_path.unlink(missing_ok=True)

            self.stats.misses += 1
            return default

    async def set(self, key: str | list[Any], value: Any, ttl: int | None = None, tags: set[str] | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key or key parts
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            tags: Optional tags for cache entry

        """
        cache_key = self._generate_key(key)
        ttl = ttl or self.config.default_ttl
        tags = tags or set()

        # Calculate size
        serialized = self._serialize_value(value)
        size_bytes = len(serialized)

        entry = CacheEntry(
            key=cache_key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time(),
            access_count=1,
            ttl=ttl,
            size_bytes=size_bytes,
            tags=tags,
        )

        async with self._lock:
            # Store in memory cache
            if self.config.backend in [CacheBackend.MEMORY, CacheBackend.HYBRID]:
                await self._ensure_memory_capacity()
                self.memory_cache[cache_key] = entry

            # Store in file cache
            if self.config.backend in [CacheBackend.FILE, CacheBackend.HYBRID]:
                try:
                    file_path = self._get_file_path(cache_key)

                    # Serialize entry metadata along with value
                    entry_data = {
                        "key": entry.key,
                        "value": entry.value,
                        "created_at": entry.created_at,
                        "last_accessed": entry.last_accessed,
                        "access_count": entry.access_count,
                        "ttl": entry.ttl,
                        "size_bytes": entry.size_bytes,
                        "tags": entry.tags,
                    }

                    serialized_entry = self._serialize_value(entry_data)
                    file_path.write_bytes(serialized_entry)

                except Exception as e:
                    logger.warning(f"Error writing cache file: {e}")

            self._update_stats()

            # Incremental cleanup: periodically remove expired entries
            if self.config.auto_cleanup:
                self._insertion_count += 1
                if self._insertion_count % self._cleanup_every_n == 0:
                    await self._incremental_cleanup()

    async def delete(self, key: str | list[Any]) -> bool:
        """
        Delete entry from cache.

        Args:
            key: Cache key or key parts

        Returns:
            True if entry was deleted, False if not found

        """
        cache_key = self._generate_key(key)

        async with self._lock:
            return await self._remove_entry(cache_key)

    async def _remove_entry(self, cache_key: str) -> bool:
        """Remove entry from all cache backends."""
        removed = False

        # Remove from memory
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            removed = True

        # Remove from file
        file_path = self._get_file_path(cache_key)
        if file_path.exists():
            file_path.unlink()
            removed = True

        if removed:
            self.stats.evictions += 1
            self._update_stats()

        return removed

    async def clear(self, tags: builtins.set[str] | None = None) -> int:
        """
        Clear cache entries, optionally filtered by tags.

        Args:
            tags: If provided, only clear entries with these tags

        Returns:
            Number of entries cleared

        """
        async with self._lock:
            cleared_count = 0

            if tags is None:
                # Clear all entries
                cleared_count = len(self.memory_cache)
                self.memory_cache.clear()

                # Clear file cache
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                    cleared_count += 1
            else:
                # Clear entries with matching tags
                keys_to_remove = []

                for key, entry in self.memory_cache.items():
                    if entry.tags.intersection(tags):
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    await self._remove_entry(key)
                    cleared_count += 1

            self._update_stats()
            return cleared_count

    async def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up

        """
        async with self._lock:
            expired_keys = []

            # Check memory cache
            for key, entry in self.memory_cache.items():
                if entry.is_expired:
                    expired_keys.append(key)

            # Check file cache
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    data = cache_file.read_bytes()
                    entry_data = self._deserialize_value(data)
                    entry = CacheEntry(**entry_data)

                    if entry.is_expired:
                        cache_file.unlink()
                        expired_keys.append(entry.key)

                except Exception as e:
                    logger.warning(f"Error checking cache file {cache_file}: {e}")
                    cache_file.unlink()

            # Remove expired entries
            for key in expired_keys:
                await self._remove_entry(key)

            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            return len(expired_keys)

    async def _ensure_memory_capacity(self) -> None:
        """Ensure memory cache doesn't exceed capacity limits."""
        while len(self.memory_cache) >= self.config.max_memory_items:
            # Evict based on strategy
            if self.config.strategy == CacheStrategy.LRU:
                # Remove least recently used
                oldest_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k].last_accessed)
            elif self.config.strategy == CacheStrategy.LFU:
                # Remove least frequently used
                oldest_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k].access_count)
            else:  # TTL or ADAPTIVE
                # Remove oldest entry
                oldest_key = min(self.memory_cache.keys(), key=lambda k: self.memory_cache[k].created_at)

            await self._remove_entry(oldest_key)

    def _update_stats(self) -> None:
        """Update cache statistics."""
        self.stats.entry_count = len(self.memory_cache)
        self.stats.total_size_bytes = sum(entry.size_bytes for entry in self.memory_cache.values())
        self.stats.memory_usage_mb = self.stats.total_size_bytes / (1024 * 1024)

        if self.memory_cache:
            self.stats.average_age = sum(entry.age_seconds for entry in self.memory_cache.values()) / len(self.memory_cache)

        self.stats.update_hit_rate()

    async def warm_cache(self, warm_functions: list[Callable]) -> None:
        """
        Warm cache by pre-loading frequently accessed data.

        Args:
            warm_functions: List of functions to call for cache warming

        """
        logger.info(f"Starting cache warming with {len(warm_functions)} functions")

        for func in warm_functions:
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except Exception as e:
                logger.warning(f"Error in cache warming function {func.__name__}: {e}")

        logger.info("Cache warming completed")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        self._update_stats()

        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "hit_rate": self.stats.hit_rate,
            "evictions": self.stats.evictions,
            "entry_count": self.stats.entry_count,
            "total_size_mb": self.stats.memory_usage_mb,
            "average_age_seconds": self.stats.average_age,
            "config": {
                "backend": self.config.backend.value,
                "default_ttl": self.config.default_ttl,
                "max_memory_items": self.config.max_memory_items,
                "strategy": self.config.strategy.value,
            },
        }

    async def close(self) -> None:
        """Clean up resources."""
        # Run a final cleanup of expired entries
        await self._incremental_cleanup(max_entries=self._cleanup_batch_size * 10)
        logger.info("Cache manager closed")


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def cached(key: str | list[Any], func: Callable, *args: Any, ttl: int | None = None, tags: set[str] | None = None, **kwargs: Any) -> Any:
    """
    Execute function with caching.

    Args:
        key: Cache key or key parts
        func: Function to execute if not cached
        *args: Positional arguments for the function
        ttl: Time-to-live for cache entry
        tags: Optional tags for cache entry
        **kwargs: Keyword arguments for the function

    Returns:
        Cached or computed result

    """
    cache = get_cache_manager()

    # Try to get from cache first
    try:
        result = await cache.get(key)
        if result is not None:
            return result
    except Exception as e:
        logger.warning(f"Cache get failed for key {key}: {e}")

    # Execute function and cache result
    if asyncio.iscoroutinefunction(func):
        result = await func(*args, **kwargs)
    else:
        result = func(*args, **kwargs)

    # Try to cache the result
    try:
        await cache.set(key, result, ttl=ttl, tags=tags)
    except Exception as e:
        logger.warning(f"Cache set failed for key {key}: {e}")

    return result


def cache_key(*parts: Any) -> str:
    """Generate a cache key from multiple parts."""
    return get_cache_manager()._generate_key(list(parts))
