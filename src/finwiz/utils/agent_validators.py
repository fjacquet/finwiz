"""
Agent validation decorators for FinWiz.

This module provides decorators to enforce architectural constraints on agents,
specifically ensuring that final reporter agents do not receive tools, maintaining
proper separation of concerns.

Usage:
    from finwiz.utils.agent_validators import final_reporter

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        return Agent(config=..., tools=[])
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from crewai import Agent

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class FinalReporterError(Exception):
    """
    Raised when final reporter has tools.

    This exception is raised by the @final_reporter decorator when
    an agent designated as a final reporter is created with tools,
    violating the architectural constraint that final reporters
    should only consume upstream context.
    """

    pass


def final_reporter(func: Callable) -> Callable:
    """
    Enforce that final reporter has no tools.

    This decorator validates that agents designated as final reporters
    do not have any tools assigned to them. Final reporters should only
    consume upstream context and format output, not perform additional
    research or data gathering.

    Args:
        func: Agent creation function to wrap

    Returns:
        Wrapped function that validates agent has no tools

    Raises:
        FinalReporterError: If agent has any tools

    Example:
        @final_reporter
        @agent
        def investment_reporter(self) -> Agent:
            return Agent(
                config=self.agents_config['investment_reporter'],
                tools=[],  # Must be empty
                verbose=True
            )

    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Agent:
        # Call the original function to create the agent
        agent = func(*args, **kwargs)

        # Validate that the agent has no tools
        if agent.tools and len(agent.tools) > 0:
            tool_count = len(agent.tools)
            agent_role = getattr(agent, "role", "Unknown")
            error_msg = (
                f"Final reporter '{agent_role}' must have NO tools. Found {tool_count} tool{'s' if tool_count > 1 else ''}. Final reporters should only consume upstream context."
            )
            logger.error(
                f"Final reporter validation failed for '{agent_role}'",
                extra={"agent_role": agent_role, "tool_count": tool_count},
            )
            raise FinalReporterError(error_msg)

        # Log successful validation
        agent_role = getattr(agent, "role", "Unknown")
        logger.info(
            f"Final reporter validation passed for '{agent_role}'",
            extra={"agent_role": agent_role, "tool_count": 0},
        )

        return agent

    return wrapper
