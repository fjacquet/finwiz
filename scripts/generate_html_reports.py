#!/usr/bin/env python
"""
Generate HTML reports from existing JSON crew outputs.

This script finds all JSON crew output files and generates corresponding
HTML reports using the JsonToHtmlConverter.

Usage:
    python scripts/generate_html_reports.py
    python scripts/generate_html_reports.py --output-dir custom/path
    python scripts/generate_html_reports.py --force  # Overwrite existing
"""

import argparse
import logging
from pathlib import Path

from finwiz.integration.html_auto_generator import auto_generate_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def find_crew_json_files(output_dir: Path) -> list[Path]:
    """
    Find all crew output JSON files.

    Args:
        output_dir: Base output directory to search

    Returns:
        List of JSON file paths

    """
    json_files = []

    # Patterns for crew output files
    patterns = [
        "deep_analysis_*/deep_analysis_*.json",
        "stock/discovery_output_*.json",
        "etf/discovery_output_*.json",
        "crypto/discovery_output_*.json",
        "discovery/discovery_output_*.json",
        "portfolio/*.json",
    ]

    for pattern in patterns:
        matches = list(output_dir.glob(pattern))
        json_files.extend(matches)
        logger.debug(f"Pattern '{pattern}' found {len(matches)} files")

    return json_files


def generate_html_for_files(json_files: list[Path], force: bool = False) -> tuple[int, int]:
    """
    Generate HTML reports for JSON files.

    Args:
        json_files: List of JSON file paths
        force: Whether to overwrite existing HTML files

    Returns:
        Tuple of (success_count, skip_count)

    """
    success_count = 0
    skip_count = 0

    for json_path in json_files:
        logger.info(f"Processing: {json_path.relative_to(json_path.parents[1])}")

        # Determine crew name from path
        crew_name = json_path.parent.name

        # Check if HTML already exists
        html_dir = json_path.parent / "html"
        html_path = html_dir / f"{json_path.stem}.html"

        if html_path.exists() and not force:
            logger.info("  ⏭️  HTML already exists, skipping")
            skip_count += 1
            continue

        # Generate HTML (reads JSON file internally)
        try:
            # Load JSON data
            import json

            with open(json_path) as f:
                output_data = json.load(f)

            # Generate HTML
            result_path = auto_generate_html(json_path, output_data, crew_name)

            if result_path:
                logger.info(f"  ✅ Generated: {result_path.relative_to(json_path.parents[1])}")
                success_count += 1
            else:
                logger.warning("  ⚠️  Generation failed (no template?)")
                skip_count += 1

        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            skip_count += 1

    return success_count, skip_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate HTML reports from JSON crew outputs")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory to search for JSON files (default: output/)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing HTML files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    output_dir = args.output_dir

    if not output_dir.exists():
        logger.error(f"Output directory not found: {output_dir}")
        return 1

    logger.info(f"🔍 Searching for JSON files in: {output_dir}")

    # Find all JSON files
    json_files = find_crew_json_files(output_dir)

    if not json_files:
        logger.warning("No JSON files found")
        return 0

    logger.info(f"📋 Found {len(json_files)} JSON files")

    # Generate HTML reports
    logger.info("🚀 Generating HTML reports...")
    success_count, skip_count = generate_html_for_files(json_files, args.force)

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files: {len(json_files)}")
    logger.info(f"✅ Generated: {success_count}")
    logger.info(f"⏭️  Skipped: {skip_count}")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
