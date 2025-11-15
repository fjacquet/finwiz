#!/usr/bin/env python3
"""
Test script to verify what financial data Yahoo Finance actually provides.

This script checks if Yahoo Finance provides the critical fields we need:
- ROE (Return on Equity)
- Debt to Equity ratio
- Revenue Growth
- Other fundamental metrics
"""

import yfinance as yf


def test_yahoo_finance_data(ticker: str = "AAPL"):
    """Test what data Yahoo Finance provides for a given ticker."""
    print(f"\n{'=' * 80}")
    print(f"Testing Yahoo Finance data for {ticker}")
    print(f"{'=' * 80}\n")

    try:
        # Fetch ticker data
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        # Critical fields we need
        critical_fields = {
            "returnOnEquity": "ROE (Return on Equity)",
            "debtToEquity": "Debt to Equity Ratio",
            "revenueGrowth": "Revenue Growth",
            "profitMargins": "Profit Margin",
            "currentPrice": "Current Price",
            "regularMarketPrice": "Regular Market Price",
        }

        print("CRITICAL FIELDS CHECK:")
        print("-" * 80)

        available_fields = []
        missing_fields = []

        for field_key, field_name in critical_fields.items():
            value = info.get(field_key)
            if value is not None:
                available_fields.append(field_key)
                print(f"✅ {field_name:30} ({field_key:20}): {value}")
            else:
                missing_fields.append(field_key)
                print(f"❌ {field_name:30} ({field_key:20}): NOT AVAILABLE")

        # Additional useful fields
        print(f"\n{'=' * 80}")
        print("ADDITIONAL FINANCIAL METRICS:")
        print("-" * 80)

        additional_fields = {
            "totalRevenue": "Total Revenue",
            "ebitda": "EBITDA",
            "earningsGrowth": "Earnings Growth",
            "marketCap": "Market Cap",
            "trailingPE": "P/E Ratio (Trailing)",
            "forwardPE": "P/E Ratio (Forward)",
            "priceToBook": "Price to Book",
            "beta": "Beta",
            "fiftyTwoWeekHigh": "52 Week High",
            "fiftyTwoWeekLow": "52 Week Low",
            "averageVolume": "Average Volume",
            "dividendYield": "Dividend Yield",
        }

        for field_key, field_name in additional_fields.items():
            value = info.get(field_key)
            if value is not None:
                print(f"  {field_name:30} ({field_key:20}): {value}")
            else:
                print(f"  {field_name:30} ({field_key:20}): N/A")

        # Summary
        print(f"\n{'=' * 80}")
        print("SUMMARY:")
        print("-" * 80)
        print(f"✅ Available critical fields: {len(available_fields)}/{len(critical_fields)}")
        print(f"❌ Missing critical fields: {len(missing_fields)}/{len(critical_fields)}")

        if missing_fields:
            print(f"\nMissing fields: {', '.join(missing_fields)}")
            print("\n⚠️  WARNING: Some critical fields are not available from Yahoo Finance!")
            print("   Consider using alternative data sources or marking these as optional.")
        else:
            print("\n✅ All critical fields are available from Yahoo Finance!")

        # Show all available keys for reference
        print(f"\n{'=' * 80}")
        print(f"ALL AVAILABLE KEYS ({len(info)} total):")
        print("-" * 80)
        for i, key in enumerate(sorted(info.keys()), 1):
            print(f"{i:3}. {key}")

    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")


if __name__ == "__main__":
    import sys

    # Test with AAPL by default, or use command line argument
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    test_yahoo_finance_data(ticker)

    # Test with a few more tickers
    print("\n" + "=" * 80)
    print("Testing additional tickers...")
    print("=" * 80)

    for test_ticker in ["MSFT", "GOOGL", "SPY"]:
        test_yahoo_finance_data(test_ticker)
