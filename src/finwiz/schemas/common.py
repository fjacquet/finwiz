from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["Low", "Medium", "High", "Very High"]


class AssetClass(StrEnum):
    """Asset class enumeration for type-safe asset classification."""

    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"

    @classmethod
    def from_string(cls, value: str) -> AssetClass:
        """Convert string to AssetClass with validation."""
        try:
            return cls(value.lower())
        except ValueError:
            valid = [e.value for e in cls]
            raise ValueError(f"Invalid asset_class: {value}. Must be one of: {valid}") from None


class RiskAssessmentStandardized(BaseModel):
    """
    Standardized risk assessment across Stock/ETF/Crypto on a 0-5 scale.

    - score: 0 (lowest) .. 5 (highest)
    - level: human-friendly label mapped from score
    - risk_factors: up to 10 concise reasons
    - scale: reserved for future alternate encodings
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scale: Literal["0_5", "L_M_H", "L_M_H_VH"] = "0_5"
    score: float = Field(ge=0.0, le=5.0)
    level: RiskLevel
    risk_factors: list[str] = Field(default_factory=list, max_length=10)
