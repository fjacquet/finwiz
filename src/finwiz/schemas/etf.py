from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized


class ETFTopHolding(BaseModel):
    """A single ETF top holding with weight and provenance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    weight_pct: float = Field(ge=0.0, le=100.0)
    source_url: str = Field(description="Source URL for the holding data")
    as_of: date

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        """Validate that source_url is a valid URL."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v


class ETFFactsheet(BaseModel):
    """
    ETF factsheet highlights and metadata.

    Include commonly available numbers to aid the final reporter and risk synthesis.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1

    ticker: str = Field(min_length=1, max_length=15)
    issuer: str
    expense_ratio: float = Field(ge=0.0, le=5.0, description="Total expense ratio (%)")
    tracking_diff: Optional[float] = Field(
        default=None,
        ge=-10.0,
        le=10.0,
        description="Annualized tracking difference vs benchmark in %",
    )
    replication_method: Literal["physical", "synthetic", "optimized", "other"] = "other"

    factsheet_url: str = Field(description="URL to the ETF factsheet")
    as_of: date

    factsheet_highlights: list[str] = Field(default_factory=list, max_length=20)
    top_holdings: list[ETFTopHolding] = Field(default_factory=list)

    @field_validator("factsheet_url")
    @classmethod
    def validate_factsheet_url(cls, v: str) -> str:
        """Validate that factsheet_url is a valid URL."""
        import re

        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    # standardized risk lives separately
    risk: Optional[RiskAssessmentStandardized] = None


class ETFMarketTrend(BaseModel):
    """ETF market trend analysis output."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    analysis_date: date = Field(description="Date of the analysis")
    key_trends: list[str] = Field(description="Key ETF market trends", max_length=20)
    emerging_sectors: list[str] = Field(description="Emerging ETF sectors", max_length=15)
    global_factors: list[str] = Field(description="Global economic factors impacting ETFs", default_factory=list, max_length=10)
    liquidity_trends: list[str] = Field(description="Liquidity and volume trends", default_factory=list, max_length=10)
    regulatory_developments: list[str] = Field(description="Regulatory developments", default_factory=list, max_length=10)
    data_sources: list[str] = Field(description="Data sources used", default_factory=list)


class ETFCandidate(BaseModel):
    """Individual ETF candidate from screening task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    name: str = Field(description="Full ETF name")
    issuer: str = Field(description="ETF issuer/provider")
    category: Optional[str] = Field(None, description="ETF category (e.g., equity, bond, commodity)")
    aum: Optional[float] = Field(None, gt=0, description="Assets under management in USD")
    expense_ratio: Optional[float] = Field(None, ge=0.0, le=5.0, description="Expense ratio percentage")
    tracking_error: Optional[float] = Field(None, ge=0.0, description="Tracking error vs benchmark")
    selection_rationale: str = Field(description="Why this ETF was selected", min_length=20)
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in selection")


class ETFScreeningResult(BaseModel):
    """ETF screening task output with top candidates."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    screening_date: date = Field(description="Date of screening")
    total_screened: int = Field(ge=0, description="Total ETFs screened")
    candidates: list[ETFCandidate] = Field(description="Top ETF candidates", max_length=20)
    screening_criteria: list[str] = Field(description="Criteria used for screening", max_length=10)
    market_context: str = Field(description="Market context during screening")


class ETFTechnicalIndicators(BaseModel):
    """Technical indicators for an ETF."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    rsi: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative Strength Index")
    macd: Optional[float] = Field(None, description="MACD indicator value")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    bollinger_upper: Optional[float] = Field(None, gt=0, description="Bollinger Bands upper bound")
    bollinger_lower: Optional[float] = Field(None, gt=0, description="Bollinger Bands lower bound")
    moving_avg_50: Optional[float] = Field(None, gt=0, description="50-day moving average")
    moving_avg_200: Optional[float] = Field(None, gt=0, description="200-day moving average")


class ETFQuantitativeMetrics(BaseModel):
    """Quantitative analysis metrics for an ETF."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=15)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[float] = Field(None, le=0.0, description="Maximum drawdown percentage")
    volatility: Optional[float] = Field(None, ge=0.0, description="Annualized volatility")
    beta: Optional[float] = Field(None, description="Beta relative to benchmark")
    alpha: Optional[float] = Field(None, description="Alpha (excess return)")
    tracking_error: Optional[float] = Field(None, ge=0.0, description="Tracking error vs benchmark")
    correlation_with_benchmark: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Correlation with benchmark")
    recommendation: Optional[Literal["BUY", "HOLD", "SELL"]] = Field(None, description="Investment recommendation")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recommendation confidence")


class ETFTechnicalAnalysis(BaseModel):
    """Technical analysis output for ETF technical detail task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=15)
    name: str = Field(description="Full ETF name")
    analysis_date: date = Field(description="Date of analysis")

    # ETF structure
    factsheet: Optional[ETFFactsheet] = Field(None, description="ETF factsheet data")
    replication_method: Optional[str] = Field(None, description="Replication method details")
    lending_practices: Optional[str] = Field(None, description="Securities lending practices")

    # Performance
    tracking_accuracy: Optional[str] = Field(None, description="Tracking accuracy assessment")
    historical_performance: Optional[str] = Field(None, description="Historical performance summary")

    # Technical indicators
    technical_indicators: Optional[ETFTechnicalIndicators] = Field(None, description="Technical indicators")

    # Quantitative analysis
    quantitative_metrics: Optional[ETFQuantitativeMetrics] = Field(None, description="Quantitative metrics")

    # Management
    fund_manager_assessment: Optional[str] = Field(None, description="Fund manager expertise assessment")
    issuer_stability: Optional[str] = Field(None, description="Issuer stability assessment")

    # Overall assessment
    investment_thesis: str = Field(description="Investment thesis summary", min_length=50)
    liquidity_profile: Optional[str] = Field(None, description="Liquidity profile assessment")


class ETFRiskProfile(BaseModel):
    """Risk assessment output for ETF risk assessment task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=15)
    name: str = Field(description="Full ETF name")
    assessment_date: date = Field(description="Date of risk assessment")

    # Standardized risk assessment
    risk_assessment: RiskAssessmentStandardized = Field(description="Standardized risk assessment")

    # Risk categories
    volatility_risk: str = Field(description="Volatility and drawdown risk assessment", min_length=20)
    concentration_risk: str = Field(description="Holdings concentration risk assessment", min_length=20)
    liquidity_risk: str = Field(description="Liquidity risk assessment", min_length=20)
    counterparty_risk: str = Field(description="Counterparty and structural risk assessment", min_length=20)
    regulatory_risk: str = Field(description="Regulatory and tax risk assessment", min_length=20)

    # Quantitative risk metrics
    quantitative_risk_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Quantitative risk metrics (tracking error, correlation, etc.)"
    )

    # Risk mitigation
    risk_mitigation_strategies: list[str] = Field(default_factory=list, description="Risk mitigation strategies", max_length=10)

    # Overall risk summary
    risk_summary: str = Field(description="Overall risk summary", min_length=50)
