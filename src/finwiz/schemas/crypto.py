from __future__ import annotations

from datetime import date
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .common import RiskAssessmentStandardized


class CryptoThesis(BaseModel):
    """Crypto investment thesis bullets with optional citations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1

    symbol: str = Field(min_length=2, max_length=10, description="Crypto symbol, e.g., BTC")
    thesis_bullets: list[str] = Field(default_factory=list, max_length=20)
    references: list[str] = Field(default_factory=list, description="List of reference URLs")

    @field_validator("references")
    @classmethod
    def validate_references(cls, v: list[str]) -> list[str]:
        """Validate that references are valid URLs."""
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

        for url in v:
            if not url_pattern.match(url):
                raise ValueError(f"Invalid URL format: {url}")
        return v


# Alias via type for clarity in exports
CryptoRisk = RiskAssessmentStandardized


class CryptoCandidate(BaseModel):
    """Individual cryptocurrency candidate from market analysis."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=2, max_length=10, description="Crypto symbol (e.g., BTC, ETH)")
    name: str = Field(description="Full cryptocurrency name")
    market_cap: Optional[float] = Field(None, gt=0, description="Market capitalization in USD")
    current_price: Optional[float] = Field(None, gt=0, description="Current price in USD")
    volume_24h: Optional[float] = Field(None, ge=0, description="24-hour trading volume in USD")
    price_change_24h: Optional[float] = Field(None, description="24-hour price change percentage")
    selection_rationale: str = Field(description="Why this crypto was selected", min_length=20)
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in selection")


class CryptoMarketAnalysis(BaseModel):
    """Market analysis output for crypto market analysis task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    analysis_date: date = Field(description="Date of the analysis")
    market_sentiment: Literal["bullish", "bearish", "neutral", "mixed"] = Field(description="Overall crypto market sentiment")
    key_trends: list[str] = Field(description="Key market trends identified", max_length=20)
    emerging_opportunities: list[str] = Field(description="Emerging opportunities in crypto space", max_length=15)
    regulatory_developments: list[str] = Field(description="Recent regulatory developments", default_factory=list, max_length=10)
    adoption_trends: list[str] = Field(description="Blockchain adoption trends", default_factory=list, max_length=10)
    candidates: list[CryptoCandidate] = Field(description="Top cryptocurrency candidates", max_length=20)
    data_sources: list[str] = Field(description="Data sources used", default_factory=list)


class CryptoTechnicalIndicators(BaseModel):
    """Technical indicators for a cryptocurrency."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=2, max_length=10)
    rsi: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative Strength Index")
    macd: Optional[float] = Field(None, description="MACD indicator value")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    bollinger_upper: Optional[float] = Field(None, gt=0, description="Bollinger Bands upper bound")
    bollinger_lower: Optional[float] = Field(None, gt=0, description="Bollinger Bands lower bound")
    moving_avg_50: Optional[float] = Field(None, gt=0, description="50-day moving average")
    moving_avg_200: Optional[float] = Field(None, gt=0, description="200-day moving average")
    support_levels: list[float] = Field(default_factory=list, description="Support price levels")
    resistance_levels: list[float] = Field(default_factory=list, description="Resistance price levels")
    volume_trend: Optional[Literal["increasing", "decreasing", "stable"]] = Field(None, description="Volume trend")


