#!/usr/bin/env python3
"""
A+ Scoring Tool Demo.

Demonstrates the A+ Investment Scoring Tool with sample data for different asset types.
Shows how the tool evaluates ETFs, stocks, and cryptocurrencies for A+ potential.
"""

from datetime import datetime

from finwiz.tools.a_plus_scoring_tool import APlusScoringTool


def demo_etf_scoring() -> None:
    """Demonstrate A+ scoring for ETFs."""
    print("=" * 60)
    print("ETF A+ SCORING DEMONSTRATION")
    print("=" * 60)

    tool = APlusScoringTool()

    # Excellent ETF example (Vanguard Total Stock Market)
    excellent_etf_data = {
        "expense_ratio": 0.03,  # Very low cost
        "aum": 300e9,  # Large AUM
        "tracking_error": 0.0005,  # Excellent tracking
        "history_years": 20,  # Long track record
        "momentum_score": 0.75,
        "trend_strength": 0.80,
        "volatility_score": 0.70,
        "volatility": 0.16,
        "beta": 1.0,
        "max_drawdown": 0.12,
        "issuer_reputation": 0.95,
        "regulatory_compliance": 0.98,
        "transparency_score": 0.90,
    }

    result = tool._run(
        symbol="VTI", asset_type="etf", fundamental_data=excellent_etf_data, market_context={"vix": 18, "inflation": 2.8}
    )

    print(f"Symbol: {result['symbol']}")
    print(f"Grade: {result['grade']} ({result['percentage']:.1f}%)")
    print(f"A+ Candidate: {result['is_a_plus_candidate']}")
    print(f"Composite Score: {result['analysis_summary']['composite_score']:.3f}")
    print(f"Recommendation: {result['recommendation']}")
    print("\nComponent Scores:")
    for component, score in result["analysis_summary"]["component_scores"].items():
        print(f"  {component.capitalize()}: {score:.3f}")
    print(f"\nTop Strengths: {', '.join(result['analysis_summary']['top_strengths'])}")
    print(f"Main Concerns: {', '.join(result['analysis_summary']['main_concerns'])}")
    print(f"Confidence: {result['analysis_summary']['confidence']:.2f}")


def demo_stock_scoring() -> None:
    """Demonstrate A+ scoring for stocks."""
    print("\n" + "=" * 60)
    print("STOCK A+ SCORING DEMONSTRATION")
    print("=" * 60)

    tool = APlusScoringTool()

    # Excellent stock example (High-quality growth company)
    excellent_stock_data = {
        "roe": 0.28,  # Excellent ROE
        "revenue_growth": 0.22,  # Strong growth
        "debt_to_equity": 0.15,  # Low debt
        "market_cap": 50e9,  # Large cap
        "fcf_positive": True,
        "fcf_growing": True,
        "momentum_score": 0.85,
        "trend_strength": 0.80,
        "volatility_score": 0.65,
        "volatility": 0.25,
        "beta": 1.3,
        "max_drawdown": 0.18,
        "management_quality": 0.90,
        "governance_score": 0.88,
        "competitive_moat": 0.92,
    }

    result = tool._run(
        symbol="AAPL", asset_type="stock", fundamental_data=excellent_stock_data, market_context={"vix": 20, "inflation": 3.2}
    )

    print(f"Symbol: {result['symbol']}")
    print(f"Grade: {result['grade']} ({result['percentage']:.1f}%)")
    print(f"A+ Candidate: {result['is_a_plus_candidate']}")
    print(f"Composite Score: {result['analysis_summary']['composite_score']:.3f}")
    print(f"Recommendation: {result['recommendation']}")
    print("\nComponent Scores:")
    for component, score in result["analysis_summary"]["component_scores"].items():
        print(f"  {component.capitalize()}: {score:.3f}")
    print(f"\nTop Strengths: {', '.join(result['analysis_summary']['top_strengths'])}")
    print(f"Main Concerns: {', '.join(result['analysis_summary']['main_concerns'])}")
    print(f"Confidence: {result['analysis_summary']['confidence']:.2f}")


def demo_crypto_scoring() -> None:
    """Demonstrate A+ scoring for cryptocurrencies."""
    print("\n" + "=" * 60)
    print("CRYPTO A+ SCORING DEMONSTRATION")
    print("=" * 60)

    tool = APlusScoringTool()

    # Quality crypto example (Bitcoin)
    quality_crypto_data = {
        "market_cap": 800e9,  # Very large market cap
        "daily_volume": 15e9,  # High liquidity
        "age_months": 180,  # Mature project
        "institutional_adoption": True,
        "real_utility": True,
        "momentum_score": 0.70,
        "trend_strength": 0.75,
        "volatility_score": 0.40,  # High volatility penalty
        "volatility": 0.60,
        "beta": 3.0,
        "max_drawdown": 0.50,
        "team_quality": 0.85,
        "development_activity": 0.80,
        "community_strength": 0.95,
    }

    result = tool._run(
        symbol="BTC", asset_type="crypto", fundamental_data=quality_crypto_data, market_context={"vix": 25, "inflation": 3.8}
    )

    print(f"Symbol: {result['symbol']}")
    print(f"Grade: {result['grade']} ({result['percentage']:.1f}%)")
    print(f"A+ Candidate: {result['is_a_plus_candidate']}")
    print(f"Composite Score: {result['analysis_summary']['composite_score']:.3f}")
    print(f"Recommendation: {result['recommendation']}")
    print("\nComponent Scores:")
    for component, score in result["analysis_summary"]["component_scores"].items():
        print(f"  {component.capitalize()}: {score:.3f}")
    print(f"\nTop Strengths: {', '.join(result['analysis_summary']['top_strengths'])}")
    print(f"Main Concerns: {', '.join(result['analysis_summary']['main_concerns'])}")
    print(f"Confidence: {result['analysis_summary']['confidence']:.2f}")


