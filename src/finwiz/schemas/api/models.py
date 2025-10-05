"""
API schemas for FinWiz FastAPI endpoints.

This module contains Pydantic models for API request/response handling,
including validation, serialization, and documentation.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from finwiz.schemas.common import RiskAssessmentStandardized
from finwiz.schemas.investment_discovery import APlusAnalysis, InvestmentCandidate
from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration, RebalancingResult


# Base API Models
class APIResponse(BaseModel):
    """Base API response model."""

    success: bool = Field(..., description="Whether the request was successful")
    message: str | None = Field(None, description="Response message")
    timestamp: str = Field(..., description="Response timestamp")

    model_config = ConfigDict(extra="forbid")


class ErrorResponse(APIResponse):
    """Error response model."""

    success: bool = Field(default=False, description="Always false for error responses")
    error_code: str = Field(..., description="Error code identifier")
    error_details: dict[str, Any] | None = Field(None, description="Additional error details")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""

    error_code: str = Field(default="VALIDATION_ERROR", description="Validation error code")
    field_errors: dict[str, list[str]] = Field(..., description="Field-specific validation errors")


# Portfolio Rebalancing API Models
class RebalancingRequest(BaseModel):
    """Request model for portfolio rebalancing analysis."""

    portfolio_config: PortfolioConfiguration = Field(..., description="Portfolio configuration")
    available_capital: float = Field(default=0.0, description="Available capital for rebalancing")

    model_config = ConfigDict(extra="forbid")


class RebalancingResponse(APIResponse):
    """Response model for portfolio rebalancing analysis."""

    result: RebalancingResult | None = Field(None, description="Rebalancing analysis result")


# Investment Discovery API Models
class DiscoveryRequest(BaseModel):
    """Request model for investment discovery analysis."""

    asset_class: Literal["stock", "etf", "crypto"] = Field(..., description="Asset class to discover")
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = Field(
        default="moderate", description="Risk tolerance level"
    )
    investment_amount: float = Field(..., gt=0, description="Investment amount")
    time_horizon: Literal["short", "medium", "long"] = Field(default="medium", description="Investment time horizon")
    exclude_sectors: list[str] = Field(default_factory=list, description="Sectors to exclude")
    include_esg: bool = Field(default=False, description="Include ESG considerations")

    model_config = ConfigDict(extra="forbid")


class DiscoveryResponse(APIResponse):
    """Response model for investment discovery analysis."""

    candidates: list[InvestmentCandidate] = Field(default_factory=list, description="Investment candidates")
    analysis: APlusAnalysis | None = Field(None, description="Detailed analysis")
    total_candidates: int = Field(..., description="Total number of candidates found")


# Portfolio Analysis API Models
class PortfolioAnalysisRequest(BaseModel):
    """Request model for portfolio analysis."""

    holdings: dict[str, float] = Field(..., description="Current portfolio holdings (symbol: weight)")
    benchmark: str | None = Field(None, description="Benchmark ticker for comparison")
    analysis_period: Literal["1m", "3m", "6m", "1y", "2y", "5y"] = Field(default="1y", description="Analysis period")
    include_risk_assessment: bool = Field(default=True, description="Include risk assessment")
    include_performance_attribution: bool = Field(default=True, description="Include performance attribution")

    model_config = ConfigDict(extra="forbid")


class PortfolioAnalysisResponse(APIResponse):
    """Response model for portfolio analysis."""

    risk_assessment: RiskAssessmentStandardized | None = Field(None, description="Risk assessment")
    performance_metrics: dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    attribution_analysis: dict[str, Any] = Field(default_factory=dict, description="Performance attribution")
    recommendations: list[str] = Field(default_factory=list, description="Portfolio recommendations")


# Stock Analysis API Models
class StockAnalysisRequest(BaseModel):
    """Request model for stock analysis."""

    ticker: str = Field(..., description="Stock ticker symbol")
    analysis_type: Literal["fundamental", "technical", "comprehensive"] = Field(
        default="comprehensive", description="Type of analysis to perform"
    )
    include_peer_comparison: bool = Field(default=True, description="Include peer comparison")
    include_sector_analysis: bool = Field(default=True, description="Include sector analysis")

    model_config = ConfigDict(extra="forbid")


class StockAnalysisResponse(APIResponse):
    """Response model for stock analysis."""

    ticker: str = Field(..., description="Analyzed ticker symbol")
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    target_price: float | None = Field(None, description="Price target")
    risk_score: int = Field(..., ge=1, le=10, description="Risk score (1-10)")
    analysis_summary: str = Field(..., description="Analysis summary")
    key_metrics: dict[str, float] = Field(default_factory=dict, description="Key financial metrics")


# ETF Analysis API Models
class ETFAnalysisRequest(BaseModel):
    """Request model for ETF analysis."""

    ticker: str = Field(..., description="ETF ticker symbol")
    include_holdings_analysis: bool = Field(default=True, description="Include holdings analysis")
    include_expense_analysis: bool = Field(default=True, description="Include expense analysis")
    benchmark_comparison: bool = Field(default=True, description="Compare against benchmark")

    model_config = ConfigDict(extra="forbid")


class ETFAnalysisResponse(APIResponse):
    """Response model for ETF analysis."""

    ticker: str = Field(..., description="Analyzed ETF ticker")
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    expense_ratio: float = Field(..., description="ETF expense ratio")
    tracking_error: float | None = Field(None, description="Tracking error vs benchmark")
    top_holdings: list[dict[str, Any]] = Field(default_factory=list, description="Top holdings")
    risk_assessment: RiskAssessmentStandardized | None = Field(None, description="Risk assessment")


# Crypto Analysis API Models
class CryptoAnalysisRequest(BaseModel):
    """Request model for cryptocurrency analysis."""

    symbol: str = Field(..., description="Cryptocurrency symbol")
    include_defi_metrics: bool = Field(default=True, description="Include DeFi metrics")
    include_on_chain_analysis: bool = Field(default=True, description="Include on-chain analysis")
    include_sentiment_analysis: bool = Field(default=True, description="Include sentiment analysis")

    model_config = ConfigDict(extra="forbid")


class CryptoAnalysisResponse(APIResponse):
    """Response model for cryptocurrency analysis."""

    symbol: str = Field(..., description="Analyzed cryptocurrency symbol")
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(..., description="Investment recommendation")
    risk_score: int = Field(..., ge=1, le=10, description="Risk score (1-10)")
    market_cap_rank: int | None = Field(None, description="Market cap ranking")
    volatility_score: float = Field(..., ge=0, le=1, description="Volatility score")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Sentiment score")


# Monitoring API Models
class MonitoringAlert(BaseModel):
    """Monitoring alert model."""

    alert_id: str = Field(..., description="Unique alert identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: Literal["INFO", "WARNING", "ERROR", "CRITICAL"] = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: str = Field(..., description="Alert timestamp")
    portfolio_id: str | None = Field(None, description="Associated portfolio ID")
    ticker: str | None = Field(None, description="Associated ticker symbol")

    model_config = ConfigDict(extra="forbid")


class MonitoringStatusRequest(BaseModel):
    """Request model for monitoring status."""

    portfolio_id: str | None = Field(None, description="Portfolio ID to check")
    alert_types: list[str] = Field(default_factory=list, description="Specific alert types to check")
    severity_filter: list[str] = Field(default_factory=list, description="Severity levels to include")
    time_range: Literal["1h", "6h", "24h", "7d", "30d"] = Field(default="24h", description="Time range for alerts")

    model_config = ConfigDict(extra="forbid")


class MonitoringStatusResponse(APIResponse):
    """Response model for monitoring status."""

    active_alerts: list[MonitoringAlert] = Field(default_factory=list, description="Active alerts")
    alert_summary: dict[str, int] = Field(default_factory=dict, description="Alert count by severity")
    system_health: Literal["HEALTHY", "WARNING", "UNHEALTHY", "CRITICAL"] = Field(..., description="Overall system health")
    last_check: str = Field(..., description="Last monitoring check timestamp")


# Feedback API Models
class FeedbackSubmissionRequest(BaseModel):
    """Request model for submitting feedback."""

    recommendation_id: str = Field(..., description="ID of the recommendation being reviewed")
    user_id: str = Field(..., description="User identifier")
    feedback_type: Literal["rating", "comment", "outcome"] = Field(..., description="Type of feedback")
    rating: int | None = Field(None, ge=1, le=5, description="Rating (1-5 stars)")
    comment: str | None = Field(None, description="Text comment")
    outcome: Literal["accepted", "rejected", "modified"] | None = Field(None, description="Recommendation outcome")
    performance_data: dict[str, float] | None = Field(None, description="Performance tracking data")

    model_config = ConfigDict(extra="forbid")


class FeedbackSubmissionResponse(APIResponse):
    """Response model for feedback submission."""

    feedback_id: str = Field(..., description="Unique feedback identifier")
    processed: bool = Field(..., description="Whether feedback was processed successfully")


# Batch Processing API Models
class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""

    tickers: list[str] = Field(..., min_length=1, max_length=100, description="List of tickers to analyze")
    analysis_type: Literal["stock", "etf", "crypto"] = Field(..., description="Type of analysis")
    priority: Literal["low", "normal", "high"] = Field(default="normal", description="Processing priority")
    callback_url: str | None = Field(None, description="Callback URL for results")
    user_id: str = Field(..., description="User identifier")

    model_config = ConfigDict(extra="forbid")


class BatchAnalysisResponse(APIResponse):
    """Response model for batch analysis."""

    batch_id: str = Field(..., description="Unique batch identifier")
    estimated_completion: str = Field(..., description="Estimated completion time")
    status_url: str = Field(..., description="URL to check batch status")


class BatchStatusResponse(APIResponse):
    """Response model for batch status check."""

    batch_id: str = Field(..., description="Batch identifier")
    status: Literal["queued", "processing", "completed", "failed"] = Field(..., description="Batch status")
    progress: float = Field(..., ge=0, le=1, description="Completion progress (0-1)")
    completed_count: int = Field(..., description="Number of completed analyses")
    total_count: int = Field(..., description="Total number of analyses")
    results_url: str | None = Field(None, description="URL to download results")
    error_message: str | None = Field(None, description="Error message if batch failed")


# Health Check API Models
class HealthCheckResponse(APIResponse):
    """Response model for health check endpoint."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Service health status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Uptime in seconds")
    dependencies: dict[str, str] = Field(default_factory=dict, description="Dependency health status")
    metrics: dict[str, float] = Field(default_factory=dict, description="Performance metrics")


