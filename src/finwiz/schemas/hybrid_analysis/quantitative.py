"""
Quantitative analysis schemas for Python-calculated metrics.

This module provides Pydantic models for deterministic quantitative analysis
performed by Python code (not AI agents).
"""

from datetime import datetime

from pydantic import BaseModel, Field

from finwiz.schemas.hybrid_analysis.metadata import DataQualityMetrics
from finwiz.schemas.portfolio_review import PriceTargets


class QuantitativeAnalysis(BaseModel):
    """
    Python-calculated quantitative metrics (deterministic).

    Contains all scores, grades, and metrics calculated by Python code
    using deterministic algorithms. This data is passed as READ-ONLY
    context to AI agents for qualitative analysis.

    Examples:
        >>> analysis = QuantitativeAnalysis(
        ...     composite_score=0.85,
        ...     fundamental_score=0.90,
        ...     technical_score=0.80,
        ...     risk_score=2.5,
        ...     grade="A",
        ...     preliminary_recommendation="BUY",
        ...     fundamental_metrics={"roe": 0.25, "debt_to_equity": 0.3},
        ...     technical_indicators={"rsi": 55.0, "macd": 1.2},
        ...     risk_metrics={"volatility": 0.15, "max_drawdown": 0.10},
        ...     calculation_timestamp=datetime.now(),
        ...     data_quality=DataQualityMetrics(...),
        ...     confidence_level=0.90,
        ...     python_rationale="Strong fundamentals with moderate technical signals",
        ... )

    """

    # Core Scores
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score (0.0-1.0)")
    fundamental_score: float = Field(..., ge=0.0, le=1.0, description="Fundamental analysis score (0.0-1.0)")
    technical_score: float = Field(..., ge=0.0, le=1.0, description="Technical analysis score (0.0-1.0)")
    risk_score: float = Field(..., ge=0.0, le=5.0, description="Risk assessment score (0.0-5.0, lower is better)")

    # Grade & Preliminary Recommendation
    grade: str = Field(..., pattern=r"^(A\+|A|A-|B\+|B|B-|C\+|C|C-|D\+|D|D-|F)$", description="Letter grade from A+ to F")
    preliminary_recommendation: str = Field(..., pattern=r"^(BUY|HOLD|SELL)$", description="Initial recommendation before AI analysis")

    # Detailed Metrics
    fundamental_metrics: dict[str, float] = Field(..., description="ROE, debt_to_equity, revenue_growth, profit_margin, etc.")
    technical_indicators: dict[str, float] = Field(..., description="RSI, MACD, trend_strength, momentum, etc.")
    risk_metrics: dict[str, float] = Field(..., description="volatility, max_drawdown, beta, sharpe_ratio, etc.")

    # Metadata
    calculation_timestamp: datetime = Field(..., description="When calculations were performed (UTC)")
    data_quality: DataQualityMetrics = Field(..., description="Quality assessment of input data")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in calculations (0.0-1.0)")

    # Template-based rationale (to be enhanced by AI)
    python_rationale: str = Field(..., min_length=10, description="Template-generated rationale from Python")

    # ADR-011: tactical 3-6 month price target + stop-loss floor.
    # Optional because compute_tactical_pricing returns None for short / stale /
    # degenerate history.
    price_targets: PriceTargets | None = Field(
        default=None,
        description="Tactical 3-6 month price target and stop-loss floor (ADR-011)",
    )

    model_config = {
        "str_strip_whitespace": True,
        "validate_default": True,
        "json_schema_extra": {
            "examples": [
                {
                    "composite_score": 0.85,
                    "fundamental_score": 0.90,
                    "technical_score": 0.80,
                    "risk_score": 2.5,
                    "grade": "A",
                    "preliminary_recommendation": "BUY",
                    "fundamental_metrics": {"roe": 0.25, "debt_to_equity": 0.3, "revenue_growth": 0.15, "profit_margin": 0.20},
                    "technical_indicators": {"rsi": 55.0, "macd": 1.2, "trend_strength": 0.75},
                    "risk_metrics": {"volatility": 0.15, "max_drawdown": 0.10, "beta": 1.1, "sharpe_ratio": 1.5},
                    "calculation_timestamp": "2025-11-21T10:30:00Z",
                    "data_quality": {"completeness_score": 0.95, "freshness_score": 1.0, "accuracy_confidence": 0.90, "source_reliability": 0.85, "missing_fields": []},
                    "confidence_level": 0.90,
                    "python_rationale": "Strong fundamentals with moderate technical signals",
                }
            ]
        },
    }
