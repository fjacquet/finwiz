"""
Base Asset Analyzer.

Abstract base class defining the interface for asset-specific analysis strategies.
Part of Phase 2A refactoring using Strategy Pattern.
Updated in Phase 2A.3 to support centralized ScoringThresholds.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from finwiz.scoring.scoring_thresholds import ScoringThresholds


class AssetAnalyzer(ABC):
    """
    Abstract base class for asset-specific analysis strategies.

    Defines the interface that all asset analyzers must implement:
    - calculate_fundamental_score: Asset-specific fundamental scoring
    - extract_metrics: Extract asset-specific metrics from data
    - validate_data: Validate asset-specific data requirements

    Phase 2A.3: Supports centralized ScoringThresholds for all thresholds.
    """

    def set_thresholds(self, thresholds: ScoringThresholds) -> None:
        """
        Set scoring thresholds for this analyzer.

        Args:
            thresholds: ScoringThresholds instance with configured values

        """
        self.thresholds = thresholds

    @abstractmethod
    def calculate_fundamental_score(self, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score for this asset type.

        Args:
            data: Dictionary containing analysis data

        Returns:
            Tuple of (score, details_dict) where:
            - score: Float between 0.0 and 1.0
            - details_dict: Dictionary with scoring breakdown

        """
        pass

    @abstractmethod
    def extract_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract asset-specific metrics from raw data.

        Args:
            data: Dictionary containing raw analysis data

        Returns:
            Dictionary with extracted asset-specific metrics

        """
        pass

    @abstractmethod
    def validate_data(self, data: dict[str, Any]) -> bool:
        """
        Validate that required data fields are present for this asset type.

        Args:
            data: Dictionary containing analysis data

        Returns:
            True if all required fields are present, False otherwise

        """
        pass
