#!/usr/bin/env python3
"""
Test script to verify the hallucination fix works correctly.

This script tests that:
1. Report crew fails when insufficient tickers are provided
2. Report crew extracts validated tickers correctly
3. Report crew detects hallucinated tickers in output
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from finwiz.crews.report_crew.report_crew import ReportCrew


def test_extract_validated_tickers():
    """Test that _extract_validated_tickers works correctly."""
    print("\n=== Test 1: Extract Validated Tickers ===")
    
    crew = ReportCrew()
    
    # Test with valid data
    context = {
        "stock_analysis_data": {
            "tasks_output": [
                {"pydantic": {"ticker": "AAPL"}},
                {"pydantic": {"ticker": "MSFT"}},
                {"pydantic": {}},  # No ticker
            ]
        },
        "etf_analysis_data": {
            "tasks_output": [
                {"pydantic": {"ticker": "VOO"}},
            ]
        },
        "crypto_analysis_data": {
            "tasks_output": [
                {"pydantic": {"symbol": "BTC"}},
            ]
        },
    }
    
    tickers = crew._extract_validated_tickers(context)
    print(f"Extracted tickers: {tickers}")
    
    expected = ["AAPL", "BTC", "MSFT", "VOO"]
    assert tickers == expected, f"Expected {expected}, got {tickers}"
    print("✓ Test passed: Correctly extracted validated tickers")


def test_insufficient_tickers():
    """Test that prepare_crew_context fails with insufficient tickers."""
    print("\n=== Test 2: Insufficient Tickers ===")
    
    crew = ReportCrew()
    
    # Mock context with only 1 ticker
    context_with_one_ticker = {
        "stock_analysis_data": {
            "tasks_output": [
                {"pydantic": {"ticker": "AAPL"}},
            ]
        },
        "etf_analysis_data": {"tasks_output": []},
        "crypto_analysis_data": {"tasks_output": []},
    }
    
    # This should raise ValueError
    try:
        # We need to mock get_integrated_data_context
        original_method = crew.get_integrated_data_context
        crew.get_integrated_data_context = lambda max_age_hours: context_with_one_ticker
        
        result = crew.prepare_crew_context(max_age_hours=24)
        
        # Check if it returned an error context instead of raising
        if result.get("error") and "Insufficient validated tickers" in result.get("error", ""):
            print(f"✓ Test passed: Correctly rejected insufficient tickers (via error context)")
            print(f"  Error message: {result['error']}")
        else:
            print("✗ Test failed: Should have raised ValueError or returned error for insufficient tickers")
            sys.exit(1)
    except ValueError as e:
        if "Insufficient validated tickers" in str(e):
            print(f"✓ Test passed: Correctly rejected insufficient tickers (via exception)")
            print(f"  Error message: {e}")
        else:
            print(f"✗ Test failed: Wrong error message: {e}")
            sys.exit(1)
    finally:
        crew.get_integrated_data_context = original_method


def test_hallucination_detection():
    """Test that _validate_task_output detects hallucinated tickers."""
    print("\n=== Test 3: Hallucination Detection ===")
    
    crew = ReportCrew()
    
    validated_tickers = ["AAPL", "MSFT", "VOO"]
    
    # Test 1: Valid output (should pass)
    valid_output = "We recommend investing in AAPL and MSFT for growth."
    try:
        crew._validate_task_output(valid_output, validated_tickers)
        print("✓ Test passed: Valid output accepted")
    except ValueError as e:
        print(f"✗ Test failed: Valid output rejected: {e}")
        sys.exit(1)
    
    # Test 2: Hallucinated ticker ABC (should fail)
    hallucinated_output = "We recommend ABC stock for growth."
    try:
        crew._validate_task_output(hallucinated_output, validated_tickers)
        print("✗ Test failed: Should have detected hallucinated ticker ABC")
        sys.exit(1)
    except ValueError as e:
        if "hallucinated ticker 'ABC'" in str(e):
            print("✓ Test passed: Correctly detected hallucinated ticker ABC")
        else:
            print(f"✗ Test failed: Wrong error message: {e}")
            sys.exit(1)
    
    # Test 3: Fake company name (should fail)
    fake_company_output = "Alpha Beta Corp is a great investment."
    try:
        crew._validate_task_output(fake_company_output, validated_tickers)
        print("✗ Test failed: Should have detected fake company name")
        sys.exit(1)
    except ValueError as e:
        if "fake company name" in str(e):
            print("✓ Test passed: Correctly detected fake company name")
        else:
            print(f"✗ Test failed: Wrong error message: {e}")
            sys.exit(1)


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Hallucination Fix Implementation")
    print("=" * 60)
    
    try:
        test_extract_validated_tickers()
        test_insufficient_tickers()
        test_hallucination_detection()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nThe hallucination fix is working correctly!")
        print("The report crew will now:")
        print("  1. Fail if fewer than 3 validated tickers are provided")
        print("  2. Extract only real tickers from upstream data")
        print("  3. Detect and reject hallucinated tickers in outputs")
        
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
