"""
Unit tests for LLM configuration helpers.

Tests the externalized LLM configuration logic to ensure correct LLM
selection based on optimization mode and environment variables.
"""

from finwiz.crews.helpers.llm_config import get_crew_llm


class TestGetCrewLLM:
    """Test suite for get_crew_llm function."""

    def test_should_return_mini_model_when_mini_model_enabled(self, mocker):
        """Test that mini model is returned when optimization mode requires it."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.llm_config.get_performance_config_manager")
        mock_perf_config.return_value.should_use_mini_model.return_value = True
        mock_get_mini = mocker.patch("finwiz.crews.helpers.llm_config.get_mini_llm")
        mock_get_mini.return_value = mocker.Mock()

        # Act
        result = get_crew_llm()

        # Assert
        mock_get_mini.assert_called_once()
        assert result == mock_get_mini.return_value

    def test_should_return_standard_llm_when_mini_model_disabled(self, mocker):
        """Test that standard LLM is returned when mini model not required."""
        # Arrange
        mock_perf_config = mocker.patch("finwiz.crews.helpers.llm_config.get_performance_config_manager")
        mock_perf_config.return_value.should_use_mini_model.return_value = False
        mock_get_configured = mocker.patch("finwiz.crews.helpers.llm_config.get_configured_llm")
        mock_get_configured.return_value = mocker.Mock()

        # Act
        result = get_crew_llm()

        # Assert
        mock_get_configured.assert_called_once_with(model_type="standard")
        assert result == mock_get_configured.return_value
