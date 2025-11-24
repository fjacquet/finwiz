"""
Unit tests for DataQualityMetrics enhancements.

Tests the field-level tracking functionality added in Task 1.2.
"""

from pytest import approx

from finwiz.utils.data_quality_metrics import DataQualityMetrics


class TestFieldLevelTracking:
    """Test cases for field-level tracking functionality."""

    def test_should_track_calculated_fields(self):
        """Test tracking of successfully calculated fields."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])

        # Act
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")

        # Assert
        assert len(metrics.fields_calculated) == 2
        assert "volatility" in metrics.fields_calculated
        assert "max_drawdown" in metrics.fields_calculated

    def test_should_track_defaulted_fields(self):
        """Test tracking of fields using default values."""
        # Arrange
        metrics = DataQualityMetrics()

        # Act
        metrics.record_defaulted_field("volatility", 0.20)
        metrics.record_defaulted_field("beta", 1.0)

        # Assert
        assert len(metrics.fields_defaulted) == 2
        assert "volatility" in metrics.fields_defaulted
        assert "beta" in metrics.fields_defaulted

    def test_should_track_missing_fields(self):
        """Test tracking of completely missing fields."""
        # Arrange
        metrics = DataQualityMetrics()

        # Act
        metrics.record_missing_field("sharpe_ratio")
        metrics.record_missing_field("sortino_ratio")

        # Assert
        assert len(metrics.fields_missing) == 2
        assert "sharpe_ratio" in metrics.fields_missing
        assert "sortino_ratio" in metrics.fields_missing

    def test_should_not_duplicate_field_tracking(self):
        """Test that fields are not tracked multiple times."""
        # Arrange
        metrics = DataQualityMetrics()

        # Act
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("volatility")  # Duplicate
        metrics.record_calculated_field("volatility")  # Duplicate

        # Assert
        assert len(metrics.fields_calculated) == 1
        assert metrics.fields_calculated.count("volatility") == 1


class TestCompletenessScore:
    """Test cases for completeness score calculation."""

    def test_should_calculate_perfect_completeness(self):
        """Test completeness score when all fields are calculated."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")
        metrics.record_calculated_field("beta")

        # Act
        completeness = metrics.calculate_completeness_score()

        # Assert
        assert completeness == approx(1.0)

    def test_should_calculate_partial_completeness(self):
        """Test completeness score when some fields are calculated."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta", "sharpe_ratio"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")

        # Act
        completeness = metrics.calculate_completeness_score()

        # Assert
        assert completeness == approx(0.5)  # 2 out of 4 fields

    def test_should_return_neutral_when_no_fields_expected(self):
        """Test completeness score when no fields are expected."""
        # Arrange
        metrics = DataQualityMetrics()

        # Act
        completeness = metrics.calculate_completeness_score()

        # Assert
        assert completeness == approx(0.5)  # Neutral score


class TestQualityLevel:
    """Test cases for quality level determination."""

    def test_should_return_high_quality_level(self):
        """Test high quality level with good completeness and quality."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")
        metrics.record_calculated_field("beta")

        # Act
        quality_level = metrics.get_quality_level()

        # Assert
        assert quality_level == "high"

    def test_should_return_medium_quality_level(self):
        """Test medium quality level with acceptable completeness."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta", "sharpe_ratio"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")
        metrics.record_calculated_field("beta")
        # 3 out of 4 = 75% completeness

        # Act
        quality_level = metrics.get_quality_level()

        # Assert
        assert quality_level == "medium"

    def test_should_return_low_quality_level(self):
        """Test low quality level with poor completeness."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta", "sharpe_ratio"])
        metrics.record_calculated_field("volatility")
        # Only 1 out of 4 = 25% completeness

        # Act
        quality_level = metrics.get_quality_level()

        # Assert
        assert quality_level == "low"


class TestQualityScoreWithFieldTracking:
    """Test cases for quality score calculation with field tracking."""

    def test_should_penalize_defaulted_fields(self):
        """Test that defaulted fields reduce quality score."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")
        metrics.record_defaulted_field("beta", 1.0)

        # Act
        quality_score = metrics.calculate_quality_score()

        # Assert
        assert quality_score < 1.0  # Should be penalized
        assert quality_score > 0.5  # But not too low

    def test_should_penalize_missing_fields_more_than_defaulted(self):
        """Test that missing fields have higher penalty than defaulted."""
        # Arrange
        metrics_defaulted = DataQualityMetrics()
        metrics_defaulted.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics_defaulted.record_calculated_field("volatility")
        metrics_defaulted.record_calculated_field("max_drawdown")
        metrics_defaulted.record_defaulted_field("beta", 1.0)

        metrics_missing = DataQualityMetrics()
        metrics_missing.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics_missing.record_calculated_field("volatility")
        metrics_missing.record_calculated_field("max_drawdown")
        metrics_missing.record_missing_field("beta")

        # Act
        score_defaulted = metrics_defaulted.calculate_quality_score()
        score_missing = metrics_missing.calculate_quality_score()

        # Assert
        assert score_missing < score_defaulted  # Missing is worse than defaulted


class TestGetSummary:
    """Test cases for summary generation with field tracking."""

    def test_should_include_field_tracking_in_summary(self):
        """Test that summary includes field tracking information."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics.record_calculated_field("volatility")
        metrics.record_defaulted_field("max_drawdown", -0.20)
        metrics.record_missing_field("beta")

        # Act
        summary = metrics.get_summary()

        # Assert
        assert "field_tracking" in summary
        assert summary["field_tracking"]["calculated"] == 1
        assert summary["field_tracking"]["defaulted"] == 1
        assert summary["field_tracking"]["missing"] == 1
        assert summary["field_tracking"]["total_expected"] == 3

    def test_should_include_completeness_score_in_summary(self):
        """Test that summary includes completeness score."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown"])
        metrics.record_calculated_field("volatility")

        # Act
        summary = metrics.get_summary()

        # Assert
        assert "completeness_score" in summary
        assert summary["completeness_score"] == approx(0.5)  # 1 out of 2

    def test_should_include_quality_level_in_summary(self):
        """Test that summary includes quality level."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown", "beta"])
        metrics.record_calculated_field("volatility")
        metrics.record_calculated_field("max_drawdown")
        metrics.record_calculated_field("beta")

        # Act
        summary = metrics.get_summary()

        # Assert
        assert "quality_level" in summary
        assert summary["quality_level"] == "high"


class TestReset:
    """Test cases for metrics reset functionality."""

    def test_should_reset_field_tracking(self):
        """Test that reset clears field tracking lists."""
        # Arrange
        metrics = DataQualityMetrics()
        metrics.set_expected_fields(["volatility", "max_drawdown"])
        metrics.record_calculated_field("volatility")
        metrics.record_defaulted_field("max_drawdown", -0.20)

        # Act
        metrics.reset()

        # Assert
        assert len(metrics.fields_calculated) == 0
        assert len(metrics.fields_defaulted) == 0
        assert len(metrics.fields_missing) == 0
        assert metrics.total_fields_expected == 0
