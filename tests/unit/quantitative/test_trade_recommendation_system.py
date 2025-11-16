"""
Unit tests for the trade recommendation system.

Tests priority scoring, quantity calculations, cost estimation,
rationale generation, and trade validation.
"""

import pytest

from finwiz.quantitative.cost_analyzer import BrokerType
from finwiz.quantitative.trade_recommendation_system import (
    PriorityScore,
    TradeCalculationResult,
    TradeRecommendationSystem,
)
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    RebalancingMethod,
    RebalancingNeed,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


class TestTradeRecommendationSystem:
    """Test suite for TradeRecommendationSystem."""

    @pytest.fixture
    def trade_system(self):
        """Create trade recommendation system instance."""
        return TradeRecommendationSystem(BrokerType.COMMISSION_FREE)

    @pytest.fixture
    def sample_portfolio_config(self):
        """Create sample portfolio configuration."""
        return PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=100.0, cost_basis=150.0),
                Holding(symbol="GOOGL", shares=10.0, cost_basis=2000.0),
                Holding(symbol="MSFT", shares=50.0, cost_basis=250.0),
            ],
            target_weights={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
            tolerance_bands={"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05},
            global_tolerance=0.05,
            available_capital=10000.0,  # Increased to handle trade costs
            transaction_cost_rate=0.001,
            min_trade_size=100.0,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
        )

    @pytest.fixture
    def sample_portfolio_analysis(self):
        """Create sample portfolio analysis."""
        return PortfolioAnalysis(
            total_value=50000.0,
            weightings={"AAPL": 0.3, "GOOGL": 0.4, "MSFT": 0.3},
            deviations_from_target={"AAPL": -0.1, "GOOGL": 0.1, "MSFT": 0.0},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
            risk_metrics={"concentration_risk": 6.0},
        )

    @pytest.fixture
    def sample_rebalancing_needs(self):
        """Create sample rebalancing needs."""
        return [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.3,
                target_weight=0.4,
                deviation=-0.1,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.4,
                target_weight=0.3,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.7,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="MSFT",
                current_weight=0.3,
                target_weight=0.3,
                deviation=0.0,
                tolerance_band=0.05,
                urgency_score=0.1,
                needs_rebalancing=True,
            ),
        ]

    @pytest.fixture
    def sample_prices(self):
        """Create sample price data."""
        return {"AAPL": 150.0, "GOOGL": 2000.0, "MSFT": 250.0}

    def test_should_generate_trade_recommendations_when_valid_inputs_provided(
        self, trade_system, sample_rebalancing_needs, sample_portfolio_analysis, sample_prices, sample_portfolio_config
    ):
        """Test basic trade recommendation generation."""
        # Act
        recommendations = trade_system.generate_trade_recommendations(
            rebalancing_needs=sample_rebalancing_needs,
            current_portfolio=sample_portfolio_analysis,
            target_weights=sample_portfolio_config.target_weights,
            prices=sample_prices,
            config=sample_portfolio_config,
            holdings=sample_portfolio_config.holdings,
        )

        # Assert
        assert len(recommendations) == 2  # Only AAPL and GOOGL need rebalancing

        # Check AAPL buy recommendation
        aapl_rec = next(r for r in recommendations if r.symbol == "AAPL")
        assert aapl_rec.action == TradeAction.BUY
        assert aapl_rec.quantity > 0
        assert aapl_rec.current_weight == 0.3
        assert aapl_rec.target_weight == 0.4
        assert aapl_rec.priority in [1, 2]
        assert len(aapl_rec.rationale) >= 10

        # Check GOOGL sell recommendation
        googl_rec = next(r for r in recommendations if r.symbol == "GOOGL")
        assert googl_rec.action == TradeAction.SELL
        assert googl_rec.quantity > 0
        assert googl_rec.current_weight == 0.4
        assert googl_rec.target_weight == 0.3
        assert googl_rec.priority in [1, 2]
        assert len(googl_rec.rationale) >= 10

    def test_should_return_empty_list_when_no_rebalancing_needed(self, trade_system, sample_portfolio_analysis, sample_prices, sample_portfolio_config):
        """Test that no recommendations are generated when no rebalancing is needed."""
        # Arrange - create needs with no positions exceeding tolerance
        no_rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.4,
                target_weight=0.4,
                deviation=0.0,
                tolerance_band=0.05,
                urgency_score=0.1,
                needs_rebalancing=True,
            )
        ]

        # Act
        recommendations = trade_system.generate_trade_recommendations(
            rebalancing_needs=no_rebalancing_needs,
            current_portfolio=sample_portfolio_analysis,
            target_weights=sample_portfolio_config.target_weights,
            prices=sample_prices,
            config=sample_portfolio_config,
            holdings=sample_portfolio_config.holdings,
        )

        # Assert
        assert len(recommendations) == 0

    def test_should_calculate_correct_trade_quantities_for_fractional_shares(self, trade_system, sample_portfolio_analysis, sample_prices, sample_portfolio_config):
        """Test fractional share quantity calculations."""
        # Arrange
        need = RebalancingNeed(
            symbol="AAPL",
            current_weight=0.3,
            target_weight=0.4,
            deviation=-0.1,
            tolerance_band=0.05,
            urgency_score=0.8,
                needs_rebalancing=True,
        )

        # Use higher capital config to avoid validation errors
        high_capital_config = sample_portfolio_config.model_copy()
        high_capital_config.available_capital = 20000.0

        # Act
        calculation = trade_system._calculate_trade_details(need, sample_portfolio_analysis, sample_prices, high_capital_config, high_capital_config.holdings)

        # Assert
        assert calculation.is_valid
        assert calculation.action == TradeAction.BUY

        # Expected trade value: (0.4 - 0.3) * 50000 = 5000
        expected_trade_value = 5000.0
        expected_quantity = expected_trade_value / 150.0  # Price of AAPL

        assert abs(calculation.trade_value - expected_trade_value) < 1.0
        assert abs(calculation.quantity - expected_quantity) < 0.01
        assert calculation.fractional_quantity == calculation.quantity

    def test_should_use_cost_analyzer_for_cost_calculations(self, trade_system):
        """Test that the system uses CostAnalyzer for cost calculations."""
        # Assert that the trade system has a cost analyzer
        assert hasattr(trade_system, "cost_analyzer")
        assert trade_system.cost_analyzer.broker_type == BrokerType.COMMISSION_FREE

    def test_should_assign_priority_scores_correctly(self, trade_system, sample_portfolio_analysis, sample_portfolio_config):
        """Test priority score calculation."""
        # Arrange
        calculations = [
            TradeCalculationResult(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=33.33,
                fractional_quantity=33.33,
                trade_value=5000.0,
                commission_cost=5.0,
                spread_cost=2.5,
                market_impact_cost=0.0,
                total_cost=7.5,
                is_valid=True,
                validation_errors=[],
            ),
            TradeCalculationResult(
                symbol="GOOGL",
                action=TradeAction.SELL,
                quantity=2.5,
                fractional_quantity=2.5,
                trade_value=5000.0,
                commission_cost=5.0,
                spread_cost=2.5,
                market_impact_cost=0.0,
                total_cost=7.5,
                is_valid=True,
                validation_errors=[],
            ),
        ]

        needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.3,
                target_weight=0.4,
                deviation=-0.1,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.4,
                target_weight=0.3,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.6,
                needs_rebalancing=True,
            ),
        ]

        # Act
        priority_scores = trade_system._calculate_priority_scores(calculations, needs, sample_portfolio_analysis, sample_portfolio_config)

        # Assert
        assert len(priority_scores) == 2

        # AAPL should have higher priority due to higher urgency score
        aapl_priority = priority_scores[0]  # First calculation is AAPL
        googl_priority = priority_scores[1]  # Second calculation is GOOGL

        assert aapl_priority.urgency_score == 0.8
        assert googl_priority.urgency_score == 0.6
        assert aapl_priority.overall_priority > googl_priority.overall_priority

        # Check that priority ranks are assigned (1 = highest)
        assert aapl_priority.priority_rank == 1
        assert googl_priority.priority_rank == 2

    def test_should_generate_appropriate_rationale_for_trades(self, trade_system):
        """Test trade rationale generation."""
        # Arrange
        calculation = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=33.33,
            fractional_quantity=33.33,
            trade_value=5000.0,
            commission_cost=5.0,
            spread_cost=2.5,
            market_impact_cost=0.0,
            total_cost=7.5,
            is_valid=True,
            validation_errors=[],
        )

        priority = PriorityScore(
            urgency_score=0.8,
            deviation_score=0.7,
            risk_score=0.6,
            cost_efficiency_score=0.9,
            overall_priority=0.75,
            priority_rank=1,
        )

        # Act
        rationale = trade_system._generate_trade_rationale("AAPL", calculation, 0.3, 0.4, priority)

        # Assert
        assert len(rationale) >= 10
        assert "AAPL" in rationale
        assert "Buy" in rationale
        assert "33.33" in rationale
        assert "30.0%" in rationale or "0.3" in rationale
        assert "40.0%" in rationale or "0.4" in rationale
        assert "High urgency" in rationale  # Due to urgency_score >= 0.7

    def test_should_determine_urgency_levels_correctly(self, trade_system):
        """Test urgency level determination from scores."""
        assert trade_system._determine_urgency_level(0.9) == UrgencyLevel.CRITICAL
        assert trade_system._determine_urgency_level(0.7) == UrgencyLevel.HIGH
        assert trade_system._determine_urgency_level(0.5) == UrgencyLevel.MEDIUM
        assert trade_system._determine_urgency_level(0.2) == UrgencyLevel.LOW

    def test_should_assess_tax_implications_for_large_sales(self, trade_system, sample_portfolio_config):
        """Test tax implications assessment."""
        # Large sale
        large_sale = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.SELL,
            quantity=100.0,
            fractional_quantity=100.0,
            trade_value=10000.0,
            commission_cost=10.0,
            spread_cost=5.0,
            market_impact_cost=0.0,
            total_cost=15.0,
            is_valid=True,
            validation_errors=[],
        )

        tax_implications = trade_system._assess_tax_implications(large_sale, sample_portfolio_config)
        assert tax_implications is not None
        assert "capital gains" in tax_implications.lower()

        # Small sale
        small_sale = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.SELL,
            quantity=5.0,
            fractional_quantity=5.0,
            trade_value=500.0,
            commission_cost=1.0,
            spread_cost=0.5,
            market_impact_cost=0.0,
            total_cost=1.5,
            is_valid=True,
            validation_errors=[],
        )

        small_tax_implications = trade_system._assess_tax_implications(small_sale, sample_portfolio_config)
        assert small_tax_implications is None

        # Buy order
        buy_order = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=10.0,
            fractional_quantity=10.0,
            trade_value=1500.0,
            commission_cost=2.0,
            spread_cost=1.0,
            market_impact_cost=0.0,
            total_cost=3.0,
            is_valid=True,
            validation_errors=[],
        )

        buy_tax_implications = trade_system._assess_tax_implications(buy_order, sample_portfolio_config)
        assert buy_tax_implications is None

    def test_should_assess_market_impact_warnings(self, trade_system, sample_portfolio_analysis):
        """Test market impact warning assessment."""
        # Large trade (15% of portfolio)
        large_trade = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=100.0,
            fractional_quantity=100.0,
            trade_value=7500.0,  # 15% of 50k portfolio
            commission_cost=7.5,
            spread_cost=3.75,
            market_impact_cost=15.0,
            total_cost=26.25,
            is_valid=True,
            validation_errors=[],
        )

        warning = trade_system._assess_market_impact_warning(large_trade, sample_portfolio_analysis)
        assert warning is not None
        assert "Large trade" in warning

        # Small trade (1% of portfolio)
        small_trade = TradeCalculationResult(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=3.33,
            fractional_quantity=3.33,
            trade_value=500.0,  # 1% of 50k portfolio
            commission_cost=1.0,
            spread_cost=0.5,
            market_impact_cost=0.0,
            total_cost=1.5,
            is_valid=True,
            validation_errors=[],
        )

        small_warning = trade_system._assess_market_impact_warning(small_trade, sample_portfolio_analysis)
        assert small_warning is None

    def test_should_validate_trade_recommendations_correctly(self, trade_system, sample_portfolio_config):
        """Test trade recommendation validation."""
        # Valid recommendation
        valid_rec = TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=10.0,
            current_price=150.0,
            trade_value=1500.0,
            estimated_commission=2.0,
            estimated_spread_cost=1.0,
            total_estimated_cost=3.0,
            current_weight=0.3,
            target_weight=0.4,
            weight_deviation=-0.1,
            projected_weight_after_trade=0.35,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Buy AAPL to rebalance portfolio",
        )

        # Create invalid recommendation manually (bypassing Pydantic validation)
        invalid_rec = TradeRecommendation.model_construct(
            symbol="GOOGL",
            action=TradeAction.BUY,
            quantity=-5.0,  # Invalid
            current_price=2000.0,
            trade_value=10000.0,
            estimated_commission=10.0,
            estimated_spread_cost=5.0,
            total_estimated_cost=15.0,
            current_weight=0.4,
            target_weight=0.3,
            weight_deviation=0.1,
            projected_weight_after_trade=0.35,
            priority=2,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Sell GOOGL to rebalance portfolio",
        )

        # Act
        valid_recs, errors = trade_system.validate_trade_recommendations([valid_rec, invalid_rec], sample_portfolio_config)

        # Assert
        assert len(valid_recs) == 1
        assert valid_recs[0].symbol == "AAPL"
        assert len(errors) > 0
        assert any("GOOGL" in error and "quantity" in error for error in errors)

    def test_should_handle_insufficient_capital_validation(self, trade_system, sample_portfolio_config):
        """Test validation of capital constraints."""
        # Create config with limited capital
        limited_config = sample_portfolio_config.model_copy()
        limited_config.available_capital = 1000.0

        # Create recommendation requiring more capital than available
        expensive_rec = TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=20.0,
            current_price=150.0,
            trade_value=3000.0,  # Exceeds available capital
            estimated_commission=3.0,
            estimated_spread_cost=1.5,
            total_estimated_cost=4.5,
            current_weight=0.3,
            target_weight=0.4,
            weight_deviation=-0.1,
            projected_weight_after_trade=0.35,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Buy AAPL to rebalance portfolio",
        )

        # Act
        valid_recs, errors = trade_system.validate_trade_recommendations([expensive_rec], limited_config)

        # Assert
        assert len(valid_recs) == 0
        assert len(errors) > 0
        assert any("capital" in error.lower() for error in errors)

    def test_should_handle_invalid_price_data_gracefully(self, trade_system, sample_rebalancing_needs, sample_portfolio_analysis, sample_portfolio_config):
        """Test handling of invalid or missing price data."""
        # Arrange - prices with invalid data
        invalid_prices = {"AAPL": 0.0, "GOOGL": -100.0, "MSFT": 250.0}

        # Act
        recommendations = trade_system.generate_trade_recommendations(
            rebalancing_needs=sample_rebalancing_needs,
            current_portfolio=sample_portfolio_analysis,
            target_weights=sample_portfolio_config.target_weights,
            prices=invalid_prices,
            config=sample_portfolio_config,
            holdings=sample_portfolio_config.holdings,
        )

        # Assert - should only generate recommendations for valid prices
        assert len(recommendations) == 0  # MSFT doesn't exceed tolerance

        # Test with some valid prices - use higher capital to avoid validation errors
        high_capital_config = sample_portfolio_config.model_copy()
        high_capital_config.available_capital = 20000.0

        partial_prices = {"AAPL": 150.0, "GOOGL": 0.0, "MSFT": 250.0}
        partial_recommendations = trade_system.generate_trade_recommendations(
            rebalancing_needs=sample_rebalancing_needs,
            current_portfolio=sample_portfolio_analysis,
            target_weights=high_capital_config.target_weights,
            prices=partial_prices,
            config=high_capital_config,
            holdings=high_capital_config.holdings,
        )

        # Should only get AAPL recommendation
        assert len(partial_recommendations) == 1
        assert partial_recommendations[0].symbol == "AAPL"

    def test_should_handle_minimum_trade_size_constraint(self, trade_system, sample_portfolio_analysis, sample_portfolio_config):
        """Test minimum trade size constraint handling."""
        # Arrange - create a need that results in very small trade
        small_need = RebalancingNeed(
            symbol="AAPL",
            current_weight=0.399,  # Very close to target
            target_weight=0.4,
            deviation=-0.001,  # Tiny deviation
            tolerance_band=0.05,  # Force it to be considered
            urgency_score=0.5,
                needs_rebalancing=True,
        )

        prices = {"AAPL": 150.0}

        # Act
        calculation = trade_system._calculate_trade_details(small_need, sample_portfolio_analysis, prices, sample_portfolio_config, sample_portfolio_config.holdings)

        # Assert - should be invalid due to minimum trade size
        assert not calculation.is_valid
        assert any("minimum" in error.lower() for error in calculation.validation_errors)
