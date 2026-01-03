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
    from finwiz.scoring.thresholds import ScoringThresholds


class AssetAnalyzer(ABC):
    """
    Abstract base class for asset-specific analysis strategies.

    Defines the interface that all asset analyzers must implement:
    - calculate_fundamental_score: Asset-specific fundamental scoring
    - extract_metrics: Extract asset-specific metrics from data
    - validate_data: Validate asset-specific data requirements

    Phase 2A.3: Supports centralized ScoringThresholds for all thresholds.
    """

    def __init__(self) -> None:
        """Initialize base analyzer."""
        self._data_quality_metrics = None

    def set_thresholds(self, thresholds: ScoringThresholds) -> None:
        """
        Set scoring thresholds for this analyzer.

        Args:
            thresholds: ScoringThresholds instance with configured values

        """
        self.thresholds = thresholds

    def set_data_quality_metrics(self, metrics: Any) -> None:
        """
        Set data quality metrics tracker.

        Args:
            metrics: DataQualityMetrics instance for tracking field calculations

        """
        self._data_quality_metrics = metrics

    def _track_calculated_field(self, field_name: str, value: Any, default: Any) -> None:
        """
        Track whether a field was successfully calculated or defaulted.

        Args:
            field_name: Name of the field
            value: Actual value extracted
            default: Default value that would be used

        """
        if self._data_quality_metrics is None:
            return

        # If value equals default, it means we're using fallback
        if value == default or value is None:
            self._data_quality_metrics.record_defaulted_field(field_name, default)
        else:
            self._data_quality_metrics.record_calculated_field(field_name)

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
