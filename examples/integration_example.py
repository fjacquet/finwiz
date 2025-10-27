#!/usr/bin/env python3
"""
Example showing how to integrate inline HTML generation into existing FinWiz code.

This demonstrates the before/after of adding HTML generation to existing functions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================================================
# BEFORE: Original FinWiz code (JSON only)
# ============================================================================


def save_portfolio_analysis_old(portfolio_data, output_path):
    """Original function - saves JSON only."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(portfolio_data, f, indent=2, default=str)

    print(f"📄 Portfolio analysis saved: {output_path}")
    return output_path


def save_backtesting_results_old(results_data, output_path):
    """Original function - saves JSON only."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results_data, f, indent=2, default=str)

    print(f"📊 Backtesting results saved: {output_path}")
    return output_path


# ============================================================================
# AFTER: Updated FinWiz code (JSON + HTML)
# ============================================================================

from finwiz.utils.html_generator import JSONWriter, auto_html, save_backtesting_results, save_portfolio_review


def save_portfolio_analysis_new(portfolio_data, output_path):
    """Updated function - saves JSON + HTML automatically."""
    json_path, html_path = save_portfolio_review(portfolio_data, output_path)

    print(f"📄 Portfolio analysis saved: {json_path}")
    if html_path:
        print(f"🌐 HTML report generated: {html_path}")

    return json_path


def save_backtesting_results_new(results_data, output_path):
    """Updated function - saves JSON + HTML automatically."""
    json_path, html_path = save_backtesting_results(results_data, output_path)

    print(f"📊 Backtesting results saved: {json_path}")
    if html_path:
        print(f"🌐 HTML report generated: {html_path}")

    return json_path


@auto_html("portfolio_review")
def save_portfolio_analysis_decorator(portfolio_data, output_path):
    """Alternative approach using decorator."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(portfolio_data, f, indent=2, default=str)

    print(f"📄 Portfolio analysis saved: {output_path}")
    return output_path  # HTML generated automatically by decorator


def save_portfolio_analysis_context_manager(portfolio_data, output_path):
    """Alternative approach using context manager."""
    with JSONWriter(output_path, "portfolio_review") as writer:
        writer.write(portfolio_data)

    print("📄 Portfolio analysis saved with HTML")


# ============================================================================
# CrewAI Flow Integration Example
# ============================================================================


class ExampleFlow:
    """Example showing Flow integration."""

    def save_analysis_results_old(self, analysis_data):
        """Original Flow method - JSON only."""
        portfolio_data = self._format_portfolio_data(analysis_data)

        output_path = f"output/portfolio/portfolio_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, "w") as f:
            json.dump(portfolio_data, f, indent=2, default=str)

        return {"portfolio_saved": True, "path": output_path}

    def save_analysis_results_new(self, analysis_data):
        """Updated Flow method - JSON + HTML."""
        portfolio_data = self._format_portfolio_data(analysis_data)

        output_path = f"output/portfolio/portfolio_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        json_path, html_path = save_portfolio_review(portfolio_data, output_path)

        return {"portfolio_saved": True, "json_path": str(json_path), "html_path": str(html_path) if html_path else None}

    def _format_portfolio_data(self, analysis_data):
        """Helper method to format data."""
        return {"as_of": datetime.now().isoformat(), "base_currency": "USD", "holdings": analysis_data.get("holdings", [])}


# ============================================================================
# Demo Functions
# ============================================================================


def create_sample_portfolio_data():
    """Create sample portfolio data for testing."""
    return {
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
                ],
                "citations": ["Yahoo Finance", "SEC 10-K Filing"],
                "alternatives": [],
                "crew_analysis_used": "deep_analysis",
            },
            {
                "asset_class": "stock",
                "name": "Microsoft Corporation",
                "ticker": "MSFT",
                "currency": "USD",
                "decision": "KEEP",
                "composite_score": 0.88,
                "grade": "A",
                "grade_description": "Very Good - Strong investment",
                "recommended_action": "KEEP - Solid performer",
                "risk": {
                    "scale": "0_5",
                    "score": 1.5,
                    "level": "Low",
                    "risk_factors": ["Market volatility", "Competition in cloud services"],
                },
                "rationale_bullets": [
                    "☁️ Leading position in cloud computing",
                    "💼 Strong enterprise software portfolio",
                    "📊 Consistent financial performance",
                ],
                "citations": ["Yahoo Finance", "Company Reports"],
                "alternatives": [],
                "crew_analysis_used": "deep_analysis",
            },
        ],
    }


def create_sample_backtesting_data():
    """Create sample backtesting data for testing."""
    return {
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
                "ticker": "MSFT",
                "grade": "A",
                "composite_score": 0.88,
                "asset_class": "stock",
                "recommendation": "BUY",
                "analysis_file": "output/stock/MSFT_analysis.json",
            },
            {
                "ticker": "GOOGL",
                "grade": "A",
                "composite_score": 0.85,
                "asset_class": "stock",
                "recommendation": "BUY",
                "analysis_file": "output/stock/GOOGL_analysis.json",
            },
        ]
    }


def demo_before_after():
    """Demonstrate before/after comparison."""
    print("🔄 Before/After Integration Demo\n")

    portfolio_data = create_sample_portfolio_data()
    backtesting_data = create_sample_backtesting_data()

    print("📊 BEFORE (JSON only):")
    print("=" * 50)

    # Old way - JSON only
    save_portfolio_analysis_old(portfolio_data, "output/integration/portfolio_old.json")
    save_backtesting_results_old(backtesting_data, "output/integration/backtesting_old.json")

    print("\n📊 AFTER (JSON + HTML):")
    print("=" * 50)

    # New way - JSON + HTML
    save_portfolio_analysis_new(portfolio_data, "output/integration/portfolio_new.json")
    save_backtesting_results_new(backtesting_data, "output/integration/backtesting_new.json")

    print("\n📊 ALTERNATIVE APPROACHES:")
    print("=" * 50)

    # Decorator approach
    print("Using @auto_html decorator:")
    save_portfolio_analysis_decorator(portfolio_data, "output/integration/portfolio_decorator.json")

    # Context manager approach
    print("Using JSONWriter context manager:")
    save_portfolio_analysis_context_manager(portfolio_data, "output/integration/portfolio_context.json")


def demo_flow_integration():
    """Demonstrate Flow integration."""
    print("\n🌊 CrewAI Flow Integration Demo\n")

    flow = ExampleFlow()
    analysis_data = {"holdings": create_sample_portfolio_data()["holdings"]}

    print("📊 OLD Flow method (JSON only):")
    result_old = flow.save_analysis_results_old(analysis_data)
    print(f"Result: {result_old}")

    print("\n📊 NEW Flow method (JSON + HTML):")
    result_new = flow.save_analysis_results_new(analysis_data)
    print(f"Result: {result_new}")


def main():
    """Run integration examples."""
    print("🚀 FinWiz HTML Integration Examples\n")

    demo_before_after()
    demo_flow_integration()

    print("\n✅ Integration examples completed!")
    print("\n📁 Check the output/integration/ directory for generated files")
    print("🌐 Open the .html files in your browser to see the reports")

    print("\n📖 Migration Steps:")
    print("1. Import HTML generator functions")
    print("2. Replace json.dump() calls with save_*() functions")
    print("3. Update return values to handle both JSON and HTML paths")
    print("4. Test that both JSON and HTML are generated correctly")


if __name__ == "__main__":
    main()
