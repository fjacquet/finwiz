"""
Tests for PerplexityFeatureFlagTracker in finwiz.tools.perplexity_logging.

The tracker is the feature-flag success/failure chokepoint used by
enhanced_sec_tool, alpha_vantage_tool, enhanced_crypto_tool, and
perplexity_analysis_integration.
"""

from finwiz.config.features.flags import FeatureFlags
from finwiz.tools.perplexity_logging import PerplexityFeatureFlagTracker


class TestPerplexityFeatureFlagTracker:
    """Test feature flag success/failure recording and circuit breaker status checks."""

    def test_should_record_success_when_perplexity_succeeds(self, mocker):
        """Test feature flag success recording for successful Perplexity calls."""
        # Arrange
        mock_feature_flags = mocker.Mock(spec=FeatureFlags)
        mocker.patch("finwiz.config.features.flags.get_feature_flags", return_value=mock_feature_flags)

        # Act
        PerplexityFeatureFlagTracker.record_operation_success("AAPL", "sentiment", 5)

        # Assert
        mock_feature_flags.record_success.assert_called_once_with("perplexity_research")

    def test_should_record_failure_when_perplexity_fails(self, mocker):
        """Test feature flag failure recording for API errors and timeouts."""
        # Arrange
        mock_feature_flags = mocker.Mock(spec=FeatureFlags)
        mocker.patch("finwiz.config.features.flags.get_feature_flags", return_value=mock_feature_flags)

        # Act
        PerplexityFeatureFlagTracker.record_operation_failure("AAPL", "sentiment", "timeout_error", False)

        # Assert
        mock_feature_flags.record_failure.assert_called_once_with("perplexity_research")

    def test_should_check_circuit_breaker_status(self, mocker):
        """Test circuit breaker status checking integration."""
        # Arrange
        mock_feature_flags = mocker.Mock(spec=FeatureFlags)
        mock_feature_flags.is_enabled.return_value = True
        mock_feature_flags.get_flag_status.return_value = {
            "circuit_breaker": {"is_open": False, "failure_count": 2},
            "fallback_strategy": "cached_only",
        }
        mocker.patch("finwiz.config.features.flags.get_feature_flags", return_value=mock_feature_flags)

        # Act
        status = PerplexityFeatureFlagTracker.check_circuit_breaker_status()

        # Assert
        assert status["is_enabled"] is True
        assert status["circuit_breaker_info"]["is_open"] is False
        assert status["fallback_strategy"] == "cached_only"