# Configuration API Models
class ConfigurationUpdateRequest(BaseModel):
    """Request model for updating configuration."""

    config_section: str = Field(..., description="Configuration section to update")
    config_data: dict[str, Any] = Field(..., description="Configuration data")
    validate_only: bool = Field(default=False, description="Only validate, don't apply changes")

    model_config = ConfigDict(extra="forbid")


class ConfigurationUpdateResponse(APIResponse):
    """Response model for configuration update."""

    validation_passed: bool = Field(..., description="Whether validation passed")
    changes_applied: bool = Field(..., description="Whether changes were applied")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors")
    restart_required: bool = Field(default=False, description="Whether service restart is required")


# Search and Discovery API Models
class SearchRequest(BaseModel):
    """Request model for search functionality."""

    query: str = Field(..., min_length=1, description="Search query")
    search_type: Literal["ticker", "company", "sector", "all"] = Field(default="all", description="Type of search")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    filters: dict[str, Any] = Field(default_factory=dict, description="Additional search filters")

    model_config = ConfigDict(extra="forbid")


class SearchResult(BaseModel):
    """Individual search result."""

    ticker: str = Field(..., description="Ticker symbol")
    name: str = Field(..., description="Company/asset name")
    asset_type: Literal["stock", "etf", "crypto"] = Field(..., description="Type of asset")
    sector: str | None = Field(None, description="Sector classification")
    market_cap: float | None = Field(None, description="Market capitalization")
    relevance_score: float = Field(..., ge=0, le=1, description="Search relevance score")

    model_config = ConfigDict(extra="forbid")


class SearchResponse(APIResponse):
    """Response model for search results."""

    results: list[SearchResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., description="Total number of matching results")
    query_time: float = Field(..., description="Query execution time in seconds")
    suggestions: list[str] = Field(default_factory=list, description="Search suggestions")
