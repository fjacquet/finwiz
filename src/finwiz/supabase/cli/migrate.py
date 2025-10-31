#!/usr/bin/env python
"""
CLI command for migrating file-based exports to Supabase.

Provides a command-line interface for:
- Migrating all exports or specific asset classes
- Dry-run mode to preview migrations
- Progress tracking with visual feedback
- Summary report of migration results
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.services.migration_service import MigrationService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_progress_bar(
    current: int,
    total: int,
    file_path: Path,
    bar_length: int = 50,
) -> None:
    """
    Print a progress bar to the console.

    Args:
        current: Current file number
        total: Total number of files
        file_path: Path to current file being processed
        bar_length: Length of progress bar in characters

    """
    percent = current / total
    filled_length = int(bar_length * percent)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)

    # Truncate file path if too long
    file_str = str(file_path)
    if len(file_str) > 60:
        file_str = "..." + file_str[-57:]

    # Print progress bar (overwrite previous line)
    print(
        f"\r[{bar}] {current}/{total} ({percent*100:.1f}%) - {file_str}",
        end="",
        flush=True,
    )


def print_summary(result: any) -> None:
    """
    Print migration summary report.

    Args:
        result: MigrationResult object

    """
    print("\n\n" + "=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)

    summary = result.summary()
    print(f"Total files scanned:    {summary['total_files']}")
    print(f"Successfully migrated:  {summary['successful']}")
    print(f"Skipped (duplicates):   {summary['skipped']}")
    print(f"Failed:                 {summary['failed']}")
    print(f"Success rate:           {summary['success_rate']}")

    # Print errors if any
    if result.errors:
        print("\n" + "-" * 70)
        print("ERRORS:")
        print("-" * 70)
        for error in result.errors[:10]:  # Show first 10 errors
            print(f"  • {error['file']}")
            print(f"    Error: {error['error']}")

        if len(result.errors) > 10:
            print(f"\n  ... and {len(result.errors) - 10} more errors")

    print("=" * 70)


async def run_migration(
    output_dir: str,
    asset_classes: list[str] | None,
    dry_run: bool,
    force: bool,
    verbose: bool,
) -> int:
    """
    Run the migration process.

    Args:
        output_dir: Base directory for exports
        asset_classes: Optional list of asset classes to migrate
        dry_run: If True, preview without executing
        force: If True, skip idempotency checks
        verbose: If True, enable debug logging

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    # Configure logging level
    if verbose:
        logging.getLogger("finwiz.supabase").setLevel(logging.DEBUG)

    # Initialize service
    logger.info("Initializing migration service...")
    client = SupabaseClient()
    service = MigrationService(client=client, output_dir=output_dir)

    # Check if Supabase is enabled
    if not client.enabled:
        logger.error("Supabase is not enabled. Set SUPABASE_ENABLED=true in environment.")
        return 1

    # Scan for exports
    logger.info(f"Scanning for exports in: {output_dir}")
    json_files = service.scan_exports(asset_classes=asset_classes)

    if not json_files:
        logger.warning("No export files found to migrate")
        return 0

    logger.info(f"Found {len(json_files)} export files")

    # Dry-run mode: preview without executing
    if dry_run:
        print("\n" + "=" * 70)
        print("DRY RUN MODE - Preview of files to migrate:")
        print("=" * 70)

        for idx, file_path in enumerate(json_files, start=1):
            # Check if already migrated
            already_migrated = await service._is_already_migrated(file_path)
            status = "SKIP (already migrated)" if already_migrated and not force else "MIGRATE"

            print(f"{idx:4d}. [{status:25s}] {file_path}")

        print("=" * 70)
        print(f"\nTotal files: {len(json_files)}")
        print("\nRun without --dry-run to execute migration")
        return 0

    # Execute migration with progress tracking
    logger.info("Starting migration...")

    result = await service.migrate_all(
        asset_classes=asset_classes,
        force=force,
        progress_callback=print_progress_bar,
    )

    # Print summary
    print_summary(result)

    # Return exit code based on results
    if result.failed > 0:
        logger.warning(f"Migration completed with {result.failed} failures")
        return 1

    logger.info("Migration completed successfully")
    return 0


def main() -> int:
    """
    Execute migration CLI command.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    parser = argparse.ArgumentParser(
        description="Migrate file-based exports to Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all exports
  python -m finwiz.supabase.cli.migrate

  # Dry-run to preview migration
  python -m finwiz.supabase.cli.migrate --dry-run

  # Migrate only stock exports
  python -m finwiz.supabase.cli.migrate --asset-class stock

  # Force re-migration of all files
  python -m finwiz.supabase.cli.migrate --force

  # Migrate from custom directory
  python -m finwiz.supabase.cli.migrate --output-dir /path/to/exports
        """,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Base directory for exports (default: output)",
    )

    parser.add_argument(
        "--asset-class",
        type=str,
        action="append",
        dest="asset_classes",
        choices=["stock", "etf", "crypto"],
        help="Asset class to migrate (can be specified multiple times)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without executing",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-migration of already migrated files",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Run migration
    try:
        exit_code = asyncio.run(
            run_migration(
                output_dir=args.output_dir,
                asset_classes=args.asset_classes,
                dry_run=args.dry_run,
                force=args.force,
                verbose=args.verbose,
            )
        )
        return exit_code

    except KeyboardInterrupt:
        print("\n\nMigration interrupted by user")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        logger.error(f"Migration failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
