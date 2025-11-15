"""
Unit tests for feedback integration tools.

Tests the refactored feedback tools that now inherit from AsyncFeedbackTool.
"""

import pytest

from finwiz.tools.feedback_integration_tool import (
    CriteriaOptimizationTool,
    FeedbackAnalysisTool,
    FeedbackCollectionTool,
    LearningMetricsTool,
    PerformanceTrackingTool,
)


class TestFeedbackCollectionTool:
    """Test suite for FeedbackCollectionTool."""

    def test_should_inherit_from_async_feedback_tool(self):
        """Test that tool inherits from AsyncFeedbackTool."""
        # Arrange & Act
        tool = FeedbackCollectionTool()

        # Assert
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        assert tool.name == "feedback_collection_tool"

    def test_should_have_correct_attributes(self):
        """Test tool has correct name and description."""
        # Arrange & Act
        tool = FeedbackCollectionTool()

        # Assert
        assert tool.name == "feedback_collection_tool"
        assert "feedback" in tool.description.lower()
        assert "recommendation" in tool.description.lower()


class TestPerformanceTrackingTool:
    """Test suite for PerformanceTrackingTool."""

    def test_should_inherit_from_async_feedback_tool(self):
        """Test that tool inherits from AsyncFeedbackTool."""
        # Arrange & Act
        tool = PerformanceTrackingTool()

        # Assert
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        assert tool.name == "performance_tracking_tool"

    def test_should_have_correct_attributes(self):
        """Test tool has correct name and description."""
        # Arrange & Act
        tool = PerformanceTrackingTool()

        # Assert
        assert tool.name == "performance_tracking_tool"
        assert "performance" in tool.description.lower()
        assert "recommendation" in tool.description.lower()


class TestCriteriaOptimizationTool:
    """Test suite for CriteriaOptimizationTool."""

    def test_should_inherit_from_async_feedback_tool(self):
        """Test that tool inherits from AsyncFeedbackTool."""
        # Arrange & Act
        tool = CriteriaOptimizationTool()

        # Assert
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        assert tool.name == "criteria_optimization_tool"

    def test_should_have_correct_attributes(self):
        """Test tool has correct name and description."""
        # Arrange & Act
        tool = CriteriaOptimizationTool()

        # Assert
        assert tool.name == "criteria_optimization_tool"
        assert "criteria" in tool.description.lower()
        assert "optimize" in tool.description.lower()


class TestFeedbackAnalysisTool:
    """Test suite for FeedbackAnalysisTool."""

    def test_should_inherit_from_async_feedback_tool(self):
        """Test that tool inherits from AsyncFeedbackTool."""
        # Arrange & Act
        tool = FeedbackAnalysisTool()

        # Assert
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        assert tool.name == "feedback_analysis_tool"

    def test_should_have_correct_attributes(self):
        """Test tool has correct name and description."""
        # Arrange & Act
        tool = FeedbackAnalysisTool()

        # Assert
        assert tool.name == "feedback_analysis_tool"
        assert "analyze" in tool.description.lower()
        assert "feedback" in tool.description.lower()


class TestLearningMetricsTool:
    """Test suite for LearningMetricsTool."""

    def test_should_inherit_from_async_feedback_tool(self):
        """Test that tool inherits from AsyncFeedbackTool."""
        # Arrange & Act
        tool = LearningMetricsTool()

        # Assert
        assert hasattr(tool, "_run")
        assert hasattr(tool, "_arun")
        assert tool.name == "learning_metrics_tool"

    def test_should_have_correct_attributes(self):
        """Test tool has correct name and description."""
        # Arrange & Act
        tool = LearningMetricsTool()

        # Assert
        assert tool.name == "learning_metrics_tool"
        assert "metrics" in tool.description.lower()
        assert "learning" in tool.description.lower()


