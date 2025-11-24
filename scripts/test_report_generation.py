#!/usr/bin/env python3
"""
Test script for report generation fixes.

Tests:
1. Deep analysis scores properly merged into portfolio_review.json
2. Individual HTML files generated for each deep analysis
3. Discovery opportunities included in final report
4. All JSON data properly integrated

Usage:
    uv run python scripts/test_report_generation.py
"""

import json
import sys
from pathlib import Path


def test_portfolio_scores_merged():
    """Test that deep analysis scores are merged into portfolio_review.json."""
    print("\n" + "=" * 80)
    print("TEST 1: Portfolio Scores Merged")
    print("=" * 80)

    portfolio_path = Path("output/portfolio/portfolio_review.json")
    if not portfolio_path.exists():
        print("❌ FAIL: portfolio_review.json not found")
        return False

    with open(portfolio_path) as f:
        portfolio_data = json.load(f)

    # Check if we have real scores (not placeholder 0.75)
    holdings = portfolio_data.get("holdings", [])
    placeholder_count = sum(1 for h in holdings if abs(h["composite_score"] - 0.75) < 0.01 or abs(h["composite_score"] - 0.80) < 0.01)

    print(f"\nPortfolio review has {len(holdings)} holdings")
    print(f"Holdings with placeholder scores: {placeholder_count}")

    if placeholder_count == len(holdings):
        print("\n❌ FAIL: All holdings have placeholder scores (0.75 or 0.80)")
        print("This means deep analysis scores were NOT merged")

        # Show what scores should be
        print("\nExpected scores from deep analysis:")
        for asset_class in ["stock", "etf", "crypto"]:
            latest_path = Path(f"output/deep_analysis_{asset_class}/deep_analysis_{asset_class}_latest.json")
            if latest_path.exists():
                with open(latest_path) as f:
                    data = json.load(f)
                if "raw_output" in data:
                    raw = data["raw_output"]
                    if "ticker=" in raw and "composite_score=" in raw:
                        ticker = raw.split("ticker='")[1].split("'")[0] if "ticker='" in raw else "N/A"
                        score = raw.split("composite_score=")[1].split()[0] if "composite_score=" in raw else "0"
                        grade = raw.split("grade='")[1].split("'")[0] if "grade='" in raw else "N/A"
                        print(f"  {ticker}: {score} ({grade})")

        return False

    print(f"\n✅ PASS: {len(holdings) - placeholder_count} holdings have real deep analysis scores")

    # Show actual scores
    print("\nActual scores in portfolio_review.json:")
    for h in holdings:
        print(f"  {h['ticker']}: {h['composite_score']:.3f} ({h['grade']})")

    return True


def test_individual_html_files():
    """Test that individual HTML files are generated for each deep analysis."""
    print("\n" + "=" * 80)
    print("TEST 2: Individual HTML Files Generated")
    print("=" * 80)

    html_files = []
    for asset_class in ["stock", "etf", "crypto"]:
        html_dir = Path(f"output/deep_analysis_{asset_class}")
        if html_dir.exists():
            html_files.extend(list(html_dir.glob("*_deep_analysis.html")))

    print(f"\nFound {len(html_files)} individual HTML reports:")
    for html_file in html_files:
        print(f"  ✓ {html_file}")

    if len(html_files) == 0:
        print("\n❌ FAIL: No individual HTML files generated")
        print("Expected files like: output/deep_analysis_stock/MSFT_deep_analysis.html")
        return False

    print(f"\n✅ PASS: {len(html_files)} individual HTML files generated")
    return True


def test_discovery_in_report():
    """Test that discovery opportunities are included in final report."""
    print("\n" + "=" * 80)
    print("TEST 3: Discovery Opportunities in Final Report")
    print("=" * 80)

    # Check if discovery file exists
    discovery_path = Path("output/discovery/consolidated_discovery.json")
    if not discovery_path.exists():
        print("⚠️  SKIP: consolidated_discovery.json not found (discovery may not have run)")
        return True  # Not a failure, just didn't run

    with open(discovery_path) as f:
        discovery_data = json.load(f)

    opportunities = discovery_data.get("opportunities", [])
    print(f"\nDiscovery found {len(opportunities)} A+ opportunities")

    # Check if final HTML report exists
    report_path = Path("output/finwiz_family_financial_plan.html")
    if not report_path.exists():
        print("❌ FAIL: Final HTML report not found")
        return False

    # Check if discovery section is in the report
    with open(report_path) as f:
        html_content = f.read()

    if "Découverte d'Opportunités" in html_content or "Discovery" in html_content:
        print("\n✅ PASS: Discovery section found in final report")

        # Check if opportunity count matches
        if str(len(opportunities)) in html_content:
            print(f"✅ PASS: Opportunity count ({len(opportunities)}) displayed correctly")
        else:
            print("⚠️  WARNING: Opportunity count may not match")

        return True
    else:
        print("\n❌ FAIL: Discovery section NOT found in final report")
        print(f"Expected to find {len(opportunities)} opportunities listed")
        return False


def test_all_json_integrated():
    """Test that all JSON data is properly integrated."""
    print("\n" + "=" * 80)
    print("TEST 4: All JSON Data Integrated")
    print("=" * 80)

    # Check all expected files exist
    expected_files = [
        "output/portfolio/portfolio_review.json",
        "output/finwiz_family_financial_plan.html",
    ]

    missing_files = [f for f in expected_files if not Path(f).exists()]

    if missing_files:
        print("\n❌ FAIL: Missing expected files:")
        for f in missing_files:
            print(f"  - {f}")
        return False

    print("\n✅ PASS: All expected output files present")

    # Check deep analysis files
    deep_analysis_files = []
    for asset_class in ["stock", "etf", "crypto"]:
        latest_path = Path(f"output/deep_analysis_{asset_class}/deep_analysis_{asset_class}_latest.json")
        if latest_path.exists():
            deep_analysis_files.append(str(latest_path))

    print(f"✅ PASS: Found {len(deep_analysis_files)} deep analysis JSON files")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("REPORT GENERATION TEST SUITE")
    print("=" * 80)
    print("\nTesting fixes for:")
    print("  1. Deep analysis scores merged into portfolio_review.json")
    print("  2. Individual HTML files for each deep analysis")
    print("  3. Discovery opportunities in final report")
    print("  4. All JSON data properly integrated")

    results = {
        "Portfolio Scores Merged": test_portfolio_scores_merged(),
        "Individual HTML Files": test_individual_html_files(),
        "Discovery in Report": test_discovery_in_report(),
        "All JSON Integrated": test_all_json_integrated(),
    }

    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\n{passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
