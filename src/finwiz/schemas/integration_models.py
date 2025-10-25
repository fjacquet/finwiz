"""
Integration schemas for crew data coordination and metadata tracking.

This module provides the core schemas for the crew data integration system,
including metadata tracking, validation status, and data freshness monitoring.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataSourceType(str, Enum):
    """Types of data sources used by crews."""

    SEC_EDGAR = "SEC_EDGAR"
    YAHOO_FINANCE = "YAHOO_FINANCE"
    ALPHA_VANTAGE = "ALPHA_VANTAGE"
    COINMARKETCAP = "COINMARKETCAP"
    KRAKEN = "KRAKEN"
    INTERNAL = "INTERNAL"
    CACHED = "CACHED"


class DataQuality(str, Enum):
    """Data quality assessment levels."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ValidationStatus(BaseModel):
    """Validation status for crew outputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    is_valid: bool = Field(description="Whether the data passed validation")
    validation_timestamp: datetime = Field(description="When validation was performed")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors encountered")
    validation_warnings: list[str] = Field(default_factory=list, description="List of validation warnings")
    schema_version: int = Field(default=1, description="Schema version used for validation")


class FreshnessStatus(BaseModel):
    """Data freshness information."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    is_fresh: bool = Field(description="Whether data is considered fresh")
    age_hours: float = Field(ge=0.0, description="Age of data in hours")
    max_age_hours: int = Field(default=24, ge=1, description="Maximum acceptable age in hours")
    refresh_recommended: bool = Field(description="Whether refresh is recommended")
    last_updated: datetime = Field(description="When data was last updated")


class DataSource(BaseModel):
    """Information about data sources used by crews."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_type: DataSourceType = Field(description="Type of data source")
    source_url: Optional[str] = Field(default=None, description="URL of the data source")
    accessed_at: datetime = Field(description="When the source was accessed")

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that source_url is a valid URL if provided."""
        if v is None:
            return v

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

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    data_quality: DataQuality = Field(description="Assessed quality of the data")
    response_time_ms: Optional[float] = Field(default=None, ge=0.0, description="Response time in milliseconds")


class CrewOutputMetadata(BaseModel):
    """Base metadata for all crew outputs."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    crew_name: str = Field(min_length=1, description="Name of the crew that generated this output")
    execution_timestamp: datetime = Field(description="When the crew execution completed")
    schema_version: int = Field(default=1, ge=1, description="Version of the output schema")
    validation_status: ValidationStatus = Field(description="Validation results for this output")
    data_sources: list[DataSource] = Field(default_factory=list, description="List of data sources used")
    dependencies_met: bool = Field(description="Whether all required dependencies were available")
    freshness_status: FreshnessStatus = Field(description="Data freshness information")
    execution_duration_seconds: Optional[float] = Field(default=None, ge=0.0, description="How long the crew execution took")
    input_hash: Optional[str] = Field(default=None, description="Hash of input parameters for cache validation")


# Enhanced SEC Citation Models
class SECCitation(BaseModel):
    """Enhanced SEC citation with full provenance tracking."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(min_length=1, max_length=10, description="Stock ticker symbol")
    filing_url: str = Field(description="URL to the SEC filing")
    filed_at: datetime = Field(description="Date when the filing was submitted")

    @field_validator("filing_url")
    @classmethod
    def validate_filing_url(cls, v: str) -> str:
        """Validate that filing_url is a valid URL."""
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

        if not url_pattern.match(v):
            raise ValueError(f"Invalid URL format: {v}")
        return v

    section: str = Field(min_length=1, description="Section of the filing (e.g., Item 1A)")
    excerpt: str = Field(min_length=20, description="Relevant excerpt from the filing")
    sec_citation: str = Field(min_length=1, description="Formatted citation (e.g., '10-K (2024), Item 1A, p. 17')")
    extraction_timestamp: datetime = Field(description="When this data was extracted")
    validation_status: ValidationStatus = Field(description="Validation status of this citation")


