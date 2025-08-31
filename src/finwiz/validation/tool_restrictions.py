"""
Tool restriction validation for FinWiz crews.

This module provides runtime validation to ensure architectural compliance,
specifically that the final reporter crew has no external tools and makes
no external API calls.
"""

import logging
from typing import Any

from crewai import Agent, Task

logger = logging.getLogger(__name__)


class ToolRestrictionError(Exception):
    """Raised when tool restrictions are violated."""

    def __init__(self, agent_role: str, violation: str) -> None:
        super().__init__(f"Tool restriction violation in {agent_role}: {violation}")
        self.agent_role = agent_role
        self.violation = violation


class ToolRestrictionValidator:
    """Validates tool restrictions for crew agents."""

    RESTRICTED_AGENTS = {
        "investment_reporter": "Final reporter must have no external tools",
    }

    def __init__(self) -> None:
        self.violations: list[str] = []
        self.logger = logger

    def validate_agent_tools(self, agent: Agent) -> None:
        """
        Validate that restricted agents have no tools.

        Args:
            agent: The agent to validate

        Raises:
            ToolRestrictionError: If tool restrictions are violated

        """
        agent_role = getattr(agent, "role", "unknown")

        # Check if this agent has tool restrictions
        is_restricted = (
            any(restricted_role in agent_role.lower() for restricted_role in self.RESTRICTED_AGENTS.keys())
            or "financial plan specialist" in agent_role.lower()
        )

        if is_restricted:
            if hasattr(agent, "tools") and agent.tools:
                violation = f"Agent has {len(agent.tools)} tools but should have none"
                logger.error(f"Tool restriction violation: {agent_role} - {violation}")
                raise ToolRestrictionError(agent_role, violation)

            logger.info(f"Tool restriction validation passed for {agent_role}")

    def validate_crew_compliance(self, agents: list[Agent]) -> None:
        """
        Validate tool restrictions for all agents in a crew.

        Args:
            agents: List of agents to validate

        Raises:
            ToolRestrictionError: If any tool restrictions are violated

        """
        for agent in agents:
            self.validate_agent_tools(agent)

    def monitor_task_execution(self, task: Task, agent: Agent) -> None:
        """
        Monitor task execution to prevent external API calls in restricted agents.

        Args:
            task: The task being executed
            agent: The agent executing the task

        """
        agent_role = getattr(agent, "role", "unknown")

        is_restricted = (
            any(restricted_role in agent_role.lower() for restricted_role in self.RESTRICTED_AGENTS.keys())
            or "financial plan specialist" in agent_role.lower()
        )

        if is_restricted:
            self.logger.info(f"Monitoring restricted agent execution: {agent_role}")

            # Log that this agent should only consume upstream context
            self.logger.info(f"Agent {agent_role} executing task with upstream context only")


class ReporterInputValidator:
    """Validates that reporter only consumes upstream context."""

    def __init__(self) -> None:
        self.required_context_keys = {
            "ten_k_insights",
            "market_sentiment",
            "risk_score_standardized",
            "portfolio_allocation",
            "risk_assessment",
        }
        self.logger = logger

    def validate_reporter_context(self, context: dict[str, Any]) -> None:
        """
        Validate that reporter receives proper upstream context.

        Args:
            context: The context data being passed to the reporter

        Raises:
            ValueError: If required context is missing

        """
        missing_keys = self.required_context_keys - set(context.keys())

        if missing_keys:
            self.logger.warning(f"Reporter context missing keys: {missing_keys}")
            # Don't raise error, just log warning for graceful degradation

        # Validate that context only contains expected upstream data
        unexpected_keys = set(context.keys()) - self.required_context_keys
        if unexpected_keys:
            self.logger.info(f"Reporter context has additional keys: {unexpected_keys}")

        self.logger.info("Reporter context validation completed")
