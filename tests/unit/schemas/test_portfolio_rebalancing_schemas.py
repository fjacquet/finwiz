"""
Unit tests for portfolio rebalancing schemas.

Tests all validation rules, edge cases, and error conditions for the
portfolio rebalancing Pydantic models.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from finwiz.schemas.portfolio_rebalancing import (
    CostAnalysis,
    ExecutionSummary,
    Holding,
    PortfolioAnalysis,
    PortfolioConfiguration,
    PortfolioMetrics,
    PriceData,
    RebalancingMethod,
    RebalancingNeed,
    RebalancingRecommendation,
    RebalancingResult,
    TradeAction,
    TradeRecommendation,
    UrgencyLevel,
)


class TestHolding:
    """Test cases for Holding schema."""

    def test_should_create_valid_holding_when_all_fields_provided(self):
        # Arrange & Act
        holding = Holding(symbol="AAPL", shares=100.0, cost_basis=150.0, acquisition_date=datetime(2023, 1, 1))

        # Assert
        assert holding.symbol == "AAPL"
        assert holding.shares == 100.0
        assert holding.cost_basis == 150.0
        assert holding.acquisition_date == datetime(2023, 1, 1)

    def test_should_create_valid_holding_when_optional_fields_omitted(self):
        # Arrange & Act
        holding = Holding(symbol="MSFT", shares=50.0)

        # Assert
        assert holding.symbol == "MSFT"
        assert holding.shares == 50.0
        assert holding.cost_basis is None
        assert holding.acquisition_date is None

    def test_should_uppercase_symbol_when_lowercase_provided(self):
        # Arrange & Act
        holding = Holding(symbol="aapl", shares=100.0)

        # Assert
        assert holding.symbol == "AAPL"

    def test_should_accept_symbol_with_hyphens_and_periods(self):
        # Arrange & Act
        holding = Holding(symbol="BRK-B", shares=10.0)

        # Assert
        assert holding.symbol == "BRK-B"

    def test_should_raise_error_when_symbol_empty(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="", shares=100.0)

        assert "String should have at least 1 character" in str(exc_info.value)

    def test_should_raise_error_when_symbol_too_long(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="VERYLONGSYMBOL", shares=100.0)

        assert "String should have at most 10 characters" in str(exc_info.value)

    def test_should_raise_error_when_symbol_contains_invalid_characters(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="AAP@L", shares=100.0)

        assert "Symbol must contain only alphanumeric characters" in str(exc_info.value)

    def test_should_raise_error_when_shares_zero(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="AAPL", shares=0.0)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_should_raise_error_when_shares_negative(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="AAPL", shares=-10.0)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_should_raise_error_when_cost_basis_zero(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="AAPL", shares=100.0, cost_basis=0.0)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_should_raise_error_when_cost_basis_negative(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Holding(symbol="AAPL", shares=100.0, cost_basis=-50.0)

        assert "Input should be greater than 0" in str(exc_info.value)


class TestPortfolioConfiguration:
    """Test cases for PortfolioConfiguration schema."""

    def test_should_create_valid_configuration_when_all_fields_provided(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0), Holding(symbol="GOOGL", shares=10.0), Holding(symbol="MSFT", shares=50.0)]
        target_weights = {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3}
        tolerance_bands = {"AAPL": 0.05, "GOOGL": 0.03}

        # Act
        config = PortfolioConfiguration(
            holdings=holdings,
            target_weights=target_weights,
            tolerance_bands=tolerance_bands,
            global_tolerance=0.04,
            available_capital=1000.0,
            transaction_cost_rate=0.002,
            min_trade_size=0.1,
            rebalancing_method=RebalancingMethod.MINIMIZE_COSTS,
        )

        # Assert
        assert len(config.holdings) == 3
        assert config.target_weights == target_weights
        assert config.tolerance_bands == tolerance_bands
        assert config.global_tolerance == 0.04
        assert config.available_capital == 1000.0
        assert config.transaction_cost_rate == 0.002
        assert config.min_trade_size == 0.1
        assert config.rebalancing_method == RebalancingMethod.MINIMIZE_COSTS

    def test_should_create_valid_configuration_with_defaults(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}

        # Act
        config = PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        # Assert
        assert config.global_tolerance == 0.05
        assert config.available_capital == 0.0
        assert config.transaction_cost_rate == 0.001
        assert config.min_trade_size == 0.01
        assert config.rebalancing_method == RebalancingMethod.MINIMIZE_TRADES
        assert config.tolerance_bands == {}

    def test_should_raise_error_when_holdings_empty(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=[], target_weights={})

        assert "List should have at least 1 item" in str(exc_info.value)

    def test_should_raise_error_when_target_weight_negative(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": -0.1}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        assert "Target weight for AAPL must be between 0.0 and 1.0" in str(exc_info.value)

    def test_should_raise_error_when_target_weight_exceeds_one(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.5}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        assert "Target weight for AAPL must be between 0.0 and 1.0" in str(exc_info.value)

    def test_should_raise_error_when_tolerance_band_too_small(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}
        tolerance_bands = {"AAPL": 0.0005}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights, tolerance_bands=tolerance_bands)

        assert "Tolerance for AAPL must be between 0.1% and 50%" in str(exc_info.value)

    def test_should_raise_error_when_tolerance_band_too_large(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}
        tolerance_bands = {"AAPL": 0.6}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights, tolerance_bands=tolerance_bands)

        assert "Tolerance for AAPL must be between 0.1% and 50%" in str(exc_info.value)

    def test_should_raise_error_when_target_weights_sum_exceeds_one(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0), Holding(symbol="GOOGL", shares=10.0)]
        target_weights = {"AAPL": 0.7, "GOOGL": 0.5}  # Sum = 1.2

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        assert "Target weights sum to 120.0%, must be ≤ 100%" in str(exc_info.value)

    def test_should_raise_error_when_missing_target_weight_for_holding(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0), Holding(symbol="GOOGL", shares=10.0)]
        target_weights = {"AAPL": 0.5}  # Missing GOOGL

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        assert "Missing target weights for holdings: GOOGL" in str(exc_info.value)

    def test_should_raise_error_when_target_weight_for_non_held_symbol(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}  # GOOGL not held

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights)

        assert "Target weights specified for non-held symbols: GOOGL" in str(exc_info.value)

    def test_should_raise_error_when_tolerance_band_for_invalid_symbol(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}
        tolerance_bands = {"GOOGL": 0.05}  # GOOGL not in targets

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights, tolerance_bands=tolerance_bands)

        assert "Tolerance bands specified for invalid symbols: GOOGL" in str(exc_info.value)

    def test_should_raise_error_when_global_tolerance_zero(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights, global_tolerance=0.0)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_should_raise_error_when_global_tolerance_too_large(self):
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioConfiguration(holdings=holdings, target_weights=target_weights, global_tolerance=0.6)

        assert "Input should be less than or equal to 0.5" in str(exc_info.value)


class TestTradeRecommendation:
    """Test cases for TradeRecommendation schema."""

    def test_should_create_valid_buy_recommendation(self):
        # Arrange & Act
        trade = TradeRecommendation(
            symbol="AAPL",
            action=TradeAction.BUY,
            quantity=10.0,
            current_price=150.0,
            trade_value=1500.0,
            estimated_commission=1.0,
            estimated_spread_cost=0.5,
            total_estimated_cost=1.5,
            current_weight=0.25,
            target_weight=0.30,
            weight_deviation=-0.05,
            projected_weight_after_trade=0.30,
            priority=1,
            urgency=UrgencyLevel.HIGH,
            rationale="Position is underweighted and showing strong momentum",
        )

        # Assert
        assert trade.symbol == "AAPL"
        assert trade.action == TradeAction.BUY
        assert trade.quantity == 10.0
        assert trade.current_price == 150.0
        assert trade.trade_value == 1500.0
        assert trade.total_estimated_cost == 1.5

    def test_should_create_valid_sell_recommendation(self):
        # Arrange & Act
        trade = TradeRecommendation(
            symbol="GOOGL",
            action=TradeAction.SELL,
            quantity=5.0,
            current_price=2500.0,
            trade_value=12500.0,
            estimated_commission=2.0,
            estimated_spread_cost=1.0,
            total_estimated_cost=3.0,
            current_weight=0.40,
            target_weight=0.30,
            weight_deviation=0.10,
            projected_weight_after_trade=0.30,
            priority=2,
            urgency=UrgencyLevel.MEDIUM,
            rationale="Position is overweighted relative to target allocation",
        )

        # Assert
        assert trade.action == TradeAction.SELL
        assert trade.quantity == 5.0
        assert trade.weight_deviation == 0.10

    def test_should_create_valid_hold_recommendation(self):
        # Arrange & Act
        trade = TradeRecommendation(
            symbol="MSFT",
            action=TradeAction.HOLD,
            quantity=0.0,
            current_price=300.0,
            trade_value=0.0,
            estimated_commission=0.0,
            estimated_spread_cost=0.0,
            total_estimated_cost=0.0,
            current_weight=0.25,
            target_weight=0.25,
            weight_deviation=0.0,
            projected_weight_after_trade=0.25,
            priority=10,
            urgency=UrgencyLevel.LOW,
            rationale="Position is within tolerance band",
        )

        # Assert
        assert trade.action == TradeAction.HOLD
        assert trade.quantity == 0.0
        assert trade.trade_value == 0.0

    def test_should_raise_error_when_trade_value_inconsistent(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1000.0,  # Should be 1500.0
                estimated_commission=1.0,
                estimated_spread_cost=0.5,
                total_estimated_cost=1.5,
                current_weight=0.25,
                target_weight=0.30,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Test rationale",
            )

        assert "Trade value 1000.0 doesn't match quantity × price 1500.0" in str(exc_info.value)

    def test_should_raise_error_when_total_cost_inconsistent(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1500.0,
                estimated_commission=1.0,
                estimated_spread_cost=0.5,
                total_estimated_cost=2.0,  # Should be 1.5
                current_weight=0.25,
                target_weight=0.30,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Test rationale",
            )

        assert "Total cost 2.0 doesn't match sum of components 1.5" in str(exc_info.value)

    def test_should_raise_error_when_buy_action_with_zero_quantity(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=0.0,  # Invalid for BUY
                current_price=150.0,
                trade_value=0.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.25,
                target_weight=0.30,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Test rationale",
            )

        assert "BUY action requires positive quantity" in str(exc_info.value)

    def test_should_raise_error_when_sell_action_with_negative_quantity(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=-5.0,  # Invalid for SELL
                current_price=150.0,
                trade_value=750.0,
                estimated_commission=1.0,
                estimated_spread_cost=0.5,
                total_estimated_cost=1.5,
                current_weight=0.25,
                target_weight=0.30,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Test rationale",
            )

        assert "SELL action requires positive quantity" in str(exc_info.value)

    def test_should_raise_error_when_hold_action_with_nonzero_quantity(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.HOLD,
                quantity=5.0,  # Invalid for HOLD
                current_price=150.0,
                trade_value=750.0,
                estimated_commission=0.0,
                estimated_spread_cost=0.0,
                total_estimated_cost=0.0,
                current_weight=0.25,
                target_weight=0.25,
                weight_deviation=0.0,
                projected_weight_after_trade=0.25,
                priority=10,
                urgency=UrgencyLevel.LOW,
                rationale="Test rationale",
            )

        assert "HOLD action should have zero quantity" in str(exc_info.value)

    def test_should_raise_error_when_rationale_too_short(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1500.0,
                estimated_commission=1.0,
                estimated_spread_cost=0.5,
                total_estimated_cost=1.5,
                current_weight=0.25,
                target_weight=0.30,
                weight_deviation=-0.05,
                projected_weight_after_trade=0.30,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Short",  # Too short
            )

        assert "String should have at least 10 characters" in str(exc_info.value)


class TestPortfolioAnalysis:
    """Test cases for PortfolioAnalysis schema."""

    def test_should_create_valid_portfolio_analysis(self):
        # Arrange & Act
        analysis = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.02, "MSFT": -0.03},
            positions_needing_rebalancing=["AAPL"],
            risk_metrics={"portfolio_beta": 1.2, "sharpe_ratio": 0.8},
        )

        # Assert
        assert analysis.total_value == 100000.0
        assert len(analysis.weightings) == 3
        assert analysis.positions_needing_rebalancing == ["AAPL"]

    def test_should_raise_error_when_weightings_sum_too_low(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysis(
                total_value=100000.0,
                weightings={"AAPL": 0.3, "GOOGL": 0.2, "MSFT": 0.2},  # Sum = 0.7
                deviations_from_target={"AAPL": 0.05, "GOOGL": -0.02, "MSFT": -0.03},
            )

        assert "Portfolio weightings sum to 0.700, should be close to 1.0" in str(exc_info.value)

    def test_should_raise_error_when_weightings_sum_too_high(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PortfolioAnalysis(
                total_value=100000.0,
                weightings={"AAPL": 0.5, "GOOGL": 0.4, "MSFT": 0.4},  # Sum = 1.3
                deviations_from_target={"AAPL": 0.05, "GOOGL": -0.02, "MSFT": -0.03},
            )

        assert "Portfolio weightings sum to 1.300, should be close to 1.0" in str(exc_info.value)


class TestRebalancingResult:
    """Test cases for RebalancingResult schema."""

    def test_should_create_valid_rebalancing_result(self):
        # Arrange
        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.02, "MSFT": -0.03},
        )

        projected_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.35, "GOOGL": 0.32, "MSFT": 0.33},
            deviations_from_target={"AAPL": 0.0, "GOOGL": 0.0, "MSFT": 0.0},
        )

        trade_recommendations = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=5.0,
                current_price=150.0,
                trade_value=750.0,
                estimated_commission=1.0,
                estimated_spread_cost=0.5,
                total_estimated_cost=1.5,
                current_weight=0.4,
                target_weight=0.35,
                weight_deviation=0.05,
                projected_weight_after_trade=0.35,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Reduce overweight position",
            )
        ]

        cost_analysis = CostAnalysis(total_transaction_costs=1.5, commission_costs=1.0, spread_costs=0.5, cost_as_percentage=0.0015)

        execution_summary = ExecutionSummary(
            total_trades_required=1,
            positions_requiring_action=1,
            positions_within_tolerance=2,
            estimated_execution_time="5 minutes",
            capital_required=0.0,
        )

        # Act
        result = RebalancingResult(
            current_portfolio=current_portfolio,
            projected_portfolio=projected_portfolio,
            trade_recommendations=trade_recommendations,
            cost_analysis=cost_analysis,
            current_risk_score=6.0,
            projected_risk_score=5.5,
            risk_improvement=0.5,
            execution_summary=execution_summary,
            overall_recommendation=RebalancingRecommendation.REBALANCE_SOON,
            next_review_date=datetime.now() + timedelta(days=30),
        )

        # Assert
        assert result.current_risk_score == 6.0
        assert result.projected_risk_score == 5.5
        assert result.risk_improvement == 0.5
        assert len(result.trade_recommendations) == 1

    def test_should_raise_error_when_trade_count_mismatch(self):
        # Arrange
        current_portfolio = PortfolioAnalysis(total_value=100000.0, weightings={"AAPL": 1.0}, deviations_from_target={"AAPL": 0.0})

        cost_analysis = CostAnalysis(total_transaction_costs=0.0, commission_costs=0.0, spread_costs=0.0, cost_as_percentage=0.0)

        execution_summary = ExecutionSummary(
            total_trades_required=2,  # Mismatch: says 2 but no trades provided
            positions_requiring_action=0,
            positions_within_tolerance=1,
            estimated_execution_time="0 minutes",
            capital_required=0.0,
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RebalancingResult(
                current_portfolio=current_portfolio,
                projected_portfolio=current_portfolio,
                trade_recommendations=[],  # Empty but execution_summary says 2 trades
                cost_analysis=cost_analysis,
                current_risk_score=5.0,
                projected_risk_score=5.0,
                risk_improvement=0.0,
                execution_summary=execution_summary,
                overall_recommendation=RebalancingRecommendation.NO_ACTION,
                next_review_date=datetime.now() + timedelta(days=30),
            )

        assert "Trade count mismatch: 0 vs 2" in str(exc_info.value)

    def test_should_raise_error_when_risk_improvement_calculation_wrong(self):
        # Arrange
        current_portfolio = PortfolioAnalysis(total_value=100000.0, weightings={"AAPL": 1.0}, deviations_from_target={"AAPL": 0.0})

        cost_analysis = CostAnalysis(total_transaction_costs=0.0, commission_costs=0.0, spread_costs=0.0, cost_as_percentage=0.0)

        execution_summary = ExecutionSummary(
            total_trades_required=0,
            positions_requiring_action=0,
            positions_within_tolerance=1,
            estimated_execution_time="0 minutes",
            capital_required=0.0,
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RebalancingResult(
                current_portfolio=current_portfolio,
                projected_portfolio=current_portfolio,
                trade_recommendations=[],
                cost_analysis=cost_analysis,
                current_risk_score=6.0,
                projected_risk_score=4.0,
                risk_improvement=1.0,  # Should be 2.0 (6.0 - 4.0)
                execution_summary=execution_summary,
                overall_recommendation=RebalancingRecommendation.NO_ACTION,
                next_review_date=datetime.now() + timedelta(days=30),
            )

        assert "Risk improvement calculation error: 1.0 vs 2.0" in str(exc_info.value)


class TestPriceData:
    """Test cases for PriceData schema."""

    def test_should_create_valid_price_data(self):
        # Arrange & Act
        price_data = PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now(), source="yahoo_finance", currency="USD")

        # Assert
        assert price_data.symbol == "AAPL"
        assert price_data.price == 150.0
        assert price_data.source == "yahoo_finance"
        assert price_data.currency == "USD"

    def test_should_create_price_data_with_defaults(self):
        # Arrange & Act
        price_data = PriceData(symbol="AAPL", price=150.0)

        # Assert
        assert price_data.source == "yahoo_finance"
        assert price_data.currency == "USD"
        assert isinstance(price_data.timestamp, datetime)

    def test_should_raise_error_when_price_zero(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PriceData(symbol="AAPL", price=0.0)

        assert "Input should be greater than 0" in str(exc_info.value)

    def test_should_raise_error_when_price_negative(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            PriceData(symbol="AAPL", price=-10.0)

        assert "Input should be greater than 0" in str(exc_info.value)


class TestEnums:
    """Test cases for enum values."""

    def test_trade_action_enum_values(self):
        # Assert
        assert TradeAction.BUY == "BUY"
        assert TradeAction.SELL == "SELL"
        assert TradeAction.HOLD == "HOLD"

    def test_urgency_level_enum_values(self):
        # Assert
        assert UrgencyLevel.LOW == "LOW"
        assert UrgencyLevel.MEDIUM == "MEDIUM"
        assert UrgencyLevel.HIGH == "HIGH"
        assert UrgencyLevel.CRITICAL == "CRITICAL"

    def test_rebalancing_method_enum_values(self):
        # Assert
        assert RebalancingMethod.MINIMIZE_TRADES == "MINIMIZE_TRADES"
        assert RebalancingMethod.MINIMIZE_COSTS == "MINIMIZE_COSTS"
        assert RebalancingMethod.RISK_AWARE == "RISK_AWARE"
        assert RebalancingMethod.TAX_EFFICIENT == "TAX_EFFICIENT"

    def test_rebalancing_recommendation_enum_values(self):
        # Assert
        assert RebalancingRecommendation.REBALANCE_NOW == "REBALANCE_NOW"
        assert RebalancingRecommendation.REBALANCE_SOON == "REBALANCE_SOON"
        assert RebalancingRecommendation.MONITOR == "MONITOR"
        assert RebalancingRecommendation.NO_ACTION == "NO_ACTION"


class TestCostAnalysis:
    """Test cases for CostAnalysis schema."""

    def test_should_create_valid_cost_analysis(self):
        # Arrange & Act
        cost_analysis = CostAnalysis(
            total_transaction_costs=10.0,
            commission_costs=5.0,
            spread_costs=3.0,
            market_impact_costs=2.0,
            cost_as_percentage=0.01,
            break_even_days=30,
        )

        # Assert
        assert cost_analysis.total_transaction_costs == 10.0
        assert cost_analysis.commission_costs == 5.0
        assert cost_analysis.spread_costs == 3.0
        assert cost_analysis.market_impact_costs == 2.0
        assert cost_analysis.cost_as_percentage == 0.01
        assert cost_analysis.break_even_days == 30

    def test_should_raise_error_when_negative_costs(self):
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            CostAnalysis(total_transaction_costs=-5.0, commission_costs=5.0, spread_costs=3.0, cost_as_percentage=0.01)

        assert "Input should be greater than or equal to 0" in str(exc_info.value)


class TestRebalancingNeed:
    """Test cases for RebalancingNeed schema."""

    def test_should_create_valid_rebalancing_need(self):
        # Arrange & Act
        need = RebalancingNeed(
            symbol="AAPL",
            current_weight=0.35,
            target_weight=0.30,
            deviation=0.05,
            tolerance_band=0.03,
            exceeds_tolerance=True,
            urgency_score=0.7,
            recommended_action=TradeAction.SELL,
        )

        # Assert
        assert need.symbol == "AAPL"
        assert need.current_weight == 0.35
        assert need.target_weight == 0.30
        assert need.deviation == 0.05
        assert need.exceeds_tolerance is True
        assert need.urgency_score == 0.7
        assert need.recommended_action == TradeAction.SELL


class TestPortfolioMetrics:
    """Test cases for PortfolioMetrics schema."""

    def test_should_create_valid_portfolio_metrics(self):
        # Arrange & Act
        metrics = PortfolioMetrics(
            total_value=100000.0,
            number_of_positions=5,
            largest_position_weight=0.35,
            concentration_risk_score=6.0,
            diversification_ratio=0.8,
            effective_number_of_positions=4.2,
            turnover_if_rebalanced=0.15,
            cash_weight=0.05,
        )

        # Assert
        assert metrics.total_value == 100000.0
        assert metrics.number_of_positions == 5
        assert metrics.largest_position_weight == 0.35
        assert metrics.concentration_risk_score == 6.0
        assert metrics.diversification_ratio == 0.8
        assert metrics.effective_number_of_positions == 4.2
        assert metrics.turnover_if_rebalanced == 0.15
        assert metrics.cash_weight == 0.05
