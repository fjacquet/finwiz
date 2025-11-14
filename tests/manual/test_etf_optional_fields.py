#!/usr/bin/env python3
"""Test ETF scoring with optional tracking_error and AUM fields."""

from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
import json

# Test with CORC.SW (previously failed due to missing tracking_error)
ticker = 'CORC.SW'
asset_class = 'etf'

print(f"Testing {ticker} with optional tracking_error...")
print("=" * 60)

# Get data
tool = QuantitativeAnalysisTool(asset_class=asset_class)
result = tool._run(symbol=ticker, asset_class=asset_class)
data = json.loads(result)

print(f'\nData for {ticker}:')
print(f'  expense_ratio: {data.get("expense_ratio")}')
print(f'  tracking_error: {data.get("tracking_error")}')
print(f'  aum: {data.get("aum")}')
print()

# Try scoring
scorer = DeepAnalysisScorer()
analysis = scorer.calculate_composite_score(ticker, asset_class, data)

print(f'Analysis Result:')
print(f'  Grade: {analysis.grade}')
print(f'  Composite Score: {analysis.composite_score:.2f}')
print(f'  Recommendation: {analysis.recommendation}')
print()
print(f'Rationale:')
print(f'  {analysis.rationale}')
