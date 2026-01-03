"""
FinWiz Crew Data Integration System.

This module provides centralized data integration and coordination between crews.
After migration, this module only contains core data access functionality.
"""

from .config import (
    CrewDependencyConfig,
    DataQualityConfig,
    IntegrationConfig,
    get_crew_dependency_config,
    get_data_quality_config,
    get_integration_config,
)
from .accessor import CrewDataAccessor
from .manager import CrewDataIntegrationManager

__all__ = [
    "CrewDataIntegrationManager",
    "CrewDataAccessor",
    "IntegrationConfig",
    "CrewDependencyConfig",
    "DataQualityConfig",
    "get_integration_config",
    "get_crew_dependency_config",
    "get_data_quality_config",
]
