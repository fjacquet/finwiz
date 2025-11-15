#!/usr/bin/env python3
"""Test ETF expense ratio fallback functionality."""

from finwiz.utils.etf_expense_fallback import (
    get_fallback_expense_ratio,
    has_fallback_data,
    load_expense_ratios,
)

print("Testing ETF Expense Ratio Fallback")
print("=" * 60)

# Test loading
ratios = load_expense_ratios()
print(f"\n✅ Loaded {len(ratios)} ETF expense ratios from config")

# Test specific tickers
test_tickers = ["VUSA.L", "VUAA.DU", "QDV5.DU", "XB0T.DE", "CSYZ.DE", "GREIT.SW", "ZSIL.SW"]

print("\nTesting fallback for problematic ETFs:")
for ticker in test_tickers:
    has_data = has_fallback_data(ticker)
    ratio = get_fallback_expense_ratio(ticker)

    if ratio is not None:
        print(f"  ✅ {ticker}: {ratio:.6f} ({ratio * 100:.2f}%)")
    else:
        print(f"  ❌ {ticker}: No fallback data")

# Test integration with tool
print("\n" + "=" * 60)
print("Testing integration with QuantitativeAnalysisTool:")
print("=" * 60)

import json

from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

tool = QuantitativeAnalysisTool(asset_class="etf")

# Test with a ticker that should use fallback
ticker = "VUSA.L"
print(f"\nTesting {ticker}...")

try:
    result = tool._run(symbol=ticker, asset_class="etf")
    data = json.loads(result)

    expense_ratio = data.get("expense_ratio")
    if expense_ratio is not None:
        print(f"  ✅ Got expense_ratio: {expense_ratio:.6f} ({expense_ratio * 100:.2f}%)")
    else:
        print("  ❌ No expense_ratio in result")

except Exception as e:
    print(f"  ⚠️ Tool execution error: {e}")

print("\n" + "=" * 60)
print("Summary:")
print(f"  - Fallback config has {len(ratios)} ETFs")
print(f"  - {sum(1 for t in test_tickers if has_fallback_data(t))}/{len(test_tickers)} test tickers have fallback data")
print("=" * 60)
