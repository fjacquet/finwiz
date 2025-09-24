#!/usr/bin/env python3
"""
Demonstration of RebalancingHistoryTracker functionality.

This example shows how to use the RebalancingHistoryTracker to:
1. Record rebalancing actions
2. Analyze performance attribution
3. Generate trend analysis
4. Create analytics dashboards
"""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from finwiz.quantitative.rebalancing_history_tracker import RebalancingHistoryTracker
from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    ExecutionSummary,
    PortfolioAnalysis,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


def create_sample_rebalancing_result(portfolio_value: float = 100000.0) -> RebalancingResult:
    """Create a sample rebalancing result for demonstration."""
    # Current portfolio analysis
    current_portfolio = PortfolioAnalysis(
        total_value=portfolio_value,
        weightings={"AAPL": 0.45, "GOOGL": 0.30, "MSFT": 0.25},
        deviations_from_target={"AAPL": 0.10, "GOOGL": -0.05, "MSFT": 0.0},
        positions_needing_rebalancing=["AAPL", "GOOGL"],
        risk_metrics={"volatility": 0.16, "sharpe_ratio": 1.1},
    )

    # Trade recommendations
    trade_recommendations = [
        TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.SELL,
            quantity=67.0,
            current_price=150.0,
            trade_value=10050.0,
            estimated_commission=5.0,
            estimated_spread_cost=20.0,
            total_estimated_cost=25.0,
            current_weight=0.45,
            target_weight=0.35,
            weight_deviation=0.10,
            projected_weight_after_trade=0.35,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Reduce overweight position to target allocation",
        ),
        TradeRecommendation(
            symbol="GOOGL",
            action=TradeAction.BUY,
            quantity=4.0,
            current_price=2500.0,
            trade_value=10000.0,
            estimated_commission=5.0,
            estimated_spread_cost=25.0,
            total_estimated_cost=30.0,
            current_weight=0.30,
            target_weight=0.35,
            weight_deviation=-0.05,
            projected_weight_after_trade=0.35,
            priority=2,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Increase underweight position to target allocation",
        ),
    ]

    # Projected portfolio after rebalancing
    projected_portfolio = PortfolioAnalysis(
        total_value=portfolio_value,
        weightings={"AAPL": 0.35, "GOOGL": 0.35, "MSFT": 0.30},
        deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.05},
        positions_needing_rebalancing=[],
        risk_metrics={"volatility": 0.14, "sharpe_ratio": 1.3},
    )

    # Cost analysis
    cost_analysis = CostAnalysis(
        total_transaction_costs=55.0,
        commission_costs=10.0,
        spread_costs=45.0,
        cost_as_percentage=0.00055,
    )

    # Execution summary
    execution_summary = ExecutionSummary(
        total_trades_required=2,
        positions_requiring_action=2,
        positions_within_tolerance=1,
        estimated_execution_time="3 minutes",
        capital_required=0.0,
    )

    return RebalancingResult(
        analysis_timestamp=datetime.now(),
        portfolio_id="demo_portfolio",
        current_portfolio=current_portfolio,
        trade_recommendations=trade_recommendations,
        projected_portfolio=projected_portfolio,
        cost_analysis=cost_analysis,
        current_risk_score=6.5,
        projected_risk_score=5.8,
        risk_improvement=0.7,
        execution_summary=execution_summary,
        overall_recommendation=RebalancingRecommendation.REBALANCE_NOW,
        next_review_date=datetime.now() + timedelta(days=30),
    )


