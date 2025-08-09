"""
Defines the Crypto Crew for cryptocurrency research.

This module initializes and configures the crypto analysis crew, including agents,
_tasks, and tools.
"""

from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    DirectoryReadTool,
    FileReadTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    YoutubeVideoSearchTool,
)

from finwiz.tools.coinmarketcap_tool import get_coinmarketcap_tools
from finwiz.tools.finance_tools import get_crypto_research_tools

# Get the absolute path of the current script
current_script_path = Path(__file__).resolve()
crew_dir = current_script_path.parent

# Initialize tools
search_tool = SerperDevTool()
scrape_tool = FirecrawlScrapeWebsiteTool()
firecrawl_search = FirecrawlSearchTool()
youtube_tool = YoutubeVideoSearchTool()
crypto_tools = get_crypto_research_tools()
coinmarketcap_tools = get_coinmarketcap_tools()

# Define a shared list of research tools for agents (includes validator via crypto_tools)
research_tools = [
    search_tool,
    scrape_tool,
    firecrawl_search,
    youtube_tool,
    *crypto_tools,
    # Contract-aware reading of outputs and schemas
    DirectoryReadTool(directory=("output/crypto")),
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/CryptoThesis.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/crypto_thesis.example.json")),
]


@CrewBase
class CryptoCrew:
    """Crypto crew for cryptocurrency analysis."""

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_analyst"],
            tools=research_tools,
            reasoning=True,
            verbose=True,
        )

    @agent
    def technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_analyst"],
            tools=[*crypto_tools],
            reasoning=True,
            verbose=True,
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=research_tools,
            verbose=True,
            reasoning=True,
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            tools=[*crypto_tools, *coinmarketcap_tools],
            verbose=True,
        )

    @agent
    def research_director(self) -> Agent:
        return Agent(config=self.agents_config["research_director"], tools=[], verbose=True)

    @task
    def market_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["market_analysis_task"], async_execution=True)

    @task
    def technical_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["technical_analysis_task"], async_execution=True)

    @task
    def risk_assessment_task(self) -> Task:
        return Task(config=self.tasks_config["risk_assessment_task"], async_execution=True)

    @task
    def investment_strategy_task(self) -> Task:
        return Task(config=self.tasks_config["investment_strategy_task"], async_execution=True)

    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the crypto analysis crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
