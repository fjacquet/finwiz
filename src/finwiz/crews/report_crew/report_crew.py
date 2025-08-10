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

# Third-party imports
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

from finwiz.tools.file_conversion_tools import HtmlToPdfTool  # Added for PDF conversion

# Local application imports
from finwiz.tools.rag_tools import get_rag_tools

# from finwiz.tools.html_output_tool import HTMLOutputTool

load_dotenv()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="report")


crypto_reports = DirectoryReadTool(directory=("output/crypto"))
etf_reports = DirectoryReadTool(directory=("output/etf"))
stock_reports = DirectoryReadTool(directory=("output/stock"))
portfolio_outputs = DirectoryReadTool(directory=("output/portfolio"))

html_to_pdf_tool = HtmlToPdfTool()  # Tool instance for PDF conversion


# Tools for report generation and analysis
tools = [
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
    crypto_reports,
    etf_reports,
    stock_reports,
    portfolio_outputs,
    # Schemas and examples for contract-aware reading
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/ReporterInput.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/reporter_input.example.json")),
]


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

    @agent
    def financial_integration_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            reasoning=True,
            tools=tools,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """Agent that proposes optimal cross-asset portfolio allocations."""
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=tools,
            reasoning=True,
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that identifies and mitigates portfolio and market risks."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=tools,
            reasoning=True,
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
    def pdf_conversion_specialist(self) -> Agent:
        """Agent specialized in converting final HTML reports to PDF."""
        return Agent(
            config=self.agents_config["pdf_conversion_specialist"],
            verbose=True,
            tools=[html_to_pdf_tool],  # Use the specific tool instance
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
    def pdf_generation_task(self) -> Task:
        """Generate a PDF version of the final HTML report."""
        return Task(
            config=self.tasks_config["pdf_generation_task"],
            verbose=True,
            # Agent is assigned via tasks.yaml, context is passed from previous task
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
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            allow_delegation=False,
            allow_termination=True,
            respect_context_window=True,
            max_retries=10,
            max_rpm=20,
        )
