"""
Data models for portfolio holdings processing.

This module contains Pydantic models and dataclasses for portfolio processing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from finwiz.schemas.portfolio_review import HoldingDecision

AssetClass = Literal["stock", "etf", "crypto"]


@dataclass
class RawHolding:
    """Raw holding data from CSV."""

    asset_class: AssetClass
    name: str
    ticker: str
    currency: str
    source_file: str
    line_number: int


@dataclass
class ProcessingResult:
    """Result of processing a single holding."""

    holding: RawHolding
    decision: HoldingDecision | None
    success: bool
    validation_status: str
    error_message: str | None = None


@dataclass
class ProcessingSummary:
    """Summary of holdings processing."""

    total_holdings: int
    processed_successfully: int
    processed_with_warnings: int
    failed_to_process: int
    excluded_holdings: list[tuple[str, str]]  # (ticker, reason)
    by_asset_class: dict[str, int]
    validation_failures: list[tuple[str, str]]  # (ticker, reason)
