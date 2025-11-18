"""
Analyzer Factory.

Factory for creating asset-specific analyzers based on asset class.
Part of Phase 2A refactoring using Strategy Pattern.
"""

from __future__ import annotations

from finwiz.scoring.asset_analyzers.base import AssetAnalyzer
from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer
from finwiz.scoring.asset_analyzers.etf_analyzer import ETFAnalyzer
from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer


class AnalyzerFactory:
    """
    Factory for creating asset-specific analyzers.

    Maps asset_class strings to appropriate analyzer implementations.
    Handles unknown asset classes gracefully with clear error messages.
    """

    # Registry of available analyzers
    _ANALYZERS = {
        "stock": StockAnalyzer,
        "etf": ETFAnalyzer,
        "crypto": CryptoAnalyzer,
    }

    @classmethod
    def get_analyzer(cls, asset_class: str) -> AssetAnalyzer:
        """
        Get the appropriate analyzer for the given asset class.

        Args:
            asset_class: Asset class (stock, etf, crypto)

        Returns:
            AssetAnalyzer instance for the specified asset class

        Raises:
            ValueError: If asset_class is not recognized

        """
        # Normalize asset class to lowercase
        normalized_class = asset_class.lower().strip()

        # Look up analyzer class
        analyzer_class = cls._ANALYZERS.get(normalized_class)

        if analyzer_class is None:
            # Unknown asset class - provide helpful error message
            valid_classes = ", ".join(cls._ANALYZERS.keys())
            raise ValueError(f"Unknown asset class: '{asset_class}'. Valid asset classes are: {valid_classes}")

        # Instantiate and return analyzer
        return analyzer_class()

    @classmethod
    def get_supported_asset_classes(cls) -> list[str]:
        """
        Get list of supported asset classes.

        Returns:
            List of supported asset class strings

        """
        return list(cls._ANALYZERS.keys())
