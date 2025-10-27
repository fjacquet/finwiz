#!/usr/bin/env python3
"""
Generate HTML reports from JSON files.

This script converts FinWiz JSON output files into professional HTML reports
with dark/light mode support.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.utils.template_renderer import TemplateRenderer, generate_html_reports


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate HTML reports from FinWiz JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all HTML reports from output directory
  python scripts/generate_html_reports.py --all
  
  # Generate specific report
  python scripts/generate_html_reports.py --file output/portfolio_review.json --type portfolio_review
  
  # Generate with custom output path
  python scripts/generate_html_reports.py --file output/backtesting_results_default.json --type backtesting_results --output reports/backtesting.html

Supported template types:
  - backtesting_results
  - portfolio_review
  - a_plus_discovery
  - deep_analysis_consolidated
  - optimization_report
  - validation_report
  - discovery_latest
  - portfolio_processing_summary
  - feedback_learning_report
        """,
    )

    parser.add_argument("--all", action="store_true", help="Generate HTML reports for all JSON files in output directory")

    parser.add_argument("--file", type=Path, help="Path to specific JSON file to convert")

    parser.add_argument(
        "--type",
        choices=[
            "backtesting_results",
            "portfolio_review",
            "a_plus_discovery",
            "deep_analysis_consolidated",
            "optimization_report",
            "validation_report",
            "discovery_latest",
            "portfolio_processing_summary",
            "feedback_learning_report",
        ],
        help="Template type to use for rendering",
    )

    parser.add_argument("--output", type=Path, help="Output path for HTML file (optional)")

    parser.add_argument("--templates-dir", type=Path, help="Custom templates directory (optional)")

    args = parser.parse_args()

    # Validate arguments
    if not args.all and not args.file:
        parser.error("Either --all or --file must be specified")

    if args.file and not args.type:
        parser.error("--type must be specified when using --file")

    if args.all and (args.file or args.type or args.output):
        parser.error("--all cannot be used with --file, --type, or --output")

    try:
        renderer = TemplateRenderer(args.templates_dir)

        if args.all:
            # Generate all reports
            print("🚀 Generating HTML reports for all JSON files...")
            generated_files = generate_html_reports()

            if generated_files:
                print(f"\n✅ Successfully generated {len(generated_files)} HTML reports:")
                for file_path in generated_files:
                    print(f"   📄 {file_path}")
            else:
                print("⚠️  No JSON files found to process")

        else:
            # Generate specific report
            if not args.file.exists():
                print(f"❌ Error: JSON file not found: {args.file}")
                sys.exit(1)

            print(f"🚀 Generating HTML report for {args.file}...")
            html_file = renderer.save_html_report(args.file, args.type, args.output)
            print(f"✅ Successfully generated: {html_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
