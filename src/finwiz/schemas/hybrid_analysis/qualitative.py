"""
Qualitative insights schemas for AI-generated contextual analysis.

This module provides Pydantic models for AI-generated qualitative insights
that complement Python-calculated quantitative metrics.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class SecAnalysisInsights(BaseModel):
    """
    SEC filings analysis insights (AI-generated).

    Qualitative analysis of business model, competitive advantages,
    and risk factors from SEC 10-K and 10-Q filings.
    """

    business_model: str = Field(default="", description="Comprehensive business model analysis")
    competitive_advantages: list[str] = Field(default_factory=list, description="List of identified competitive advantages")
    risk_factors: list[str] = Field(default_factory=list, description="Risk factors from SEC filings with severity ratings")
    strategic_initiatives: list[str] = Field(default_factory=list, description="Key strategic initiatives with expected impact")

    @field_validator("business_model", mode="before")
    @classmethod
    def coerce_business_model(cls, v: object) -> str:
        """Coerce dict to string (AI sometimes returns a dict for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    @field_validator("risk_factors", mode="before")
    @classmethod
    def coerce_risk_factors(cls, v: list) -> list[str]:
        """Coerce dict entries (e.g. {'risk': '...', 'severity': '...'}) to strings."""
        result = []
        for item in v:
            if isinstance(item, dict):
                risk = item.get("risk", item.get("name", str(item)))
                severity = item.get("severity", "")
                result.append(f"{risk} (Sévérité: {severity})" if severity else str(risk))
            else:
                result.append(str(item))
        return result

    model_config = {
        "str_strip_whitespace": True,
    }


class FundamentalContextInsights(BaseModel):
    """
    Fundamental analysis context (AI-generated).

    Industry context, growth drivers, competitive positioning,
    and management assessment.
    """

    industry_analysis: str = Field(default="", description="Industry context and trends")
    growth_drivers: list[str] = Field(default_factory=list, description="Key growth drivers and catalysts")
    competitive_positioning: str = Field(default="", description="Competitive positioning analysis")
    management_assessment: str = Field(default="", description="Management quality and track record")

    @field_validator("industry_analysis", "competitive_positioning", "management_assessment", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict entries to strings (AI sometimes returns dicts for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    model_config = {
        "str_strip_whitespace": True,
    }


class TechnicalStrategyInsights(BaseModel):
    """
    Technical analysis strategy (AI-generated).

    Chart patterns, support/resistance levels, entry/exit strategy,
    and timing assessment.
    """

    chart_patterns: list[str] = Field(default_factory=list, description="Identified chart patterns and formations")
    support_resistance: str = Field(default="", description="Key support and resistance levels")
    entry_exit_strategy: str = Field(default="", description="Entry/exit strategy with price targets")
    timing_assessment: str = Field(default="", description="Market timing and momentum assessment")

    @field_validator("support_resistance", "entry_exit_strategy", "timing_assessment", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict entries (e.g. {'support_levels': '...', 'resistance_levels': '...'}) to strings."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    model_config = {
        "str_strip_whitespace": True,
    }


class ContextualRiskInsights(BaseModel):
    """
    Contextual risk analysis (AI-generated).

    Regulatory, geopolitical, competitive, and operational risks
    with stress scenarios.
    """

    regulatory_risks: list[str] = Field(default_factory=list, description="Regulatory and compliance risks")
    geopolitical_risks: list[str] = Field(default_factory=list, description="Geopolitical and macroeconomic risks")
    competitive_risks: list[str] = Field(default_factory=list, description="Competitive and market risks")
    operational_risks: list[str] = Field(default_factory=list, description="Operational and execution risks")
    stress_scenarios: list[str] = Field(default_factory=list, description="Stress test scenarios and outcomes")

    model_config = {
        "str_strip_whitespace": True,
    }


class ScenarioProbabilities(BaseModel):
    """Probabilities for bull/base/bear scenarios (must sum to 1.0)."""

    bull: float = Field(..., ge=0.0, le=1.0, description="Bull case probability")
    base: float = Field(..., ge=0.0, le=1.0, description="Base case probability")
    bear: float = Field(..., ge=0.0, le=1.0, description="Bear case probability")

    model_config = {
        "str_strip_whitespace": True,
    }

    @model_validator(mode="after")
    def validate_probabilities_sum_to_one(self) -> "ScenarioProbabilities":
        """Ensure probabilities sum to 1.0 (with tolerance for floating point)."""
        total = self.bull + self.base + self.bear
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Probabilities must sum to 1.0, got {total:.4f}")
        return self


class ActionPlan(BaseModel):
    """Actionable steps for investment strategy."""

    immediate_actions: list[str] = Field(default_factory=list, description="Immediate actions to take")
    monitoring_points: list[str] = Field(default_factory=list, description="Key metrics and events to monitor")
    exit_triggers: list[str] = Field(default_factory=list, description="Conditions that would trigger exit")

    model_config = {
        "str_strip_whitespace": True,
    }


class InvestmentSynthesis(BaseModel):
    """
    Investment synthesis and final recommendation (AI-generated).

    Investment thesis, bull/base/bear scenarios, final recommendation,
    and action plan.
    """

    investment_thesis: str = Field(default="", description="Comprehensive investment thesis")
    bull_case: str = Field(default="", description="Bull case scenario with catalysts")
    base_case: str = Field(default="", description="Base case scenario (most likely)")
    bear_case: str = Field(default="", description="Bear case scenario with risks")
    scenario_probabilities: ScenarioProbabilities | None = Field(default=None, description="Probabilities for bull/base/bear scenarios")
    final_recommendation: Literal["BUY", "HOLD", "SELL"] = Field(default="HOLD", description="Final AI-refined recommendation")
    recommendation_confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(default="MEDIUM", description="AI confidence in recommendation")
    action_plan: ActionPlan | None = Field(default=None, description="Actionable steps: immediate_actions, monitoring_points, exit_triggers")

    @field_validator("investment_thesis", "bull_case", "base_case", "bear_case", mode="before")
    @classmethod
    def coerce_prose_to_string(cls, v: object) -> str:
        """Coerce dict to string (AI sometimes returns a dict for prose fields)."""
        if isinstance(v, dict):
            return " | ".join(f"{k}: {val}" for k, val in v.items())
        return str(v) if v is not None else ""

    @model_validator(mode="before")
    @classmethod
    def provide_defaults_for_optional_fields(cls, values: object) -> object:
        """Ensure action_plan is never None (empty lists are honest; None hides the section)."""
        if not isinstance(values, dict):
            return values
        if values.get("action_plan") is None:
            values["action_plan"] = {"immediate_actions": [], "monitoring_points": [], "exit_triggers": []}
        return values

    model_config = {
        "str_strip_whitespace": True,
    }


class QualitativeInsights(BaseModel):
    """
    AI-generated qualitative analysis (contextual).

    Comprehensive qualitative insights that complement Python-calculated
    quantitative metrics. Provides context, interpretation, and strategic
    guidance.
    """

    # Investment Strategy — placed FIRST so LLM fills it before token budget runs out
    investment_synthesis: InvestmentSynthesis | None = Field(default=None, description="Investment synthesis and recommendation")

    # SEC Analysis
    sec_insights: SecAnalysisInsights | None = Field(default=None, description="SEC filings analysis")

    # Fundamental Analysis
    fundamental_context: FundamentalContextInsights | None = Field(default=None, description="Fundamental context and positioning")

    # Technical Analysis
    technical_strategy: TechnicalStrategyInsights | None = Field(default=None, description="Technical strategy and timing")

    # Risk Analysis
    contextual_risks: ContextualRiskInsights | None = Field(default=None, description="Contextual risk analysis")

    # Metadata
    analysis_timestamp: datetime | None = Field(default=None, description="When AI analysis was performed (UTC)")
    ai_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="AI confidence in overall analysis (0.0-1.0)")

    model_config = {
        "str_strip_whitespace": True,
    }
