"""
Unit tests for the CostAnalyzer class.

Tests comprehensive transaction cost modeling including commission calculation,
bid-ask spread estimation, market impact modeling, and cost-benefit analysis.
"""

from __future__ import annotations

import pytest
from pytest import approx

from finwiz.quantitative.cost_analyzer import (
    BrokerType,
    CostAnalyzer,
)
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


class TestCostAnalyzer:
    """Test cases for CostAnalyzer class."""

    def test_should_initialize_with_default_broker_type_when_no_type_specified(self):
        # Arrange & Act
        analyzer = CostAnalyzer()

        # Assert
        assert analyzer.broker_type == BrokerType.DISCOUNT
        assert analyzer.fee_structure.broker_type == BrokerType.DISCOUNT

    def test_should_initialize_with_specified_broker_type_when_type_provided(self):
        # Arrange & Act
        analyzer = CostAnalyzer(BrokerType.COMMISSION_FREE)

        # Assert
        assert analyzer.broker_type == BrokerType.COMMISSION_FREE
        assert analyzer.fee_structure.broker_type == BrokerType.COMMISSION_FREE

    def test_should_calculate_zero_commission_when_commission_free_broker(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.COMMISSION_FREE)

        # Act
        commission = analyzer.calculate_commission_cost(1000.0, "AAPL", 10.0)

        # Assert
        # Should only have regulatory fees (SEC fee: 1000 * 0.0000221 = 0.0221)
        assert 0.02 <= commission <= 0.03
        assert commission == pytest.approx(0.0221, rel=1e-3)

    def test_should_calculate_commission_with_minimum_when_discount_broker(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.DISCOUNT)

        # Act
        commission = analyzer.calculate_commission_cost(100.0, "AAPL", 1.0)

        # Assert
        # Should have regulatory fees only for discount broker
        expected = 100.0 * 0.0000221  # SEC fee
        assert commission == pytest.approx(expected, rel=1e-3)

    def test_should_calculate_full_service_commission_with_base_and_per_share_fees(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.FULL_SERVICE)

        # Act
        commission = analyzer.calculate_commission_cost(5000.0, "AAPL", 50.0)

        # Assert
        # Base: $25 + Per share: 50 * $0.02 = $1 + Percentage: 5000 * 0.001 = $5 + SEC: 5000 * 0.0000221 = $0.11
        # Total: $25 + $1 + $5 + $0.11 = $31.11
        expected = 25.0 + (50.0 * 0.02) + (5000.0 * 0.001) + (5000.0 * 0.0000221)
        assert commission == pytest.approx(expected, rel=1e-3)

    def test_should_apply_maximum_commission_limit_when_exceeded(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.FULL_SERVICE)

        # Act
        commission = analyzer.calculate_commission_cost(100000.0, "AAPL", 1000.0)

        # Assert
        # Should be capped at maximum commission of $250
        assert commission <= 250.0

    def test_should_add_foreign_stock_fee_when_foreign_symbol(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.FULL_SERVICE)

        # Act
        commission = analyzer.calculate_commission_cost(1000.0, "ASML.AS", 10.0)

        # Assert
        # Should include $50 foreign stock fee
        base_commission = analyzer.calculate_commission_cost(1000.0, "AAPL", 10.0)
        assert commission == base_commission + 50.0

    def test_should_estimate_tight_spread_for_etf_symbols(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act
        spread_estimate = analyzer.estimate_bid_ask_spread("SPY", 10000.0)

        # Assert
        assert spread_estimate.symbol == "SPY"
        assert spread_estimate.estimated_spread_bps == approx(2.0)  # ETF should have 2 bps
        assert spread_estimate.estimated_spread_percentage == approx(0.0002)
        assert spread_estimate.estimated_spread_cost == approx(2.0)  # 10000 * 0.0002
        assert "ETF classification" in spread_estimate.factors_considered

    def test_should_estimate_wider_spread_for_small_cap_stocks(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act
        spread_estimate = analyzer.estimate_bid_ask_spread("SMALLCAP", 5000.0)

        # Assert
        assert spread_estimate.estimated_spread_bps == approx(15.0)  # Small cap should have 15 bps
        assert spread_estimate.estimated_spread_cost == approx(7.5)  # 5000 * 0.0015

    def test_should_adjust_spread_for_high_volatility_when_market_data_provided(self):
        # Arrange
        analyzer = CostAnalyzer()
        market_data = {
            "VOLATILE": {
                "volatility": 0.4,  # High volatility
                "avg_daily_volume": 500000,
            }
        }

        # Act
        spread_estimate = analyzer.estimate_bid_ask_spread("VOLATILE", 1000.0, market_data)

        # Assert
        # Base spread (15 bps for small cap) * 1.5 for high volatility = 22.5 bps
        assert spread_estimate.estimated_spread_bps == approx(22.5)
        assert "High volatility adjustment" in spread_estimate.factors_considered

    def test_should_estimate_negligible_market_impact_for_small_trades(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act
        impact_estimate = analyzer.estimate_market_impact("AAPL", 1000.0, 100000.0)

        # Assert
        assert impact_estimate.symbol == "AAPL"
        assert impact_estimate.estimated_impact_bps == approx(0.0)
        assert impact_estimate.impact_category == "NEGLIGIBLE"
        assert impact_estimate.estimated_impact_cost == approx(0.0)
        assert len(impact_estimate.mitigation_suggestions) == 0

    def test_should_estimate_moderate_market_impact_for_medium_trades(self):
        # Arrange
        analyzer = CostAnalyzer()
        market_data = {
            "AAPL": {
                "avg_daily_volume": 1000000,
                "price": 150.0,
                "market_cap": 3000000000000,  # $3T (large cap)
            }
        }

        # Act
        # Trade value of $1M against daily volume of $150M (1M shares * $150) = 0.67%
        impact_estimate = analyzer.estimate_market_impact("AAPL", 1000000.0, 10000000.0, market_data)

        # Assert
        assert impact_estimate.impact_category == "MODERATE"
        assert impact_estimate.estimated_impact_bps > 0
        assert len(impact_estimate.mitigation_suggestions) > 0
        assert "Consider splitting into smaller orders" in impact_estimate.mitigation_suggestions

    def test_should_estimate_severe_market_impact_for_large_trades(self):
        # Arrange
        analyzer = CostAnalyzer()
        market_data = {
            "SMALLCAP": {
                "avg_daily_volume": 10000,
                "price": 50.0,
                "market_cap": 500000000,  # $500M (small cap)
            }
        }

        # Act
        # Trade value of $500k against daily volume of $500k (10k shares * $50) = 100%
        impact_estimate = analyzer.estimate_market_impact("SMALLCAP", 500000.0, 1000000.0, market_data)

        # Assert
        assert impact_estimate.impact_category == "SEVERE"
        assert impact_estimate.estimated_impact_bps >= 20.0
        assert "Strongly consider splitting into multiple sessions" in impact_estimate.mitigation_suggestions

    def test_should_analyze_zero_costs_when_no_trade_recommendations(self):
        # Arrange
        analyzer = CostAnalyzer()
        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.5, "GOOGL": 0.5},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0},
        )
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=100),
                Holding(symbol="GOOGL", shares=20),
            ],
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )

        # Act
        cost_analysis = analyzer.analyze_transaction_costs([], portfolio, config)

        # Assert
        assert cost_analysis.total_transaction_costs == approx(0.0)
        assert cost_analysis.commission_costs == approx(0.0)
        assert cost_analysis.spread_costs == approx(0.0)
        assert cost_analysis.market_impact_costs == approx(0.0)
        assert cost_analysis.cost_as_percentage == approx(0.0)
        assert cost_analysis.break_even_days is None

    def test_should_analyze_comprehensive_costs_when_trade_recommendations_provided(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.COMMISSION_FREE)

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1500.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.4,
                target_weight=0.5,
                weight_deviation=-0.1,
                projected_weight_after_trade=0.5,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Rebalance to target allocation",
            ),
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.SELL,
                quantity=2.0,
                current_price=2500.0,
                trade_value=5000.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.6,
                target_weight=0.5,
                weight_deviation=0.1,
                projected_weight_after_trade=0.5,
                priority=2,
                urgency=UrgencyLevel.LOW,
                rationale="Rebalance to target allocation",
            ),
        ]

        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.6},
            deviations_from_target={"AAPL": -0.1, "GOOGL": 0.1},
        )

        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=40),
                Holding(symbol="GOOGL", shares=24),
            ],
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )

        # Act
        cost_analysis = analyzer.analyze_transaction_costs(trade_recommendations, portfolio, config)

        # Assert
        assert cost_analysis.total_transaction_costs > 0.0
        assert cost_analysis.commission_costs >= 0.0  # Should have regulatory fees
        assert cost_analysis.spread_costs > 0.0
        assert cost_analysis.market_impact_costs >= 0.0
        assert cost_analysis.cost_as_percentage > 0.0
        assert isinstance(cost_analysis.break_even_days, (int, type(None)))

    def test_should_perform_cost_benefit_analysis_with_proceed_recommendation_when_low_costs(self):
        # Arrange
        analyzer = CostAnalyzer()

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=1.0,
                current_price=150.0,
                trade_value=150.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.49,
                target_weight=0.5,
                weight_deviation=-0.01,
                projected_weight_after_trade=0.5,
                priority=1,
                urgency=UrgencyLevel.LOW,
                rationale="Minor rebalancing",
            ),
        ]

        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.49, "GOOGL": 0.51},
            deviations_from_target={"AAPL": -0.01, "GOOGL": 0.01},
        )

        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=326),
                Holding(symbol="GOOGL", shares=20),
            ],
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )

        # Act
        cost_benefit = analyzer.perform_cost_benefit_analysis(50.0, trade_recommendations, portfolio, config)

        # Assert
        assert cost_benefit.total_rebalancing_cost == approx(50.0)
        assert cost_benefit.cost_as_percentage_of_portfolio == approx(0.05)  # 50/100000 * 100
        assert cost_benefit.recommendation == "PROCEED"
        assert "reasonable" in cost_benefit.rationale.lower()

    def test_should_perform_cost_benefit_analysis_with_reject_recommendation_when_high_costs(self):
        # Arrange
        analyzer = CostAnalyzer()

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=100.0,
                current_price=150.0,
                trade_value=15000.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.4,
                target_weight=0.5,
                weight_deviation=-0.1,
                projected_weight_after_trade=0.5,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Large rebalancing",
            ),
        ]

        portfolio = PortfolioAnalysis(
            total_value=50000.0,  # Small portfolio
            weightings={"AAPL": 0.4, "GOOGL": 0.6},
            deviations_from_target={"AAPL": -0.1, "GOOGL": 0.1},
        )

        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=133),
                Holding(symbol="GOOGL", shares=12),
            ],
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
        )

        # Act
        # High cost: $2000 on $50k portfolio = 4%
        cost_benefit = analyzer.perform_cost_benefit_analysis(2000.0, trade_recommendations, portfolio, config)

        # Assert
        assert cost_benefit.cost_as_percentage_of_portfolio == approx(4.0)
        assert cost_benefit.recommendation == "REJECT"
        assert "excessive" in cost_benefit.rationale.lower()

    def test_should_generate_alternative_approaches_when_costs_are_high(self):
        # Arrange
        analyzer = CostAnalyzer()

        many_trades = [
            TradeRecommendation(
                symbol=f"STOCK{i}",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=100.0,
                trade_value=1000.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.05,
                target_weight=0.1,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.1,
                priority=i,
                urgency=UrgencyLevel.MEDIUM,
                rationale=f"Rebalance {f'STOCK{i}'}",
            )
            for i in range(1, 8)  # 7 trades
        ]

        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={f"STOCK{i}": 0.14 for i in range(1, 8)},  # 7 * 0.14 = 0.98 ≈ 1.0
            deviations_from_target={f"STOCK{i}": -0.05 for i in range(1, 8)},
        )

        config = PortfolioConfiguration(
            holdings=[Holding(symbol=f"STOCK{i}", shares=50) for i in range(1, 8)],
            target_weights={f"STOCK{i}": 0.1 for i in range(1, 8)},
        )

        # Act
        cost_benefit = analyzer.perform_cost_benefit_analysis(1500.0, many_trades, portfolio, config)

        # Assert
        assert len(cost_benefit.alternative_approaches) > 0
        alternatives_text = " ".join(cost_benefit.alternative_approaches)
        assert "new contributions" in alternatives_text.lower()
        assert "split rebalancing" in alternatives_text.lower()

    def test_should_identify_etf_symbols_correctly(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act & Assert
        assert analyzer._is_etf("SPY") is True
        assert analyzer._is_etf("VTI") is True
        assert analyzer._is_etf("QQQ") is True
        assert analyzer._is_etf("SPYETF") is True
        assert analyzer._is_etf("AAPL") is False
        assert analyzer._is_etf("GOOGL") is False

    def test_should_identify_foreign_stocks_correctly(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act & Assert
        assert analyzer._is_foreign_stock("ASML.AS") is True
        assert analyzer._is_foreign_stock("NESN.SW") is True
        assert analyzer._is_foreign_stock("LONGNAME") is True
        assert analyzer._is_foreign_stock("STOCKF") is True
        assert analyzer._is_foreign_stock("AAPL") is False
        assert analyzer._is_foreign_stock("MSFT") is False

    def test_should_identify_large_cap_stocks_correctly(self):
        # Arrange
        analyzer = CostAnalyzer()
        market_data = {
            "LARGECAP": {"market_cap": 50000000000},  # $50B
            "SMALLCAP": {"market_cap": 1000000000},  # $1B
        }

        # Act & Assert
        assert analyzer._is_large_cap("LARGECAP", market_data) is True
        assert analyzer._is_large_cap("SMALLCAP", market_data) is False
        assert analyzer._is_large_cap("AAPL", None) is True  # Fallback heuristic
        assert analyzer._is_large_cap("UNKNOWN", None) is False

    def test_should_estimate_daily_volume_value_from_market_data(self):
        # Arrange
        analyzer = CostAnalyzer()
        market_data = {
            "AAPL": {
                "avg_daily_volume": 1000000,
                "price": 150.0,
            }
        }

        # Act
        volume_value = analyzer._estimate_avg_daily_volume_value("AAPL", market_data)

        # Assert
        assert volume_value == approx(150000000.0)  # 1M shares * $150

    def test_should_use_fallback_volume_estimates_when_no_market_data(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act
        large_cap_volume = analyzer._estimate_avg_daily_volume_value("AAPL", None)
        small_cap_volume = analyzer._estimate_avg_daily_volume_value("SMALLCAP", None)

        # Assert
        assert large_cap_volume == approx(100000000.0)  # $100M for large cap
        assert small_cap_volume == approx(5000000.0)  # $5M for small cap

    def test_should_handle_edge_case_with_zero_trade_value(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Act
        commission = analyzer.calculate_commission_cost(0.0, "AAPL", 0.0)
        spread_estimate = analyzer.estimate_bid_ask_spread("AAPL", 0.0)
        impact_estimate = analyzer.estimate_market_impact("AAPL", 0.0, 100000.0)

        # Assert
        assert commission >= 0.0
        assert spread_estimate.estimated_spread_cost == approx(0.0)
        assert impact_estimate.estimated_impact_cost == approx(0.0)

    def test_should_handle_edge_case_with_very_large_trade_value(self):
        # Arrange
        analyzer = CostAnalyzer(BrokerType.FULL_SERVICE)

        # Act
        commission = analyzer.calculate_commission_cost(10000000.0, "AAPL", 100000.0)

        # Assert
        # Calculate expected: base(25) + per_share(100000*0.02=2000) + percentage(10M*0.001=10000) + SEC(10M*0.0000221=221)
        # Total would be 12246, but capped at 250
        # However, the regulatory fees are added after the cap, so: 250 + 221 = 471
        expected_max = 250.0 + (10000000.0 * 0.0000221)  # Max commission + regulatory fees
        assert commission == pytest.approx(expected_max, rel=1e-3)

    def test_should_calculate_break_even_correctly_when_benefit_exists(self):
        # Arrange
        analyzer = CostAnalyzer()

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1500.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.3,
                target_weight=0.5,
                weight_deviation=-0.2,  # Large deviation
                projected_weight_after_trade=0.5,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Large rebalancing needed",
            ),
        ]

        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.3, "GOOGL": 0.7},
            deviations_from_target={"AAPL": -0.2, "GOOGL": 0.2},
        )

        # Act
        break_even_days = analyzer._calculate_break_even_days(365.0, trade_recommendations, portfolio)

        # Assert
        assert isinstance(break_even_days, int)
        assert break_even_days > 0

    def test_should_return_none_break_even_when_no_benefit(self):
        # Arrange
        analyzer = CostAnalyzer()

        # Create a trade with zero deviation (no benefit)
        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.HOLD,  # HOLD action should result in no benefit
                quantity=0.0,
                current_price=150.0,
                trade_value=0.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.5,
                target_weight=0.5,
                weight_deviation=0.0,  # No deviation
                projected_weight_after_trade=0.5,
                priority=1,
                urgency=UrgencyLevel.LOW,
                rationale="No rebalancing needed",
            ),
        ]

        portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.5, "GOOGL": 0.5},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0},
        )

        # Act
        break_even_days = analyzer._calculate_break_even_days(1000.0, trade_recommendations, portfolio)

        # Assert
        assert break_even_days is None
