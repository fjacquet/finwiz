"""
Tests for Perplexity feature flag integration behavior across all tools.

This module tests the PERPLEXITY_RESEARCH feature flag integration with various
analysis tools, ensuring proper fallback behavior and success/failure tracking.
"""

import asyncio
import os

from finwiz.config.features.flags import FeatureFlags, FeatureFlagStrategy
from finwiz.schemas.perplexity import SonarArticle, SonarSearchResult
from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool
from finwiz.tools.perplexity_analysis_integration import (
    PerplexityAnalysisIntegration,
)
from finwiz.tools.perplexity_logging import PerplexityFeatureFlagTracker


class TestPerplexityFeatureFlagIntegration:
    """Test feature flag integration behavior across all tools."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing feature flags instance
        import finwiz.config.features.flags

        finwiz.config.features.flags._feature_flags = None

    def test_should_enable_perplexity_when_flag_enabled(self, mocker):
        """Test tool behavior with PERPLEXITY_RESEARCH flag enabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Act
        tool = EnhancedSentimentAnalysisTool()
        perplexity_integration = tool._get_perplexity_integration()

        # Assert
        assert perplexity_integration is not None
        assert perplexity_integration.is_available is True

    def test_should_disable_perplexity_when_flag_disabled(self, mocker):
        """Test tool behavior with PERPLEXITY_RESEARCH flag disabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "false"})

        # Act
        tool = EnhancedSentimentAnalysisTool()
        perplexity_integration = tool._get_perplexity_integration()

        # Assert
        assert perplexity_integration is None

    def test_should_fallback_when_api_key_missing(self, mocker):
        """Test fallback behavior when API key is missing but flag is enabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true"})
        mocker.patch.dict(os.environ, {}, clear=True)  # Clear PPLX_API_KEY

        # Act
        tool = EnhancedSentimentAnalysisTool()
        perplexity_integration = tool._get_perplexity_integration()

        # Assert
        assert perplexity_integration is None

    def test_should_use_yahoo_only_when_perplexity_disabled(self, mocker):
        """Test that sentiment analysis uses only Yahoo Finance when Perplexity is disabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "false"})

        mock_yahoo_data = [
            {
                "title": "Apple Reports Strong Earnings",
                "publisher": "Reuters",
                "link": "https://example.com/apple-earnings",
                "providerPublishTime": 1640995200,  # 2022-01-01
                "summary": "Apple exceeded expectations",
                "source": "yahoo_finance",
            }
        ]

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool.data_sources, "get_news_data", return_value=mock_yahoo_data)

        # Act
        result = asyncio.run(tool.data_sources.get_enhanced_news_data("AAPL", "stock", 20))

        # Assert
        assert result["yahoo_articles"] == mock_yahoo_data
        assert result["sonar_articles"] == []
        assert result["combined_count"] == 1
        assert result["sonar_fallback_used"] is False

    def test_should_combine_sources_when_perplexity_enabled(self, mocker):
        """Test that sentiment analysis combines Yahoo and Sonar when Perplexity is enabled."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        mock_yahoo_data = [
            {
                "title": "Apple Reports Strong Earnings",
                "publisher": "Reuters",
                "link": "https://example.com/apple-earnings",
                "providerPublishTime": 1640995200,
                "summary": "Apple exceeded expectations",
                "source": "yahoo_finance",
            }
        ]

        mock_sonar_articles = [
            SonarArticle(
                title="Apple Stock Analysis",
                url="https://example.com/apple-analysis",
                summary="Technical analysis shows bullish trend",
                publisher="Bloomberg",
                published_date="2022-01-01T12:00:00Z",
                relevance_score=0.95,
                content_type="analysis",
                analysis_type="sentiment",
            )
        ]

        mock_sonar_result = SonarSearchResult(
            query="AAPL sentiment analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=mock_sonar_articles,
            total_results=1,
            search_time_ms=250,
            success=True,
        )

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool.data_sources, "get_news_data", return_value=mock_yahoo_data)

        # Mock the Perplexity integration
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=mock_sonar_result)
        mocker.patch.object(tool.data_sources, "get_perplexity_integration", return_value=mock_integration)

        # Act
        result = asyncio.run(tool.data_sources.get_enhanced_news_data("AAPL", "stock", 20))

        # Assert
        assert result["yahoo_articles"] == mock_yahoo_data
        assert result["sonar_articles"] == mock_sonar_articles
        assert result["combined_count"] == 2
        assert result["sonar_fallback_used"] is False

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

    def test_should_use_circuit_breaker_strategy_for_perplexity_flag(self, mocker):
        """Test that perplexity_research flag uses circuit breaker strategy."""
        # Arrange - mock env vars to ensure default values
        mocker.patch.dict(
            os.environ,
            {
                "FF_PERPLEXITY_BREAKER_THRESHOLD": "5",
                "FF_PERPLEXITY_BREAKER_TIMEOUT": "300",
            },
        )

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["perplexity_research"]
        assert config.strategy == FeatureFlagStrategy.CIRCUIT_BREAKER
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 300

    def test_should_fallback_gracefully_when_perplexity_fails(self, mocker):
        """Test graceful fallback when Perplexity integration fails."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        mock_yahoo_data = [
            {
                "title": "Apple Reports Strong Earnings",
                "publisher": "Reuters",
                "link": "https://example.com/apple-earnings",
                "providerPublishTime": 1640995200,
                "summary": "Apple exceeded expectations",
                "source": "yahoo_finance",
            }
        ]

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool.data_sources, "get_news_data", return_value=mock_yahoo_data)

        # Mock Perplexity integration to fail
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(side_effect=Exception("API Error"))
        mocker.patch.object(tool.data_sources, "get_perplexity_integration", return_value=mock_integration)

        # Mock feature flag tracker (patched where it's imported, not at module level)
        mock_tracker = mocker.patch("finwiz.tools.perplexity_logging.PerplexityFeatureFlagTracker")

        # Act
        result = asyncio.run(tool.data_sources.get_enhanced_news_data("AAPL", "stock", 20))

        # Assert
        assert result["yahoo_articles"] == mock_yahoo_data
        assert result["sonar_articles"] == []
        assert result["combined_count"] == 1
        assert result["sonar_fallback_used"] is True

        # Verify failure was recorded
        mock_tracker.record_operation_failure.assert_called_once_with("AAPL", "sentiment", "integration_error")

    def test_should_log_feature_flag_status_for_debugging(self, mocker):
        """Test that feature flag status is logged for debugging purposes."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Patch where it's actually imported
        mock_logger = mocker.patch("finwiz.tools.perplexity_analysis_integration.PerplexityOperationLogger")

        # Act
        tool = EnhancedSentimentAnalysisTool()
        tool.data_sources.get_perplexity_integration()

        # Assert
        # Note: fallback_strategy will be "disable" based on the actual flag definition
        mock_logger.log_feature_flag_status.assert_called_once()
        call_args = mock_logger.log_feature_flag_status.call_args[0]
        assert call_args[0] == "sentiment_analysis"
        assert call_args[1] is True

    def test_should_continue_reporter_flow_on_perplexity_failure(self, mocker):
        """Test that reporter flow continues uninterrupted when Perplexity fails."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        mock_yahoo_data = [
            {
                "title": "Apple Reports Strong Earnings",
                "publisher": "Reuters",
                "link": "https://example.com/apple-earnings",
                "providerPublishTime": 1640995200,
                "summary": "Apple exceeded expectations",
                "source": "yahoo_finance",
            }
        ]

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool.data_sources, "get_news_data", return_value=mock_yahoo_data)

        # Mock Perplexity integration to fail
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(side_effect=Exception("Network timeout"))
        mocker.patch.object(tool.data_sources, "get_perplexity_integration", return_value=mock_integration)

        # Act - This should not raise an exception
        result = asyncio.run(tool.data_sources.get_enhanced_news_data("AAPL", "stock", 20))

        # Assert - Flow continues with Yahoo data only
        assert result is not None
        assert result["yahoo_articles"] == mock_yahoo_data
        assert result["sonar_fallback_used"] is True

    def test_should_handle_missing_perplexity_integration_gracefully(self, mocker):
        """Test graceful handling when Perplexity integration cannot be initialized."""
        # Arrange
        mocker.patch.dict(os.environ, {"FF_PERPLEXITY_RESEARCH": "true"})

        # Mock the PerplexityAnalysisIntegration constructor to raise an exception
        original_init = PerplexityAnalysisIntegration.__init__

        def mock_init(self, *args, **kwargs):
            raise ImportError("Module not found")

        mocker.patch.object(PerplexityAnalysisIntegration, "__init__", side_effect=mock_init)

        # Act
        tool = EnhancedSentimentAnalysisTool()
        perplexity_integration = tool._get_perplexity_integration()

        # Assert
        assert perplexity_integration is None

    def test_should_validate_environment_variable_configuration(self, mocker):
        """Test that environment variables are properly validated for feature flag configuration."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {"FF_PERPLEXITY_RESEARCH": "true", "FF_PERPLEXITY_BREAKER_THRESHOLD": "3", "FF_PERPLEXITY_BREAKER_TIMEOUT": "600"},
        )

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["perplexity_research"]
        assert config.enabled is True
        assert config.circuit_breaker_threshold == 3
        assert config.circuit_breaker_timeout == 600

    def test_should_use_default_values_when_environment_invalid(self, mocker):
        """Test that default values are used when environment variables are invalid."""
        # Arrange
        mocker.patch.dict(
            os.environ,
            {
                "FF_PERPLEXITY_RESEARCH": "true",
                "FF_PERPLEXITY_BREAKER_THRESHOLD": "invalid",
                "FF_PERPLEXITY_BREAKER_TIMEOUT": "not_a_number",
            },
        )

        # Act
        flags = FeatureFlags()

        # Assert
        config = flags.flags["perplexity_research"]
        assert config.enabled is True
        assert config.circuit_breaker_threshold == 5  # Default value
        assert config.circuit_breaker_timeout == 300  # Default value
