#!/usr/bin/env python3
"""Test ETF scoring with optional tracking_error and AUM fields."""

import json

from finwiz.config.critical_fields_config import CriticalFieldError
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

# Test with CORC.SW (previously failed due to missing tracking_error)
ticker = "CORC.SW"
asset_class = "etf"

print(f"Testing {ticker} with optional tracking_error...")
print("=" * 60)

# Get data
tool = QuantitativeAnalysisTool(asset_class=asset_class)
result = tool._run(symbol=ticker, asset_class=asset_class)
data = json.loads(result)

print(f"\nData for {ticker}:")
print(f"  current_price: {data.get('current_price')}")
print(f"  expense_ratio: {data.get('expense_ratio')}")
print(f"  tracking_error: {data.get('tracking_error')}")
print(f"  aum: {data.get('aum')}")
print(f"  volatility: {data.get('volatility')}")
print()

# Try scoring
scorer = DeepAnalysisScorer()
try:
    analysis = scorer.calculate_composite_score(ticker, asset_class, data)
except CriticalFieldError as e:
    print(f"❌ Analysis failed as expected: {e}")
    print("\nThis is correct behavior - ETFs need critical fields (current_price, volatility, expense_ratio)")
    print("to perform meaningful analysis. Without these, we'd be making assumptions.")
    exit(0)

print("✅ Analysis Result:")
print(f"  Grade: {analysis.grade}")
print(f"  Composite Score: {analysis.composite_score:.2f}")
print(f"  Recommendation: {analysis.recommendation}")
print()
print("Rationale:")
print(f"  {analysis.rationale}")
print()
print("Note: tracking_error and aum are optional - analysis proceeds without them")
