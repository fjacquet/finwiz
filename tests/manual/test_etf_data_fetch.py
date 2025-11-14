#!/usr/bin/env python3
"""
Test script to verify ETF data fetching from Yahoo Finance.
"""

import yfinance as yf


def test_etf_data(ticker: str = "SPY"):
    """Test fetching ETF-specific data from Yahoo Finance."""
    print(f"\n{'='*80}")
    print(f"Testing ETF data fetch for {ticker}")
    print(f"{'='*80}\n")
    
    try:
        # Fetch ticker data
        etf = yf.Ticker(ticker)
        info = etf.info
        
        # Check for ETF-specific fields
        print("ETF-Specific Fields:")
        print("-" * 80)
        
        # Expense Ratio
        expense_ratio = info.get("annualReportExpenseRatio")
        if expense_ratio is not None:
            print(f"✅ Expense Ratio: {expense_ratio} ({expense_ratio * 100:.2f}%)")
        else:
            print(f"❌ Expense Ratio: NOT AVAILABLE")
        
        # Total Assets (AUM)
        total_assets = info.get("totalAssets")
        if total_assets is not None:
            print(f"✅ Total Assets (AUM): ${total_assets:,.0f} (${total_assets / 1e9:.2f}B)")
        else:
            print(f"❌ Total Assets (AUM): NOT AVAILABLE")
        
        # Other useful fields
        print(f"\nOther Fields:")
        print("-" * 80)
        
        fields_to_check = [
            ("category", "Category"),
            ("fundFamily", "Fund Family"),
            ("fundInceptionDate", "Inception Date"),
            ("ytdReturn", "YTD Return"),
            ("threeYearAverageReturn", "3-Year Avg Return"),
            ("fiveYearAverageReturn", "5-Year Avg Return"),
            ("beta3Year", "3-Year Beta"),
            ("yield", "Yield"),
        ]
        
        for key, label in fields_to_check:
            value = info.get(key)
            if value is not None:
                print(f"  {label}: {value}")
        
        # Check if we can calculate tracking error
        print(f"\nTracking Error Calculation:")
        print("-" * 80)
        
        # Get historical data
        hist = etf.history(period="1y")
        if not hist.empty:
            returns = hist["Close"].pct_change().dropna()
            volatility = returns.std() * (252 ** 0.5)  # Annualized
            print(f"✅ Historical data available: {len(hist)} days")
            print(f"  Volatility (annualized): {volatility:.2%}")
            print(f"  Note: Tracking error requires benchmark data")
        else:
            print(f"❌ No historical data available")
        
        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY:")
        print("-" * 80)
        
        has_expense_ratio = expense_ratio is not None
        has_aum = total_assets is not None
        
        if has_expense_ratio and has_aum:
            print(f"✅ {ticker} has all required ETF data")
            print(f"   Expense Ratio: {expense_ratio * 100:.2f}%")
            print(f"   AUM: ${total_assets / 1e9:.2f}B")
        else:
            print(f"⚠️ {ticker} is missing some ETF data:")
            if not has_expense_ratio:
                print(f"   ❌ Expense Ratio missing")
            if not has_aum:
                print(f"   ❌ AUM missing")
        
        print(f"⚠️ Tracking error calculation not yet implemented")
        
    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")


if __name__ == "__main__":
    import sys
    
    # Test with SPY by default
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    test_etf_data(ticker)
    
    # Test with a few more ETFs
    print("\n" + "="*80)
    print("Testing additional ETFs...")
    print("="*80)
    
    for test_ticker in ["QQQ", "VTI", "CORC.SW"]:
        test_etf_data(test_ticker)
