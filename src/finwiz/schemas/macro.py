"""Macroeconomic data schemas for v4 Data Intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# Yield curve regime classification based on 10Y-2Y spread
YieldCurveRegime = Literal["inverted", "flat", "normal", "steep", "unknown"]


class MacroSnapshot(BaseModel):
    """Session-level macroeconomic data snapshot.

    Collected ONCE per analysis run and shared across all holdings.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    fed_rate: float | None = Field(None, description="Federal Funds Rate (%)")
    cpi_yoy: float | None = Field(None, description="CPI Year-over-Year change (%)")
    unemployment_rate: float | None = Field(None, description="Unemployment Rate (%)")
    gdp_growth: float | None = Field(None, description="Real GDP Growth Rate (%)")
    treasury_10y: float | None = Field(None, description="10-Year Treasury Yield (%)")
    treasury_2y: float | None = Field(None, description="2-Year Treasury Yield (%)")
    yield_curve_spread: float | None = Field(None, description="10Y-2Y Treasury spread (%)")
    vix: float | None = Field(None, description="VIX Volatility Index")
    fear_greed_index: int | None = Field(None, ge=0, le=100, description="CNN Fear & Greed Index (0-100)")
    fear_greed_label: Literal["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"] | None = Field(None, description="Fear & Greed classification")
    fetched_at: datetime = Field(default_factory=datetime.now, description="When snapshot was collected")
    data_sources: dict[str, str] = Field(default_factory=dict, description="Field → data source mapping (e.g. 'fed_rate' → 'FRED:FEDFUNDS')")

    def is_recession_signal(self) -> bool:
        """Check if macro data suggests recession risk (inverted yield curve)."""
        if self.yield_curve_spread is not None and self.yield_curve_spread < 0:
            return True
        return False

    def get_market_regime(self) -> str:
        """Classify current market regime from VIX and yield curve."""
        if self.vix is None:
            return "unknown"
        if self.vix > 30:
            return "high_volatility"
        if self.vix > 20:
            return "elevated_volatility"
        if self.is_recession_signal():
            return "recession_risk"
        return "normal"


class MacroScore(BaseModel):
    """Computed macro adjustment score for a single holding.

    Produced by MacroScorer, consumed by DeepAnalysisScorer as an additive overlay.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(..., description="Ticker symbol this score applies to")
    macro_score: float | None = Field(None, ge=-1.0, le=1.0, description="Computed macro adjustment score")
    yield_curve_regime: YieldCurveRegime | None = Field(None, description="Classified yield curve regime")
    market_regime: str | None = Field(None, description="Market regime from VIX/yield curve")
    confidence: float | None = Field(None, ge=0.0, le=1.0, description="Data completeness confidence (0-1)")
    asset_class: str | None = Field(None, description="Asset class used for sensitivity scaling")
    sensitivity_applied: float | None = Field(None, description="Sensitivity coefficient applied")
    details: dict[str, Any] = Field(default_factory=dict, description="Full scoring breakdown")
