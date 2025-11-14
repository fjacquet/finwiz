#!/usr/bin/env python3
"""
Test to reproduce the ETF scoring bug where CORC.SW gets A+ with terrible metrics.
"""

from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


def test_etf_with_bad_metrics():
    """Test ETF with 20% expense ratio and 30% tracking error."""
    scorer = DeepAnalysisScorer()
    
    # CORC.SW data - as percentages (20.0 = 20%)
    data_as_percentages = {
        "asset_class": "etf",
        "current_price": 100.0,
        "expense_ratio": 20.0,  # 20% - TERRIBLE!
        "tracking_error": 30.0,  # 30% - TERRIBLE!
        "aum": 100e6,  # $100M - small
        "volatility": 0.047,  # 4.7% - good
        "max_drawdown": -0.037,  # -3.7% - good
        "beta": 1.0,
        "rsi": 50.0,
        "macd": 0.0,
        "macd_signal": 0.0,
    }
    
    print("\n" + "="*80)
    print("TEST 1: ETF with expense_ratio=20.0 (as percentage)")
    print("="*80)
    
    try:
        result = scorer.calculate_composite_score("CORC.SW", "etf", data_as_percentages)
        
        print(f"\nResults:")
        print(f"  Fundamental Score: {result.fundamental_score:.3f}")
        print(f"  Technical Score: {result.technical_score:.3f}")
        print(f"  Risk Score: {result.risk_score:.3f}")
        print(f"  Composite Score: {result.composite_score:.3f}")
        print(f"  Grade: {result.grade}")
        print(f"  Recommendation: {result.recommendation}")
        
        print(f"\nFundamental Details:")
        for key, value in result.fundamental_details.items():
            print(f"  {key}: {value}")
        
        # Check if scoring is correct
        if result.fundamental_score > 0.3:
            print(f"\n❌ BUG CONFIRMED: Fundamental score {result.fundamental_score:.3f} is too high!")
            print(f"   Expected: ~0.20 (expense_ratio=20% and tracking_error=30% should get lowest scores)")
        else:
            print(f"\n✅ Scoring is correct: Fundamental score {result.fundamental_score:.3f} reflects bad metrics")
            
        if result.grade in ["A+", "A"]:
            print(f"❌ BUG CONFIRMED: Grade {result.grade} is too high for terrible ETF!")
        else:
            print(f"✅ Grade {result.grade} is appropriate")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test with correct decimal format
    data_as_decimals = data_as_percentages.copy()
    data_as_decimals["expense_ratio"] = 0.20  # 0.20 = 20% as decimal
    data_as_decimals["tracking_error"] = 0.30  # 0.30 = 30% as decimal
    
    print("\n" + "="*80)
    print("TEST 2: ETF with expense_ratio=0.20 (as decimal)")
    print("="*80)
    
    try:
        result2 = scorer.calculate_composite_score("CORC.SW", "etf", data_as_decimals)
        
        print(f"\nResults:")
        print(f"  Fundamental Score: {result2.fundamental_score:.3f}")
        print(f"  Composite Score: {result2.composite_score:.3f}")
        print(f"  Grade: {result2.grade}")
        
        if result2.fundamental_score > 0.3:
            print(f"\n❌ Still too high with decimal format!")
        else:
            print(f"\n✅ Decimal format gives correct low score")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_etf_with_bad_metrics()
