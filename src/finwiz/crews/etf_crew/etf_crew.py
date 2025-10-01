"""
Expert team for Exchange-Traded Fund (ETF) research.

This module configures agents (Market Analyst, ETF Specialist, Risk Assessor,
Investment Strategist, Research Director, Quality Control Specialist) and their
tasks to identify high-potential ETFs and provide detailed investment
recommendations. The crew follows a KISS (Keep It Simple, Stupid) approach with
DRY (Don't Repeat Yourself) principles and includes a dedicated Quality Control
agent to ensure consistent output quality. ETF investment analysis crew using
the CrewAI framework.
"""

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
from finwiz.tools.finance_tools import get_etf_research_tools
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.rag_tools import get_rag_tools

# from finwiz.tools.finance_tools import get_data_output_tools
# from finwiz.tools.html_output_tool import HTMLOutputTool
from finwiz.tools.yahoo_finance_etf_holdings_tool import YahooFinanceETFHoldingsTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

# Removed incompatible LangChain tool


load_dotenv()

# Initialize research tools
# directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=10, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=10, save_file=False)
search_tool = SerperDevTool(n_results=10, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=10, save_file=False)
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
yahoo_etf_tool = YahooFinanceETFHoldingsTool()
yahoo_news_tool = YahooFinanceNewsTool()
youtube_tool = YoutubeVideoSearchTool()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="etf")

# Get enhanced ETF research tools
etf_research_tools = get_etf_research_tools()

# Get quantitative analysis tool
quantitative_tool = get_quantitative_analysis_tool()

# Tools for ETF research and analysis
tools = [
    # Basic research tools
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    youtube_tool,
    # Enhanced ETF-specific tools
    *etf_research_tools,
    quantitative_tool,  # Add quantitative analysis tool
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
    # Contract-aware reading of outputs and schemas
    DirectoryReadTool(directory=("output/etf")),
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/ETFFactsheet.schema.json")),
    FileReadTool(file_path=("docs/schemas/ETFTopHolding.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/etf_factsheet.example.json")),
    FileReadTool(file_path=("docs/schemas/RiskAssessmentStandardized.schema.json")),
]


@CrewBase
class EtfCrew:
    """
    EtfCrew - Expert ETF trading research team.

    Specialized in identifying high-potential ETFs and providing
    detailed investment recommendations to maximize returns.
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

        super().__init__()

        # Make Pydantic models available for CrewAI resolution
        self.ETFTopHolding = ETFTopHolding
        self.ETFFactsheet = ETFFactsheet
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

    @agent
    def market_etf_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_etf_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,  # Enable AI reasoning for ETF analysis decisions
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            verbose=True,
            tools=tools,
            reasoning=True,  # Enable AI reasoning for risk assessment decisions
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
    def etf_market_trends_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_market_trends_task"],
            verbose=True,
            reasoning=False,
            async_execution=True,
        )

    @task
    def etf_screening_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_screening_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=ETFTopHolding,
        )

    @task
    def etf_technical_detail_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_technical_detail_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=ETFFactsheet,
        )

    @task
    def etf_risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["etf_risk_assessment_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=RiskAssessmentStandardized,
        )

    @task
    def etf_investment_strategy_task(self) -> Task:
        return Task(config=self.tasks_config["etf_investment_strategy_task"], verbose=True)

    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create a specialized ETF trading research crew with a sequential workflow."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_retries=10,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
        )
