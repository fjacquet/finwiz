from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskAssessmentStandardized

Decision = Literal["KEEP", "SELL"]
AssetClass = Literal["stock", "etf", "crypto"]  # Added crypto support for A+ discoveries
Grade = Literal["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
ImprovementType = Literal["replacement", "addition", "rebalancing"]
Priority = Literal["high", "medium", "low"]


class Alternative(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    name: str
    asset_class: AssetClass
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk_score_standardized: float = Field(ge=0.0, le=5.0)
    key_metrics: dict = Field(default_factory=dict)
    thesis_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)

    # A+ discovery enhancement fields
    is_a_plus_candidate: bool = Field(default=False, description="Whether this is an A+ grade candidate")
    discovery_source: Optional[str] = Field(None, description="Source of A+ discovery (e.g., 'investment_discovery_crew')")
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in A+ classification")
    expected_annual_benefit: Optional[float] = Field(None, description="Expected annual benefit in percentage points")

    # NEW: Transition strategy fields
    transition_strategy: str = Field(default="", description="Strategy for transitioning to this alternative")
    swap_timing: Literal["immediate", "gradual", "tax_optimized"] = Field(default="gradual", description="Recommended timing for swap")
    tax_implications: str = Field(default="", description="Tax considerations for the swap")
    expected_cost_basis_impact: Optional[float] = Field(None, description="Expected impact on cost basis")

    # NEW: Comparison metrics
    expense_ratio_savings: Optional[float] = Field(None, description="Expense ratio savings for ETFs")
    fundamental_improvement: Optional[dict] = Field(None, description="Fundamental metric improvements for stocks")
    liquidity_improvement: Optional[float] = Field(None, description="Liquidity improvement for crypto")


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
    expected_annual_benefit: Optional[float] = Field(None, description="Expected annual benefit in percentage points")
    risk_impact_description: str = Field(..., description="Description of risk impact")
    cost_analysis: dict[str, float] = Field(default_factory=dict, description="Transaction costs and fees")
    implementation_notes: list[str] = Field(default_factory=list, description="Implementation considerations")


class PriceTargets(BaseModel):
    """Price targets for buy/sell decisions."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_price: float
    currency: str
    fair_value_estimate: Optional[float] = None

    # Buy targets
    buy_target_primary: Optional[float] = None
    buy_target_secondary: Optional[float] = None
    buy_rationale: str = ""

    # Sell targets
    sell_target_primary: Optional[float] = None
    sell_target_secondary: Optional[float] = None
    stop_loss_level: Optional[float] = None
    sell_rationale: str = ""

    # Technical levels
    support_levels: list[float] = Field(default_factory=list)
    resistance_levels: list[float] = Field(default_factory=list)

    # Metadata
    calculation_method: str = ""
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.5)
    data_as_of: datetime
    data_sources: list[str] = Field(default_factory=list)


class PositionSizeRecommendation(BaseModel):
    """Position sizing recommendation."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    current_size_pct: float = Field(ge=0.0, le=100.0)
    recommended_size_pct: float = Field(ge=0.0, le=100.0)
    sizing_action: Literal["add", "trim", "hold", "exit"]

    # Rationale
    sizing_rationale: str
    risk_contribution: float = Field(ge=0.0, le=100.0, default=0.0)
    correlation_with_portfolio: float = Field(ge=-1.0, le=1.0, default=0.0)

    # Constraints applied
    concentration_limits_applied: bool = False
    risk_limits_applied: bool = False


class HoldingDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    asset_class: AssetClass
    name: str
    ticker: str
    currency: str
    decision: Decision
    composite_score: float = Field(ge=0.0, le=1.0)
    grade: Grade = Field(description="Letter grade (A+ to F)")
    grade_description: str = Field(description="Human-readable grade description")
    recommended_action: str = Field(description="Recommended action based on grade")
    risk: RiskAssessmentStandardized
    rationale_bullets: list[str] = Field(default_factory=list, max_length=10)
    citations: list[str] = Field(default_factory=list, max_length=10)
    alternatives: list[Alternative] = Field(default_factory=list, max_length=3)

    # NEW: Price targets and position sizing
    price_targets: Optional[PriceTargets] = None
    position_sizing: Optional[PositionSizeRecommendation] = None

    # A+ improvement suggestions enhancement
    a_plus_improvement_suggestions: list[APlusImprovementSuggestion] = Field(default_factory=list, max_length=5, description="A+ improvement suggestions for this holding")
    has_a_plus_opportunities: bool = Field(default=False, description="Whether A+ improvement opportunities exist for this holding")
    current_grade_potential: Optional[str] = Field(None, description="Assessment of current holding's potential for grade improvement")

    # NEW: Data freshness and crew analysis tracking
    data_freshness: Literal["fresh", "recent", "stale"] = Field(default="stale", description="Freshness of analysis data")
    crew_analysis_used: Optional[str] = Field(None, description="Which crew analysis was used (stock_crew/etf_crew/crypto_crew)")
    analysis_date: Optional[datetime] = Field(None, description="When the analysis was performed")


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
    last_discovery_date: Optional[datetime] = Field(None, description="When A+ discovery was last performed")
    discovery_coverage: list[str] = Field(default_factory=list, description="Asset types covered in discovery")
    market_conditions_note: str = Field(default="", description="Note about market conditions during discovery")


class PortfolioReview(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    as_of: datetime
    base_currency: str = "CHF"
    holdings: list[HoldingDecision] = Field(default_factory=list)

    # A+ opportunities integration
    a_plus_opportunities: APlusOpportunitySection = Field(default_factory=APlusOpportunitySection, description="A+ investment opportunities identified for this portfolio")

    # Portfolio-level A+ metrics
    current_a_plus_holdings_count: int = Field(default=0, description="Number of current A+ holdings")
    potential_a_plus_holdings_count: int = Field(default=0, description="Potential A+ holdings after improvements")
    portfolio_grade_improvement_potential: float = Field(default=0.0, description="Maximum potential grade improvement")

    # Migration and compatibility fields
    schema_version: str = Field(default="2.1", description="Schema version for migration compatibility")
    has_a_plus_analysis: bool = Field(default=False, description="Whether A+ analysis has been performed")
    has_deep_analysis: bool = Field(default=False, description="Whether deep holding analysis has been performed")
