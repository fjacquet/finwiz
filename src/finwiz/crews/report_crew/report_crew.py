"""
Define the Report Crew for integrated financial analysis.

This module sets up specialized agents (Financial Integration
Analyst, Portfolio Allocator, Risk Manager, Investment Reporter)
and their sequential tasks. The crew consolidates recommendations
from Stock, ETF, and Crypto crews, creates an optimal portfolio
allocation within a specified budget (e.g., 1000 CHF monthly),
assesses associated risks, and produces a detailed, evidence-based
investment report.
"""


from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    DirectorySearchTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

load_dotenv()

# Initialize research tools
directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=25, save_file=True, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=25, save_file=True)
search_tool = SerperDevTool(n_results=25, save_file=True, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=25, save_file=True)
youtube_tool = YoutubeVideoSearchTool()

# Tools for financial research and analysis
tools = [
    directory_search_tool,
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    youtube_tool,
]


@CrewBase
class ReportCrew:
    """
    ReportCrew - Expert Financial Integration Team.

    Specialized in analyzing recommendations from various financial
    crews and creating detailed, evidence-based investment plans
    with a fixed budget. The team focuses on creating optimal
    portfolio allocations across asset classes while maintaining
    rigorous risk management protocols.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def financial_integration_analyst(self) -> Agent:
        """
        Create a financial integration analyst.

        Specializes in consolidating recommendations from multiple
        sources and identifying the strongest opportunities.
        """
        return Agent(
            config=self.agents_config["financial_integration_analyst"],
            tools=tools,
            verbose=True,
        )

    @agent
    def portfolio_allocator(self) -> Agent:
        """
        Create a portfolio allocation specialist.

        Develops optimal asset allocation strategies within the 1000 CHF
        monthly budget.
        """
        return Agent(
            config=self.agents_config["portfolio_allocator"], tools=tools, verbose=True
        )

    @agent
    def risk_manager(self) -> Agent:
        """
        Create a risk management specialist.

        Evaluates investment risks and develops appropriate mitigation
        strategies.
        """
        return Agent(
            config=self.agents_config["risk_manager"], tools=tools, verbose=True
        )

    @agent
    def investment_reporter(self) -> Agent:
        """
        Create an investment report specialist.

        Synthesizes analyses into comprehensive, evidence-based
        investment reports.
        """
        return Agent(
            config=self.agents_config["investment_reporter"], tools=tools, verbose=True
        )

    @task
    def integration_analysis_task(self) -> Task:
        """
        Define task to analyze and integrate recommendations.

        Integrates recommendations from all financial crews.
        """
        return Task(
            config=self.tasks_config["integration_analysis_task"],
            agent=self.financial_integration_analyst,
        )

    @task
    def portfolio_allocation_task(self) -> Task:
        """
        Define task to create an optimal portfolio allocation.

        Allocates portfolio within a 1000 CHF budget.
        """
        return Task(
            config=self.tasks_config["portfolio_allocation_task"],
            agent=self.portfolio_allocator,
        )

    @task
    def risk_assessment_task(self) -> Task:
        """
        Define task to assess risks in the proposed portfolio.

        Assesses risks in the proposed portfolio allocation.
        """
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            agent=self.risk_manager,
        )

    @task
    def final_report_task(self) -> Task:
        """
        Define task to create a comprehensive investment report.

        Details recommendations for investment.
        """
        return Task(
            config=self.tasks_config["final_report_task"],
            agent=self.investment_reporter,

        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized financial integration crew.

        This crew analyzes recommendations from Stock, ETF, and Crypto
        Crews, creates an optimal portfolio allocation within a 1000 CHF
        monthly budget, assesses investment risks, and produces a
        comprehensive investment report with actionable recommendations
        backed by verifiable evidence. Uses a sequential workflow.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm="gpt-4.1-mini",
            verbose=True,
            memory=True,
            cache=True,
            allow_delegation=True,
            allow_termination=True,
            respect_context_window=True,
            max_retries=3,
        )
