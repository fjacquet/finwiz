#!/usr/bin/env python3
"""
Test tracking error calculation for ETFs.
"""

import yfinance as yf
import pandas as pd


def calculate_tracking_error(etf_symbol: str, benchmark_symbol: str = "SPY"):
    """Calculate tracking error between ETF and benchmark."""
    print(f"\n{'='*80}")
    print(f"Calculating Tracking Error: {etf_symbol} vs {benchmark_symbol}")
    print(f"{'='*80}\n")
    
    try:
        # Fetch data
        etf = yf.Ticker(etf_symbol)
        benchmark = yf.Ticker(benchmark_symbol)
        
        # Get 1 year of historical data
        etf_hist = etf.history(period="1y")
        benchmark_hist = benchmark.history(period="1y")
        
        if etf_hist.empty or benchmark_hist.empty:
            print(f"❌ No historical data available")
            return None
        
        # Calculate daily returns
        etf_returns = etf_hist["Close"].pct_change().dropna()
        benchmark_returns = benchmark_hist["Close"].pct_change().dropna()
        
        print(f"ETF data points: {len(etf_returns)}")
        print(f"Benchmark data points: {len(benchmark_returns)}")
        
        # Align dates
        aligned_etf, aligned_benchmark = etf_returns.align(benchmark_returns, join="inner")
        
        print(f"Aligned data points: {len(aligned_etf)}")
        
        if len(aligned_etf) < 20:
            print(f"❌ Insufficient data for tracking error calculation")
            return None
        
        # Calculate tracking difference
        tracking_diff = aligned_etf - aligned_benchmark
        
        # Annualized tracking error
        tracking_error = tracking_diff.std() * (252 ** 0.5)
        
        print(f"\nResults:")
        print(f"  Tracking Difference Std Dev (daily): {tracking_diff.std():.6f}")
        print(f"  Tracking Error (annualized): {tracking_error:.6f} ({tracking_error*100:.4f}%)")
        
        # Additional stats
        mean_diff = tracking_diff.mean() * 252  # Annualized
        print(f"  Mean Tracking Difference (annualized): {mean_diff:.6f} ({mean_diff*100:.4f}%)")
        
        # Correlation
        correlation = aligned_etf.corr(aligned_benchmark)
        print(f"  Correlation: {correlation:.4f}")
        
        return tracking_error
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    # Test with various ETFs
    test_cases = [
        ("SPY", "SPY", "S&P 500 vs itself (should be ~0)"),
        ("VOO", "SPY", "Vanguard S&P 500 vs SPY (should be very low)"),
        ("QQQ", "SPY", "Nasdaq-100 vs S&P 500 (should be higher)"),
        ("VTI", "SPY", "Total Market vs S&P 500 (should be low)"),
    ]
    
    results = {}
    
    for etf, benchmark, description in test_cases:
        print(f"\n{'='*80}")
        print(f"Test: {description}")
        print(f"{'='*80}")
        
        te = calculate_tracking_error(etf, benchmark)
        results[etf] = te
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for etf, te in results.items():
        if te is not None:
            print(f"{etf:10} Tracking Error: {te:.6f} ({te*100:.4f}%)")
        else:
            print(f"{etf:10} Tracking Error: N/A")
