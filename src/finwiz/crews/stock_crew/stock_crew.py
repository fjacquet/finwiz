"""
Define the Stock Crew for stock market research.

DISCOVERY CREW - Designed to screen and identify top 10 promising stocks.

This module configures agents (Market Analyst, Fundamental Analyst,
Risk Assessor, Investment Strategist, Research Director) and their
tasks to identify promising stock investments and provide detailed
recommendations.

Purpose: Discovery of NEW stock opportunities (not single-ticker deep analysis)
Use Case: "Find me the best growth stocks"
Output: Top 10 stocks with analysis
Runs: AFTER portfolio analysis to find new opportunities

For single-ticker deep analysis of existing holdings, use DeepAnalysisCrew instead.
"""

import time
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_pydantic, task
from dotenv import load_dotenv

from finwiz.config.llm.llm_config import get_configured_llm
from finwiz.infrastructure.decorators.agent_validators import final_reporter
from finwiz.infrastructure.decorators.task_decorators import async_task, sync_task
from finwiz.infrastructure.logging.helpers import CrewLogger
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crew_exports import StockCrewExport
from finwiz.schemas.stock import (
    MarketSentiment,
    MarketTrend,
    StockScreeningResult,
    StockTechnicalAnalysis,
    TenKInsight,
)
from finwiz.tools.logger import get_logger
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.tools.tool_factories import get_stock_crew_tools

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Get standardized tool set for stock crew and make them robust
raw_tools = get_stock_crew_tools(
    include_rag=False,  # Disabled - qdrant-client conflict
    include_quantitative=True,
    collection_suffix="stock",
)
tools = make_tools_robust(raw_tools)


@CrewBase
class StockCrew:
    """
    StockCrew - Expert stock market research team.

    DISCOVERY CREW - Screens and identifies top 10 promising stocks.

    Specialized in identifying high-potential stock investments and
    providing detailed, evidence-based investment recommendations.

    Purpose: Discovery of NEW stock opportunities
    Input: Market screening criteria
    Output: Top 10 stocks with comprehensive analysis
    NOT for: Analyzing specific holdings you already own (use DeepAnalysisCrew)
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

        # Make Pydantic models available for CrewAI resolution BEFORE super().__init__()
        # Use the @output_pydantic decorator to mark them for CrewAI
        self.MarketSentiment = output_pydantic(MarketSentiment)
        self.MarketTrend = output_pydantic(MarketTrend)
        self.StockScreeningResult = output_pydantic(StockScreeningResult)
        self.StockTechnicalAnalysis = output_pydantic(StockTechnicalAnalysis)
        self.TenKInsight = output_pydantic(TenKInsight)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)

        # Initialize structured logger
        self.crew_logger = CrewLogger("StockCrew")

    def _get_configured_llm(self) -> LLM:
        """
        Get configured LLM instance for this crew.

        Uses LLM_MODEL_STANDARD environment variable.
        """
        return get_configured_llm(model_type="standard")

    @agent
    def market_technical_analyst(self) -> Agent:
        """Agent that performs technical analysis on target stocks."""
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            verbose=True,
            reasoning=True,  # Enable for complex technical analysis
            max_reasoning_attempts=3,  # Prevent infinite loops
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
            reasoning=True,  # Enable for complex risk assessment
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Consolidate analysis findings into StockCrewExport."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty - enforced by @final_reporter decorator
            verbose=True,
            llm=self._get_configured_llm(),
        )

    # @agent
    # def translator(self) -> Agent:
    #     """Create translator agent that converts English reports to French while preserving layout."""
    #     return Agent(
    #         config=self.agents_config["translator"],
    #         tools=[],  # No tools - only consumes upstream HTML context
    #         verbose=True,
    #         llm=self._get_configured_llm(),
    #     )

    @async_task
    @task
    def market_technical_analysis_task(self) -> Task:
        """Execute technical analysis for short-listed tickers."""
        return Task(
            config=self.tasks_config["market_technical_analysis_task"],
        )

    @async_task
    @task
    def stock_screening_task(self) -> Task:
        """Screen stocks based on predefined quantitative filters."""
        return Task(
            config=self.tasks_config["stock_screening_task"],
        )

    @async_task
    @task
    def technical_detail_task(self) -> Task:
        """Deep dive into technical indicators and patterns for candidates."""
        return Task(
            config=self.tasks_config["technical_detail_task"],
        )

    @sync_task
    @task
    def stock_risk_assessment_task(self) -> Task:
        """Assess key risks for recommended tickers and mitigation actions."""
        return Task(
            config=self.tasks_config["stock_risk_assessment_task"],
        )

    @sync_task
    @task
    def generate_export_task(self) -> Task:
        """Generate StockCrewExport JSON from all analysis findings."""
        return Task(
            config=self.tasks_config["generate_export_task"],
            output_pydantic=StockCrewExport,
        )

    # @sync_task
    # @task
    # def translation_task(self) -> Task:
    #     """Task to translate the English report to French while preserving layout."""
    #     return Task(
    #         config=self.tasks_config["translation_task"],
    #     )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized stock market research crew.

        Uses a sequential workflow for analysis with validation steps to ensure
        high-quality, consistent output formats for both HTML and JSON data.
        """
        from finwiz.config.llm.llm_config import get_manager_llm

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
            manager_llm=get_manager_llm(),  # Use configured LLM to avoid 'stop' parameter errors
            memory=False,  # ⚡ DISABLED: Prevents token overflow from accumulated memory
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
