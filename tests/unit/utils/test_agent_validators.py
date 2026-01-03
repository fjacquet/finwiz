"""
Unit tests for agent validation decorators.

Tests the @final_reporter decorator to ensure it correctly validates
that final reporter agents have no tools.
"""

import pytest
from crewai import Agent

from finwiz.infrastructure.decorators.agent_validators import FinalReporterError, final_reporter


class TestFinalReporterDecorator:
    """Test suite for @final_reporter decorator."""

    def test_should_allow_agent_when_no_tools(self, mocker):
        """Test decorator allows agents with no tools."""
        # Arrange
        mock_logger = mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        @final_reporter
        def create_reporter():
            return Agent(
                role="Investment Reporter",
                goal="Create comprehensive reports",
                backstory="Expert financial reporter",
                tools=[],  # No tools
                verbose=False,
            )

        # Act
        agent = create_reporter()

        # Assert
        assert agent is not None
        assert agent.role == "Investment Reporter"
        assert len(agent.tools) == 0
        mock_logger.info.assert_called_once()
        assert "validation passed" in mock_logger.info.call_args[0][0].lower()

    def test_should_reject_agent_when_tools_present(self, mocker):
        """Test decorator rejects agents with tools (raises FinalReporterError)."""
        # Arrange
        mock_logger = mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        # Create a mock BaseTool that will pass Pydantic validation
        from crewai.tools import BaseTool

        mock_tool = mocker.Mock(spec=BaseTool)
        mock_tool.name = "MockTool"
        mock_tool.description = "A mock tool"

        @final_reporter
        def create_reporter_with_tools():
            # Create agent with mock tools attribute
            agent = Agent(
                role="Investment Reporter",
                goal="Create comprehensive reports",
                backstory="Expert financial reporter",
                tools=[],  # Start with empty tools
                verbose=False,
            )
            # Manually set tools to bypass Pydantic validation
            agent.tools = [mock_tool, mock_tool, mock_tool]
            return agent

        # Act & Assert
        with pytest.raises(FinalReporterError) as exc_info:
            create_reporter_with_tools()

        # Verify error message content
        error_message = str(exc_info.value)
        assert "Investment Reporter" in error_message
        assert "3 tools" in error_message
        assert "must have NO tools" in error_message
        assert "upstream context" in error_message

        # Verify error logging
        mock_logger.error.assert_called_once()
        assert "validation failed" in mock_logger.error.call_args[0][0].lower()

    def test_should_include_agent_role_in_error_message(self, mocker):
        """Test error message includes agent role and tool count."""
        # Arrange
        mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        from crewai.tools import BaseTool

        mock_tool = mocker.Mock(spec=BaseTool)
        mock_tool.name = "MockTool"

        @final_reporter
        def create_custom_reporter():
            agent = Agent(
                role="Custom Financial Reporter",
                goal="Generate reports",
                backstory="Specialized reporter",
                tools=[],
                verbose=False,
            )
            # Manually set tools to bypass Pydantic validation
            agent.tools = [mock_tool]
            return agent

        # Act & Assert
        with pytest.raises(FinalReporterError) as exc_info:
            create_custom_reporter()

        error_message = str(exc_info.value)
        assert "Custom Financial Reporter" in error_message
        assert "1 tool" in error_message  # Singular form

    def test_should_preserve_function_metadata(self):
        """Test decorator preserves function metadata."""

        # Arrange
        @final_reporter
        def investment_reporter():
            """Create investment reporter agent."""
            return Agent(
                role="Reporter",
                goal="Report",
                backstory="Reporter",
                tools=[],
                verbose=False,
            )

        # Assert
        assert investment_reporter.__name__ == "investment_reporter"
        assert "Create investment reporter agent" in investment_reporter.__doc__

    def test_should_log_validation_success_with_agent_role(self, mocker):
        """Test decorator logs successful validation with agent role."""
        # Arrange
        mock_logger = mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        @final_reporter
        def create_translator():
            return Agent(
                role="Translator",
                goal="Translate reports",
                backstory="Expert translator",
                tools=[],
                verbose=False,
            )

        # Act
        agent = create_translator()

        # Assert
        assert agent is not None
        mock_logger.info.assert_called_once()

        # Verify log message and extra fields
        log_call = mock_logger.info.call_args
        assert "Translator" in log_call[0][0]
        assert "validation passed" in log_call[0][0].lower()
        assert log_call[1]["extra"]["agent_role"] == "Translator"
        assert log_call[1]["extra"]["tool_count"] == 0

    def test_should_log_validation_failure_with_details(self, mocker):
        """Test decorator logs validation failure with agent role and tool count."""
        # Arrange
        mock_logger = mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        from crewai.tools import BaseTool

        mock_tool = mocker.Mock(spec=BaseTool)
        mock_tool.name = "MockTool"

        @final_reporter
        def create_invalid_reporter():
            agent = Agent(
                role="Invalid Reporter",
                goal="Report",
                backstory="Reporter",
                tools=[],
                verbose=False,
            )
            # Manually set tools to bypass Pydantic validation
            agent.tools = [mock_tool, mock_tool]
            return agent

        # Act & Assert
        with pytest.raises(FinalReporterError):
            create_invalid_reporter()

        # Verify error logging with extra fields
        mock_logger.error.assert_called_once()
        log_call = mock_logger.error.call_args
        assert "Invalid Reporter" in log_call[0][0]
        assert "validation failed" in log_call[0][0].lower()
        assert log_call[1]["extra"]["agent_role"] == "Invalid Reporter"
        assert log_call[1]["extra"]["tool_count"] == 2

    def test_should_handle_agent_without_role_attribute(self, mocker):
        """Test decorator handles agents without explicit role attribute gracefully."""
        # Arrange
        mock_logger = mocker.patch("finwiz.infrastructure.decorators.agent_validators.logger")

        from crewai.tools import BaseTool

        mock_tool = mocker.Mock(spec=BaseTool)
        mock_tool.name = "MockTool"

        @final_reporter
        def create_minimal_agent():
            # Create agent with minimal config
            agent = Agent(
                role="",  # Empty role
                goal="Test",
                backstory="Test",
                tools=[],
                verbose=False,
            )
            # Manually set tools to bypass Pydantic validation
            agent.tools = [mock_tool]
            return agent

        # Act & Assert
        with pytest.raises(FinalReporterError) as exc_info:
            create_minimal_agent()

        # Should still raise error even with empty role
        error_message = str(exc_info.value)
        assert "must have NO tools" in error_message
        assert "1 tool" in error_message
