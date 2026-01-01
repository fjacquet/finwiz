"""
Operation execution for Supabase client.

Handles operation execution with timeout, circuit breaker protection,
and metrics recording for both pool and API-based operations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncpg
    from supabase import Client

    from finwiz.supabase.circuit_breaker import CircuitBreaker
    from finwiz.supabase.client_metrics import ClientMetrics

logger = logging.getLogger(__name__)


def record_success(
    start_time: float,
    metrics: ClientMetrics,
    circuit_breaker: CircuitBreaker,
    is_available: bool,
) -> None:
    """
    Record successful operation metrics.

    Args:
        start_time: Operation start timestamp
        metrics: ClientMetrics instance for recording
        circuit_breaker: CircuitBreaker for success tracking
        is_available: Current availability status

    """
    response_time = (time.time() - start_time) * 1000
    metrics.record_response_time(response_time)
    metrics.record_success()
    circuit_breaker.record_success()

    if metrics.should_log():
        metrics.log(is_available, circuit_breaker.is_open())


def record_timeout(
    timeout: float,
    metrics: ClientMetrics,
    circuit_breaker: CircuitBreaker,
) -> None:
    """
    Record timeout metrics.

    Args:
        timeout: Timeout value that was exceeded
        metrics: ClientMetrics instance for recording
        circuit_breaker: CircuitBreaker for failure tracking

    """
    logger.warning(f"⚠️ Database operation timed out after {timeout}s [Total timeouts: {metrics.timeout_count + 1}, Success rate: {metrics.get_success_rate():.1%}]")
    metrics.record_timeout()
    circuit_breaker.record_failure()


def record_error(
    error: Exception,
    metrics: ClientMetrics,
    circuit_breaker: CircuitBreaker,
) -> None:
    """
    Record error metrics.

    Args:
        error: Exception that occurred
        metrics: ClientMetrics instance for recording
        circuit_breaker: CircuitBreaker for failure tracking

    """
    logger.error(f"❌ Database operation failed: {error} [Total failures: {metrics.failed_operations + 1}, Success rate: {metrics.get_success_rate():.1%}]")
    metrics.record_failure()
    circuit_breaker.record_failure()


async def execute_with_pool(
    operation: Callable,
    timeout: float,
    start_time: float,
    conn: asyncpg.Connection,
    release_func: Callable,
    metrics: ClientMetrics,
    circuit_breaker: CircuitBreaker,
    is_available: bool,
) -> Any | None:
    """
    Execute operation using connection pool.

    Args:
        operation: Async callable that takes connection as argument
        timeout: Timeout in seconds
        start_time: Operation start timestamp
        conn: Database connection
        release_func: Function to release connection
        metrics: ClientMetrics instance
        circuit_breaker: CircuitBreaker instance
        is_available: Current availability status

    Returns:
        Operation result or None on failure

    """
    try:
        result = await asyncio.wait_for(operation(conn), timeout=timeout)
        record_success(start_time, metrics, circuit_breaker, is_available)
        return result

    except TimeoutError:
        record_timeout(timeout, metrics, circuit_breaker)
        return None

    except Exception as e:
        record_error(e, metrics, circuit_breaker)
        return None

    finally:
        await release_func(conn)


async def execute_with_api(
    operation: Callable,
    timeout: float,
    start_time: float,
    client: Client,
    metrics: ClientMetrics,
    circuit_breaker: CircuitBreaker,
    is_available: bool,
) -> Any | None:
    """
    Execute operation using API client.

    Args:
        operation: Callable that takes client as argument
        timeout: Timeout in seconds
        start_time: Operation start timestamp
        client: Supabase API client
        metrics: ClientMetrics instance
        circuit_breaker: CircuitBreaker instance
        is_available: Current availability status

    Returns:
        Operation result or None on failure

    """
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(operation, client),
            timeout=timeout,
        )
        record_success(start_time, metrics, circuit_breaker, is_available)
        return result

    except TimeoutError:
        record_timeout(timeout, metrics, circuit_breaker)
        return None

    except Exception as e:
        record_error(e, metrics, circuit_breaker)
        return None
