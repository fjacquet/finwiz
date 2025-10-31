"""
Migration service for importing existing file-based exports to Supabase.

Provides functionality to:
- Scan output directory for JSON exports
- Validate exports against Pydantic schemas
- Store validated exports in Supabase
- Track migration progress and errors
- Prevent duplicate migrations (idempotency)
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)


class MigrationResult:
    """Result of a migration operation."""

    def __init__(self) -> None:
        """Initialize migration result."""
        self.total_files: int = 0
        self.successful: int = 0
        self.skipped: int = 0
        self.failed: int = 0
        self.errors: list[dict[str, Any]] = []
        self.migrated_files: list[str] = []
        self.skipped_files: list[str] = []

    def add_success(self, file_path: str) -> None:
        """Record successful migration."""
        self.successful += 1
        self.migrated_files.append(file_path)

    def add_skip(self, file_path: str, reason: str) -> None:
        """Record skipped file."""
        self.skipped += 1
        self.skipped_files.append(file_path)
        logger.debug(f"Skipped {file_path}: {reason}")

    def add_error(self, file_path: str, error: str) -> None:
        """Record failed migration."""
        self.failed += 1
        self.errors.append({"file": file_path, "error": error})
        logger.error(f"Failed to migrate {file_path}: {error}")

    def summary(self) -> dict[str, Any]:
        """Get migration summary."""
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "skipped": self.skipped,
            "failed": self.failed,
            "success_rate": (
                f"{(self.successful / self.total_files * 100):.1f}%"
                if self.total_files > 0
                else "0%"
            ),
        }


class MigrationService:
    """
    Service for migrating file-based exports to Supabase.

    Handles scanning, validation, and storage of existing JSON exports
    with idempotency checks and progress tracking.

    Attributes:
        client: SupabaseClient instance
        repository: AnalysisRepository for storage operations
        output_dir: Base directory for exports (default: "output")

    """

    def __init__(
        self,
        client: SupabaseClient | None = None,
        output_dir: str = "output",
    ) -> None:
        """
        Initialize migration service.

        Args:
            client: SupabaseClient instance (creates new if None)
            output_dir: Base directory for exports (default: "output")

        """
        self.client = client or SupabaseClient()
        self.repository = AnalysisRepository(self.client)
        self.output_dir = Path(output_dir)

        # Table for tracking migrated files (idempotency)
        self.migration_table = "migration_history"

    def scan_exports(
        self,
        asset_classes: list[str] | None = None,
    ) -> list[Path]:
        """
        Scan output directory for JSON exports.

        Finds all JSON files in the output directory structure,
        optionally filtered by asset class.

        Args:
            asset_classes: Optional list of asset classes to scan
                          (e.g., ["stock", "etf", "crypto"])
                          If None, scans all asset classes

        Returns:
            List of Path objects for found JSON files

        """
        if not self.output_dir.exists():
            logger.warning(f"Output directory does not exist: {self.output_dir}")
            return []

        # Default to all known asset classes
        if asset_classes is None:
            asset_classes = ["stock", "etf", "crypto"]

        json_files: list[Path] = []

        for asset_class in asset_classes:
            asset_dir = self.output_dir / asset_class

            if not asset_dir.exists():
                logger.debug(f"Asset class directory not found: {asset_dir}")
                continue

            # Find all JSON files (excluding HTML)
            for json_file in asset_dir.glob("*.json"):
                # Skip non-analysis files (e.g., consolidated reports)
                if "_consolidated_" in json_file.name:
                    continue

                json_files.append(json_file)

        logger.info(f"Found {len(json_files)} JSON export files")
        return sorted(json_files)

    async def _is_already_migrated(self, file_path: Path) -> bool:
        """
        Check if file has already been migrated.

        Uses file hash for idempotency check to prevent duplicate migrations.

        Args:
            file_path: Path to JSON file

        Returns:
            True if file has been migrated, False otherwise

        """
        # Calculate file hash for idempotency
        file_hash = self._calculate_file_hash(file_path)

        def query(client: Any) -> Any:
            """Query migration history."""
            return (
                client.table(self.migration_table)
                .select("id")
                .eq("file_hash", file_hash)
                .limit(1)
                .execute()
            )

        try:
            result = await self.client.execute_with_timeout(query, timeout=2.0)
            return bool(result and result.data)
        except Exception as e:
            logger.warning(f"Failed to check migration history: {e}")
            # If check fails, proceed with migration (better to duplicate than skip)
            return False

    async def _record_migration(
        self,
        file_path: Path,
        analysis_id: str | None = None,
    ) -> None:
        """
        Record successful migration in history table.

        Args:
            file_path: Path to migrated file
            analysis_id: ID of created analysis record (optional)

        """
        file_hash = self._calculate_file_hash(file_path)

        def insert(client: Any) -> Any:
            """Insert migration record."""
            return (
                client.table(self.migration_table)
                .insert(
                    {
                        "file_path": str(file_path),
                        "file_hash": file_hash,
                        "analysis_id": analysis_id,
                        "migrated_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                .execute()
            )

        try:
            await self.client.execute_with_timeout(insert, timeout=5.0)
            logger.debug(f"Recorded migration: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to record migration history: {e}")
            # Non-critical error, continue

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA256 hash of file content.

        Args:
            file_path: Path to file

        Returns:
            Hex string of file hash

        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    def _extract_metadata_from_path(self, file_path: Path) -> dict[str, str]:
        """
        Extract ticker and asset class from file path.

        Expected format: output/{asset_class}/{ticker}_{suffix}.json

        Args:
            file_path: Path to JSON file

        Returns:
            Dict with 'ticker' and 'asset_class' keys

        """
        # Get asset class from parent directory
        asset_class = file_path.parent.name

        # Extract ticker from filename (format: TICKER_suffix.json)
        filename = file_path.stem  # Remove .json extension
        ticker = filename.split("_")[0]  # Get part before first underscore

        return {
            "ticker": ticker.upper(),
            "asset_class": asset_class.lower(),
        }

    def _validate_export_data(self, data: dict[str, Any]) -> bool:
        """
        Validate export data has required fields.

        Args:
            data: Export data dictionary

        Returns:
            True if valid, False otherwise

        """
        required_fields = [
            "ticker",
            "asset_class",
            "composite_score",
            "grade",
            "recommendation",
        ]

        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False

        return True

    async def migrate_export(
        self,
        file_path: Path,
        force: bool = False,
    ) -> bool:
        """
        Migrate a single export file to Supabase.

        Validates the export data and stores it in the database.
        Includes idempotency check to prevent duplicates.

        Args:
            file_path: Path to JSON export file
            force: If True, skip idempotency check and force migration

        Returns:
            True if migration successful, False otherwise

        """
        # Check if already migrated (unless forced)
        if not force and await self._is_already_migrated(file_path):
            logger.debug(f"Already migrated: {file_path}")
            return False

        try:
            # Read and parse JSON
            with open(file_path, encoding="utf-8") as f:
                export_data = json.load(f)

            # Extract metadata from path (fallback if not in data)
            metadata = self._extract_metadata_from_path(file_path)

            # Ensure ticker and asset_class are present
            if "ticker" not in export_data:
                export_data["ticker"] = metadata["ticker"]
            if "asset_class" not in export_data:
                export_data["asset_class"] = metadata["asset_class"]

            # Validate export data
            if not self._validate_export_data(export_data):
                logger.error(f"Invalid export data: {file_path}")
                return False

            # Get file modification time as timestamp (preserve original date)
            file_mtime = datetime.fromtimestamp(
                file_path.stat().st_mtime,
                tz=timezone.utc,
            )

            # Override created_at with file timestamp if not present
            if "analysis_timestamp" not in export_data:
                export_data["analysis_timestamp"] = file_mtime.isoformat()

            # Store in database
            ticker = export_data["ticker"]
            asset_class = export_data["asset_class"]

            success = await self.repository.store_analysis(
                ticker=ticker,
                asset_class=asset_class,
                export_data=export_data,
            )

            if success:
                # Record migration in history
                await self._record_migration(file_path)
                logger.info(f"Migrated: {ticker} ({asset_class}) from {file_path}")
                return True

            return False

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return False
        except ValidationError as e:
            logger.error(f"Validation failed for {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to migrate {file_path}: {e}")
            return False

    async def migrate_all(
        self,
        asset_classes: list[str] | None = None,
        force: bool = False,
        progress_callback: Any = None,
    ) -> MigrationResult:
        """
        Migrate all exports to Supabase.

        Scans for exports, validates, and stores them in the database.
        Provides progress tracking and error reporting.

        Args:
            asset_classes: Optional list of asset classes to migrate
            force: If True, skip idempotency checks and force migration
            progress_callback: Optional callback function(current, total, file_path)
                              called after each file is processed

        Returns:
            MigrationResult with summary and details

        """
        result = MigrationResult()

        # Scan for exports
        json_files = self.scan_exports(asset_classes=asset_classes)
        result.total_files = len(json_files)

        if result.total_files == 0:
            logger.warning("No export files found to migrate")
            return result

        logger.info(f"Starting migration of {result.total_files} files...")

        # Process each file
        for idx, file_path in enumerate(json_files, start=1):
            # Call progress callback if provided
            if progress_callback:
                progress_callback(idx, result.total_files, file_path)

            try:
                # Check if already migrated (unless forced)
                if not force and await self._is_already_migrated(file_path):
                    result.add_skip(str(file_path), "already migrated")
                    continue

                # Attempt migration
                success = await self.migrate_export(file_path, force=force)

                if success:
                    result.add_success(str(file_path))
                else:
                    result.add_error(str(file_path), "migration returned False")

            except Exception as e:
                result.add_error(str(file_path), str(e))

        # Log summary
        summary = result.summary()
        logger.info(
            f"Migration complete: {summary['successful']} successful, "
            f"{summary['skipped']} skipped, {summary['failed']} failed "
            f"({summary['success_rate']} success rate)"
        )

        return result
