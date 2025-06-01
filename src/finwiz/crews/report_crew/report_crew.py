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

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectorySearchTool
from dotenv import load_dotenv

from finwiz.tools.finance_tools import get_report_integration_tools

load_dotenv()


# Initialize tools for report crew
directory_search_tool = DirectorySearchTool(directory="./search_results")

# Get report integration tools
integration_tools = get_report_integration_tools()

# Combine directory search tool with report integration tools
tools = [directory_search_tool, *integration_tools]


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
        """
        Create a financial integration analyst.

        Specializes in consolidating recommendations from Stock, ETF, and Crypto
        crews without conducting additional external research, and identifying
        the strongest opportunities from the provided crew outputs.
        """
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            allow_delegation=False,
            respect_context_window=True,
            max_reasoning_steps=5,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """
        Create a portfolio allocation specialist.

        Develops optimal asset allocation strategies within the 1000 CHF
        monthly budget based exclusively on the recommendations from
        Stock, ETF, and Crypto crews.
        """
        return Agent(
            config=self.agents_config["portfolio_allocator"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            allow_delegation=False,
            respect_context_window=True,
            max_reasoning_steps=5,
        )

    @agent
    def risk_manager(self) -> Agent:
        """
        Create a risk management specialist.

        Evaluates investment risks and develops appropriate mitigation
        strategies based on the integrated analysis of recommendations
        from Stock, ETF, and Crypto crews.
        """
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            allow_delegation=False,
            respect_context_window=True,
            max_reasoning_steps=5,
        )

    @task
    def integration_portfolio_task(self) -> Task:
        """
        Define task to analyze, integrate, and allocate investments.

        Integrates recommendations from Stock, ETF, and Crypto crews without
        conducting additional external research, and creates an optimal
        portfolio allocation within a 1000 CHF budget.
        """
        return Task(
            config=self.tasks_config["integration_portfolio_task"],  # type: ignore[index]
            async_execution=False,
        )

    @task
    def risk_final_report_task(self) -> Task:
        """
        Define task to assess risks and create the final investment report.

        Evaluates portfolio risks and creates a comprehensive investment report
        with risk mitigation strategies and implementation guidance based
        exclusively on the integrated analysis of recommendations from
        Stock, ETF, and Crypto crews.
        """
        return Task(
            config=self.tasks_config["risk_final_report_task"],  # type: ignore[index]
            async_execution=False,
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
            process=Process.hierarchical,
            verbose=True,
            memory=True,
            allow_delegation=True,
            allow_termination=True,
            respect_context_window=True,
            max_retries=10,
        )
