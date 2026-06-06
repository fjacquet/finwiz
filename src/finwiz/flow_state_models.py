"""
Flow State Pydantic Models for FinWiz Application.

Contains state containers for the CrewAI flow execution.
"""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DeepAnalysisResult(BaseModel):
    """Result from deep crew analysis of a portfolio holding."""

    ticker: str = Field(..., description="Stock/ETF/crypto ticker symbol")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")
    crew_name: str = Field(..., description="Name of crew that performed analysis")
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When analysis was performed (ISO format)",
    )
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Composite score (0.0-1.0)")
    grade: str = Field(..., description="Letter grade (A+ to F)")

    # Investment recommendation
    recommendation: str = Field(..., description="Investment recommendation (BUY, HOLD, SELL)")
    rationale: str = Field(..., description="Detailed rationale for the recommendation")
    risk_details: dict[str, float] = Field(default_factory=dict, description="Risk factor breakdown")

    # Individual scores (optional)
    fundamental_score: float | None = Field(None, ge=0.0, le=1.0, description="Fundamental analysis score")
    technical_score: float | None = Field(None, ge=0.0, le=1.0, description="Technical analysis score")
    risk_score: float | None = Field(None, ge=0.0, le=5.0, description="Risk score (0-5 scale)")

    # Score details
    fundamental_details: dict[str, Any] = Field(default_factory=dict, description="Fundamental analysis breakdown")
    technical_details: dict[str, Any] = Field(default_factory=dict, description="Technical analysis breakdown")

    # Data quality and freshness
    data_freshness_hours: float = Field(..., ge=0.0, description="Age of market data in hours")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence level in analysis")
    warnings: list[str] = Field(default_factory=list, description="List of analysis warnings")
    data_quality: dict[str, Any] | None = Field(None, description="Data quality metrics tracking")

    # Data lineage
    lineage: dict[str, Any] | None = Field(None, description="Complete data lineage from sources")

    # Trust-spine confidence marker: 'low' when upstream qualify stage used a Python fallback (DEGRADED).
    confidence: Literal["high", "low"] = Field(default="high", description="Pipeline confidence: 'low' when qualify stage degraded to Python fallback")

    # Cache metadata
    cached: bool = Field(default=False, description="Whether result came from cache")

    # v5.2 fact pack — verified corporate facts injected into the qualify prompt.
    # Carried here so the merge layer can populate HoldingDecision.fact_pack for
    # the report renderer's provenance footer. Avoid circular import via late binding.
    fact_pack: Any = Field(default=None, description="FactPack from v5.2 fact_pack stage (Any to avoid circular import)")

    # ADR-011: tactical price targets surfaced to the merge / renderer.
    # Optional Any to avoid a circular import with hybrid_analysis.PriceTargets.
    price_targets: Any = Field(default=None, description="Tactical PriceTargets (ADR-011); Any to avoid circular import")

    # Sentiment scoring (Phase 14)
    sentiment_score: float | None = Field(None, ge=-1.0, le=1.0, description="Sentiment score from news analysis (-1 bearish to +1 bullish). None = no news data.")
    sentiment_confidence: float | None = Field(None, ge=0.0, le=1.0, description="Confidence in sentiment score. None = no news data.")

    # Macro scoring (Phase 15)
    macro_score: float | None = Field(None, ge=-1.0, le=1.0, description="Macro context score (-1 headwinds to +1 tailwinds). None = no macro data.")
    macro_regime: str | None = Field(None, description="Detected market regime (normal, elevated_volatility, high_volatility, recession_risk). None = no macro data.")

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True,
        "ser_json_timedelta": "iso8601",
        "ser_json_bytes": "base64",
    }

    @property
    def quality_level(self) -> str:
        """Get quality level from data_quality metrics."""
        if self.data_quality and "quality_level" in self.data_quality:
            return str(self.data_quality["quality_level"])
        return "unknown"

    @property
    def completeness_score(self) -> float:
        """Get completeness score from data_quality metrics."""
        if self.data_quality and "completeness_score" in self.data_quality:
            return float(self.data_quality["completeness_score"])
        return 0.5


