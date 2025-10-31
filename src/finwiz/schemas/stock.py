from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized


class TenKInsight(BaseModel):
    """
    Extracted 10-K insight with provenance.

    section: One of the most-cited sections to constrain prompts and allow
             downstream section-specific synthesis.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    filing_url: str = Field(description="URL to the SEC filing")
    filed_at: AwareDatetime
    section: Literal["Item 1", "Item 1A", "Item 7", "Item 7A", "Item 8"]
    excerpt: str = Field(min_length=20)
    sec_citation: str  # e.g., "10-K (2024), Item 1A, p. 17"

    @field_validator("filing_url")
    @classmethod
    def validate_filing_url(cls, v: str) -> str:
        """Validate that filing_url is a valid URL."""
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


class SentimentItem(BaseModel):
    """Individual sentiment item with headline, URL, date, and score."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    headline: str
    url: str = Field(description="Article URL")
    date: AwareDatetime
    score: float = Field(ge=-1.0, le=1.0)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that url is a valid URL."""
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


class MarketSentiment(BaseModel):
    """Market sentiment analysis for a stock with aggregated scores and top headlines."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    mean_score: float = Field(ge=-1.0, le=1.0)
    counts: dict[Literal["pos", "neu", "neg"], int]
    top_pos: list[SentimentItem] = Field(default_factory=list)
    top_neg: list[SentimentItem] = Field(default_factory=list)


class MarketTrend(BaseModel):
    """Market trend analysis output for stock market trends task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    analysis_date: date = Field(description="Date of the analysis")
    key_trends: list[str] = Field(description="Key market trends identified", max_length=20)
    growth_sectors: list[str] = Field(description="Emerging growth sectors", max_length=15)
    market_sentiment: Literal["bullish", "bearish", "neutral", "mixed"] = Field(description="Overall market sentiment")
    economic_factors: list[str] = Field(description="Global economic factors impacting markets", default_factory=list, max_length=10)
    data_sources: list[str] = Field(description="Data sources used", default_factory=list)


class StockCandidate(BaseModel):
    """Individual stock candidate from screening task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=10)
    company_name: str = Field(description="Full company name")
    sector: Optional[str] = Field(None, description="Industry sector")
    market_cap: Optional[float] = Field(None, gt=0, description="Market capitalization in USD")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    dividend_yield: Optional[float] = Field(None, ge=0.0, le=100.0, description="Dividend yield percentage")
    selection_rationale: str = Field(description="Why this stock was selected", min_length=20)
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in selection")


class StockScreeningResult(BaseModel):
    """Stock screening task output with top candidates."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    screening_date: date = Field(description="Date of screening")
    total_screened: int = Field(ge=0, description="Total stocks screened")
    candidates: list[StockCandidate] = Field(description="Top stock candidates", max_length=20)
    screening_criteria: list[str] = Field(description="Criteria used for screening", max_length=10)
    market_context: str = Field(description="Market context during screening")
    sentiments: list[MarketSentiment] = Field(default_factory=list, description="Sentiment analysis for each candidate")


class TechnicalIndicators(BaseModel):
    """Technical indicators for a stock."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=10)
    rsi: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative Strength Index")
    macd: Optional[float] = Field(None, description="MACD indicator value")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    bollinger_upper: Optional[float] = Field(None, gt=0, description="Bollinger Bands upper bound")
    bollinger_lower: Optional[float] = Field(None, gt=0, description="Bollinger Bands lower bound")
    moving_avg_50: Optional[float] = Field(None, gt=0, description="50-day moving average")
    moving_avg_200: Optional[float] = Field(None, gt=0, description="200-day moving average")
    support_levels: list[float] = Field(default_factory=list, description="Support price levels")
    resistance_levels: list[float] = Field(default_factory=list, description="Resistance price levels")


class QuantitativeMetrics(BaseModel):
    """Quantitative analysis metrics for a stock."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=10)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[float] = Field(None, le=0.0, description="Maximum drawdown percentage")
    volatility: Optional[float] = Field(None, ge=0.0, description="Annualized volatility")
    beta: Optional[float] = Field(None, description="Beta relative to market")
    alpha: Optional[float] = Field(None, description="Alpha (excess return)")
    var_95: Optional[float] = Field(None, description="Value at Risk (95% confidence)")
    expected_return: Optional[float] = Field(None, description="Expected annual return")
    recommendation: Optional[Literal["BUY", "HOLD", "SELL"]] = Field(None, description="Investment recommendation")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recommendation confidence")


class StockTechnicalAnalysis(BaseModel):
    """Technical analysis output for stock technical detail task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    company_name: str = Field(description="Full company name")
    analysis_date: date = Field(description="Date of analysis")

    # Financial fundamentals
    revenue: Optional[float] = Field(None, gt=0, description="Annual revenue in USD")
    revenue_growth: Optional[float] = Field(None, description="Revenue growth rate")
    net_income: Optional[float] = Field(None, description="Net income in USD")
    profit_margin: Optional[float] = Field(None, ge=-100.0, le=100.0, description="Profit margin percentage")
    roe: Optional[float] = Field(None, description="Return on equity")
    debt_to_equity: Optional[float] = Field(None, ge=0.0, description="Debt-to-equity ratio")

    # Technical indicators
    technical_indicators: Optional[TechnicalIndicators] = Field(None, description="Technical indicators")

    # Quantitative analysis
    quantitative_metrics: Optional[QuantitativeMetrics] = Field(None, description="Quantitative metrics")

    # 10-K insights
    ten_k_insights: list[TenKInsight] = Field(default_factory=list, description="10-K filing insights")

    # Competitive analysis
    competitive_advantages: list[str] = Field(default_factory=list, description="Competitive advantages", max_length=10)
    key_risks: list[str] = Field(default_factory=list, description="Key risk factors", max_length=10)

    # Overall assessment
    investment_thesis: str = Field(description="Investment thesis summary", min_length=50)
    price_target: Optional[float] = Field(None, gt=0, description="12-month price target")


class StockRiskProfile(BaseModel):
    """Risk assessment output for stock risk assessment task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    ticker: str = Field(min_length=1, max_length=10)
    company_name: str = Field(description="Full company name")
    assessment_date: date = Field(description="Date of risk assessment")

    # Standardized risk assessment
    risk_assessment: RiskAssessmentStandardized = Field(description="Standardized risk assessment")

    # Risk categories
    regulatory_risk: str = Field(description="Regulatory risk assessment", min_length=20)
    financial_risk: str = Field(description="Financial stability risk assessment", min_length=20)
    valuation_risk: str = Field(description="Valuation risk assessment", min_length=20)
    competitive_risk: str = Field(description="Competitive positioning risk assessment", min_length=20)
    governance_risk: str = Field(description="Corporate governance risk assessment", min_length=20)

    # Quantitative risk metrics
    quantitative_risk_metrics: dict[str, Any] = Field(default_factory=dict, description="Quantitative risk metrics (VaR, drawdown, etc.)")

    # Market sentiment
    sentiment: Optional[MarketSentiment] = Field(None, description="Market sentiment analysis")

    # Risk mitigation
    risk_mitigation_strategies: list[str] = Field(default_factory=list, description="Risk mitigation strategies", max_length=10)

    # Overall risk summary
    risk_summary: str = Field(description="Overall risk summary", min_length=50)
