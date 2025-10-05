"""
Integration and system-level schemas for FinWiz.

This module contains Pydantic models for system integration, validation,
health checking, pipeline management, and crew coordination.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# Enums for integration
class ValidationSeverity(str, Enum):
    """Validation error severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatus(str, Enum):
    """Health status levels."""

    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    UNHEALTHY = "UNHEALTHY"
    CRITICAL = "CRITICAL"


class DataQualityLevel(str, Enum):
    """Data quality assessment levels."""

    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    ACCEPTABLE = "ACCEPTABLE"
    POOR = "POOR"
    UNACCEPTABLE = "UNACCEPTABLE"


class RecoveryStrategy(str, Enum):
    """Data recovery strategy types."""

    RETRY = "RETRY"
    FALLBACK = "FALLBACK"
    SKIP = "SKIP"
    MANUAL = "MANUAL"


# Crew Execution Models
class PreExecutionResult(BaseModel):
    """Result of pre-execution validation and preparation."""

    can_proceed: bool = Field(description="Whether crew execution can proceed")
    dependencies_met: bool = Field(description="Whether all dependencies are satisfied")
    missing_dependencies: list[str] = Field(default_factory=list)
    stale_dependencies: list[str] = Field(default_factory=list)
    upstream_data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class PostExecutionResult(BaseModel):
    """Result of post-execution processing."""

    storage_success: bool = Field(description="Whether data was stored successfully")
    validation_success: bool = Field(description="Whether validation passed")
    metadata_stored: bool = Field(description="Whether metadata was persisted")
    lineage_updated: bool = Field(description="Whether data lineage was updated")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CrewExecutionContext(BaseModel):
    """Context information for crew execution."""

    crew_name: str = Field(description="Name of the crew being executed")
    execution_id: str = Field(description="Unique execution identifier")
    start_time: datetime = Field(description="Execution start time")
    dependencies: list[str] = Field(default_factory=list)
    max_age_hours: int = Field(default=24, description="Maximum acceptable data age")
    upstream_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of crew execution coordination."""

    crew_name: str = Field(description="Name of executed crew")
    success: bool = Field(description="Whether execution was successful")
    execution_time: float = Field(description="Execution time in seconds")
    output_data: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class CrewConfig(BaseModel):
    """Configuration for crew execution."""

    crew_name: str = Field(description="Name of the crew")
    dependencies: list[str] = Field(default_factory=list)
    max_execution_time: int = Field(default=300, description="Maximum execution time in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")


class UpstreamDataCollection(BaseModel):
    """Collection of upstream data available to a crew."""

    crew_name: str = Field(description="Name of the crew requesting data")
    available_data: dict[str, Any] = Field(default_factory=dict)
    data_freshness: dict[str, datetime] = Field(default_factory=dict)
    missing_dependencies: list[str] = Field(default_factory=list)
    stale_dependencies: list[str] = Field(default_factory=list)


# Validation Models
class ValidationErrorAnalysis(BaseModel):
    """Analysis of a validation error with categorization and severity."""

    error_type: str = Field(description="Type of validation error")
    severity: ValidationSeverity = Field(description="Severity level of the error")
    field_path: str = Field(description="Path to the field with error")
    error_message: str = Field(description="Detailed error message")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix for the error")
    recovery_strategy: RecoveryStrategy = Field(description="Recommended recovery strategy")
    can_auto_fix: bool = Field(default=False, description="Whether error can be automatically fixed")


class ValidationErrorReport(BaseModel):
    """Comprehensive report on validation errors and recovery options."""

    total_errors: int = Field(description="Total number of validation errors")
    error_breakdown: dict[str, int] = Field(description="Breakdown of errors by type")
    severity_breakdown: dict[ValidationSeverity, int] = Field(description="Breakdown by severity")
    errors: list[ValidationErrorAnalysis] = Field(description="Detailed error analysis")
    recovery_recommendations: list[str] = Field(description="Recovery recommendations")
    can_proceed: bool = Field(description="Whether processing can proceed despite errors")


class ValidationResult(BaseModel):
    """Result of data validation."""

    is_valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    sanitized_data: Optional[dict[str, Any]] = Field(None, description="Sanitized data if validation passed")
    validation_time: float = Field(description="Time taken for validation in seconds")


class CrossCrewValidationResult(BaseModel):
    """Result of cross-crew data consistency validation."""

    crews_validated: list[str] = Field(description="List of crews that were validated")
    consistency_score: float = Field(ge=0, le=1, description="Overall consistency score")
    inconsistencies: list[str] = Field(default_factory=list, description="Detected inconsistencies")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improvement")


class ValidationPipelineResult(BaseModel):
    """Comprehensive result of validation pipeline execution."""

    pipeline_success: bool = Field(description="Whether pipeline completed successfully")
    individual_results: dict[str, ValidationResult] = Field(description="Results for each validation step")
    cross_crew_result: Optional[CrossCrewValidationResult] = Field(None, description="Cross-crew validation result")
    overall_quality_score: float = Field(ge=0, le=1, description="Overall data quality score")
    execution_time: float = Field(description="Total pipeline execution time")


# Health Monitoring Models
class HealthStatusModel(BaseModel):
    """Health status for a component."""

    component_name: str = Field(description="Name of the component")
    status: HealthStatus = Field(description="Current health status")
    last_check: datetime = Field(description="Timestamp of last health check")
    message: str = Field(description="Status message")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Health metrics")


class SystemHealthReport(BaseModel):
    """Comprehensive system health report."""

    overall_status: HealthStatus = Field(description="Overall system health status")
    component_statuses: list[HealthStatusModel] = Field(description="Individual component statuses")
    critical_issues: list[str] = Field(default_factory=list, description="Critical issues requiring attention")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for improvement")
    report_timestamp: datetime = Field(description="When the report was generated")


# Data Recovery Models
class DataRepairSuggestion(BaseModel):
    """Suggestion for repairing invalid data."""

    field_path: str = Field(description="Path to the field needing repair")
    current_value: Any = Field(description="Current invalid value")
    suggested_value: Any = Field(description="Suggested replacement value")
    confidence: float = Field(ge=0, le=1, description="Confidence in the suggestion")
    repair_method: str = Field(description="Method used to generate suggestion")
    requires_manual_review: bool = Field(default=False, description="Whether manual review is required")


class MissingDataScenario(BaseModel):
    """Represents a missing data scenario with context."""

    data_type: str = Field(description="Type of missing data")
    context: dict[str, Any] = Field(description="Context information about the missing data")
    severity: ValidationSeverity = Field(description="Severity of the missing data")
    fallback_available: bool = Field(description="Whether fallback data is available")


class FallbackDataProvider(BaseModel):
    """Provides fallback data for common missing scenarios."""

    provider_name: str = Field(description="Name of the fallback provider")
    supported_scenarios: list[str] = Field(description="List of supported missing data scenarios")
    reliability_score: float = Field(ge=0, le=1, description="Reliability score of the provider")


class RecoveryAction(BaseModel):
    """Represents a recovery action for missing data."""

    action_type: RecoveryStrategy = Field(description="Type of recovery action")
    description: str = Field(description="Description of the recovery action")
    estimated_success_rate: float = Field(ge=0, le=1, description="Estimated success rate")
    execution_time_estimate: int = Field(description="Estimated execution time in seconds")
    requires_user_input: bool = Field(default=False, description="Whether user input is required")


# Storage Models
class StorageResult(BaseModel):
    """Result of storage operation."""

    success: bool = Field(description="Whether storage was successful")
    storage_key: Optional[str] = Field(None, description="Key where data was stored")
    error_message: Optional[str] = Field(None, description="Error message if storage failed")
    storage_time: float = Field(description="Time taken for storage operation")


class RetrievalResult(BaseModel):
    """Result of retrieval operation."""

    success: bool = Field(description="Whether retrieval was successful")
    data: Optional[dict[str, Any]] = Field(None, description="Retrieved data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Data metadata")
    retrieval_time: float = Field(description="Time taken for retrieval operation")


class StorageQuery(BaseModel):
    """Query parameters for storage retrieval."""

    crew_name: str = Field(description="Name of the crew")
    data_type: Optional[str] = Field(None, description="Type of data to retrieve")
    max_age_hours: int = Field(default=24, description="Maximum age of data in hours")
    include_metadata: bool = Field(default=True, description="Whether to include metadata")


# Configuration Models
class IntegrationConfig(BaseModel):
    """Configuration for the integration system."""

    # Storage configuration
    storage_backend: Literal["file", "redis", "database"] = Field(default="file", description="Storage backend type")
    storage_path: str = Field(default="./data", description="Path for file-based storage")
    cache_ttl_seconds: int = Field(default=3600, description="Default cache TTL in seconds")

    # Validation configuration
    validation_strictness: Literal["off", "warn", "error"] = Field(default="warn", description="Validation strictness level")
    enable_cross_crew_validation: bool = Field(default=True, description="Enable cross-crew validation")
    max_validation_errors: int = Field(default=10, description="Maximum validation errors before stopping")

    # Health monitoring
    health_check_interval: int = Field(default=300, description="Health check interval in seconds")
    enable_health_monitoring: bool = Field(default=True, description="Enable health monitoring")

    # Performance settings
    max_concurrent_crews: int = Field(default=5, description="Maximum concurrent crew executions")
    execution_timeout: int = Field(default=600, description="Execution timeout in seconds")

    # Logging and debugging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO", description="Logging level")
    enable_performance_logging: bool = Field(default=True, description="Enable performance logging")
    enable_data_lineage: bool = Field(default=True, description="Enable data lineage tracking")


class CrewDependencyConfig(BaseModel):
    """Configuration for crew dependencies and execution order."""

    crew_name: str = Field(description="Name of the crew")
    dependencies: list[str] = Field(default_factory=list, description="List of crew dependencies")
    optional_dependencies: list[str] = Field(default_factory=list, description="List of optional dependencies")
    max_wait_time: int = Field(default=300, description="Maximum wait time for dependencies")

    # Execution settings
    parallel_execution: bool = Field(default=False, description="Whether crew can execute in parallel")
    priority: int = Field(default=0, description="Execution priority (higher = more priority)")
    retry_on_dependency_failure: bool = Field(default=True, description="Retry if dependencies fail")

    # Data requirements
    required_data_types: list[str] = Field(default_factory=list, description="Required data types from dependencies")
    optional_data_types: list[str] = Field(default_factory=list, description="Optional data types")
    data_freshness_requirements: dict[str, int] = Field(default_factory=dict, description="Freshness requirements by data type")

    @field_validator("priority")
    @classmethod
    def validate_priority_range(cls, v: int) -> int:
        """Validate priority is within reasonable range."""
        if not -10 <= v <= 10:
            raise ValueError("Priority must be between -10 and 10")
        return v


class DataQualityConfig(BaseModel):
    """Configuration for data quality checks and validation."""

    # Quality thresholds
    minimum_quality_score: float = Field(default=0.7, ge=0, le=1, description="Minimum acceptable quality score")
    warning_quality_score: float = Field(default=0.8, ge=0, le=1, description="Quality score that triggers warnings")

    # Validation settings
    enable_schema_validation: bool = Field(default=True, description="Enable Pydantic schema validation")
    enable_business_rule_validation: bool = Field(default=True, description="Enable business rule validation")
    enable_data_consistency_checks: bool = Field(default=True, description="Enable data consistency checks")

    # Quality metrics
    track_completeness: bool = Field(default=True, description="Track data completeness")
    track_accuracy: bool = Field(default=True, description="Track data accuracy")
    track_timeliness: bool = Field(default=True, description="Track data timeliness")
    track_consistency: bool = Field(default=True, description="Track data consistency")

    # Remediation settings
    auto_fix_minor_issues: bool = Field(default=True, description="Automatically fix minor data issues")
    quarantine_invalid_data: bool = Field(default=True, description="Quarantine invalid data for review")
    notify_on_quality_issues: bool = Field(default=True, description="Send notifications for quality issues")

    @field_validator("warning_quality_score")
    @classmethod
    def validate_warning_threshold(cls, v: float, info: Any) -> float:
        """Validate warning threshold is higher than minimum."""
        if hasattr(info, "data") and "minimum_quality_score" in info.data:
            if v <= info.data["minimum_quality_score"]:
                raise ValueError("Warning quality score must be higher than minimum quality score")
        return v


# SEC Citation Models
class SECFilingInfo(BaseModel):
    """Information extracted from SEC filing URL."""

    cik: str = Field(description="Central Index Key")
    accession_number: str = Field(description="SEC accession number")
    filing_type: str = Field(description="Type of SEC filing")
    filing_date: Optional[datetime] = Field(None, description="Filing date if available")
    company_name: Optional[str] = Field(None, description="Company name if available")


class SECCitationValidationResult(BaseModel):
    """Result of SEC citation validation."""

    is_valid: bool = Field(description="Whether the citation is valid")
    filing_info: Optional[SECFilingInfo] = Field(None, description="Extracted filing information")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in validation result")


class ConsolidatedSECCitations(BaseModel):
    """Consolidated SEC citations for report integration."""

    total_citations: int = Field(description="Total number of SEC citations")
    valid_citations: int = Field(description="Number of valid citations")
    invalid_citations: int = Field(description="Number of invalid citations")
    citations_by_type: dict[str, int] = Field(description="Citations grouped by filing type")
    validation_results: list[SECCitationValidationResult] = Field(description="Individual validation results")
    overall_confidence: float = Field(ge=0, le=1, description="Overall confidence in citations")


# Freshness Models
class FreshnessCheckResult(BaseModel):
    """Result of a freshness check for a single data source."""

    data_source: str = Field(description="Name of the data source")
    is_fresh: bool = Field(description="Whether data is considered fresh")
    age_hours: float = Field(description="Age of data in hours")
    threshold_hours: float = Field(description="Freshness threshold in hours")
    last_updated: datetime = Field(description="When data was last updated")


class FreshnessReport(BaseModel):
    """Comprehensive freshness report across all crew outputs."""

    overall_freshness: bool = Field(description="Whether all data is fresh")
    total_sources: int = Field(description="Total number of data sources checked")
    fresh_sources: int = Field(description="Number of fresh data sources")
    stale_sources: int = Field(description="Number of stale data sources")
    check_results: list[FreshnessCheckResult] = Field(description="Individual check results")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations for stale data")
    report_timestamp: datetime = Field(description="When the report was generated")


# Monitoring Models
class MonitoringRule(BaseModel):
    """Configuration for automated monitoring rules."""

    rule_name: str = Field(description="Name of the monitoring rule")
    rule_type: Literal["threshold", "trend", "anomaly", "pattern"] = Field(description="Type of monitoring rule")
    metric_name: str = Field(description="Name of the metric to monitor")

    # Threshold rules
    threshold_value: Optional[float] = Field(None, description="Threshold value for alerts")
    comparison_operator: Literal["gt", "lt", "gte", "lte", "eq", "ne"] | None = Field(None, description="Comparison operator")

    # Trend rules
    trend_window: Optional[int] = Field(None, description="Window size for trend analysis")
    trend_threshold: Optional[float] = Field(None, description="Threshold for trend detection")

    # General settings
    enabled: bool = Field(default=True, description="Whether rule is enabled")
    alert_frequency: Literal["immediate", "hourly", "daily"] = Field(default="immediate", description="Alert frequency")
    severity: ValidationSeverity = Field(default=ValidationSeverity.WARNING, description="Alert severity")


class PortfolioAlert(BaseModel):
    """Portfolio monitoring alert."""

    alert_id: str = Field(description="Unique alert identifier")
    alert_type: str = Field(description="Type of alert")
    severity: ValidationSeverity = Field(description="Alert severity")
    message: str = Field(description="Alert message")

    # Context
    portfolio_id: str = Field(description="Portfolio identifier")
    affected_assets: list[str] = Field(default_factory=list, description="Assets affected by alert")
    metric_values: dict[str, float] = Field(default_factory=dict, description="Relevant metric values")

    # Timing
    triggered_at: datetime = Field(description="When alert was triggered")
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")

    # Actions
    recommended_actions: list[str] = Field(default_factory=list, description="Recommended actions")
    auto_actions_taken: list[str] = Field(default_factory=list, description="Automatic actions taken")


class MonitoringStatus(BaseModel):
    """Current monitoring status for a portfolio."""

    portfolio_id: str = Field(description="Portfolio identifier")
    monitoring_enabled: bool = Field(description="Whether monitoring is enabled")
    last_check: datetime = Field(description="Last monitoring check timestamp")

    # Active alerts
    active_alerts: list[PortfolioAlert] = Field(default_factory=list, description="Currently active alerts")
    alert_counts_by_severity: dict[ValidationSeverity, int] = Field(default_factory=dict, description="Alert counts by severity")

    # Monitoring rules
    active_rules: list[MonitoringRule] = Field(default_factory=list, description="Active monitoring rules")
    disabled_rules: list[str] = Field(default_factory=list, description="Names of disabled rules")

    # Performance
    monitoring_performance: dict[str, float] = Field(default_factory=dict, description="Monitoring performance metrics")


class PortfolioHealthDashboard(BaseModel):
    """Portfolio health dashboard data."""

    portfolio_id: str = Field(description="Portfolio identifier")
    overall_health_score: float = Field(ge=0, le=1, description="Overall portfolio health score")

    # Health components
    risk_health: float = Field(ge=0, le=1, description="Risk management health score")
    performance_health: float = Field(ge=0, le=1, description="Performance health score")
    diversification_health: float = Field(ge=0, le=1, description="Diversification health score")
    liquidity_health: float = Field(ge=0, le=1, description="Liquidity health score")

    # Key metrics
    key_metrics: dict[str, float] = Field(description="Key portfolio metrics")
    trend_indicators: dict[str, str] = Field(description="Trend indicators (up/down/stable)")

    # Alerts and recommendations
    critical_alerts: list[PortfolioAlert] = Field(default_factory=list, description="Critical alerts")
    top_recommendations: list[str] = Field(default_factory=list, description="Top recommendations")

    # Metadata
    last_updated: datetime = Field(description="When dashboard was last updated")
    data_freshness: dict[str, datetime] = Field(description="Freshness of underlying data")
