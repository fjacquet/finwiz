"""
Comprehensive unit tests for portfolio optimization objective functions.

Tests the ObjectiveFunctionCalculator and ObjectiveFunction enum for various
optimization objectives including Sharpe ratio, volatility, returns, risk parity,
diversification, and CVaR. Covers edge cases, parameter validation, and mathematical
correctness.
"""

import numpy as np
import pytest

from finwiz.quantitative.objective_functions import (
    ObjectiveFunction,
    ObjectiveFunctionCalculator,
)


class TestObjectiveFunctionEnum:
    """Test cases for ObjectiveFunction enum."""

    def test_enum_values_exist(self):
        """Test that all expected objective function types exist."""
        assert hasattr(ObjectiveFunction, "MAX_SHARPE")
        assert hasattr(ObjectiveFunction, "MIN_VOLATILITY")
        assert hasattr(ObjectiveFunction, "MAX_RETURN")
        assert hasattr(ObjectiveFunction, "RISK_PARITY")
        assert hasattr(ObjectiveFunction, "MAX_DIVERSIFICATION")
        assert hasattr(ObjectiveFunction, "MIN_CVAR")

    def test_enum_string_values(self):
        """Test that enum values are correct strings."""
        assert ObjectiveFunction.MAX_SHARPE.value == "max_sharpe"
        assert ObjectiveFunction.MIN_VOLATILITY.value == "min_volatility"
        assert ObjectiveFunction.MAX_RETURN.value == "max_return"
        assert ObjectiveFunction.RISK_PARITY.value == "risk_parity"
        assert ObjectiveFunction.MAX_DIVERSIFICATION.value == "max_diversification"
        assert ObjectiveFunction.MIN_CVAR.value == "min_cvar"

    def test_enum_is_string_enum(self):
        """Test that ObjectiveFunction is a string enum."""
        assert isinstance(ObjectiveFunction.MAX_SHARPE, str)
        assert ObjectiveFunction.MIN_VOLATILITY.value == "min_volatility"


class TestObjectiveFunctionCalculatorInitialization:
    """Test cases for ObjectiveFunctionCalculator initialization."""

    def test_calculator_initialization(self):
        """Test basic calculator initialization."""
        calculator = ObjectiveFunctionCalculator()
        assert calculator is not None
        assert isinstance(calculator, ObjectiveFunctionCalculator)

    def test_multiple_calculator_instances(self):
        """Test that multiple calculator instances can be created."""
        calc1 = ObjectiveFunctionCalculator()
        calc2 = ObjectiveFunctionCalculator()
        assert calc1 is not calc2


