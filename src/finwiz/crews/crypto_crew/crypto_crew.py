"""
Defines the Crypto Crew, specialized in cryptocurrency research and investment analysis.

This module sets up the agents (Market Analyst, Technical Analyst, Risk Assessor,
Investment Strategist, Research Director) and their corresponding tasks to
identify potential "unicorn" cryptocurrency projects and generate comprehensive
investment recommendations.
"""


# Standard library imports

# Third-party imports
from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    YoutubeVideoSearchTool,
)

from dotenv import load_dotenv
from finwiz.tools.web_tools import (
    get_search_tools,
    get_news_tools,
    get_scrape_tools,
    get_youtube_tools,
)

from finwiz.tools.coinmarketcap_tool import get_coinmarketcap_tools
from finwiz.tools.rag_tools import get_rag_tools

# from finwiz.tools.finance_tools import get_data_output_tools
from finwiz.tools.yahoo_finance_tool import (
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)
from finwiz.utils.config_loader import load_config_with_guidelines, load_yaml_config


load_dotenv()

# directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=10, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=10, save_file=False)
search_tool = SerperDevTool(n_results=10, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=10, save_file=False)
# Get yahoo tools
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
yahoo_news_tool = YahooFinanceNewsTool()
youtube_tool = YoutubeVideoSearchTool()
# Get JSON output tools
# json_tools = get_data_output_tools()

# Get CoinMarketCap tools
coinmarketcap_tools = get_coinmarketcap_tools()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="crypto")

# Tools for crypto research and analysis
tools = [
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    yahoo_ticker_tool,
    yahoo_history_tool,
    yahoo_news_tool,
    youtube_tool,
    # *json_tools,  # Add JSON output tools
    *coinmarketcap_tools,  # Add CoinMarketCap tools
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
]


@CrewBase
class CryptoCrew:
    """
    CryptoCrew - An expert team for cryptocurrency research.

    This crew specializes in investment analysis and is designed to
    identify potential unicorn cryptocurrency projects, providing
    comprehensive investment recommendations.
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
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            verbose=True,
            tools=tools,
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"], verbose=True, tools=tools
        )

    @task
    def market_technical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_technical_analysis_task"], verbose=True
        )

    @task
    def crypto_screening_task(self) -> Task:
        return Task(config=self.tasks_config["crypto_screening_task"], verbose=True)

    @task
    def crypto_technical_detail_task(self) -> Task:
        return Task(
            config=self.tasks_config["crypto_technical_detail_task"], verbose=True
        )

    @task
    def investment_risk_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["investment_risk_strategy_task"], verbose=True
        )

    @crew
    def crew(self) -> Crew:
        """
        Create the CryptoCrew for cryptocurrency research.

        This crew uses a sequential process to analyze potential unicorn
        projects and offer investment analysis, with validation steps to ensure
        high-quality, consistent output formats for both HTML and JSON data.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,  # Use our manually sequenced tasks
            process=Process.sequential,
            verbose=True,
            tools=tools,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
        )
