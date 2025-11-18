#!/usr/bin/env python3
"""
Generate HTML Reports from JSON Output Files.

This script converts all JSON output files to HTML using Jinja2 templates.
Run this after FinWiz analysis to generate human-readable HTML reports.

Usage:
    python scripts/generate_html_reports.py
    python scripts/generate_html_reports.py --output-dir output
    python scripts/generate_html_reports.py --verbose
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.tools.logger import get_logger
from finwiz.utils.json_to_html_converter import JsonToHtmlConverter

logger = get_logger(__name__)


def main():
    """Main entry point for HTML report generation."""
    parser = argparse.ArgumentParser(
        description="Generate HTML reports from JSON output files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory containing JSON files (default: output)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)

    # Initialize converter
    converter = JsonToHtmlConverter()

    # Convert all JSON files
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        logger.error(f"Output directory does not exist: {output_dir}")
        sys.exit(1)

    logger.info(f"🔄 Converting JSON files in {output_dir} to HTML...")
    results = converter.convert_directory(output_dir)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 HTML Report Generation Summary")
    print("=" * 60)
    print(f"✅ Successfully converted: {len(results['success'])} files")
    print(f"❌ Failed to convert: {len(results['failed'])} files")
    print("=" * 60)

    if results["success"]:
        print("\n✅ Successfully converted files:")
        for success_file in results["success"]:
            html_file = Path(success_file).with_suffix(".html")
            print(f"   {success_file} → {html_file}")

    if results["failed"]:
        print("\n❌ Failed to convert files:")
        for failed_file in results["failed"]:
            print(f"   {failed_file}")

    print("\n💡 Tip: Open the HTML files in your browser to view the reports")

    # Exit with error code if any conversions failed
    sys.exit(0 if not results["failed"] else 1)


if __name__ == "__main__":
    main()
