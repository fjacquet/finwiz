"""
Unit tests for scoring utility functions.

Tests the threshold-based scoring utilities used across different scorers.
"""

from finwiz.scoring.scoring_utils import (
    calculate_threshold_score,
    interpolate_threshold_score,
)


class TestCalculateThresholdScore:
    """Test suite for calculate_threshold_score utility function."""

    def test_should_score_value_at_exact_threshold(self):
        """Test scoring when value exactly matches a threshold."""
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        score = calculate_threshold_score(0.15, thresholds)

        assert score == 0.8

    def test_should_score_value_between_thresholds(self):
        """Test scoring when value is between thresholds."""
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        score = calculate_threshold_score(0.12, thresholds)

        assert score == 0.6  # Should use the lower threshold's score

    def test_should_score_value_above_all_thresholds(self):
        """Test scoring when value exceeds all thresholds."""
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        score = calculate_threshold_score(0.25, thresholds)

        assert score == 1.0  # Should use the highest score

    def test_should_score_value_below_all_thresholds(self):
        """Test scoring when value is below all thresholds."""
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        score = calculate_threshold_score(0.03, thresholds)

        assert score == 0.0  # Should return 0.0 for values below first threshold

    def test_should_handle_reverse_scoring_lower_is_better(self):
        """Test reverse scoring where lower values get higher scores."""
        # Debt thresholds: lower debt = higher score
        thresholds = [(0.2, 1.0), (0.5, 0.8), (1.0, 0.6), (2.0, 0.4)]

        # Low debt should get high score
        score_low = calculate_threshold_score(0.15, thresholds, reverse=True)
        assert score_low == 1.0

        # Medium debt should get medium score
        score_med = calculate_threshold_score(0.7, thresholds, reverse=True)
        assert score_med == 0.8

        # High debt should get low score
        score_high = calculate_threshold_score(2.5, thresholds, reverse=True)
        assert score_high == 0.4

    def test_should_handle_empty_thresholds(self):
        """Test handling of empty thresholds list."""
        score = calculate_threshold_score(0.5, [], reverse=False)

        assert score == 0.5  # Should return neutral score

    def test_should_handle_single_threshold(self):
        """Test handling of single threshold."""
        thresholds = [(0.10, 0.8)]

        score_below = calculate_threshold_score(0.05, thresholds)
        score_above = calculate_threshold_score(0.15, thresholds)

        assert score_below == 0.0
        assert score_above == 0.8

    def test_should_handle_roe_scoring_pattern(self):
        """Test ROE scoring pattern (higher is better)."""
        roe_thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        # Excellent ROE
        assert calculate_threshold_score(0.25, roe_thresholds) == 1.0
        # Good ROE
        assert calculate_threshold_score(0.18, roe_thresholds) == 0.8
        # Acceptable ROE
        assert calculate_threshold_score(0.12, roe_thresholds) == 0.6
        # Poor ROE
        assert calculate_threshold_score(0.03, roe_thresholds) == 0.0

    def test_should_handle_expense_ratio_scoring_pattern(self):
        """Test expense ratio scoring pattern (lower is better)."""
        expense_thresholds = [(0.001, 1.0), (0.0025, 0.8), (0.005, 0.6), (0.01, 0.4)]

        # Excellent (very low expense)
        assert calculate_threshold_score(0.0005, expense_thresholds, reverse=True) == 1.0
        # Good
        assert calculate_threshold_score(0.002, expense_thresholds, reverse=True) == 1.0
        # Acceptable
        assert calculate_threshold_score(0.004, expense_thresholds, reverse=True) == 0.8
        # Poor (high expense)
        assert calculate_threshold_score(0.015, expense_thresholds, reverse=True) == 0.4


class TestInterpolateThresholdScore:
    """Test suite for interpolate_threshold_score utility function."""

    def test_should_interpolate_between_thresholds(self):
        """Test linear interpolation between threshold points."""
        thresholds = [(0.10, 0.6), (0.20, 1.0)]

        # Midpoint should be halfway between scores
        score = interpolate_threshold_score(0.15, thresholds)

        assert abs(score - 0.8) < 0.001  # Halfway between 0.6 and 1.0 (with floating point tolerance)

    def test_should_return_exact_score_at_threshold(self):
        """Test that exact threshold values return exact scores."""
        thresholds = [(0.10, 0.6), (0.20, 1.0)]

        score_lower = interpolate_threshold_score(0.10, thresholds)
        score_upper = interpolate_threshold_score(0.20, thresholds)

        assert score_lower == 0.6
        assert score_upper == 1.0

    def test_should_return_zero_below_first_threshold(self):
        """Test that values below first threshold return 0.0."""
        thresholds = [(0.10, 0.6), (0.20, 1.0)]

        score = interpolate_threshold_score(0.05, thresholds)

        assert score == 0.0

    def test_should_return_max_score_above_last_threshold(self):
        """Test that values above last threshold return max score."""
        thresholds = [(0.10, 0.6), (0.20, 1.0)]

        score = interpolate_threshold_score(0.25, thresholds)

        assert score == 1.0

    def test_should_handle_reverse_interpolation(self):
        """Test interpolation with reverse scoring."""
        thresholds = [(0.2, 1.0), (0.5, 0.6)]

        # Value between thresholds should interpolate
        score = interpolate_threshold_score(0.35, thresholds, reverse=True)

        # Should be between 1.0 and 0.6
        assert 0.6 < score < 1.0

    def test_should_handle_multiple_threshold_ranges(self):
        """Test interpolation across multiple threshold ranges."""
        thresholds = [(0.05, 0.4), (0.10, 0.6), (0.15, 0.8), (0.20, 1.0)]

        # Test interpolation in first range
        score1 = interpolate_threshold_score(0.075, thresholds)
        assert 0.4 < score1 < 0.6

        # Test interpolation in second range
        score2 = interpolate_threshold_score(0.125, thresholds)
        assert 0.6 < score2 < 0.8

        # Test interpolation in third range
        score3 = interpolate_threshold_score(0.175, thresholds)
        assert 0.8 < score3 < 1.0

    def test_should_handle_empty_thresholds(self):
        """Test handling of empty thresholds list."""
        score = interpolate_threshold_score(0.5, [])

        assert score == 0.5  # Should return neutral score
