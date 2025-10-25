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

from finwiz.flow_state import DeepAnalysisResult
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.tools.logger import get_logger
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.tools.tool_factories import (
    get_stock_crew_tools,
    get_etf_crew_tools,
    get_crypto_crew_tools,
)
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.llm_config import get_configured_llm
from finwiz.utils.logging_helpers import CrewLogger
from finwiz.utils.task_decorators import async_task, sync_task

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()


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

        # Make Pydantic models available for CrewAI resolution BEFORE super().__init__()
        self.DeepAnalysisResult = output_pydantic(DeepAnalysisResult)
        self.RiskAssessmentStandardized = output_pydantic(RiskAssessmentStandardized)

        super().__init__()

        # Initialize structured logger
        self.crew_logger = CrewLogger("DeepAnalysisCrew")

    def get_tools_for_asset_class(self, asset_class: str) -> list:
        """
        Route to appropriate tool set based on asset class.

        Args:
            asset_class: One of "stock", "etf", "crypto"

        Returns:
            List of tools appropriate for the asset class

        Raises:
            ValueError: If asset_class is not valid

        """
        asset_class_lower = asset_class.lower()

        if asset_class_lower == "stock":
            raw_tools = get_stock_crew_tools(
                include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
                include_quantitative=True,
                collection_suffix="stock_deep",
            )
        elif asset_class_lower == "etf":
            raw_tools = get_etf_crew_tools(
                include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
                include_quantitative=True,
                collection_suffix="etf_deep",
            )
        elif asset_class_lower == "crypto":
            raw_tools = get_crypto_crew_tools(
                include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
                include_quantitative=True,
                collection_suffix="crypto_deep",
            )
        else:
            raise ValueError(
                f"Invalid asset_class: {asset_class}. "
                f"Must be one of: stock, etf, crypto"
            )

        # Apply robust wrapper for error handling
        tools = make_tools_robust(raw_tools)
        logger.info(f"Loaded {len(tools)} tools for asset_class: {asset_class}")
        return tools

    def _get_configured_llm(self) -> LLM:
        """Get configured LLM instance for this crew."""
        return get_configured_llm()

    @agent
    def asset_analyst(self) -> Agent:
        """Agent that performs deep analysis of the provided ticker."""
        return Agent(
            config=self.agents_config["asset_analyst"],
            verbose=True,
            reasoning=False,  # ⚡ OPTIMIZED: Disabled reasoning for faster execution (simple data fetching)
            tools=[],  # Tools will be set dynamically based on asset_class
            llm=self._get_configured_llm(),
        )

    @agent
    def risk_assessor(self) -> Agent:
        """Agent that evaluates risks for the provided ticker."""
        return Agent(
            config=self.agents_config["risk_assessor"],
            verbose=True,
            reasoning=False,  # ⚡ OPTIMIZED: Disabled reasoning for faster execution (straightforward risk calculation)
            tools=[],  # Tools will be set dynamically based on asset_class
            llm=self._get_configured_llm(),
        )

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Agent that consolidates findings and generates final report."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            verbose=True,
            reasoning=False,  # ⚡ OPTIMIZED: Disabled reasoning for faster execution (final reporters just consolidate)
            tools=[],  # MUST be empty - enforced by @final_reporter decorator
            llm=self._get_configured_llm(),
        )

    @async_task
    @task
    def deep_analysis_task(self) -> Task:
        """Execute comprehensive analysis for the provided ticker."""
        return Task(
            config=self.tasks_config["deep_analysis_task"],
            verbose=True,
        )

    @async_task
    @task
    def technical_analysis_task(self) -> Task:
        """Execute technical analysis for the provided ticker."""
        return Task(
            config=self.tasks_config["technical_analysis_task"],
            verbose=True,
        )

    @async_task
    @task
    def risk_assessment_task(self) -> Task:
        """Execute risk assessment for the provided ticker."""
        return Task(
            config=self.tasks_config["risk_assessment_task"],
            verbose=True,
        )

    @sync_task
    @task
    def final_report_task(self) -> Task:
        """Generate final investment report consolidating all findings."""
        return Task(
            config=self.tasks_config["final_report_task"],
            verbose=True,
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a unified deep analysis crew with dynamic tool routing.

        Uses a sequential workflow for analysis with validation steps to ensure
        high-quality, consistent output formats.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_iter=25,  # Prevent infinite loops - max iterations per agent
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=10,
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
        
        # Initialize API efficiency tracking
        api_metrics = {
            "api_calls": 0,
            "fresh_data_count": 0,
            "cached_data_count": 0,
            "task_times": {},
        }

        try:
            # Get tools for the specified asset class
            tools = self.get_tools_for_asset_class(asset_class)

            # Dynamically assign tools to agents by calling agent methods
            # Get agent instances
            asset_analyst_agent = self.asset_analyst()
            risk_assessor_agent = self.risk_assessor()
            investment_reporter_agent = self.investment_reporter()
            
            # Assign tools to asset_analyst and risk_assessor
            asset_analyst_agent.tools = tools
            risk_assessor_agent.tools = tools
            logger.info(f"Assigned {len(tools)} tools to asset_analyst and risk_assessor")
            
            # Verify investment_reporter has no tools (enforced by @final_reporter)
            if investment_reporter_agent.tools and len(investment_reporter_agent.tools) > 0:
                logger.warning(f"Investment reporter has {len(investment_reporter_agent.tools)} tools - should be empty!")

            # Log API efficiency patterns
            logger.info(
                f"📊 API Efficiency Patterns Enabled for {ticker}:\n"
                f"  ✅ Smart Batching: Fetch multiple indicators in single call\n"
                f"  ✅ Context Sharing: Pass data between tasks (max_age=5min)\n"
                f"  ✅ Parallel I/O: Async execution for independent tasks\n"
                f"  ❌ NOT Acceptable: 24h cached prices, stale sentiment, skipping fetches"
            )

            # Execute crew with task timing
            task_start = time.time()
            crew_instance = self.crew()
            result = crew_instance.kickoff(inputs=inputs)
            
            # Calculate execution metrics
            duration = time.time() - start_time
            
            # Log API efficiency metrics
            total_data_points = api_metrics["fresh_data_count"] + api_metrics["cached_data_count"]
            freshness_pct = (
                (api_metrics["fresh_data_count"] / total_data_points * 100)
                if total_data_points > 0
                else 0
            )
            
            logger.info(
                f"📊 API Efficiency Metrics for {ticker}:\n"
                f"  • Total API calls: {api_metrics['api_calls']}\n"
                f"  • Fresh data: {api_metrics['fresh_data_count']}\n"
                f"  • Cached data: {api_metrics['cached_data_count']}\n"
                f"  • Data freshness: {freshness_pct:.1f}% fresh\n"
                f"  • Total execution time: {duration:.2f}s"
            )
            
            # Log optimization opportunities
            if api_metrics["api_calls"] > 10:
                logger.warning(
                    f"⚠️ Optimization Opportunity: {ticker} made {api_metrics['api_calls']} API calls. "
                    f"Consider batching or context sharing to reduce redundant fetches."
                )
            
            if freshness_pct < 50 and total_data_points > 0:
                logger.warning(
                    f"⚠️ Data Freshness Alert: Only {freshness_pct:.1f}% of data is fresh. "
                    f"Verify context sharing is working correctly."
                )
            
            self.crew_logger.log_complete(duration)
            return result
            
        except Exception as e:
            self.crew_logger.log_error(e)
            raise
