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
    DirectorySearchTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    # TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

from finwiz.tools.coinmarketcap_tool import get_coinmarketcap_tools
from finwiz.tools.finance_tools import get_data_output_tools
from finwiz.tools.yahoo_finance_tool import (
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)

# Removed incompatible LangChain tool

load_dotenv()

directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=10, save_file=True, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=10, save_file=True)
search_tool = SerperDevTool(n_results=10, save_file=True, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=10, save_file=True)
# search_tool3 = TavilySearchTool(max_results=25)
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
yahoo_news_tool = YahooFinanceNewsTool()
youtube_tool = YoutubeVideoSearchTool()

# Get JSON output tools
json_tools = get_data_output_tools()

# Get CoinMarketCap tools
coinmarketcap_tools = get_coinmarketcap_tools()

# Tools for crypto research and analysis
tools = [
    directory_search_tool,
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    # search_tool3,
    yahoo_ticker_tool,
    yahoo_history_tool,
    yahoo_news_tool,
    youtube_tool,
    *json_tools,  # Add JSON output tools
    *coinmarketcap_tools,  # Add CoinMarketCap tools
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
        """
        Create a Market & Technical Analyst agent.

        This agent analyzes cryptocurrency market trends and evaluates technical aspects
        of blockchain projects to identify high-potential investment opportunities.
        """
        return Agent(
            config=self.agents_config["market_technical_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            respect_context_window=True,
            allow_delegation=False,
            max_reasoning_steps=3,
        )

    @agent
    def investment_risk_analyst(self) -> Agent:
        """
        Create an Investment & Risk Analyst agent.

        This agent assesses risks and develops investment strategies for cryptocurrency
        projects, balancing risk factors with return potential.
        """
        return Agent(
            config=self.agents_config["investment_risk_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            respect_context_window=True,
            allow_delegation=False,
            max_reasoning_steps=3,
        )

    @agent
    def research_director(self) -> Agent:
        """
        Create a Research Director agent.

        This agent oversees the entire research process and synthesizes all findings
        into comprehensive cryptocurrency investment recommendations.
        """
        return Agent(
            config=self.agents_config["research_director"],
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            respect_context_window=True,
            allow_delegation=False,
            max_reasoning_steps=3,
        )

    @task
    def market_technical_analysis_task(self) -> Task:
        """
        Define the market and technical analysis task.

        This task involves researching cryptocurrency market trends and conducting
        in-depth technical evaluation of projects, focusing on both market potential
        and technical innovation.
        """
        return Task(
            config=self.tasks_config["market_technical_analysis_task"],
            async_execution=False,
        )

    @task
    def investment_risk_strategy_task(self) -> Task:
        """
        Define the investment risk and strategy task.

        This task involves evaluating potential risks of the selected cryptocurrencies
        and developing comprehensive investment strategies, including risk assessment,
        entry points, position sizing, and expected returns.
        """
        return Task(
            config=self.tasks_config["investment_risk_strategy_task"],
            async_execution=False,
        )

    @task
    def research_synthesis_task(self) -> Task:
        """
        Define the research synthesis task.

        This task involves compiling all analyses and recommendations into a final
        cryptocurrency investment report with clear, actionable insights.
        """
        return Task(
            config=self.tasks_config["research_synthesis_task"],
            async_execution=False,
        )

    @crew
    def crew(self) -> Crew:
        """
        Create the CryptoCrew for cryptocurrency research.

        This crew uses a sequential process to analyze potential unicorn
        projects and offer investment analysis.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_retries=10,
        )
