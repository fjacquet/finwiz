"""Result models for deterministic portfolio valuation.

Produced by `finwiz.scoring.portfolio_valuation.value_holdings`. Pure data —
no AI, no network. Models live here per the schemas-in-`schemas/` rule.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HoldingValuation(BaseModel):
    """Per-holding valuation output. All money fields optional (graceful degradation)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str
    quantity: float | None = None
    native_currency: str | None = None
    native_value: float | None = None
    eur_value: float | None = None
    weight: float | None = Field(default=None, ge=0.0, le=1.0)


class ValuationResult(BaseModel):
    """Portfolio-level valuation: per-ticker breakdown, total EUR, coverage."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    per_ticker: dict[str, HoldingValuation] = Field(default_factory=dict)
    total_value_eur: float | None = None
    priced_count: int = 0
    total_count: int = 0
    coverage_note: str = ""
