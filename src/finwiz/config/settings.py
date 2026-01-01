"""
FinWiz Configuration Settings.

This module provides centralized configuration for FinWiz features,
including hybrid analysis performance and quality thresholds.

Usage:
    from finwiz.config.settings import get_settings

    settings = get_settings()
    max_time = settings.hybrid_analysis.max_processing_time_seconds
"""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class YFinanceSettings(BaseModel):
    """
    Configuration for yfinance library (v1.0+).

    These settings configure the yfinance global settings including
    network retry mechanism and debug options.

    Reference: https://ranaroussi.github.io/yfinance/advanced/config.html
    """

    # Network settings
    retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Number of retry attempts for transient network errors (exponential backoff: 1s, 2s, 4s...)",
    )

    proxy: str | None = Field(
        default=None,
        description="Proxy server URL for all yfinance requests (e.g., 'http://proxy:8080')",
    )

    # Debug settings
    hide_exceptions: bool = Field(
        default=True,
        description="Whether to hide exceptions in yfinance (default: True)",
    )

    logging: bool = Field(
        default=False,
        description="Enable verbose yfinance debug logging (default: False)",
    )


class HybridAnalysisSettings(BaseModel):
    """
    Configuration for Python/AI hybrid analysis.

    These settings control performance thresholds and quality requirements
    for the hybrid analysis architecture where Python performs deterministic
    calculations and AI provides contextual insights.

    Requirements: 7.1, 7.2, 7.3, 7.4
    """

    # Performance Thresholds (Requirements 7.1, 7.2)
    max_processing_time_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        description="Maximum processing time per holding in seconds (default: 30s)",
    )

    max_llm_cost_dollars: float = Field(
        default=0.10,
        ge=0.0,
        le=10.0,
        description="Maximum LLM cost per holding in dollars (default: $0.10)",
    )

    # Quality Thresholds (Requirements 7.3, 7.4)
    min_report_word_count: int = Field(
        default=2000,
        ge=500,
        le=10000,
        description="Minimum report word count (default: 2000 words)",
    )

    min_unique_insights_count: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Minimum number of unique qualitative insights (default: 5)",
    )

    min_executive_summary_words: int = Field(
        default=200,
        ge=50,
        le=1000,
        description="Minimum executive summary word count (default: 200 words)",
    )

    min_investment_rationale_words: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Minimum investment rationale word count (default: 500 words)",
    )

    # Batch Processing Thresholds (Requirements 10.1, 10.2)
    max_batch_processing_time_seconds: float = Field(
        default=1800.0,
        ge=60.0,
        le=7200.0,
        description="Maximum batch processing time for 66 holdings in seconds (default: 1800s = 30 minutes)",
    )

    max_batch_llm_cost_dollars: float = Field(
        default=6.60,
        ge=0.0,
        le=100.0,
        description="Maximum batch LLM cost for 66 holdings in dollars (default: $6.60)",
    )

    # Reliability Threshold (Requirement 10.4)
    min_success_rate: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Minimum success rate for batch processing (default: 95%)",
    )

    # Feature Flags
    enable_hybrid_analysis: bool = Field(
        default=True,
        description="Enable hybrid Python/AI analysis (default: True)",
    )

    enable_fallback_to_python_only: bool = Field(
        default=True,
        description="Enable fallback to Python-only analysis on AI failure (default: True)",
    )

    log_performance_warnings: bool = Field(
        default=True,
        description="Log warnings when performance thresholds are exceeded (default: True)",
    )

    log_quality_warnings: bool = Field(
        default=True,
        description="Log warnings when quality thresholds are not met (default: True)",
    )


class FinWizSettings(BaseSettings):
    """
    Main FinWiz configuration settings.

    Loads configuration from environment variables and .env files.
    Settings can be overridden via environment variables with FINWIZ_ prefix.

    Example:
        FINWIZ_HYBRID_ANALYSIS__MAX_PROCESSING_TIME_SECONDS=45.0

    """

    model_config = SettingsConfigDict(
        env_prefix="FINWIZ_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # YFinance Configuration (v1.0+)
    yfinance: YFinanceSettings = Field(
        default_factory=YFinanceSettings,
        description="YFinance library configuration with retry mechanism",
    )

    # Hybrid Analysis Configuration
    hybrid_analysis: HybridAnalysisSettings = Field(
        default_factory=HybridAnalysisSettings,
        description="Hybrid analysis configuration",
    )

    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # API Keys (loaded from environment)
    openai_api_key: str | None = Field(
        default=None,
        description="OpenAI API key",
    )

    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )

    perplexity_api_key: str | None = Field(
        default=None,
        description="Perplexity API key",
    )


# Singleton instance
_settings: FinWizSettings | None = None


def get_settings() -> FinWizSettings:
    """
    Get FinWiz settings singleton.

    Returns:
        FinWizSettings instance

    Example:
        >>> settings = get_settings()
        >>> max_time = settings.hybrid_analysis.max_processing_time_seconds
        >>> print(f"Max processing time: {max_time}s")

    """
    global _settings
    if _settings is None:
        _settings = FinWizSettings()
    return _settings


def reset_settings() -> None:
    """
    Reset settings singleton (useful for testing).

    Example:
        >>> reset_settings()
        >>> settings = get_settings()  # Fresh instance

    """
    global _settings
    _settings = None


# Convenience function for hybrid analysis settings
def get_hybrid_analysis_settings() -> HybridAnalysisSettings:
    """
    Get hybrid analysis settings.

    Returns:
        HybridAnalysisSettings instance

    Example:
        >>> settings = get_hybrid_analysis_settings()
        >>> if settings.enable_hybrid_analysis:
        ...     print("Hybrid analysis enabled")

    """
    return get_settings().hybrid_analysis


# Convenience function for yfinance settings
def get_yfinance_settings() -> YFinanceSettings:
    """
    Get yfinance settings.

    Returns:
        YFinanceSettings instance

    Example:
        >>> settings = get_yfinance_settings()
        >>> print(f"Retries: {settings.retries}")

    """
    return get_settings().yfinance
