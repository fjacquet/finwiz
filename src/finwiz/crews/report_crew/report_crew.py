"""
Define the Report Crew for integrated financial analysis.

This module sets up specialized agents (Financial Integration
Analyst, Portfolio Allocator, Risk Manager) and their sequential
tasks. The crew exclusively consumes and analyzes recommendations
from Stock, ETF, and Crypto crews, creates an optimal portfolio
allocation within a specified budget (1000 CHF monthly),
assesses associated risks, and produces a detailed, evidence-based
investment report without conducting additional external research.
"""

import logging
from pathlib import Path
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

from finwiz.crews.helpers.context_preparation import ContextPreparationManager
from finwiz.integration.aplus_discovery_accessor import APlusDiscoveryAccessor
from finwiz.integration.backtesting_extractor import BacktestingDataExtractor
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.task_decorators import async_task, sync_task

load_dotenv()

logger = logging.getLogger(__name__)

# Get RAG tools for knowledge retrieval and storage and make them robust
# raw_rag_tools = get_rag_tools(collection_suffix="report")  # DISABLED - qdrant conflict
raw_rag_tools = []  # Empty list
rag_tools = make_tools_robust(raw_rag_tools)


@CrewBase
class ReportCrew:
    """
    ReportCrew - Expert Financial Integration Team.

    Specialized in analyzing recommendations exclusively from Stock, ETF,
    and Crypto crews without conducting additional external research.
    Creates detailed, evidence-based investment plans with a fixed budget.
    The team focuses on creating optimal portfolio allocations across
    asset classes while maintaining rigorous risk management protocols.
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize report crew with data integration."""
        super().__init__(*args, **kwargs)

        # Initialize tools
        self.tools = self._get_tools()

        # Initialize context preparation manager
        self.context_manager = self._get_context_manager()

    def _get_tools(self) -> list[Any]:
        """Get all tools for the crew."""
        return [
            *rag_tools,  # RAG tools for knowledge retrieval
            # ALWAYS load ALL output directories
            DirectoryReadTool(directory="output/stock"),
            DirectoryReadTool(directory="output/etf"),
            DirectoryReadTool(directory="output/crypto"),
            DirectoryReadTool(directory="output/portfolio"),
            DirectoryReadTool(directory="output/discovery"),
            DirectoryReadTool(directory="output/deep_analysis"),
            DirectoryReadTool(directory="output/report"),
            # Schema tools for contract-aware reading
            DirectoryReadTool(directory="docs/schemas"),
            DirectoryReadTool(directory="docs/schemas/examples"),
            FileReadTool(file_path="docs/schemas/ReporterInput.schema.json"),
            FileReadTool(file_path="docs/schemas/examples/reporter_input.example.json"),
            FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
            FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
            FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
        ]

    def _get_context_manager(self) -> ContextPreparationManager:
        """Get context preparation manager."""
        output_dir = Path("output")
        integration_manager = CrewDataIntegrationManager(output_dir)
        data_accessor = CrewDataAccessor(integration_manager)
        discovery_accessor = APlusDiscoveryAccessor(output_dir=output_dir)
        backtesting_extractor = BacktestingDataExtractor(logger=logger)
        availability_tracker = DataAvailabilityTracker(
            stale_threshold_hours=168.0,  # 7 days
            logger=logger,
        )

        return ContextPreparationManager(
            data_accessor=data_accessor,
            discovery_accessor=discovery_accessor,
            backtesting_extractor=backtesting_extractor,
            availability_tracker=availability_tracker,
        )

    @agent
    def financial_integration_analyst(self) -> Agent:
        """Agent that integrates Stock/ETF/Crypto analyses into unified narrative."""
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            reasoning=True,
            tools=self.tools,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """Agent that proposes optimal cross-asset portfolio allocations."""
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=self.tools,
            reasoning=True,
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that identifies and mitigates portfolio and market risks."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=self.tools,
            reasoning=True,
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

    @async_task
    @task
    def comprehensive_financial_integration_task(self) -> Task:
        """Integrate Stock/ETF/Crypto analyses into a unified narrative."""
        return Task(
            config=self.tasks_config["comprehensive_financial_integration_task"],
            verbose=True,
        )

    @async_task
    @task
    def optimal_portfolio_allocation_task(self) -> Task:
        """Derive optimal asset allocation based on goals and constraints."""
        return Task(
            config=self.tasks_config["optimal_portfolio_allocation_task"],
            verbose=True,
        )

    @async_task
    @task
    def risk_assessment_mitigation_task(self) -> Task:
        """Assess key risks and propose mitigation strategies."""
        return Task(
            config=self.tasks_config["risk_assessment_mitigation_task"],
            verbose=True,
        )

    @sync_task
    @task
    def comprehensive_investment_report_task(self) -> Task:
        """Compile the comprehensive HTML investment report."""
        return Task(
            config=self.tasks_config["comprehensive_investment_report_task"],
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized financial integration crew.

        This crew analyzes recommendations exclusively from Stock, ETF, and Crypto
        Crews without conducting additional external research, creates an optimal
        portfolio allocation within a 1000 CHF monthly budget, assesses investment
        risks, and produces a comprehensive investment report with actionable
        recommendations backed by verifiable evidence. Uses a sequential workflow.
        """
        agents = [
            self.financial_integration_analyst(),
            self.portfolio_allocator(),
            self.risk_manager(),
            self.investment_reporter(),
        ]

        tasks = [
            self.comprehensive_financial_integration_task(),
            self.optimal_portfolio_allocation_task(),
            self.risk_assessment_mitigation_task(),
            self.comprehensive_investment_report_task(),
        ]

        # Create crew with integrated data context
        from finwiz.utils.llm_config import get_manager_llm

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            allow_delegation=False,
            allow_termination=True,
            respect_context_window=True,
            max_retries=10,
            max_rpm=20,
            llm="gpt-5",
            manager_llm=get_manager_llm(),
        )

        return crew
