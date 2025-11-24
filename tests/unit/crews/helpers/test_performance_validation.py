"""
Unit tests for performance validation helpers.

Tests the externalized performance validation logic to ensure correct
validation against target metrics.
"""

import pytest
from pytest import approx

from finwiz.crews.helpers.performance_validation import validate_performance_targets


class TestValidatePerformanceTargets:
    """Test suite for validate_performance_targets function."""

    def test_should_validate_pure_python_targets_when_ai_summary_disabled(self):
        """Test validation of pure Python performance targets."""
        # Arrange
        ticker = "AAPL"
        execution_time = 20.0  # Within 10-30s target
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["approach"] == "PURE PYTHON"
        assert result["execution_time"] == approx(20.0)
        assert result["llm_calls"] == 0
        assert result["cost_usd"] == approx(0.0)
        assert result["time_target_met"] is True
        assert result["llm_target_met"] is True
        assert result["cost_target_met"] is True
        assert result["speedup_factor"] > 10  # Should be 10-20x faster
        assert result["cost_reduction_pct"] == approx(100.0)

    def test_should_validate_hybrid_targets_when_ai_summary_enabled(self):
        """Test validation of hybrid approach performance targets."""
        # Arrange
        ticker = "GOOGL"
        execution_time = 25.0  # Within 15-40s target
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = True

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["ticker"] == "GOOGL"
        assert result["approach"] == "HYBRID"
        assert result["execution_time"] == approx(25.0)
        assert result["llm_calls"] == 1
        assert result["cost_usd"] == approx(0.01)
        assert result["time_target_met"] is True
        assert result["llm_target_met"] is True
        assert result["cost_target_met"] is True
        assert result["speedup_factor"] > 8  # Should be 8-15x faster
        assert result["cost_reduction_pct"] >= 80.0

    def test_should_fail_time_target_when_execution_too_slow(self):
        """Test that time target fails when execution is too slow."""
        # Arrange
        ticker = "MSFT"
        execution_time = 50.0  # Exceeds 30s target for pure Python
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["time_target_met"] is False
        assert result["all_targets_met"] is False

    def test_should_fail_time_target_when_execution_too_fast(self):
        """Test that time target fails when execution is suspiciously fast."""
        # Arrange
        ticker = "TSLA"
        execution_time = 5.0  # Below 10s minimum for pure Python
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["time_target_met"] is False
        assert result["all_targets_met"] is False

    def test_should_calculate_speedup_factor_correctly(self):
        """Test that speedup factor is calculated correctly."""
        # Arrange
        ticker = "NVDA"
        execution_time = 20.0  # 20 seconds
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False
        # Baseline average: (5*60 + 10*60) / 2 = 450 seconds
        # Expected speedup: 450 / 20 = 22.5x

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["speedup_factor"] == pytest.approx(22.5, rel=0.1)
        assert result["speedup_target_met"] is True

    def test_should_calculate_cost_reduction_correctly_for_pure_python(self):
        """Test that cost reduction is 100% for pure Python."""
        # Arrange
        ticker = "AMD"
        execution_time = 15.0
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["cost_reduction_pct"] == approx(100.0)
        assert result["cost_reduction_target_met"] is True

    def test_should_calculate_cost_reduction_correctly_for_hybrid(self):
        """Test that cost reduction is 80-90% for hybrid approach."""
        # Arrange
        ticker = "INTC"
        execution_time = 30.0
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = True
        # Baseline average: ($0.05 + $0.10) / 2 = $0.075
        # Hybrid cost: $0.01
        # Expected reduction: (0.075 - 0.01) / 0.075 * 100 = 86.67%

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["cost_reduction_pct"] == pytest.approx(86.67, rel=0.1)
        assert result["cost_reduction_target_met"] is True

    def test_should_include_targets_in_result(self):
        """Test that target values are included in result for reference."""
        # Arrange
        ticker = "META"
        execution_time = 20.0
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert "targets" in result
        assert result["targets"]["approach"] == "PURE PYTHON"
        assert result["targets"]["time_range"] == "10-30s"
        assert result["targets"]["llm_calls"] == 0
        assert result["targets"]["cost"] == "$0.00"
        assert "speedup_range" in result["targets"]
        assert "cost_reduction" in result["targets"]

    def test_should_set_all_targets_met_when_all_pass(self):
        """Test that all_targets_met is True when all targets pass."""
        # Arrange
        ticker = "NFLX"
        execution_time = 20.0  # Within target
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["time_target_met"] is True
        assert result["llm_target_met"] is True
        assert result["cost_target_met"] is True
        assert result["speedup_target_met"] is True
        assert result["cost_reduction_target_met"] is True
        assert result["all_targets_met"] is True

    def test_should_handle_zero_execution_time_gracefully(self):
        """Test that zero execution time doesn't cause division by zero."""
        # Arrange
        ticker = "AAPL"
        execution_time = 0.0
        api_metrics = {"api_calls": 5}
        ai_summary_enabled = False

        # Act
        result = validate_performance_targets(ticker, execution_time, api_metrics, ai_summary_enabled)

        # Assert
        assert result["speedup_factor"] == 0
        assert result["time_target_met"] is False
