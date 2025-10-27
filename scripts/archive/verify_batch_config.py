#!/usr/bin/env python
"""
Verification script for batch prefetch configuration.

This script demonstrates the configuration loading, validation, and logging.
"""

import os
import sys

# Add src to path
sys.path.insert(0, "src")

from finwiz.config.batch_prefetch_config import (
    get_batch_prefetch_config,
    reset_config_cache,
)


def test_default_configuration():
    """Test default configuration."""
    print("\n" + "=" * 80)
    print("TEST 1: Default Configuration")
    print("=" * 80)

    # Clear any existing environment variables
    for key in ["BATCH_PREFETCH_ENABLED", "ALPHA_VANTAGE_RATE_LIMIT", "BATCH_PREFETCH_MIN_HOLDINGS"]:
        os.environ.pop(key, None)

    reset_config_cache()
    config = get_batch_prefetch_config(log_config=True)

    print("\nConfiguration loaded:")
    print(f"  enabled: {config.enabled}")
    print(f"  alpha_vantage_rate_limit: {config.alpha_vantage_rate_limit}")
    print(f"  min_holdings_for_batch: {config.min_holdings_for_batch}")

    assert config.enabled is True
    assert config.alpha_vantage_rate_limit == 5
    assert config.min_holdings_for_batch == 10
    print("\n✓ Default configuration test PASSED")


def test_custom_configuration():
    """Test custom configuration from environment variables."""
    print("\n" + "=" * 80)
    print("TEST 2: Custom Configuration")
    print("=" * 80)

    # Set custom environment variables
    os.environ["BATCH_PREFETCH_ENABLED"] = "false"
    os.environ["ALPHA_VANTAGE_RATE_LIMIT"] = "75"
    os.environ["BATCH_PREFETCH_MIN_HOLDINGS"] = "20"

    reset_config_cache()
    config = get_batch_prefetch_config(log_config=True)

    print("\nConfiguration loaded:")
    print(f"  enabled: {config.enabled}")
    print(f"  alpha_vantage_rate_limit: {config.alpha_vantage_rate_limit}")
    print(f"  min_holdings_for_batch: {config.min_holdings_for_batch}")

    assert config.enabled is False
    assert config.alpha_vantage_rate_limit == 75
    assert config.min_holdings_for_batch == 20
    print("\n✓ Custom configuration test PASSED")


def test_invalid_configuration():
    """Test invalid configuration handling."""
    print("\n" + "=" * 80)
    print("TEST 3: Invalid Configuration Handling")
    print("=" * 80)

    # Set invalid environment variables
    os.environ["BATCH_PREFETCH_ENABLED"] = "true"
    os.environ["ALPHA_VANTAGE_RATE_LIMIT"] = "invalid"
    os.environ["BATCH_PREFETCH_MIN_HOLDINGS"] = "not_a_number"

    reset_config_cache()
    config = get_batch_prefetch_config(log_config=True)

    print("\nConfiguration loaded (with fallback to defaults):")
    print(f"  enabled: {config.enabled}")
    print(f"  alpha_vantage_rate_limit: {config.alpha_vantage_rate_limit}")
    print(f"  min_holdings_for_batch: {config.min_holdings_for_batch}")

    # Should fall back to defaults for invalid values
    assert config.enabled is True
    assert config.alpha_vantage_rate_limit == 5  # Default
    assert config.min_holdings_for_batch == 10  # Default
    print("\n✓ Invalid configuration handling test PASSED")


def test_premium_tier_configuration():
    """Test premium tier configuration."""
    print("\n" + "=" * 80)
    print("TEST 4: Premium Tier Configuration")
    print("=" * 80)

    # Set premium tier configuration
    os.environ["BATCH_PREFETCH_ENABLED"] = "true"
    os.environ["ALPHA_VANTAGE_RATE_LIMIT"] = "75"
    os.environ["BATCH_PREFETCH_MIN_HOLDINGS"] = "10"

    reset_config_cache()
    config = get_batch_prefetch_config(log_config=True)

    print("\nConfiguration loaded:")
    print(f"  enabled: {config.enabled}")
    print(f"  alpha_vantage_rate_limit: {config.alpha_vantage_rate_limit} (Premium tier)")
    print(f"  min_holdings_for_batch: {config.min_holdings_for_batch}")

    assert config.enabled is True
    assert config.alpha_vantage_rate_limit == 75
    assert config.min_holdings_for_batch == 10
    print("\n✓ Premium tier configuration test PASSED")


def main():
    """Run all verification tests."""
    print("\n" + "=" * 80)
    print("BATCH PREFETCH CONFIGURATION VERIFICATION")
    print("=" * 80)

    try:
        test_default_configuration()
        test_custom_configuration()
        test_invalid_configuration()
        test_premium_tier_configuration()

        print("\n" + "=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nBatch prefetch configuration is working correctly!")
        print("Configuration can be controlled via environment variables:")
        print("  - BATCH_PREFETCH_ENABLED (default: true)")
        print("  - ALPHA_VANTAGE_RATE_LIMIT (default: 5)")
        print("  - BATCH_PREFETCH_MIN_HOLDINGS (default: 10)")
        print("\n")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
