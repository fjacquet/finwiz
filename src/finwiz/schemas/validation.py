"""
Validated ticker payload emitted by validation tools.

This model is referenced by YAML prompts and used for JSON Schema export.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidatedTicker(BaseModel):
    """
    Strict, minimal contract for a validated symbol.

    Fields mirror `TickerExistenceValidationTool` output (see
    `src/finwiz/tools/ticker_validation_tool.py`).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=1, max_length=15)
    asset_class: Literal["stock", "etf", "crypto"]
    valid: bool
    reason: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
