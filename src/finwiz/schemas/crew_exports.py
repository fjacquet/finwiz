"""
Pydantic export schemas for all FinWiz crews.

This module defines validated export objects that each crew generates and saves to JSON.
These schemas follow the AI Minimalism principle: crews generate structured JSON exports,
and Python templates (Jinja2) render HTML reports from these exports.

All schemas use strict validation with extra='forbid' to ensure data quality.
"""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Import existing schemas from finwiz.schemas
from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.crypto import CryptoThesis
from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
from finwiz.schemas.portfolio_review import Grade
from finwiz.schemas.python_analysis import PythonDeepAnalysisResult
from finwiz.schemas.rebalancing import TradeRecommendation
from finwiz.schemas.stock import TenKInsight


class CrewExportBase(BaseModel):
    """Base schema for all crew exports with common fields."""

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    crew_name: str = Field(..., description="Name of the crew that generated this export")
    ticker: str = Field(..., description="Asset ticker symbol (or 'N/A' for portfolio-level analysis)")
    asset_class: str = Field(..., pattern="^(stock|etf|crypto|portfolio|N/A)$", description="Asset class")
    session_id: str = Field(..., description="Flow session identifier for tracking")
    analysis_date: datetime = Field(default_factory=datetime.now, description="When the analysis was performed")


class StockCrewExport(CrewExportBase):
    """
    Export schema for Stock Crew analysis.

    Contains fundamental analysis, risk assessment, technical indicators,
    and investment recommendations for a stock.
    """

    crew_name: str = Field(default="stock_crew")
    asset_class: str = Field(default="stock")

    # Analysis Results
    fundamental_analysis: TenKInsight = Field(..., description="10-K fundamental analysis insights")
    risk_assessment: RiskAssessmentStandardized = Field(..., description="Standardized risk assessment")
    technical_indicators: dict[str, Any] = Field(
        default_factory=dict, description="Technical analysis indicators (RSI, MACD, etc.)"
    )

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Recommendations
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed rationale for recommendation")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class ETFCrewExport(CrewExportBase):
    """
    Export schema for ETF Crew analysis.

    Contains factsheet data, holdings analysis, cost metrics,
    and investment recommendations for an ETF.
    """

    crew_name: str = Field(default="etf_crew")
    asset_class: str = Field(default="etf")

    # Analysis Results
    factsheet: ETFFactsheet = Field(..., description="ETF factsheet with key metrics")
    top_holdings: list[ETFTopHolding] = Field(default_factory=list, description="Top holdings with weights")
    risk_assessment: RiskAssessmentStandardized = Field(..., description="Standardized risk assessment")

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Cost Analysis
    expense_ratio: float = Field(..., ge=0.0, le=5.0, description="Total expense ratio (percentage)")
    tracking_error: Optional[float] = Field(None, description="Tracking error vs benchmark (if applicable)")

    # Recommendations
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed rationale for recommendation")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class CryptoCrewExport(CrewExportBase):
    """
    Export schema for Crypto Crew analysis.

    Contains investment thesis, risk assessment, technical analysis,
    and recommendations for a cryptocurrency.
    """

    crew_name: str = Field(default="crypto_crew")
    asset_class: str = Field(default="crypto")

    # Analysis Results
    thesis: CryptoThesis = Field(..., description="Investment thesis with key points")
    risk_assessment: RiskAssessmentStandardized = Field(..., description="Standardized risk assessment")
    technical_analysis: dict[str, Any] = Field(default_factory=dict, description="Technical analysis indicators and patterns")

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Volatility Metrics
    volatility_30d: float = Field(..., ge=0.0, description="30-day volatility (annualized)")
    max_drawdown: float = Field(..., le=0.0, description="Maximum drawdown (negative percentage)")

    # Recommendations
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed rationale for recommendation")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class DeepAnalysisCrewExport(CrewExportBase):
    """
    Export schema for Deep Analysis Crew.

    Contains comprehensive analysis for underperforming holdings (grade < B)
    with detailed investigation and recommendations.
    """

    crew_name: str = Field(default="deep_analysis_crew")

    # Comprehensive Analysis
    detailed_analysis: dict[str, Any] = Field(
        default_factory=dict, description="Detailed analysis findings across multiple dimensions"
    )
    risk_assessment: RiskAssessmentStandardized = Field(..., description="Standardized risk assessment")

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    grade: Grade = Field(..., description="Letter grade (A+ to F)")

    # Recommendations
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in recommendation")
    rationale: str = Field(..., min_length=50, description="Detailed rationale for recommendation")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class DiscoveryOpportunity(BaseModel):
    """Single A+ investment opportunity discovered through screening."""

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    ticker: str = Field(..., description="Investment ticker symbol")
    name: str = Field(..., description="Full name of the investment")
    asset_class: Literal["stock", "etf", "crypto"] = Field(..., description="Asset class")
    composite_score: float = Field(..., ge=0.7, le=1.0, description="Composite score (A+ threshold: 0.7+)")
    grade: Grade = Field(default="A+", description="Letter grade (should be A+ for discoveries)")
    rationale: str = Field(..., min_length=50, description="Why this is an A+ opportunity")


