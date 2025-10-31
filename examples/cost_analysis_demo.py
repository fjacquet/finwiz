#!/usr/bin/env python3
"""
Cost Analysis Demo.

Demonstrates the CostAnalyzer functionality for portfolio rebalancing
transaction cost analysis.
"""

from finwiz.quantitative.cost_analyzer import BrokerType, CostAnalyzer
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


def main() -> None:
    """Demonstrate cost analysis functionality."""
    print("=== FinWiz Cost Analysis Demo ===\n")

    # Initialize cost analyzer with different broker types
    print("1. Testing different broker types:")

    brokers = [
        BrokerType.COMMISSION_FREE,
        BrokerType.DISCOUNT,
        BrokerType.FULL_SERVICE,
    ]

    for broker_type in brokers:
        analyzer = CostAnalyzer(broker_type)
        commission = analyzer.calculate_commission_cost(10000.0, "AAPL", 100.0)
        print(f"   {broker_type}: ${commission:.2f} commission on $10,000 trade")

    print("\n2. Testing spread estimation:")

    analyzer = CostAnalyzer()

    # Test different symbol types
    symbols_and_values = [
        ("SPY", 5000.0, "ETF"),
        ("AAPL", 10000.0, "Large Cap Stock"),
        ("SMALLCAP", 2000.0, "Small Cap Stock"),
    ]

    for symbol, trade_value, description in symbols_and_values:
        spread_estimate = analyzer.estimate_bid_ask_spread(symbol, trade_value)
        print(f"   {description} ({symbol}): {spread_estimate.estimated_spread_bps:.1f} bps, ${spread_estimate.estimated_spread_cost:.2f} cost")

    print("\n3. Testing market impact estimation:")

    portfolio_value = 100000.0
    trade_sizes = [
        (500.0, "Small trade (0.5%)"),
        (5000.0, "Medium trade (5%)"),
        (15000.0, "Large trade (15%)"),
    ]

    for trade_value, description in trade_sizes:
        impact_estimate = analyzer.estimate_market_impact("AAPL", trade_value, portfolio_value)
        print(f"   {description}: {impact_estimate.impact_category}, {impact_estimate.estimated_impact_bps:.1f} bps, ${impact_estimate.estimated_impact_cost:.2f} cost")

    print("\n4. Testing comprehensive cost analysis:")

    # Create sample trade recommendations
    trade_recommendations = [
        TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=33.33,
            current_price=150.0,
            trade_value=33.33 * 150.0,  # Ensure consistency
            estimated_commission=0.0,
            estimated_spread_cost=0.0,
            total_estimated_cost=0.0,
            current_weight=0.3,
            target_weight=0.4,
            weight_deviation=-0.1,
            projected_weight_after_trade=0.4,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Rebalance AAPL to target allocation",
        ),
        TradeRecommendation(
            symbol="GOOGL",
            action=TradeAction.SELL,
            quantity=2.5,
            current_price=2000.0,
            trade_value=2.5 * 2000.0,  # Ensure consistency
            estimated_commission=0.0,
            estimated_spread_cost=0.0,
            total_estimated_cost=0.0,
            current_weight=0.4,
            target_weight=0.3,
            weight_deviation=0.1,
            projected_weight_after_trade=0.3,
            priority=2,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Rebalance GOOGL to target allocation",
        ),
    ]

    # Create portfolio analysis
    portfolio = PortfolioAnalysis(
        total_value=100000.0,
        weightings={"AAPL": 0.3, "GOOGL": 0.4, "MSFT": 0.3},
        deviations_from_target={"AAPL": -0.1, "GOOGL": 0.1, "MSFT": 0.0},
    )

    # Create portfolio configuration
    config = PortfolioConfiguration(
        holdings=[
            Holding(symbol="AAPL", shares=200),
            Holding(symbol="GOOGL", shares=20),
            Holding(symbol="MSFT", shares=120),
        ],
        target_weights={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
    )

    # Analyze costs
    cost_analysis = analyzer.analyze_transaction_costs(trade_recommendations, portfolio, config)

    print(f"   Total transaction costs: ${cost_analysis.total_transaction_costs:.2f}")
    print(f"   Commission costs: ${cost_analysis.commission_costs:.2f}")
    print(f"   Spread costs: ${cost_analysis.spread_costs:.2f}")
    print(f"   Market impact costs: ${cost_analysis.market_impact_costs:.2f}")
    print(f"   Cost as % of portfolio: {cost_analysis.cost_as_percentage:.3f}%")
    if cost_analysis.break_even_days:
        print(f"   Break-even period: {cost_analysis.break_even_days} days")

    print("\n5. Testing cost-benefit analysis:")

    cost_benefit = analyzer.perform_cost_benefit_analysis(
        cost_analysis.total_transaction_costs,
        trade_recommendations,
        portfolio,
        config,
    )

    print(f"   Recommendation: {cost_benefit.recommendation}")
    print(f"   Rationale: {cost_benefit.rationale}")
    print(f"   Expected annual benefit: ${cost_benefit.expected_annual_benefit:.2f}")

    if cost_benefit.alternative_approaches:
        print("   Alternative approaches:")
        for approach in cost_benefit.alternative_approaches:
            print(f"     - {approach}")

    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
