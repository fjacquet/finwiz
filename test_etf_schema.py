#!/usr/bin/env python3
"""Test ETF schema to ensure union types work with CrewAI."""

from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
from datetime import date

def test_etf_schema():
    """Test that ETF schemas work without union type errors."""
    
    # Test ETFTopHolding
    holding = ETFTopHolding(
        ticker="AAPL",
        weight_pct=5.2,
        source_url="https://example.com/holdings",
        as_of=date.today()
    )
    print(f"✅ ETFTopHolding created: {holding.ticker} - {holding.weight_pct}%")
    
    # Test ETFFactsheet with optional fields
    factsheet = ETFFactsheet(
        ticker="VTI",
        issuer="Vanguard",
        expense_ratio=0.03,
        tracking_diff=None,  # Test optional field
        factsheet_url="https://example.com/factsheet",
        as_of=date.today(),
        risk=None  # Test optional field
    )
    print(f"✅ ETFFactsheet created: {factsheet.ticker} - {factsheet.expense_ratio}%")
    
    # Test with tracking_diff set
    factsheet_with_tracking = ETFFactsheet(
        ticker="SPY",
        issuer="State Street",
        expense_ratio=0.09,
        tracking_diff=0.02,  # Test optional field with value
        factsheet_url="https://example.com/spy",
        as_of=date.today()
    )
    print(f"✅ ETFFactsheet with tracking_diff: {factsheet_with_tracking.ticker} - {factsheet_with_tracking.tracking_diff}%")
    
    print("🎉 All ETF schema tests passed!")

if __name__ == "__main__":
    test_etf_schema()