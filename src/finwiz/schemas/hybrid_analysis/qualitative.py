"""
Qualitative insights schemas for AI-generated contextual analysis.

This module provides Pydantic models for AI-generated qualitative insights
that complement Python-calculated quantitative metrics.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SecAnalysisInsights(BaseModel):
    """
    SEC filings analysis insights (AI-generated).

    Qualitative analysis of business model, competitive advantages,
    and risk factors from SEC 10-K and 10-Q filings.
    """

    business_model: str = Field(..., min_length=100, description="Comprehensive business model analysis (minimum 100 words)")
    competitive_advantages: list[str] = Field(..., min_length=1, description="List of identified competitive advantages")
    risk_factors: list[str] = Field(..., min_length=1, description="Risk factors from SEC filings with severity ratings")
    strategic_initiatives: list[str] = Field(default_factory=list, description="Key strategic initiatives with expected impact")

    model_config = {
        "str_strip_whitespace": True,
    }


class FundamentalContextInsights(BaseModel):
    """
    Fundamental analysis context (AI-generated).

    Industry context, growth drivers, competitive positioning,
    and management assessment.
    """

    industry_analysis: str = Field(..., min_length=100, description="Industry context and trends (minimum 100 words)")
    growth_drivers: list[str] = Field(..., min_length=1, description="Key growth drivers and catalysts")
    competitive_positioning: str = Field(..., min_length=50, description="Competitive positioning analysis")
    management_assessment: str = Field(..., min_length=50, description="Management quality and track record")

    model_config = {
        "str_strip_whitespace": True,
    }


class TechnicalStrategyInsights(BaseModel):
    """
    Technical analysis strategy (AI-generated).

    Chart patterns, support/resistance levels, entry/exit strategy,
    and timing assessment.
    """

    chart_patterns: list[str] = Field(..., min_length=1, description="Identified chart patterns and formations")
    support_resistance: str = Field(..., min_length=50, description="Key support and resistance levels")
    entry_exit_strategy: str = Field(..., min_length=100, description="Entry/exit strategy with price targets (minimum 100 words)")
    timing_assessment: str = Field(..., min_length=50, description="Market timing and momentum assessment")

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


class InvestmentSynthesis(BaseModel):
    """
    Investment synthesis and final recommendation (AI-generated).

    Investment thesis, bull/base/bear scenarios, final recommendation,
    and action plan.
    """

    investment_thesis: str = Field(..., min_length=200, description="Comprehensive investment thesis (minimum 200 words)")
    bull_case: str = Field(..., min_length=100, description="Bull case scenario with catalysts")
    base_case: str = Field(..., min_length=100, description="Base case scenario (most likely)")
    bear_case: str = Field(..., min_length=100, description="Bear case scenario with risks")
    scenario_probabilities: dict[str, float] = Field(..., description="Probabilities for bull/base/bear scenarios (must sum to 1.0)")
    final_recommendation: str = Field(..., pattern=r"^(BUY|HOLD|SELL)$", description="Final AI-refined recommendation")
    recommendation_confidence: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH)$", description="AI confidence in recommendation")
    action_plan: dict[str, list[str]] = Field(..., description="Actionable steps: immediate_actions, monitoring_points, exit_triggers")

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

    # SEC Analysis
    sec_insights: SecAnalysisInsights = Field(..., description="SEC filings analysis")

    # Fundamental Analysis
    fundamental_context: FundamentalContextInsights = Field(..., description="Fundamental context and positioning")

    # Technical Analysis
    technical_strategy: TechnicalStrategyInsights = Field(..., description="Technical strategy and timing")

    # Risk Analysis
    contextual_risks: ContextualRiskInsights = Field(..., description="Contextual risk analysis")

    # Investment Strategy
    investment_synthesis: InvestmentSynthesis = Field(..., description="Investment synthesis and recommendation")

    # Metadata
    analysis_timestamp: datetime = Field(..., description="When AI analysis was performed (UTC)")
    ai_confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in overall analysis (0.0-1.0)")

    model_config = {
        "str_strip_whitespace": True,
    }
