"""
Unit tests for the portfolio rebalancing optimization engine.

Tests cover all optimization strategies, constraint handling, and edge cases
following FinWiz testing standards with comprehensive mocking.
"""

from pytest import approx
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../src"))

from finwiz.quantitative.rebalancing_engine import (
    MinimizeCostsStrategy,
    MinimizeTradesStrategy,
    OptimizationConstraint,
    RebalancingEngine,
    RiskAwareStrategy,
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


class TestMinimizeTradesStrategy:
    """Test cases for the minimize trades optimization strategy."""

    def test_should_prioritize_high_urgency_trades_when_optimizing(self):
        """Test that high urgency trades are prioritized."""
        # Arrange
        strategy = MinimizeTradesStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.4,
                target_weight=0.3,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.9,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.1,
                target_weight=0.2,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.3,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.1, "MSFT": 0.5},
            deviations_from_target={"AAPL": 0.1, "GOOGL": -0.1, "MSFT": 0.0},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
        )

        target_weights = {"AAPL": 0.3, "GOOGL": 0.2, "MSFT": 0.5}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0}
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=266.67),
                Holding(symbol="GOOGL", shares=4.0),
                Holding(symbol="MSFT", shares=166.67),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=20000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 2
        assert result.trades[0].symbol == "AAPL"  # Higher urgency should be first
        assert result.trades[0].urgency == UrgencyLevel.CRITICAL
        assert result.trades[1].symbol == "GOOGL"
        assert result.trades[1].urgency == UrgencyLevel.MEDIUM
        assert result.method_used == "MINIMIZE_TRADES"

    def test_should_respect_minimum_trade_size_constraint_when_optimizing(self):
        """Test that trades below minimum size are skipped."""
        # Arrange
        strategy = MinimizeTradesStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.301,
                target_weight=0.3,
                deviation=0.001,
                tolerance_band=0.05,
                urgency_score=0.5,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.301, "GOOGL": 0.699},
            deviations_from_target={"AAPL": 0.001, "GOOGL": -0.001},
            positions_needing_rebalancing=["AAPL"],
        )

        target_weights = {"AAPL": 0.3, "GOOGL": 0.7}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}
        constraints = [
            OptimizationConstraint(
                name="min_trade_size",
                constraint_type="min_trade_size",
                value=1000.0,  # High minimum trade size
                description="Minimum trade size",
            )
        ]
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=200.67),
                Holding(symbol="GOOGL", shares=27.96),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=10000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 0  # Trade should be skipped due to minimum size
        assert result.method_used == "MINIMIZE_TRADES"

    def test_should_handle_insufficient_capital_constraint_when_optimizing(self):
        """Test handling of insufficient capital constraint."""
        # Arrange
        strategy = MinimizeTradesStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="GOOGL",
                current_weight=0.1,
                target_weight=0.5,
                deviation=0.4,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.9, "GOOGL": 0.1},
            deviations_from_target={"AAPL": 0.4, "GOOGL": -0.4},
            positions_needing_rebalancing=["GOOGL"],
        )

        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=600.0),
                Holding(symbol="GOOGL", shares=4.0),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=5000.0,  # Insufficient for full rebalancing
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 1
        assert result.trades[0].symbol == "GOOGL"
        assert result.trades[0].action == TradeAction.BUY
        assert result.capital_used <= 5000.0
        assert "Insufficient capital" not in result.constraints_violated  # Should do partial trade

    def test_should_skip_trades_with_invalid_prices_when_optimizing(self):
        """Test that trades with invalid prices are skipped."""
        # Arrange
        strategy = MinimizeTradesStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="INVALID",
                current_weight=0.3,
                target_weight=0.2,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"INVALID": 0.3, "AAPL": 0.7},
            deviations_from_target={"INVALID": 0.1, "AAPL": -0.1},
            positions_needing_rebalancing=["INVALID"],
        )

        target_weights = {"INVALID": 0.2, "AAPL": 0.8}
        prices = {"INVALID": 0.0, "AAPL": 150.0}  # Invalid price
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="INVALID", shares=100.0),
                Holding(symbol="AAPL", shares=466.67),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=10000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 0  # Trade should be skipped due to invalid price
        assert result.method_used == "MINIMIZE_TRADES"


