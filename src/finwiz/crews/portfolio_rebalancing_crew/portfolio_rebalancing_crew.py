"""
Define the Portfolio Rebalancing Crew for portfolio optimization and rebalancing analysis.

This module configures agents (Portfolio Analyst, Rebalancing Strategist, Risk Manager)
and their tasks to analyze current portfolio composition, generate optimal rebalancing
recommendations, and validate risk constraints.
"""

from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_pydantic, task
from crewai_custom_tools import StandardizedRiskScoringTool, TickerExistenceValidationTool, YahooFinanceHistoryTool, YahooFinanceTickerInfoTool
from dotenv import load_dotenv

from finwiz.infrastructure.decorators.agent_validators import final_reporter
from finwiz.infrastructure.decorators.task_decorators import async_task, sync_task
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crew_exports import RebalancingCrewExport
from finwiz.schemas.portfolio_review import Alternative, HoldingDecision, PortfolioReview, PriceTargets
from finwiz.schemas.rebalancing.analysis import PortfolioAnalysis
from finwiz.schemas.rebalancing.enums import RebalancingRecommendation
from finwiz.tools.alternative_finder_tool import AlternativeFinder
from finwiz.tools.analysis.analysis_coordinator import HoldingAnalyzerOrchestrator
from finwiz.tools.file_tools import DirectoryReadTool, FileReadTool
from finwiz.tools.logger import get_logger
from finwiz.tools.portfolio_price_service import PortfolioPriceService
from finwiz.tools.portfolio_rebalancing_tool import get_portfolio_rebalancing_tool
from finwiz.tools.position_sizing_tool import PositionSizingTool
from finwiz.tools.price_target_calculator import PriceTargetCalculator
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool

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

# Initialize new portfolio holdings analysis tools
holding_analyzer_orchestrator = HoldingAnalyzerOrchestrator()
price_target_calculator = PriceTargetCalculator()
alternative_finder = AlternativeFinder()
position_sizing_tool = PositionSizingTool()

