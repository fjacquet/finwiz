from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from .common import RiskAssessmentStandardized
from .crypto import CryptoThesis
from .etf import ETFFactsheet, ETFTopHolding
from .stock import MarketSentiment, TenKInsight


class ReporterInput(BaseModel):
    """
    Aggregate input for the final tool-less reporter.

    Only validated, structured data should reach the reporter. Extra keys are
    forbidden to prevent silent schema drift.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    # stock
    schema_version: int = 1
    ten_k_insights: list[TenKInsight] = Field(default_factory=list)
    stock_sentiments: list[MarketSentiment] = Field(default_factory=list)
    stock_risks: list[RiskAssessmentStandardized] = Field(default_factory=list)

    # etf (to be specialized later)
    etf_factsheets: list[ETFFactsheet] = Field(default_factory=list)
    etf_holdings: list[ETFTopHolding] = Field(default_factory=list)
    etf_risks: list[RiskAssessmentStandardized] = Field(default_factory=list)

    # crypto (to be specialized later)
    crypto_theses: list[CryptoThesis] = Field(default_factory=list)
    crypto_risks: list[RiskAssessmentStandardized] = Field(default_factory=list)

    # meta
    as_of: date
