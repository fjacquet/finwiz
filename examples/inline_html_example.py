#!/usr/bin/env python3
"""
Example of inline HTML generation with FinWiz reports.

This demonstrates how to automatically generate HTML reports
when creating JSON files.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.utils.html_generator import (
    JSONWriter,
    auto_html,
    disable_html_generation,
    enable_html_generation,
    save_backtesting_results,
    save_json_with_html,
)


def example_1_direct_save():
    """Example 1: Direct save with automatic HTML generation."""
    print("📊 Example 1: Direct Save with HTML Generation")

    # Sample backtesting data
    backtesting_data = {
        "candidates": [
            {
                "ticker": "AAPL",
                "grade": "A+",
                "composite_score": 0.95,
                "asset_class": "stock",
                "recommendation": "BUY",
                "analysis_file": "output/stock/AAPL_analysis.json",
            },
            {
                "ticker": "GOOGL",
                "grade": "A",
                "composite_score": 0.88,
                "asset_class": "stock",
                "recommendation": "BUY",
                "analysis_file": "output/stock/GOOGL_analysis.json",
            },
        ]
    }

    # Save with automatic HTML generation
    json_path, html_path = save_backtesting_results(backtesting_data, "output/examples/backtesting_results_example.json")

    print(f"✅ JSON saved: {json_path}")
    if html_path:
        print(f"✅ HTML generated: {html_path}")
    print()


def example_2_context_manager():
    """Example 2: Using JSONWriter context manager."""
    print("📊 Example 2: JSONWriter Context Manager")

    # Using context manager for portfolio review
    with JSONWriter("output/examples/portfolio_review_example.json", "portfolio_review") as writer:
        portfolio_data = {
            "as_of": datetime.now().isoformat(),
            "base_currency": "USD",
            "holdings": [
                {
                    "asset_class": "stock",
                    "name": "Apple Inc.",
                    "ticker": "AAPL",
                    "currency": "USD",
                    "decision": "KEEP",
                    "composite_score": 0.95,
                    "grade": "A+",
                    "grade_description": "Excellent - Top tier investment",
                    "recommended_action": "KEEP - Outstanding performer",
                    "risk": {
                        "scale": "0_5",
                        "score": 1.2,
                        "level": "Low",
                        "risk_factors": ["Market volatility", "Tech sector exposure"],
                    },
                    "rationale_bullets": [
                        "💎 Exceptional financial performance",
                        "🚀 Strong market position and brand loyalty",
                        "📈 Consistent revenue and profit growth",
                        "💰 Strong balance sheet and cash position",
                    ],
                    "citations": ["Yahoo Finance", "SEC 10-K Filing"],
                    "alternatives": [],
                    "crew_analysis_used": "deep_analysis",
                }
            ],
        }

        writer.write(portfolio_data)

    print()


@auto_html("a_plus_discovery")
def save_discovery_report(output_path: str):
    """Example 3: Using decorator for automatic HTML generation."""
    print("📊 Example 3: Auto-HTML Decorator")

    discovery_data = {
        "discovery_id": "Example-2025-10-27-001",
        "generated_at": datetime.now().isoformat(),
        "asset_type": "stock",
        "grade": "A+",
        "discovery_criteria": {
            "stock_min_roe": 20,
            "stock_min_revenue_growth": 15,
            "stock_max_debt_to_equity": 0.3,
            "stock_min_market_cap": 1000000000,
        },
        "candidates": [
            {
                "ticker": "MSFT",
                "company_name": "Microsoft Corporation",
                "asset_type": "stock",
                "grade": "A+",
                "rationale": "Microsoft demonstrates exceptional financial metrics with high ROE, consistent revenue growth, and strong market position in cloud computing and enterprise software.",
                "criteria_used": {
                    "stock_min_roe": 25.5,
                    "stock_min_revenue_growth": 18.2,
                    "stock_max_debt_to_equity": 0.15,
                    "stock_min_market_cap": 2800000000000,
                },
            }
        ],
    }

    # Save JSON file
    json_path = Path(output_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    import json

    with open(json_path, "w") as f:
        json.dump(discovery_data, f, indent=2, default=str)

    return json_path


def example_4_generic_save():
    """Example 4: Generic save with template type detection."""
    print("📊 Example 4: Generic Save with Auto-Detection")

    validation_data = {
        "validation_status": "PASSED",
        "total_checks": 25,
        "passed_checks": 23,
        "failed_checks": 2,
        "validation_results": [
            {
                "check_name": "Schema Validation",
                "category": "Data Quality",
                "status": "PASSED",
                "severity": "High",
                "message": "All required fields present and valid",
            },
            {
                "check_name": "Data Freshness",
                "category": "Timeliness",
                "status": "FAILED",
                "severity": "Medium",
                "message": "Some data is older than 24 hours",
            },
        ],
    }

    # Generic save - template type auto-detected from filename
    json_path, html_path = save_json_with_html(validation_data, "output/examples/validation_report_example.json")

    print(f"✅ JSON saved: {json_path}")
    if html_path:
        print(f"✅ HTML generated: {html_path}")
    print()


def example_5_toggle_generation():
    """Example 5: Enabling/disabling HTML generation."""
    print("📊 Example 5: Toggle HTML Generation")

    sample_data = {"test": "data", "timestamp": datetime.now().isoformat()}

    # Disable HTML generation
    disable_html_generation()
    json_path, html_path = save_json_with_html(sample_data, "output/examples/no_html.json")
    print(f"JSON only: {json_path}, HTML: {html_path}")

    # Re-enable HTML generation
    enable_html_generation()
    json_path, html_path = save_json_with_html(sample_data, "output/examples/with_html.json")
    print(f"JSON + HTML: {json_path}, HTML: {html_path}")
    print()


def main():
    """Run all examples."""
    print("🚀 FinWiz Inline HTML Generation Examples\n")

    # Ensure HTML generation is enabled
    enable_html_generation()

    # Run examples
    example_1_direct_save()
    example_2_context_manager()
    save_discovery_report("output/examples/a_plus_discovery_example.json")
    print()
    example_4_generic_save()
    example_5_toggle_generation()

    print("✅ All examples completed!")
    print("\n📁 Check the output/examples/ directory for generated files")
    print("🌐 Open the .html files in your browser to see the reports")


if __name__ == "__main__":
    main()