# Tools for portfolio rebalancing analysis
tools = [
    portfolio_rebalancing_tool,  # Main portfolio rebalancing tool
    quantitative_tool,  # Add quantitative analysis tool for optimization
    ticker_validation_tool,  # Add ticker validation for portfolio holdings
    standardized_risk_tool,  # Add standardized risk scoring for consistency
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

# Tools for holding analysis (includes orchestrator and calculators)
holding_analysis_tools = [
    *tools,  # Include all base tools
    # Note: The actual tool instances (holding_analyzer_orchestrator, price_target_calculator, etc.)
    # are Python objects, not CrewAI tools. They will be used programmatically in the crew logic.
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
        # Use the @output_pydantic decorator to mark them for CrewAI
        self.PortfolioReview = output_pydantic(PortfolioReview)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)
        self.HoldingDecision = output_pydantic(HoldingDecision)
        self.PriceTargets = output_pydantic(PriceTargets)
        self.Alternative = output_pydantic(Alternative)
        self.PortfolioAnalysis = output_pydantic(PortfolioAnalysis)
        self.RebalancingRecommendation = output_pydantic(RebalancingRecommendation)

        # CrewBase does not support super().__init__() - config loading is sufficient

    def _get_configured_llm(self) -> LLM:
        """
        Get configured LLM instance for this crew.

        Uses LLM_MODEL_STANDARD environment variable.
        """
        from finwiz.config.llm.llm_config import get_configured_llm

        return get_configured_llm(model_type="standard")

    @agent
    def holding_analyzer(self) -> Agent:
        """Agent that coordinates deep analysis for individual holdings."""
        return Agent(
            config=self.agents_config["holding_analyzer"],
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            tools=holding_analysis_tools,
            llm=self._get_configured_llm(),
        )

    @agent
    def price_target_specialist(self) -> Agent:
        """Agent that calculates actionable buy/sell price targets."""
        return Agent(
            config=self.agents_config["price_target_specialist"],
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            tools=holding_analysis_tools,
            llm=self._get_configured_llm(),
        )

    @agent
    def alternative_researcher(self) -> Agent:
        """Agent that finds better alternatives for underperforming holdings."""
        return Agent(
            config=self.agents_config["alternative_researcher"],
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            tools=holding_analysis_tools,
            llm=self._get_configured_llm(),
        )

    @agent
    def portfolio_analyst(self) -> Agent:
        """Agent that analyzes current portfolio composition and calculates weightings."""
        return Agent(
            config=self.agents_config["portfolio_analyst"],
            verbose=True,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            tools=holding_analysis_tools,
            llm=self._get_configured_llm(),
        )

    @agent
    def rebalancing_strategist(self) -> Agent:
        """Agent that generates optimal rebalancing trade recommendations."""
        return Agent(
            config=self.agents_config["rebalancing_strategist"],
            verbose=True,
            tools=holding_analysis_tools,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            llm=self._get_configured_llm(),
        )

    @agent
    def risk_manager(self) -> Agent:
        """Agent that validates rebalancing recommendations against risk constraints."""
        return Agent(
            config=self.agents_config["risk_manager"],
            verbose=True,
            tools=holding_analysis_tools,
            reasoning=True,
            max_reasoning_attempts=3,  # Prevent infinite reasoning loops
            llm=self._get_configured_llm(),
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Consolidate rebalancing findings into RebalancingCrewExport."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty - enforced by @final_reporter decorator
            verbose=True,
            llm=self._get_configured_llm(),
        )

    # @agent
    # def translator(self) -> Agent:
    #     """Create translator agent that converts English reports to French while preserving layout."""
    #     return Agent(
    #         config=self.agents_config["translator"],
    #         tools=[],  # No tools - only consumes upstream HTML context
    #         verbose=True,
    #     )

    @async_task
    @task
    def analyze_holding_task(self) -> Task:
        """Analyze individual holding using appropriate crew."""
        return Task(
            config=self.tasks_config["analyze_holding_task"],
        )

    @async_task
    @task
    def calculate_price_targets_task(self) -> Task:
        """Calculate actionable buy/sell price targets."""
        return Task(
            config=self.tasks_config["calculate_price_targets_task"],
        )

    @async_task
    @task
    def find_alternatives_task(self) -> Task:
        """Find better alternatives for underperforming holdings."""
        return Task(
            config=self.tasks_config["find_alternatives_task"],
        )

    @async_task
    @task
    def portfolio_analysis_task(self) -> Task:
        """Analyze current portfolio composition and calculate weightings."""
        return Task(
            config=self.tasks_config["portfolio_analysis_task"],
        )

    @async_task
    @task
    def rebalancing_optimization_task(self) -> Task:
        """Generate optimal rebalancing trade recommendations."""
        return Task(
            config=self.tasks_config["rebalancing_optimization_task"],
        )

    @sync_task
    @task
    def risk_validation_task(self) -> Task:
        """Validate rebalancing recommendations against risk constraints."""
        return Task(
            config=self.tasks_config["risk_validation_task"],
        )

    @sync_task
    @task
    def generate_export_task(self) -> Task:
        """Generate RebalancingCrewExport JSON from all rebalancing findings."""
        return Task(
            config=self.tasks_config["generate_export_task"],
            output_pydantic=RebalancingCrewExport,
        )

    # @sync_task
    # @task
    # def translation_task(self) -> Task:
    #     """Task to translate the English report to French while preserving layout."""
    #     return Task(
    #         config=self.tasks_config["translation_task"],
    #     )

    @crew
    def crew(self) -> Crew:
        """
        Create a specialized portfolio rebalancing crew.

        Uses a sequential workflow for portfolio analysis, optimization, and risk validation
        to ensure high-quality, consistent rebalancing recommendations.

        Note: Individual holding analysis tasks (analyze_holding_task, calculate_price_targets_task,
        find_alternatives_task) can be executed in parallel using asyncio for improved performance.
        The portfolio_analysis_task depends on these and will wait for all to complete.
        """
        from finwiz.config.llm.llm_config import get_manager_llm

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
            manager_llm=get_manager_llm(),  # Use configured LLM to avoid 'stop' parameter errors
            memory=False,  # ⚡ DISABLED: Prevents token overflow from accumulated memory
        )

    async def analyze_holdings_parallel(
        self,
        holdings: list[dict],
        max_concurrent: int = 10,
    ) -> list[dict]:
        """
        Analyze multiple holdings in parallel using asyncio.

        This method provides parallel processing for individual holding analysis
        to improve performance when analyzing large portfolios.

        Args:
            holdings: List of holding dicts with ticker, asset_class, currency, name
            max_concurrent: Maximum number of concurrent analyses (default 10)

        Returns:
            List of analysis results for each holding

        Example:
            holdings = [
                {"ticker": "AAPL", "asset_class": "stock", "currency": "USD", "name": "Apple Inc."},
                {"ticker": "VUSA.L", "asset_class": "etf", "currency": "USD", "name": "Vanguard S&P 500"},
            ]
            results = await crew.analyze_holdings_parallel(holdings)

        """
        import asyncio

        logger.info(
            "Starting parallel holding analysis",
            extra={
                "total_holdings": len(holdings),
                "max_concurrent": max_concurrent,
            },
        )

        # Process holdings in chunks to respect rate limits
        results = []
        for i in range(0, len(holdings), max_concurrent):
            chunk = holdings[i : i + max_concurrent]

            # Create tasks for this chunk
            tasks = []
            for holding in chunk:
                task = asyncio.create_task(self._analyze_single_holding_async(holding))
                tasks.append(task)

            # Wait for all tasks in chunk to complete
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(chunk_results)

            logger.info(
                "Completed chunk",
                extra={
                    "chunk_start": i,
                    "chunk_size": len(chunk),
                    "completed": len(results),
                    "total": len(holdings),
                },
            )

        # Filter out any BaseException objects from asyncio.gather results
        valid_results: list[dict] = [r for r in results if isinstance(r, dict)]

        logger.info(
            "Completed parallel holding analysis",
            extra={"total_analyzed": len(valid_results)},
        )

        return valid_results

    async def _analyze_single_holding_async(self, holding: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a single holding asynchronously.

        Args:
            holding: Dict with ticker, asset_class, currency, name

        Returns:
            Analysis result dict

        """
        try:
            # Use HoldingAnalyzerOrchestrator
            analysis = holding_analyzer_orchestrator.analyze_holding(
                ticker=holding["ticker"],
                asset_class=holding["asset_class"],
                currency=holding["currency"],
                name=holding.get("name", ""),
            )

            # Calculate price targets if we have analysis
            price_targets = None
            if analysis.composite_score > 0.5:
                price_targets = price_target_calculator.calculate_targets(
                    ticker=holding["ticker"],
                    asset_class=holding["asset_class"],
                    current_price=holding.get("current_price", 100.0),
                    currency=holding["currency"],
                    decision=holding.get("decision", "KEEP"),
                )

            # Find alternatives if grade is below B
            alternatives = []
            if hasattr(analysis, "grade"):
                from finwiz.tools.alternative_finder_tool import HoldingProfile

                # Extract risk score with proper None handling
                risk_score = getattr(analysis, "risk_score", None)
                if risk_score is None:
                    risk_score = 2.5  # Default risk score

                profile = HoldingProfile(
                    ticker=holding["ticker"],
                    name=holding.get("name", holding["ticker"]),
                    asset_class=holding["asset_class"],
                    grade=getattr(analysis, "grade", "C"),
                    composite_score=analysis.composite_score,
                    risk_score=risk_score,
                )
                alternatives = alternative_finder.find_alternatives(profile)

            return {
                "ticker": holding["ticker"],
                "analysis": analysis,
                "price_targets": price_targets,
                "alternatives": alternatives,
                "status": "success",
            }

        except Exception as e:
            logger.error(
                "Error analyzing holding",
                extra={
                    "ticker": holding["ticker"],
                    "error": str(e),
                },
            )
            return {
                "ticker": holding["ticker"],
                "analysis": None,
                "price_targets": None,
                "alternatives": [],
                "status": "error",
                "error": str(e),
            }
