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

from finwiz.config.llm.llm_config import get_configured_llm
from finwiz.config.performance.performance_config import get_performance_config_manager
from finwiz.crews.deep_analysis.performance_validation import (
    log_performance_validation,
    validate_performance_targets,
)
from finwiz.crews.deep_analysis.tool_routing import get_tools_for_asset_class
from finwiz.flow_state import DeepAnalysisResult
from finwiz.infrastructure.decorators.task_decorators import async_task
from finwiz.infrastructure.json.crewai_json_patch import apply_json_repair_patch
from finwiz.infrastructure.logging.helpers import CrewLogger
from finwiz.infrastructure.monitoring.performance import get_performance_monitor
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.tools.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)

load_dotenv()

# Apply JSON repair patch for LLM outputs (handles trailing commas, etc.)
apply_json_repair_patch()


def _build_asset_analyst_tools() -> list[Any]:
    """Return an empty tool list — agent runs on prompt + fact_pack only.

    The earlier design gave the agent a ``PerplexitySearchTool`` for "bounded
    fact verification". In practice it added 10-15 s per tool call plus an
    extra agent reasoning iteration to interpret the result, and on the
    2026-04-29 run the slowest holding (DELL) sat in the agent loop for
    24 minutes. Since the ``fact_pack`` stage already runs Perplexity
    deterministically before qualify, and ``analysis/_helpers._build_crew_inputs``
    interpolates the verified facts directly into the prompt, the agent has
    *nothing* it could verify that Python hasn't already verified.

    Removing the tool also lets ``max_iter`` collapse to 1 in practice — with
    no tools to call, the LLM returns text on the first iteration and exits.
    """
    return []


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
        # Token monitoring is enabled at flow level (flows/orchestrator.py)
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

        # Import Pydantic models for Task output_pydantic (use raw classes).
        # The crew emits the *bridging* schema _QualitativeInsightsRaw — it
        # excludes ``fact_pack`` and ``analysis_timestamp`` (Python supplies
        # both), which removes the LLM/Pydantic thrash that exhausted the
        # 600s per-holding budget on 2026-04-28. Promotion to the canonical
        # QualitativeInsights happens in qualify._extract_qualitative.
        from finwiz.analysis.stages.qualify import _QualitativeInsightsRaw
        from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights

        # Store raw Pydantic classes for Task.output_pydantic
        self.QualitativeInsights = QualitativeInsights
        self.QualitativeInsightsRaw = _QualitativeInsightsRaw

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
        # Deep analysis needs high max_tokens regardless of model — full JSON output
        # requires 1500-2000 words across 5 sections. Mini default (1024) is far too low.
        if self.perf_config.should_use_mini_model():
            return get_configured_llm(model_type="mini", max_tokens=40960)
        else:
            return get_configured_llm(model_type="standard", max_tokens=61440)

    @agent
    def asset_analyst(self) -> Agent:
        """Qualitative analyst with bounded fact-verification access.

        Has access to PerplexitySearchTool ONLY — no other tools. Used to verify
        current corporate structure (acquisitions, divestitures, partnerships)
        before mentioning them in the narrative, since the model's training data
        is often outdated for corporate facts. The tasks.yaml prompt caps usage
        to 2-3 calls per holding to keep token cost bounded.

        When PPLX_API_KEY is not set (CI, local dev without Perplexity key),
        the agent falls back to zero-tool mode and the prompt's anti-hallucination
        rules become the only safeguard.
        """
        return Agent(
            config=self.agents_config["asset_analyst"],
            verbose=True,
            reasoning=False,  # Plan tool calls via the prompt, not via reasoning loop (cheaper)
            tools=_build_asset_analyst_tools(),
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
            # Use the bridging schema (no fact_pack, no analysis_timestamp).
            # Python promotes the raw payload back to QualitativeInsights in
            # qualify._extract_qualitative — the LLM never has to satisfy
            # FactPack's freshness model_validator or its 200/1000-char caps.
            output_pydantic=self.QualitativeInsightsRaw,
        )

    @crew
    def crew(self) -> Crew:
        """
        Create a unified deep analysis crew with hybrid Python/AI architecture.

        Uses a SINGLE TASK workflow:
        1. deep_qualitative_analysis_task - AI provides qualitative insights

        ⚡ TOKEN OVERFLOW FIX: Removed generate_enriched_analysis_task
        Python's synthesize_enriched_analysis() handles consolidation, not AI.
        This eliminates task-to-task context propagation that caused 200K-335K token overflow.

        Python metrics are calculated by orchestrator BEFORE crew execution.
        AI agent receives Python metrics as READ-ONLY context.
        """
        # ⚡ SINGLE TASK: Only AI qualitative analysis
        # Python handles synthesis - no need for second AI task
        crew_tasks = [
            self.deep_qualitative_analysis_task(),
            # generate_enriched_analysis_task REMOVED:
            # - Was causing 200K-335K token overflow from context propagation
            # - Python's synthesize_enriched_analysis() does the same work for $0
        ]
        logger.info("🔬 SINGLE-TASK MODE: AI qualitative only, Python handles synthesis")

        return Crew(
            # ⚡ SINGLE AGENT: Only asset_analyst for qualitative analysis
            # investment_reporter was REMOVED - Python handles consolidation
            agents=[self.asset_analyst()],
            tasks=crew_tasks,  # Dynamic task list based on configuration
            process=Process.sequential,
            verbose=True,
            max_iter=2,  # ⚡ With zero tools the agent returns on iteration 1; 2 is defense-in-depth
            respect_context_window=True,
            allow_delegation=False,
            max_rpm=20,
            max_retries=3,  # ⚡ OPTIMIZED: Reduced from 10 to 3 (reduce retry overhead)
            # manager_llm removed: only used for hierarchical process, not sequential
            memory=False,  # ⚡ DISABLED: Prevents token overflow from accumulated memory (968KB+)
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
            # ⚡ MINIMAL-TOOL MODE: Python pre-summarizes the bulk of inputs to keep
            # the prompt under the 262K context window. The asset_analyst agent
            # additionally has PerplexitySearchTool for bounded fact verification
            # (max 2 calls per holding, capped via the tasks.yaml prompt) — used
            # only to validate current corporate facts the model might hallucinate.
            # Tool outputs were previously causing 288K-381K token overflow when
            # unbounded tool sets were attached; the cap above prevents regression.
            logger.info("⚡ MINIMAL-TOOL MODE: Python summarizes inputs; agent has PerplexitySearchTool for bounded fact verification (≤2 calls).")

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
                performance_monitor.record_analysis_result(result.grade, result.composite_score, result.confidence, ticker=ticker)

            # Complete performance tracking (pass ticker for concurrent tracking)
            performance_monitor.complete_ticker_analysis(success=True, ticker=ticker)

            # Check if hybrid approach was used
            ai_summary_enabled = self.perf_config.should_use_ai_summary()

            # Validate performance improvements (Requirements 18.28-18.30 and 18.31-18.36)
            performance_validation = validate_performance_targets(
                ticker=ticker,
                execution_time=total_duration,
                _api_metrics={},
                ai_summary_enabled=ai_summary_enabled,
            )

            # Log performance validation results
            log_performance_validation(performance_validation)

            # Store performance metrics in crew state for potential use
            self.performance_metrics = performance_validation

            self.crew_logger.log_complete(total_duration)
            return result

        except Exception as e:
            # Complete performance tracking with error (pass ticker for concurrent tracking)
            if "performance_monitor" in locals():
                performance_monitor.complete_ticker_analysis(success=False, error_message=str(e), ticker=ticker)

            self.crew_logger.log_error(e)
            raise
