"""
Tool Input Fixer - Handles malformed tool inputs from LLM.

This module provides a wrapper that fixes common LLM tool calling issues,
particularly JSON arrays being passed instead of individual parameters.
"""

import json
from typing import Any, Callable

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ToolInputFixer:
    """
    Wrapper that fixes malformed tool inputs before passing to actual tool.
    
    Handles cases where LLM passes:
    - JSON arrays: [{"param": "value"}, {...}]
    - JSON strings: '{"param": "value"}'
    - Multiple items when tool expects one
    """
    
    @staticmethod
    def fix_input(tool_input: Any) -> dict[str, Any]:
        """
        Fix malformed tool input.
        
        Args:
            tool_input: Raw input from LLM (could be string, dict, list, etc.)
            
        Returns:
            Fixed dictionary with proper parameters
        """
        # If it's already a clean dict, return it
        if isinstance(tool_input, dict) and not any(isinstance(v, (list, dict)) for v in tool_input.values()):
            return tool_input
        
        # If it's a string, try to parse as JSON
        if isinstance(tool_input, str):
            try:
                parsed = json.loads(tool_input)
                tool_input = parsed
            except json.JSONDecodeError:
                logger.warning(f"Could not parse tool input as JSON: {tool_input[:100]}")
                return {}
        
        # If it's a list, take the first non-empty dict
        if isinstance(tool_input, list):
            logger.warning(f"Tool received array input with {len(tool_input)} items, using first item only")
            for item in tool_input:
                if isinstance(item, dict) and item:
                    return item
            return {}
        
        # If it's a dict but has nested structures, flatten it
        if isinstance(tool_input, dict):
            # Look for common wrapper patterns
            if len(tool_input) == 1:
                key = list(tool_input.keys())[0]
                value = tool_input[key]
                if isinstance(value, dict):
                    return value
        
        return tool_input if isinstance(tool_input, dict) else {}
    
    @staticmethod
    def wrap_tool(tool_func: Callable) -> Callable:
        """
        Wrap a tool function to fix inputs before execution.
        
        Args:
            tool_func: Original tool function
            
        Returns:
            Wrapped function that fixes inputs
        """
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            # If called with a single positional arg that looks like malformed input
            if len(args) == 1 and not kwargs:
                fixed_input = ToolInputFixer.fix_input(args[0])
                if fixed_input:
                    logger.info(f"Fixed tool input: {fixed_input}")
                    return tool_func(**fixed_input)
            
            # If kwargs look malformed
            if kwargs:
                fixed_input = ToolInputFixer.fix_input(kwargs)
                if fixed_input != kwargs:
                    logger.info(f"Fixed tool kwargs: {fixed_input}")
                    return tool_func(**fixed_input)
            
            # Otherwise call normally
            return tool_func(*args, **kwargs)
        
        return wrapped


def fix_tool_input(func: Callable) -> Callable:
    """
    Decorator to automatically fix tool inputs.
    
    Usage:
        @fix_tool_input
        def my_tool(ticker: str, form_type: str) -> str:
            return f"Analyzing {ticker}"
    """
    return ToolInputFixer.wrap_tool(func)
