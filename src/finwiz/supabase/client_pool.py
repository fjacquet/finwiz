"""
Connection pool management for Supabase client.

Handles asyncpg connection pool initialization, connection acquisition,
and pool lifecycle management.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import asyncpg

if TYPE_CHECKING:
    from finwiz.supabase.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


async def create_connection_pool(
    db_url: str,
    pool_min_size: int,
    pool_max_size: int,
    pool_idle_timeout: int,
    circuit_breaker: CircuitBreaker,
) -> asyncpg.Pool | None:
    """
    Create asyncpg connection pool with configuration.

    Args:
        db_url: Database connection string (Supavisor Session Mode)
        pool_min_size: Minimum connections in pool
        pool_max_size: Maximum connections in pool
        pool_idle_timeout: Idle connection timeout in seconds
        circuit_breaker: Circuit breaker for failure tracking

    Returns:
        Initialized asyncpg pool or None if creation failed

    """
    try:
        pool = await asyncpg.create_pool(
            dsn=db_url,
            min_size=pool_min_size,
            max_size=pool_max_size,
            max_inactive_connection_lifetime=pool_idle_timeout,
            command_timeout=5.0,
            ssl="require",
        )
        logger.info(f"✅ Connection pool initialized: min={pool_min_size}, max={pool_max_size}, idle_timeout={pool_idle_timeout}s")
        circuit_breaker.record_success()
        return pool
    except Exception as e:
        circuit_breaker.record_failure()
        logger.error(f"❌ Failed to initialize connection pool: {e}")
        return None


async def acquire_connection(
    pool: asyncpg.Pool,
    timeout: float,
    circuit_breaker: CircuitBreaker,
) -> asyncpg.Connection | None:
    """
    Acquire connection from pool with timeout.

    Args:
        pool: asyncpg connection pool
        timeout: Timeout in seconds for acquiring connection
        circuit_breaker: Circuit breaker for failure tracking

    Returns:
        Database connection or None if acquisition failed

    """
    try:
        conn = await asyncio.wait_for(
            pool.acquire(),
            timeout=timeout,
        )
        return conn
    except TimeoutError:
        logger.warning("⚠️ Connection pool exhausted, timeout waiting for connection")
        circuit_breaker.record_failure()
        return None
    except Exception as e:
        logger.error(f"❌ Failed to acquire connection: {e}")
        circuit_breaker.record_failure()
        return None


async def release_connection(
    pool: asyncpg.Pool | None,
    conn: asyncpg.Connection | None,
) -> None:
    """
    Release connection back to pool.

    Args:
        pool: asyncpg connection pool
        conn: Database connection to release

    """
    if pool and conn:
        await pool.release(conn)


async def close_pool(pool: asyncpg.Pool | None) -> None:
    """
    Close connection pool gracefully.

    Args:
        pool: asyncpg connection pool to close

    """
    if pool:
        await pool.close()
        logger.info("✅ Connection pool closed")


def get_pool_stats(
    pool: asyncpg.Pool | None,
    pool_min_size: int,
    pool_max_size: int,
    pool_idle_timeout: int,
) -> dict[str, Any]:
    """
    Get connection pool statistics for monitoring.

    Args:
        pool: asyncpg connection pool
        pool_min_size: Configured minimum pool size
        pool_max_size: Configured maximum pool size
        pool_idle_timeout: Configured idle timeout

    Returns:
        Dictionary with pool statistics

    """
    if not pool:
        return {"status": "disabled"}

    return {
        "status": "active",
        "size": pool.get_size(),
        "free_size": pool.get_idle_size(),
        "min_size": pool_min_size,
        "max_size": pool_max_size,
        "idle_timeout": pool_idle_timeout,
    }


def calculate_pool_utilization(stats: dict[str, Any]) -> float:
    """
    Calculate pool utilization from stats.

    Args:
        stats: Pool statistics from get_pool_stats()

    Returns:
        Utilization as float between 0.0 and 1.0

    """
    if stats["status"] == "disabled":
        return 0.0

    size = stats["size"]
    free_size = stats["free_size"]
    max_size = stats["max_size"]

    return (size - free_size) / max_size if max_size > 0 else 0.0
