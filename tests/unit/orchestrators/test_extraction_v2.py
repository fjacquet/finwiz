#!/usr/bin/env python3
"""
Test extraction with the ACTUAL agent output structure.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set minimal environment variables
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")
os.environ["SERPER_API_KEY"] = os.environ.get("SERPER_API_KEY", "test-key")

from finwiz.flow_state import FinwizState
from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator


def test_extraction_actual():
    """Test with the actual output structure from the agent."""
    # Create orchestrator with mock state
    state = FinwizState()
    orchestrator = DeepAnalysisOrchestrator(state)

    # This is the ACTUAL raw output from task 1 (data_collection_task)
    mock_raw_output = """{"ticker":"AAPL","asset_class":"stock","collection_timestamp":"2025-11-19T00:00:00Z","ticker_validation":{"symbol":"AAPL","asset_class":"stock","valid":true,"reason":null,"meta":{},"quantitative_analysis":{"symbol":"AAPL","analysis_type":"comprehensive","timeframe":"1y","data":{"sma_short":150.0,"sma_long":145.0,"performance":{"1m":5.5,"3m":15.2,"6m":25.0,"1y":30.1},"buy_signals":3,"sell_signals":1}},"sentiment_analysis":{"symbol":"AAPL","sentiment_score":0.75,"articles":[{"title":"Apple's New Product Launch: What to Expect","source":"TechCrunch","date":"2025-10-15"}],"trending_topics":["AI Integration","Product Launch","Market Expansion"]},"sec_analysis":{"ticker":"AAPL","form_type":"10-K","sections":{"Item 1":"Business Description","Item 1A":"Risk Factors","Item 7":"Financial Information"},"risk_assessment":{"overall":"low","details":{"business_risk":"stable","financial_risk":"minimal"}}}}}"""

    # Create a mock TaskOutput
    class MockTaskOutput:
        def __init__(self, raw_data):
            self.raw = raw_data
            self.output = None

    # Create a mock CrewOutput
    class MockCrewOutput:
        def __init__(self):
            # Task 1: data collection (has the wrong structure)
            # Task 2: python scoring (has detailed_analysis with the data we need)
            task1_raw = mock_raw_output
            task2_raw = """{"crew_name":"DeepAnalysisCrew","ticker":"AAPL","asset_class":"stock","session_id":"2025-11-19T00:00:00Z","analysis_date":"2025-11-19T00:00:00Z","detailed_analysis":{"roe":0.12,"debt_to_equity":0.5,"revenue_growth":0.07,"profit_margin":0.21,"volatility":0.2,"beta":1.1,"rsi":65.0,"macd":0.05},"risk_assessment":{"scale":"1-5","score":4.0,"level":"low","risk_factors":["market volatility","competitive pressure"]},"composite_score":0.87,"grade":"A","recommendation":"BUY","confidence":0.9,"rationale":"The company's strong financials..."}"""

            self.tasks_output = [MockTaskOutput(task1_raw), MockTaskOutput(task2_raw)]
            self.pydantic = None

    # Test extraction from task 1
    crew_output = MockCrewOutput()
    extracted = orchestrator._extract_collected_data(crew_output)

    print("\n✅ EXTRACTION TEST RESULTS (ACTUAL STRUCTURE):")
    print(f"Extracted {len(extracted) if extracted else 0} fields from Task 1")

    if extracted:
        print("\n📋 Available fields from Task 1:")
        for key in sorted(extracted.keys()):
            value = extracted[key]
            if not isinstance(value, (dict, list)):
                print(f"  - {key}: {value} ({type(value).__name__})")

        # Check for critical fields
        critical_stock = ["current_price", "roe", "debt_to_equity", "revenue_growth", "volatility", "beta"]
        print("\n🔍 Critical fields check:")
        for field in critical_stock:
            if field in extracted:
                print(f"  ✅ {field}: {extracted[field]}")
            else:
                print(f"  ❌ {field}: MISSING")

        print("\n💡 INSIGHT: Task 1 doesn't collect the right metrics!")
        print("   - It collects: sma_short, sma_long, performance, buy_signals")
        print("   - But we need: current_price, roe, debt_to_equity, revenue_growth, volatility, beta")
        print("\n   The agent needs to be instructed to collect different metrics!")

    else:
        print("❌ Extraction failed - no data returned")

    # Now let's try extracting from Task 2 instead
    print("\n" + "=" * 60)
    print("TRYING TASK 2 OUTPUT:")

    # Modify to extract from task 2
    import json

    task2_data = json.loads(crew_output.tasks_output[1].raw)
    if "detailed_analysis" in task2_data:
        print("\n✅ Found detailed_analysis in Task 2!")
        print("\n📋 Available fields from Task 2 detailed_analysis:")
        for key, value in task2_data["detailed_analysis"].items():
            print(f"  - {key}: {value}")

        print("\n⚠️ PROBLEM: Task 2 is making up its own data instead of calling the Python scorer!")
        print("   The agent should extract data from Task 1 and pass it to the DeepAnalysisScorer tool.")
        print("   Instead, it's generating its own scores without using the tool.")


if __name__ == "__main__":
    test_extraction_actual()
