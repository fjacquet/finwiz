"""
Enriched analysis schema combining Python calculations and AI insights.

This module provides the EnrichedAnalysis model that merges quantitative
Python calculations with qualitative AI-generated insights.
"""

from datetime import datetime

from pydantic import BaseModel, Field, computed_field

from finwiz.schemas.hybrid_analysis.qualitative import QualitativeInsights
from finwiz.schemas.hybrid_analysis.quantitative import QuantitativeAnalysis


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
    ticker: str = Field(..., min_length=1, description="Stock ticker symbol")
    company_name: str = Field(..., min_length=1, description="Company name")
    asset_class: str = Field(..., pattern=r"^(stock|etf|crypto)$", description="Asset class (stock, etf, crypto)")
    analysis_date: datetime = Field(default_factory=datetime.utcnow, description="Analysis date (UTC)")

    # Python (deterministic)
    quantitative: QuantitativeAnalysis = Field(..., description="Python-calculated metrics")

    # AI (contextual)
    qualitative: QualitativeInsights = Field(..., description="AI-generated insights")

    # Final synthesis (hybrid)
    final_grade: str = Field(..., pattern=r"^(A\+|A|A-|B\+|B|B-|C\+|C|C-|D\+|D|D-|F)$", description="Final grade (from Python)")
    final_score: float = Field(..., ge=0.0, le=1.0, description="Final score (from Python)")
    final_recommendation: str = Field(..., pattern=r"^(BUY|HOLD|SELL)$", description="Final recommendation (may differ from preliminary)")
    recommendation_confidence: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH)$", description="AI confidence assessment")

    # Rich output (AI-generated)
    executive_summary: str = Field(..., min_length=200, description="AI-written executive summary (minimum 200 words)")
    investment_rationale: str = Field(..., min_length=500, description="Detailed investment rationale (minimum 500 words)")

    # Quality metrics
    report_word_count: int = Field(..., ge=2000, description="Total report word count (minimum 2000)")
    unique_insights_count: int = Field(..., ge=5, description="Number of unique qualitative insights (minimum 5)")

    # Processing metadata
    processing_time_seconds: float = Field(..., gt=0, description="Total processing time in seconds")
    llm_cost_dollars: float = Field(..., ge=0, description="LLM cost for analysis in dollars")

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
    }

    @computed_field
    @property
    def calculated_word_count(self) -> int:
        """
        Calculate actual word count from report content.

        Returns:
            Total word count from all text sections

        """
        sections = [
            self.executive_summary,
            self.investment_rationale,
            self.qualitative.sec_insights.business_model,
            self.qualitative.investment_synthesis.investment_thesis,
        ]
        return len(" ".join(sections).split())