class CryptoTechnicalAnalysis(BaseModel):
    """Technical analysis output for crypto technical analysis task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    symbol: str = Field(min_length=2, max_length=10)
    name: str = Field(description="Full cryptocurrency name")
    analysis_date: date = Field(description="Date of analysis")

    # Technical indicators
    technical_indicators: Optional[CryptoTechnicalIndicators] = Field(None, description="Technical indicators")

    # Price analysis
    entry_points: list[float] = Field(default_factory=list, description="Potential entry price points")
    exit_points: list[float] = Field(default_factory=list, description="Potential exit price points")
    price_targets: list[float] = Field(default_factory=list, description="Price targets")

    # Chart patterns
    chart_patterns: list[str] = Field(default_factory=list, description="Identified chart patterns", max_length=10)

    # Trend analysis
    trend_direction: Optional[Literal["bullish", "bearish", "neutral", "mixed"]] = Field(
        None, description="Overall trend direction"
    )
    trend_strength: Optional[Literal["strong", "moderate", "weak"]] = Field(None, description="Trend strength")

    # Overall assessment
    technical_summary: str = Field(description="Technical analysis summary", min_length=50)


class CryptoQuantitativeMetrics(BaseModel):
    """Quantitative analysis metrics for a cryptocurrency."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=2, max_length=10)
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    max_drawdown: Optional[float] = Field(None, le=0.0, description="Maximum drawdown percentage")
    volatility: Optional[float] = Field(None, ge=0.0, description="Annualized volatility")
    var_95: Optional[float] = Field(None, description="Value at Risk (95% confidence)")
    cvar_95: Optional[float] = Field(None, description="Conditional Value at Risk (95% confidence)")
    correlation_with_btc: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Correlation with Bitcoin")
    expected_return: Optional[float] = Field(None, description="Expected annual return")
    recommendation: Optional[Literal["BUY", "HOLD", "SELL"]] = Field(None, description="Investment recommendation")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Recommendation confidence")


class CryptoRiskProfile(BaseModel):
    """Risk assessment output for crypto risk assessment task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    symbol: str = Field(min_length=2, max_length=10)
    name: str = Field(description="Full cryptocurrency name")
    assessment_date: date = Field(description="Date of risk assessment")

    # Standardized risk assessment
    risk_assessment: RiskAssessmentStandardized = Field(description="Standardized risk assessment")

    # Risk categories
    volatility_risk: str = Field(description="Extreme volatility risk assessment", min_length=20)
    regulatory_risk: str = Field(description="Regulatory uncertainty risk assessment", min_length=20)
    technology_risk: str = Field(description="Technology and security risk assessment", min_length=20)
    market_risk: str = Field(description="Market manipulation and liquidity risk assessment", min_length=20)
    adoption_risk: str = Field(description="Adoption and utility risk assessment", min_length=20)

    # Quantitative risk metrics
    quantitative_risk_metrics: dict[str, Any] = Field(
        default_factory=dict, description="Quantitative risk metrics (VaR, CVaR, drawdown, etc.)"
    )

    # Tokenomics
    tokenomics_assessment: Optional[str] = Field(None, description="Tokenomics and supply dynamics assessment")

    # Risk mitigation
    risk_mitigation_strategies: list[str] = Field(default_factory=list, description="Risk mitigation strategies", max_length=10)

    # Overall risk summary
    risk_summary: str = Field(description="Overall risk summary", min_length=50)


class CryptoInvestmentStrategy(BaseModel):
    """Investment strategy output for crypto investment strategy task."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: int = 1
    symbol: str = Field(min_length=2, max_length=10)
    name: str = Field(description="Full cryptocurrency name")
    strategy_date: date = Field(description="Date of strategy creation")

    # Investment thesis
    investment_thesis: CryptoThesis = Field(description="Investment thesis with bullets and references")

    # Risk assessment
    risk_assessment: RiskAssessmentStandardized = Field(description="Standardized risk assessment")

    # Quantitative analysis
    quantitative_metrics: Optional[CryptoQuantitativeMetrics] = Field(None, description="Quantitative analysis metrics")

    # Strategy details
    recommended_allocation: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Recommended portfolio allocation percentage"
    )
    position_sizing: Optional[str] = Field(None, description="Position sizing recommendations")
    entry_strategy: str = Field(description="Entry strategy details", min_length=20)
    exit_strategy: str = Field(description="Exit strategy details", min_length=20)
    time_horizon: Literal["short", "medium", "long"] = Field(description="Investment time horizon")

    # Risk management
    stop_loss_level: Optional[float] = Field(None, gt=0, description="Recommended stop-loss price level")
    take_profit_levels: list[float] = Field(default_factory=list, description="Take-profit price levels")
    risk_management_tactics: list[str] = Field(default_factory=list, description="Risk management tactics", max_length=10)

    # Overall recommendation
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(description="Investment recommendation")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation")
    strategy_summary: str = Field(description="Overall strategy summary", min_length=50)
