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
    TavilySearchTool,
    YoutubeVideoSearchTool,
)
from dotenv import load_dotenv

# Removed incompatible LangChain tool

load_dotenv()

directory_search_tool = DirectorySearchTool(directory="./search_results")
news_tool = SerperDevTool(n_results=25, save_file=True, search_type="news")
scrape_tool = FirecrawlScrapeWebsiteTool(limit=25, save_file=True)
search_tool = SerperDevTool(n_results=25, save_file=True, search_type="search")
search_tool2 = FirecrawlSearchTool(limit=25, save_file=True)
search_tool3 = TavilySearchTool(max_results=25)
youtube_tool = YoutubeVideoSearchTool()

# Tools for cryptocurrency research and analysis
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
    def market_analyst(self) -> Agent:
        """
        Create a Market Analyst agent.

        Responsible for analyzing market trends, sentiment, and news
        related to cryptocurrencies.
        """
        return Agent(
            config=self.agents_config["market_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def technical_analyst(self) -> Agent:
        """
        Create a Technical Analyst agent.

        Focused on evaluating the technical aspects of cryptocurrencies,
        including blockchain technology, tokenomics, and whitepapers.
        """
        return Agent(
            config=self.agents_config["technical_analyst"],
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def risk_assessor(self) -> Agent:
        """
        Create a Risk Assessor agent.

        Dedicated to identifying and evaluating potential risks
        associated with cryptocurrency investments.
        """
        return Agent(
            config=self.agents_config["risk_assessor"],
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def investment_strategist(self) -> Agent:
        """
        Create an Investment Strategist agent.

        Formulates investment strategies based on the analyses from
        other agents.
        """
        return Agent(
            config=self.agents_config["investment_strategist"],
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @agent
    def research_director(self) -> Agent:
        """
        Create a Research Director agent.

        Responsible for overseeing the research process, ensuring quality,
        and synthesizing the final investment thesis.
        """
        return Agent(
            config=self.agents_config["research_director"],
            verbose=True,
            tools=tools,
            reasoning=True,
            max_reasoning_steps=5,
        )

    @task
    def market_analysis_task(self) -> Task:
        """
        Define the task for the Market Analyst.

        Conduct comprehensive market research and identify promising
        cryptocurrency sectors or projects.
        """
        return Task(
            config=self.tasks_config["market_analysis_task"],
        )

    @task
    def technical_evaluation_task(self) -> Task:
        """
        Define the task for the Technical Analyst.

        Perform an in-depth technical review of selected cryptocurrencies.
        """
        return Task(
            config=self.tasks_config["technical_evaluation_task"],
        )

    @task
    def risk_assessment_task(self) -> Task:
        """
        Define the task for the Risk Assessor.

        Evaluate the risks associated with the identified cryptocurrency
        investment opportunities.
        """
        return Task(
            config=self.tasks_config["risk_assessment_task"],
        )

    @task
    def investment_strategy_task(self) -> Task:
        """
        Define the task for the Investment Strategist.

        Develop a detailed investment plan, including allocation and
        potential returns.
        """
        return Task(
            config=self.tasks_config["investment_strategy_task"],
        )

    @task
    def research_synthesis_task(self) -> Task:
        """
        Define the task for the Research Director.

        Compile all findings into a final, actionable investment thesis report.
        """
        return Task(
            config=self.tasks_config["research_synthesis_task"],
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
            process=Process.hierarchical,
            manager_llm="gpt-4.1-mini",
            verbose=True,
            memory=True,
            cache=True,
            respect_context_window=True,
            max_retries=3,
            allow_delegation=True,
            allow_termination=True,
            # Can be changed to Process.hierarchical
            # if a more complex workflow is needed
        )
