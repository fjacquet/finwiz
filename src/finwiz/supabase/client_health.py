"""
Health checking and configuration logging for Supabase client.

Provides connectivity testing, health status building,
and configuration logging functionality.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.supabase.circuit_breaker import CircuitBreaker
    from finwiz.supabase.models import SupabaseHealthStatus

logger = logging.getLogger(__name__)


def build_health_status(
    is_available: bool,
    success_rate: float,
    avg_response_time: float,
    circuit_breaker: CircuitBreaker,
    timeout_count: int,
    total_operations: int,
    successful_operations: int,
    failed_operations: int,
    url: str,
    read_timeout: float,
    write_timeout: float,
    connectivity_test_timeout: float,
    max_retries: int,
) -> SupabaseHealthStatus:
    """
    Build health status object with current metrics.

    Args:
        is_available: Whether Supabase is currently available
        success_rate: Operation success rate (0.0 to 1.0)
        avg_response_time: Average response time in milliseconds
        circuit_breaker: Circuit breaker instance for state
        timeout_count: Number of timed out operations
        total_operations: Total operations count
        successful_operations: Successful operations count
        failed_operations: Failed operations count
        url: Supabase URL (will be masked)
        read_timeout: Read timeout setting
        write_timeout: Write timeout setting
        connectivity_test_timeout: Connectivity test timeout
        max_retries: Maximum retry attempts

    Returns:
        SupabaseHealthStatus with current metrics and configuration

    """
    # Import here to avoid circular dependency
    from finwiz.supabase.models import SupabaseHealthStatus

    masked_url = url[:20] + "..." if len(url) > 20 else url

    return SupabaseHealthStatus(
        is_available=is_available,
        success_rate=success_rate,
        avg_response_time=avg_response_time,
        circuit_breaker_open=circuit_breaker.is_open(),
        timeout_count=timeout_count,
        total_operations=total_operations,
        successful_operations=successful_operations,
        failed_operations=failed_operations,
        last_check_timestamp=datetime.now(),
        configuration={
            "url": masked_url,
            "read_timeout": read_timeout,
            "write_timeout": write_timeout,
            "connectivity_test_timeout": connectivity_test_timeout,
            "max_retries": max_retries,
            "circuit_breaker_threshold": circuit_breaker.failure_threshold,
            "circuit_breaker_timeout": circuit_breaker.recovery_timeout,
        },
    )


def log_configuration(
    url: str,
    enabled: bool,
    db_url: str | None,
    pool_min_size: int,
    pool_max_size: int,
    pool_idle_timeout: int,
    read_timeout: float,
    write_timeout: float,
    connectivity_test_timeout: float,
    max_retries: int,
    circuit_breaker: CircuitBreaker,
) -> None:
    """
    Log current configuration at startup.

    Args:
        url: Supabase URL
        enabled: Whether Supabase is enabled
        db_url: Database connection URL
        pool_min_size: Minimum pool connections
        pool_max_size: Maximum pool connections
        pool_idle_timeout: Idle connection timeout
        read_timeout: Read operation timeout
        write_timeout: Write operation timeout
        connectivity_test_timeout: Connectivity test timeout
        max_retries: Maximum retry attempts
        circuit_breaker: Circuit breaker instance

    """
    masked_url = url[:20] + "..." if len(url) > 20 else url
    has_db_url = "Yes" if db_url else "No"

    logger.info(
        f"📋 Supabase Configuration: "
        f"URL={masked_url}, "
        f"Enabled={enabled}, "
        f"DB URL Configured={has_db_url}, "
        f"Pool Min/Max={pool_min_size}/{pool_max_size}, "
        f"Pool Idle Timeout={pool_idle_timeout}s, "
        f"Read Timeout={read_timeout}s, "
        f"Write Timeout={write_timeout}s, "
        f"Connectivity Test Timeout={connectivity_test_timeout}s, "
        f"Max Retries={max_retries}, "
        f"Circuit Breaker Threshold={circuit_breaker.failure_threshold}, "
        f"Circuit Breaker Timeout={circuit_breaker.recovery_timeout}s"
    )


def log_health_check_result(
    stats: dict[str, Any],
) -> None:
    """
    Log periodic health check result.

    Args:
        stats: Pool statistics from get_pool_stats()

    """
    if stats["status"] == "disabled":
        return

    size = stats["size"]
    free_size = stats["free_size"]
    max_size = stats["max_size"]
    utilization = (size - free_size) / max_size if max_size > 0 else 0.0

    logger.info(f"🏥 Pool Health Check: size={size}/{max_size}, free={free_size}, utilization={utilization:.1%}")

    if utilization >= 0.95:
        logger.error(f"🚨 CRITICAL: Pool utilization very high: {utilization:.1%}")
    elif utilization >= 0.80:
        logger.warning(f"⚠️ WARNING: Pool utilization high: {utilization:.1%}")


def log_connectivity_success(
    connectivity_test_timeout: float,
    health_status: SupabaseHealthStatus,
) -> None:
    """
    Log successful connectivity test result.

    Args:
        connectivity_test_timeout: Timeout setting used
        health_status: Current health status

    """
    logger.info(f"✅ Supabase connectivity test passed (timeout: {connectivity_test_timeout}s)")
    logger.info(f"📊 Supabase Health Status: Available={health_status.is_available}, Circuit Breaker={'OPEN' if health_status.circuit_breaker_open else 'CLOSED'}")


def log_connectivity_failure(
    error: str,
    connectivity_test_timeout: float | None = None,
) -> None:
    """
    Log connectivity test failure.

    Args:
        error: Error description
        connectivity_test_timeout: Timeout if applicable

    """
    if connectivity_test_timeout:
        error_msg = (
            f"❌ Supabase connectivity test failed: {error} "
            f"after {connectivity_test_timeout}s\n"
            f"   Check your SUPABASE_DB_URL configuration in .env\n"
            f"   Set SUPABASE_ENABLED=false to disable Supabase integration"
        )
    else:
        error_msg = (
            f"❌ Supabase connectivity test failed: {error}\n"
            f"   Check your SUPABASE_URL and SUPABASE_DB_URL configuration in .env\n"
            f"   Set SUPABASE_ENABLED=false to disable Supabase integration"
        )
    logger.error(error_msg)