class TestFeedbackToolsIntegration:
    """Integration tests for all feedback tools."""

    def test_should_instantiate_all_tools(self):
        """Test that all feedback tools can be instantiated."""
        # Arrange & Act
        tools = [
            FeedbackCollectionTool(),
            PerformanceTrackingTool(),
            CriteriaOptimizationTool(),
            FeedbackAnalysisTool(),
            LearningMetricsTool(),
        ]

        # Assert
        assert len(tools) == 5
        for tool in tools:
            assert hasattr(tool, "_run")
            assert hasattr(tool, "_arun")
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_should_have_unique_names(self):
        """Test that all tools have unique names."""
        # Arrange
        tools = [
            FeedbackCollectionTool(),
            PerformanceTrackingTool(),
            CriteriaOptimizationTool(),
            FeedbackAnalysisTool(),
            LearningMetricsTool(),
        ]

        # Act
        names = [tool.name for tool in tools]

        # Assert
        assert len(names) == len(set(names))  # All names are unique


class TestToolResultStandardization:
    """Test that feedback tools return standardized ToolResult format."""

    @pytest.mark.asyncio
    async def test_feedback_collection_returns_standard_format_on_error(self, mocker):
        """Test FeedbackCollectionTool returns standardized error format."""
        # Arrange
        tool = FeedbackCollectionTool()
        mocker.patch(
            "finwiz.tools.feedback_integration_tool.get_feedback_service",
            side_effect=Exception("Service unavailable"),
        )

        # Act
        result = await tool._arun(
            user_id="test_user",
            recommendation_id="rec_123",
            symbol="AAPL",
            asset_type="stock",
            outcome="accepted",
            sentiment="positive",
            confidence_rating=4,
        )

        # Assert - Verify standardized format
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None
        assert "Service unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_performance_tracking_returns_standard_format_on_error(self, mocker):
        """Test PerformanceTrackingTool returns standardized error format."""
        # Arrange
        tool = PerformanceTrackingTool()
        mocker.patch(
            "finwiz.tools.feedback_integration_tool.get_feedback_service",
            side_effect=Exception("Database error"),
        )

        # Act
        result = await tool._arun(
            recommendation_id="rec_123",
            symbol="AAPL",
            holding_period_days=90,
            absolute_return=0.15,
            benchmark_return=0.10,
            current_grade="A+",
            grade_maintained=True,
        )

        # Assert - Verify standardized format
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_criteria_optimization_returns_standard_format_on_error(self, mocker):
        """Test CriteriaOptimizationTool returns standardized error format."""
        # Arrange
        tool = CriteriaOptimizationTool()
        mocker.patch(
            "finwiz.tools.feedback_integration_tool.get_feedback_service",
            side_effect=Exception("Optimization failed"),
        )

        # Act
        result = await tool._arun(
            current_criteria={"min_score": 0.85},
            force_adjustment=False,
        )

        # Assert - Verify standardized format
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None
        assert "Optimization failed" in result["error"]

    @pytest.mark.asyncio
    async def test_feedback_analysis_returns_standard_format_on_error(self, mocker):
        """Test FeedbackAnalysisTool returns standardized error format."""
        # Arrange
        tool = FeedbackAnalysisTool()
        mocker.patch(
            "finwiz.tools.feedback_integration_tool.get_feedback_service",
            side_effect=Exception("Analysis error"),
        )

        # Act
        result = await tool._arun(days_back=90)

        # Assert - Verify standardized format
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None
        assert "Analysis error" in result["error"]

    @pytest.mark.asyncio
    async def test_learning_metrics_returns_standard_format_on_error(self, mocker):
        """Test LearningMetricsTool returns standardized error format."""
        # Arrange
        tool = LearningMetricsTool()
        mocker.patch(
            "finwiz.tools.feedback_integration_tool.get_feedback_service",
            side_effect=Exception("Metrics error"),
        )

        # Act
        result = await tool._arun(days_back=30)

        # Assert - Verify standardized format
        assert isinstance(result, dict)
        assert "success" in result
        assert "data" in result
        assert "error" in result
        assert result["success"] is False
        assert result["error"] is not None
        assert "Metrics error" in result["error"]
