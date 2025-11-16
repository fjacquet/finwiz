"""
Unit tests for portfolio optimization module.

Tests the PortfolioOptimizer class and related functionality for mean-variance
optimization, risk parity, efficient frontier generation, and portfolio analytics.
"""

import numpy as np
import pytest

from finwiz.quantitative.constraint_handlers import ConstraintType
from finwiz.quantitative.optimization import (
    EfficientFrontier,
    ObjectiveFunction,
    OptimizationConstraint,
    OptimizationMethod,
    OptimizationResult,
    PortfolioInputs,
    PortfolioMetrics,
    PortfolioOptimizer,
)


class TestPortfolioOptimizer:
    """Test cases for PortfolioOptimizer class."""

    @pytest.fixture
    def optimizer(self):
        """Create a portfolio optimizer instance."""
        return PortfolioOptimizer()

    @pytest.fixture
    def sample_inputs(self):
        """Create sample portfolio inputs for testing."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
        expected_returns = [0.12, 0.15, 0.10, 0.14]

        # Create a realistic covariance matrix
        correlation_matrix = np.array([[1.00, 0.60, 0.70, 0.50], [0.60, 1.00, 0.65, 0.55], [0.70, 0.65, 1.00, 0.60], [0.50, 0.55, 0.60, 1.00]])

        volatilities = [0.20, 0.25, 0.18, 0.22]
        covariance_matrix = np.outer(volatilities, volatilities) * correlation_matrix

        return PortfolioInputs(
            symbols=symbols,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix.tolist(),
            risk_free_rate=0.03,
            current_weights=[0.25, 0.25, 0.25, 0.25],
        )

    @pytest.fixture
    def simple_inputs(self):
        """Create simple 2-asset portfolio inputs."""
        return PortfolioInputs(
            symbols=["STOCK1", "STOCK2"],
            expected_returns=[0.10, 0.12],
            covariance_matrix=[[0.04, 0.02], [0.02, 0.09]],
            risk_free_rate=0.02,
        )

    def test_optimizer_initialization(self, optimizer):
        """Test portfolio optimizer initialization."""
        assert optimizer is not None
        assert hasattr(optimizer, "config")
        assert hasattr(optimizer, "_cvxpy_available")

    def test_check_cvxpy_availability(self, optimizer):
        """Test CVXPY availability check."""
        availability = optimizer._check_cvxpy_availability()
        assert isinstance(availability, bool)

    def test_optimize_portfolio_max_sharpe(self, optimizer, sample_inputs):
        """Test portfolio optimization for maximum Sharpe ratio."""
        result = optimizer.optimize_portfolio(sample_inputs, objective=ObjectiveFunction.MAX_SHARPE, method=OptimizationMethod.MEAN_VARIANCE)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert len(result.optimal_weights) == len(sample_inputs.symbols)
        assert abs(sum(result.optimal_weights) - 1.0) < 1e-6  # Weights sum to 1
        assert all(w >= 0 for w in result.optimal_weights)  # Long-only
        assert result.metrics.sharpe_ratio > 0
        assert result.computation_time >= 0

    def test_optimize_portfolio_min_volatility(self, optimizer, sample_inputs):
        """Test portfolio optimization for minimum volatility."""
        result = optimizer.optimize_portfolio(sample_inputs, objective=ObjectiveFunction.MIN_VOLATILITY, method=OptimizationMethod.MEAN_VARIANCE)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.metrics.volatility > 0
        assert abs(sum(result.optimal_weights) - 1.0) < 1e-6

    def test_optimize_portfolio_max_return(self, optimizer, sample_inputs):
        """Test portfolio optimization for maximum return."""
        result = optimizer.optimize_portfolio(sample_inputs, objective=ObjectiveFunction.MAX_RETURN, method=OptimizationMethod.MEAN_VARIANCE)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.metrics.expected_return > 0

        # Should concentrate in highest return asset
        max_return_idx = np.argmax(sample_inputs.expected_returns)
        assert result.optimal_weights[max_return_idx] > 0.5

    def test_optimize_portfolio_risk_parity(self, optimizer, sample_inputs):
        """Test risk parity optimization."""
        result = optimizer.optimize_portfolio(sample_inputs, objective=ObjectiveFunction.RISK_PARITY, method=OptimizationMethod.RISK_PARITY)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert abs(sum(result.optimal_weights) - 1.0) < 1e-6
        assert all(w > 0 for w in result.optimal_weights)  # All weights positive

    def test_optimize_portfolio_black_litterman(self, optimizer, sample_inputs):
        """Test Black-Litterman optimization."""
        result = optimizer.optimize_portfolio(sample_inputs, method=OptimizationMethod.BLACK_LITTERMAN)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.optimization_method == OptimizationMethod.BLACK_LITTERMAN

    def test_optimize_portfolio_hrp(self, optimizer, sample_inputs):
        """Test Hierarchical Risk Parity optimization."""
        result = optimizer.optimize_portfolio(sample_inputs, method=OptimizationMethod.HIERARCHICAL_RISK_PARITY)

        assert isinstance(result, OptimizationResult)
        assert result.success is True
        assert result.optimization_method == OptimizationMethod.HIERARCHICAL_RISK_PARITY

    def test_portfolio_inputs_validation(self):
        """Test portfolio inputs validation."""
        # Test mismatched lengths
        with pytest.raises(ValueError):
            PortfolioInputs(
                symbols=["A", "B"],
                expected_returns=[0.1, 0.2, 0.3],  # Wrong length
                covariance_matrix=[[0.04, 0.02], [0.02, 0.09]],
            )

        # Test invalid covariance matrix dimensions
        with pytest.raises(ValueError):
            PortfolioInputs(
                symbols=["A", "B"],
                expected_returns=[0.1, 0.2],
                covariance_matrix=[[0.04]],  # Wrong dimensions
            )

        # Test invalid current weights
        with pytest.raises(ValueError):
            PortfolioInputs(
                symbols=["A", "B"],
                expected_returns=[0.1, 0.2],
                covariance_matrix=[[0.04, 0.02], [0.02, 0.09]],
                current_weights=[0.3, 0.4],  # Don't sum to 1
            )

    def test_validate_inputs_positive_definite(self, optimizer):
        """Test input validation for positive definite covariance matrix."""
        # Create non-positive definite matrix
        inputs = PortfolioInputs(
            symbols=["A", "B"],
            expected_returns=[0.1, 0.2],
            covariance_matrix=[[0.04, 0.05], [0.05, 0.04]],  # Not positive definite
        )

        # Should not raise error but log warning
        validation_errors = optimizer._validate_inputs(inputs)

        # Check that validation detected the issue
        assert len(validation_errors) > 0
        assert any("positive definite" in error.lower() for error in validation_errors)

    def test_calculate_portfolio_metrics(self, optimizer, sample_inputs):
        """Test portfolio metrics calculation."""
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        returns = np.array(sample_inputs.expected_returns)
        cov_matrix = np.array(sample_inputs.covariance_matrix)

        metrics = optimizer._calculate_portfolio_metrics(weights, returns, cov_matrix, sample_inputs.risk_free_rate)

        assert isinstance(metrics, PortfolioMetrics)
        assert metrics.expected_return > 0
        assert metrics.volatility > 0
        assert metrics.sharpe_ratio > 0
        assert metrics.diversification_ratio > 0
        assert -1 <= metrics.var_95 <= 0  # VaR should be negative
        assert metrics.cvar_95 <= metrics.var_95  # CVaR should be worse than VaR

    def test_generate_efficient_frontier(self, optimizer, simple_inputs):
        """Test efficient frontier generation."""
        frontier = optimizer.generate_efficient_frontier(simple_inputs, num_points=10)

        assert isinstance(frontier, EfficientFrontier)
        assert len(frontier.points) > 0
        assert len(frontier.points) <= 10
        assert frontier.max_sharpe_portfolio is not None
        assert frontier.min_volatility_portfolio is not None

        # Check that points are sorted by return
        returns = [point.expected_return for point in frontier.points]
        assert returns == sorted(returns)

        # Check that all points have valid weights
        for point in frontier.points:
            assert abs(sum(point.weights) - 1.0) < 1e-6
            assert all(w >= -1e-6 for w in point.weights)  # Allow small negative due to numerical errors

    def test_optimize_for_target_return(self, optimizer, simple_inputs):
        """Test optimization for target return."""
        returns = np.array(simple_inputs.expected_returns)
        cov_matrix = np.array(simple_inputs.covariance_matrix)
        target_return = 0.11  # Between min and max returns

        weights = optimizer._optimize_for_target_return(returns, cov_matrix, target_return)

        if weights is not None:
            assert abs(sum(weights) - 1.0) < 1e-6
            assert abs(np.dot(weights, returns) - target_return) < 1e-6
            assert all(w >= -1e-6 for w in weights)

    def test_calculate_portfolio_attribution(self, optimizer, sample_inputs):
        """Test portfolio attribution analysis."""
        weights = np.array([0.4, 0.3, 0.2, 0.1])
        returns = np.array(sample_inputs.expected_returns)
        benchmark_weights = np.array([0.25, 0.25, 0.25, 0.25])

        attribution = optimizer.calculate_portfolio_attribution(weights, returns, benchmark_weights)

        assert isinstance(attribution, dict)
        assert "portfolio_return" in attribution
        assert "benchmark_return" in attribution
        assert "active_return" in attribution
        assert "allocation_effect" in attribution
        assert "selection_effect" in attribution

        # Active return should equal allocation + selection effects
        active_return = attribution["active_return"]
        allocation_effect = attribution["allocation_effect"]
        selection_effect = attribution["selection_effect"]
        assert abs(active_return - (allocation_effect + selection_effect)) < 1e-10

    def test_rebalance_portfolio(self, optimizer):
        """Test portfolio rebalancing calculation."""
        current_weights = np.array([0.3, 0.3, 0.2, 0.2])
        target_weights = np.array([0.25, 0.25, 0.25, 0.25])

        trades, total_cost = optimizer.rebalance_portfolio(current_weights, target_weights, transaction_cost=0.001, min_trade_size=0.01)

        assert len(trades) == len(current_weights)
        assert total_cost >= 0

        # Check that trades move towards target
        new_weights = current_weights + trades
        assert np.allclose(new_weights, target_weights, atol=0.01)

    def test_get_available_methods(self, optimizer):
        """Test getting available optimization methods."""
        methods = optimizer.get_available_methods()

        assert isinstance(methods, list)
        assert OptimizationMethod.MEAN_VARIANCE in methods
        assert OptimizationMethod.RISK_PARITY in methods
        assert OptimizationMethod.BLACK_LITTERMAN in methods
        assert OptimizationMethod.HIERARCHICAL_RISK_PARITY in methods

    def test_optimization_with_constraints(self, optimizer, sample_inputs):
        """Test optimization with additional constraints."""
        constraints = [OptimizationConstraint(constraint_type=ConstraintType.WEIGHT_BOUNDS, parameters={"min_weight": 0.1, "max_weight": 0.4})]

        result = optimizer.optimize_portfolio(sample_inputs, objective=ObjectiveFunction.MAX_SHARPE, constraints=constraints)

        assert isinstance(result, OptimizationResult)
        assert result.success is True

    def test_optimization_error_handling(self, optimizer):
        """Test error handling in optimization."""
        # Test with invalid covariance matrix (not positive definite)
        invalid_inputs = PortfolioInputs(
            symbols=["A", "B"],  # At least 2 assets required
            expected_returns=[0.1, 0.08],
            covariance_matrix=[[0.04, 0.05], [0.05, 0.03]],  # Not positive definite
        )

        result = optimizer.optimize_portfolio(invalid_inputs)

        # Should return fallback result or handle gracefully
        assert isinstance(result, OptimizationResult)
        # May succeed with regularization or fail gracefully
        assert result.message is not None

    def test_objective_function_calculation(self, optimizer, sample_inputs):
        """Test objective function value calculation."""
        weights = np.array([0.25, 0.25, 0.25, 0.25])
        returns = np.array(sample_inputs.expected_returns)
        cov_matrix = np.array(sample_inputs.covariance_matrix)

        # Test different objectives
        sharpe_value = optimizer._calculate_objective_value(weights, returns, cov_matrix, sample_inputs.risk_free_rate, ObjectiveFunction.MAX_SHARPE)
        assert sharpe_value > 0

        vol_value = optimizer._calculate_objective_value(weights, returns, cov_matrix, sample_inputs.risk_free_rate, ObjectiveFunction.MIN_VOLATILITY)
        assert vol_value > 0

        return_value = optimizer._calculate_objective_value(weights, returns, cov_matrix, sample_inputs.risk_free_rate, ObjectiveFunction.MAX_RETURN)
        assert return_value > 0

    def test_risk_parity_objective(self, optimizer, sample_inputs):
        """Test risk parity optimization objective."""
        returns = np.array(sample_inputs.expected_returns)
        cov_matrix = np.array(sample_inputs.covariance_matrix)

        result = optimizer._optimize_risk_parity(returns, cov_matrix, None)

        assert len(result) == len(sample_inputs.symbols)
        assert abs(sum(result) - 1.0) < 1e-6
        assert all(w > 0 for w in result)

        # Check that risk contributions are more equal than equal weights
        portfolio_vol = np.sqrt(np.dot(result.T, np.dot(cov_matrix, result)))
        marginal_contrib = np.dot(cov_matrix, result) / portfolio_vol
        risk_contrib = result * marginal_contrib

        # Risk contributions should be more equal
        risk_contrib_std = np.std(risk_contrib)
        equal_weight_risk_contrib = (
            np.array([0.25] * 4) * np.dot(cov_matrix, np.array([0.25] * 4)) / np.sqrt(np.dot(np.array([0.25] * 4).T, np.dot(cov_matrix, np.array([0.25] * 4))))
        )
        equal_weight_std = np.std(equal_weight_risk_contrib)

        # Risk parity should have lower standard deviation of risk contributions
        assert risk_contrib_std <= equal_weight_std * 1.1  # Allow some tolerance

    def test_portfolio_metrics_accuracy(self, optimizer, sample_inputs):
        """Test accuracy of portfolio metrics calculations."""
        weights = np.array([0.3, 0.3, 0.2, 0.2])
        returns = np.array(sample_inputs.expected_returns)
        cov_matrix = np.array(sample_inputs.covariance_matrix)

        metrics = optimizer._calculate_portfolio_metrics(weights, returns, cov_matrix, sample_inputs.risk_free_rate)

        # Manual calculation for verification
        expected_return = np.dot(weights, returns)
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe_ratio = (expected_return - sample_inputs.risk_free_rate) / portfolio_vol

        assert abs(metrics.expected_return - expected_return) < 1e-10
        assert abs(metrics.volatility - portfolio_vol) < 1e-10
        assert abs(metrics.sharpe_ratio - sharpe_ratio) < 1e-10

        # Check diversification ratio
        weighted_avg_vol = np.dot(weights, np.sqrt(np.diag(cov_matrix)))
        expected_div_ratio = weighted_avg_vol / portfolio_vol
        assert abs(metrics.diversification_ratio - expected_div_ratio) < 1e-10

    def test_efficient_frontier_properties(self, optimizer, simple_inputs):
        """Test properties of efficient frontier."""
        frontier = optimizer.generate_efficient_frontier(simple_inputs, num_points=20)

        # Check that volatility increases with return (generally)
        points = frontier.points
        if len(points) > 1:
            # Sort by return
            sorted_points = sorted(points, key=lambda p: p.expected_return)

            # Volatility should generally increase with return
            volatilities = [p.volatility for p in sorted_points]
            returns = [p.expected_return for p in sorted_points]

            # Check that we don't have decreasing volatility with increasing return
            # (allowing for some numerical noise)
            for i in range(1, len(volatilities)):
                if returns[i] > returns[i - 1]:
                    assert volatilities[i] >= volatilities[i - 1] - 1e-6

        # Max Sharpe portfolio should have highest Sharpe ratio
        max_sharpe = frontier.max_sharpe_portfolio
        if max_sharpe and len(points) > 1:
            for point in points:
                assert max_sharpe.sharpe_ratio >= point.sharpe_ratio - 1e-6

        # Min volatility portfolio should have lowest volatility
        min_vol = frontier.min_volatility_portfolio
        if min_vol and len(points) > 1:
            for point in points:
                assert min_vol.volatility <= point.volatility + 1e-6
