"""
Agent definitions for the Report Crew.

This module defines all agents used in the Report Crew with their configurations.
"""

import logging
from typing import Any

from crewai import Agent
from crewai.project import agent

from finwiz.infrastructure.decorators.agent_validators import final_reporter

logger = logging.getLogger(__name__)


class ReportCrewAgents:
    """Defines all agents for the Report Crew."""

    def __init__(self, agents_config: dict[str, Any], tools: list[Any]) -> None:
        """Initialize agents with configuration and tools."""
        self.agents_config = agents_config
        self.tools = tools

    @agent
    def financial_integration_analyst(self) -> Agent:
        """Agent that integrates Stock/ETF/Crypto analyses into unified narrative."""
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            reasoning=True,  # Enable AI reasoning for complex financial integration decisions
            tools=self.tools,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """Agent that proposes optimal cross-asset portfolio allocations."""
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=self.tools,
            reasoning=True,  # Enable AI reasoning for optimal portfolio allocation decisions
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that identifies and mitigates portfolio and market risks."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=self.tools,
            reasoning=True,  # Enable AI reasoning for risk assessment and mitigation decisions
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Define the final reporter with no tools; format the consolidated HTML report."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            verbose=True,
            tools=[],
        )

    def get_all_agents(self) -> list[Agent]:
        """Get all agents as a list."""
        return [
            self.financial_integration_analyst(),
            self.portfolio_allocator(),
            self.risk_manager(),
            self.investment_reporter(),
        ]
