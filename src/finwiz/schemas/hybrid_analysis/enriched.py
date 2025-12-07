"""
Enriched analysis schema combining Python calculations and AI insights.

This module provides the EnrichedAnalysis model that merges quantitative
Python calculations with qualitative AI-generated insights.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis


def _coerce_none_to_str(v: Any, default: str = "") -> str:
    """Coerce None to default string for LLM outputs that return null."""
    if v is None:
        return default
    return str(v)


class EnrichedAnalysis(BaseModel):
    """
    Combined Python calculations + AI insights.

    Merges deterministic quantitative analysis from Python with contextual
    qualitative insights from AI agents to produce comprehensive investment
    analysis.

    Examples:
        >>> enriched = EnrichedAnalysis(
        ...     ticker="AAPL",
        ...     company_name="Apple Inc.",
        ...     asset_class="stock",
        ...     quantitative=quantitative_analysis,
        ...     qualitative=qualitative_insights,
        ...     final_grade="A",
        ...     final_score=0.85,
        ...     final_recommendation="BUY",
        ...     recommendation_confidence="HIGH",
        ...     executive_summary="Strong fundamentals...",
        ...     investment_rationale="Comprehensive analysis...",
        ...     report_word_count=2500,
        ...     unique_insights_count=7,
        ...     processing_time_seconds=25.5,
        ...     llm_cost_dollars=0.08,
        ... )

    """

    # Identification
    ticker: str = Field(default="", description="Stock ticker symbol")
    company_name: str = Field(default="", description="Company name")
    asset_class: str = Field(default="stock", description="Asset class (stock, etf, crypto)")

    # Validators to handle None from LLM outputs (Pydantic v2 treats null as explicit None)
    @field_validator("ticker", "company_name", "asset_class", "final_grade", 
                     "final_recommendation", "recommendation_confidence",
                     "executive_summary", "investment_rationale", mode="before")
    @classmethod
    def coerce_none_to_empty_string(cls, v: Any) -> str:
        """Coerce None to empty string for LLM outputs that return null."""
        return _coerce_none_to_str(v, "")
    analysis_date: datetime = Field(default_factory=datetime.utcnow, description="Analysis date (UTC)")

    # Python (deterministic)
    quantitative: QuantitativeAnalysis | None = Field(default=None, description="Python-calculated metrics")

    # AI (contextual)
    qualitative: QualitativeInsights | None = Field(default=None, description="AI-generated insights")

    # Final synthesis (hybrid)
    final_grade: str = Field(default="C", description="Final grade (from Python)")
    final_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Final score (from Python)")
    final_recommendation: str = Field(default="HOLD", description="Final recommendation (BUY/HOLD/SELL)")
    recommendation_confidence: str = Field(default="MEDIUM", description="AI confidence assessment (LOW/MEDIUM/HIGH)")

    # Rich output (AI-generated)
    executive_summary: str = Field(default="", description="AI-written executive summary")
    investment_rationale: str = Field(default="", description="Detailed investment rationale")

    # Quality metrics
    report_word_count: int = Field(default=0, ge=0, description="Total report word count")
    unique_insights_count: int = Field(default=0, ge=0, description="Number of unique qualitative insights")

    # Processing metadata
    processing_time_seconds: float = Field(default=0.0, ge=0, description="Total processing time in seconds")
    llm_cost_dollars: float = Field(default=0.0, ge=0, description="LLM cost for analysis in dollars")

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
    }

    @computed_field
    @property
    def calculated_word_count(self) -> int:
        """
        Calculate actual word count from all report content.

        Counts words from all text sections including:
        - Executive summary
        - Investment rationale
        - SEC insights (business model, competitive advantages, risk factors, strategic initiatives)
        - Fundamental context (industry analysis, growth drivers, competitive positioning, management assessment)
        - Technical strategy (chart patterns, support/resistance, entry/exit strategy, timing assessment)
        - Contextual risks (all risk categories and stress scenarios)
        - Investment synthesis (investment thesis, bull/base/bear cases)

        Returns:
            Total word count from all text sections

        """
        sections: list[str] = []

        # Core summaries
        sections.append(self.executive_summary)
        sections.append(self.investment_rationale)

        # Only add qualitative sections if qualitative is not None
        if self.qualitative:
            # SEC insights
            if self.qualitative.sec_insights:
                sections.append(self.qualitative.sec_insights.business_model)
                sections.extend(self.qualitative.sec_insights.competitive_advantages)
                sections.extend(self.qualitative.sec_insights.risk_factors)
                sections.extend(self.qualitative.sec_insights.strategic_initiatives)

            # Fundamental context
            if self.qualitative.fundamental_context:
                sections.append(self.qualitative.fundamental_context.industry_analysis)
                sections.extend(self.qualitative.fundamental_context.growth_drivers)
                sections.append(self.qualitative.fundamental_context.competitive_positioning)
                sections.append(self.qualitative.fundamental_context.management_assessment)

            # Technical strategy
            if self.qualitative.technical_strategy:
                sections.extend(self.qualitative.technical_strategy.chart_patterns)
                sections.append(self.qualitative.technical_strategy.support_resistance)
                sections.append(self.qualitative.technical_strategy.entry_exit_strategy)
                sections.append(self.qualitative.technical_strategy.timing_assessment)

            # Contextual risks
            if self.qualitative.contextual_risks:
                sections.extend(self.qualitative.contextual_risks.regulatory_risks)
                sections.extend(self.qualitative.contextual_risks.geopolitical_risks)
                sections.extend(self.qualitative.contextual_risks.competitive_risks)
                sections.extend(self.qualitative.contextual_risks.operational_risks)
                sections.extend(self.qualitative.contextual_risks.stress_scenarios)

            # Investment synthesis
            if self.qualitative.investment_synthesis:
                sections.append(self.qualitative.investment_synthesis.investment_thesis)
                sections.append(self.qualitative.investment_synthesis.bull_case)
                sections.append(self.qualitative.investment_synthesis.base_case)
                sections.append(self.qualitative.investment_synthesis.bear_case)

        # Combine all sections and count words
        combined_text = " ".join(str(section) for section in sections if section)
        return len(combined_text.split())
