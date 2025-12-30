"""
Define the Deep Analysis Crew for single-ticker analysis.

This module configures agents (Asset Analyst, Risk Assessor, Investment Reporter)
and their tasks to perform comprehensive deep analysis of individual holdings
across all asset classes (stocks, ETFs, cryptocurrencies) through dynamic tool routing.

API EFFICIENCY PATTERNS (Requirement 11):
=====================================

This crew implements smart API usage patterns to minimize redundant calls while
maintaining data accuracy for real-money decisions.

✅ ACCEPTABLE PATTERNS:
----------------------
1. Smart Batching (Tool-Level) - FUTURE ENHANCEMENT:
   - Current: Individual calls per indicator, store in context
   - Future: Fetch multiple indicators in ONE call: indicators=["RSI", "MACD", "BB"]
   - Will reduce 3 API calls to 1 (same freshness, lower cost)
   - Note: TwelveDataIndicatorTool batch support is a future enhancement

2. Context Sharing (Crew-Level):
   - deep_analysis_task fetches price data, stores in context with timestamp
   - technical_analysis_task checks context for fresh data (max_age=5min)
   - Re-fetches if stale: if not is_fresh(timestamp, max_age=5): refetch()
   - Example: context["price_data"] = {"data": prices, "timestamp": datetime.now()}

3. Parallel I/O (Task-Level):
   - async_execution: true for deep_analysis, technical_analysis, risk_assessment
   - Concurrent API calls where possible (respects rate limits)
   - async_execution: false for final_report (CrewAI requirement)

4. Monitoring & Optimization:
   - Log API call counts per ticker
   - Log data freshness percentage (fresh vs cached)
   - Log execution time breakdown by task
   - Identify optimization opportunities

❌ NOT ACCEPTABLE PATTERNS:
--------------------------
1. Using 24-hour cached prices for buy/sell decisions
2. Using stale sentiment data (>15 minutes old) for risk assessment
3. Skipping data fetches to save costs (accuracy > cost)
4. Caching time-sensitive data beyond freshness thresholds

PRIORITY ORDER:
--------------
1. Accuracy First: Real money decisions require current data
2. Smart Efficiency: Minimize redundant calls through intelligent design
3. Cost Optimization: Optimize where possible without compromising accuracy

FRESHNESS THRESHOLDS:
--------------------
- Market prices: 5 minutes maximum
- Technical indicators: 5 minutes maximum
- Sentiment data: 15 minutes maximum
- Company fundamentals: 24 hours maximum
- SEC filings: 7 days maximum (static data)
"""

import time
from typing import Any

from crewai import LLM, Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, output_pydantic, task
from dotenv import load_dotenv

from finwiz.crews.deep_analysis.performance_validation import (
    log_performance_validation,
    validate_performance_targets,
)
from finwiz.crews.deep_analysis.tool_routing import get_tools_for_asset_class
from finwiz.flow_state import DeepAnalysisResult
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.tools.logger import get_logger
from finwiz.utils.crewai_json_patch import apply_json_repair_patch
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.performance_config import get_performance_config_manager
from finwiz.utils.performance_monitor import get_performance_monitor
from finwiz.utils.task_decorators import async_task, sync_task

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Apply JSON repair patch for LLM outputs (handles trailing commas, etc.)
apply_json_repair_patch()


