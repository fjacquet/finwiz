"""
Performance optimization configuration for FinWiz.

This module manages performance-related configuration settings including
optimization modes, batch processing, and performance monitoring.
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class OptimizationMode(Enum):
    """Performance optimization modes."""

    MAXIMUM_SPEED = "maximum_speed"
    BALANCED = "balanced"
    BASELINE = "baseline"


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    execution_time: float = 0.0
    llm_call_count: int = 0
    api_call_count: int = 0
    cost_estimate: float = 0.0
    ticker: str = ""
    mode: OptimizationMode = OptimizationMode.BASELINE


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""

    # Risk Assessment Configuration
    risk_assessment_use_mini: bool = True
    use_minimal_risk_tools: bool = True

    # Deep Analysis Configuration
    deep_analysis_ai_summary: bool = False
    deep_analysis_batch_size: int = 5

    # Optimization Mode
    mode: OptimizationMode = OptimizationMode.MAXIMUM_SPEED

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.deep_analysis_batch_size < 1:
            raise ValueError("Deep analysis batch size must be at least 1")
        if self.deep_analysis_batch_size > 20:
            logger.warning(f"Large batch size ({self.deep_analysis_batch_size}) may cause memory issues")


class PerformanceConfigManager:
    """Manager for performance optimization configuration."""

    def __init__(self) -> None:
        """Initialize performance configuration manager."""
        self.config = self._load_configuration()
        self._validate_configuration()
        self._log_configuration()

    def _load_configuration(self) -> OptimizationConfig:
        """Load configuration from environment variables."""
        # Load environment variables with defaults
        risk_assessment_use_mini = os.getenv("RISK_ASSESSMENT_USE_MINI", "true").lower() == "true"
        use_minimal_risk_tools = os.getenv("USE_MINIMAL_RISK_TOOLS", "true").lower() == "true"
        deep_analysis_ai_summary = os.getenv("DEEP_ANALYSIS_AI_SUMMARY", "false").lower() == "true"

        try:
            deep_analysis_batch_size = int(os.getenv("DEEP_ANALYSIS_BATCH_SIZE", "5"))
        except ValueError:
            logger.warning("Invalid DEEP_ANALYSIS_BATCH_SIZE value, using default: 5")
            deep_analysis_batch_size = 5

        # Determine optimization mode based on configuration
        mode = self._determine_optimization_mode(risk_assessment_use_mini, use_minimal_risk_tools, deep_analysis_ai_summary)

        return OptimizationConfig(
            risk_assessment_use_mini=risk_assessment_use_mini,
            use_minimal_risk_tools=use_minimal_risk_tools,
            deep_analysis_ai_summary=deep_analysis_ai_summary,
            deep_analysis_batch_size=deep_analysis_batch_size,
            mode=mode,
        )

    def _determine_optimization_mode(self, use_mini: bool, minimal_tools: bool, ai_summary: bool) -> OptimizationMode:
        """Determine optimization mode based on configuration."""
        if use_mini and minimal_tools and not ai_summary:
            return OptimizationMode.MAXIMUM_SPEED
        elif use_mini and minimal_tools and ai_summary:
            return OptimizationMode.BALANCED
        else:
            return OptimizationMode.BASELINE

    def _validate_configuration(self) -> None:
        """Validate configuration values."""
        errors = []

        # Validate batch size
        if self.config.deep_analysis_batch_size < 1:
            errors.append("DEEP_ANALYSIS_BATCH_SIZE must be at least 1")
        elif self.config.deep_analysis_batch_size > 50:
            errors.append("DEEP_ANALYSIS_BATCH_SIZE should not exceed 50 for memory safety")

        # Validate mode consistency
        if self.config.mode == OptimizationMode.MAXIMUM_SPEED and self.config.deep_analysis_ai_summary:
            logger.warning("Maximum speed mode with AI summary enabled - consider disabling AI summary for best performance")

        if errors:
            error_msg = "Configuration validation errors: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Performance configuration validation passed")

    def _log_configuration(self) -> None:
        """Log current configuration at startup."""
        logger.info("Performance Optimization Configuration:")
        logger.info(f"  Mode: {self.config.mode.value}")
        logger.info(f"  Risk Assessment Use Mini: {self.config.risk_assessment_use_mini}")
        logger.info(f"  Use Minimal Risk Tools: {self.config.use_minimal_risk_tools}")
        logger.info(f"  Deep Analysis AI Summary: {self.config.deep_analysis_ai_summary}")
        logger.info(f"  Deep Analysis Batch Size: {self.config.deep_analysis_batch_size}")

        # Log expected performance characteristics
        self._log_performance_expectations()

    def _log_performance_expectations(self) -> None:
        """Log expected performance characteristics for current mode."""
        expectations = {
            OptimizationMode.MAXIMUM_SPEED: {
                "time_per_ticker": "10-30 seconds",
                "llm_calls": "0 for calculations",
                "cost_per_ticker": "$0 for calculations",
                "description": "Python scoring + no AI summary + gpt-4o-mini + minimal tools",
            },
            OptimizationMode.BALANCED: {
                "time_per_ticker": "15-40 seconds",
                "llm_calls": "1 for summary",
                "cost_per_ticker": "$0.01",
                "description": "Python scoring + optional AI summary + gpt-4o-mini + minimal tools",
            },
            OptimizationMode.BASELINE: {
                "time_per_ticker": "5-10 minutes",
                "llm_calls": "5-10 for analysis",
                "cost_per_ticker": "$0.05-0.10",
                "description": "AI scoring for comparison/debugging",
            },
        }

        exp = expectations[self.config.mode]
        logger.info(f"Expected Performance ({self.config.mode.value}):")
        logger.info(f"  Description: {exp['description']}")
        logger.info(f"  Time per ticker: {exp['time_per_ticker']}")
        logger.info(f"  LLM calls: {exp['llm_calls']}")
        logger.info(f"  Cost per ticker: {exp['cost_per_ticker']}")

    def get_config(self) -> OptimizationConfig:
        """Get current optimization configuration."""
        return self.config

    def get_mode(self) -> OptimizationMode:
        """Get current optimization mode."""
        return self.config.mode

    def is_maximum_speed_mode(self) -> bool:
        """Check if running in maximum speed mode."""
        return self.config.mode == OptimizationMode.MAXIMUM_SPEED

    def is_balanced_mode(self) -> bool:
        """Check if running in balanced mode."""
        return self.config.mode == OptimizationMode.BALANCED

    def is_baseline_mode(self) -> bool:
        """Check if running in baseline mode."""
        return self.config.mode == OptimizationMode.BASELINE

    def should_use_ai_summary(self) -> bool:
        """Check if AI summary should be used."""
        return self.config.deep_analysis_ai_summary

    def should_use_mini_model(self) -> bool:
        """Check if mini model should be used for risk assessment."""
        return self.config.risk_assessment_use_mini

    def should_use_minimal_tools(self) -> bool:
        """Check if minimal tool set should be used."""
        return self.config.use_minimal_risk_tools

    def get_batch_size(self) -> int:
        """Get deep analysis batch size."""
        return self.config.deep_analysis_batch_size

    def get_configuration_summary(self) -> dict[str, Any]:
        """Get configuration summary for logging/debugging."""
        return {
            "mode": self.config.mode.value,
            "risk_assessment_use_mini": self.config.risk_assessment_use_mini,
            "use_minimal_risk_tools": self.config.use_minimal_risk_tools,
            "deep_analysis_ai_summary": self.config.deep_analysis_ai_summary,
            "deep_analysis_batch_size": self.config.deep_analysis_batch_size,
            "expected_performance": self._get_expected_performance(),
        }

    def _get_expected_performance(self) -> dict[str, str]:
        """Get expected performance characteristics for current mode."""
        if self.config.mode == OptimizationMode.MAXIMUM_SPEED:
            return {"time_per_ticker": "10-30 seconds", "speedup_factor": "10-20x", "cost_savings": "100%"}
        elif self.config.mode == OptimizationMode.BALANCED:
            return {"time_per_ticker": "15-40 seconds", "speedup_factor": "8-15x", "cost_savings": "80-90%"}
        else:  # BASELINE
            return {"time_per_ticker": "5-10 minutes", "speedup_factor": "1x (baseline)", "cost_savings": "0% (baseline)"}


# Global performance configuration manager instance
_performance_config_manager: PerformanceConfigManager | None = None


def get_performance_config_manager() -> PerformanceConfigManager:
    """Get the global performance configuration manager instance."""
    global _performance_config_manager
    if _performance_config_manager is None:
        _performance_config_manager = PerformanceConfigManager()
    return _performance_config_manager


def get_optimization_mode() -> OptimizationMode:
    """Get current optimization mode."""
    return get_performance_config_manager().get_mode()


def is_maximum_speed_mode() -> bool:
    """Check if running in maximum speed mode."""
    return get_performance_config_manager().is_maximum_speed_mode()


def is_balanced_mode() -> bool:
    """Check if running in balanced mode."""
    return get_performance_config_manager().is_balanced_mode()


def is_baseline_mode() -> bool:
    """Check if running in baseline mode."""
    return get_performance_config_manager().is_baseline_mode()


def should_use_ai_summary() -> bool:
    """Check if AI summary should be used."""
    return get_performance_config_manager().should_use_ai_summary()


def should_use_mini_model() -> bool:
    """Check if mini model should be used."""
    return get_performance_config_manager().should_use_mini_model()


def should_use_minimal_tools() -> bool:
    """Check if minimal tools should be used."""
    return get_performance_config_manager().should_use_minimal_tools()


def get_batch_size() -> int:
    """Get deep analysis batch size."""
    return get_performance_config_manager().get_batch_size()
