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

# Third-party imports
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

# Local application imports
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.manager import CrewDataIntegrationManager
from finwiz.tools.file_conversion_tools import HtmlToPdfTool  # Added for PDF conversion
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.validation.tool_restrictions import ReporterInputValidator, ToolRestrictionValidator

# from finwiz.tools.html_output_tool import HTMLOutputTool

load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="report")

html_to_pdf_tool = HtmlToPdfTool()  # Tool instance for PDF conversion


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

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize report crew with validators and data integration."""
        super().__init__(*args, **kwargs)
        self.tool_validator = ToolRestrictionValidator()
        self.input_validator = ReporterInputValidator()

        # Initialize data integration components
        self.output_dir = Path("output")
        self.integration_manager = CrewDataIntegrationManager(self.output_dir)
        self.data_accessor = CrewDataAccessor(self.integration_manager)

        # Initialize tools with data availability checking
        self._initialize_tools()

    def _initialize_tools(self) -> None:
        """Initialize tools with data availability checking and graceful degradation."""
        try:
            # Check data availability before setting up tools
            availability_report = self.data_accessor.check_data_availability()

            # Log data availability status
            logger.info(
                f"Data availability check: {availability_report.overall_status.value}",
                extra={
                    "stock_available": availability_report.stock_available,
                    "etf_available": availability_report.etf_available,
                    "crypto_available": availability_report.crypto_available,
                    "discovery_available": availability_report.discovery_available,
                    "portfolio_available": availability_report.portfolio_available,
                },
            )

            # Set up tools based on data availability
            self.tools = [*rag_tools]  # Always include RAG tools

            # Add directory tools only for available data
            if availability_report.stock_available:
                self.tools.append(DirectoryReadTool(directory="output/stock"))
            if availability_report.etf_available:
                self.tools.append(DirectoryReadTool(directory="output/etf"))
            if availability_report.crypto_available:
                self.tools.append(DirectoryReadTool(directory="output/crypto"))
            if availability_report.portfolio_available:
                self.tools.append(DirectoryReadTool(directory="output/portfolio"))
            if availability_report.discovery_available:
                self.tools.append(DirectoryReadTool(directory="output/discovery"))

            # Always add schema tools for contract-aware reading
            self.tools.extend(
                [
                    DirectoryReadTool(directory="docs/schemas"),
                    DirectoryReadTool(directory="docs/schemas/examples"),
                    FileReadTool(file_path="docs/schemas/ReporterInput.schema.json"),
                    FileReadTool(file_path="docs/schemas/examples/reporter_input.example.json"),
                    FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
                    FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
                    FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
                ]
            )

            # Log warnings for missing data
            if availability_report.missing_data:
                logger.warning(
                    f"Missing data for crews: {', '.join(availability_report.missing_data)}. "
                    "Report generation will proceed with available data."
                )

            # Log stale data warnings
            if availability_report.stale_data:
                stale_warnings = self.data_accessor.get_stale_data_warnings()
                for warning in stale_warnings:
                    logger.warning(warning)

        except Exception as e:
            logger.error(f"Failed to initialize tools with data integration: {str(e)}", exc_info=True)
            # Fallback to basic tools
            self.tools = [
                *rag_tools,
                DirectoryReadTool(directory="output/crypto"),
                DirectoryReadTool(directory="output/etf"),
                DirectoryReadTool(directory="output/stock"),
                DirectoryReadTool(directory="output/portfolio"),
                DirectoryReadTool(directory="output/discovery"),
                DirectoryReadTool(directory="docs/schemas"),
                DirectoryReadTool(directory="docs/schemas/examples"),
                FileReadTool(file_path="docs/schemas/ReporterInput.schema.json"),
                FileReadTool(file_path="docs/schemas/examples/reporter_input.example.json"),
                FileReadTool(file_path="docs/schemas/APlusDiscoveryResult.schema.json"),
                FileReadTool(file_path="docs/schemas/OptimizationResult.schema.json"),
                FileReadTool(file_path="docs/schemas/ValidationResult.schema.json"),
            ]

    def get_integrated_data_context(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Get integrated data context for report generation.

        Args:
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Dictionary containing consolidated data and metadata

        """
        try:
            # Get consolidated reporter input with all integrated data
            integrated_data = self.data_accessor.get_consolidated_reporter_input(max_age_hours)

            # Add data availability information
            integrated_data["data_availability_report"] = self.data_accessor.check_data_availability(max_age_hours)

            # Add stale data warnings
            integrated_data["stale_data_warnings"] = self.data_accessor.get_stale_data_warnings(max_age_hours)

            logger.info("Integrated data context prepared for report generation")
            return integrated_data

        except Exception as e:
            logger.error(f"Failed to get integrated data context: {str(e)}", exc_info=True)
            return {
                "error": f"Data integration failed: {str(e)}",
                "fallback_mode": True,
                "data_availability_report": None,
                "stale_data_warnings": [f"Data integration error: {str(e)}"],
            }

    @agent
    def financial_integration_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            reasoning=False,
            tools=self.tools,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """Agent that proposes optimal cross-asset portfolio allocations."""
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=self.tools,
            reasoning=False,
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that identifies and mitigates portfolio and market risks."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=self.tools,
            reasoning=False,
        )

    @agent
    def investment_reporter(self) -> Agent:
        """Define the final reporter with no tools; format the consolidated HTML report."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            verbose=True,
            # Per FinWiz policy: final reporter must have NO tools; it only consumes upstream
            # context and formats the final HTML report.
            tools=[],
        )

    @agent
    def translator(self) -> Agent:
        """Create translator agent that converts English reports to French while preserving layout."""
        return Agent(
            config=self.agents_config["translator"],
            tools=[],  # No tools - only consumes upstream HTML context
            verbose=True,
        )

    @task
    def comprehensive_financial_integration_task(self) -> Task:
        """Integrate Stock/ETF/Crypto analyses into a unified narrative."""
        return Task(
            config=self.tasks_config["comprehensive_financial_integration_task"],
            verbose=True,
        )

    @task
    def optimal_portfolio_allocation_task(self) -> Task:
        """Derive optimal asset allocation based on goals and constraints."""
        return Task(
            config=self.tasks_config["optimal_portfolio_allocation_task"],
            verbose=True,
        )

    @task
    def risk_assessment_mitigation_task(self) -> Task:
        """Assess key risks and propose mitigation strategies."""
        return Task(
            config=self.tasks_config["risk_assessment_mitigation_task"],
            verbose=True,
        )

    @task
    def comprehensive_investment_report_task(self) -> Task:
        """Compile the comprehensive HTML investment report."""
        return Task(
            config=self.tasks_config["comprehensive_investment_report_task"],
            verbose=True,
        )

    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
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
        # Get all agents for validation and crew creation
        agents = [
            self.financial_integration_analyst(),
            self.portfolio_allocator(),
            self.risk_manager(),
            self.investment_reporter(),
            self.translator(),
        ]

        tasks = [
            self.comprehensive_financial_integration_task(),
            self.optimal_portfolio_allocation_task(),
            self.risk_assessment_mitigation_task(),
            self.comprehensive_investment_report_task(),
            self.translation_task(),
        ]

        # Validate tool restrictions before creating crew
        try:
            self.tool_validator.validate_crew_compliance(agents)
            logger.info("Tool restriction validation passed for ReportCrew")
        except Exception as e:
            logger.error(f"Tool restriction validation failed: {e}")
            raise

        # Create crew with integrated data context
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
        )

        return crew

    def kickoff(self, inputs: dict[str, Any] | None = None, max_age_hours: int = 24) -> Any:
        """
        Execute the crew with integrated data context.

        Args:
            inputs: Additional inputs for crew execution
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Crew execution result

        """
        try:
            # Prepare integrated context
            integrated_context = self.prepare_crew_context(max_age_hours)

            # Merge with provided inputs
            if inputs:
                integrated_context.update(inputs)

            # Log execution start with data status
            logger.info(
                "Starting ReportCrew execution with integrated data",
                extra={
                    "max_age_hours": max_age_hours,
                    "has_integrated_context": "error" not in integrated_context,
                    "fallback_mode": integrated_context.get("fallback_mode", False),
                },
            )

            # Execute crew with integrated context
            crew = self.crew()
            result = crew.kickoff(inputs=integrated_context)

            logger.info("ReportCrew execution completed successfully")
            return result

        except Exception as e:
            logger.error(f"ReportCrew execution failed: {str(e)}", exc_info=True)
            raise

    def validate_reporter_input(self, context: dict[str, Any]) -> None:
        """
        Validate that reporter receives proper upstream context.

        Args:
            context: The context data being passed to the reporter

        """
        self.input_validator.validate_reporter_context(context)

    def prepare_crew_context(self, max_age_hours: int = 24) -> dict[str, Any]:
        """
        Prepare integrated context for crew execution.

        Args:
            max_age_hours: Maximum acceptable age in hours for data

        Returns:
            Dictionary containing all integrated data and metadata for crew execution

        """
        try:
            # Get integrated data context
            integrated_context = self.get_integrated_data_context(max_age_hours)

            # Validate the integrated context
            self.validate_reporter_input(integrated_context)

            # Add execution metadata
            integrated_context["execution_metadata"] = {
                "max_age_hours": max_age_hours,
                "integration_manager_initialized": self.integration_manager is not None,
                "data_accessor_initialized": self.data_accessor is not None,
                "tools_count": len(self.tools),
            }

            logger.info("Crew context prepared with integrated data")
            return integrated_context

        except Exception as e:
            logger.error(f"Failed to prepare crew context: {str(e)}", exc_info=True)
            # Return minimal context for graceful degradation
            return {
                "error": f"Context preparation failed: {str(e)}",
                "fallback_mode": True,
                "execution_metadata": {
                    "max_age_hours": max_age_hours,
                    "integration_manager_initialized": False,
                    "data_accessor_initialized": False,
                    "tools_count": len(self.tools) if hasattr(self, "tools") else 0,
                },
            }
