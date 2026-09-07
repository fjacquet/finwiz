"""
Pydantic export schemas for FinWiz crews.

This module defines validated export objects that a crew generates and saves to JSON.
These schemas follow the AI Minimalism principle: crews generate structured JSON exports,
and Python templates (Jinja2) render HTML reports from these exports.

All schemas use strict validation with extra='forbid' to ensure data quality.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# Import existing schemas from finwiz.schemas
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.portfolio_review import Grade


class CrewExportBase(BaseModel):
    """Base schema for all crew exports with common fields."""

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    crew_name: str = Field(..., description="Name of the crew that generated this export")
    ticker: str = Field(..., description="Asset ticker symbol (or 'N/A' for portfolio-level analysis)")
    asset_class: str = Field(..., pattern="^(stock|etf|crypto|portfolio|N/A)$", description="Asset class")
    session_id: str = Field(..., description="Flow session identifier for tracking")
    analysis_date: datetime = Field(default_factory=datetime.now, description="When the analysis was performed")


class DeepAnalysisCrewExport(CrewExportBase):
    """
    Export schema for Deep Analysis Crew.

    Contains comprehensive analysis for underperforming holdings (grade < B)
    with detailed investigation and recommendations.
    """

    crew_name: str = Field(default="deep_analysis_crew")

    # Comprehensive Analysis
    detailed_analysis: dict[str, Any] = Field(default_factory=dict, description="Detailed analysis findings across multiple dimensions")
    risk_assessment: RiskAssessmentStandardized = Field(..., description="Standardized risk assessment")

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Recommendations
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed rationale for recommendation")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")
