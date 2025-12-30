"""
Flow State Management for FinWiz Application.

This module provides state management for the CrewAI flow execution.
Models are defined in flow_state_models.py, utility functions in flow_state_utils.py.
"""

import os
from typing import Any

from finwiz.tools.logger import get_logger

# Import models from dedicated module
from .flow_state_models import DeepAnalysisResult, FinwizState

# Import utility functions from dedicated module
from .flow_state_utils import (
    check_core_analysis_availability,
    extract_market_conditions,
    extract_market_context_from_core_analysis,
    get_degraded_functionality_summary,
    prepare_core_analysis_summary,
)

# Re-export for backward compatibility
__all__ = [
    "DeepAnalysisResult",
    "FinwizState",
    "FlowStateManager",
]


class FlowStateManager:
    """Manages flow state and provides state-related utilities.

    This is a thin coordinator that delegates analysis operations to
    dedicated utility functions in flow_state_utils.py.
    """

    def __init__(self) -> None:
        """Initialize the FlowStateManager."""
        self.logger = get_logger(__name__)

    def create_initial_state(self) -> FinwizState:
        """Create initial FinwizState with session information from environment.

        Returns:
            FinwizState: Initialized state with session metadata
        """
        has_existing_session = os.getenv("FINWIZ_HAS_EXISTING_SESSION", "false") == "true"
        session_id = os.getenv("FINWIZ_SESSION_ID", "")
        analysis_count = int(os.getenv("FINWIZ_ANALYSIS_COUNT", "0"))

        state = FinwizState(
            has_existing_session=has_existing_session,
            session_id=session_id,
            analysis_count=analysis_count,
        )

        self.logger.debug(f"Flow state initialized with timestamp: {state.timestamp}")

        if state.has_existing_session:
            self.logger.debug(f"Flow initialized with existing session: {state.session_id}")
        else:
            self.logger.debug("Flow initialized without existing session")

        return state

    def check_core_analysis_availability(self, state: FinwizState) -> dict[str, Any]:
        """Check which core analysis crews are available and their status.

        Delegates to flow_state_utils.check_core_analysis_availability().
        """
        return check_core_analysis_availability(state, self.logger)

    def extract_market_conditions(self, state: FinwizState) -> dict[str, Any]:
        """Extract market conditions from core analysis results.

        Delegates to flow_state_utils.extract_market_conditions().
        """
        return extract_market_conditions(state)

    def extract_market_context_from_core_analysis(
        self, core_analysis_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract market context information from core analysis results.

        Args:
            core_analysis_data: Dictionary containing core analysis results

        Returns:
            Dictionary with extracted market context

        Delegates to flow_state_utils.extract_market_context_from_core_analysis().
        """
        return extract_market_context_from_core_analysis(core_analysis_data, self.logger)

    def prepare_core_analysis_summary(
        self, consolidated_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Prepare a summary of core analysis results for the reporter.

        Args:
            consolidated_data: Consolidated data from all crews

        Returns:
            Dictionary with core analysis summary

        Delegates to flow_state_utils.prepare_core_analysis_summary().
        """
        return prepare_core_analysis_summary(consolidated_data, self.logger)

    def get_degraded_functionality_summary(self, state: FinwizState) -> dict[str, Any]:
        """Get summary of degraded functionality across the system.

        Delegates to flow_state_utils.get_degraded_functionality_summary().
        """
        return get_degraded_functionality_summary(state)
