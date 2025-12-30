"""Supabase client with connection pooling and circuit breaker protection."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

import asyncpg
from supabase import Client, create_client

from finwiz.supabase.circuit_breaker import CircuitBreaker
from finwiz.supabase.client_config import load_config
from finwiz.supabase.client_health import (
    build_health_status,
    log_configuration,
    log_connectivity_failure,
    log_connectivity_success,
    log_health_check_result,
)
from finwiz.supabase.client_metrics import ClientMetrics
from finwiz.supabase.client_operations import (
    execute_with_api,
    execute_with_pool,
)
from finwiz.supabase.client_pool import (
    acquire_connection,
    close_pool,
    create_connection_pool,
    get_pool_stats,
    release_connection,
)
from finwiz.supabase.models import SupabaseHealthStatus

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase client with connection pooling and circuit breaker."""

    _instance: SupabaseClient | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(
        cls,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> SupabaseClient:
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> None:
        """Initialize Supabase client (only runs once due to singleton)."""
        if hasattr(self, "_initialized"):
            return

        # Load configuration from environment
        config = load_config()
        self.url = config.url
        self.key = config.key
        self.db_url = config.db_url
        self.enabled = config.enabled
        self.pool_min_size = config.pool_min_size
        self.pool_max_size = config.pool_max_size
        self.pool_idle_timeout = config.pool_idle_timeout
        self.read_timeout = config.read_timeout
        self.write_timeout = config.write_timeout
        self.connectivity_test_timeout = config.connectivity_test_timeout
        self.max_retries = config.max_retries

        # API and pool clients (lazily initialized)
        self.api_client: Client | None = None
        self.db_pool: asyncpg.Pool | None = None

        # Circuit breaker and concurrency control
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self._semaphore = asyncio.Semaphore(config.max_concurrent_operations)

        # State and metrics
        self.is_available: bool = False
        self._metrics = ClientMetrics()
        self._initialized = True

    async def initialize_pool(self) -> None:
        """Initialize connection pool lazily on first use."""
        if self.db_pool is not None:
            return

        if not self.enabled or not self.db_url:
            logger.info("Database connection pool disabled (using API client only)")
            return

        async with self._lock:
            if self.db_pool is not None:
                return

            self.db_pool = await create_connection_pool(
                db_url=self.db_url,
                pool_min_size=self.pool_min_size,
                pool_max_size=self.pool_max_size,
                pool_idle_timeout=self.pool_idle_timeout,
                circuit_breaker=self.circuit_breaker,
            )

    def get_api_client(self) -> Client | None:
        """Get Supabase API client if available and circuit is closed."""
        if not self.enabled:
            logger.debug("Supabase integration is disabled")
            return None

        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is open, skipping database operation")
            return None

        if not self.url or not self.key:
            logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
            return None

        if not self.api_client:
            try:
                self.api_client = create_client(self.url, self.key)
                self.circuit_breaker.record_success()
                logger.info("✅ Supabase API client initialized successfully")
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"❌ Failed to connect to Supabase API: {e}")
                return None

        return self.api_client

    async def get_connection(self) -> asyncpg.Connection | None:
        """Get database connection from pool."""
        if not self.enabled or self.circuit_breaker.is_open():
            return None
        await self.initialize_pool()
        if not self.db_pool:
            return None
        return await acquire_connection(
            pool=self.db_pool,
            timeout=5.0,
            circuit_breaker=self.circuit_breaker,
        )

    async def release_connection(self, conn: asyncpg.Connection) -> None:
        """Release connection back to pool."""
        await release_connection(self.db_pool, conn)

    async def close(self) -> None:
        """Close connection pool gracefully."""
        await close_pool(self.db_pool)

    async def get_pool_stats(self) -> dict[str, Any]:
        """Get connection pool statistics for monitoring."""
        return get_pool_stats(
            pool=self.db_pool,
            pool_min_size=self.pool_min_size,
            pool_max_size=self.pool_max_size,
            pool_idle_timeout=self.pool_idle_timeout,
        )

    async def execute_with_timeout(
        self,
        operation: Callable,
        timeout: float | None = None,
        use_pool: bool = False,
    ) -> Any | None:
        """Execute operation with timeout and circuit breaker protection."""
        if timeout is None:
            timeout = self.read_timeout

        start_time = time.time()
        self._metrics.total_operations += 1

        async with self._semaphore:
            if use_pool:
                conn = await self.get_connection()
                if not conn:
                    self._metrics.record_failure()
                    return None
                return await execute_with_pool(
                    operation=operation,
                    timeout=timeout,
                    start_time=start_time,
                    conn=conn,
                    release_func=self.release_connection,
                    metrics=self._metrics,
                    circuit_breaker=self.circuit_breaker,
                    is_available=self.is_available,
                )
            else:
                client = self.get_api_client()
                if not client:
                    self._metrics.record_failure()
                    return None
                return await execute_with_api(
                    operation=operation,
                    timeout=timeout,
                    start_time=start_time,
                    client=client,
                    metrics=self._metrics,
                    circuit_breaker=self.circuit_breaker,
                    is_available=self.is_available,
                )

    async def test_connectivity(self) -> bool:
        """Test Supabase connectivity with simple query."""
        log_configuration(
            url=self.url,
            enabled=self.enabled,
            db_url=self.db_url,
            pool_min_size=self.pool_min_size,
            pool_max_size=self.pool_max_size,
            pool_idle_timeout=self.pool_idle_timeout,
            read_timeout=self.read_timeout,
            write_timeout=self.write_timeout,
            connectivity_test_timeout=self.connectivity_test_timeout,
            max_retries=self.max_retries,
            circuit_breaker=self.circuit_breaker,
        )

        if not self.enabled:
            logger.info("ℹ️ Supabase integration is disabled")
            self.is_available = False
            return False

        if not self.url or not self.key:
            logger.warning("⚠️ Missing SUPABASE_URL or SUPABASE_KEY - caching disabled")
            self.is_available = False
            return False

        try:
            client = self.get_api_client()
            if not client:
                self.is_available = False
                log_connectivity_failure("Could not create API client")
                raise ConnectionError("Could not create API client")

            self.is_available = True
            health = self.get_health_status()
            log_connectivity_success(self.connectivity_test_timeout, health)
            return True

        except ConnectionError:
            raise
        except Exception as e:
            self.is_available = False
            log_connectivity_failure(str(e))
            raise ConnectionError(str(e)) from e

    def get_health_status(self) -> SupabaseHealthStatus:
        """Get current health status with metrics."""
        return build_health_status(
            is_available=self.is_available,
            success_rate=self._metrics.get_success_rate(),
            avg_response_time=self._metrics.get_avg_response_time(),
            circuit_breaker=self.circuit_breaker,
            timeout_count=self._metrics.timeout_count,
            total_operations=self._metrics.total_operations,
            successful_operations=self._metrics.successful_operations,
            failed_operations=self._metrics.failed_operations,
            url=self.url,
            read_timeout=self.read_timeout,
            write_timeout=self.write_timeout,
            connectivity_test_timeout=self.connectivity_test_timeout,
            max_retries=self.max_retries,
        )

    def reset_metrics(self) -> None:
        """Reset operation metrics."""
        self._metrics.reset()

    def log_metrics(self) -> None:
        """Log current metrics at INFO level."""
        self._metrics.log(self.is_available, self.circuit_breaker.is_open())

    async def periodic_health_check(self) -> None:
        """Perform periodic health check on connection pool."""
        if not self.db_pool:
            logger.debug("Connection pool not initialized, skipping health check")
            return

        stats = await self.get_pool_stats()
        log_health_check_result(stats)

    @property
    def metrics(self) -> ClientMetrics:
        """Get metrics instance for direct access."""
        return self._metrics
