"""Registry for lazy-loaded orchestrator instantiation.

Maps orchestrator names to their module paths, class names, and
required dependency keys from OrchestratorDependencies.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestratorConfig:
    """Configuration for a single orchestrator."""

    module: str
    class_name: str
    deps_keys: tuple[str, ...]


ORCHESTRATOR_REGISTRY: dict[str, OrchestratorConfig] = {
    "error_handler": OrchestratorConfig(
        module="finwiz.orchestrators.error_handling_orchestrator",
        class_name="ErrorHandlingOrchestrator",
        deps_keys=("crew_factory", "integration_manager", "error_handler"),
    ),
    "progress": OrchestratorConfig(
        module="finwiz.orchestrators.progress_tracking_orchestrator",
        class_name="ProgressTrackingOrchestrator",
        deps_keys=(),
    ),
    "utility": OrchestratorConfig(
        module="finwiz.orchestrators.utility_orchestrator",
        class_name="UtilityOrchestrator",
        deps_keys=(),
    ),
    "deep_analysis": OrchestratorConfig(
        module="finwiz.orchestrators.deep_analysis_orchestrator",
        class_name="DeepAnalysisOrchestrator",
        deps_keys=("crew_factory", "integration_manager", "error_handler", "batch_prefetch_config"),
    ),
    "alternatives": OrchestratorConfig(
        module="finwiz.orchestrators.alternatives_matching_orchestrator",
        class_name="AlternativesMatchingOrchestrator",
        deps_keys=("crew_factory", "integration_manager", "error_handler"),
    ),
    "discovery": OrchestratorConfig(
        module="finwiz.orchestrators.discovery_orchestrator",
        class_name="DiscoveryOrchestrator",
        deps_keys=("availability_tracker",),
    ),
    "validation": OrchestratorConfig(
        module="finwiz.orchestrators.validation_orchestrator",
        class_name="ValidationOrchestrator",
        deps_keys=("data_accessor", "integration_manager"),
    ),
    "reporting": OrchestratorConfig(
        module="finwiz.orchestrators.reporting_orchestrator",
        class_name="ReportingOrchestrator",
        deps_keys=("integration_manager",),
    ),
}


def create_orchestrator(name: str, state: Any, deps: Any) -> Any:
    """Create an orchestrator instance by name with lazy import.

    Args:
        name: Registry key (e.g. "validation", "deep_analysis")
        state: FinwizState instance
        deps: OrchestratorDependencies instance

    Returns:
        Instantiated orchestrator

    Raises:
        KeyError: If name is not in the registry

    """
    config = ORCHESTRATOR_REGISTRY[name]
    mod = importlib.import_module(config.module)
    cls = getattr(mod, config.class_name)
    kwargs: dict[str, Any] = {"state": state}
    for key in config.deps_keys:
        kwargs[key] = getattr(deps, key)
    logger.info(f"Lazy-loaded {config.class_name}")
    return cls(**kwargs)