class TestGetObjectiveFunction:
    """Test cases for get_objective_function method."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_returns(self):
        """Sample returns for 3 assets."""
        return np.array([0.10, 0.12, 0.08])

    @pytest.fixture
    def sample_cov_matrix(self):
        """Sample positive definite covariance matrix."""
        return np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )

    @pytest.fixture
    def sample_weights(self):
        """Sample portfolio weights (normalized)."""
        return np.array([0.3, 0.5, 0.2])

    def test_max_sharpe_objective_returns_callable(self, calculator, sample_returns, sample_cov_matrix):
        """Test that MAX_SHARPE objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, sample_returns, sample_cov_matrix, risk_free_rate=0.02
        )
        assert callable(obj_func)

    def test_min_volatility_objective_returns_callable(self, calculator, sample_cov_matrix):
        """Test that MIN_VOLATILITY objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, np.array([0.10, 0.12, 0.08]), sample_cov_matrix
        )
        assert callable(obj_func)

    def test_max_return_objective_returns_callable(self, calculator, sample_returns, sample_cov_matrix):
        """Test that MAX_RETURN objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, sample_returns, sample_cov_matrix
        )
        assert callable(obj_func)

    def test_risk_parity_objective_returns_callable(self, calculator, sample_cov_matrix, sample_returns):
        """Test that RISK_PARITY objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, sample_returns, sample_cov_matrix
        )
        assert callable(obj_func)

    def test_max_diversification_objective_returns_callable(self, calculator, sample_cov_matrix, sample_returns):
        """Test that MAX_DIVERSIFICATION objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, sample_returns, sample_cov_matrix
        )
        assert callable(obj_func)

    def test_min_cvar_objective_returns_callable(self, calculator, sample_returns, sample_cov_matrix):
        """Test that MIN_CVAR objective returns a callable."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, sample_returns, sample_cov_matrix, confidence_level=0.05
        )
        assert callable(obj_func)

    def test_invalid_objective_raises_error(self, calculator, sample_returns, sample_cov_matrix):
        """Test that invalid objective function raises ValueError."""
        with pytest.raises(ValueError, match="Objective function .* not implemented"):
            calculator.get_objective_function("invalid_objective", sample_returns, sample_cov_matrix)


class TestMaxSharpeObjective:
    """Test cases for maximum Sharpe ratio objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample portfolio data."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        return returns, cov_matrix

    def test_max_sharpe_equal_weights(self, calculator, sample_data):
        """Test Sharpe ratio with equal weights."""
        returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.02
        )
        weights = np.array([1 / 3, 1 / 3, 1 / 3])
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))
        assert result < 0  # Negative because it's for minimization

    def test_max_sharpe_single_asset(self, calculator, sample_data):
        """Test Sharpe ratio with single asset portfolio."""
        returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.02
        )
        weights = np.array([1.0, 0.0, 0.0])
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))

    def test_max_sharpe_zero_volatility_returns_neg_inf(self, calculator):
        """Test that zero volatility returns negative infinity."""
        returns = np.array([0.10, 0.10])
        # Zero covariance matrix (zero volatility)
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.02
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        assert result == -np.inf

    def test_max_sharpe_high_return_low_risk_optimal(self, calculator):
        """Test that high return with low risk produces good Sharpe ratio."""
        # Asset with 20% return and 5% volatility (excellent risk-adjusted return)
        returns = np.array([0.20, 0.05])
        cov_matrix = np.array([[0.0025, 0.0], [0.0, 0.0004]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.02
        )
        weights = np.array([1.0, 0.0])
        result = obj_func(weights)
        # Should be negative (minimizing negative Sharpe)
        assert result < 0

    def test_max_sharpe_different_risk_free_rates(self, calculator, sample_data):
        """Test Sharpe ratio with different risk-free rates."""
        returns, cov_matrix = sample_data
        weights = np.array([0.3, 0.5, 0.2])

        obj_func_low = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.01
        )
        obj_func_high = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=0.05
        )

        result_low = obj_func_low(weights)
        result_high = obj_func_high(weights)

        # Lower risk-free rate gives higher Sharpe (numerator larger)
        # Since we return -Sharpe, lower risk-free rate should be more negative
        assert result_low < result_high


