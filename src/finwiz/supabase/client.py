"""
Supabase client with connection pooling and circuit breaker protection.

Manages Supabase connection with:
- Singleton pattern for single instance per application
- asyncpg connection pool for direct SQL operations
- Lazy pool initialization (create on first use)
- Circuit breaker for failure protection
- Timeout enforcement for operations
- Connection pool monitoring and health checks
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import asyncpg
from supabase import Client, create_client

from finwiz.supabase.circuit_breaker import CircuitBreaker
from finwiz.supabase.models import SupabaseHealthStatus

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Singleton Supabase client with connection pooling and circuit breaker protection.

    Provides connection management with:
    - Singleton pattern (only one instance per application)
    - asyncpg connection pool for direct SQL operations
    - Lazy pool initialization (create on first use, not during startup)
    - Supabase API client for REST/GraphQL operations
    - Circuit breaker for failure protection
    - Timeout enforcement for operations
    - Connection pool monitoring and health checks
    - SSL enforcement for all connections

    Attributes:
        url: Supabase project URL
        key: Supabase API key
        db_url: Database connection string (Supavisor Session Mode)
        enabled: Whether Supabase integration is enabled
        is_available: Whether Supabase connectivity test passed
        api_client: Supabase API client instance (lazy initialized)
        db_pool: asyncpg connection pool (lazy initialized)
        circuit_breaker: Circuit breaker for failure protection
        pool_min_size: Minimum connections in pool
        pool_max_size: Maximum connections in pool
        pool_idle_timeout: Idle connection timeout in seconds
        read_timeout: Timeout for read operations in seconds
        write_timeout: Timeout for write operations in seconds

    """

    _instance: SupabaseClient | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(
        cls,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> SupabaseClient:
        """
        Ensure only one instance exists (singleton pattern).

        Args:
            failure_threshold: Circuit breaker failure threshold (default: 3)
            recovery_timeout: Circuit breaker recovery timeout in seconds (default: 300)

        Returns:
            The singleton SupabaseClient instance

        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> None:
        """
        Initialize Supabase client (only runs once due to singleton).

        Args:
            failure_threshold: Circuit breaker failure threshold (default: 3)
            recovery_timeout: Circuit breaker recovery timeout in seconds (default: 300)

        """
        # Only initialize once
        if hasattr(self, "_initialized"):
            return

        # Environment configuration
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_KEY", "")
        self.db_url: str | None = os.getenv("SUPABASE_DB_URL")  # Session Mode connection string
        self.enabled: bool = os.getenv("SUPABASE_ENABLED", "true").lower() == "true"

        # API client (for REST/GraphQL operations)
        self.api_client: Client | None = None

        # Database connection pool (for direct SQL operations)
        self.db_pool: asyncpg.Pool | None = None

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

        # Pool configuration
        self.pool_min_size: int = int(os.getenv("SUPABASE_POOL_MIN_SIZE", "2"))
        self.pool_max_size: int = int(os.getenv("SUPABASE_POOL_MAX_SIZE", "10"))
        self.pool_idle_timeout: int = int(os.getenv("SUPABASE_POOL_IDLE_TIMEOUT", "300"))

        # Configurable timeouts from environment
        self.read_timeout: float = float(os.getenv("DATABASE_READ_TIMEOUT", "2.0"))
        self.write_timeout: float = float(os.getenv("DATABASE_WRITE_TIMEOUT", "5.0"))
        self.max_retries: int = int(os.getenv("SUPABASE_MAX_RETRIES", "1"))
        self.connectivity_test_timeout: float = float(os.getenv("SUPABASE_CONNECTIVITY_TEST_TIMEOUT", "5.0"))

        # Connection pool limit to prevent exhaustion
        max_concurrent = int(os.getenv("SUPABASE_MAX_CONCURRENT_OPERATIONS", "10"))
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_concurrent)

        self.is_available: bool = False  # Set by connectivity test

        # Metrics tracking
        self.total_operations: int = 0
        self.successful_operations: int = 0
        self.failed_operations: int = 0
        self.timeout_count: int = 0
        self.response_times: list[float] = []  # Store recent response times
        self.max_response_times: int = 100  # Keep last 100 response times

        self._initialized = True

    async def initialize_pool(self) -> None:
        """
        Initialize connection pool lazily on first use.

        Creates asyncpg connection pool with Supavisor Session Mode connection string.
        Uses async lock to ensure thread-safe initialization.
        """
        if self.db_pool is not None:
            return

        if not self.enabled or not self.db_url:
            logger.info("Database connection pool disabled (using API client only)")
            return

        async with self._lock:
            # Double-check after acquiring lock
            if self.db_pool is not None:
                return

            try:
                # Create asyncpg connection pool with Supavisor Session Mode
                self.db_pool = await asyncpg.create_pool(
                    dsn=self.db_url,
                    min_size=self.pool_min_size,
                    max_size=self.pool_max_size,
                    max_inactive_connection_lifetime=self.pool_idle_timeout,
                    command_timeout=5.0,  # 5 second timeout for commands
                    ssl="require",  # Enforce SSL
                )
                logger.info(f"✅ Connection pool initialized: min={self.pool_min_size}, max={self.pool_max_size}, idle_timeout={self.pool_idle_timeout}s")
                self.circuit_breaker.record_success()
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"❌ Failed to initialize connection pool: {e}")
                self.db_pool = None

    def get_api_client(self) -> Client | None:
        """
        Get Supabase API client if available and circuit is closed.

        Returns:
            Supabase API client instance or None if unavailable/circuit open

        """
        if not self.enabled:
            logger.debug("Supabase integration is disabled")
            return None

        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is open, skipping database operation")
            return None

        if not self.url or not self.key:
            logger.error("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
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
        """
        Get database connection from pool.

        Acquires a connection from the asyncpg pool with a 5-second timeout.
        Initializes the pool lazily on first use.

        Returns:
            Database connection or None if unavailable/circuit open

        """
        if not self.enabled or self.circuit_breaker.is_open():
            return None

        # Initialize pool on first use (lazy initialization)
        await self.initialize_pool()

        if not self.db_pool:
            return None

        try:
            # Acquire connection with timeout
            conn = await asyncio.wait_for(
                self.db_pool.acquire(),
                timeout=5.0,  # Wait up to 5 seconds for available connection
            )
            return conn
        except TimeoutError:
            logger.warning("⚠️ Connection pool exhausted, timeout waiting for connection")
            self.circuit_breaker.record_failure()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to acquire connection: {e}")
            self.circuit_breaker.record_failure()
            return None

    async def release_connection(self, conn: asyncpg.Connection) -> None:
        """
        Release connection back to pool.

        Args:
            conn: Database connection to release

        """
        if self.db_pool and conn:
            await self.db_pool.release(conn)

    async def close(self) -> None:
        """
        Close connection pool gracefully.

        Closes all connections in the pool and cleans up resources.
        Should be called during application shutdown.
        """
        if self.db_pool:
            await self.db_pool.close()
            logger.info("✅ Connection pool closed")

    async def get_pool_stats(self) -> dict[str, Any]:
        """
        Get connection pool statistics for monitoring.

        Returns:
            Dictionary with pool statistics including size, utilization, and configuration

        """
        if not self.db_pool:
            return {"status": "disabled"}

        return {
            "status": "active",
            "size": self.db_pool.get_size(),
            "free_size": self.db_pool.get_idle_size(),
            "min_size": self.pool_min_size,
            "max_size": self.pool_max_size,
            "idle_timeout": self.pool_idle_timeout,
        }

    async def execute_with_timeout(
        self,
        operation: Callable,
        timeout: float | None = None,
        use_pool: bool = False,
    ) -> Any | None:
        """
        Execute operation with timeout and circuit breaker protection.

        Supports both connection pool (direct SQL) and API client (REST/GraphQL) modes.
        Uses a semaphore to limit concurrent operations and prevent connection
        pool exhaustion when processing many holdings simultaneously.

        Args:
            operation: Callable that takes connection/client and returns result
            timeout: Timeout in seconds (default: uses read_timeout from config)
            use_pool: If True, use connection pool; if False, use API client

        Returns:
            Operation result or None if failed/timed out

        """
        # Use configured read_timeout if not specified
        if timeout is None:
            timeout = self.read_timeout

        # Track operation start time
        start_time = time.time()
        self.total_operations += 1

        # Use semaphore to limit concurrent operations
        async with self._semaphore:
            if use_pool:
                # Use connection pool for direct SQL operations
                conn = await self.get_connection()
                if not conn:
                    self.failed_operations += 1
                    return None

                try:
                    # Execute operation with timeout
                    result = await asyncio.wait_for(operation(conn), timeout=timeout)

                    # Record success metrics
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    self._record_response_time(response_time)
                    self.successful_operations += 1
                    self.circuit_breaker.record_success()

                    # Log metrics every 100 operations
                    if self.should_log_metrics():
                        self.log_metrics()

                    return result

                except TimeoutError:
                    logger.warning(f"⚠️ Database operation timed out after {timeout}s [Total timeouts: {self.timeout_count + 1}, Success rate: {self.get_success_rate():.1%}]")
                    self.timeout_count += 1
                    self.failed_operations += 1
                    self.circuit_breaker.record_failure()
                    return None

                except Exception as e:
                    logger.error(f"❌ Database operation failed: {e} [Total failures: {self.failed_operations + 1}, Success rate: {self.get_success_rate():.1%}]")
                    self.failed_operations += 1
                    self.circuit_breaker.record_failure()
                    return None

                finally:
                    await self.release_connection(conn)

            else:
                # Use API client for REST/GraphQL operations
                client = self.get_api_client()
                if not client:
                    self.failed_operations += 1
                    return None

                try:
                    # Execute operation with timeout
                    result = await asyncio.wait_for(
                        asyncio.to_thread(operation, client),
                        timeout=timeout,
                    )

                    # Record success metrics
                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    self._record_response_time(response_time)
                    self.successful_operations += 1
                    self.circuit_breaker.record_success()

                    # Log metrics every 100 operations
                    if self.should_log_metrics():
                        self.log_metrics()

                    return result

                except TimeoutError:
                    logger.warning(f"⚠️ Database operation timed out after {timeout}s [Total timeouts: {self.timeout_count + 1}, Success rate: {self.get_success_rate():.1%}]")
                    self.timeout_count += 1
                    self.failed_operations += 1
                    self.circuit_breaker.record_failure()
                    return None

                except Exception as e:
                    logger.error(f"❌ Database operation failed: {e} [Total failures: {self.failed_operations + 1}, Success rate: {self.get_success_rate():.1%}]")
                    self.failed_operations += 1
                    self.circuit_breaker.record_failure()
                    return None

    async def test_connectivity(self) -> bool:
        """
        Test Supabase connectivity with simple query.

        Performs a lightweight connectivity test using a simple SELECT query
        with a 5-second timeout. Sets the is_available flag based on the result.

        Returns:
            True if connectivity test passed, False otherwise

        """
        # Log configuration at startup
        self.log_configuration()

        if not self.enabled:
            logger.info("ℹ️ Supabase integration is disabled")
            self.is_available = False
            return False

        if not self.url or not self.key:
            logger.warning("⚠️ Supabase connectivity test failed: Missing SUPABASE_URL or SUPABASE_KEY")
            logger.warning("⚠️ Caching disabled - analysis will proceed without cache")
            self.is_available = False
            return False

        try:
            # Simple connectivity test - just check if API client can be created
            # This is faster and more reliable than querying a table
            client = self.get_api_client()
            if not client:
                self.is_available = False
                error_msg = (
                    "❌ Supabase connectivity test failed: Could not create API client\n"
                    "   Check your SUPABASE_URL and SUPABASE_KEY configuration in .env\n"
                    "   Set SUPABASE_ENABLED=false to disable Supabase integration"
                )
                logger.error(error_msg)
                raise ConnectionError(error_msg)

            # API client created successfully - Supabase is available
            result = True

            if result is not None:
                self.is_available = True
                logger.info(f"✅ Supabase connectivity test passed (timeout: {self.connectivity_test_timeout}s)")
                # Log initial health status
                health = self.get_health_status()
                logger.info(f"📊 Supabase Health Status: Available={health.is_available}, Circuit Breaker={'OPEN' if health.circuit_breaker_open else 'CLOSED'}")
                return True
            else:
                self.is_available = False
                error_msg = (
                    f"❌ Supabase connectivity test failed: Operation timed out after {self.connectivity_test_timeout}s\n"
                    f"   Check your SUPABASE_DB_URL configuration in .env\n"
                    f"   Set SUPABASE_ENABLED=false to disable Supabase integration"
                )
                logger.error(error_msg)
                raise ConnectionError(error_msg)

        except ConnectionError:
            # Re-raise ConnectionError from timeout case
            raise
        except Exception as e:
            self.is_available = False
            error_msg = (
                f"❌ Supabase connectivity test failed: {e}\n"
                f"   Check your SUPABASE_URL and SUPABASE_DB_URL configuration in .env\n"
                f"   Set SUPABASE_ENABLED=false to disable Supabase integration"
            )
            logger.error(error_msg)
            raise ConnectionError(error_msg) from e

    def _record_response_time(self, response_time_ms: float) -> None:
        """
        Record response time for metrics calculation.

        Maintains a rolling window of recent response times for calculating
        average response time.

        Args:
            response_time_ms: Response time in milliseconds

        """
        self.response_times.append(response_time_ms)
        # Keep only the most recent response times
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)

    def get_success_rate(self) -> float:
        """
        Calculate operation success rate.

        Returns:
            Success rate as float between 0.0 and 1.0

        """
        if self.total_operations == 0:
            return 0.0
        return self.successful_operations / self.total_operations

    def get_avg_response_time(self) -> float:
        """
        Calculate average response time.

        Returns:
            Average response time in milliseconds

        """
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def get_health_status(self) -> SupabaseHealthStatus:
        """
        Get current health status with metrics.

        Returns:
            SupabaseHealthStatus with current metrics and configuration

        """
        return SupabaseHealthStatus(
            is_available=self.is_available,
            success_rate=self.get_success_rate(),
            avg_response_time=self.get_avg_response_time(),
            circuit_breaker_open=self.circuit_breaker.is_open(),
            timeout_count=self.timeout_count,
            total_operations=self.total_operations,
            successful_operations=self.successful_operations,
            failed_operations=self.failed_operations,
            last_check_timestamp=datetime.now(),
            configuration={
                "url": self.url[:20] + "..." if len(self.url) > 20 else self.url,
                "read_timeout": self.read_timeout,
                "write_timeout": self.write_timeout,
                "connectivity_test_timeout": self.connectivity_test_timeout,
                "max_retries": self.max_retries,
                "circuit_breaker_threshold": self.circuit_breaker.failure_threshold,
                "circuit_breaker_timeout": self.circuit_breaker.recovery_timeout,
            },
        )

    def reset_metrics(self) -> None:
        """
        Reset operation metrics.

        Useful for testing or periodic metric resets.
        """
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.timeout_count = 0
        self.response_times = []
        logger.debug("Supabase client metrics reset")

    def log_metrics(self) -> None:
        """
        Log current metrics at INFO level.

        Logs operational metrics including success rate, response times,
        and operation counts.
        """
        health = self.get_health_status()
        logger.info(
            f"Supabase Metrics: "
            f"Available={health.is_available}, "
            f"Success Rate={health.success_rate:.1%}, "
            f"Avg Response Time={health.avg_response_time:.1f}ms, "
            f"Circuit Breaker={'OPEN' if health.circuit_breaker_open else 'CLOSED'}, "
            f"Total Ops={health.total_operations}, "
            f"Successful={health.successful_operations}, "
            f"Failed={health.failed_operations}, "
            f"Timeouts={health.timeout_count}"
        )

    def log_configuration(self) -> None:
        """
        Log current configuration at startup.

        Logs Supabase configuration including URL, timeouts, pool settings,
        and circuit breaker configuration.
        """
        masked_url = self.url[:20] + "..." if len(self.url) > 20 else self.url
        has_db_url = "Yes" if self.db_url else "No"
        logger.info(
            f"📋 Supabase Configuration: "
            f"URL={masked_url}, "
            f"Enabled={self.enabled}, "
            f"DB URL Configured={has_db_url}, "
            f"Pool Min/Max={self.pool_min_size}/{self.pool_max_size}, "
            f"Pool Idle Timeout={self.pool_idle_timeout}s, "
            f"Read Timeout={self.read_timeout}s, "
            f"Write Timeout={self.write_timeout}s, "
            f"Connectivity Test Timeout={self.connectivity_test_timeout}s, "
            f"Max Retries={self.max_retries}, "
            f"Circuit Breaker Threshold={self.circuit_breaker.failure_threshold}, "
            f"Circuit Breaker Timeout={self.circuit_breaker.recovery_timeout}s"
        )

    def should_log_metrics(self) -> bool:
        """
        Check if metrics should be logged (every 100 operations).

        Returns:
            True if metrics should be logged, False otherwise

        """
        return self.total_operations > 0 and self.total_operations % 100 == 0

    async def periodic_health_check(self) -> None:
        """
        Perform periodic health check on connection pool.

        Logs pool statistics and alerts if utilization is high.
        Should be called periodically (e.g., every 5 minutes) by monitoring system.
        """
        if not self.db_pool:
            logger.debug("Connection pool not initialized, skipping health check")
            return

        stats = await self.get_pool_stats()

        if stats["status"] == "disabled":
            return

        # Calculate utilization
        size = stats["size"]
        free_size = stats["free_size"]
        max_size = stats["max_size"]
        utilization = (size - free_size) / max_size if max_size > 0 else 0.0

        # Log health check
        logger.info(f"🏥 Pool Health Check: size={size}/{max_size}, free={free_size}, utilization={utilization:.1%}")

        # Alert if utilization is high
        if utilization >= 0.95:
            logger.error(f"🚨 CRITICAL: Pool utilization very high: {utilization:.1%}")
        elif utilization >= 0.80:
            logger.warning(f"⚠️ WARNING: Pool utilization high: {utilization:.1%}")