# Enhanced Ticker Validation Models
class ValidatedTicker(BaseModel):
    """Ticker validation result with comprehensive metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=1, max_length=10, description="Stock ticker symbol")
    is_valid: bool = Field(description="Whether the ticker is valid")
    validation_source: str = Field(min_length=1, description="Source used for validation")
    validation_timestamp: datetime = Field(description="When validation was performed")
    market: Optional[str] = Field(default=None, description="Market where ticker is traded")
    sector: Optional[str] = Field(default=None, description="Sector classification")
    company_name: Optional[str] = Field(default=None, description="Full company name")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors")
    alternative_suggestions: list[str] = Field(
        default_factory=list, description="Alternative ticker suggestions if validation failed"
    )


class ValidatedETF(BaseModel):
    """ETF validation result with comprehensive metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=1, max_length=15, description="ETF ticker symbol")
    is_valid: bool = Field(description="Whether the ETF ticker is valid")
    validation_source: str = Field(min_length=1, description="Source used for validation")
    validation_timestamp: datetime = Field(description="When validation was performed")
    fund_name: Optional[str] = Field(default=None, description="Full fund name")
    issuer: Optional[str] = Field(default=None, description="Fund issuer/provider")
    expense_ratio: Optional[float] = Field(default=None, ge=0.0, le=5.0, description="Expense ratio percentage")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors")


class ValidatedCrypto(BaseModel):
    """Crypto validation result with comprehensive metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(min_length=2, max_length=10, description="Crypto symbol (e.g., BTC)")
    is_valid: bool = Field(description="Whether the crypto symbol is valid")
    validation_source: str = Field(min_length=1, description="Source used for validation")
    validation_timestamp: datetime = Field(description="When validation was performed")
    full_name: Optional[str] = Field(default=None, description="Full cryptocurrency name")
    market_cap_rank: Optional[int] = Field(default=None, ge=1, description="Market capitalization rank")
    is_active: Optional[bool] = Field(default=None, description="Whether the crypto is actively traded")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors")


# Enhanced Crew Output Schemas
class StockCrewOutput(BaseModel):
    """Enhanced stock crew output with integration metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: CrewOutputMetadata = Field(description="Integration metadata")
    ten_k_insights: list[dict] = Field(
        default_factory=list, description="10-K filing insights (using existing TenKInsight structure)"
    )
    validated_tickers: list[ValidatedTicker] = Field(default_factory=list, description="Validated ticker symbols with metadata")
    market_sentiments: list[dict] = Field(
        default_factory=list, description="Market sentiment data (using existing MarketSentiment structure)"
    )
    risk_assessments: list[dict] = Field(
        default_factory=list, description="Risk assessments (using existing RiskAssessmentStandardized structure)"
    )
    sec_citations: list[SECCitation] = Field(default_factory=list, description="SEC/EDGAR citations with full provenance")


class ETFCrewOutput(BaseModel):
    """Enhanced ETF crew output with integration metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: CrewOutputMetadata = Field(description="Integration metadata")
    validated_etfs: list[ValidatedETF] = Field(default_factory=list, description="Validated ETF symbols with metadata")
    factsheets: list[dict] = Field(default_factory=list, description="ETF factsheets (using existing ETFFactsheet structure)")
    holdings_analysis: list[dict] = Field(
        default_factory=list, description="ETF holdings analysis (using existing ETFTopHolding structure)"
    )
    risk_assessments: list[dict] = Field(
        default_factory=list, description="Risk assessments (using existing RiskAssessmentStandardized structure)"
    )


class CryptoCrewOutput(BaseModel):
    """Enhanced crypto crew output with integration metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: CrewOutputMetadata = Field(description="Integration metadata")
    validated_symbols: list[ValidatedCrypto] = Field(default_factory=list, description="Validated crypto symbols with metadata")
    crypto_theses: list[dict] = Field(
        default_factory=list, description="Crypto investment theses (using existing CryptoThesis structure)"
    )
    risk_assessments: list[dict] = Field(
        default_factory=list, description="Risk assessments (using existing RiskAssessmentStandardized structure)"
    )
    market_analysis: list[dict] = Field(default_factory=list, description="Crypto market analysis data")


