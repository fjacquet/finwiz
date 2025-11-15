"""
Asset Analyzer Strategy Pattern.

Provides asset-specific analysis strategies for stocks, ETFs, and cryptocurrencies.
Part of Phase 2A refactoring to eliminate duplicate conditional logic.
"""

from finwiz.scoring.asset_analyzers.base import AssetAnalyzer
from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer
from finwiz.scoring.asset_analyzers.etf_analyzer import ETFAnalyzer
from finwiz.scoring.asset_analyzers.factory import AnalyzerFactory
from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer

__all__ = [
    "AssetAnalyzer",
    "StockAnalyzer",
    "ETFAnalyzer",
    "CryptoAnalyzer",
    "AnalyzerFactory",
]
