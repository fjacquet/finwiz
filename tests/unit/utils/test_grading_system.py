"""
Unit tests for the grading system utilities.

Tests the conversion of composite scores to letter grades and
the generation of portfolio-wide grade summaries.
"""

from pytest import approx

from finwiz.scoring.grading_system import (
    format_grade_display,
    get_portfolio_grade_summary,
    score_to_grade,
)


class TestScoreToGrade:
    """Test score to grade conversion."""

    def test_should_return_a_plus_when_excellent_score(self):
        """Test A+ grade for excellent scores."""
        # Arrange
        score = 0.98

        # Act
        grade_info = score_to_grade(score)

        # Assert
        assert grade_info.grade == "A+"
        assert grade_info.percentage == approx(98.0)
        assert "Excellent" in grade_info.description
        assert "Augmentez" in grade_info.action
        assert grade_info.emoji == "🏆"

    def test_should_return_a_when_very_good_score(self):
        """Test A grade for very good scores."""
        # Arrange
        score = 0.88

        # Act
        grade_info = score_to_grade(score)

        # Assert
        assert grade_info.grade == "A"
        assert grade_info.percentage == approx(88.0)
        assert "Très bon" in grade_info.description

    def test_should_return_b_when_good_score(self):
        """Test B grade for good scores."""
        # Arrange
        score = 0.77

        # Act
        grade_info = score_to_grade(score)

        # Assert
        assert grade_info.grade == "B"
        assert grade_info.percentage == approx(77.0)
        assert "Bon" in grade_info.description
        assert "Maintenez" in grade_info.action

    def test_should_return_c_when_acceptable_score(self):
        """Test C grade for acceptable scores."""
        # Arrange
        score = 0.67

        # Act
        grade_info = score_to_grade(score)

        # Assert
        assert grade_info.grade == "C"
        assert grade_info.percentage == approx(67.0)
        assert "Passable" in grade_info.description

    def test_should_return_f_when_failing_score(self):
        """Test F grade for failing scores."""
        # Arrange
        score = 0.00

        # Act
        grade_info = score_to_grade(score)

        # Assert
        assert grade_info.grade == "F"
        assert grade_info.percentage == approx(0.0)
        assert "Échec" in grade_info.description
        assert "Vendez" in grade_info.action
        assert grade_info.emoji == "❌"

    def test_should_handle_boundary_scores(self):
        """Test boundary scores between grades."""
        # Test cases for grade boundaries
        test_cases = [
            (0.95, "A+"),
            (0.94, "A"),
            (0.85, "A"),
            (0.84, "B+"),
            (0.80, "B+"),
            (0.79, "B"),
            (0.75, "B"),
            (0.74, "C+"),
            (0.70, "C+"),
            (0.69, "C"),
            (0.65, "C"),
            (0.64, "D"),
            (0.50, "D"),
            (0.49, "F"),
        ]

        for score, expected_grade in test_cases:
            grade_info = score_to_grade(score)
            assert grade_info.grade == expected_grade, f"Score {score} should be grade {expected_grade}, got {grade_info.grade}"


class TestFormatGradeDisplay:
    """Test grade display formatting."""

    def test_should_format_with_percentage_by_default(self):
        """Test default formatting includes percentage."""
        # Arrange
        score = 0.77

        # Act
        result = format_grade_display(score)

        # Assert
        assert "✅ B (77%)" == result

    def test_should_format_without_percentage_when_requested(self):
        """Test formatting without percentage."""
        # Arrange
        score = 0.88

        # Act
        result = format_grade_display(score, include_percentage=False)

        # Assert
        assert "⭐ A" == result


class TestPortfolioGradeSummary:
    """Test portfolio-wide grade analysis."""

    def test_should_calculate_portfolio_average_correctly(self):
        """Test portfolio average calculation."""
        # Arrange
        scores = [0.80, 0.70, 0.60]  # B+, C+, D

        # Act
        summary = get_portfolio_grade_summary(scores)

        # Assert
        assert abs(summary["average_score"] - 0.70) < 0.01  # Allow for floating point precision
        assert abs(summary["average_percentage"] - 70.0) < 0.1
        assert summary["average_grade"] == "C+"
        assert summary["total_positions"] == 3

    def test_should_calculate_grade_distribution(self):
        """Test grade distribution calculation."""
        # Arrange
        scores = [0.88, 0.85, 0.77, 0.77, 0.00]  # A, A, B, B, F

        # Act
        summary = get_portfolio_grade_summary(scores)

        # Assert
        distribution = summary["distribution"]
        assert distribution["A"]["count"] == 2
        assert distribution["A"]["percentage"] == approx(40.0)
        assert distribution["B"]["count"] == 2
        assert distribution["B"]["percentage"] == approx(40.0)
        assert distribution["F"]["count"] == 1
        assert distribution["F"]["percentage"] == approx(20.0)

    def test_should_handle_empty_portfolio(self):
        """Test handling of empty portfolio."""
        # Arrange
        scores = []

        # Act
        summary = get_portfolio_grade_summary(scores)

        # Assert
        assert summary["average_grade"] == "N/A"
        assert summary["total_positions"] == 0
        assert summary["distribution"] == {}

    def test_should_handle_single_position(self):
        """Test handling of single position portfolio."""
        # Arrange
        scores = [0.85]

        # Act
        summary = get_portfolio_grade_summary(scores)

        # Assert
        assert summary["average_grade"] == "A"
        assert summary["total_positions"] == 1
        assert summary["distribution"]["A"]["count"] == 1
        assert summary["distribution"]["A"]["percentage"] == approx(100.0)


class TestGradeSystemIntegration:
    """Test integration scenarios."""

    def test_should_provide_consistent_grade_mapping(self):
        """Test that grade mapping is consistent across functions."""
        # Arrange
        test_scores = [0.98, 0.88, 0.77, 0.67, 0.00]

        # Act & Assert
        for score in test_scores:
            grade_info = score_to_grade(score)
            formatted = format_grade_display(score, include_percentage=False)

            # Check that emoji and grade are consistent
            assert grade_info.emoji in formatted
            assert grade_info.grade in formatted

    def test_should_handle_realistic_portfolio_scenario(self):
        """Test with realistic portfolio scores."""
        # Arrange - Typical portfolio with mostly good investments and few problems
        realistic_scores = [
            0.85,
            0.82,
            0.80,
            0.78,
            0.75,  # ETFs (good grades)
            0.77,
            0.75,
            0.72,
            0.68,  # Individual stocks (mixed)
            0.00,
            0.00,  # Two invalid positions
        ]

        # Act
        summary = get_portfolio_grade_summary(realistic_scores)

        # Assert
        assert summary["total_positions"] == 11
        assert 60 <= summary["average_percentage"] <= 75  # Adjusted range due to F grades
        assert "F" in summary["distribution"]  # Should have failing grades
        assert summary["distribution"]["F"]["count"] == 2  # Two failing positions
