"""
Expert team for Exchange-Traded Fund (ETF) research.

This module configures agents (Market Analyst, ETF Specialist, Risk Assessor,
Investment Strategist, Research Director, Quality Control Specialist) and their
tasks to identify high-potential ETFs and provide detailed investment
recommendations. The crew follows a KISS (Keep It Simple, Stupid) approach with
DRY (Don't Repeat Yourself) principles and includes a dedicated Quality Control
agent to ensure consistent output quality. ETF investment analysis crew using
the CrewAI framework.
"""

import time
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
from finwiz.tools.tool_factories import get_etf_crew_tools
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task

load_dotenv()

# Get standardized tool set for ETF crew
tools = get_etf_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="etf",
)


@CrewBase
class EtfCrew:
    """
    EtfCrew - Expert ETF trading research team.

    Specialized in identifying high-potential ETFs and providing
    detailed investment recommendations to maximize returns.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self) -> None:
        """Initialize ETF crew with configuration files."""
        # Set configuration paths before calling super().__init__()
        from pathlib import Path

        import yaml

        # Get the directory of this file
        current_dir = Path(__file__).parent

        # Load configuration files
        with open(current_dir / "config" / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)

        with open(current_dir / "config" / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        super().__init__()

        # Make Pydantic models available for CrewAI resolution
        self.ETFTopHolding = ETFTopHolding
        self.ETFFactsheet = ETFFactsheet
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

        # Initialize structured logger
        self.crew_logger = CrewLogger("EtfCrew")

    def _get_configured_llm(self) -> LLM:
        """Get configured LLM instance for this crew."""
        return get_configured_llm()

    @agent
    def market_etf_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_etf_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,  # Enable AI reasoning for ETF analysis decisions
            llm=self._get_configured_llm(),
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            verbose=True,
            tools=tools,
            reasoning=True,  # Enable AI reasoning for risk assessment decisions
            llm=self._get_configured_llm(),
        )

    @agent
    def translator(self) -> Agent:
        """Create translator agent that converts English reports to French while preserving layout."""
        return Agent(
            config=self.agents_config["translator"],
            tools=[],  # No tools - only consumes upstream HTML context
            verbose=True,
            llm=self._get_configured_llm(),
        )

    @async_task
    @task
    def etf_market_trends_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_market_trends_task"],
            verbose=True,
            reasoning=False,
        )

    @async_task
    @task
    def etf_screening_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_screening_task"],
            verbose=True,
            output_pydantic=ETFTopHolding,
        )

    @async_task
    @task
    def etf_technical_detail_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_technical_detail_task"],
            verbose=True,
            output_pydantic=ETFFactsheet,
        )

    @async_task
    @task
    def etf_risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_risk_assessment_task"],
            verbose=True,
            output_pydantic=RiskAssessmentStandardized,
        )

    @sync_task
    @task
    def etf_investment_strategy_task(self) -> Task:
        return Task(config=self.tasks_config["etf_investment_strategy_task"], verbose=True)

    @sync_task
    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create a specialized ETF trading research crew with a sequential workflow."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_retries=10,
            max_iter=25,  # Prevent infinite loops - max iterations per agent
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
        )

    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        """
        Execute the crew with structured logging.

        Args:
            inputs: Input parameters for crew execution

        Returns:
            Crew execution result

        """
        self.crew_logger.log_start(inputs or {})
        start_time = time.time()

        try:
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs=inputs)
            duration = time.time() - start_time
            self.crew_logger.log_complete(duration)
            return result
        except Exception as e:
            self.crew_logger.log_error(e)
            raise
