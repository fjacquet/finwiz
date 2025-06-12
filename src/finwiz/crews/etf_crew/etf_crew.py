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
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

# from finwiz.tools.finance_tools import get_data_output_tools
# from finwiz.tools.html_output_tool import HTMLOutputTool
from finwiz.tools.yahoo_finance_tool import (
    YahooFinanceETFHoldingsTool,
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.utils.config_loader import load_config_with_guidelines, load_yaml_config

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

# Tools for ETF research and analysis
tools = [
    # directory_search_tool,
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    # search_tool3,
    yahoo_etf_tool,
    yahoo_history_tool,
    yahoo_news_tool,
    yahoo_ticker_tool,
    youtube_tool,
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
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

    @agent
    def market_etf_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['market_etf_analyst'],
            verbose=True,
            tools=tools
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_assessor'],
            verbose=True,
            tools=tools
        )
      
    @task
    def etf_market_trends_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_market_trends_task'],
            verbose=True
        )

    @task
    def etf_screening_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_screening_task'],
            verbose=True
        )
           
    @task
    def etf_technical_detail_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_technical_detail_task'],
            verbose=True
        )

    @task
    def etf_risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_risk_assessment_task'],
            verbose=True
        )

    @task
    def etf_investment_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config['etf_investment_strategy_task'],
            verbose=True
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
