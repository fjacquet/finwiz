#!/usr/bin/env python3
"""
Script to validate generated financial reports for hallucinations and data quality issues.

Usage:
    python scripts/validate_report.py output/finwiz_family_financial_plan.html
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.validation.report_validator import validate_report_file

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def load_validated_tickers() -> list[str]:
    """Load validated tickers from various sources."""
    validated_tickers = []

    # Try to load from validation output
    validation_file = Path("output/validation/validated_tickers.json")
    if validation_file.exists():
        import json

        with open(validation_file) as f:
            data = json.load(f)
            validated_tickers.extend(data.get("validated_tickers", []))

    # Add common tickers that should always be valid
    common_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "SPY", "QQQ", "VTI", "TLT", "BND", "BTC", "ETH"]
    validated_tickers.extend(common_tickers)

    # Remove duplicates
    validated_tickers = list(set(validated_tickers))

    logger.info(f"Loaded {len(validated_tickers)} validated tickers")
    return validated_tickers


def main():
    """Main validation function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_report.py <report_file>")
        print("Example: python scripts/validate_report.py output/finwiz_family_financial_plan.html")
        sys.exit(1)

    report_path = Path(sys.argv[1])

    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}")
        sys.exit(1)

    print(f"\n{'=' * 80}")
    print(f"Validating Report: {report_path}")
    print(f"{'=' * 80}\n")

    # Load validated tickers
    validated_tickers = load_validated_tickers()

    # Validate report
    result = validate_report_file(report_path, validated_tickers)

    # Print results
    print(f"\n{'=' * 80}")
    print("VALIDATION RESULTS")
    print(f"{'=' * 80}\n")

    if result.is_valid:
        print("✅ REPORT PASSED VALIDATION")
    else:
        print("❌ REPORT FAILED VALIDATION")

    print("\nStatistics:")
    print(f"  Total checks: {result.stats.get('total_checks', 0)}")
    print(f"  Errors: {result.stats.get('errors', 0)}")
    print(f"  Warnings: {result.stats.get('warnings', 0)}")
    print(f"  Tickers found: {result.stats.get('tickers_found', 0)}")
    print(f"  URLs found: {result.stats.get('urls_found', 0)}")

    if result.issues:
        print(f"\n{'=' * 80}")
        print(f"ERRORS ({len(result.issues)})")
        print(f"{'=' * 80}\n")
        for i, issue in enumerate(result.issues, 1):
            print(f"{i}. [{issue.severity}] {issue.category}")
            print(f"   {issue.message}")
            if issue.location:
                print(f"   Location: {issue.location[:100]}...")
            print()

    if result.warnings:
        print(f"\n{'=' * 80}")
        print(f"WARNINGS ({len(result.warnings)})")
        print(f"{'=' * 80}\n")
        for i, warning in enumerate(result.warnings, 1):
            print(f"{i}. [{warning.severity}] {warning.category}")
            print(f"   {warning.message}")
            if warning.location:
                print(f"   Location: {warning.location[:100]}...")
            print()

    print(f"\n{'=' * 80}\n")

    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
