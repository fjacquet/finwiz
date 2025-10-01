"""
Define the Stock Crew for stock market research.

This module configures agents (Market Analyst, Fundamental Analyst,
Risk Assessor, Investment Strategist, Research Director) and their
tasks to identify promising stock investments and provide detailed
recommendations.
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
    # TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.stock import MarketSentiment, TenKInsight
from finwiz.tools.finance_tools import get_stock_research_tools
from finwiz.tools.logger import get_logger
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Initialize research tools
news_tool = SerperDevTool(n_results=10, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=10, save_file=False)
search_tool = SerperDevTool(n_results=10, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=10, save_file=False)
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
yahoo_news_tool = YahooFinanceNewsTool()
yahoo_company_info_tool = YahooFinanceCompanyInfoTool()
youtube_tool = YoutubeVideoSearchTool()

# Get various financial tools
# data_output_tools = get_data_output_tools()
stock_research_tools = get_stock_research_tools()

# Get quantitative analysis tool
quantitative_tool = get_quantitative_analysis_tool()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="stock")

# Tools for stock research and analysis
tools = [
    *stock_research_tools,  # Add stock research tools
    quantitative_tool,  # Add quantitative analysis tool
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
    # Contract-aware reading of outputs and schemas
    DirectoryReadTool(directory=("output/stock")),
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/MarketSentiment.schema.json")),
    FileReadTool(file_path=("docs/schemas/TenKInsight.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/market_sentiment.example.json")),
    FileReadTool(file_path=("docs/schemas/examples/tenk_insight.example.json")),
]


@CrewBase
class StockCrew:
    """
    StockCrew - Expert stock market research team.

    Specialized in identifying high-potential stock investments and
    providing detailed, evidence-based investment recommendations.
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

        super().__init__()

        # Make Pydantic models available for CrewAI resolution
        self.MarketSentiment = MarketSentiment
        self.TenKInsight = TenKInsight
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

    @agent
    def market_technical_analyst(self) -> Agent:
        """Agent that performs technical analysis on target stocks."""
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            verbose=True,
            reasoning=True,  # Enable AI reasoning to show decision-making process
            tools=tools,
        )

    @agent
    def investment_risk_analyst(self) -> Agent:
        """Agent that evaluates stock-specific and market risks."""
        return Agent(
            config=self.agents_config["investment_risk_analyst"],
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
    def market_technical_analysis_task(self) -> Task:
        """Execute technical analysis for short-listed tickers."""
        return Task(
            config=self.tasks_config["market_technical_analysis_task"],
            verbose=True,
            async_execution=True,
        )

    @task
    def stock_screening_task(self) -> Task:
        """Screen stocks based on predefined quantitative filters."""
        return Task(
            config=self.tasks_config["stock_screening_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=MarketSentiment,
        )

    @task
    def technical_detail_task(self) -> Task:
        """Deep dive into technical indicators and patterns for candidates."""
        return Task(
            config=self.tasks_config["technical_detail_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=TenKInsight,
        )

    @task
    def stock_risk_assessment_task(self) -> Task:
        """Assess key risks for recommended tickers and mitigation actions."""
        return Task(
            config=self.tasks_config["stock_risk_assessment_task"],
            verbose=True,
            output_pydantic=RiskAssessmentStandardized,
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
        Create a specialized stock market research crew.

        Uses a sequential workflow for analysis with validation steps to ensure
        high-quality, consistent output formats for both HTML and JSON data.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
        )
