"""
Session management schemas for persistent financial planning.

This module defines the data models for managing financial planning sessions,
including the FinancialPlan model and related structures for session persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskAssessmentStandardized
from .crypto import CryptoThesis
from .etf import ETFFactsheet, ETFTopHolding
from .stock import MarketSentiment, TenKInsight


class AnalysisRecord(BaseModel):
    """Record of a single analysis run within a financial plan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    timestamp: datetime
    analysis_type: str = Field(..., description="Type of analysis performed (e.g., 'full_analysis', 'portfolio_review')")
    ten_k_insights: list[TenKInsight] = Field(default_factory=list)
    market_sentiments: list[MarketSentiment] = Field(default_factory=list)
    etf_factsheets: list[ETFFactsheet] = Field(default_factory=list)
    etf_holdings: list[ETFTopHolding] = Field(default_factory=list)
    crypto_theses: list[CryptoThesis] = Field(default_factory=list)
    risk_assessments: list[RiskAssessmentStandardized] = Field(default_factory=list)
    portfolio_data: dict[str, Any] = Field(default_factory=dict)


class ClientProfile(BaseModel):
    """Client profile information extracted from financial plan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    investment_horizon: Optional[str] = None
    monthly_budget: Optional[str] = None
    risk_tolerance: Optional[str] = None
    currency: str = Field(default="CHF")


class FinancialPlan(BaseModel):
    """
    Complete financial plan model for session persistence.

    This model represents the state of a financial planning session,
    including client information, analysis history, and current recommendations.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    plan_id: str = Field(..., description="Unique identifier for the financial plan")
    created_at: datetime
    last_updated: datetime

    # Client information
    client_profile: ClientProfile = Field(default_factory=ClientProfile)

    # Analysis history
    analysis_history: list[AnalysisRecord] = Field(default_factory=list)

    # Current state
    current_portfolio_data: dict[str, Any] = Field(default_factory=dict)
    current_recommendations: dict[str, Any] = Field(default_factory=dict)

    # Metadata
    report_language: str = Field(default="fr")
    version: int = Field(default=1)


class SessionMetadata(BaseModel):
    """Metadata about a session file."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    file_path: str
    file_size: int
    last_modified: datetime
    is_corrupted: bool = False
    corruption_reason: Optional[str] = None
