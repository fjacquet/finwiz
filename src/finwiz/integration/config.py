"""
Integration System Configuration.

Configuration settings and constants for the crew data integration system.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class IntegrationConfig(BaseModel):
    """Configuration for the integration system."""

    # Directory settings
    output_dir: Path = Field(default=Path("output"))
    integration_dir_name: str = Field(default="integration")
    metadata_dir_name: str = Field(default="metadata")
    contracts_dir_name: str = Field(default="contracts")
    consolidated_dir_name: str = Field(default="consolidated")

    # Data freshness settings
    default_max_age_hours: int = Field(default=24)
    stale_data_warning_hours: int = Field(default=12)

    # Crew execution settings
    max_execution_timeout_minutes: int = Field(default=30)
    retry_attempts: int = Field(default=3)
    retry_delay_seconds: int = Field(default=5)

    # Validation settings
    strict_validation: bool = Field(default=True)
    allow_partial_data: bool = Field(default=True)

    # Logging settings
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    enable_structured_logging: bool = Field(default=True)


class CrewDependencyConfig(BaseModel):
    """Configuration for crew dependencies and execution order."""

    # Define crew execution dependencies
    crew_dependencies: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "stock": [],  # No dependencies
            "etf": [],  # No dependencies
            "crypto": [],  # No dependencies
            "discovery": ["stock", "etf", "crypto"],  # Depends on all analysis crews
            "portfolio": ["stock", "etf", "crypto", "discovery"],  # Depends on all
            "report": ["stock", "etf", "crypto", "discovery", "portfolio"],  # Final crew
        }
    )

    # Crew output schemas (to be enhanced with actual schema references)
    crew_schemas: dict[str, str] = Field(
        default_factory=lambda: {
            "stock": "StockCrewOutput",
            "etf": "ETFCrewOutput",
            "crypto": "CryptoCrewOutput",
            "discovery": "DiscoveryCrewOutput",
            "portfolio": "PortfolioCrewOutput",
            "report": "ReportCrewOutput",
        }
    )

    # Expected output files for each crew
    expected_outputs: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "stock": ["stock_analysis.json", "stock_recommendations.json"],
            "etf": ["etf_analysis.json", "etf_recommendations.json"],
            "crypto": ["crypto_analysis.json", "crypto_recommendations.json"],
            "discovery": ["discovery_opportunities.json", "a_plus_opportunities.json"],
            "portfolio": ["portfolio_analysis.json", "rebalancing_recommendations.json"],
            "report": ["final_report.json", "report_metadata.json"],
        }
    )


class DataQualityConfig(BaseModel):
    """Configuration for data quality checks and validation."""

    # Required metadata fields for all crew outputs
    required_metadata_fields: list[str] = Field(default_factory=lambda: ["crew_name", "execution_timestamp", "schema_version", "validation_status"])

    # Data quality thresholds
    min_confidence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    max_error_rate: float = Field(default=0.1, ge=0.0, le=1.0)

    # Validation rules
    validate_ticker_symbols: bool = Field(default=True)
    validate_sec_citations: bool = Field(default=True)
    validate_sentiment_scores: bool = Field(default=True)
    validate_risk_assessments: bool = Field(default=True)


def load_integration_config(config_path: Path | None = None) -> IntegrationConfig:
    """
    Load integration configuration from file and environment variables.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        IntegrationConfig instance with loaded configuration

    """
    # Start with default configuration
    config_data = {}

    # Load from YAML file if provided
    if config_path and config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            file_config = yaml.safe_load(f)
            if "integration" in file_config:
                config_data = file_config["integration"]

    # Override with environment variables
    env_overrides = _get_env_overrides()
    config_data = _merge_config(config_data, env_overrides)

    return IntegrationConfig(**config_data)


def load_crew_dependency_config(config_path: Path | None = None) -> CrewDependencyConfig:
    """
    Load crew dependency configuration from file.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        CrewDependencyConfig instance with loaded configuration

    """
    config_data = {}

    # Load from YAML file if provided
    if config_path and config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            file_config = yaml.safe_load(f)
            if "crew_dependencies" in file_config:
                config_data = file_config["crew_dependencies"]

    return CrewDependencyConfig(**config_data)


def load_data_quality_config(config_path: Path | None = None) -> DataQualityConfig:
    """
    Load data quality configuration from file.

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        DataQualityConfig instance with loaded configuration

    """
    config_data = {}

    # Load from YAML file if provided
    if config_path and config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            file_config = yaml.safe_load(f)
            if "data_quality" in file_config:
                config_data = file_config["data_quality"]

    return DataQualityConfig(**config_data)


def _get_env_overrides() -> dict[str, Any]:
    """Get configuration overrides from environment variables."""
    env_overrides: dict[str, Any] = {}

    # Output directory
    if output_dir := os.getenv("FINWIZ_INTEGRATION_OUTPUT_DIR"):
        env_overrides["output_dir"] = Path(output_dir)

    # Data freshness settings
    if default_max_age := os.getenv("FINWIZ_INTEGRATION_DEFAULT_MAX_AGE_HOURS"):
        env_overrides["default_max_age_hours"] = int(default_max_age)

    if stale_warning := os.getenv("FINWIZ_INTEGRATION_STALE_WARNING_HOURS"):
        env_overrides["stale_data_warning_hours"] = int(stale_warning)

    # Execution settings
    if timeout := os.getenv("FINWIZ_INTEGRATION_MAX_EXECUTION_TIMEOUT_MINUTES"):
        env_overrides["max_execution_timeout_minutes"] = int(timeout)

    if retry_attempts := os.getenv("FINWIZ_INTEGRATION_MAX_RETRIES"):
        env_overrides["retry_attempts"] = int(retry_attempts)

    if retry_delay := os.getenv("FINWIZ_INTEGRATION_RETRY_DELAY"):
        env_overrides["retry_delay_seconds"] = int(retry_delay)

    # Validation settings
    if strict_validation := os.getenv("FINWIZ_INTEGRATION_STRICT_VALIDATION"):
        env_overrides["strict_validation"] = strict_validation.lower() in ("true", "1", "yes")

    if allow_partial := os.getenv("FINWIZ_INTEGRATION_ALLOW_PARTIAL_DATA"):
        env_overrides["allow_partial_data"] = allow_partial.lower() in ("true", "1", "yes")

    # Logging settings
    if log_level := os.getenv("FINWIZ_INTEGRATION_LOG_LEVEL"):
        env_overrides["log_level"] = log_level

    if structured_logging := os.getenv("FINWIZ_INTEGRATION_STRUCTURED_LOGGING"):
        env_overrides["enable_structured_logging"] = structured_logging.lower() in ("true", "1", "yes")

    return env_overrides


def _merge_config(base_config: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    """Merge configuration dictionaries recursively."""
    merged = base_config.copy()

    for key, value in overrides.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value

    return merged


# Default configuration instances
DEFAULT_INTEGRATION_CONFIG = IntegrationConfig()
DEFAULT_CREW_DEPENDENCY_CONFIG = CrewDependencyConfig()
DEFAULT_DATA_QUALITY_CONFIG = DataQualityConfig()


def get_integration_config() -> IntegrationConfig:
    """Get the default integration configuration."""
    return DEFAULT_INTEGRATION_CONFIG


def get_crew_dependency_config() -> CrewDependencyConfig:
    """Get the default crew dependency configuration."""
    return DEFAULT_CREW_DEPENDENCY_CONFIG


def get_data_quality_config() -> DataQualityConfig:
    """Get the default data quality configuration."""
    return DEFAULT_DATA_QUALITY_CONFIG
