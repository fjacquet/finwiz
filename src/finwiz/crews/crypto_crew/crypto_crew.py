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

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crypto import CryptoThesis
from finwiz.tools.coinmarketcap_tool import get_coinmarketcap_tools
from finwiz.tools.finance_tools import get_crypto_research_tools
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.rag_tools import get_rag_tools

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
quantitative_tool = get_quantitative_analysis_tool()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="crypto")

# Define a shared list of research tools for agents (includes validator via crypto_tools)
research_tools = [
    search_tool,
    scrape_tool,
    firecrawl_search,
    youtube_tool,
    *crypto_tools,
    quantitative_tool,  # Add quantitative analysis tool
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
    # Contract-aware reading of outputs and schemas
    DirectoryReadTool(directory=("output/crypto")),
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/CryptoThesis.schema.json")),
    FileReadTool(file_path=("docs/schemas/RiskAssessmentStandardized.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/crypto_thesis.example.json")),
]


@CrewBase
class CryptoCrew:
    """Crypto crew for cryptocurrency analysis."""

    def __init__(self) -> None:
        """Set configuration paths before calling super().__init__()."""
        from pathlib import Path

        import yaml

        # Get the directory of this file
        current_dir = Path(__file__).parent

        # Load configuration files
        with open(current_dir / "config" / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)

        with open(current_dir / "config" / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        super().__init__()

        # Make Pydantic models available for CrewAI resolution
        self.CryptoThesis = CryptoThesis
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["market_analyst"],
            tools=research_tools,
            reasoning=True,  # Enable AI reasoning for market analysis decisions
            verbose=True,
        )

    @agent
    def technical_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_analyst"],
            tools=[*crypto_tools, quantitative_tool, *rag_tools],
            reasoning=True,  # Enable AI reasoning for technical analysis decisions
            verbose=True,
          )

    @agent
    def risk_assessor(self) -> Agent:
        return Agent(
            config=self.agents_config["risk_assessor"],
            tools=research_tools,
            verbose=True,
            reasoning=True,  # Enable AI reasoning for risk assessment decisions
        )

    @agent
    def investment_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_strategist"],
            tools=[*crypto_tools, *coinmarketcap_tools, quantitative_tool, *rag_tools],
            verbose=True,
            reasoning=True,  # Enable AI reasoning for investment strategy decisions
        )

    @agent
    def research_director(self) -> Agent:
        return Agent(config=self.agents_config["research_director"], tools=[], verbose=True)

    @agent
    def translator(self) -> Agent:
        """Create translator agent that converts English reports to French while preserving layout."""
        return Agent(
            config=self.agents_config["translator"],
            tools=[],  # No tools - only consumes upstream HTML context
            verbose=True,
        )

    @task
    def market_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config["market_analysis_task"],
            async_execution=True,
            output_pydantic=CryptoThesis,
        )

    @task
    def technical_analysis_task(self) -> Task:
        return Task(config=self.tasks_config["technical_analysis_task"], async_execution=True)

    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            async_execution=True,
            output_pydantic=RiskAssessmentStandardized,
        )

    @task
    def investment_strategy_task(self) -> Task:
        return Task(
            config=self.tasks_config["investment_strategy_task"],
            async_execution=True,
            output_pydantic=CryptoThesis,
        )

    @task
    def final_report_task(self) -> Task:
        return Task(
            config=self.tasks_config["final_report_task"],
        )

    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the crypto analysis crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
        )
