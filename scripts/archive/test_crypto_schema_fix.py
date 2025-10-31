#!/usr/bin/env python
"""
Quick test to verify the crypto schema fixes work correctly.
"""

from datetime import date

from src.finwiz.schemas.common import RiskAssessmentStandardized
from src.finwiz.schemas.crypto import (
    CryptoInvestmentStrategy,
    CryptoQuantitativeMetrics,
    CryptoThesis,
)


def test_portfolio_symbol():
    """Test that portfolio identifiers up to 30 chars work."""
    print("Testing portfolio symbol length...")

    # Test individual crypto (short)
    thesis_btc = CryptoThesis(symbol="BTC", thesis_bullets=["Bitcoin thesis"], references=["https://bitcoin.org/"])
    print(f"✅ Short symbol works: {thesis_btc.symbol}")

    # Test portfolio identifier (long)
    thesis_portfolio = CryptoThesis(
        symbol="CRYPTO_TOP10_PORTFOLIO",  # 23 chars
        thesis_bullets=["Portfolio thesis"],
        references=["https://example.com/"],
    )
    print(f"✅ Long symbol works: {thesis_portfolio.symbol} ({len(thesis_portfolio.symbol)} chars)")


def test_url_validation():
    """Test that URLs with trailing slashes work."""
    print("\nTesting URL validation...")

    valid_urls = [
        "https://polygon.technology/",
        "https://cardano.org/",
        "https://ethereum.org/en/",
        "https://glassnode.com/",
        "https://coinmetrics.io/",
        "https://www.sec.gov/",
    ]

    thesis = CryptoThesis(symbol="TEST", thesis_bullets=["Test"], references=valid_urls)

    print(f"✅ All {len(valid_urls)} URLs validated successfully:")
    for url in thesis.references:
        print(f"   - {url}")


def test_max_drawdown():
    """Test that negative max drawdown values work."""
    print("\nTesting max drawdown validation...")

    # Test negative drawdown (correct)
    metrics = CryptoQuantitativeMetrics(
        symbol="BTC",
        sharpe_ratio=1.05,
        sortino_ratio=1.4,
        max_drawdown=-0.62,  # Negative (correct)
        volatility=0.68,
    )
    print(f"✅ Negative max drawdown works: {metrics.max_drawdown}")

    # Test zero drawdown (edge case)
    metrics_zero = CryptoQuantitativeMetrics(symbol="STABLE", max_drawdown=0.0)
    print(f"✅ Zero max drawdown works: {metrics_zero.max_drawdown}")


def test_full_strategy():
    """Test complete CryptoInvestmentStrategy object."""
    print("\nTesting complete CryptoInvestmentStrategy...")

    strategy = CryptoInvestmentStrategy(
        schema_version=1,
        symbol="TOP10PORT",
        name="Top Crypto Portfolio",
        strategy_date=date(2025, 10, 8),
        investment_thesis=CryptoThesis(
            symbol="TOP10PORT",
            thesis_bullets=[
                "Diversified portfolio of top 10 cryptocurrencies",
                "Core-satellite approach with BTC/ETH as core",
            ],
            references=[
                "https://glassnode.com/",
                "https://ethereum.org/en/",
                "https://polygon.technology/",
                "https://cardano.org/",
            ],
        ),
        risk_assessment=RiskAssessmentStandardized(scale="0_5", score=2.8, level="High", risk_factors=["Market volatility", "Regulatory risk"]),
        quantitative_metrics=CryptoQuantitativeMetrics(
            symbol="TOP10PORT",
            sharpe_ratio=1.05,
            sortino_ratio=1.4,
            max_drawdown=-0.62,  # Negative!
            volatility=0.68,
            correlation_with_btc=0.92,
            expected_return=0.22,
            recommendation="BUY",
            confidence=0.72,
        ),
        recommended_allocation=100.0,
        entry_strategy="DCA over 4-6 weeks with momentum filter",
        exit_strategy="Stop-loss and trailing rules",
        time_horizon="long",
        stop_loss_level=0.2,
        take_profit_levels=[0.5, 1.0, 2.0],
        recommendation="BUY",
        confidence_level=0.72,
        strategy_summary="Long-term capital appreciation strategy with tactical overlays",
    )

    print("✅ Complete strategy validated successfully!")
    print(f"   Symbol: {strategy.symbol}")
    print(f"   Max Drawdown: {strategy.quantitative_metrics.max_drawdown}")
    print(f"   References: {len(strategy.investment_thesis.references)} URLs")
    print(f"   Recommendation: {strategy.recommendation}")


if __name__ == "__main__":
    print("=" * 80)
    print("Crypto Schema Fix Validation Tests")
    print("=" * 80)

    try:
        test_portfolio_symbol()
        test_url_validation()
        test_max_drawdown()
        test_full_strategy()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nThe crypto schema fixes are working correctly.")
        print("You can now re-run the crypto crew analysis.")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED!")
        print("=" * 80)
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