class DiscoveryCrewExport(CrewExportBase):
    """
    Export schema for Investment Discovery Crew.

    Contains A+ investment opportunities discovered through market screening,
    with criteria and context for the discoveries.
    """

    crew_name: str = Field(default="discovery_crew")
    ticker: str = Field(default="N/A", description="Not applicable for discovery (portfolio-level)")
    asset_class: str = Field(default="N/A", description="Multiple asset classes analyzed")

    # Discovery Results
    opportunities: list[DiscoveryOpportunity] = Field(
        default_factory=list, max_length=10, description="Top A+ opportunities discovered"
    )
    screening_criteria: dict[str, Any] = Field(default_factory=dict, description="Criteria used for A+ screening")
    market_context: str = Field(..., min_length=50, description="Market conditions during discovery")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class RebalancingCrewExport(CrewExportBase):
    """
    Export schema for Portfolio Rebalancing Crew.

    This crew receives ALL analysis results as inputs:
    - Current holdings (stock/etf/crypto exports)
    - Deep analysis results (detailed grades)
    - Discovery opportunities (A+ alternatives)

    It proposes optimal portfolio allocation and required trades.
    """

    crew_name: str = Field(default="rebalancing_crew")
    ticker: str = Field(default="N/A", description="Not applicable for rebalancing (portfolio-level)")
    asset_class: str = Field(default="portfolio", description="Portfolio-level analysis")

    # Input Summary (what the crew saw)
    holdings_analyzed: int = Field(..., ge=0, description="Number of current holdings analyzed")
    deep_analyses_reviewed: int = Field(..., ge=0, description="Number of deep analyses reviewed")
    opportunities_discovered: int = Field(..., ge=0, description="Number of A+ opportunities found")

    # Current State
    current_allocation: dict[str, float] = Field(
        default_factory=dict, description="Current portfolio allocation by ticker (percentages)"
    )
    current_total_value: float = Field(..., gt=0, description="Current total portfolio value")

    # Optimization Results
    target_allocation: dict[str, float] = Field(default_factory=dict, description="Recommended allocation by ticker (percentages)")
    trades_required: list[TradeRecommendation] = Field(default_factory=list, description="Specific trade recommendations")

    # Performance Metrics
    expected_return: float = Field(..., description="Expected annual return (percentage)")
    expected_risk: float = Field(..., ge=0.0, description="Expected volatility (percentage)")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return metric")

    # Improvement Analysis
    improvement_summary: str = Field(..., min_length=50, description="How rebalancing improves the portfolio")
    risk_reduction: float = Field(..., description="Expected risk reduction (percentage points)")
    return_improvement: float = Field(..., description="Expected return improvement (percentage points)")

    # Metadata
    data_sources: list[str] = Field(default_factory=list, description="Data sources used in analysis")
    report_html_path: str = Field(..., description="Path to generated HTML report")
    report_json_path: str = Field(..., description="Path to this JSON export file")


class ConsolidatedReportExport(BaseModel):
    """
    Consolidated export from all SME crews.

    This is the aggregated result of all crew analyses, created by Python
    consolidation (NO AI). It serves as input to the final report template.
    """

    model_config = {"extra": "forbid", "str_strip_whitespace": True}

    session_id: str = Field(..., description="Flow session identifier")
    consolidation_date: datetime = Field(default_factory=datetime.now, description="When consolidation occurred")

    # SME Crew Results
    stock_analyses: list[StockCrewExport] = Field(default_factory=list, description="All stock analysis results")
    etf_analyses: list[ETFCrewExport] = Field(default_factory=list, description="All ETF analysis results")
    crypto_analyses: list[CryptoCrewExport] = Field(default_factory=list, description="All crypto analysis results")
    deep_analyses: list[DeepAnalysisCrewExport | PythonDeepAnalysisResult] = Field(
        default_factory=list, description="All deep analysis results (CrewAI or Python)"
    )
    discovery_results: Optional[DiscoveryCrewExport] = Field(None, description="Investment discovery results (single)")
    rebalancing_results: Optional[RebalancingCrewExport] = Field(None, description="Portfolio rebalancing results (single)")

    # Additional Data (optional, set by consolidator)
    portfolio_data: Optional[dict[str, Any]] = Field(None, description="Portfolio review data")
    aplus_opportunities: Optional[dict[str, Any]] = Field(None, description="A+ investment opportunities")
    backtesting_data: Optional[dict[str, Any]] = Field(None, description="Backtesting results")

    # Execution Metadata
    crew_execution_status: dict[str, str] = Field(
        default_factory=dict, description="Execution status for each crew (completed/failed)"
    )
    total_execution_time: float = Field(..., ge=0.0, description="Total execution time in seconds")

    # Error Tracking
    errors: list[str] = Field(default_factory=list, description="Any errors encountered during execution")
