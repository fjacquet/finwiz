"""
Unit tests for portfolio analyzer module.

Tests the PortfolioAnalyzer class functionality including weighting calculations,
rebalancing need identification, portfolio metrics, and error handling.
"""

from pytest import approx
from datetime import datetime

import pytest

from finwiz.quantitative.portfolio_analyzer import (
    InsufficientDataError,
    PortfolioAnalysisError,
    PortfolioAnalyzer,
)
from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PriceData,
)


class TestPortfolioAnalyzer:
    """Test cases for PortfolioAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PortfolioAnalyzer()

        # Sample holdings
        self.sample_holdings = [
            Holding(symbol="AAPL", shares=100.0),
            Holding(symbol="GOOGL", shares=10.0),
            Holding(symbol="MSFT", shares=50.0),
        ]

        # Sample prices
        self.sample_prices = {
            "AAPL": 150.0,
            "GOOGL": 2500.0,
            "MSFT": 300.0,
        }

        # Sample price data objects
        self.sample_price_data = {
            "AAPL": PriceData(symbol="AAPL", price=150.0, timestamp=datetime.now()),
            "GOOGL": PriceData(symbol="GOOGL", price=2500.0, timestamp=datetime.now()),
            "MSFT": PriceData(symbol="MSFT", price=300.0, timestamp=datetime.now()),
        }

    def test_should_calculate_correct_weightings_when_valid_portfolio_provided(self):
        """Test correct weighting calculation for valid portfolio."""
        # Act
        weightings = self.analyzer.calculate_current_weightings(self.sample_holdings, self.sample_prices)

        # Assert
        expected_total_value = 15000 + 25000 + 15000  # 55000
        assert abs(weightings["AAPL"] - (15000 / expected_total_value)) < 0.001
        assert abs(weightings["GOOGL"] - (25000 / expected_total_value)) < 0.001
        assert abs(weightings["MSFT"] - (15000 / expected_total_value)) < 0.001

        # Check that weights sum to 1.0
        total_weight = sum(weightings.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_should_raise_error_when_empty_holdings_provided(self):
        """Test error handling for empty holdings list."""
        # Act & Assert
        with pytest.raises(PortfolioAnalysisError, match="Cannot calculate weightings for empty portfolio"):
            self.analyzer.calculate_current_weightings([], self.sample_prices)

    def test_should_raise_error_when_missing_price_data(self):
        """Test error handling for missing price data."""
        # Arrange
        incomplete_prices = {"AAPL": 150.0, "GOOGL": 2500.0}  # Missing MSFT

        # Act & Assert
        with pytest.raises(InsufficientDataError) as exc_info:
            self.analyzer.calculate_current_weightings(self.sample_holdings, incomplete_prices)

        assert "MSFT" in str(exc_info.value)

    def test_should_raise_error_when_invalid_price_provided(self):
        """Test error handling for invalid (zero or negative) prices."""
        # Arrange
        invalid_prices = self.sample_prices.copy()
        invalid_prices["AAPL"] = 0.0

        # Act & Assert
        with pytest.raises(PortfolioAnalysisError, match="Invalid price for AAPL"):
            self.analyzer.calculate_current_weightings(self.sample_holdings, invalid_prices)

    def test_should_identify_rebalancing_needs_correctly(self):
        """Test identification of positions requiring rebalancing."""
        # Arrange
        current_weights = {"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34}
        tolerance_bands = {"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05}

        # Act
        needs = self.analyzer.identify_rebalancing_needs(current_weights, target_weights, tolerance_bands)

        # Assert
        assert len(needs) == 3

        # Check AAPL (overweight by 7%, exceeds 5% tolerance)
        aapl_need = next(n for n in needs if n.symbol == "AAPL")
        assert aapl_need.needs_rebalancing
        assert aapl_need.deviation == pytest.approx(0.07, abs=0.001)

        # Check MSFT (underweight by 9%, exceeds 5% tolerance)
        msft_need = next(n for n in needs if n.symbol == "MSFT")
        assert msft_need.needs_rebalancing
        assert msft_need.deviation == pytest.approx(-0.09, abs=0.001)

    def test_should_use_global_tolerance_when_position_tolerance_not_specified(self):
        """Test fallback to global tolerance for positions without specific tolerance."""
        # Arrange
        current_weights = {"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34}
        tolerance_bands = {"AAPL": 0.02}  # Only AAPL has specific tolerance
        global_tolerance = 0.1  # 10% global tolerance

        # Act
        needs = self.analyzer.identify_rebalancing_needs(current_weights, target_weights, tolerance_bands, global_tolerance)

        # Assert
        aapl_need = next(n for n in needs if n.symbol == "AAPL")
        googl_need = next(n for n in needs if n.symbol == "GOOGL")

        # AAPL should use specific tolerance (2%)
        assert aapl_need.tolerance_band == approx(0.02)
        assert aapl_need.needs_rebalancing  # 7% deviation > 2% tolerance

        # GOOGL should use global tolerance (10%)
        assert googl_need.tolerance_band == approx(0.1)
        assert not googl_need.needs_rebalancing  # 2% deviation < 10% tolerance

    def test_should_calculate_portfolio_metrics_correctly(self):
        """Test calculation of comprehensive portfolio metrics."""
        # Act
        metrics = self.analyzer.calculate_portfolio_metrics(self.sample_holdings, self.sample_prices)

        # Assert
        assert metrics.total_value == approx(55000.0)
        assert metrics.number_of_positions == 3
        assert metrics.largest_position_weight == pytest.approx(25000 / 55000, abs=0.001)  # GOOGL
        assert 0 <= metrics.concentration_risk_score <= 10
        assert 0 <= metrics.diversification_ratio <= 1
        assert metrics.effective_number_of_positions > 0

    def test_should_analyze_current_portfolio_without_targets(self):
        """Test portfolio analysis without target weights."""
        # Act
        analysis = self.analyzer.analyze_current_portfolio(self.sample_holdings, self.sample_price_data)

        # Assert
        assert analysis.total_value == approx(55000.0)
        assert len(analysis.weightings) == 3
        assert len(analysis.deviations_from_target) == 0  # No targets provided
        assert len(analysis.positions_needing_rebalancing) == 0
        assert "concentration_risk" in analysis.risk_metrics

    def test_should_analyze_current_portfolio_with_targets(self):
        """Test portfolio analysis with target weights."""
        # Arrange
        target_weights = {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.3}

        # Act
        analysis = self.analyzer.analyze_current_portfolio(self.sample_holdings, self.sample_price_data, target_weights)

        # Assert
        assert analysis.total_value == approx(55000.0)
        assert len(analysis.deviations_from_target) == 3

        # Check deviations
        expected_aapl_weight = 15000 / 55000  # ~0.273
        expected_deviation = expected_aapl_weight - 0.4
        assert analysis.deviations_from_target["AAPL"] == pytest.approx(expected_deviation, abs=0.001)

    def test_should_compare_allocations_correctly(self):
        """Test detailed allocation comparison."""
        # Arrange
        current_weights = {"AAPL": 0.3, "GOOGL": 0.4, "MSFT": 0.3}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34}

        # Act
        comparison = self.analyzer.compare_allocations(current_weights, target_weights)

        # Assert
        assert len(comparison) == 3

        # Check AAPL comparison
        aapl_comp = comparison["AAPL"]
        assert aapl_comp["current_weight"] == approx(0.3)
        assert aapl_comp["target_weight"] == approx(0.33)
        assert aapl_comp["absolute_deviation"] == pytest.approx(-0.03, abs=0.001)
        assert "Underweight" in aapl_comp["status"]

    def test_should_handle_new_positions_in_target_weights(self):
        """Test handling of positions in target but not in current portfolio."""
        # Arrange
        current_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "TSLA": 0.34}  # TSLA is new

        # Act
        comparison = self.analyzer.compare_allocations(current_weights, target_weights)

        # Assert
        assert len(comparison) == 3

        # Check new position
        tsla_comp = comparison["TSLA"]
        assert tsla_comp["current_weight"] == approx(0.0)
        assert tsla_comp["target_weight"] == approx(0.34)
        assert tsla_comp["absolute_deviation"] == approx(-0.34)

    def test_should_calculate_rebalancing_impact_correctly(self):
        """Test calculation of rebalancing impact analysis."""
        # Arrange
        current_weights = {"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34}
        total_value = 100000.0

        # Act
        impact = self.analyzer.calculate_rebalancing_impact(current_weights, target_weights, total_value)

        # Assert
        assert "total_turnover_percentage" in impact
        assert "number_of_trades_required" in impact
        assert "positions_to_buy" in impact
        assert "positions_to_sell" in impact
        assert "estimated_complexity" in impact

        # Check specific calculations
        assert "AAPL" in impact["positions_to_sell"]  # Overweight
        assert "MSFT" in impact["positions_to_buy"]  # Underweight

    def test_should_calculate_concentration_risk_correctly(self):
        """Test concentration risk calculation."""
        # Test equal weights (low concentration)
        equal_weights = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
        equal_risk = self.analyzer._calculate_concentration_risk(equal_weights)

        # Test concentrated portfolio (high concentration)
        concentrated_weights = {"A": 0.8, "B": 0.1, "C": 0.05, "D": 0.05}
        concentrated_risk = self.analyzer._calculate_concentration_risk(concentrated_weights)

        # Assert
        assert 0 <= equal_risk <= 10
        assert 0 <= concentrated_risk <= 10
        assert concentrated_risk > equal_risk

    def test_should_calculate_diversification_ratio_correctly(self):
        """Test diversification ratio calculation."""
        # Test equal weights (high diversification)
        equal_weights = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
        equal_div = self.analyzer._calculate_diversification_ratio(equal_weights)

        # Test concentrated portfolio (low diversification)
        concentrated_weights = {"A": 0.8, "B": 0.1, "C": 0.05, "D": 0.05}
        concentrated_div = self.analyzer._calculate_diversification_ratio(concentrated_weights)

        # Assert
        assert 0 <= equal_div <= 1
        assert 0 <= concentrated_div <= 1
        assert equal_div > concentrated_div

    def test_should_calculate_effective_positions_correctly(self):
        """Test effective number of positions calculation."""
        # Test equal weights
        equal_weights = {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}
        equal_effective = self.analyzer._calculate_effective_positions(equal_weights)

        # Test concentrated portfolio
        concentrated_weights = {"A": 0.8, "B": 0.1, "C": 0.05, "D": 0.05}
        concentrated_effective = self.analyzer._calculate_effective_positions(concentrated_weights)

        # Assert
        assert equal_effective == pytest.approx(4.0, abs=0.1)  # Should be close to actual number
        assert concentrated_effective < equal_effective
        assert concentrated_effective > 1.0  # Should be greater than 1

    def test_should_handle_empty_weightings_gracefully(self):
        """Test handling of empty weightings in metric calculations."""
        # Act
        concentration_risk = self.analyzer._calculate_concentration_risk({})
        diversification_ratio = self.analyzer._calculate_diversification_ratio({})
        effective_positions = self.analyzer._calculate_effective_positions({})

        # Assert
        assert concentration_risk == approx(0.0)
        assert diversification_ratio == approx(0.0)
        assert effective_positions == approx(0.0)

    def test_should_assess_rebalancing_complexity_correctly(self):
        """Test rebalancing complexity assessment."""
        # Test simple rebalancing
        simple_complexity = self.analyzer._assess_rebalancing_complexity(1, 5.0)
        assert simple_complexity == "Simple"

        # Test moderate rebalancing
        moderate_complexity = self.analyzer._assess_rebalancing_complexity(3, 15.0)
        assert moderate_complexity == "Moderate"

        # Test complex rebalancing
        complex_complexity = self.analyzer._assess_rebalancing_complexity(8, 40.0)
        assert complex_complexity == "Complex"

        # Test very complex rebalancing
        very_complex_complexity = self.analyzer._assess_rebalancing_complexity(15, 80.0)
        assert very_complex_complexity == "Very Complex"

        # Test no action required
        no_action_complexity = self.analyzer._assess_rebalancing_complexity(0, 0.0)
        assert no_action_complexity == "No Action Required"

    def test_should_get_position_status_correctly(self):
        """Test position status determination."""
        # Test on target
        assert self.analyzer._get_position_status(0.005, 0.3) == "On Target"

        # Test overweight variations
        assert "Slightly Overweight" in self.analyzer._get_position_status(0.03, 0.3)
        assert "Overweight" in self.analyzer._get_position_status(0.07, 0.3)
        assert "Significantly Overweight" in self.analyzer._get_position_status(0.15, 0.3)

        # Test underweight variations
        assert "Slightly Underweight" in self.analyzer._get_position_status(-0.03, 0.3)
        assert "Underweight" in self.analyzer._get_position_status(-0.07, 0.3)
        assert "Significantly Underweight" in self.analyzer._get_position_status(-0.15, 0.3)

    def test_should_sort_rebalancing_needs_by_urgency(self):
        """Test that rebalancing needs are sorted by urgency score."""
        # Arrange
        current_weights = {"AAPL": 0.5, "GOOGL": 0.3, "MSFT": 0.2}
        target_weights = {"AAPL": 0.33, "GOOGL": 0.33, "MSFT": 0.34}
        tolerance_bands = {"AAPL": 0.05, "GOOGL": 0.05, "MSFT": 0.05}

        # Act
        needs = self.analyzer.identify_rebalancing_needs(current_weights, target_weights, tolerance_bands)

        # Assert
        # Should be sorted by urgency score (highest first)
        for i in range(len(needs) - 1):
            assert needs[i].urgency_score >= needs[i + 1].urgency_score

    def test_should_raise_error_for_invalid_rebalancing_needs_input(self):
        """Test error handling for invalid rebalancing needs input."""
        # Test empty current weights
        with pytest.raises(PortfolioAnalysisError, match="Current and target weights are required"):
            self.analyzer.identify_rebalancing_needs({}, {"AAPL": 0.5}, {})

        # Test empty target weights
        with pytest.raises(PortfolioAnalysisError, match="Current and target weights are required"):
            self.analyzer.identify_rebalancing_needs({"AAPL": 0.5}, {}, {})

    def test_should_calculate_risk_metrics_comprehensively(self):
        """Test comprehensive risk metrics calculation."""
        # Arrange
        weightings = {"AAPL": 0.4, "GOOGL": 0.3, "MSFT": 0.2, "TSLA": 0.1}

        # Act
        risk_metrics = self.analyzer._calculate_risk_metrics(weightings)

        # Assert
        required_metrics = [
            "concentration_risk",
            "diversification_ratio",
            "effective_positions",
            "largest_position",
            "top_5_concentration",
        ]

        for metric in required_metrics:
            assert metric in risk_metrics
            assert isinstance(risk_metrics[metric], (int, float))

        # Validate specific values
        assert risk_metrics["largest_position"] == approx(0.4)  # AAPL
        assert risk_metrics["top_5_concentration"] == approx(1.0)  # All positions (only 4)


class TestPortfolioAnalyzerEdgeCases:
    """Test edge cases and error conditions for PortfolioAnalyzer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = PortfolioAnalyzer()

    def test_should_handle_single_position_portfolio(self):
        """Test handling of single-position portfolio."""
        # Arrange
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        prices = {"AAPL": 150.0}

        # Act
        weightings = self.analyzer.calculate_current_weightings(holdings, prices)
        metrics = self.analyzer.calculate_portfolio_metrics(holdings, prices)

        # Assert
        assert weightings["AAPL"] == approx(1.0)
        assert metrics.number_of_positions == 1
        assert metrics.largest_position_weight == approx(1.0)
        assert metrics.concentration_risk_score == approx(10.0)  # Maximum concentration

    def test_should_handle_very_small_positions(self):
        """Test handling of very small position sizes."""
        # Arrange
        holdings = [
            Holding(symbol="AAPL", shares=0.001),
            Holding(symbol="GOOGL", shares=0.001),
        ]
        prices = {"AAPL": 150.0, "GOOGL": 2500.0}

        # Act
        weightings = self.analyzer.calculate_current_weightings(holdings, prices)

        # Assert
        total_value = 0.001 * 150 + 0.001 * 2500  # 2.65
        expected_aapl_weight = (0.001 * 150) / total_value
        assert weightings["AAPL"] == pytest.approx(expected_aapl_weight, abs=0.001)

    def test_should_handle_zero_tolerance_gracefully(self):
        """Test handling of very small tolerance bands."""
        # Arrange
        current_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        tolerance_bands = {"AAPL": 0.001}  # Very small tolerance (schema requires > 0)

        # Act
        needs = self.analyzer.identify_rebalancing_needs(current_weights, target_weights, tolerance_bands, global_tolerance=0.05)

        # Assert
        # With very small tolerance, any deviation triggers rebalancing
        # Since current == target, no rebalancing needed
        aapl_needs = [n for n in needs if n.symbol == "AAPL"]
        assert len(aapl_needs) == 0 or not aapl_needs[0].needs_rebalancing

    def test_should_handle_missing_current_positions(self):
        """Test handling when target includes positions not currently held."""
        # Arrange
        current_weights = {"AAPL": 1.0}  # Only AAPL held
        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}  # Want to add GOOGL
        tolerance_bands = {}

        # Act
        needs = self.analyzer.identify_rebalancing_needs(current_weights, target_weights, tolerance_bands)

        # Assert
        googl_need = next(n for n in needs if n.symbol == "GOOGL")
        assert googl_need.current_weight == approx(0.0)
        assert googl_need.target_weight == approx(0.5)
        assert googl_need.needs_rebalancing  # 50% deviation > 5% default tolerance