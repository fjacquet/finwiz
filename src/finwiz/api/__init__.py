"""
FinWiz API module for REST endpoints.

This module provides REST API endpoints for FinWiz functionality,
including portfolio rebalancing, analysis, and monitoring.
"""

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

__all__ = ["create_app", "rebalancing_router"]
