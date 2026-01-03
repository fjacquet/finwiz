"""
Fundamental Scoring Module.

Handles fundamental analysis scoring for stocks, ETFs, and cryptocurrencies.
Extracted from DeepAnalysisScorer as part of Phase 2A refactoring.

Updated in Phase 2A.2 to use Strategy Pattern with asset-specific analyzers.
Updated in Phase 2A.3 to use centralized ScoringThresholds.
"""

from __future__ import annotations

import logging
from typing import Any

from finwiz.scoring.asset_analyzers.factory import AnalyzerFactory
from finwiz.scoring.thresholds import ScoringThresholds, get_thresholds

logger = logging.getLogger(__name__)


class FundamentalScorer:
    """
    Fundamental analysis scorer for all asset classes.

    Uses Strategy Pattern (Phase 2A.2) to delegate asset-specific logic
    to specialized analyzers:
    - StockAnalyzer: ROE, debt/equity, revenue growth, profit margins
    - ETFAnalyzer: expense ratio, tracking error, AUM, diversification
    - CryptoAnalyzer: market cap, volume, adoption metrics, tokenomics

    Phase 2A.3: Uses centralized ScoringThresholds for all thresholds.
    """

    def __init__(self, thresholds: ScoringThresholds | None = None) -> None:
        """
        Initialize the fundamental scorer.

        Args:
            thresholds: Optional custom thresholds (defaults to DEFAULT_THRESHOLDS)

        """
        self.logger = logger
        self._data_quality_metrics: Any = None
        self._current_ticker: str | None = None
        self.thresholds = thresholds or get_thresholds()

    def calculate_fundamental_score(self, asset_class: str, data: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """
        Calculate fundamental score based on asset class.

        Uses Strategy Pattern to delegate to asset-specific analyzers.

        Args:
            asset_class: Asset class (stock, etf, crypto)
            data: Dictionary containing analysis data

        Returns:
            Tuple of (score, details_dict)

        """
        try:
            # Get appropriate analyzer using factory (Strategy Pattern)
            analyzer = AnalyzerFactory.get_analyzer(asset_class)

            # Pass thresholds to analyzer
            analyzer.set_thresholds(self.thresholds)

            # Pass data quality metrics to analyzer for field tracking
            if self._data_quality_metrics is not None:
                analyzer.set_data_quality_metrics(self._data_quality_metrics)

            # Delegate to asset-specific analyzer
            return analyzer.calculate_fundamental_score(data)

        except ValueError as e:
            # Unknown asset class
            self.logger.warning(f"Unknown asset class: {asset_class} - {e}")
            return 0.5, {"error": str(e)}

    def set_context(self, ticker: str, data_quality_metrics: Any = None) -> None:
        """
        Set context for scoring operations.

        Args:
            ticker: Current ticker being scored
            data_quality_metrics: Optional data quality metrics tracker

        """
        self._current_ticker = ticker
        self._data_quality_metrics = data_quality_metrics
