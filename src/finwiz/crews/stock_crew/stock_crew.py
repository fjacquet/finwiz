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
    DirectorySearchTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    # TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

from finwiz.tools.finance_tools import get_data_output_tools
from finwiz.tools.yahoo_finance_tool import (
    YahooFinanceCompanyInfoTool,
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)

# Removed incompatible LangChain tool

load_dotenv()

# Initialize research tools

directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=10, save_file=True, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=10, save_file=True)
search_tool = SerperDevTool(n_results=10, save_file=True, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=10, save_file=True)
# search_tool3 = TavilySearchTool(max_results=25)

yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
yahoo_compinfo_tool = YahooFinanceCompanyInfoTool()
yahoo_news_tool = YahooFinanceNewsTool()
youtube_tool = YoutubeVideoSearchTool()

# Get JSON output tools
json_tools = get_data_output_tools()

# Tools for stock research and analysis
tools = [
    directory_search_tool,
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    # search_tool3,
    yahoo_ticker_tool,
    yahoo_history_tool,
    yahoo_compinfo_tool,
    yahoo_news_tool,
    youtube_tool,
    *json_tools,  # Add JSON output tools
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
        """
        Create a Market & Technical Analyst agent.

        This agent analyzes stock market trends and evaluates technical aspects
        of company financials to identify high-potential investment opportunities.
        """
        return Agent(
            config=self.agents_config["market_technical_analyst"],  # type: ignore[index]
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

        This agent assesses risks and develops investment strategies for stocks,
        balancing risk factors with return potential.
        """
        return Agent(
            config=self.agents_config["investment_risk_analyst"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            memory=True,
            cache=True,
            allow_delegation=False,
            respect_context_window=True,
            max_reasoning_steps=3,
        )

    @agent
    def research_director(self) -> Agent:
        """
        Create a Research Director agent.

        This agent oversees the entire research process and synthesizes all findings
        into comprehensive stock investment recommendations.
        """
        return Agent(
            config=self.agents_config["research_director"],  # type: ignore[index]
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
    def market_technical_analysis_task(self) -> Task:
        """
        Define the market and technical analysis task.

        This task involves researching stock market trends and conducting in-depth
        financial analysis of companies, focusing on identifying promising stocks
        and evaluating their fundamentals, valuation, and growth prospects.
        """
        return Task(
            config=self.tasks_config["market_technical_analysis_task"],  # type: ignore[index]
            async_execution=False,
        )

    @task
    def investment_risk_strategy_task(self) -> Task:
        """
        Define the investment risk and strategy task.

        This task involves evaluating potential risks of the selected stocks
        and developing comprehensive investment strategies, including risk assessment,
        entry points, position sizing, and expected returns.
        """
        return Task(
            config=self.tasks_config["investment_risk_strategy_task"],  # type: ignore[index]
            async_execution=False,
        )

    @task
    def research_synthesis_task(self) -> Task:
        """
        Define the research synthesis task.

        This task involves compiling all analyses and recommendations into a final
        stock investment report with clear, actionable insights.
        """
        return Task(
            config=self.tasks_config["research_synthesis_task"],  # type: ignore[index]
            async_execution=False,
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized stock market research crew.

        Uses a sequential workflow for analysis.
        """
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            max_retries=10,
        )