def main() -> None:
    """Demonstrate RebalancingHistoryTracker functionality."""
    print("🔄 RebalancingHistoryTracker Demo")
    print("=" * 50)

    # Create temporary storage for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "rebalancing_history"
        tracker = RebalancingHistoryTracker(storage_path=str(storage_path))

        portfolio_id = "demo_portfolio_001"

        print(f"\n📊 Recording rebalancing history for portfolio: {portfolio_id}")

        # Simulate multiple rebalancing events over time
        base_date = datetime.now() - timedelta(days=180)
        entry_ids = []

        for i in range(6):
            # Create rebalancing result with varying portfolio values
            portfolio_value = 100000 + (i * 8000)  # Growing portfolio
            result = create_sample_rebalancing_result(portfolio_value)
            result.analysis_timestamp = base_date + timedelta(days=i * 30)

            # Simulate executed trades (sometimes partial execution)
            executed_trades = result.trade_recommendations.copy()
            if i % 3 == 0:  # Every third rebalancing, only execute first trade
                executed_trades = executed_trades[:1]
                execution_status = "PARTIAL"
            else:
                execution_status = "COMPLETED"

            # Record the rebalancing action
            entry_id = tracker.record_rebalancing_action(
                portfolio_id=portfolio_id,
                rebalancing_result=result,
                executed_trades=executed_trades,
                execution_status=execution_status,
                execution_notes=f"Rebalancing event #{i + 1} - {execution_status.lower()} execution",
            )

            entry_ids.append(entry_id)
            print(f"  ✅ Recorded rebalancing #{i + 1}: {entry_id[:8]}... (${portfolio_value:,.0f})")

        print("\n📈 Retrieving portfolio history...")

        # Get full history
        full_history = tracker.get_portfolio_history(portfolio_id)
        print(f"  📋 Total history entries: {len(full_history)}")

        # Get filtered history (last 90 days)
        recent_start = datetime.now() - timedelta(days=90)
        recent_history = tracker.get_portfolio_history(portfolio_id, start_date=recent_start)
        print(f"  📋 Recent entries (last 90 days): {len(recent_history)}")

        print("\n🎯 Analyzing performance attribution...")

        # Performance attribution analysis
        try:
            start_date = base_date
            end_date = datetime.now()
            attribution = tracker.analyze_performance_attribution(portfolio_id, start_date, end_date)

            start_str = attribution.start_date.strftime("%Y-%m-%d")
            end_str = attribution.end_date.strftime("%Y-%m-%d")
            print(f"  📊 Analysis period: {start_str} to {end_str}")
            print(f"  💰 Rebalanced return: {attribution.rebalanced_return:.2%}")
            print(f"  📈 Buy-and-hold return: {attribution.buy_and_hold_return:.2%}")
            print(f"  ⚡ Rebalancing alpha: {attribution.rebalancing_alpha:.2%}")
            print(f"  💸 Total costs: ${attribution.total_rebalancing_costs:.2f}")
            print(f"  🎯 Net benefit: {attribution.net_benefit:.2%}")
            print(f"  📅 Avg days between rebalancing: {attribution.average_days_between_rebalancing:.1f}")

        except ValueError as e:
            print(f"  ⚠️  Performance attribution: {e}")

        print("\n📊 Analyzing rebalancing trends...")

        # Trend analysis
        trend_analysis = tracker.analyze_rebalancing_trends(portfolio_id, analysis_period_days=365)

        print(f"  🎯 Optimal frequency: {trend_analysis.optimal_frequency_days} days")
        print(f"  📏 Optimal tolerance: {trend_analysis.optimal_tolerance_band:.1%}")
        print(f"  🎯 Recommended frequency: {trend_analysis.recommended_frequency} days")
        print(f"  📏 Recommended tolerance: {trend_analysis.recommended_tolerance:.1%}")
        print(f"  🎯 Confidence score: {trend_analysis.confidence_score:.1%}")

        print("\n  📈 Performance by frequency:")
        for freq, perf in trend_analysis.frequency_performance.items():
            cost = trend_analysis.frequency_costs[freq]
            risk = trend_analysis.frequency_risk[freq]
            print(f"    {freq:3d} days: {perf:.1%} return, {cost:.1%} cost, {risk:.1%} risk")

        print("\n🎛️  Generating analytics dashboard...")

        # Generate comprehensive analytics
        analytics = tracker.generate_analytics_dashboard(portfolio_id)

        print(f"  📊 Portfolio: {analytics.portfolio_id}")
        print(f"  📅 Analysis date: {analytics.analysis_date.strftime('%Y-%m-%d %H:%M')}")
        print(f"  🔄 Total rebalancing events: {analytics.total_rebalancing_events}")
        print(f"  📈 Success rate: {analytics.rebalancing_success_rate:.1%}")
        print(f"  💰 Cost efficiency score: {analytics.cost_efficiency_score:.1f}/10")
        print(f"  📊 Avg deviation improvement: {analytics.average_deviation_improvement:.2%}")

        print("\n  🏆 Most rebalanced positions:")
        for symbol in analytics.most_rebalanced_positions:
            print(f"    📈 {symbol}")

        print("\n  💡 Strategy recommendations:")
        for i, recommendation in enumerate(analytics.strategy_recommendations, 1):
            print(f"    {i}. {recommendation}")

        if analytics.tolerance_adjustment_suggestions:
            print("\n  ⚙️  Tolerance adjustments suggested:")
            for symbol, tolerance in analytics.tolerance_adjustment_suggestions.items():
                print(f"    📏 {symbol}: {tolerance:.1%}")

        print("\n  📋 Position histories:")
        for pos_history in analytics.position_histories:
            print(f"    📈 {pos_history.symbol}:")
            print(f"      🔄 Rebalanced {pos_history.rebalancing_frequency} times")
            print(f"      📊 Avg deviation: {pos_history.average_deviation:.2%}")
            print(f"      📈 Max deviation: {pos_history.max_deviation:.2%}")
            print(f"      💰 Total costs: ${pos_history.total_transaction_costs:.2f}")

    print("\n✅ Demo completed successfully!")
    print("\n💡 The RebalancingHistoryTracker provides comprehensive tracking and analysis")
    print("   of portfolio rebalancing activities, helping optimize rebalancing strategies")
    print("   through data-driven insights and performance attribution analysis.")


if __name__ == "__main__":
    main()