# Discovery and Integration-Specific Schemas
class APlusOpportunity(BaseModel):
    """Single A+ opportunity with full data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    symbol: str = Field(..., description="Ticker symbol")
    name: str = Field(..., description="Company/fund name")
    grade: str = Field(..., description="Investment grade (A+, A, etc.)")
    composite_score: float = Field(ge=0.0, le=1.0, description="Composite quality score")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in recommendation")
    risk_score: float = Field(ge=0.0, le=10.0, description="Risk score (0-10 scale)")
    allocation_recommendation: str = Field(default="", description="Allocation guidance")
    replacement_note: str = Field(default="", description="What this might replace")
    rationale: list[str] = Field(default_factory=list, description="Investment rationale points")
    key_metrics: dict[str, Any] = Field(default_factory=dict, description="Key financial metrics")


class APlusOpportunityCollection(BaseModel):
    """Collection of A+ opportunities with metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    etf_opportunities: list[APlusOpportunity] = Field(default_factory=list, description="List of A+ ETF opportunities")
    stock_opportunities: list[APlusOpportunity] = Field(default_factory=list, description="List of A+ stock opportunities")
    crypto_opportunities: list[APlusOpportunity] = Field(default_factory=list, description="List of A+ crypto opportunities")
    discovery_summary: str = Field(min_length=10, description="Summary of the discovery analysis")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score for the opportunities (0.0 to 1.0)")
    validation_timestamp: datetime = Field(description="When the opportunities were validated")
    allocation_recommendations: list[dict] = Field(
        default_factory=list, description="Allocation recommendations for each opportunity"
    )
    replacement_notes: list[str] = Field(default_factory=list, description="Notes about what each opportunity might replace")
    market_context: dict[str, Any] | None = Field(None, description="Market context data (VIX, regime, etc.)")
    backtesting_metrics: dict[str, Any] | None = Field(None, description="Backtesting performance metrics")


class IntegrationErrorType(str, Enum):
    """Types of integration errors."""

    MISSING_DATA = "MISSING_DATA"
    STALE_DATA = "STALE_DATA"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    ACCESS_ERROR = "ACCESS_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    SCHEMA_ERROR = "SCHEMA_ERROR"


class IntegrationError(BaseModel):
    """Detailed error information for integration issues."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    error_type: IntegrationErrorType = Field(description="Type of integration error")
    crew_name: str = Field(min_length=1, description="Name of the crew that encountered the error")
    error_message: str = Field(min_length=1, description="Detailed error message")
    expected_path: Optional[str] = Field(default=None, description="Expected file or data path")
    actual_path: Optional[str] = Field(default=None, description="Actual file or data path found")
    recovery_suggestions: list[str] = Field(default_factory=list, description="List of suggested recovery actions")
    timestamp: datetime = Field(description="When the error occurred")
    context: dict = Field(default_factory=dict, description="Additional context information")


class DataAvailabilityStatus(str, Enum):
    """Overall data availability status."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"
    UNAVAILABLE = "UNAVAILABLE"


class DataAvailabilityReport(BaseModel):
    """Report on data availability across all crews."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stock_available: bool = Field(description="Whether stock crew data is available")
    etf_available: bool = Field(description="Whether ETF crew data is available")
    crypto_available: bool = Field(description="Whether crypto crew data is available")
    discovery_available: bool = Field(description="Whether discovery crew data is available")
    portfolio_available: bool = Field(description="Whether portfolio data is available")

    missing_data: list[str] = Field(default_factory=list, description="List of missing data components")
    stale_data: list[str] = Field(default_factory=list, description="List of stale data components")
    integration_errors: list[IntegrationError] = Field(default_factory=list, description="List of integration errors encountered")

    overall_status: DataAvailabilityStatus = Field(description="Overall data availability status")
    report_timestamp: datetime = Field(description="When this report was generated")

    data_freshness_summary: dict = Field(default_factory=dict, description="Summary of data freshness across crews")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improving data availability")


# Enhanced Discovery Crew Output
class DiscoveryCrewOutput(BaseModel):
    """Enhanced discovery crew output with integration metadata."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: CrewOutputMetadata = Field(description="Integration metadata")
    a_plus_opportunities: APlusOpportunityCollection = Field(description="Collection of A+ investment opportunities")
    portfolio_improvements: list[dict] = Field(default_factory=list, description="Portfolio improvement suggestions")
    optimization_results: list[dict] = Field(default_factory=list, description="Portfolio optimization results")
    validation_results: list[dict] = Field(default_factory=list, description="Validation results for discovered opportunities")
    market_analysis: dict = Field(default_factory=dict, description="Overall market analysis context")