class FinwizState(BaseModel):
    """Comprehensive structured state for the FinWiz analysis flow."""

    # Required for CrewAI Flow persistence
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique flow state ID for persistence",
    )

    # Session metadata
    current_day: int = Field(default_factory=lambda: datetime.now().day)
    current_month: int = Field(default_factory=lambda: datetime.now().month)
    current_year: int = Field(default_factory=lambda: datetime.now().year)
    current_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    full_date: str = Field(default_factory=lambda: datetime.now().strftime("%B %d, %Y"))
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report_language: str = Field(default="fr", description="Report language")

    # Session information
    has_existing_session: bool = Field(default=False)
    session_id: str = Field(default="")
    analysis_count: int = Field(default=0)

    # Phase 4 discovery toggle — populated from CLI flag or env var at startup.
    discovery_enabled: bool = Field(
        default=False,
        description="Whether Phase 4 (A+ investment discovery) runs this session",
    )

    # Core analysis results
    stock_result: str = Field(default="")
    etf_result: str = Field(default="")
    crypto_result: str = Field(default="")

    # Stock analysis status
    stock_analysis_success: bool = Field(default=False)
    stock_analysis_error: str | None = None
    stock_analysis_disabled: bool = Field(default=False)
    stock_analysis_fallback: bool = Field(default=False)
    stock_analysis_result: dict[str, Any] | None = None

    # ETF analysis status
    etf_analysis_success: bool = Field(default=False)
    etf_analysis_error: str | None = None
    etf_analysis_disabled: bool = Field(default=False)
    etf_analysis_fallback: bool = Field(default=False)
    etf_analysis_result: dict[str, Any] | None = None

    # Crypto analysis status
    crypto_analysis_success: bool = Field(default=False)
    crypto_analysis_error: str | None = None
    crypto_analysis_disabled: bool = Field(default=False)
    crypto_analysis_fallback: bool = Field(default=False)
    crypto_analysis_result: dict[str, Any] | None = None

    # Data integration and validation
    data_availability_report: dict[str, Any] | None = None
    stale_data_warnings: list[str] = Field(default_factory=list)
    refresh_recommendations: list[str] = Field(default_factory=list)
    data_integration_error: str | None = None

    # Portfolio review data
    portfolio_review: dict[str, Any] | None = None
    portfolio_review_json: str | None = None
    portfolio_review_success: bool = Field(default=False)
    portfolio_review_error: str | None = None
    core_analysis_status: dict[str, Any] | None = None

    # Portfolio rebalancing data
    portfolio_rebalancing_available: bool = Field(default=False)
    portfolio_rebalancing_result: dict[str, Any] | None = None
    rebalancing_success: bool = Field(default=False)
    rebalancing_results: dict[str, Any] | None = None
    rebalancing_error: str | None = None
    portfolio_rebalancing_error: str | None = None
    portfolio_allocation_updates: dict[str, Any] | None = None

    # Investment discovery data
    investment_discovery_available: bool = Field(default=False)
    investment_discovery_result: dict[str, Any] | None = None
    investment_discovery_structured: dict[str, Any] | None = None
    investment_discovery_error: str | None = None

    # Consolidated data and integration
    consolidated_data: dict[str, Any] | None = None
    core_analysis_summary: dict[str, Any] | None = None
    integrated_data_available: bool = Field(default=False)
    integrated_data_error: str | None = None
    market_sentiment: dict[str, Any] | None = None
    ticker_validation: dict[str, Any] | None = None
    aplus_opportunities: dict[str, Any] | None = None
    aplus_availability_status: dict[str, Any] | None = None
    market_context: dict[str, Any] | None = None

    # System health and error tracking
    error_summaries: list[dict[str, Any]] = Field(default_factory=list)
    system_health: dict[str, Any] | None = None
    system_status_for_report: dict[str, Any] | None = None

    # Reporter input validation
    reporter_input: dict[str, Any] | None = None
    report_generation_error: str | None = None
    report_generation_success: bool = Field(default=False)
    report_path: str | None = None
    report_generation_method: str | None = None
    generated_html_reports: dict[str, Any] | None = None

    # Degraded functionality tracking
    stock_degraded_functionality: list[str] = Field(default_factory=list)
    etf_degraded_functionality: list[str] = Field(default_factory=list)
    crypto_degraded_functionality: list[str] = Field(default_factory=list)
    stock_fallback_strategy: str | None = None
    etf_fallback_strategy: str | None = None
    crypto_fallback_strategy: str | None = None

    # Deep portfolio analysis results
    deep_analysis_results: dict[str, DeepAnalysisResult] = Field(default_factory=dict)
    deep_analysis_success: bool = Field(default=False)
    deep_analysis_count: int = Field(default=0)
    deep_analysis_error: str | None = None
    # Coverage tuple (analyzed, total) populated by DeepAnalysisOrchestrator so
    # the reporting layer can render a truthful "X/Y holdings analyzed" banner
    # and mark unanalyzed holdings as "Analyse en attente".
    deep_analysis_coverage: tuple[int, int] | None = None

    # Portfolio-Aware Opportunity Cascade
    # Gap profile built after deep analysis (Phase 3.6); consumed by discovery
    # and alternatives ranking. Stored as a dict (PortfolioGapProfile.model_dump()).
    portfolio_gap_profile: dict[str, Any] = Field(default_factory=dict)
    # Ranked top-N gap-fill opportunities, emitted before enrichment (fast shortlist).
    opportunity_shortlist: list[dict[str, Any]] = Field(default_factory=list)
    shortlist_ready: bool = Field(default=False)

    # Alternative matching results
    portfolio_alternatives: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    alternatives_success: bool = Field(default=False)
    alternatives_count: int = Field(default=0)
    alternatives_error: str | None = None

    # Data availability tracking
    data_availability_summary: dict[str, Any] | None = None
    data_availability_summary_formatted: str | None = None

    # Report aggregation fields
    crew_export_paths: dict[str, list[str]] = Field(default_factory=dict)
    crew_html_paths: dict[str, list[str]] = Field(default_factory=dict)
    consolidated_json_path: str | None = None
    final_report_path: str | None = None
    crew_execution_status: dict[str, str] = Field(default_factory=dict)
    crew_execution_errors: dict[str, str] = Field(default_factory=dict)

    # Resilience tracking fields
    total_holdings: int = Field(default=0)
    holdings_processed: int = Field(default=0)
    holdings_remaining: int = Field(default=0)
    current_ticker: str = Field(default="")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0)

    # Timing fields
    flow_start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_checkpoint_time: str | None = None
    estimated_time_remaining: float = Field(default=0.0, ge=0.0)

    # Error tracking
    errors: list[str] = Field(default_factory=list)
    failed_holdings: list[str] = Field(default_factory=list)
    retry_counts: dict[str, int] = Field(default_factory=dict)
    timeout_holdings: list[str] = Field(default_factory=list)
    retryable_errors: list[Any] = Field(default_factory=list)
    non_retryable_errors: list[Any] = Field(default_factory=list)

    # Resume metadata
    resume_from_checkpoint: bool = Field(default=False)
    checkpoint_uuid: str | None = None

    # Batch pre-fetch fields
    batch_prefetch_enabled: bool = Field(default=False)
    prefetched_data: dict[str, dict[str, Any]] | None = None
    batch_prefetch_metrics: dict[str, Any] | None = None

    # LLM cost tracking fields (COST-01, COST-02)
    llm_total_cost: float = Field(default=0.0)
    llm_crew_costs: dict[str, float] = Field(default_factory=dict)
    llm_call_count: int = Field(default=0)
    llm_cost_summary: dict[str, Any] | None = None

    # Stress testing fields (RISK-01 to RISK-04)
    stress_test_results: list[dict[str, Any]] = Field(default_factory=list)
    stress_test_count: int = Field(default=0)
    stress_test_error: str | None = None

    # Macro snapshot for report-time access (Phase 16)
    macro_snapshot: dict[str, Any] | None = Field(default=None, description="Session-level MacroSnapshot dict for report generation")

    # Run ledger — populated by DeepAnalysisOrchestrator.__init__ at analysis time.
    # Type is Any to avoid a circular import (RunLedger lives in analysis.stages._ledger).
    # Readers that need ledger-derived views should use ledger_coverage or cast at point of use.
    run_ledger: Any = Field(default=None, exclude=True, description="Active RunLedger instance for this analysis run")

    model_config = {
        "extra": "allow",
        "ser_json_timedelta": "iso8601",
        "ser_json_bytes": "base64",
    }

    @property
    def ledger_coverage(self) -> tuple[int, int]:
        """Backwards-compatible (analyzed, total) view derived from the run ledger.

        Falls back to (0, 0) if no ledger is attached (e.g. during tests that bypass
        the orchestrator, or before Phase 3 runs).
        """
        if self.run_ledger is None:
            return (0, 0)
        summary = self.run_ledger.coverage()
        return (summary.analyzed, summary.total)