@CrewBase
class DeepAnalysisCrew:
    """
    DeepAnalysisCrew - Unified deep analysis crew for single ticker analysis.

    Handles stocks, ETFs, and cryptocurrencies through dynamic tool routing
    based on the asset_class parameter. Eliminates code duplication and provides
    a single source of truth for deep analysis logic.
    """

    agents: list[BaseAgent]
    tasks: list[Task]

    def __init__(self) -> None:
        """Initialize deep analysis crew with configuration files."""
        # Set configuration paths before calling super().__init__()
        from pathlib import Path

        import yaml

        # Get the directory of this file
        current_dir = Path(__file__).parent

        # Load configuration files
        with open(current_dir / "config" / "agents.yaml") as f:
            self.agents_config = yaml.safe_load(f)

        with open(current_dir / "config" / "tasks.yaml") as f:
            self.tasks_config = yaml.safe_load(f)

        # Import Pydantic models for Task output_pydantic (use raw classes)
        from finwiz.schemas.hybrid_analysis.enriched import EnrichedAnalysis
        from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights

        # Store raw Pydantic classes for Task.output_pydantic
        self.QualitativeInsights = QualitativeInsights
        self.EnrichedAnalysis = EnrichedAnalysis

        # Make Pydantic models available for CrewAI resolution (wrapped versions)
        self.DeepAnalysisResult = output_pydantic(DeepAnalysisResult)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)

        # Initialize structured logger
        self.crew_logger = CrewLogger("DeepAnalysisCrew")

        # Initialize pre-fetched data storage (Requirement 17.29)
        self.prefetched_data: dict[str, dict[str, Any]] | None = None

        # Initialize performance metrics storage (Requirement 18.28-18.30)
        self.performance_metrics: dict[str, Any] | None = None

        # Initialize performance configuration manager
        self.perf_config = get_performance_config_manager()

    def set_prefetched_data(self, prefetched_data: dict[str, dict[str, Any]]) -> None:
        """
        Set pre-fetched data for batch mode execution.

        This method enables batch mode by providing pre-fetched data that tools
        can use instead of making live API calls. This eliminates API latency
        during crew execution.

        Args:
            prefetched_data: Dict mapping ticker to pre-fetched data from BatchDataPreFetcher
                Format: {
                    "AAPL": {
                        "ticker": "AAPL",
                        "yahoo_finance": {...},
                        "alpha_vantage": {...},
                        "fetch_timestamp": "2025-01-25T10:30:00"
                    },
                    ...
                }

        Requirements: 17.30

        Example:
            >>> crew = DeepAnalysisCrew()
            >>> crew.set_prefetched_data(batch_data)
            >>> result = crew.kickoff(inputs={"ticker": "AAPL", "asset_class": "stock"})

        """
        self.prefetched_data = prefetched_data
        logger.info(f"Pre-fetched data set for {len(prefetched_data)} tickers")

    def get_tools_for_asset_class(self, asset_class: str, minimal: bool = False) -> list[Any]:
        """
        Route to appropriate tool set based on asset class and optimization mode.

        Delegates to the extracted tool_routing module.

        Args:
            asset_class: One of "stock", "etf", "crypto"
            minimal: If True, return minimal tool set (for risk assessment only)

        Returns:
            List of tools appropriate for the asset class

        """
        use_minimal_tools = minimal or self.perf_config.should_use_minimal_tools()
        return get_tools_for_asset_class(
            asset_class=asset_class,
            minimal=minimal,
            prefetched_data=self.prefetched_data,
            use_minimal_tools=use_minimal_tools,
        )

    def _get_configured_llm(self) -> LLM:
        """
        Get configured LLM instance for this crew based on optimization mode.

        Uses environment variables:
            - LLM_MODEL_MINI for performance-optimized operations
            - LLM_MODEL_STANDARD for standard operations
        """
        from finwiz.utils.llm_config import get_mini_llm

        # Use mini model for maximum speed and balanced modes
        if self.perf_config.should_use_mini_model():
            return get_mini_llm()
        else:
            return get_configured_llm(model_type="standard")

    @agent
    def asset_analyst(self) -> Agent:
        """
        Agent that formats Python calculation results.

        CRITICAL: NO TOOLS - Python orchestrator calls tools and calculates scores.
        This agent only READS the Python results from input and formats them nicely.
        """
        return Agent(
            config=self.agents_config["asset_analyst"],
            verbose=True,
            reasoning=False,  # No reasoning needed - just format Python results
            tools=[],  # NO TOOLS - Python does all tool calling
            llm=self._get_configured_llm(),
        )

    @agent
    def investment_reporter(self) -> Agent:
        """
        Agent that formats Python calculation results into reports.

        CRITICAL: NO TOOLS - Python orchestrator already calculated all scores.
        This agent only READS the Python results from input and creates formatted reports.
        """
        return Agent(
            config=self.agents_config["investment_reporter"],
            verbose=True,
            reasoning=False,  # No reasoning needed - just format Python results
            tools=[],  # NO TOOLS - Python already did all calculations
            llm=self._get_configured_llm(),
        )

    @async_task
    @task
    def deep_qualitative_analysis_task(self) -> Task:
        """
        AI performs qualitative analysis using Python metrics as READ-ONLY context.

        Python metrics (scores, grades, metrics) are provided as context.
        AI focuses on qualitative insights: business model, competitive analysis,
        chart patterns, risk factors, and investment synthesis.
        """
        return Task(
            config=self.tasks_config["deep_qualitative_analysis_task"],
            verbose=True,
            output_pydantic=self.QualitativeInsights,  # Pydantic model for structured output
        )

    @sync_task
    @task
    def generate_enriched_analysis_task(self) -> Task:
        """
        Final reporter consolidates Python metrics + AI insights.

        This is a FINAL REPORTER task with NO TOOLS.
        Consolidates QuantitativeAnalysis (Python) + QualitativeInsights (AI)
        into EnrichedAnalysis output.
        """
        return Task(
            config=self.tasks_config["generate_enriched_analysis_task"],
            verbose=True,
            output_pydantic=self.EnrichedAnalysis,  # Pydantic model for structured output
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a unified deep analysis crew with hybrid Python/AI architecture.

        Uses a sequential workflow:
        1. deep_qualitative_analysis_task - AI provides qualitative insights
        2. generate_enriched_analysis_task - Consolidates Python metrics + AI insights

        Python metrics are calculated by orchestrator BEFORE crew execution.
        AI agent receives Python metrics as READ-ONLY context.
        """
        # Hybrid architecture: Python metrics + AI qualitative analysis
        crew_tasks = [
            self.deep_qualitative_analysis_task(),
            self.generate_enriched_analysis_task(),
        ]
        logger.info("🔬 HYBRID MODE: Python metrics + AI qualitative analysis")

        from finwiz.utils.llm_config import get_manager_llm

        return Crew(
            agents=self.agents,
            tasks=crew_tasks,  # Dynamic task list based on configuration
            process=Process.sequential,
            verbose=True,
            max_iter=15,  # ⚡ OPTIMIZED: Reduced from 25 to 15 (sufficient for straightforward tasks)
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=3,  # ⚡ OPTIMIZED: Reduced from 10 to 3 (reduce retry overhead)
            manager_llm=get_manager_llm(),  # Use configured LLM to avoid 'stop' parameter errors
        )

    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        """
        Execute the crew with structured logging and dynamic tool assignment.

        Args:
            inputs: Input parameters for crew execution (must include 'asset_class')

        Returns:
            Crew execution result

        Raises:
            ValueError: If asset_class is not provided in inputs

        """
        if inputs is None:
            inputs = {}

        # Validate required inputs
        asset_class = inputs.get("asset_class")
        if not asset_class:
            raise ValueError("asset_class is required in inputs for DeepAnalysisCrew")

        ticker = inputs.get("ticker")
        if not ticker:
            raise ValueError("ticker is required in inputs for DeepAnalysisCrew")

        self.crew_logger.log_start(inputs)
        start_time = time.time()

        # Initialize performance monitoring
        session_id = inputs.get("session_id", "default")
        performance_monitor = get_performance_monitor(session_id)
        performance_monitor.start_ticker_analysis(ticker, asset_class)

        try:
            # ⚡ PYTHON SCORING: Only asset_analyst needs tools for data collection
            # Get full tool set for asset analyst (data collection)
            analyst_tools = self.get_tools_for_asset_class(asset_class, minimal=False)

            # Dynamically assign tools to agents by calling agent methods
            # Get agent instances
            asset_analyst_agent = self.asset_analyst()
            investment_reporter_agent = self.investment_reporter()

            # Assign tools to agents
            asset_analyst_agent.tools = analyst_tools
            # investment_reporter has DeepAnalysisScoringTool (set in agent definition)
            logger.info(
                f"⚡ PYTHON SCORING TOOL: asset_analyst has {len(analyst_tools)} data collection tools. "
                f"investment_reporter has {len(investment_reporter_agent.tools)} Python scoring tool."
            )

            # Log performance targets
            logger.info(
                f"🎯 PERFORMANCE TARGETS for {ticker} (Requirements 18.28-18.30):\n"
                f"  ⏱️  Execution time: 10-30 seconds (vs 5-10 minutes with AI)\n"
                f"  🤖 LLM calls: 0 for calculations (vs 15-25 with AI)\n"
                f"  💰 Cost: $0 for calculations (vs $0.05-0.10 with AI)\n"
                f"  🚀 Speedup: 10-20x faster than AI approach\n"
                f"  💸 Cost reduction: 100% for calculations"
            )

            # Execute crew with performance tracking
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs=inputs)

            # Calculate execution metrics
            total_duration = time.time() - start_time

            # Record performance metrics
            if hasattr(result, "grade") and hasattr(result, "composite_score") and hasattr(result, "confidence"):
                performance_monitor.record_analysis_result(result.grade, result.composite_score, result.confidence)

            # Complete performance tracking
            performance_monitor.complete_ticker_analysis(success=True)

            # Check if hybrid approach was used
            ai_summary_enabled = self.perf_config.should_use_ai_summary()

            # Validate performance improvements (Requirements 18.28-18.30 and 18.31-18.36)
            performance_validation = validate_performance_targets(
                ticker=ticker,
                execution_time=total_duration,
                api_metrics={},
                ai_summary_enabled=ai_summary_enabled,
            )

            # Log performance validation results
            log_performance_validation(performance_validation)

            # Store performance metrics in crew state for potential use
            self.performance_metrics = performance_validation

            self.crew_logger.log_complete(total_duration)
            return result

        except Exception as e:
            # Complete performance tracking with error
            if "performance_monitor" in locals():
                performance_monitor.complete_ticker_analysis(success=False, error_message=str(e))

            self.crew_logger.log_error(e)
            raise
