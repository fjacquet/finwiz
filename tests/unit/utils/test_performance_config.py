"""Unit tests for performance configuration module."""

import os

import pytest

from finwiz.config.performance.performance_config import (
    OptimizationMode,
    PerformanceConfigManager,
    get_batch_size,
    is_balanced_mode,
    is_baseline_mode,
    is_maximum_speed_mode,
    should_use_ai_summary,
    should_use_mini_model,
    should_use_minimal_tools,
)


class TestPerformanceConfig:
    """Test suite for performance configuration."""

    def test_should_load_default_configuration(self, mocker):
        """Test loading default configuration values."""
        mocker.patch.dict(os.environ, {}, clear=True)
        config_manager = PerformanceConfigManager()
        config = config_manager.get_config()

        # Default values
        assert config.risk_assessment_use_mini is True
        assert config.use_minimal_risk_tools is True
        assert config.deep_analysis_ai_summary is False
        assert config.deep_analysis_batch_size == 5
        assert config.mode == OptimizationMode.MAXIMUM_SPEED

    def test_should_load_environment_configuration(self, mocker):
        """Test loading configuration from environment variables."""
        env_vars = {
            "RISK_ASSESSMENT_USE_MINI": "false",
            "USE_MINIMAL_RISK_TOOLS": "false",
            "DEEP_ANALYSIS_AI_SUMMARY": "true",
            "DEEP_ANALYSIS_BATCH_SIZE": "10",
        }

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        config = config_manager.get_config()

        assert config.risk_assessment_use_mini is False
        assert config.use_minimal_risk_tools is False
        assert config.deep_analysis_ai_summary is True
        assert config.deep_analysis_batch_size == 10
        assert config.mode == OptimizationMode.BASELINE

    def test_should_determine_maximum_speed_mode(self, mocker):
        """Test maximum speed mode determination."""
        env_vars = {"RISK_ASSESSMENT_USE_MINI": "true", "USE_MINIMAL_RISK_TOOLS": "true", "DEEP_ANALYSIS_AI_SUMMARY": "false"}

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        assert config_manager.get_mode() == OptimizationMode.MAXIMUM_SPEED
        assert config_manager.is_maximum_speed_mode() is True
        assert config_manager.is_balanced_mode() is False
        assert config_manager.is_baseline_mode() is False

    def test_should_determine_balanced_mode(self, mocker):
        """Test balanced mode determination."""
        env_vars = {"RISK_ASSESSMENT_USE_MINI": "true", "USE_MINIMAL_RISK_TOOLS": "true", "DEEP_ANALYSIS_AI_SUMMARY": "true"}

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        assert config_manager.get_mode() == OptimizationMode.BALANCED
        assert config_manager.is_maximum_speed_mode() is False
        assert config_manager.is_balanced_mode() is True
        assert config_manager.is_baseline_mode() is False

    def test_should_determine_baseline_mode(self, mocker):
        """Test baseline mode determination."""
        env_vars = {"RISK_ASSESSMENT_USE_MINI": "false", "USE_MINIMAL_RISK_TOOLS": "false", "DEEP_ANALYSIS_AI_SUMMARY": "false"}

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        assert config_manager.get_mode() == OptimizationMode.BASELINE
        assert config_manager.is_maximum_speed_mode() is False
        assert config_manager.is_balanced_mode() is False
        assert config_manager.is_baseline_mode() is True

    def test_should_validate_batch_size_limits(self, mocker):
        """Test batch size validation."""
        # Test invalid batch size (too small)
        mocker.patch.dict(os.environ, {"DEEP_ANALYSIS_BATCH_SIZE": "0"}, clear=True)
        with pytest.raises(ValueError, match="Deep analysis batch size must be at least 1"):
            PerformanceConfigManager()

        # Test valid batch size
        mocker.patch.dict(os.environ, {"DEEP_ANALYSIS_BATCH_SIZE": "5"}, clear=True)
        config_manager = PerformanceConfigManager()
        assert config_manager.get_batch_size() == 5

    def test_should_handle_invalid_batch_size_string(self, mocker):
        """Test handling of invalid batch size string."""
        mocker.patch.dict(os.environ, {"DEEP_ANALYSIS_BATCH_SIZE": "invalid"}, clear=True)
        config_manager = PerformanceConfigManager()
        # Should use default value of 5
        assert config_manager.get_batch_size() == 5

    def test_global_functions(self, mocker):
        """Test global convenience functions."""
        env_vars = {
            "RISK_ASSESSMENT_USE_MINI": "true",
            "USE_MINIMAL_RISK_TOOLS": "true",
            "DEEP_ANALYSIS_AI_SUMMARY": "false",
            "DEEP_ANALYSIS_BATCH_SIZE": "7",
        }

        mocker.patch.dict(os.environ, env_vars, clear=True)
        # Clear global instance to force reload
        import finwiz.config.performance.performance_config

        finwiz.config.performance.performance_config._performance_config_manager = None

        assert is_maximum_speed_mode() is True
        assert is_balanced_mode() is False
        assert is_baseline_mode() is False
        assert should_use_ai_summary() is False
        assert should_use_mini_model() is True
        assert should_use_minimal_tools() is True
        assert get_batch_size() == 7

    def test_configuration_summary(self, mocker):
        """Test configuration summary generation."""
        env_vars = {
            "RISK_ASSESSMENT_USE_MINI": "true",
            "USE_MINIMAL_RISK_TOOLS": "true",
            "DEEP_ANALYSIS_AI_SUMMARY": "true",
            "DEEP_ANALYSIS_BATCH_SIZE": "8",
        }

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        summary = config_manager.get_configuration_summary()

        assert summary["mode"] == "balanced"
        assert summary["risk_assessment_use_mini"] is True
        assert summary["use_minimal_risk_tools"] is True
        assert summary["deep_analysis_ai_summary"] is True
        assert summary["deep_analysis_batch_size"] == 8
        assert "expected_performance" in summary

    def test_expected_performance_characteristics(self, mocker):
        """Test expected performance characteristics for each mode."""
        # Maximum Speed mode
        env_vars = {"RISK_ASSESSMENT_USE_MINI": "true", "USE_MINIMAL_RISK_TOOLS": "true", "DEEP_ANALYSIS_AI_SUMMARY": "false"}

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        expected = config_manager._get_expected_performance()

        assert expected["time_per_ticker"] == "10-30 seconds"
        assert expected["speedup_factor"] == "10-20x"
        assert expected["cost_savings"] == "100%"

        # Balanced mode
        env_vars["DEEP_ANALYSIS_AI_SUMMARY"] = "true"

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        expected = config_manager._get_expected_performance()

        assert expected["time_per_ticker"] == "15-40 seconds"
        assert expected["speedup_factor"] == "8-15x"
        assert expected["cost_savings"] == "80-90%"

        # Baseline mode
        env_vars.update({"RISK_ASSESSMENT_USE_MINI": "false", "USE_MINIMAL_RISK_TOOLS": "false"})

        mocker.patch.dict(os.environ, env_vars, clear=True)
        config_manager = PerformanceConfigManager()
        expected = config_manager._get_expected_performance()

        assert expected["time_per_ticker"] == "5-10 minutes"
        assert expected["speedup_factor"] == "1x (baseline)"
        assert expected["cost_savings"] == "0% (baseline)"
