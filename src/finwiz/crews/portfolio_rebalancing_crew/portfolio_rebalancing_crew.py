"""
Define the Portfolio Rebalancing Crew for portfolio optimization and rebalancing analysis.

This module configures agents (Portfolio Analyst, Rebalancing Strategist, Risk Manager)
and their tasks to analyze current portfolio composition, generate optimal rebalancing
recommendations, and validate risk constraints.
"""

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import DirectoryReadTool, FileReadTool
from dotenv import load_dotenv

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.tools.enhanced_sec_tool import StandardizedRiskScoringTool
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_price_service import PortfolioPriceService
from finwiz.tools.portfolio_rebalancing_tool import get_portfolio_rebalancing_tool
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.rag_tools import get_rag_tools
from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Initialize portfolio rebalancing tools
yahoo_ticker_tool = YahooFinanceTickerInfoTool()
yahoo_history_tool = YahooFinanceHistoryTool()
portfolio_price_service = PortfolioPriceService()
portfolio_rebalancing_tool = get_portfolio_rebalancing_tool()
ticker_validation_tool = TickerExistenceValidationTool()
standardized_risk_tool = StandardizedRiskScoringTool()

# Get quantitative analysis tool for portfolio optimization
quantitative_tool = get_quantitative_analysis_tool()

# Get RAG tools for knowledge retrieval and storage
rag_tools = get_rag_tools(collection_suffix="portfolio_rebalancing")

# Tools for portfolio rebalancing analysis
tools = [
    portfolio_rebalancing_tool,  # Main portfolio rebalancing tool
    quantitative_tool,  # Add quantitative analysis tool for optimization
    ticker_validation_tool,  # Add ticker validation for portfolio holdings
    standardized_risk_tool,  # Add standardized risk scoring for consistency
    *rag_tools,  # Add RAG tools for knowledge retrieval and storage
    yahoo_ticker_tool,  # Price data retrieval
    yahoo_history_tool,  # Historical data for analysis
    # Contract-aware reading of outputs and schemas
    DirectoryReadTool(directory=("output/portfolio")),
    DirectoryReadTool(directory=("docs/schemas")),
    DirectoryReadTool(directory=("docs/schemas/examples")),
    FileReadTool(file_path=("docs/schemas/PortfolioReview.schema.json")),
    FileReadTool(file_path=("docs/schemas/RiskAssessmentStandardized.schema.json")),
    FileReadTool(file_path=("docs/schemas/examples/portfolio_review.example.json")),
]


@CrewBase
class PortfolioRebalancingCrew:
    """
    PortfolioRebalancingCrew - Expert portfolio optimization and rebalancing team.

    Specialized in analyzing current portfolio composition, generating optimal
    rebalancing recommendations, and ensuring risk management compliance.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

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

        # Make Pydantic models available for CrewAI resolution (BEFORE super().__init__())
        self.PortfolioReview = PortfolioReview
        self.RiskAssessmentStandardized = RiskAssessmentStandardized

        super().__init__()

    @agent
    def portfolio_analyst(self) -> Agent:
        """Agent that analyzes current portfolio composition and calculates weightings."""
        return Agent(
            config=self.agents_config["portfolio_analyst"],
            verbose=True,
            reasoning=False,
            tools=tools,
        )

    @agent
    def rebalancing_strategist(self) -> Agent:
        """Agent that generates optimal rebalancing trade recommendations."""
        return Agent(
            config=self.agents_config["rebalancing_strategist"],
            verbose=True,
            tools=tools,
            reasoning=False,
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that validates rebalancing recommendations against risk constraints."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=tools,
            reasoning=False,
        )

    @agent
    def translator(self) -> Agent:
        """Create translator agent that converts English reports to French while preserving layout."""
        return Agent(
            config=self.agents_config["translator"],
            tools=[],  # No tools - only consumes upstream HTML context
            verbose=True,
        )

    @task
    def portfolio_analysis_task(self) -> Task:
        """Analyze current portfolio composition and calculate weightings."""
        return Task(
            config=self.tasks_config["portfolio_analysis_task"],
            verbose=True,
            async_execution=True,
            output_pydantic=PortfolioReview,
        )

    @task
    def rebalancing_optimization_task(self) -> Task:
        """Generate optimal rebalancing trade recommendations."""
        return Task(
            config=self.tasks_config["rebalancing_optimization_task"],
            verbose=True,
            async_execution=True,
        )

    @task
    def risk_validation_task(self) -> Task:
        """Validate rebalancing recommendations against risk constraints."""
        return Task(
            config=self.tasks_config["risk_validation_task"],
            verbose=True,
            output_pydantic=RiskAssessmentStandardized,
        )

    @task
    def translation_task(self) -> Task:
        """Task to translate the English report to French while preserving layout."""
        return Task(
            config=self.tasks_config["translation_task"],
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized portfolio rebalancing crew.

        Uses a sequential workflow for portfolio analysis, optimization, and risk validation
        to ensure high-quality, consistent rebalancing recommendations.
        """
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
