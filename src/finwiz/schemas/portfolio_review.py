from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from crewai_custom_tools.models.analytics_models import (
    AssetClass,
    PositionSizeRecommendation,
    PriceTargets,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized

Decision = Literal["KEEP", "SELL"]
# AssetClass, PositionSizeRecommendation, and PriceTargets are re-exported from
# crewai_custom_tools.models.analytics_models (Wave-3 Task 9 schema shim) — the
# central package owns the canonical definitions now. finwiz keeps re-exporting
# them here so every existing `from finwiz.schemas.portfolio_review import
# AssetClass` (etc.) import path keeps working; because these are the same
# class/type objects, isinstance checks and Pydantic validation stay coherent.

# Ticker validation: matches Yahoo / Kraken formats — uppercase alnum plus
# `.` (BRK.B), `-` (BTC-USD), `:` (exchange:symbol), `^` (^GSPC), `=` (futures).
# Constrained to defend HTML render sites against attribute / script injection.
_TICKER_RE = re.compile(r"^[A-Z0-9:.\-^=]{1,15}$")
Grade = Literal["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "N/A"]
"""Letter grade scale.

`"N/A"` is reserved for holdings whose deep analysis did not run (or
failed) for this kickoff. Renderers MUST display these as
"⏳ Analyse en attente" rather than coloring them like a real low grade.
The placeholder leak from `decisions.py` (default 0.6 / D) was the source
of the DELL "B+ → D" panic — see merge.py for the explicit overwrite.
"""
ImprovementType = Literal["replacement", "addition", "rebalancing"]
Priority = Literal["high", "medium", "low"]


class Alternative(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    name: str
    asset_class: AssetClass
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F, or N/A when deep analysis didn't run)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk_score_standardized: float = Field(ge=0.0, le=5.0)
    key_metrics: dict = Field(default_factory=dict)
    thesis_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)

    # A+ discovery enhancement fields
    is_a_plus_candidate: bool = Field(default=False, description="Whether this is an A+ grade candidate")
    discovery_source: str | None = Field(None, description="Source of A+ discovery (e.g., 'investment_discovery_crew')")
    confidence_level: float | None = Field(None, ge=0.0, le=1.0, description="Confidence in A+ classification")
    expected_annual_benefit: float | None = Field(None, description="Expected annual benefit in percentage points")

    # NEW: Transition strategy fields
    transition_strategy: str = Field(default="", description="Strategy for transitioning to this alternative")
    swap_timing: Literal["immediate", "gradual", "tax_optimized"] = Field(default="gradual", description="Recommended timing for swap")
    tax_implications: str = Field(default="", description="Tax considerations for the swap")
    expected_cost_basis_impact: float | None = Field(None, description="Expected impact on cost basis")

    # NEW: Comparison metrics
    expense_ratio_savings: float | None = Field(None, description="Expense ratio savings for ETFs")
    fundamental_improvement: dict | None = Field(None, description="Fundamental metric improvements for stocks")
    liquidity_improvement: float | None = Field(None, description="Liquidity improvement for crypto")


class APlusImprovementSuggestion(BaseModel):
    """A+ improvement suggestion for a specific holding."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    improvement_type: ImprovementType = Field(..., description="Type of improvement suggested")
    recommended_symbol: str = Field(..., description="Recommended A+ investment symbol")
    recommended_name: str = Field(..., description="Full name of recommended investment")
    recommended_grade: Grade = Field(..., description="Grade of recommended investment")
    expected_grade_improvement: float = Field(..., description="Expected numerical improvement in grade")
    grade_improvement_description: str = Field(..., description="Human-readable description of grade improvement")
    allocation_percentage: float = Field(..., ge=0.0, le=100.0, description="Recommended allocation percentage")
    implementation_priority: Priority = Field(..., description="Implementation priority")
    rationale: str = Field(..., description="Detailed rationale for the improvement")
    expected_annual_benefit: float | None = Field(None, description="Expected annual benefit in percentage points")
    risk_impact_description: str = Field(..., description="Description of risk impact")
    cost_analysis: dict[str, float] = Field(default_factory=dict, description="Transaction costs and fees")
    implementation_notes: list[str] = Field(default_factory=list, description="Implementation considerations")


class HoldingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asset_class: AssetClass
    name: str
    ticker: str
    currency: str

    @field_validator("ticker")
    @classmethod
    def _validate_ticker(cls, v: str) -> str:
        """Ticker must match the Yahoo / Kraken format (defense in depth for HTML renderers)."""
        if not _TICKER_RE.match(v):
            raise ValueError(f"ticker {v!r} contains characters outside [A-Z0-9:.\\-^=] or exceeds 15 chars")
        return v

    decision: Decision
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F, or N/A when deep analysis didn't run)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk: RiskAssessmentStandardized
    rationale_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)
    alternatives: list[Alternative] = Field(default_factory=list, max_length=3)

    # v5.2 fact pack — verified corporate facts surfaced as a provenance footer
    # in the HTML report. Populated by merge.py from DeepAnalysisResult.fact_pack.
    # Type is `Any` to avoid a circular import with hybrid_analysis.fact_pack.FactPack.
    fact_pack: Any = Field(default=None, description="Verified corporate facts (FactPack) from fact_pack stage; Any to avoid circular import")

    # NEW: Price targets and position sizing
    price_targets: PriceTargets | None = None
    position_sizing: PositionSizeRecommendation | None = None

    # A+ improvement suggestions enhancement
    a_plus_improvement_suggestions: list[APlusImprovementSuggestion] = Field(default_factory=list, max_length=5, description="A+ improvement suggestions for this holding")
    has_a_plus_opportunities: bool = Field(default=False, description="Whether A+ improvement opportunities exist for this holding")
    current_grade_potential: str | None = Field(None, description="Assessment of current holding's potential for grade improvement")

    # NEW: Data freshness and crew analysis tracking
    data_freshness: Literal["fresh", "recent", "stale"] = Field(default="stale", description="Freshness of analysis data")
    crew_analysis_used: str | None = Field(None, description="Which crew analysis was used (stock_crew/etf_crew/crypto_crew)")
    analysis_date: datetime | None = Field(None, description="When the analysis was performed")

    # Trust-spine confidence marker — mirrors DeepAnalysisResult.confidence.
    # 'low' when the upstream qualify stage degraded to a Python fallback (DEGRADED).
    confidence: Literal["high", "low"] = Field(default="high", description="Pipeline confidence: 'low' when qualify stage degraded to Python fallback")

    # Allocation/valuation (deterministic Python; see scoring/portfolio_valuation.py).
    # All optional — populated only when a CSV Quantity and live price/FX resolve.
    quantity: float | None = Field(default=None, description="Position size (units/shares) from the CSV")
    native_currency: str | None = Field(default=None, description="Authoritative quote currency from the price API")
    native_value: float | None = Field(default=None, description="quantity * native price, in native currency")
    eur_value: float | None = Field(default=None, description="native_value converted to EUR via live FX")
    weight: float | None = Field(default=None, ge=0.0, le=1.0, description="Share of total EUR portfolio value (0..1)")


class APlusOpportunitySection(BaseModel):
    """A+ opportunities section for portfolio review reports."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    total_opportunities_found: int = Field(default=0, description="Total number of A+ opportunities identified")
    high_priority_opportunities: int = Field(default=0, description="Number of high-priority opportunities")
    expected_portfolio_grade_improvement: float = Field(default=0.0, description="Expected improvement in portfolio grade")
    grade_improvement_description: str = Field(default="", description="Human-readable description of grade improvement")

    # Summary of opportunities by type
    replacement_opportunities: int = Field(default=0, description="Number of replacement opportunities")
    addition_opportunities: int = Field(default=0, description="Number of addition opportunities")
    rebalancing_opportunities: int = Field(default=0, description="Number of rebalancing opportunities")

    # Top recommendations summary
    top_recommendations: list[str] = Field(default_factory=list, max_length=5, description="Top A+ symbols recommended")
    implementation_timeline: str = Field(default="", description="Recommended implementation timeline")
    total_expected_annual_benefit: float = Field(default=0.0, description="Total expected annual benefit")

    # Discovery metadata
    last_discovery_date: datetime | None = Field(None, description="When A+ discovery was last performed")
    discovery_coverage: list[str] = Field(default_factory=list, description="Asset types covered in discovery")
    market_conditions_note: str = Field(default="", description="Note about market conditions during discovery")


class PortfolioReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    as_of: datetime
    base_currency: str = "CHF"
    holdings: list[HoldingDecision] = Field(default_factory=list)
    total_value_eur: float | None = Field(default=None, description="Sum of holdings' eur_value (priced holdings only); None when nothing could be priced")

    # A+ opportunities integration
    a_plus_opportunities: APlusOpportunitySection = Field(
        default_factory=lambda: APlusOpportunitySection(), description="A+ investment opportunities identified for this portfolio"
    )

    # Portfolio-level A+ metrics
    current_a_plus_holdings_count: int = Field(default=0, description="Number of current A+ holdings")
    potential_a_plus_holdings_count: int = Field(default=0, description="Potential A+ holdings after improvements")
    portfolio_grade_improvement_potential: float = Field(default=0.0, description="Maximum potential grade improvement")

    # Migration and compatibility fields
    schema_version: str = Field(default="2.1", description="Schema version for migration compatibility")
    has_a_plus_analysis: bool = Field(default=False, description="Whether A+ analysis has been performed")
    has_deep_analysis: bool = Field(default=False, description="Whether deep holding analysis has been performed")
