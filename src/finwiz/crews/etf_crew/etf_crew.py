"""
Expert team for Exchange-Traded Fund (ETF) research.

DISCOVERY CREW - Designed to screen and identify top 10 stable ETFs.

This module configures agents (Market Analyst, ETF Specialist, Risk Assessor,
Investment Strategist, Research Director, Quality Control Specialist) and their
tasks to identify high-potential ETFs and provide detailed investment
recommendations. The crew follows a KISS (Keep It Simple, Stupid) approach with
DRY (Don't Repeat Yourself) principles and includes a dedicated Quality Control
agent to ensure consistent output quality. ETF investment analysis crew using
the CrewAI framework.

Purpose: Discovery of NEW ETF opportunities (not single-ticker deep analysis)
Use Case: "Find me low-cost diversified ETFs"
Output: Top 10 ETFs with factsheet analysis
Runs: AFTER portfolio analysis to find new opportunities

For single-ticker deep analysis of existing ETF holdings, use DeepAnalysisCrew instead.
"""

import time
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_pydantic, task
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crew_exports import ETFCrewExport
from finwiz.schemas.etf import (
    ETFFactsheet,
    ETFMarketTrend,
    ETFScreeningResult,
    ETFTechnicalAnalysis,
    ETFTopHolding,
)
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.tools.tool_factories import get_etf_crew_tools
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task

load_dotenv()

# Get standardized tool set for ETF crew and make them robust
raw_tools = get_etf_crew_tools(
    include_rag=False,  # Disabled - qdrant-client conflict
    include_quantitative=True,
    collection_suffix="etf",
)
tools = make_tools_robust(raw_tools)


@CrewBase
class EtfCrew:
    """
    EtfCrew - Expert ETF trading research team.

    DISCOVERY CREW - Screens and identifies top 10 stable ETFs.

    Specialized in identifying high-potential ETFs and providing
    detailed investment recommendations to maximize returns.

    Purpose: Discovery of NEW ETF opportunities
    Input: ETF screening criteria (expense ratio, AUM, tracking error)
    Output: Top 10 ETFs with factsheet analysis
    NOT for: Analyzing specific ETFs you already own (use DeepAnalysisCrew)
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

        # Make Pydantic models available for CrewAI resolution BEFORE super().__init__()
        # Use the @output_pydantic decorator to mark them for CrewAI
        self.ETFTopHolding = output_pydantic(ETFTopHolding)
        self.ETFFactsheet = output_pydantic(ETFFactsheet)
        self.ETFMarketTrend = output_pydantic(ETFMarketTrend)
        self.ETFScreeningResult = output_pydantic(ETFScreeningResult)
        self.ETFTechnicalAnalysis = output_pydantic(ETFTechnicalAnalysis)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)

        super().__init__()

        # Initialize structured logger
        self.crew_logger = CrewLogger("EtfCrew")

    def _get_configured_llm(self) -> LLM:
        """
        Get configured LLM instance for this crew.

        Uses LLM_MODEL_STANDARD environment variable.
        """
        return get_configured_llm(model_type="standard")

    @agent
    def market_etf_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_etf_analyst"],
            verbose=True,
            tools=tools,
            reasoning=False,  # Disable reasoning to prevent infinite planning loops (same issue as stock crew)
            llm=self._get_configured_llm(),
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            verbose=True,
            tools=tools,
            reasoning=False,  # Disable reasoning to prevent infinite planning loops
            llm=self._get_configured_llm(),
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Consolidate analysis findings into ETFCrewExport."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty - enforced by @final_reporter decorator
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
            reasoning=False,  # Disable reasoning to prevent infinite loops
        )

    @async_task
    @task
    def etf_technical_detail_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_technical_detail_task"],
            verbose=True,
            output_pydantic=ETFFactsheet,
            reasoning=False,  # Disable reasoning to prevent infinite loops
        )

    @async_task
    @task
    def etf_risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_risk_assessment_task"],
            verbose=True,
            output_pydantic=RiskAssessmentStandardized,
            reasoning=False,  # Disable reasoning to prevent infinite loops
        )

    @sync_task
    @task
    def etf_investment_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_investment_strategy_task"],
            verbose=True,
            reasoning=False,  # Disable reasoning to prevent infinite loops
        )

    @sync_task
    @task
    def generate_export_task(self) -> Task:
        """Generate ETFCrewExport JSON from all analysis findings."""
        return Task(
            config=self.tasks_config["generate_export_task"],
            output_pydantic=ETFCrewExport,
            verbose=True,
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
        """Create a specialized ETF trading research crew with a sequential workflow."""
        from finwiz.utils.llm_config import get_manager_llm

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
            manager_llm=get_manager_llm(),  # Use configured LLM to avoid 'stop' parameter errors
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
