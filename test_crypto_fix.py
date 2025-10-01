#!/usr/bin/env python3
"""
Test script to verify the crypto crew JSON serialization fix.
"""

import json
import os

# Set up environment variables
os.environ.update({
    "OPENAI_API_KEY": "test-key",
    "SERPER_API_KEY": "test-key", 
    "FIRECRAWL_API_KEY": "test-key",
    "ALPHA_VANTAGE_API_KEY": "test-key",
})

from src.finwiz.schemas.crypto import CryptoThesis


def test_crypto_thesis_serialization():
    """Test that CryptoThesis can be JSON serialized."""
    # Create a sample CryptoThesis instance
    thesis = CryptoThesis(
        symbol="BTC",
        thesis_bullets=["Strong institutional adoption", "Limited supply"],
        references=["https://example.com/btc-analysis", "https://coindesk.com/bitcoin-news"]
    )

    # Test JSON serialization
    try:
        json_str = thesis.model_dump_json()
        print("✅ CryptoThesis JSON serialization successful")
        print(f"JSON: {json_str}")

        # Test deserialization
        thesis_dict = json.loads(json_str)
        thesis_restored = CryptoThesis.model_validate(thesis_dict)
        print("✅ CryptoThesis JSON deserialization successful")

        return True
    except Exception as e:
        print(f"❌ CryptoThesis serialization failed: {e}")
        return False

def test_url_validation():
    """Test URL validation in CryptoThesis."""
    # Test valid URLs
    try:
        thesis = CryptoThesis(
            symbol="ETH",
            thesis_bullets=["Smart contract platform"],
            references=["https://ethereum.org", "http://example.com/eth"]
        )
        print("✅ Valid URLs accepted")
    except Exception as e:
        print(f"❌ Valid URLs rejected: {e}")
        return False

    # Test invalid URLs
    try:
        thesis = CryptoThesis(
            symbol="ETH",
            thesis_bullets=["Smart contract platform"],
            references=["not-a-url", "ftp://invalid.com"]
        )
        print("❌ Invalid URLs should have been rejected")
        return False
    except ValueError as e:
        print("✅ Invalid URLs properly rejected")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing CryptoThesis JSON serialization fix...")

    success1 = test_crypto_thesis_serialization()
    success2 = test_url_validation()

    if success1 and success2:
        print("\n🎉 All tests passed! The JSON serialization fix is working.")
    else:
        print("\n💥 Some tests failed. Check the output above.")