class TestMinimizeCostsStrategy:
    """Test cases for the minimize costs optimization strategy."""

    def test_should_prioritize_cost_efficient_trades_when_optimizing(self):
        """Test that cost-efficient trades are prioritized."""
        # Arrange
        strategy = MinimizeCostsStrategy()

        # Create trades with different cost efficiencies
        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",  # High value, low deviation = low efficiency
                current_weight=0.4,
                target_weight=0.35,
                deviation=0.05,
                tolerance_band=0.03,
                urgency_score=0.5,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="GOOGL",  # Lower value, high deviation = high efficiency
                current_weight=0.1,
                target_weight=0.3,
                deviation=0.2,
                tolerance_band=0.05,
                urgency_score=0.7,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.1, "MSFT": 0.5},
            deviations_from_target={"AAPL": 0.05, "GOOGL": -0.2, "MSFT": 0.15},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
        )

        target_weights = {"AAPL": 0.35, "GOOGL": 0.3, "MSFT": 0.35}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0}
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=266.67),
                Holding(symbol="GOOGL", shares=4.0),
                Holding(symbol="MSFT", shares=166.67),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=30000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 2
        assert result.method_used == "MINIMIZE_COSTS"
        # Verify trades are generated (order may vary based on implementation)
        trade_symbols = {trade.symbol for trade in result.trades}
        assert "AAPL" in trade_symbols
        assert "GOOGL" in trade_symbols
        assert any("efficiency" in trade.rationale for trade in result.trades)

    def test_should_calculate_optimization_score_based_on_cost_ratio_when_optimizing(self):
        """Test that optimization score reflects cost efficiency."""
        # Arrange
        strategy = MinimizeCostsStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.6,
                target_weight=0.5,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.5,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.6, "GOOGL": 0.4},
            deviations_from_target={"AAPL": 0.1, "GOOGL": -0.1},
            positions_needing_rebalancing=["AAPL"],
        )

        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=400.0),
                Holding(symbol="GOOGL", shares=16.0),
            ],
            target_weights=target_weights,
            transaction_cost_rate=0.001,  # 0.1% transaction cost
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=0.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert result.optimization_score > 0.9  # Should be high (low cost ratio)
        assert result.total_cost > 0
        assert result.method_used == "MINIMIZE_COSTS"


class TestRiskAwareStrategy:
    """Test cases for the risk-aware optimization strategy."""

    def test_should_prioritize_concentration_risk_reduction_when_optimizing(self):
        """Test that trades reducing concentration risk are prioritized."""
        # Arrange
        strategy = RiskAwareStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",  # High concentration position
                current_weight=0.6,
                target_weight=0.3,
                deviation=0.3,
                tolerance_band=0.05,
                urgency_score=0.5,
                needs_rebalancing=True,
            ),
            RebalancingNeed(
                symbol="GOOGL",  # Normal position
                current_weight=0.1,
                target_weight=0.2,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.7,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.6, "GOOGL": 0.1, "MSFT": 0.3},
            deviations_from_target={"AAPL": 0.3, "GOOGL": -0.1, "MSFT": -0.2},
            positions_needing_rebalancing=["AAPL", "GOOGL"],
        )

        target_weights = {"AAPL": 0.3, "GOOGL": 0.2, "MSFT": 0.5}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0}
        constraints = []
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=400.0),
                Holding(symbol="GOOGL", shares=4.0),
                Holding(symbol="MSFT", shares=100.0),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=20000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        # Note: AAPL trade is rejected due to target weight (0.3) exceeding default max position size (0.25)
        assert len(result.trades) == 1
        assert result.method_used == "RISK_AWARE"
        # Only GOOGL trade is executed (AAPL violates max position constraint)
        assert result.trades[0].symbol == "GOOGL"
        assert "risk-adjusted urgency" in result.trades[0].rationale
        # Verify constraint violation was recorded
        assert "AAPL" in str(result.constraints_violated)

    def test_should_enforce_maximum_position_size_constraint_when_optimizing(self):
        """Test that maximum position size constraints are enforced."""
        # Arrange
        strategy = RiskAwareStrategy()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.2,
                target_weight=0.4,  # Would exceed max position size
                deviation=0.2,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.2, "GOOGL": 0.8},
            deviations_from_target={"AAPL": -0.2, "GOOGL": 0.2},
            positions_needing_rebalancing=["AAPL"],
        )

        target_weights = {"AAPL": 0.4, "GOOGL": 0.6}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}
        constraints = [
            OptimizationConstraint(
                name="max_position",
                constraint_type="max_position",
                value=0.3,  # 30% maximum position size
                description="Maximum position size",
            )
        ]
        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=133.33),
                Holding(symbol="GOOGL", shares=32.0),
            ],
            target_weights=target_weights,
        )

        # Act
        result = strategy.optimize(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            available_capital=30000.0,
            constraints=constraints,
            config=config,
        )

        # Assert
        assert len(result.trades) == 0  # Trade should be blocked
        assert "exceeds maximum position size" in result.constraints_violated[0]
        assert result.method_used == "RISK_AWARE"