def demo_market_regime_adaptation() -> None:
    """Demonstrate how scoring adapts to different market regimes."""
    print("\n" + "=" * 60)
    print("MARKET REGIME ADAPTATION DEMONSTRATION")
    print("=" * 60)

    tool = APlusScoringTool()

    # Sample stock data
    stock_data = {
        "roe": 0.20,
        "revenue_growth": 0.15,
        "debt_to_equity": 0.25,
        "market_cap": 10e9,
        "fcf_positive": True,
        "fcf_growing": True,
        "momentum_score": 0.70,
        "trend_strength": 0.65,
        "volatility_score": 0.60,
        "volatility": 0.22,
        "beta": 1.2,
        "max_drawdown": 0.15,
        "management_quality": 0.75,
        "governance_score": 0.80,
        "competitive_moat": 0.70,
    }

    # Bull market scenario
    bull_market = {"vix": 12, "inflation": 2.0, "rate_change_6m": -0.5}
    bull_result = tool._run("TEST", "stock", stock_data, bull_market)

    # Bear market scenario
    bear_market = {"vix": 40, "inflation": 6.5, "rate_change_6m": 3.0}
    bear_result = tool._run("TEST", "stock", stock_data, bear_market)

    print("BULL MARKET SCENARIO:")
    print(f"  Composite Score: {bull_result['analysis_summary']['composite_score']:.3f}")
    print(f"  Grade: {bull_result['grade']}")
    print(f"  Market Regime: {bull_result['a_plus_score']['market_regime']['regime_type']}")

    print("\nBEAR MARKET SCENARIO:")
    print(f"  Composite Score: {bear_result['analysis_summary']['composite_score']:.3f}")
    print(f"  Grade: {bear_result['grade']}")
    print(f"  Market Regime: {bear_result['a_plus_score']['market_regime']['regime_type']}")

    bull_score = bull_result["analysis_summary"]["composite_score"]
    bear_score = bear_result["analysis_summary"]["composite_score"]
    print(f"\nScore Difference: {bull_score - bear_score:.3f}")
    print("(Bull market typically scores higher due to relaxed criteria)")


def demo_custom_criteria() -> None:
    """Demonstrate custom criteria functionality."""
    print("\n" + "=" * 60)
    print("CUSTOM CRITERIA DEMONSTRATION")
    print("=" * 60)

    tool = APlusScoringTool()

    # ETF data that would normally pass
    etf_data = {
        "expense_ratio": 0.12,  # Moderate expense ratio
        "aum": 2e9,
        "tracking_error": 0.0015,
        "history_years": 5,
        "momentum_score": 0.70,
        "trend_strength": 0.75,
        "volatility_score": 0.65,
        "volatility": 0.18,
        "beta": 1.0,
        "max_drawdown": 0.10,
        "issuer_reputation": 0.80,
        "regulatory_compliance": 0.90,
        "transparency_score": 0.85,
    }

    # Standard criteria
    standard_result = tool._run("TEST", "etf", etf_data)

    # Strict custom criteria
    strict_criteria = {
        "etf_max_expense_ratio": 0.05,  # Very strict
        "etf_min_aum": 10e9,  # Very high requirement
    }
    strict_result = tool._run("TEST", "etf", etf_data, custom_criteria=strict_criteria)

    print("STANDARD CRITERIA:")
    print(f"  Composite Score: {standard_result['analysis_summary']['composite_score']:.3f}")
    print(f"  Grade: {standard_result['grade']}")

    print("\nSTRICT CUSTOM CRITERIA:")
    print(f"  Composite Score: {strict_result['analysis_summary']['composite_score']:.3f}")
    print(f"  Grade: {strict_result['grade']}")

    standard_score = standard_result["analysis_summary"]["composite_score"]
    strict_score = strict_result["analysis_summary"]["composite_score"]
    print(f"\nScore Impact: {standard_score - strict_score:.3f}")
    print("(Stricter criteria typically result in lower scores)")


def main() -> int:
    """Run all A+ scoring demonstrations."""
    print("A+ INVESTMENT SCORING TOOL DEMONSTRATION")
    print(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        demo_etf_scoring()
        demo_stock_scoring()
        demo_crypto_scoring()
        demo_market_regime_adaptation()
        demo_custom_criteria()

        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("\nThe A+ Scoring Tool successfully:")
        print("✓ Evaluated different asset types (ETF, Stock, Crypto)")
        print("✓ Adapted scoring criteria to market conditions")
        print("✓ Applied custom criteria overrides")
        print("✓ Generated comprehensive analysis with rationale")
        print("✓ Integrated with existing FinWiz grading system")

    except Exception as e:
        print(f"\nError during demonstration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
