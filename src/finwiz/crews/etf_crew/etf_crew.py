"""
Defines the ETF Crew, an expert team for Exchange-Traded Fund (ETF) research.

This module configures agents (Market Analyst, ETF Specialist, Risk Assessor,
Investment Strategist, Research Director) and their tasks to identify
high-potential ETFs and provide detailed investment recommendations.
"""


from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    DirectorySearchTool,
    FirecrawlScrapeWebsiteTool,
    FirecrawlSearchTool,
    SerperDevTool,
    TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

# Removed incompatible LangChain tool


load_dotenv()

# Initialize research tools
directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=25, save_file=True, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=25, save_file=True)
search_tool = SerperDevTool(n_results=25, save_file=True, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=25, save_file=True)
search_tool3 = TavilySearchTool(max_results=25)
youtube_tool = YoutubeVideoSearchTool()

# Tools for ETF research and analysis
tools = [
    directory_search_tool,
    news_tool,
    scrape_tool,
    search_tool,
    search_tool2,
    search_tool3,
    youtube_tool,
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
    def market_analyst(self) -> Agent:
        """
        Create a Market Analyst agent.

        Analyzes broad market conditions and trends relevant to ETF investments.
        """
        return Agent(
            config=self.agents_config["market_analyst"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def etf_specialist(self) -> Agent:
        """
        Create an ETF Specialist agent.

        Focuses on in-depth analysis of specific ETFs, their composition,
        and performance.
        """
        return Agent(
            config=self.agents_config["etf_specialist"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def risk_assessor(self) -> Agent:
        """
        Create a Risk Assessor agent.

        Evaluates the risks associated with potential ETF investments.
        """
        return Agent(
            config=self.agents_config["risk_assessor"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def investment_strategist(self) -> Agent:
        """
        Create an Investment Strategist agent.

        Develops ETF investment strategies based on research findings.
        """
        return Agent(
            config=self.agents_config["investment_strategist"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def research_director(self) -> Agent:
        """
        Create a Research Director agent.

        Oversees the ETF research process and synthesizes final recommendations.
        """
        return Agent(
            config=self.agents_config["research_director"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @task
    def market_analysis_task(self) -> Task:
        """
        Define the task for the Market Analyst.

        Researches market trends and identifies promising ETF categories.
        """
        return Task(
            config=self.tasks_config["market_analysis_task"],  # type: ignore[index]
        )

    @task
    def etf_evaluation_task(self) -> Task:
        """
        Define the task for the ETF Specialist.

        Conducts detailed evaluations of selected ETFs.
        """
        return Task(
            config=self.tasks_config["etf_evaluation_task"],  # type: ignore[index]
        )

    @task
    def risk_assessment_task(self) -> Task:
        """
        Define the task for the Risk Assessor.

        Analyzes the risk profiles of chosen ETFs.
        """
        return Task(
            config=self.tasks_config["risk_assessment_task"],  # type: ignore[index]
        )

    @task
    def investment_strategy_task(self) -> Task:
        """
        Define the task for the Investment Strategist.

        Formulates an ETF investment strategy.
        """
        return Task(
            config=self.tasks_config["investment_strategy_task"],  # type: ignore[index]
        )

    @task
    def research_synthesis_task(self) -> Task:
        """
        Define the task for the Research Director.

        Compiles all ETF research into a comprehensive investment
        recommendation report.
        """
        return Task(
            config=self.tasks_config["research_synthesis_task"],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized ETF trading research crew.

        Uses a sequential workflow for analysis.
        """
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
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