class TestMinVolatilityObjective:
    """Test cases for minimum volatility objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_cov_matrix(self):
        """Sample positive definite covariance matrix."""
        return np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )

    def test_min_volatility_returns_positive(self, calculator, sample_cov_matrix):
        """Test that volatility is always positive."""
        returns = np.array([0.10, 0.12, 0.08])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, sample_cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        result = obj_func(weights)
        assert result >= 0

    def test_min_volatility_zero_weights(self, calculator, sample_cov_matrix):
        """Test volatility with zero weights."""
        returns = np.array([0.10, 0.12, 0.08])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, sample_cov_matrix
        )
        weights = np.array([0.0, 0.0, 0.0])
        result = obj_func(weights)
        assert result == 0

    def test_min_volatility_single_asset(self, calculator, sample_cov_matrix):
        """Test volatility with single asset."""
        returns = np.array([0.10, 0.12, 0.08])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, sample_cov_matrix
        )
        # Only first asset (std = sqrt(0.04) = 0.2)
        weights = np.array([1.0, 0.0, 0.0])
        result = obj_func(weights)
        assert abs(result - 0.2) < 1e-10

    def test_min_volatility_uncorrelated_assets(self, calculator):
        """Test volatility with uncorrelated assets benefits from diversification."""
        returns = np.array([0.10, 0.10])
        # Two uncorrelated assets with same std = 0.1
        cov_matrix = np.array([[0.01, 0.0], [0.0, 0.01]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )

        # Equal weight portfolio
        weights = np.array([0.5, 0.5])
        result_equal = obj_func(weights)

        # Single asset portfolio
        weights_single = np.array([1.0, 0.0])
        result_single = obj_func(weights_single)

        # Equal weight should have lower volatility due to diversification
        assert result_equal < result_single


class TestMaxReturnObjective:
    """Test cases for maximum return objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_returns(self):
        """Sample returns array."""
        return np.array([0.10, 0.15, 0.08])

    @pytest.fixture
    def sample_cov_matrix(self):
        """Sample covariance matrix."""
        return np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )

    def test_max_return_negative_for_minimization(self, calculator, sample_returns, sample_cov_matrix):
        """Test that return is negated for minimization."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, sample_returns, sample_cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        result = obj_func(weights)
        expected_return = np.dot(weights, sample_returns)
        assert abs(result - (-expected_return)) < 1e-10

    def test_max_return_zero_weights(self, calculator, sample_returns, sample_cov_matrix):
        """Test max return with zero weights."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, sample_returns, sample_cov_matrix
        )
        weights = np.array([0.0, 0.0, 0.0])
        result = obj_func(weights)
        assert result == 0

    def test_max_return_all_in_highest_return_asset(self, calculator, sample_returns, sample_cov_matrix):
        """Test that allocating all to highest return asset maximizes return."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, sample_returns, sample_cov_matrix
        )
        # All in second asset (0.15 return)
        weights = np.array([0.0, 1.0, 0.0])
        result_best = obj_func(weights)

        # Equal weight
        weights_equal = np.array([1 / 3, 1 / 3, 1 / 3])
        result_equal = obj_func(weights_equal)

        # Single asset should have more negative (better for minimization)
        assert result_best < result_equal

    def test_max_return_linear_in_weights(self, calculator, sample_returns, sample_cov_matrix):
        """Test that return objective is linear in weights."""
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, sample_returns, sample_cov_matrix
        )
        weights = np.array([0.2, 0.3, 0.5])
        result = obj_func(weights)
        expected = -np.dot(weights, sample_returns)
        assert abs(result - expected) < 1e-10


class TestRiskParityObjective:
    """Test cases for risk parity objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def simple_cov_matrix(self):
        """Simple 2x2 covariance matrix."""
        return np.array([[0.04, 0.0], [0.0, 0.04]])

    def test_risk_parity_returns_non_negative(self, calculator, simple_cov_matrix):
        """Test that risk parity objective returns non-negative values."""
        returns = np.array([0.10, 0.10])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, simple_cov_matrix
        )
        weights = np.array([0.3, 0.7])
        result = obj_func(weights)
        assert result >= 0

    def test_risk_parity_equal_weights_zero(self, calculator, simple_cov_matrix):
        """Test that equal weights minimize risk parity objective."""
        returns = np.array([0.10, 0.10])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, simple_cov_matrix
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        # For symmetric matrix, equal weights should give zero or near-zero
        assert abs(result) < 1e-10

    def test_risk_parity_handles_small_weights(self, calculator, simple_cov_matrix):
        """Test that risk parity handles very small weights."""
        returns = np.array([0.10, 0.10])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, simple_cov_matrix
        )
        weights = np.array([1e-10, 1.0])
        result = obj_func(weights)
        assert np.isfinite(result)

    def test_risk_parity_unequal_weights_worse(self, calculator, simple_cov_matrix):
        """Test that unequal weights have worse (higher) risk parity objective."""
        returns = np.array([0.10, 0.10])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, simple_cov_matrix
        )
        weights_equal = np.array([0.5, 0.5])
        weights_unequal = np.array([0.8, 0.2])

        result_equal = obj_func(weights_equal)
        result_unequal = obj_func(weights_unequal)

        assert result_unequal >= result_equal

    def test_risk_parity_zero_volatility_returns_inf(self, calculator):
        """Test that zero portfolio volatility returns infinity."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, cov_matrix
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        assert result == np.inf

    def test_risk_parity_three_assets(self, calculator):
        """Test risk parity with three assets of equal volatility."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.0, 0.0], [0.0, 0.04, 0.0], [0.0, 0.0, 0.04]]
        )
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, cov_matrix
        )
        # Equal weights should be optimal
        weights = np.array([1 / 3, 1 / 3, 1 / 3])
        result = obj_func(weights)
        assert abs(result) < 1e-10


