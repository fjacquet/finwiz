"""
Unit tests for base tool classes.

Tests the AsyncFeedbackTool base class with mock implementations.
"""

import asyncio
from typing import Any

import pytest

from finwiz.tools.base_tools import AsyncFeedbackTool


class MockAsyncTool(AsyncFeedbackTool):
    """Mock async tool for testing."""

    name: str = "mock_async_tool"
    description: str = "Mock tool for testing async behavior"

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """Mock async implementation."""
        # Simulate async operation
        await asyncio.sleep(0.01)

        # Return test data
        return {
            "success": True,
            "message": "Mock operation completed",
            "input_data": kwargs,
        }


class MockFailingAsyncTool(AsyncFeedbackTool):
    """Mock async tool that raises an error."""

    name: str = "mock_failing_tool"
    description: str = "Mock tool that fails"

    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """Mock async implementation that raises an error."""
        raise ValueError("Mock error for testing")


class TestAsyncFeedbackTool:
    """Test suite for AsyncFeedbackTool base class."""

    def test_should_run_async_tool_synchronously(self):
        """Test that async tool can be run synchronously."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = tool._run(test_param="test_value")

        # Assert
        assert result["success"] is True
        assert result["message"] == "Mock operation completed"
        assert result["input_data"]["test_param"] == "test_value"

    def test_should_pass_kwargs_to_arun(self):
        """Test that kwargs are passed correctly to _arun."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = tool._run(param1="value1", param2="value2", param3=123)

        # Assert
        assert result["input_data"]["param1"] == "value1"
        assert result["input_data"]["param2"] == "value2"
        assert result["input_data"]["param3"] == 123

    def test_should_handle_no_event_loop(self):
        """Test behavior when no event loop is running."""
        # Arrange
        tool = MockAsyncTool()

        # Act - Should work without existing event loop
        result = tool._run(test="no_loop")

        # Assert
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_should_handle_existing_event_loop(self):
        """Test behavior when event loop is already running."""
        # Arrange
        tool = MockAsyncTool()

        # Act - Run in async context (event loop already running)
        result = tool._run(test="with_loop")

        # Assert
        assert result["success"] is True
        assert result["input_data"]["test"] == "with_loop"

    def test_should_propagate_errors_from_arun(self):
        """Test that errors from _arun are propagated."""
        # Arrange
        tool = MockFailingAsyncTool()

        # Act & Assert
        with pytest.raises(ValueError, match="Mock error for testing"):
            tool._run()

    @pytest.mark.asyncio
    async def test_should_call_arun_directly(self):
        """Test that _arun can be called directly in async context."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = await tool._arun(direct_call=True)

        # Assert
        assert result["success"] is True
        assert result["input_data"]["direct_call"] is True

    def test_should_require_arun_implementation(self):
        """Test that subclasses must implement _arun."""

        # Arrange - Create tool without implementing _arun
        class IncompleteAsyncTool(AsyncFeedbackTool):
            name: str = "incomplete_tool"
            description: str = "Tool without _arun implementation"

        # Act & Assert - Python prevents instantiation of abstract classes
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            tool = IncompleteAsyncTool()

    def test_should_handle_empty_kwargs(self):
        """Test tool with no arguments."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = tool._run()

        # Assert
        assert result["success"] is True
        assert result["input_data"] == {}

    def test_should_handle_complex_kwargs(self):
        """Test tool with complex argument types."""
        # Arrange
        tool = MockAsyncTool()
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2),
        }

        # Act
        result = tool._run(**complex_data)

        # Assert
        assert result["success"] is True
        assert result["input_data"]["list"] == [1, 2, 3]
        assert result["input_data"]["dict"]["nested"] == "value"
        assert result["input_data"]["tuple"] == (1, 2)


class TestAsyncFeedbackToolIntegration:
    """Integration tests for AsyncFeedbackTool in different contexts."""

    def test_should_work_in_sync_context(self):
        """Test tool works in synchronous context."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = tool._run(context="sync")

        # Assert
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_should_work_in_async_context(self):
        """Test tool works in async context."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result = tool._run(context="async")

        # Assert
        assert result["success"] is True

    def test_should_work_with_multiple_sequential_calls(self):
        """Test multiple sequential calls to the same tool."""
        # Arrange
        tool = MockAsyncTool()

        # Act
        result1 = tool._run(call=1)
        result2 = tool._run(call=2)
        result3 = tool._run(call=3)

        # Assert
        assert result1["input_data"]["call"] == 1
        assert result2["input_data"]["call"] == 2
        assert result3["input_data"]["call"] == 3

    def test_should_work_with_different_tool_instances(self):
        """Test multiple tool instances work independently."""
        # Arrange
        tool1 = MockAsyncTool()
        tool2 = MockAsyncTool()

        # Act
        result1 = tool1._run(instance=1)
        result2 = tool2._run(instance=2)

        # Assert
        assert result1["input_data"]["instance"] == 1
        assert result2["input_data"]["instance"] == 2
