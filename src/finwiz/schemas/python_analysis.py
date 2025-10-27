"""
Schemas for Python-based analysis results (non-AI).

These schemas define the structure for deterministic Python analysis outputs,
separate from CrewAI crew exports. Following the AI Minimalism principle,
Python analyzers generate structured data without LLM calls.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import Grade


class PythonDeepAnalysisResult(BaseModel):
    """
    Schema for Python-based deep analysis result (non-AI).

    This schema matches the output from the Python deep analyzer, which performs
    deterministic analysis without LLM calls. It's separate from DeepAnalysisCrewExport
    to maintain clean separation between AI and non-AI analysis paths.

    Key differences from CrewAI schema:
    - Uses execution_id instead of session_id
    - Includes separate fundamental/technical/risk scores
    - Has detailed breakdowns for each analysis component
    - Includes performance metrics (execution time, cost)
    - No report paths (Python analyzer doesn't generate HTML reports)
    """

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    # Identification
    crew_name: str = Field(default="PythonDeepAnalyzer", description="Analyzer identifier")
    execution_id: str = Field(..., description="Unique execution identifier")
    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: Literal["stock", "etf", "crypto"] = Field(..., description="Asset class")
    analysis_timestamp: str = Field(..., description="ISO 8601 timestamp of analysis")

    # Composite Scoring
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score (0-1)")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Component Scores
    fundamental_score: float = Field(..., ge=0.0, le=1.0, description="Fundamental analysis score (0-1)")
    technical_score: float = Field(..., ge=0.0, le=1.0, description="Technical analysis score (0-1)")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk assessment score (0-1)")

    # Recommendation
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation (0-1)")
    rationale: str = Field(..., min_length=10, description="Rationale for recommendation")

    # Detailed Analysis Components
    fundamental_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed fundamental analysis metrics and findings"
    )
    technical_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed technical analysis indicators and patterns"
    )
    risk_details: dict[str, Any] = Field(default_factory=dict, description="Detailed risk assessment metrics")

    # Performance Metrics
    performance_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution performance metrics (time, LLM calls, cost)",
        examples=[{"execution_time_seconds": 0.1, "llm_calls": 0, "cost_usd": 0.0}],
    )


class PythonPortfolioAnalysisResult(BaseModel):
    """
    Schema for Python-based portfolio analysis result (non-AI).

    Aggregates multiple asset analyses into portfolio-level metrics and recommendations.
    """

    model_config = {"extra": "forbid"}

    # Identification
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_timestamp: str = Field(..., description="ISO 8601 timestamp")
    portfolio_name: str = Field(default="default", description="Portfolio identifier")

    # Portfolio Metrics
    total_holdings: int = Field(..., ge=0, description="Total number of holdings analyzed")
    total_value: float = Field(..., ge=0.0, description="Total portfolio value")
    weighted_grade: float = Field(..., ge=0.0, le=1.0, description="Value-weighted average grade score")

    # Holdings Analysis
    holdings_by_grade: dict[str, int] = Field(
        default_factory=dict, description="Count of holdings by grade (A+, A, B+, etc.)"
    )
    holdings_by_recommendation: dict[str, int] = Field(
        default_factory=dict, description="Count of holdings by recommendation (BUY, HOLD, SELL)"
    )

    # Risk Metrics
    portfolio_risk_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate portfolio risk score")
    diversification_score: float = Field(..., ge=0.0, le=1.0, description="Portfolio diversification score")

    # Performance
    execution_time_seconds: float = Field(..., ge=0.0, description="Total analysis execution time")
    total_cost_usd: float = Field(default=0.0, ge=0.0, description="Total analysis cost (should be $0 for Python)")