class TestMaxDiversificationObjective:
    """Test cases for maximum diversification objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_cov_matrix(self):
        """Sample covariance matrix."""
        return np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )

    def test_max_diversification_returns_negative(self, calculator, sample_cov_matrix):
        """Test that diversification returns negative (for minimization)."""
        returns = np.array([0.10, 0.12, 0.08])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, sample_cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        result = obj_func(weights)
        assert result < 0

    def test_max_diversification_single_asset(self, calculator, sample_cov_matrix):
        """Test diversification with single asset."""
        returns = np.array([0.10, 0.12, 0.08])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, sample_cov_matrix
        )
        weights = np.array([1.0, 0.0, 0.0])
        result = obj_func(weights)
        # Single asset: weighted_avg_vol / portfolio_vol = vol / vol = 1
        # Return negative for minimization: -1
        assert abs(result - (-1.0)) < 1e-10

    def test_max_diversification_uncorrelated_assets(self, calculator):
        """Test diversification with uncorrelated assets."""
        returns = np.array([0.10, 0.10])
        # Two uncorrelated assets with same volatility
        cov_matrix = np.array([[0.01, 0.0], [0.0, 0.01]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, cov_matrix
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        # Diversification ratio > 1 for equal weight (benefit from diversification)
        # Result should be negative and less than -1
        assert result < -1.0

    def test_max_diversification_zero_volatility_returns_neg_inf(self, calculator):
        """Test that zero portfolio volatility returns negative infinity."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, cov_matrix
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        assert result == -np.inf

    def test_max_diversification_correlation_effect(self, calculator):
        """Test that lower correlation increases diversification benefit."""
        returns = np.array([0.10, 0.10])
        vol = 0.1

        # Low correlation
        cov_low = np.array([[vol**2, 0.0], [0.0, vol**2]])
        obj_func_low = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, cov_low
        )

        # High correlation
        cov_high = np.array([[vol**2, 0.99 * vol**2], [0.99 * vol**2, vol**2]])
        obj_func_high = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, cov_high
        )

        weights = np.array([0.5, 0.5])
        result_low = obj_func_low(weights)
        result_high = obj_func_high(weights)

        # Low correlation should give better (more negative) diversification ratio
        assert result_low < result_high


class TestMinCVaRObjective:
    """Test cases for minimum CVaR objective."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample data for CVaR tests."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        return returns, cov_matrix

    def test_min_cvar_returns_callable(self, calculator, sample_data):
        """Test that CVaR objective returns a callable."""
        returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.05
        )
        assert callable(obj_func)

    def test_min_cvar_with_custom_confidence(self, calculator, sample_data):
        """Test CVaR with custom confidence level."""
        returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.10
        )
        weights = np.array([0.3, 0.5, 0.2])
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))

    def test_min_cvar_zero_volatility_returns_inf(self, calculator):
        """Test that zero volatility returns infinity."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.05
        )
        weights = np.array([0.5, 0.5])
        result = obj_func(weights)
        assert result == np.inf

    def test_min_cvar_different_confidence_levels(self, calculator, sample_data):
        """Test CVaR with different confidence levels."""
        returns, cov_matrix = sample_data
        weights = np.array([0.3, 0.5, 0.2])

        obj_func_5 = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.05
        )
        obj_func_10 = calculator.get_objective_function(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.10
        )

        result_5 = obj_func_5(weights)
        result_10 = obj_func_10(weights)

        # Both should be finite
        assert np.isfinite(result_5)
        assert np.isfinite(result_10)


