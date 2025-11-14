"""
Portfolio repository for snapshot operations.

Provides async storage and retrieval of portfolio snapshots with:
- Point-in-time portfolio state capture
- Historical snapshot retrieval ordered by date
- Snapshot comparison for tracking changes
- Non-blocking background storage
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.models import PortfolioSnapshot

logger = logging.getLogger(__name__)


class PortfolioRepository:
    """
    Repository for portfolio snapshot operations.

    Handles CRUD operations for portfolio snapshots with async execution,
    historical tracking, and graceful error handling.

    Attributes:
        client: SupabaseClient instance for database operations
        table: Database table name for portfolio snapshots

    """

    def __init__(self, client: SupabaseClient) -> None:
        """
        Initialize portfolio repository.

        Args:
            client: SupabaseClient instance

        """
        self.client = client
        self.table = "portfolio_snapshots"

    async def create_snapshot(
        self,
        total_value: float,
        holdings: dict[str, Any],
        snapshot_date: datetime | None = None,
    ) -> bool:
        """
        Store portfolio snapshot asynchronously (background task).

        Creates a point-in-time snapshot of portfolio state in the background
        without blocking. Returns immediately and logs success/failure asynchronously.

        Args:
            total_value: Total portfolio value
            holdings: Portfolio holdings data (dict with ticker keys)
            snapshot_date: Optional snapshot timestamp (default: now UTC)

        Returns:
            True (always returns immediately, actual storage is async)

        """
        # Use provided snapshot_date or current time
        if snapshot_date is None:
            snapshot_date = datetime.now(timezone.utc)

        logger.debug(
            f"Scheduling async snapshot creation for {snapshot_date.isoformat()}, "
            f"total_value: ${total_value:,.2f}, holdings: {len(holdings)}"
        )

        def insert(client: Any) -> Any:
            """Insert function for execute_with_timeout."""
            return (
                client.table(self.table)
                .insert(
                    {
                        "snapshot_date": snapshot_date.isoformat(),
                        "total_value": total_value,
                        "holdings": holdings,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

        # Execute in background task (non-blocking)
        asyncio.create_task(
            self._store_with_retry(
                insert,
                snapshot_date=snapshot_date,
                total_value=total_value,
            )
        )

        return True  # Return immediately

    async def _store_with_retry(
        self,
        operation: Any,
        snapshot_date: datetime,
        total_value: float,
        max_retries: int | None = None,
    ) -> None:
        """
        Store snapshot with exponential backoff retry.

        Attempts to store snapshot with retry logic. Logs success/failure
        but does not raise exceptions (background task).

        Args:
            operation: Database operation to execute
            snapshot_date: Snapshot timestamp (for logging)
            total_value: Total portfolio value (for logging)
            max_retries: Maximum number of retry attempts (default: from client config)

        """
        # Use configured max_retries if not specified
        if max_retries is None:
            max_retries = self.client.max_retries
            
        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"Snapshot store attempt {attempt + 1}/{max_retries} for "
                    f"{snapshot_date.isoformat()} (timeout: {self.client.write_timeout}s)"
                )
                result = await self.client.execute_with_timeout(operation, timeout=self.client.write_timeout)

                if result:
                    logger.info(
                        f"Portfolio snapshot stored successfully for "
                        f"{snapshot_date.isoformat()}, value: ${total_value:,.2f}"
                    )
                    return

                # If result is None, operation failed or timed out
                logger.warning(
                    f"Snapshot store attempt {attempt + 1}/{max_retries} returned None "
                    f"for {snapshot_date.isoformat()}"
                )

            except Exception as e:
                logger.error(
                    f"Snapshot store attempt {attempt + 1}/{max_retries} failed "
                    f"for {snapshot_date.isoformat()}: {e}"
                )

            # Exponential backoff before retry (except on last attempt)
            if attempt < max_retries - 1:
                backoff_seconds = 2**attempt  # 1s, 2s, 4s
                logger.debug(f"Retrying in {backoff_seconds}s...")
                await asyncio.sleep(backoff_seconds)

        # All retries exhausted
        logger.error(
            f"Failed to store portfolio snapshot for {snapshot_date.isoformat()} "
            f"after {max_retries} attempts"
        )

    async def get_snapshots(
        self,
        limit: int = 10,
    ) -> list[PortfolioSnapshot]:
        """
        Retrieve portfolio history ordered by date descending.

        Gets the most recent portfolio snapshots, ordered from newest to oldest.
        Uses configured read timeout.

        Args:
            limit: Maximum number of snapshots to return (default: 10)

        Returns:
            List of PortfolioSnapshot objects ordered by date (may be empty)

        """
        logger.debug(f"Fetching portfolio snapshots (limit: {limit})")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return (
                client.table(self.table)
                .select("*")
                .order("snapshot_date", desc=True)
                .limit(limit)
                .execute()
            )

        try:
            result = await self.client.execute_with_timeout(query)

            if result and result.data:
                snapshots = [PortfolioSnapshot(**record) for record in result.data]
                logger.info(f"Retrieved {len(snapshots)} portfolio snapshots")
                return snapshots

            logger.info("No portfolio snapshots found")
            return []

        except Exception as e:
            logger.error(f"Failed to fetch portfolio snapshots: {e}")
            return []

    async def compare_snapshots(
        self,
        snapshot1: PortfolioSnapshot,
        snapshot2: PortfolioSnapshot,
    ) -> dict[str, Any]:
        """
        Calculate changes between two portfolio snapshots.

        Compares two snapshots to identify changes in holdings, grades,
        and total portfolio value. Tracks additions, removals, and modifications.

        Args:
            snapshot1: First snapshot (typically older)
            snapshot2: Second snapshot (typically newer)

        Returns:
            Dictionary with comparison results:
                - value_change: Change in total portfolio value
                - value_change_pct: Percentage change in value
                - holdings_added: List of tickers added
                - holdings_removed: List of tickers removed
                - holdings_modified: Dict of tickers with changes
                - grade_changes: Dict of tickers with grade evolution

        """
        logger.debug(
            f"Comparing snapshots: {snapshot1.snapshot_date.isoformat()} vs "
            f"{snapshot2.snapshot_date.isoformat()}"
        )

        # Calculate value changes
        value_change = snapshot2.total_value - snapshot1.total_value
        value_change_pct = (
            (value_change / snapshot1.total_value * 100) if snapshot1.total_value > 0 else 0.0
        )

        # Get holdings from both snapshots
        holdings1 = snapshot1.holdings
        holdings2 = snapshot2.holdings

        # Identify added and removed holdings
        tickers1 = set(holdings1.keys())
        tickers2 = set(holdings2.keys())

        holdings_added = list(tickers2 - tickers1)
        holdings_removed = list(tickers1 - tickers2)

        # Identify modified holdings (present in both)
        common_tickers = tickers1 & tickers2
        holdings_modified: dict[str, dict[str, Any]] = {}
        grade_changes: dict[str, dict[str, str]] = {}

        for ticker in common_tickers:
            holding1 = holdings1[ticker]
            holding2 = holdings2[ticker]

            # Check for any changes
            changes: dict[str, Any] = {}

            # Compare quantity
            if holding1.get("quantity") != holding2.get("quantity"):
                changes["quantity"] = {
                    "old": holding1.get("quantity"),
                    "new": holding2.get("quantity"),
                }

            # Compare value
            if holding1.get("value") != holding2.get("value"):
                changes["value"] = {
                    "old": holding1.get("value"),
                    "new": holding2.get("value"),
                }

            # Compare grade
            if holding1.get("grade") != holding2.get("grade"):
                changes["grade"] = {
                    "old": holding1.get("grade"),
                    "new": holding2.get("grade"),
                }
                grade_changes[ticker] = {
                    "old": holding1.get("grade", "N/A"),
                    "new": holding2.get("grade", "N/A"),
                }

            # Compare recommendation
            if holding1.get("recommendation") != holding2.get("recommendation"):
                changes["recommendation"] = {
                    "old": holding1.get("recommendation"),
                    "new": holding2.get("recommendation"),
                }

            if changes:
                holdings_modified[ticker] = changes

        comparison = {
            "snapshot1_date": snapshot1.snapshot_date.isoformat(),
            "snapshot2_date": snapshot2.snapshot_date.isoformat(),
            "value_change": value_change,
            "value_change_pct": value_change_pct,
            "holdings_added": holdings_added,
            "holdings_removed": holdings_removed,
            "holdings_modified": holdings_modified,
            "grade_changes": grade_changes,
        }

        logger.info(
            f"Snapshot comparison complete: "
            f"value change: ${value_change:,.2f} ({value_change_pct:.2f}%), "
            f"added: {len(holdings_added)}, removed: {len(holdings_removed)}, "
            f"modified: {len(holdings_modified)}"
        )

        return comparison

    async def get_snapshot_by_id(self, snapshot_id: str) -> PortfolioSnapshot | None:
        """
        Get portfolio snapshot by ID.

        Retrieves a specific snapshot by its unique identifier.
        Uses configured read timeout.

        Args:
            snapshot_id: Unique snapshot identifier (UUID)

        Returns:
            PortfolioSnapshot if found, None otherwise

        """
        logger.debug(f"Fetching snapshot by ID: {snapshot_id}")

        def query(client: Any) -> Any:
            """Query function for execute_with_timeout."""
            return (
                client.table(self.table).select("*").eq("id", snapshot_id).limit(1).execute()
            )

        try:
            result = await self.client.execute_with_timeout(query)

            if result and result.data:
                logger.debug(f"Found snapshot: {snapshot_id}")
                return PortfolioSnapshot(**result.data[0])

            logger.debug(f"Snapshot not found: {snapshot_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch snapshot {snapshot_id}: {e}")
            return None
