"""
Define the Stock Crew for stock market research.

This module configures agents (Market Analyst, Fundamental Analyst,
Risk Assessor, Investment Strategist, Research Director) and their
tasks to identify promising stock investments and provide detailed
recommendations.
"""

from tabnanny import verbose
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    DirectorySearchTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    # TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

from finwiz.tools.finance_tools import get_stock_research_tools
from finwiz.utils.config_loader import load_config_with_guidelines, load_yaml_config
from finwiz.tools.logger import get_logger
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

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="stock")

# Tools for stock research and analysis
tools = [
    *stock_research_tools,  # Add stock research tools
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
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

    @agent
    def market_technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            verbose=True,
            tools=tools,
        )

    @agent
    def investment_risk_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_risk_analyst"],
            verbose=True,
            tools=tools,
        )

    @task
    def market_technical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_technical_analysis_task"], verbose=True, async_execution=True
        )

    @task
    def stock_screening_task(self) -> Task:
        return Task(config=self.tasks_config["stock_screening_task"], verbose=True, async_execution=True)

    @task
    def technical_detail_task(self) -> Task:
        return Task(config=self.tasks_config["technical_detail_task"], verbose=True, async_execution=True)

    @task
    def stock_risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["stock_risk_assessment_task"], verbose=True
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
        )