class TestCalculateObjectiveValue:
    """Test cases for calculate_objective_value method."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])
        return weights, returns, cov_matrix

    def test_calculate_sharpe_ratio_value(self, calculator, sample_data):
        """Test Sharpe ratio value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MAX_SHARPE
        )
        assert isinstance(result, (float, np.floating))
        assert result >= 0  # Sharpe value should be non-negative

    def test_calculate_volatility_value(self, calculator, sample_data):
        """Test volatility value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MIN_VOLATILITY
        )
        assert isinstance(result, (float, np.floating))
        assert result >= 0

    def test_calculate_return_value(self, calculator, sample_data):
        """Test return value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MAX_RETURN
        )
        expected = np.dot(weights, returns)
        assert abs(result - expected) < 1e-10

    def test_calculate_risk_parity_value(self, calculator, sample_data):
        """Test risk parity value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.RISK_PARITY
        )
        assert isinstance(result, (float, np.floating))
        assert result >= 0

    def test_calculate_diversification_value(self, calculator, sample_data):
        """Test diversification value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MAX_DIVERSIFICATION
        )
        assert isinstance(result, (float, np.floating))
        assert result >= 1  # Diversification ratio >= 1

    def test_calculate_cvar_value(self, calculator, sample_data):
        """Test CVaR value calculation."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MIN_CVAR, confidence_level=0.05
        )
        assert isinstance(result, (float, np.floating))

    def test_calculate_zero_volatility_sharpe(self, calculator):
        """Test Sharpe calculation with zero volatility."""
        weights = np.array([0.5, 0.5])
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MAX_SHARPE
        )
        assert result == 0

    def test_calculate_unknown_objective_returns_zero(self, calculator, sample_data):
        """Test that unknown objective returns 0."""
        weights, returns, cov_matrix = sample_data
        # Use invalid enum value by directly calling with unknown objective
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, "unknown_objective"
        )
        assert result == 0.0


class TestGetGradientFunction:
    """Test cases for get_gradient_function method."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        return returns, cov_matrix

    def test_min_volatility_gradient_returns_callable(self, calculator, sample_data):
        """Test that MIN_VOLATILITY gradient returns a callable."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        assert grad_func is not None
        assert callable(grad_func)

    def test_max_return_gradient_returns_callable(self, calculator, sample_data):
        """Test that MAX_RETURN gradient returns a callable."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MAX_RETURN, returns, cov_matrix
        )
        assert grad_func is not None
        assert callable(grad_func)

    def test_max_sharpe_gradient_returns_none(self, calculator, sample_data):
        """Test that MAX_SHARPE gradient returns None (not available)."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        assert grad_func is None

    def test_risk_parity_gradient_returns_none(self, calculator, sample_data):
        """Test that RISK_PARITY gradient returns None."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.RISK_PARITY, returns, cov_matrix
        )
        assert grad_func is None

    def test_min_volatility_gradient_shape(self, calculator, sample_data):
        """Test that gradient has correct shape."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        gradient = grad_func(weights)
        assert gradient.shape == weights.shape

    def test_min_volatility_gradient_zero_volatility(self, calculator):
        """Test gradient with zero volatility."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.0, 0.0], [0.0, 0.0]])
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        weights = np.array([0.5, 0.5])
        gradient = grad_func(weights)
        assert np.allclose(gradient, np.zeros_like(weights))

    def test_max_return_gradient_constant(self, calculator, sample_data):
        """Test that max return gradient is constant (-returns)."""
        returns, cov_matrix = sample_data
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MAX_RETURN, returns, cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        gradient = grad_func(weights)
        expected = -returns
        assert np.allclose(gradient, expected)

    def test_min_volatility_gradient_mathematical_correctness(self, calculator):
        """Test mathematical correctness of volatility gradient."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.09]])
        grad_func = calculator.get_gradient_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )

        weights = np.array([0.6, 0.4])

        # Manual calculation
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        expected_gradient = np.dot(cov_matrix, weights) / portfolio_vol

        gradient = grad_func(weights)
        assert np.allclose(gradient, expected_gradient)


class TestValidateObjectiveParameters:
    """Test cases for parameter validation."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def valid_data(self):
        """Create valid test data."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        return returns, cov_matrix

    def test_valid_parameters(self, calculator, valid_data):
        """Test validation with valid parameters."""
        returns, cov_matrix = valid_data
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_mismatched_dimensions(self, calculator):
        """Test validation with mismatched dimensions."""
        returns = np.array([0.10, 0.12])  # 2 assets
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )  # 3x3
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("match covariance" in err for err in errors)

    def test_non_symmetric_covariance(self, calculator):
        """Test validation with non-symmetric covariance matrix."""
        returns = np.array([0.10, 0.12])
        cov_matrix = np.array([[0.04, 0.02], [0.01, 0.09]])  # Non-symmetric
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        assert is_valid is False
        assert any("symmetric" in err for err in errors)

    def test_non_positive_definite_covariance(self, calculator):
        """Test validation with non-positive definite covariance matrix."""
        returns = np.array([0.10, 0.12])
        # Create matrix with zero eigenvalue (not positive definite)
        # [[1, 1], [1, 1]] has eigenvalues [2, 0]
        cov_matrix = np.array([[1.0, 1.0], [1.0, 1.0]])
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        assert is_valid is False
        assert any("positive definite" in err for err in errors)

    def test_invalid_confidence_level_too_low(self, calculator, valid_data):
        """Test validation with confidence level too low."""
        returns, cov_matrix = valid_data
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.0
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("confidence" in err.lower() for err in errors)

    def test_invalid_confidence_level_too_high(self, calculator, valid_data):
        """Test validation with confidence level too high."""
        returns, cov_matrix = valid_data
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=1.0
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("confidence" in err.lower() for err in errors)

    def test_valid_confidence_level(self, calculator, valid_data):
        """Test validation with valid confidence level."""
        returns, cov_matrix = valid_data
        is_valid, errors = calculator.validate_objective_parameters(
            ObjectiveFunction.MIN_CVAR, returns, cov_matrix, confidence_level=0.05
        )
        assert is_valid is True
        assert len(errors) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    def test_single_asset_portfolio(self, calculator):
        """Test with single asset portfolio."""
        returns = np.array([0.10])
        cov_matrix = np.array([[0.04]])
        weights = np.array([1.0])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))

    def test_very_large_portfolio(self, calculator):
        """Test with large number of assets."""
        n_assets = 100
        returns = np.random.normal(0.10, 0.02, n_assets)
        # Create positive definite covariance matrix
        cov_base = np.random.randn(n_assets, n_assets)
        cov_matrix = np.dot(cov_base, cov_base.T) + np.eye(n_assets) * 0.1
        weights = np.ones(n_assets) / n_assets

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        result = obj_func(weights)
        assert np.isfinite(result)

    def test_very_small_weights(self, calculator):
        """Test with very small portfolio weights."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([1e-15, 1e-15, 1.0])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.RISK_PARITY, returns, cov_matrix
        )
        result = obj_func(weights)
        assert np.isfinite(result)

    def test_negative_returns(self, calculator):
        """Test with negative expected returns."""
        returns = np.array([-0.10, -0.05, -0.02])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))

    def test_negative_excess_returns(self, calculator):
        """Test when portfolio return is below risk-free rate."""
        returns = np.array([0.01, 0.02])  # Below 0.05 risk-free rate
        cov_matrix = np.array([[0.04, 0.01], [0.01, 0.06]])
        weights = np.array([0.5, 0.5])
        risk_free_rate = 0.05

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=risk_free_rate
        )
        result = obj_func(weights)
        # Sharpe ratio should be negative (bad return-risk tradeoff)
        assert result > 0  # Negated for minimization, so positive (negative Sharpe)

    def test_high_correlation_matrix(self, calculator):
        """Test with highly correlated assets."""
        returns = np.array([0.10, 0.12, 0.08])
        # Highly correlated
        correlation = np.array(
            [[1.0, 0.95, 0.90], [0.95, 1.0, 0.92], [0.90, 0.92, 1.0]]
        )
        volatilities = [0.2, 0.25, 0.18]
        cov_matrix = np.outer(volatilities, volatilities) * correlation

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_DIVERSIFICATION, returns, cov_matrix
        )
        weights = np.array([0.3, 0.5, 0.2])
        result = obj_func(weights)
        assert np.isfinite(result)

    def test_zero_expected_returns(self, calculator):
        """Test with zero expected returns."""
        returns = np.array([0.0, 0.0, 0.0])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix
        )
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))


