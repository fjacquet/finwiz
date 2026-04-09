"""
Integration System Health Checker.

Provides comprehensive health checking for the crew data integration pipeline
in a single-user environment. Monitors data freshness, availability, and
integration system status.

This module maintains backward compatibility by re-exporting classes and
functions from the new modular structure.
"""

# Re-export from new modules for backward compatibility
from .checks import HealthStatus
from .monitoring import (
    IntegrationHealthChecker,
    SystemHealthReport,
    get_health_checker,
    perform_comprehensive_health_check,
    perform_quick_health_check,
)

__all__ = [
    "HealthStatus",
    "IntegrationHealthChecker",
    "SystemHealthReport",
    "get_health_checker",
    "perform_comprehensive_health_check",
    "perform_quick_health_check",
]