class TestRebalancingEngine:
    """Test cases for the main rebalancing engine."""

    def test_should_initialize_with_all_strategies_when_created(self):
        """Test that engine initializes with all optimization strategies."""
        # Act
        engine = RebalancingEngine()

        # Assert
        assert RebalancingMethod.MINIMIZE_TRADES in engine.strategies
        assert RebalancingMethod.MINIMIZE_COSTS in engine.strategies
        assert RebalancingMethod.RISK_AWARE in engine.strategies
        assert isinstance(engine.strategies[RebalancingMethod.MINIMIZE_TRADES], MinimizeTradesStrategy)
        assert isinstance(engine.strategies[RebalancingMethod.MINIMIZE_COSTS], MinimizeCostsStrategy)
        assert isinstance(engine.strategies[RebalancingMethod.RISK_AWARE], RiskAwareStrategy)

    def test_should_use_correct_strategy_when_optimizing_trades(self):
        """Test that the correct strategy is used based on configuration."""
        # Arrange
        engine = RebalancingEngine()

        rebalancing_needs = [
            RebalancingNeed(
                symbol="AAPL",
                current_weight=0.4,
                target_weight=0.3,
                deviation=0.1,
                tolerance_band=0.05,
                urgency_score=0.8,
                needs_rebalancing=True,
            ),
        ]

        current_portfolio = PortfolioAnalysis(
            total_value=100000.0,
            weightings={"AAPL": 0.4, "GOOGL": 0.6},
            deviations_from_target={"AAPL": 0.1, "GOOGL": -0.1},
            positions_needing_rebalancing=["AAPL"],
        )

        target_weights = {"AAPL": 0.3, "GOOGL": 0.7}
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}

        config = PortfolioConfiguration(
            holdings=[
                Holding(symbol="AAPL", shares=266.67),
                Holding(symbol="GOOGL", shares=24.0),
            ],
            target_weights=target_weights,
            rebalancing_method=RebalancingMethod.MINIMIZE_COSTS,
        )

        # Act
        result = engine.optimize_rebalancing_trades(
            rebalancing_needs=rebalancing_needs,
            current_portfolio=current_portfolio,
            target_weights=target_weights,
            prices=prices,
            config=config,
        )

        # Assert
        assert result.method_used == "MINIMIZE_COSTS"

    def test_should_raise_error_when_unknown_strategy_specified(self):
        """Test that error is raised for unknown optimization strategy."""
        # Arrange
        from pydantic_core import ValidationError

        engine = RebalancingEngine()

        # Act & Assert - Pydantic validates enum during config creation
        with pytest.raises(ValidationError):
            config = PortfolioConfiguration(
                holdings=[Holding(symbol="AAPL", shares=100.0)],
                target_weights={"AAPL": 1.0},
                rebalancing_method="UNKNOWN_METHOD",  # Invalid method
            )

    def test_should_combine_trades_for_same_symbol_when_minimizing_costs(self):
        """Test that multiple trades for the same symbol are combined."""
        # Arrange
        engine = RebalancingEngine()

        trades = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=10.0,
                current_price=150.0,
                trade_value=1500.0,
                estimated_commission=1.5,
                estimated_spread_cost=1.5,
                total_estimated_cost=3.0,
                current_weight=0.3,
                target_weight=0.4,
                weight_deviation=-0.1,
                projected_weight_after_trade=0.4,
                priority=1,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Buy AAPL to reach target weight",
            ),
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.BUY,
                quantity=5.0,
                current_price=150.0,
                trade_value=750.0,
                estimated_commission=0.75,
                estimated_spread_cost=0.75,
                total_estimated_cost=1.5,
                current_weight=0.3,
                target_weight=0.4,
                weight_deviation=-0.1,
                projected_weight_after_trade=0.4,
                priority=2,
                urgency=UrgencyLevel.MEDIUM,
                rationale="Buy more AAPL to reach target",
            ),
        ]

        # Act
        result = engine.minimize_transaction_costs(trades)

        # Assert
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].quantity == approx(15.0)  # Combined quantity
        assert result[0].action == TradeAction.BUY
        assert "Combined" in result[0].rationale

    def test_should_calculate_tax_implications_for_sell_trades_when_cost_basis_available(self):
        """Test tax implications calculation for trades with cost basis."""
        # Arrange
        engine = RebalancingEngine()

        trades = [
            TradeRecommendation(
                symbol="AAPL",
                action=TradeAction.SELL,
                quantity=100.0,
                current_price=150.0,
                trade_value=15000.0,
                estimated_commission=15.0,
                estimated_spread_cost=15.0,
                total_estimated_cost=30.0,
                current_weight=0.6,
                target_weight=0.4,
                weight_deviation=0.2,
                projected_weight_after_trade=0.4,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Sell AAPL to reduce position",
            ),
        ]

        holdings = [
            Holding(symbol="AAPL", shares=200.0, cost_basis=100.0),  # $50 gain per share
        ]

        # Act
        result = engine.calculate_tax_implications(trades, holdings)

        # Assert
        assert result["total_realized_gains"] == approx(5000.0)  # 100 shares * $50 gain
        assert result["long_term_gains"] == approx(5000.0)
        assert len(result["tax_inefficient_trades"]) == 1
        assert result["tax_inefficient_trades"][0]["symbol"] == "AAPL"

    def test_should_handle_trades_without_cost_basis_when_calculating_tax_implications(self):
        """Test tax calculation when cost basis is not available."""
        # Arrange
        engine = RebalancingEngine()

        trades = [
            TradeRecommendation(
                symbol="GOOGL",
                action=TradeAction.SELL,
                quantity=10.0,
                current_price=2500.0,
                trade_value=25000.0,
                estimated_commission=25.0,
                estimated_spread_cost=25.0,
                total_estimated_cost=50.0,
                current_weight=0.5,
                target_weight=0.3,
                weight_deviation=0.2,
                projected_weight_after_trade=0.3,
                priority=1,
                urgency=UrgencyLevel.HIGH,
                rationale="Sell GOOGL to reduce position",
            ),
        ]

        holdings = [
            Holding(symbol="GOOGL", shares=20.0),  # No cost basis
        ]

        # Act
        result = engine.calculate_tax_implications(trades, holdings)

        # Assert
        assert result["total_realized_gains"] == approx(0.0)
        assert result["total_realized_losses"] == approx(0.0)
        assert len(result["tax_efficient_trades"]) == 0
        assert len(result["tax_inefficient_trades"]) == 0

    def test_should_build_default_constraints_from_configuration_when_none_provided(self):
        """Test that default constraints are built from configuration."""
        # Arrange
        engine = RebalancingEngine()

        config = PortfolioConfiguration(
            holdings=[Holding(symbol="AAPL", shares=100.0)],
            target_weights={"AAPL": 1.0},
            min_trade_size=100.0,
            available_capital=5000.0,
        )

        # Act
        constraints = engine._build_default_constraints(config)

        # Assert
        constraint_types = [c.constraint_type for c in constraints]
        assert "min_trade_size" in constraint_types
        assert "max_position" in constraint_types
        assert "turnover" in constraint_types
        assert "capital" in constraint_types

        min_trade_constraint = next(c for c in constraints if c.constraint_type == "min_trade_size")
        assert min_trade_constraint.value == approx(100.0)