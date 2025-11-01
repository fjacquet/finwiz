"""
Analysis repository for CRUD operations on analysis data.

Provides async storage and retrieval of analysis results with:
- TTL-based caching (default 24 hours)
- Non-blocking background storage
- Exponential backoff retry logic
- Strict timeout enforcement (2s reads, 5s writes)
- Performance monitoring and metrics tracking
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.models import AnalysisRecord
from finwiz.supabase.utils.monitoring import OperationType, PerformanceMonitor

logger = logging.getLogger(__name__)


class AnalysisRepository:
    """
    Repository for analysis storage and retrieval.

    Handles CRUD operations for analysis data with async execution,
    caching, and graceful error handling.

    Attributes:
        client: SupabaseClient instance for database operations
        table: Database table name for analyses

    """

    def __init__(
        self,
        client: SupabaseClient,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        """
        Initialize analysis repository.

        Args:
            client: SupabaseClient instance
            performance_monitor: Optional performance monitor for metrics tracking

        """
        self.client = client
        self.table = "analyses"
        self.performance_monitor = performance_monitor or PerformanceMonitor()

    async def get_cached_analysis(
        self,
        ticker: str,
        asset_class: str,
        ttl_hours: int | None = None,
    ) -> AnalysisRecord | None:
        """
        Get cached analysis if within TTL.

        Retrieves the most recent analysis for a ticker/asset_class combination
        if it exists and is within the TTL window. Uses strict 2-second timeout.

        Args:
            ticker: Asset ticker symbol (will be uppercased)
            asset_class: Asset class (stock, etf, crypto)
            ttl_hours: Cache TTL in hours (default: from env or 24)

        Returns:
            AnalysisRecord if found and within TTL, None otherwise

        """
        # Get TTL from environment or use default
        if ttl_hours is None:
            ttl_hours = int(os.getenv("ANALYSIS_CACHE_TTL_HOURS", "24"))

        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

        # Normalize inputs
        ticker_upper = ticker.upper()
        asset_class_lower = asset_class.lower()

        logger.debug(f"Checking cache for {ticker_upper} ({asset_class_lower}), TTL: {ttl_hours}h, cutoff: {cutoff_time.isoformat()}")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return (
                client.table(self.table)
                .select("*")
                .eq("ticker", ticker_upper)
                .eq("asset_class", asset_class_lower)
                .gte("created_at", cutoff_time.isoformat())
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )

        # Track operation duration
        start_time = time.time()
        success = False
        timeout = False

        try:
            # Execute with configured read timeout
            result = await self.client.execute_with_timeout(query)

            if result and result.data:
                logger.info(f"Cache HIT for {ticker_upper} ({asset_class_lower})")
                success = True
                return AnalysisRecord(**result.data[0])

            logger.info(f"Cache MISS for {ticker_upper} ({asset_class_lower})")
            success = True  # Cache miss is still a successful operation
            return None

        except TimeoutError:
            logger.error(f"Cache check timed out for {ticker_upper}")
            timeout = True
            return None

        except Exception as e:
            logger.error(f"Cache check failed for {ticker_upper}: {e}")
            return None

        finally:
            # Record operation metrics
            duration_ms = (time.time() - start_time) * 1000
            self.performance_monitor.record_operation(
                OperationType.CACHE_CHECK,
                duration_ms,
                success=success,
                timeout=timeout,
            )

    async def store_analysis(
        self,
        ticker: str,
        asset_class: str,
        export_data: dict[str, Any],
    ) -> bool:
        """
        Store analysis asynchronously (background task).

        Stores analysis results in the background without blocking.
        Returns immediately and logs success/failure asynchronously.

        Args:
            ticker: Asset ticker symbol (will be uppercased)
            asset_class: Asset class (stock, etf, crypto)
            export_data: Complete analysis export data (must include required fields)

        Returns:
            True (always returns immediately, actual storage is async)

        """
        # Normalize inputs
        ticker_upper = ticker.upper()
        asset_class_lower = asset_class.lower()

        logger.debug(f"Scheduling async storage for {ticker_upper} ({asset_class_lower})")

        # Extract required fields from export data
        composite_score = export_data.get("composite_score", 0.0)
        grade = export_data.get("grade", "F")
        recommendation = export_data.get("recommendation", "HOLD")

        def insert(client: Any) -> Any:
            """Insert function for execute_with_timeout."""
            return (
                client.table(self.table)
                .insert(
                    {
                        "ticker": ticker_upper,
                        "asset_class": asset_class_lower,
                        "composite_score": composite_score,
                        "grade": grade,
                        "recommendation": recommendation,
                        "export_json": export_data,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

        # Execute in background task (non-blocking)
        asyncio.create_task(
            self._store_with_retry(
                insert,
                ticker=ticker_upper,
                asset_class=asset_class_lower,
            )
        )

        return True  # Return immediately

    async def _store_with_retry(
        self,
        operation: Any,
        ticker: str,
        asset_class: str,
        max_retries: int | None = None,
    ) -> None:
        """
        Store with exponential backoff retry.

        Attempts to store analysis with retry logic. Logs success/failure
        but does not raise exceptions (background task).

        Args:
            operation: Database operation to execute
            ticker: Ticker symbol (for logging)
            asset_class: Asset class (for logging)
            max_retries: Maximum number of retry attempts (default: from client config)

        """
        # Use configured max_retries if not specified
        if max_retries is None:
            max_retries = self.client.max_retries

        # Track operation duration
        start_time = time.time()
        success = False
        timeout = False
            
        for attempt in range(max_retries):
            try:
                logger.debug(f"Store attempt {attempt + 1}/{max_retries} for {ticker} (timeout: {self.client.write_timeout}s)")
                result = await self.client.execute_with_timeout(operation, timeout=self.client.write_timeout)

                if result:
                    logger.info(f"Analysis stored successfully for {ticker} ({asset_class})")
                    success = True
                    break

                # If result is None, operation failed or timed out
                logger.warning(f"Store attempt {attempt + 1}/{max_retries} returned None for {ticker}")

            except TimeoutError:
                logger.error(f"Store attempt {attempt + 1}/{max_retries} timed out for {ticker}")
                timeout = True

            except Exception as e:
                logger.error(f"Store attempt {attempt + 1}/{max_retries} failed for {ticker}: {e}")

            # Exponential backoff before retry (except on last attempt)
            if attempt < max_retries - 1:
                backoff_seconds = 2**attempt  # 1s, 2s, 4s
                logger.debug(f"Retrying in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)

        # Record operation metrics
        duration_ms = (time.time() - start_time) * 1000
        self.performance_monitor.record_operation(
            OperationType.WRITE,
            duration_ms,
            success=success,
            timeout=timeout,
        )

        # All retries exhausted
        if not success:
            logger.error(f"Failed to store analysis for {ticker} ({asset_class}) after {max_retries} attempts")

    async def get_by_id(self, analysis_id: str) -> AnalysisRecord | None:
        """
        Get analysis by ID.

        Retrieves a specific analysis by its unique identifier.
        Uses configured read timeout.

        Args:
            analysis_id: Unique analysis identifier (UUID)

        Returns:
            AnalysisRecord if found, None otherwise

        """
        logger.debug(f"Fetching analysis by ID: {analysis_id}")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return client.table(self.table).select("*").eq("id", analysis_id).limit(1).execute()

        # Track operation duration
        start_time = time.time()
        success = False
        timeout = False

        try:
            result = await self.client.execute_with_timeout(query)

            if result and result.data:
                logger.debug(f"Found analysis: {analysis_id}")
                success = True
                return AnalysisRecord(**result.data[0])

            logger.debug(f"Analysis not found: {analysis_id}")
            success = True  # Not found is still a successful operation
            return None

        except TimeoutError:
            logger.error(f"Fetch timed out for analysis {analysis_id}")
            timeout = True
            return None

        except Exception as e:
            logger.error(f"Failed to fetch analysis {analysis_id}: {e}")
            return None

        finally:
            # Record operation metrics
            duration_ms = (time.time() - start_time) * 1000
            self.performance_monitor.record_operation(
                OperationType.READ,
                duration_ms,
                success=success,
                timeout=timeout,
            )

    async def get_recent_analyses(
        self,
        limit: int = 10,
        asset_class: str | None = None,
    ) -> list[AnalysisRecord]:
        """
        Get recent analyses.

        Retrieves the most recent analyses, optionally filtered by asset class.
        Uses configured read timeout.

        Args:
            limit: Maximum number of analyses to return (default: 10)
            asset_class: Optional asset class filter (stock, etf, crypto)

        Returns:
            List of AnalysisRecord objects (may be empty)

        """
        logger.debug(f"Fetching recent analyses (limit: {limit}, asset_class: {asset_class})")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            q = client.table(self.table).select("*")

            if asset_class:
                q = q.eq("asset_class", asset_class.lower())

            return q.order("created_at", desc=True).limit(limit).execute()

        # Track operation duration
        start_time = time.time()
        success = False
        timeout = False

        try:
            result = await self.client.execute_with_timeout(query)

            if result and result.data:
                analyses = [AnalysisRecord(**record) for record in result.data]
                logger.info(f"Retrieved {len(analyses)} recent analyses")
                success = True
                return analyses

            logger.info("No recent analyses found")
            success = True  # Empty result is still a successful operation
            return []

        except TimeoutError:
            logger.error("Fetch recent analyses timed out")
            timeout = True
            return []

        except Exception as e:
            logger.error(f"Failed to fetch recent analyses: {e}")
            return []

        finally:
            # Record operation metrics
            duration_ms = (time.time() - start_time) * 1000
            self.performance_monitor.record_operation(
                OperationType.READ,
                duration_ms,
                success=success,
                timeout=timeout,
            )
