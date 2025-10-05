"""
Integration and system-level schemas for FinWiz.

This module contains Pydantic models for system integration, validation,
health checking, and pipeline management.
"""

from finwiz.schemas.integration_models import (
    APlusOpportunityCollection,
    CrewOutputMetadata,
    CryptoCrewOutput,
    DataAvailabilityReport,
    DataAvailabilityStatus,
    DataQuality,
    DataSource,
    DataSourceType,
    DiscoveryCrewOutput,
    ETFCrewOutput,
    FreshnessStatus,
    IntegrationError,
    IntegrationErrorType,
    SECCitation,
    StockCrewOutput,
    ValidatedCrypto,
    ValidatedETF,
    ValidatedTicker,
    ValidationStatus,
)

from .models import (
    ConsolidatedSECCitations,
    CrewConfig,
    CrewDependencyConfig,
    CrewExecutionContext,
    CrossCrewValidationResult,
    DataQualityConfig,
    DataQualityLevel,
    # Data recovery models
    DataRepairSuggestion,
    ExecutionResult,
    FallbackDataProvider,
    # Freshness models
    FreshnessCheckResult,
    FreshnessReport,
    HealthStatus,
    # Health monitoring models
    HealthStatusModel,
    # Configuration models
    IntegrationConfig,
    MissingDataScenario,
    # Monitoring models
    MonitoringRule,
    MonitoringStatus,
    PortfolioAlert,
    PortfolioHealthDashboard,
    PostExecutionResult,
    # Crew execution models
    PreExecutionResult,
    RecoveryAction,
    RecoveryStrategy,
    RetrievalResult,
    SECCitationValidationResult,
    # SEC citation models
    SECFilingInfo,
    StorageQuery,
    # Storage models
    StorageResult,
    SystemHealthReport,
    UpstreamDataCollection,
    # Validation models
    ValidationErrorAnalysis,
    ValidationErrorReport,
    ValidationPipelineResult,
    ValidationResult,
    # Enums
    ValidationSeverity,
)

__all__ = [
    # Enums
    "ValidationSeverity",
    "HealthStatus",
    "DataQualityLevel",
    "RecoveryStrategy",
    # Crew execution models
    "PreExecutionResult",
    "PostExecutionResult",
    "CrewExecutionContext",
    "ExecutionResult",
    "CrewConfig",
    "UpstreamDataCollection",
    # Validation models
    "ValidationErrorAnalysis",
    "ValidationErrorReport",
    "ValidationResult",
    "CrossCrewValidationResult",
    "ValidationPipelineResult",
    # Health monitoring models
    "HealthStatusModel",
    "SystemHealthReport",
    # Data recovery models
    "DataRepairSuggestion",
    "MissingDataScenario",
    "FallbackDataProvider",
    "RecoveryAction",
    # Storage models
    "StorageResult",
    "RetrievalResult",
    "StorageQuery",
    # Configuration models
    "IntegrationConfig",
    "CrewDependencyConfig",
    "DataQualityConfig",
    # SEC citation models
    "SECFilingInfo",
    "SECCitationValidationResult",
    "ConsolidatedSECCitations",
    # Freshness models
    "FreshnessCheckResult",
    "FreshnessReport",
    # Monitoring models
    "MonitoringRule",
    "PortfolioAlert",
    "MonitoringStatus",
    "PortfolioHealthDashboard",
    # Discovery models
    "APlusOpportunityCollection",
    "DataAvailabilityReport",
    "DataAvailabilityStatus",
    # Integration models from parent
    "CryptoCrewOutput",
    "CrewOutputMetadata",
    "DataQuality",
    "DataSource",
    "DataSourceType",
    "DiscoveryCrewOutput",
    "ETFCrewOutput",
    "FreshnessStatus",
    "IntegrationError",
    "IntegrationErrorType",
    "SECCitation",
    "StockCrewOutput",
    "ValidatedCrypto",
    "ValidatedETF",
    "ValidatedTicker",
    "ValidationStatus",
]
