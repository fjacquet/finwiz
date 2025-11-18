#!/usr/bin/env python
"""
Flow orchestration logic for FinWiz application (Backward Compatibility Layer).

This module provides backward compatibility by re-exporting the refactored
FinwizFlow and related classes. All existing imports continue to work.

The actual implementation has been moved to flow_orchestrator_refactored.py
and delegated to focused orchestrator modules in finwiz.orchestrators.
"""

# Re-export refactored Flow
# Re-export dependencies for backward compatibility with tests
from finwiz.config.batch_prefetch_config import get_batch_prefetch_config
from finwiz.config.resilience_config import get_resilience_config
from finwiz.crew_factory import CrewFactory

# Re-export state classes
from finwiz.flow_state import DeepAnalysisResult, FinwizState, FlowStateManager
from finwiz.flows.flow_orchestrator_refactored import FinwizFlow, OrchestratorDependencies
from finwiz.integration.data_accessor import CrewDataAccessor
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker
from finwiz.integration.manager import CrewDataIntegrationManager

# Re-export orchestrators for direct access
from finwiz.orchestrators import (
    AlternativesMatchingOrchestrator,
    DeepAnalysisOrchestrator,
    DiscoveryOrchestrator,
    ErrorHandlingOrchestrator,
    ProgressTrackingOrchestrator,
    ReportingOrchestrator,
    UtilityOrchestrator,
    ValidationOrchestrator,
)
from finwiz.tools.logger import get_logger
from finwiz.utils.core_analysis_error_handler import CoreAnalysisErrorHandler
from finwiz.utils.retry_handler import create_retry_decorator

logger = get_logger(__name__)

__all__ = [
    # Main Flow class
    "FinwizFlow",
    "OrchestratorDependencies",
    # State classes
    "FinwizState",
    "DeepAnalysisResult",
    "FlowStateManager",
    # Orchestrators
    "ErrorHandlingOrchestrator",
    "ProgressTrackingOrchestrator",
    "UtilityOrchestrator",
    "DeepAnalysisOrchestrator",
    "AlternativesMatchingOrchestrator",
    "DiscoveryOrchestrator",
    "ValidationOrchestrator",
    "ReportingOrchestrator",
    # Dependencies (for backward compatibility with tests)
    "CrewFactory",
    "CrewDataIntegrationManager",
    "CrewDataAccessor",
    "CoreAnalysisErrorHandler",
    "DataAvailabilityTracker",
    "get_resilience_config",
    "get_batch_prefetch_config",
    "create_retry_decorator",
    # Utility function
    "plot",
]


def plot() -> None:
    """Initialize the FinWiz analysis flow and plot its structure."""
    logger.info("Plotting FinWiz analysis flow structure")
    flow = FinwizFlow()
    flow.plot()
