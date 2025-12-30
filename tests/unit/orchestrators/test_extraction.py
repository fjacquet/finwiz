#!/usr/bin/env python3
"""
Test the data extraction to see what fields are actually available.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set minimal environment variables
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")
os.environ["SERPER_API_KEY"] = os.environ.get("SERPER_API_KEY", "test-key")
os.environ["DEEP_ANALYSIS_BATCH_SIZE"] = "1"

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator


def test_extraction():
    """Test the extraction with a simple example."""
    # Create orchestrator with mock state
    state = FinwizState()
    orchestrator = DeepAnalysisOrchestrator(state)

    # Create a mock crew output with the expected structure
    # This simulates what the agent should be outputting
    mock_raw_output = """
    context["collected_data"] = {
        "ticker": "AAPL",
        "asset_class": "stock",
        "collection_timestamp": "2025-01-01T10:00:00Z",
        "ticker_validation": {
            "valid": true,
            "ticker": "AAPL",
            "company_name": "Apple Inc."
        },
        "quantitative_analysis": {
            "prices": {
                "current_price": 185.50,
                "day_change": 2.35,
                "day_change_percent": 1.28
            },
            "fundamentals": {
                "roe": 0.45,
                "debt_to_equity": 0.65,
                "revenue_growth": 0.12,
                "profit_margin": 0.25
            },
            "risk_metrics": {
                "volatility": 0.22,
                "beta": 1.15,
                "max_drawdown": 0.18
            },
            "technical_indicators": {
                "rsi": 55,
                "macd": 2.5
            }
        },
        "sentiment_analysis": {
            "sentiment_score": 0.75,
            "article_count": 25
        }
    }
    """

    # Create a mock TaskOutput
    class MockTaskOutput:
        def __init__(self):
            self.raw = mock_raw_output
            self.output = None

    # Create a mock CrewOutput
    class MockCrewOutput:
        def __init__(self):
            self.tasks_output = [MockTaskOutput(), MockTaskOutput()]
            self.pydantic = None

    # Test extraction (method moved to result_processor in Phase 1.1 refactoring)
    crew_output = MockCrewOutput()
    extracted = orchestrator.result_processor.extract_collected_data(crew_output)

    print("\n✅ EXTRACTION TEST RESULTS:")
    print(f"Extracted {len(extracted) if extracted else 0} fields")

    if extracted:
        print("\n📋 Available fields:")
        for key in sorted(extracted.keys()):
            value = extracted[key]
            print(f"  - {key}: {value} ({type(value).__name__})")

        # Check for critical fields
        critical_stock = ["current_price", "roe", "debt_to_equity", "revenue_growth", "volatility", "beta"]
        print("\n🔍 Critical fields check:")
        for field in critical_stock:
            if field in extracted:
                print(f"  ✅ {field}: {extracted[field]}")
            else:
                print(f"  ❌ {field}: MISSING")
    else:
        print("❌ Extraction failed - no data returned")


if __name__ == "__main__":
    test_extraction()
