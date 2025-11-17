"""
Orchestrator modules for FinWiz Flow.

This package contains focused orchestrator modules that handle specific aspects
of the FinWiz workflow. Each orchestrator has a single, clearly defined responsibility
and is designed to be < 300 lines of code.

Orchestrators:
- ErrorHandlingOrchestrator: Crew execution error handling and error aggregation
- ProgressTrackingOrchestrator: Progress calculation and metrics persistence
- UtilityOrchestrator: Data parsing, grade calculation, URL extraction/validation
- DeepAnalysisOrchestrator: Deep analysis execution and result creation
- AlternativesMatchingOrchestrator: A+ alternative matching for underperforming holdings
- DiscoveryOrchestrator: Discovery crew execution and result consolidation
- ValidationOrchestrator: Input validation and data availability checking
- ReportingOrchestrator: Report consolidation and HTML generation
"""

# Orchestrators will be imported here as they are implemented
from finwiz.orchestrators.error_handling_orchestrator import ErrorHandlingOrchestrator
from finwiz.orchestrators.progress_tracking_orchestrator import ProgressTrackingOrchestrator
# from finwiz.orchestrators.utility_orchestrator import UtilityOrchestrator
# from finwiz.orchestrators.deep_analysis_orchestrator import DeepAnalysisOrchestrator
# from finwiz.orchestrators.alternatives_matching_orchestrator import AlternativesMatchingOrchestrator
# from finwiz.orchestrators.discovery_orchestrator import DiscoveryOrchestrator
# from finwiz.orchestrators.validation_orchestrator import ValidationOrchestrator
# from finwiz.orchestrators.reporting_orchestrator import ReportingOrchestrator

__all__ = [
    # Orchestrators will be added here as they are implemented
    "ErrorHandlingOrchestrator",
    "ProgressTrackingOrchestrator",
    # "UtilityOrchestrator",
    # "DeepAnalysisOrchestrator",
    # "AlternativesMatchingOrchestrator",
    # "DiscoveryOrchestrator",
    # "ValidationOrchestrator",
    # "ReportingOrchestrator",
]
