"""
Robust Tool Wrapper - Makes tools resilient to malformed LLM inputs.

This wrapper intercepts tool calls and fixes common issues before execution.
"""

import json
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class RobustToolWrapper:
    """Wraps tools to handle malformed inputs gracefully."""

    @staticmethod
    def parse_input(raw_input: Any, args_schema: type[BaseModel]) -> dict[str, Any]:
        """
        Parse and fix malformed tool input.

        Args:
            raw_input: Raw input from LLM
            args_schema: Expected Pydantic schema

        Returns:
            Cleaned dictionary matching schema

        """
        # Case 1: JSON string - parse it first
        if isinstance(raw_input, str):
            try:
                parsed = json.loads(raw_input)
                raw_input = parsed
                logger.info(f"Parsed JSON string, got type: {type(raw_input)}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON string: {raw_input[:200]}")
                return {}

        # Case 2: JSON array - take first non-empty dict
        if isinstance(raw_input, list):
            logger.warning(f"Tool received array with {len(raw_input)} items, extracting first valid item")
            logger.debug(f"Repaired JSON: {json.dumps(raw_input, indent=2, default=str)[:500]}")

            for item in raw_input:
                # Recursively parse each item
                if isinstance(item, str):
                    try:
                        item = json.loads(item)
                    except json.JSONDecodeError:
                        continue

                if isinstance(item, dict) and item:
                    # Check if it looks like actual tool parameters
                    # Skip items that look like error responses (have 'status', 'error', 'message' keys)
                    error_indicators = {"status", "error", "message", "items"}
                    if error_indicators.intersection(item.keys()) and len(item) <= 3:
                        logger.debug(f"Skipping error/status dict: {list(item.keys())}")
                        continue

                    # Skip items that look like validation results (have 'valid', 'reason', 'meta' keys)
                    validation_indicators = {"valid", "reason", "meta"}
                    if validation_indicators.issubset(item.keys()):
                        logger.debug(f"Skipping validation result dict: {list(item.keys())}")
                        continue

                    # Check if it has actual parameter values (not just nested dicts/lists)
                    if any(not isinstance(v, (dict, list)) for v in item.values()):
                        logger.info(f"Using first valid item from array: {list(item.keys())}")
                        return item

            # If no valid items found, return empty
            logger.warning("No valid items found in array")
            return {}

        # Case 3: Already a dict - return it
        if isinstance(raw_input, dict):
            return raw_input

        # Case 4: Unknown type
        logger.error(f"Unexpected input type: {type(raw_input)}")
        return {}

    @staticmethod
    def wrap_tool(tool: BaseTool) -> BaseTool:
        """
        Wrap a tool to handle malformed inputs.

        Args:
            tool: Original BaseTool instance

        Returns:
            Wrapped tool with robust input handling

        """
        original_run = tool._run

        def robust_run(*args: Any, **kwargs: Any) -> Any:
            """Wrapped _run method with input fixing."""
            try:
                # If single positional arg (string or otherwise)
                if len(args) == 1 and not kwargs:
                    arg = args[0]

                    # Always try to parse it
                    fixed_input = RobustToolWrapper.parse_input(arg, tool.args_schema)
                    if fixed_input:
                        logger.info(f"Fixed {tool.name} input: {list(fixed_input.keys())}")
                        return original_run(**fixed_input)

                # Normal execution
                return original_run(*args, **kwargs)

            except Exception as e:
                logger.error(f"Tool {tool.name} failed: {str(e)}")
                return f"Error: {tool.name} failed - {str(e)}"

        tool._run = robust_run  # type: ignore[method-assign]
        return tool


def make_tools_robust(tools: list[BaseTool]) -> list[BaseTool]:
    """
    Wrap all tools in a list to make them robust.

    Args:
        tools: List of BaseTool instances

    Returns:
        List of wrapped tools

    """
    return [RobustToolWrapper.wrap_tool(tool) for tool in tools]
