"""
Defines the Crypto Crew for cryptocurrency research.

This module initializes and configures the crypto analysis crew, including agents,
_tasks, and tools.
"""

from pathlib import Path

from crewai import Agent, Crew, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FirecrawlScrapeWebsiteTool, FirecrawlSearchTool, SerperDevTool, YoutubeVideoSearchTool

from finwiz.tools.coinmarketcap_tool import get_coinmarketcap_tools
from finwiz.tools.finance_tools import get_crypto_research_tools
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.utils.config_loader import load_yaml_config

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
rag_tools = get_rag_tools(collection_suffix="crypto")


@CrewBase
class CryptoCrew:
    """Crypto crew for cryptocurrency analysis."""

    @agent
    def technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_analyst"],
            tools=[*crypto_tools, *rag_tools],
            verbose=True,
        )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=[search_tool, scrape_tool, *rag_tools],
            verbose=True,
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            tools=[*crypto_tools, *coinmarketcap_tools, *rag_tools],
            verbose=True,
        )

    @agent
    def research_director(self) -> Agent:
        return Agent(
            config=self.agents_config["research_director"], 
            tools=[*rag_tools],
            verbose=True
        )

    @task
    def technical_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["technical_analysis_task"],
        )

    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            context=[self.technical_analysis_task()],
        )

    @task
    def investment_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["investment_strategy_task"],
            context=[self.technical_analysis_task(), self.risk_assessment_task()],
        )

    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
            context=[
                self.technical_analysis_task(),
                self.risk_assessment_task(),
                self.investment_strategy_task(),
            ],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the crypto analysis crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )

