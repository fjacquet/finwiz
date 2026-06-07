"""
Investment Discovery Crew for A+ grade investment opportunities.

This module implements the Investment Discovery Crew that proactively discovers
A+ grade investment opportunities across ETFs, stocks, and cryptocurrencies.
The crew transforms FinWiz from a reactive evaluator to a proactive discoverer
of exceptional investment opportunities.
"""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_pydantic, task
from dotenv import load_dotenv

from finwiz.infrastructure.decorators.agent_validators import final_reporter
from finwiz.infrastructure.decorators.task_decorators import async_task, sync_task
from finwiz.schemas.crew_exports import DiscoveryCrewExport
from finwiz.schemas.investment_discovery import (
    APlusDiscoveryResult,
    OptimizationResult,
    ValidationResult,
)
from finwiz.tools.file_tools import DirectoryReadTool, FileReadTool
from finwiz.tools.finance_tools import (
    get_crypto_research_tools,
    get_etf_research_tools,
    get_investment_discovery_tools,
    get_stock_discovery_tools,
)
from finwiz.tools.optimization_tool import get_optimization_tool
from finwiz.tools.portfolio_analysis_tool import get_portfolio_analysis_tool
from finwiz.tools.portfolio_rebalancing_tool import get_portfolio_rebalancing_tool
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.risk_assessment_tool import get_risk_assessment_tool

load_dotenv()

# Lazy-loaded tool caches (avoid module-level instantiation that fails without API keys)
_tool_cache: dict[str, list] = {}


def _get_common_tools() -> list:
    """Get common tools shared by all discovery agents (lazy-loaded)."""
    if "common" not in _tool_cache:
        investment_discovery_tools = get_investment_discovery_tools()
        quantitative_tool = get_quantitative_analysis_tool()
        _tool_cache["common"] = [
            *investment_discovery_tools,
            quantitative_tool,
            # Schema and documentation access
            DirectoryReadTool(directory="output/discovery"),
            DirectoryReadTool(directory="docs/schemas"),
            DirectoryReadTool(directory="docs/schemas/examples"),
            FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
            FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
            FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
        ]
    return _tool_cache["common"]


def _get_etf_discovery_tools() -> list:
    """Get ETF discovery agent tools (lazy-loaded)."""
    if "etf" not in _tool_cache:
        _tool_cache["etf"] = _get_common_tools() + get_etf_research_tools()
    return _tool_cache["etf"]


def _get_stock_discovery_tools() -> list:
    """Get stock discovery agent tools (lazy-loaded)."""
    if "stock" not in _tool_cache:
        _tool_cache["stock"] = _get_common_tools() + get_stock_discovery_tools()
    return _tool_cache["stock"]


def _get_crypto_discovery_tools() -> list:
    """Get crypto discovery agent tools (lazy-loaded)."""
    if "crypto" not in _tool_cache:
        _tool_cache["crypto"] = _get_common_tools() + get_crypto_research_tools()
    return _tool_cache["crypto"]


def _get_portfolio_tools() -> list:
    """Get portfolio optimization tools (lazy-loaded)."""
    if "portfolio" not in _tool_cache:
        portfolio_optimization_tools = [
            get_portfolio_analysis_tool(),
            get_optimization_tool(),
            get_risk_assessment_tool(),
            get_portfolio_rebalancing_tool(),
        ]
        _tool_cache["portfolio"] = _get_common_tools() + portfolio_optimization_tools
    return _tool_cache["portfolio"]


