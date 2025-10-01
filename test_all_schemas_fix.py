#!/usr/bin/env python3
"""
Test script to verify all schema JSON serialization fixes.
"""

import json
import os
from datetime import UTC, date, datetime

# Set up environment variables
os.environ.update({
    "OPENAI_API_KEY": "test-key",
    "SERPER_API_KEY": "test-key", 
    "FIRECRAWL_API_KEY": "test-key",
    "ALPHA_VANTAGE_API_KEY": "test-key",
})

from src.finwiz.schemas.crypto import CryptoThesis
from src.finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
from src.finwiz.schemas.perplexity import SonarArticle
from src.finwiz.schemas.stock import SentimentItem, TenKInsight


def test_schema_serialization(schema_class, sample_data, schema_name):
    """Test JSON serialization for a schema."""
    try:
        # Create instance
        instance = schema_class(**sample_data)

        # Test JSON serialization
        json_str = instance.model_dump_json()

        # Test deserialization
        instance_dict = json.loads(json_str)
        instance_restored = schema_class.model_validate(instance_dict)

        print(f"✅ {schema_name} JSON serialization successful")
        return True
    except Exception as e:
        print(f"❌ {schema_name} serialization failed: {e}")
        return False

def main():
    print("Testing all schema JSON serialization fixes...")

    results = []

    # Test CryptoThesis
    crypto_data = {
        "symbol": "BTC",
        "thesis_bullets": ["Strong institutional adoption"],
        "references": ["https://example.com/btc"]
    }
    results.append(test_schema_serialization(CryptoThesis, crypto_data, "CryptoThesis"))

    # Test TenKInsight
    tenk_data = {
        "ticker": "AAPL",
        "filing_url": "https://sec.gov/filing/123",
        "filed_at": datetime.now(UTC),
        "section": "Item 1A",
        "excerpt": "This is a sample excerpt from the filing",
        "sec_citation": "10-K (2024), Item 1A, p. 17"
    }
    results.append(test_schema_serialization(TenKInsight, tenk_data, "TenKInsight"))

    # Test SentimentItem
    sentiment_data = {
        "headline": "Apple stock rises",
        "url": "https://example.com/news",
        "date": datetime.now(UTC),
        "score": 0.8
    }
    results.append(test_schema_serialization(SentimentItem, sentiment_data, "SentimentItem"))

    # Test ETFTopHolding
    holding_data = {
        "ticker": "AAPL",
        "weight_pct": 5.2,
        "source_url": "https://example.com/holdings",
        "as_of": date.today()
    }
    results.append(test_schema_serialization(ETFTopHolding, holding_data, "ETFTopHolding"))

    # Test ETFFactsheet
    factsheet_data = {
        "ticker": "SPY",
        "issuer": "SPDR",
        "expense_ratio": 0.09,
        "factsheet_url": "https://example.com/factsheet",
        "as_of": date.today(),
        "factsheet_highlights": ["Low cost", "Broad diversification"]
    }
    results.append(test_schema_serialization(ETFFactsheet, factsheet_data, "ETFFactsheet"))

    # Test SonarArticle
    sonar_data = {
        "title": "Market Analysis",
        "url": "https://example.com/article",
        "summary": "Market summary",
        "publisher": "Financial Times"
    }
    results.append(test_schema_serialization(SonarArticle, sonar_data, "SonarArticle"))

    # Summary
    passed = sum(results)
    total = len(results)

    print(f"\n📊 Results: {passed}/{total} schemas passed")

    if passed == total:
        print("🎉 All schema serialization fixes are working!")
    else:
        print("💥 Some schemas still have issues.")

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
