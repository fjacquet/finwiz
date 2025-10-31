"""
Supabase client with circuit breaker protection.

Manages Supabase connection with lazy initialization, timeout enforcement,
and automatic circuit breaker protection against cascading failures.
"""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import Any

from supabase import Client, create_client

from finwiz.supabase.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase client with circuit breaker protection.

    Provides connection management with:
    - Lazy initialization from environment variables
    - Circuit breaker for failure protection
    - Timeout enforcement for operations
    - Graceful error handling

    Attributes:
        url: Supabase project URL
        key: Supabase API key
        enabled: Whether Supabase integration is enabled
        client: Supabase client instance (lazy initialized)
        circuit_breaker: Circuit breaker for failure protection

    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: int = 300,
    ) -> None:
        """
        Initialize Supabase client.

        Args:
            failure_threshold: Circuit breaker failure threshold (default: 3)
            recovery_timeout: Circuit breaker recovery timeout in seconds (default: 300)

        """
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.key: str = os.getenv("SUPABASE_KEY", "")
        self.enabled: bool = os.getenv("SUPABASE_ENABLED", "true").lower() == "true"
        self.client: Client | None = None
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    def get_client(self) -> Client | None:
        """
        Get Supabase client if available and circuit is closed.

        Returns:
            Supabase client instance or None if unavailable/circuit open

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

        if not self.client:
            try:
                self.client = create_client(self.url, self.key)
                self.circuit_breaker.record_success()
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                self.circuit_breaker.record_failure()
                logger.error(f"Failed to connect to Supabase: {e}")
                return None

        return self.client

    async def execute_with_timeout(
        self,
        operation: Callable[[Client], Any],
        timeout: float = 2.0,
    ) -> Any | None:
        """
        Execute operation with timeout and circuit breaker protection.

        Args:
            operation: Callable that takes Supabase client and returns result
            timeout: Timeout in seconds (default: 2.0)

        Returns:
            Operation result or None if failed/timed out

        """
        client = self.get_client()
        if not client:
            return None

        try:
            # Execute operation with timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(operation, client),
                timeout=timeout,
            )
            self.circuit_breaker.record_success()
            return result

        except TimeoutError:
            logger.warning(f"Database operation timed out after {timeout}s")
            self.circuit_breaker.record_failure()
            return None

        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            self.circuit_breaker.record_failure()
            return None