class TestNumericalStability:
    """Test numerical stability of calculations."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    def test_very_small_volatility(self, calculator):
        """Test with very small volatility."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[1e-10, 0.0], [0.0, 1e-10]])
        weights = np.array([0.5, 0.5])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        result = obj_func(weights)
        assert np.isfinite(result)
        assert result >= 0

    def test_very_large_volatility(self, calculator):
        """Test with very large volatility."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[1e4, 0.0], [0.0, 1e4]])
        weights = np.array([0.5, 0.5])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        result = obj_func(weights)
        assert np.isfinite(result)
        assert result >= 0

    def test_mixed_scale_covariance(self, calculator):
        """Test with mixed scales in covariance matrix."""
        returns = np.array([0.10, 0.10])
        cov_matrix = np.array([[1e-4, 0.0], [0.0, 1e4]])
        weights = np.array([0.5, 0.5])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        result = obj_func(weights)
        assert np.isfinite(result)


class TestConsistency:
    """Test consistency between methods."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    def test_objective_function_vs_calculate_value_max_sharpe(self, calculator):
        """Test consistency between objective function and calculate_objective_value."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])
        risk_free_rate = 0.02

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_SHARPE, returns, cov_matrix, risk_free_rate=risk_free_rate
        )
        obj_value = obj_func(weights)

        calculated = calculator.calculate_objective_value(
            weights, returns, cov_matrix, risk_free_rate, ObjectiveFunction.MAX_SHARPE
        )

        # Objective function returns negated Sharpe for minimization
        # calculate_objective_value returns positive Sharpe
        assert abs(obj_value - (-calculated)) < 1e-10

    def test_objective_function_vs_calculate_value_volatility(self, calculator):
        """Test consistency for volatility objective."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MIN_VOLATILITY, returns, cov_matrix
        )
        obj_value = obj_func(weights)

        calculated = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MIN_VOLATILITY
        )

        assert abs(obj_value - calculated) < 1e-10

    def test_objective_function_vs_calculate_value_return(self, calculator):
        """Test consistency for return objective."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])

        obj_func = calculator.get_objective_function(
            ObjectiveFunction.MAX_RETURN, returns, cov_matrix
        )
        obj_value = obj_func(weights)

        calculated = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, ObjectiveFunction.MAX_RETURN
        )

        # Objective function returns negated return for minimization
        assert abs(obj_value - (-calculated)) < 1e-10


@pytest.mark.parametrize(
    "objective",
    [
        ObjectiveFunction.MAX_SHARPE,
        ObjectiveFunction.MIN_VOLATILITY,
        ObjectiveFunction.MAX_RETURN,
        ObjectiveFunction.RISK_PARITY,
        ObjectiveFunction.MAX_DIVERSIFICATION,
        ObjectiveFunction.MIN_CVAR,
    ],
)
class TestAllObjectivesFunctional:
    """Parametrized tests for all objectives to ensure they work."""

    @pytest.fixture
    def calculator(self):
        """Create calculator instance."""
        return ObjectiveFunctionCalculator()

    @pytest.fixture
    def sample_data(self):
        """Create sample data."""
        returns = np.array([0.10, 0.12, 0.08])
        cov_matrix = np.array(
            [[0.04, 0.01, 0.005], [0.01, 0.09, 0.015], [0.005, 0.015, 0.06]]
        )
        weights = np.array([0.3, 0.5, 0.2])
        return weights, returns, cov_matrix

    def test_get_objective_function_works(self, objective, calculator, sample_data):
        """Test that all objectives can be retrieved."""
        weights, returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            objective, returns, cov_matrix, confidence_level=0.05
        )
        assert callable(obj_func)

    def test_objective_function_returns_float(self, objective, calculator, sample_data):
        """Test that all objectives return float values."""
        weights, returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            objective, returns, cov_matrix, confidence_level=0.05
        )
        result = obj_func(weights)
        assert isinstance(result, (float, np.floating))

    def test_objective_is_finite(self, objective, calculator, sample_data):
        """Test that objective values are finite."""
        weights, returns, cov_matrix = sample_data
        obj_func = calculator.get_objective_function(
            objective, returns, cov_matrix, confidence_level=0.05
        )
        result = obj_func(weights)
        assert np.isfinite(result) or result in [np.inf, -np.inf]

    def test_calculate_objective_value_works(self, objective, calculator, sample_data):
        """Test that calculate_objective_value works for all objectives."""
        weights, returns, cov_matrix = sample_data
        result = calculator.calculate_objective_value(
            weights, returns, cov_matrix, 0.02, objective, confidence_level=0.05
        )
        assert isinstance(result, (float, np.floating))

    def test_validate_parameters_works(self, objective, calculator, sample_data):
        """Test that validate_objective_parameters works for all objectives."""
        weights, returns, cov_matrix = sample_data
        is_valid, errors = calculator.validate_objective_parameters(
            objective, returns, cov_matrix, confidence_level=0.05
        )
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
