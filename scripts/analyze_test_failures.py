#!/usr/bin/env python3
"""
Analyze test failures and generate a summary report.

This script runs the test suite, extracts failures, and creates a detailed
breakdown to help prioritize test fixes.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime


def run_tests_and_capture_failures():
    """Run pytest and capture all failures."""
    print("Running test suite to capture failures...")

    cmd = ["uv", "run", "pytest", "tests/unit/", "-v", "--tb=no", "--no-cov"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        print("Test run timed out after 5 minutes")
        return None


def parse_failures(output):
    """Parse pytest output to extract failure information."""
    failures = []

    for line in output.split("\n"):
        if "FAILED" in line:
            # Extract test file and test name
            parts = line.split("::")
            if len(parts) >= 2:
                test_file = parts[0].strip().replace("tests/unit/", "")
                test_class = parts[1] if len(parts) >= 3 else ""
                test_name = parts[-1].split(" ")[0] if len(parts) >= 2 else ""

                failures.append({"file": test_file, "class": test_class, "test": test_name, "full_path": "::".join(parts[:3]) if len(parts) >= 3 else "::".join(parts)})

    return failures


def categorize_failures(failures):
    """Categorize failures by file and create statistics."""
    by_file = defaultdict(list)
    by_category = defaultdict(list)

    for failure in failures:
        by_file[failure["file"]].append(failure)

        # Categorize by top-level directory
        category = failure["file"].split("/")[0] if "/" in failure["file"] else "root"
        by_category[category].append(failure)

    return by_file, by_category


def generate_report(failures, by_file, by_category):
    """Generate a detailed report of test failures."""
    report = []

    report.append("=" * 80)
    report.append("TEST FAILURE ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    report.append("")

    # Summary statistics
    report.append("SUMMARY")
    report.append("-" * 80)
    report.append(f"Total Failures: {len(failures)}")
    report.append(f"Files with Failures: {len(by_file)}")
    report.append(f"Categories: {len(by_category)}")
    report.append("")

    # Failures by category
    report.append("FAILURES BY CATEGORY")
    report.append("-" * 80)
    for category, items in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"{category:30s} {len(items):3d} failures")
    report.append("")

    # Top 20 files with most failures
    report.append("TOP 20 FILES WITH MOST FAILURES")
    report.append("-" * 80)
    sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    for file, items in sorted_files:
        report.append(f"{len(items):3d} failures - {file}")
    report.append("")

    # Detailed breakdown by file
    report.append("DETAILED BREAKDOWN BY FILE")
    report.append("-" * 80)
    for file, items in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"\n{file} ({len(items)} failures):")
        for item in items:
            test_name = item["test"]
            if len(test_name) > 70:
                test_name = test_name[:67] + "..."
            report.append(f"  - {test_name}")

    return "\n".join(report)


def save_report(report, output_file="TEST_FAILURES.txt"):
    """Save report to file."""
    with open(output_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {output_file}")


def save_json_data(failures, by_file, by_category, output_file="test_failures.json"):
    """Save structured data as JSON for programmatic access."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "total_failures": len(failures),
        "failures": failures,
        "by_file": {k: len(v) for k, v in by_file.items()},
        "by_category": {k: len(v) for k, v in by_category.items()},
    }

    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"JSON data saved to: {output_file}")


def main():
    """Main execution function."""
    print("Test Failure Analysis Tool")
    print("=" * 80)

    # Run tests and capture output
    output = run_tests_and_capture_failures()
    if not output:
        print("Failed to capture test output")
        sys.exit(1)

    # Parse failures
    failures = parse_failures(output)

    if not failures:
        print("\n🎉 No test failures found! All tests passing!")
        sys.exit(0)

    # Categorize failures
    by_file, by_category = categorize_failures(failures)

    # Generate and save report
    report = generate_report(failures, by_file, by_category)
    print("\n" + report)

    save_report(report)
    save_json_data(failures, by_file, by_category)

    print("\n" + "=" * 80)
    print(f"Analysis complete: {len(failures)} failures found")
    print("=" * 80)


if __name__ == "__main__":
    main()
