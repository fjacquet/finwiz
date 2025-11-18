"""
Unit tests for tool restriction validation.

Tests ensure that the reporter crew has no external tools and that
runtime validation prevents architectural violations.
"""

import pytest
from crewai import Agent

from finwiz.validation.tool_restrictions import (
    ReporterInputValidator,
    ToolRestrictionError,
    ToolRestrictionValidator,
)


class TestToolRestrictionValidator:
    """Test tool restriction validation for crew agents."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ToolRestrictionValidator()

    def test_should_pass_validation_when_reporter_has_no_tools(self, mocker):
        """Test that validation passes when investment reporter has no tools."""
        # Arrange
        mock_agent = mocker.Mock(spec=Agent)
        mock_agent.role = "Family Financial Plan Specialist"
        mock_agent.tools = []

        # Act & Assert - Should not raise exception
        self.validator.validate_agent_tools(mock_agent)

    def test_should_raise_error_when_reporter_has_tools(self, mocker):
        """Test that validation fails when investment reporter has tools."""
        # Arrange
        mock_agent = mocker.Mock(spec=Agent)
        mock_agent.role = "Family Financial Plan Specialist"
        mock_agent.tools = [mocker.MagicMock(), mocker.MagicMock()]  # Two mock tools

        # Act & Assert
        with pytest.raises(ToolRestrictionError) as exc_info:
            self.validator.validate_agent_tools(mock_agent)

        assert "Agent has 2 non-read-only tools but should have none" in str(exc_info.value)
        assert exc_info.value.agent_role == "Family Financial Plan Specialist"

    def test_should_allow_tools_for_non_restricted_agents(self, mocker):
        """Test that non-restricted agents can have tools."""
        # Arrange
        mock_agent = mocker.Mock(spec=Agent)
        mock_agent.role = "Portfolio Allocator"
        mock_agent.tools = [mocker.MagicMock(), mocker.MagicMock(), mocker.MagicMock()]  # Three mock tools

        # Act & Assert - Should not raise exception
        self.validator.validate_agent_tools(mock_agent)

    def test_should_validate_multiple_agents_in_crew(self, mocker):
        """Test validation of multiple agents in a crew."""
        # Arrange
        reporter_agent = mocker.Mock(spec=Agent)
        reporter_agent.role = "investment_reporter"
        reporter_agent.tools = []

        allocator_agent = mocker.Mock(spec=Agent)
        allocator_agent.role = "Portfolio Allocator"
        allocator_agent.tools = [mocker.MagicMock()]

        agents = [reporter_agent, allocator_agent]

        # Act & Assert - Should not raise exception
        self.validator.validate_crew_compliance(agents)

    def test_should_fail_crew_validation_when_reporter_has_tools(self, mocker):
        """Test that crew validation fails when reporter has tools."""
        # Arrange
        reporter_agent = mocker.Mock(spec=Agent)
        reporter_agent.role = "investment_reporter"
        reporter_agent.tools = [mocker.MagicMock()]  # Should not have tools

        allocator_agent = mocker.Mock(spec=Agent)
        allocator_agent.role = "Portfolio Allocator"
        allocator_agent.tools = [mocker.MagicMock()]

        agents = [reporter_agent, allocator_agent]

        # Act & Assert
        with pytest.raises(ToolRestrictionError):
            self.validator.validate_crew_compliance(agents)

    def test_should_log_monitoring_for_restricted_agents(self, mocker):
        """Test that task execution monitoring logs for restricted agents."""
        # Arrange
        mock_task = mocker.MagicMock()
        mock_agent = mocker.Mock(spec=Agent)
        mock_agent.role = "investment_reporter"
        mock_logger = mocker.patch.object(self.validator, "logger")

        # Act
        self.validator.monitor_task_execution(mock_task, mock_agent)

        # Assert
        mock_logger.info.assert_called()
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Monitoring restricted agent execution" in arg for arg in call_args)

    def test_should_handle_agent_without_role_attribute(self, mocker):
        """Test handling of agents without role attribute."""
        # Arrange
        mock_agent = mocker.Mock(spec=Agent)
        # Don't set role attribute
        if hasattr(mock_agent, "role"):
            delattr(mock_agent, "role")
        mock_agent.tools = []

        # Act & Assert - Should not raise exception
        self.validator.validate_agent_tools(mock_agent)


class TestReporterInputValidator:
    """Test reporter input validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ReporterInputValidator()

    def test_should_pass_validation_with_complete_context(self):
        """Test validation passes with all required context keys."""
        # Arrange
        context = {
            "ten_k_insights": [],
            "market_sentiment": {},
            "risk_score_standardized": {},
            "portfolio_allocation": {},
            "risk_assessment": {},
        }

        # Act & Assert - Should not raise exception
        self.validator.validate_reporter_context(context)

    def test_should_log_warning_for_missing_context_keys(self, mocker):
        """Test that missing context keys are logged as warnings."""
        # Arrange
        context = {
            "ten_k_insights": [],
            "market_sentiment": {},
            # Missing other required keys
        }
        mock_logger = mocker.patch.object(self.validator, "logger")

        # Act
        self.validator.validate_reporter_context(context)

        # Assert
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Reporter context missing keys" in call_args

    def test_should_log_info_for_additional_context_keys(self, mocker):
        """Test that additional context keys are logged as info."""
        # Arrange
        context = {
            "ten_k_insights": [],
            "market_sentiment": {},
            "risk_score_standardized": {},
            "portfolio_allocation": {},
            "risk_assessment": {},
            "extra_key": "extra_value",  # Additional key
        }
        mock_logger = mocker.patch.object(self.validator, "logger")

        # Act
        self.validator.validate_reporter_context(context)

        # Assert
        mock_logger.info.assert_called()
        call_args = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("Reporter context has additional keys" in arg for arg in call_args)

    def test_should_handle_empty_context(self):
        """Test handling of empty context dictionary."""
        # Arrange
        context = {}

        # Act & Assert - Should not raise exception, just log warnings
        self.validator.validate_reporter_context(context)


class TestToolRestrictionError:
    """Test the ToolRestrictionError exception."""

    def test_should_create_error_with_agent_and_violation(self):
        """Test error creation with agent role and violation message."""
        # Arrange
        agent_role = "investment_reporter"
        violation = "Agent has tools but should have none"

        # Act
        error = ToolRestrictionError(agent_role, violation)

        # Assert
        assert error.agent_role == agent_role
        assert error.violation == violation
        assert agent_role in str(error)
        assert violation in str(error)
