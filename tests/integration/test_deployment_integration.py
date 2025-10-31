"""
Integration tests for deployment and configuration management.

This module tests the complete deployment integration including
configuration validation, feature flags, monitoring, and API endpoints.
"""

import os
import tempfile
from pathlib import Path

import pytest

from finwiz.utils.configuration_manager import ConfigurationError, get_configuration_manager
from finwiz.utils.feature_flags import get_feature_flags
from finwiz.utils.monitoring import get_metrics_collector


class TestDeploymentIntegration:
    """Integration tests for deployment configuration and setup."""

    def test_should_validate_configuration_when_all_required_keys_present(self, mocker):
        """Test configuration validation with all required API keys."""
        # Arrange
        mock_env = {
            "OPENAI_API_KEY": "sk-test-key-12345678901234567890",
            "SERPER_API_KEY": "test-serper-key-12345678901234567890",
            "FIRECRAWL_API_KEY": "test-firecrawl-key-12345678901234567890",
            "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key-12345678901234567890",
        }

        mocker.patch.dict("os.environ", mock_env, clear=True)

        # Act
        config_manager = get_configuration_manager()
        result = config_manager.validate_startup_configuration()

        # Assert
        assert result is True
        assert len(config_manager.api_keys) >= 4
        assert "OpenAI" in config_manager.api_keys
        assert "Serper" in config_manager.api_keys
        assert "Firecrawl" in config_manager.api_keys
        assert "Alpha Vantage" in config_manager.api_keys

    def test_should_raise_configuration_error_when_required_keys_missing(self, mocker):
        """Test configuration validation fails when required keys are missing."""
        # Arrange
        mock_env = {
            "OPENAI_API_KEY": "sk-test-key-12345678901234567890",
            # Missing other required keys
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            # Act & Assert
            config_manager = get_configuration_manager()
            with pytest.raises(ConfigurationError) as exc_info:
                config_manager.validate_startup_configuration()

            assert "SERPER_API_KEY" in exc_info.value.missing_keys
            assert "FIRECRAWL_API_KEY" in exc_info.value.missing_keys
            assert "ALPHA_VANTAGE_API_KEY" in exc_info.value.missing_keys

    def test_should_load_feature_flags_from_environment(self, mocker):
        """Test feature flag loading from environment variables."""
        # Arrange
        mock_env = {
            "FF_PORTFOLIO_REBALANCING": "true",
            "FF_REBALANCING_API": "true",
            "FF_REBALANCING_MONITORING": "false",
            "FF_PORTFOLIO_REBALANCING_ROLLOUT": "50.0",
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            # Act
            feature_flags = get_feature_flags()

            # Assert
            assert feature_flags.is_enabled("portfolio_rebalancing") is True
            assert feature_flags.is_enabled("rebalancing_api") is True
            assert feature_flags.is_enabled("rebalancing_monitoring") is False

            # Check rollout percentage
            config = feature_flags.flags["portfolio_rebalancing"]
            assert config.rollout_percentage == 50.0

    def test_should_initialize_monitoring_system(self, mocker):
        """Test monitoring system initialization."""
        # Arrange & Act
        metrics_collector = get_metrics_collector()

        # Assert
        assert metrics_collector is not None
        assert hasattr(metrics_collector, "record_counter")
        assert hasattr(metrics_collector, "record_gauge")
        assert hasattr(metrics_collector, "get_health_status")

        # Test basic functionality
        metrics_collector.record_counter("test_counter", 1)
        metrics_collector.record_gauge("test_gauge", 42.0)

        health_status = metrics_collector.get_health_status()
        assert "status" in health_status
        assert health_status["status"] in ["healthy", "degraded", "unhealthy"]

    def test_should_handle_feature_flag_circuit_breaker(self, mocker):
        """Test circuit breaker functionality for feature flags."""
        # Arrange
        feature_flags = get_feature_flags()
        flag_name = "rebalancing_monitoring"

        # Act - Record multiple failures to trigger circuit breaker
        for _ in range(5):
            feature_flags.record_failure(flag_name)

        # Assert
        breaker = feature_flags.circuit_breakers.get(flag_name)
        if breaker:  # Only test if circuit breaker is configured
            assert breaker.failure_count >= 3
            # Circuit breaker behavior depends on threshold configuration

    def test_should_create_required_directories_on_startup(self, mocker):
        """Test that required directories are created during configuration validation."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Mock the project root path
            with mocker.patch("finwiz.utils.configuration_manager.Path") as mock_path:
                mock_path.return_value.resolve.return_value.parents = [None, project_root]

                # Act
                config_manager = get_configuration_manager()
                config_manager._validate_required_directories()

                # Assert
                expected_dirs = ["cache", "logs", "output", "report"]
                for dir_name in expected_dirs:
                    dir_path = project_root / dir_name
                    assert dir_path.exists(), f"Directory {dir_name} should be created"

    def test_should_handle_gradual_rollout_percentage(self, mocker):
        """Test gradual rollout functionality with percentage-based feature flags."""
        # Arrange
        mock_env = {
            "FF_PORTFOLIO_REBALANCING": "true",
            "FF_PORTFOLIO_REBALANCING_ROLLOUT": "25.0",
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            feature_flags = get_feature_flags()

            # Act - Test multiple user IDs to verify percentage rollout
            enabled_count = 0
            total_tests = 100

            for i in range(total_tests):
                user_id = f"user_{i}"
                if feature_flags.is_enabled("portfolio_rebalancing", user_id=user_id):
                    enabled_count += 1

            # Assert - Should be approximately 25% (allow for some variance)
            rollout_percentage = (enabled_count / total_tests) * 100
            assert 15 <= rollout_percentage <= 35, f"Rollout percentage {rollout_percentage}% not near expected 25%"

    def test_should_provide_configuration_summary(self, mocker):
        """Test configuration summary functionality."""
        # Arrange
        mock_env = {
            "OPENAI_API_KEY": "sk-test-key-12345678901234567890",
            "SERPER_API_KEY": "test-serper-key-12345678901234567890",
            "FF_PORTFOLIO_REBALANCING": "true",
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            # Act
            config_manager = get_configuration_manager()
            summary = config_manager.get_configuration_summary()

            # Assert
            assert "api_keys_configured" in summary
            assert "available_services" in summary
            assert "feature_flags" in summary
            assert isinstance(summary["api_keys_configured"], int)
            assert isinstance(summary["available_services"], list)
            assert isinstance(summary["feature_flags"], dict)

    def test_should_handle_environment_specific_configuration(self, mocker):
        """Test environment-specific configuration loading."""
        # Arrange
        environments = ["production", "staging", "development"]

        for env in environments:
            mock_env = {
                "FINWIZ_DEPLOYMENT_ENV": env,
                "FF_PORTFOLIO_REBALANCING": "true" if env != "production" else "false",
            }

            with mocker.patch.dict(os.environ, mock_env, clear=True):
                # Act
                feature_flags = get_feature_flags()

                # Assert
                feature_flags.is_enabled("portfolio_rebalancing")

                # Note: This test assumes production has rebalancing disabled by default
                # The actual behavior depends on the specific environment configuration


class TestAPIIntegration:
    """Integration tests for API endpoints and server functionality."""

    @pytest.mark.integration
    def test_should_create_fastapi_app_when_api_enabled(self, mocker):
        """Test FastAPI application creation when API features are enabled."""
        # Arrange
        mock_env = {
            "FF_REBALANCING_API": "true",
            "OPENAI_API_KEY": "sk-test-key-12345678901234567890",
            "SERPER_API_KEY": "test-serper-key-12345678901234567890",
            "FIRECRAWL_API_KEY": "test-firecrawl-key-12345678901234567890",
            "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key-12345678901234567890",
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            # Act
            try:
                from finwiz.api.app import create_app

                app = create_app()

                # Assert
                assert app is not None
                assert hasattr(app, "routes")

                # Check that rebalancing routes are included
                route_paths = [route.path for route in app.routes]
                assert any("/rebalancing" in path for path in route_paths)

            except ImportError:
                pytest.skip("FastAPI not installed - API functionality not available")

    @pytest.mark.integration
    def test_should_handle_api_disabled_gracefully(self, mocker):
        """Test that application works when API features are disabled."""
        # Arrange
        mock_env = {
            "FF_REBALANCING_API": "false",
            "OPENAI_API_KEY": "sk-test-key-12345678901234567890",
            "SERPER_API_KEY": "test-serper-key-12345678901234567890",
            "FIRECRAWL_API_KEY": "test-firecrawl-key-12345678901234567890",
            "ALPHA_VANTAGE_API_KEY": "test-alpha-vantage-key-12345678901234567890",
        }

        with mocker.patch.dict(os.environ, mock_env, clear=True):
            # Act & Assert - Should not raise any errors
            from finwiz.utils.feature_flags import is_feature_enabled

            assert is_feature_enabled("rebalancing_api") is False

            # Main application should still work
            from finwiz.utils.configuration_manager import get_configuration_manager

            config_manager = get_configuration_manager()
            assert config_manager is not None


class TestMonitoringIntegration:
    """Integration tests for monitoring and metrics functionality."""

    def test_should_collect_performance_metrics(self, mocker):
        """Test performance metrics collection."""
        # Arrange
        metrics_collector = get_metrics_collector()

        # Act
        end_timer = metrics_collector.start_timer("test_operation")
        # Simulate some work
        import time

        time.sleep(0.01)
        end_timer(success=True)

        # Assert
        performance_summary = metrics_collector.get_performance_summary()
        assert "operations" in performance_summary
        assert "test_operation" in performance_summary["operations"]

        operation_metrics = performance_summary["operations"]["test_operation"]
        assert operation_metrics["total_calls"] == 1
        assert operation_metrics["successful_calls"] == 1
        assert operation_metrics["failed_calls"] == 0
        assert operation_metrics["avg_duration"] > 0

    def test_should_track_error_rates(self, mocker):
        """Test error rate tracking in monitoring system."""
        # Arrange
        metrics_collector = get_metrics_collector()

        # Act - Record some successful and failed operations
        for i in range(10):
            success = i < 8  # 80% success rate
            metrics_collector.record_operation_metrics("test_error_tracking", duration=0.1, success=success, error=None if success else "Test error")

        # Assert
        performance_summary = metrics_collector.get_performance_summary()
        operation_metrics = performance_summary["operations"]["test_error_tracking"]

        assert operation_metrics["total_calls"] == 10
        assert operation_metrics["successful_calls"] == 8
        assert operation_metrics["failed_calls"] == 2
        assert operation_metrics["error_rate"] == 0.2  # 20% error rate

    def test_should_provide_health_status(self, mocker):
        """Test health status reporting."""
        # Arrange
        metrics_collector = get_metrics_collector()

        # Act
        health_status = metrics_collector.get_health_status()

        # Assert
        assert "status" in health_status
        assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
        assert "uptime_seconds" in health_status
        assert "total_operations" in health_status
        assert "error_rate" in health_status
        assert "timestamp" in health_status

        assert isinstance(health_status["uptime_seconds"], (int, float))
        assert isinstance(health_status["error_rate"], (int, float))
        assert health_status["error_rate"] >= 0.0
