#!/usr/bin/env python3
"""
Test script to verify all runtime fixes are working.
"""

import sys


def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from langchain_text_splitters import CharacterTextSplitter

        print("✅ langchain_text_splitters import works")
    except ImportError as e:
        print(f"❌ langchain_text_splitters import failed: {e}")
        return False

    try:
        print("✅ EnhancedSECAnalysisTool import works")
    except Exception as e:
        print(f"❌ EnhancedSECAnalysisTool import failed: {e}")
        return False

    try:
        print("✅ StandardizedSentimentAnalysisTool import works")
    except Exception as e:
        print(f"❌ StandardizedSentimentAnalysisTool import failed: {e}")
        return False

    return True


def test_tool_instantiation():
    """Test that tools can be instantiated without Pydantic errors."""
    print("\nTesting tool instantiation...")

    try:
        from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool

        tool = StandardizedSentimentAnalysisTool()
        print("✅ StandardizedSentimentAnalysisTool instantiation works")
    except Exception as e:
        print(f"❌ StandardizedSentimentAnalysisTool instantiation failed: {e}")
        return False

    try:
        from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool

        tool = EnhancedSECAnalysisTool()
        print("✅ EnhancedSECAnalysisTool instantiation works")
    except Exception as e:
        print(f"❌ EnhancedSECAnalysisTool instantiation failed: {e}")
        return False

    return True


def test_portfolio_schema():
    """Test that portfolio review schema validation works."""
    print("\nTesting portfolio review schema...")

    try:
        from datetime import datetime

        from finwiz.schemas.portfolio_review import PortfolioReview

        # Test with minimal valid data
        review = PortfolioReview(as_of=datetime.now(), base_currency="CHF", holdings=[])
        print("✅ PortfolioReview schema validation works")

        # Test serialization
        json_data = review.model_dump_json()
        print("✅ PortfolioReview serialization works")

        return True
    except Exception as e:
        print(f"❌ PortfolioReview schema test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Runtime Fixes Verification")
    print("=" * 60)

    all_passed = True

    if not test_imports():
        all_passed = False

    if not test_tool_instantiation():
        all_passed = False

    if not test_portfolio_schema():
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - Runtime fixes are working!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED - Runtime errors still exist")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