@CrewBase
class InvestmentDiscoveryCrew:
    """
    Investment Discovery Crew for A+ grade opportunities.

    Specialized crew that proactively discovers exceptional investment
    opportunities with A+ potential across ETFs, stocks, and cryptocurrencies.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

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
        self.APlusDiscoveryResult = output_pydantic(APlusDiscoveryResult)
        self.ValidationResult = output_pydantic(ValidationResult)
        self.OptimizationResult = output_pydantic(OptimizationResult)

        # CrewBase does not support super().__init__() - config loading is sufficient

    def _get_configured_llm(self) -> LLM:
        """
        Get configured LLM instance for this crew.

        Uses LLM_MODEL_STANDARD environment variable.
        """
        from finwiz.config.llm.llm_config import get_configured_llm

        return get_configured_llm(model_type="standard")

    @agent
    def etf_discovery_agent(self) -> Agent:
        """ETF Discovery Agent specialized in finding A+ grade ETFs."""
        return Agent(
            config=self.agents_config["etf_discovery_agent"],
            verbose=True,
            tools=_get_etf_discovery_tools(),
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @agent
    def stock_discovery_agent(self) -> Agent:
        """Stock Discovery Agent specialized in finding A+ grade stocks."""
        return Agent(
            config=self.agents_config["stock_discovery_agent"],
            verbose=True,
            tools=_get_stock_discovery_tools(),
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @agent
    def crypto_discovery_agent(self) -> Agent:
        """Crypto Discovery Agent specialized in finding A+ grade cryptocurrencies."""
        return Agent(
            config=self.agents_config["crypto_discovery_agent"],
            verbose=True,
            tools=_get_crypto_discovery_tools(),
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @agent
    def portfolio_optimization_agent(self) -> Agent:
        """Portfolio Optimization Agent for integrating A+ discoveries."""
        return Agent(
            config=self.agents_config["portfolio_optimization_agent"],
            verbose=True,
            tools=_get_portfolio_tools(),
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @agent
    def validation_agent(self) -> Agent:
        """Create validation agent for rigorous backtesting and risk analysis."""
        # Validation-specific tools
        from finwiz.tools.backtesting_tool import get_backtesting_tool
        from finwiz.tools.enhanced_sec_tool import StandardizedRiskScoringTool

        validation_tools = [
            get_backtesting_tool(),
            get_risk_assessment_tool(),
            StandardizedRiskScoringTool(),
            get_quantitative_analysis_tool(),
        ]

        return Agent(
            config=self.agents_config["validation_agent"],
            verbose=True,
            tools=validation_tools,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite loops
            llm=self._get_configured_llm(),
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Consolidate discovery findings into DiscoveryCrewExport."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty - enforced by @final_reporter decorator
            verbose=True,
            llm=self._get_configured_llm(),
        )

    @async_task
    @task
    def etf_discovery_task(self) -> Task:
        """Task for discovering A+ grade ETFs."""
        return Task(
            config=self.tasks_config["etf_discovery_task"],
        )

    @async_task
    @task
    def stock_discovery_task(self) -> Task:
        """Task for discovering A+ grade stocks."""
        return Task(
            config=self.tasks_config["stock_discovery_task"],
        )

    @async_task
    @task
    def crypto_discovery_task(self) -> Task:
        """Task for discovering A+ grade cryptocurrencies."""
        return Task(
            config=self.tasks_config["crypto_discovery_task"],
        )

    @async_task
    @task
    def validation_task(self) -> Task:
        """Task for validating A+ candidates through backtesting."""
        return Task(
            config=self.tasks_config["validation_task"],
        )

    @async_task
    @task
    def optimization_task(self) -> Task:
        """Task for optimizing portfolio with A+ discoveries."""
        return Task(
            config=self.tasks_config["optimization_task"],
        )

    @sync_task
    @task
    def report_generation_task(self) -> Task:
        """Task for generating comprehensive discovery report."""
        return Task(
            config=self.tasks_config["report_generation_task"],
        )

    @sync_task
    @task
    def generate_export_task(self) -> Task:
        """Generate DiscoveryCrewExport JSON from all discovery findings."""
        return Task(
            config=self.tasks_config["generate_export_task"],
            output_pydantic=DiscoveryCrewExport,
        )

    @crew
    def crew(self) -> Crew:
        """Create the Investment Discovery Crew with sequential workflow."""
        from finwiz.config.llm.llm_config import get_manager_llm

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_retries=10,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            manager_llm=get_manager_llm(),  # Use configured LLM to avoid 'stop' parameter errors
            memory=False,  # ⚡ DISABLED: Prevents token overflow from accumulated memory
        )
