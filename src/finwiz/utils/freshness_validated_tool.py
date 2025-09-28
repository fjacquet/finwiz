"""
Freshness Validated Tool Wrapper.

This module provides a wrapper that adds data freshness validation to any
existing CrewAI tool, ensuring data meets freshness requirements.
"""

import logging
from typing import Any

from crewai.tools import BaseTool

from .data_freshness_validator import DataFreshnessValidator

logger = logging.getLogger(__name__)


class RefreshResult:
    """Result of data refresh attempt."""

    def __init__(self, success: bool, data: Any = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error


class FreshnessValidatedTool(BaseTool):
    """
    Wrapper that adds freshness validation to any CrewAI tool.

    This wrapper ensures that data returned by tools meets freshness requirements,
    with graceful degradation when data is stale.
    """

    def __init__(self, base_tool: BaseTool, validator: DataFreshnessValidator | None = None, max_age_hours: int = 24):
        """
        Initialize the freshness validated tool wrapper.

        Args:
            base_tool: The original tool to wrap
            validator: Optional validator instance (creates default if None)
            max_age_hours: Maximum acceptable age for data in hours

        """
        # Initialize with base tool properties first
        super().__init__(
            name=f"FreshData_{base_tool.name}",
            description=f"{base_tool.description} (with freshness validation)",
            args_schema=base_tool.args_schema,
        )

        # Store as private attributes to avoid Pydantic validation issues
        self._base_tool = base_tool
        self._validator = validator or DataFreshnessValidator(max_age_hours=max_age_hours)

    @property
    def base_tool(self) -> BaseTool:
        """Get the wrapped base tool."""
        return self._base_tool

    @property
    def validator(self) -> DataFreshnessValidator:
        """Get the freshness validator."""
        return self._validator

    def _run(self, *args, **kwargs) -> Any:
        """Execute tool with freshness validation."""
        try:
            # Get data from base tool
            logger.debug(f"Executing base tool: {self._base_tool.name}")
            result = self._base_tool._run(*args, **kwargs)

            # Skip validation for error results
            if isinstance(result, dict) and "error" in result:
                logger.debug(f"Skipping freshness validation due to tool error: {result.get('error')}")
                return result

            # Validate freshness
            freshness_result = self._validator.validate_data_freshness(result, self._base_tool.name)

            if not freshness_result.is_fresh:
                logger.warning(f"Stale data detected from {self._base_tool.name}: {freshness_result.warning}")

                # Attempt refresh if possible
                refresh_result = self._attempt_refresh(*args, **kwargs)

                if refresh_result.success:
                    logger.info(f"Successfully refreshed data from {self._base_tool.name}")
                    result = refresh_result.data

                    # Re-validate refreshed data
                    freshness_result = self._validator.validate_data_freshness(result, self._base_tool.name)
                else:
                    logger.warning(f"Data refresh failed for {self._base_tool.name}: {refresh_result.error}")
                    # Continue with stale data (graceful degradation)

            # Add freshness metadata to result
            if isinstance(result, dict):
                result = self._validator.add_freshness_metadata(result, freshness_result)

            return result

        except Exception as e:
            logger.error(f"Freshness validated tool execution failed: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}

    def _attempt_refresh(self, *args, **kwargs) -> RefreshResult:
        """
        Attempt to refresh stale data.

        This method tries to refresh data by calling the base tool again.
        In the future, this could be enhanced with specific refresh methods.
        """
        try:
            # For now, just try calling the base tool again
            # This assumes the tool might get fresher data on retry
            logger.info(f"Attempting to refresh data from {self._base_tool.name}")
            fresh_data = self._base_tool._run(*args, **kwargs)

            # Check if refresh was successful (no error)
            if isinstance(fresh_data, dict) and "error" in fresh_data:
                return RefreshResult(success=False, error=f"Refresh failed: {fresh_data.get('error')}")

            # Validate the refreshed data
            freshness_result = self._validator.validate_data_freshness(fresh_data, self._base_tool.name)

            return RefreshResult(
                success=freshness_result.is_fresh,
                data=fresh_data if freshness_result.is_fresh else None,
                error=None if freshness_result.is_fresh else freshness_result.warning,
            )

        except Exception as e:
            logger.error(f"Data refresh failed for {self._base_tool.name}: {e}")
            return RefreshResult(success=False, error=str(e))


def add_freshness_validation(tool: BaseTool, max_age_hours: int = 24) -> FreshnessValidatedTool:
    """
    Add freshness validation to a tool.

    Args:
        tool: The tool to wrap with freshness validation
        max_age_hours: Maximum acceptable age for data in hours

    Returns:
        FreshnessValidatedTool wrapper

    """
    return FreshnessValidatedTool(tool, max_age_hours=max_age_hours)
