"""
Define the Stock Crew for stock market research.

This module configures agents (Market Analyst, Fundamental Analyst,
Risk Assessor, Investment Strategist, Research Director) and their
tasks to identify promising stock investments and provide detailed
recommendations.
"""

import time
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.stock import MarketSentiment, TenKInsight
from finwiz.tools.logger import get_logger
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Get standardized tool set for stock crew
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock",
)


@CrewBase
class StockCrew:
    """
    StockCrew - Expert stock market research team.

    Specialized in identifying high-potential stock investments and
    providing detailed, evidence-based investment recommendations.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self) -> None:
        """Initialize stock crew with configuration files."""
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
        self.MarketSentiment = MarketSentiment
        self.TenKInsight = TenKInsight
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

        # Initialize structured logger
        self.crew_logger = CrewLogger("StockCrew")

    def _get_configured_llm(self) -> LLM:
        """Get configured LLM instance for this crew."""
        return get_configured_llm()

    @agent
    def market_technical_analyst(self) -> Agent:
        """Agent that performs technical analysis on target stocks."""
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            verbose=True,
            reasoning=True,  # Enable AI reasoning to show decision-making process
            tools=tools,
            llm=self._get_configured_llm(),
        )

    @agent
    def investment_risk_analyst(self) -> Agent:
        """Agent that evaluates stock-specific and market risks."""
        return Agent(
            config=self.agents_config["investment_risk_analyst"],
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
    def market_technical_analysis_task(self) -> Task:
        """Execute technical analysis for short-listed tickers."""
        return Task(
            config=self.tasks_config["market_technical_analysis_task"],
            verbose=True,
        )

    @async_task
    @task
    def stock_screening_task(self) -> Task:
        """Screen stocks based on predefined quantitative filters."""
        return Task(
            config=self.tasks_config["stock_screening_task"],
            verbose=True,
            output_pydantic=MarketSentiment,
        )

    @async_task
    @task
    def technical_detail_task(self) -> Task:
        """Deep dive into technical indicators and patterns for candidates."""
        return Task(
            config=self.tasks_config["technical_detail_task"],
            verbose=True,
            output_pydantic=TenKInsight,
        )

    @sync_task
    @task
    def stock_risk_assessment_task(self) -> Task:
        """Assess key risks for recommended tickers and mitigation actions."""
        return Task(
            config=self.tasks_config["stock_risk_assessment_task"],
            verbose=True,
            output_pydantic=RiskAssessmentStandardized,
        )

    @sync_task
    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized stock market research crew.

        Uses a sequential workflow for analysis with validation steps to ensure
        high-quality, consistent output formats for both HTML and JSON data.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_iter=25,  # Prevent infinite loops - max iterations per agent
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
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
