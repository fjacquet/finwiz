"""
Defines the Crypto Crew for cryptocurrency research.

This module initializes and configures the crypto analysis crew, including agents,
_tasks, and tools.
"""

import time
from pathlib import Path
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, output_pydantic, task

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crypto import (
    CryptoInvestmentStrategy,
    CryptoMarketAnalysis,
    CryptoRiskProfile,
    CryptoTechnicalAnalysis,
    CryptoThesis,
)
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.tools.tool_factories import get_crypto_crew_tools
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task

# Get the absolute path of the current script
current_script_path = Path(__file__).resolve()
crew_dir = current_script_path.parent

# Get standardized tool set for crypto crew and make them robust
raw_research_tools = get_crypto_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="crypto",
)
research_tools = make_tools_robust(raw_research_tools)


@CrewBase
class CryptoCrew:
    """Crypto crew for cryptocurrency analysis."""

    def __init__(self) -> None:
        """Set configuration paths before calling super().__init__()."""
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
        self.CryptoThesis = output_pydantic(CryptoThesis)
        self.CryptoMarketAnalysis = output_pydantic(CryptoMarketAnalysis)
        self.CryptoTechnicalAnalysis = output_pydantic(CryptoTechnicalAnalysis)
        self.CryptoRiskProfile = output_pydantic(CryptoRiskProfile)
        self.CryptoInvestmentStrategy = output_pydantic(CryptoInvestmentStrategy)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)

        super().__init__()

        # Initialize structured logger
        self.crew_logger = CrewLogger("CryptoCrew")

    def _get_configured_llm(self) -> LLM:
        """Get configured LLM instance for this crew."""
        return get_configured_llm()

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_analyst"],
            tools=research_tools,
            reasoning=False,  # Enable AI reasoning for market analysis decisions
            verbose=True,
            llm=self._get_configured_llm(),
        )

    @agent
    def technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_analyst"],
            tools=research_tools,
            reasoning=False,  # Enable AI reasoning for technical analysis decisions
            verbose=True,
            llm=self._get_configured_llm(),
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=research_tools,
            verbose=True,
            reasoning=False,  # Enable AI reasoning for risk assessment decisions
            llm=self._get_configured_llm(),
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            tools=research_tools,
            verbose=True,
            reasoning=False,  # Enable AI reasoning for investment strategy decisions
            llm=self._get_configured_llm(),
        )

    @agent
    def research_director(self) -> Agent:
        return Agent(
            config=self.agents_config["research_director"],
            tools=[],
            verbose=True,
            reasoning=False,  # Enable AI reasoning for research consolidation decisions
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
    def market_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_analysis_task"],
        )

    @async_task
    @task
    def technical_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["technical_analysis_task"])

    @async_task
    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_assessment_task"],
        )

    @async_task
    @task
    def investment_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["investment_strategy_task"],
        )

    @sync_task
    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
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
        """Create the crypto analysis crew."""
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
