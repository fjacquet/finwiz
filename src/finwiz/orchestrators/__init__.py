"""Orchestrator modules for FinWiz Flow.

Orchestrators are lazy-loaded via the registry in finwiz.flows.orchestrator_registry.
Direct imports are supported for convenience.
"""

import importlib
from typing import Any

_ORCHESTRATOR_IMPORTS: dict[str, tuple[str, str]] = {
    "ErrorHandlingOrchestrator": ("finwiz.orchestrators.error_handling_orchestrator", "ErrorHandlingOrchestrator"),
    "ProgressTrackingOrchestrator": ("finwiz.orchestrators.progress_tracking_orchestrator", "ProgressTrackingOrchestrator"),
    "UtilityOrchestrator": ("finwiz.orchestrators.utility_orchestrator", "UtilityOrchestrator"),
    "DeepAnalysisOrchestrator": ("finwiz.orchestrators.deep_analysis_orchestrator", "DeepAnalysisOrchestrator"),
    "AlternativesMatchingOrchestrator": ("finwiz.orchestrators.alternatives_matching_orchestrator", "AlternativesMatchingOrchestrator"),
    "DiscoveryOrchestrator": ("finwiz.orchestrators.discovery_orchestrator", "DiscoveryOrchestrator"),
    "ValidationOrchestrator": ("finwiz.orchestrators.validation_orchestrator", "ValidationOrchestrator"),
    "ReportingOrchestrator": ("finwiz.orchestrators.reporting_orchestrator", "ReportingOrchestrator"),
}


def __getattr__(name: str) -> Any:
    """Lazy import orchestrators on demand."""
    if name in _ORCHESTRATOR_IMPORTS:
        module_path, class_name = _ORCHESTRATOR_IMPORTS[name]
        mod = importlib.import_module(module_path)  # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
        return getattr(mod, class_name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = list(_ORCHESTRATOR_IMPORTS.keys())
