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
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

# Removed incompatible LangChain tool

load_dotenv()

# Initialize research tools
news_tool = SerperDevTool(
    n_results=25, save_file=True, search_type="news", country="fr"
)
search_tool = SerperDevTool(
    n_results=25, save_file=True, search_type="search", country="fr"
)
search_tool2 = FirecrawlSearchTool(limit=25, country="fr", save_file=True)
scrape_tool = FirecrawlScrapeWebsiteTool(limit=25, country="fr", save_file=True)

# search_tool3 = DuckDuckGoSearchRun(max_results=25, country="fr", save_file=True) - removed incompatible tool
youtube_tool = YoutubeVideoSearchTool()
directory_search_tool = DirectorySearchTool(directory="./search_results")

# Tools for stock research and analysis
tools = [
    directory_search_tool,
    search_tool2,
    search_tool,
    news_tool,
    scrape_tool,
    youtube_tool,
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
    def market_analyst(self) -> Agent:
        """
        Create a Market Analyst agent.

        Analyzes overall market trends, sector performance, and economic
        indicators relevant to stock investments.
        """
        return Agent(
            config=self.agents_config["market_analyst"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def technical_analyst(self) -> Agent:
        """
        Create a Fundamental Analyst agent.

        Focuses on evaluating specific companies, their financial health,
        stock performance, and valuation.
        """
        return Agent(
            config=self.agents_config["technical_analyst"],  # type: ignore[index]
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def risk_assessor(self) -> Agent:
        """
        Create a Risk Assessor agent.

        Evaluates risks associated with potential stock investments,
        considering market, company-specific, and economic risks.
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

        Develops stock investment strategies, including asset allocation
        and portfolio construction, based on research findings.
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

        Oversees the stock research process, ensures quality of analysis,
        and synthesizes final investment recommendations.
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

        Researches stock market trends, identifies promising sectors,
        and selects potential companies for deeper analysis.
        """
        return Task(
            config=self.tasks_config["market_analysis_task"],  # type: ignore[index]
        )

    @task
    def technical_evaluation_task(self) -> Task:
        """
        Define the task for the Fundamental Analyst.

        Conducts detailed evaluations of selected stocks, including
        financial statement analysis, valuation, and growth prospects.
        """
        return Task(
            config=self.tasks_config["technical_evaluation_task"],  # type: ignore[index]
        )

    @task
    def risk_assessment_task(self) -> Task:
        """
        Define the task for the Risk Assessor.

        Analyzes risk profiles of chosen stocks and develops risk
        mitigation strategies.
        """
        return Task(
            config=self.tasks_config["risk_assessment_task"],  # type: ignore[index]
        )

    @task
    def investment_strategy_task(self) -> Task:
        """
        Define the task for the Investment Strategist.

        Formulates a comprehensive stock investment strategy based on all
        gathered insights.
        """
        return Task(
            config=self.tasks_config["investment_strategy_task"],  # type: ignore[index]
        )

    @task
    def research_synthesis_task(self) -> Task:
        """
        Define the task for the Research Director.

        Compiles all stock research findings into a detailed and
        actionable investment thesis report.
        """
        return Task(
            config=self.tasks_config["research_synthesis_task"],  # type: ignore[index]
            output_file="stock_unicorn_investment_thesis.html",
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
            process=Process.hierarchical,
            manager_llm="gpt-4.1-mini",
            verbose=True,
            memory=True,
            allow_delegation=True,
            allow_termination=True,
            cache=True,
            respect_context_window=True,
            max_retries=3,
        )
