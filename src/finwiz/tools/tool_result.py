"""
Tool Result standardization for consistent error handling across all tools.

This module provides a standardized ToolResult dataclass that all tools should use
for returning results, ensuring consistent response format and error handling.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """
    Standardized result format for all tools.

    Attributes:
        success: Whether the tool execution was successful
        data: Dictionary containing the tool's output data
        error: Error message if execution failed, None otherwise

    """

    success: bool
    data: dict[str, Any]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert ToolResult to dictionary format.

        Returns:
            Dictionary with success, data, and error fields

        """
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
        }

    @classmethod
    def success_result(cls, data: dict[str, Any]) -> "ToolResult":
        """
        Create a successful ToolResult.

        Args:
            data: Dictionary containing the tool's output data

        Returns:
            ToolResult with success=True and provided data

        """
        return cls(success=True, data=data, error=None)

    @classmethod
    def error_result(cls, error: str, data: dict[str, Any] | None = None) -> "ToolResult":
        """
        Create an error ToolResult.

        Args:
            error: Error message describing what went wrong
            data: Optional partial data that was collected before error

        Returns:
            ToolResult with success=False and error message

        """
        return cls(success=False, data=data or {}, error=error)
