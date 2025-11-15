"""Unit tests for AnalyzerFactory."""

import pytest

from finwiz.scoring.asset_analyzers.crypto_analyzer import CryptoAnalyzer
from finwiz.scoring.asset_analyzers.etf_analyzer import ETFAnalyzer
from finwiz.scoring.asset_analyzers.factory import AnalyzerFactory
from finwiz.scoring.asset_analyzers.stock_analyzer import StockAnalyzer


class TestAnalyzerFactory:
    """Test suite for AnalyzerFactory."""

    def test_get_analyzer_stock(self):
        """Test getting stock analyzer."""
        analyzer = AnalyzerFactory.get_analyzer("stock")
        assert isinstance(analyzer, StockAnalyzer)

    def test_get_analyzer_etf(self):
        """Test getting ETF analyzer."""
        analyzer = AnalyzerFactory.get_analyzer("etf")
        assert isinstance(analyzer, ETFAnalyzer)

    def test_get_analyzer_crypto(self):
        """Test getting crypto analyzer."""
        analyzer = AnalyzerFactory.get_analyzer("crypto")
        assert isinstance(analyzer, CryptoAnalyzer)

    def test_get_analyzer_case_insensitive(self):
        """Test that asset class is case-insensitive."""
        analyzer_upper = AnalyzerFactory.get_analyzer("STOCK")
        analyzer_mixed = AnalyzerFactory.get_analyzer("Stock")
        analyzer_lower = AnalyzerFactory.get_analyzer("stock")

        assert isinstance(analyzer_upper, StockAnalyzer)
        assert isinstance(analyzer_mixed, StockAnalyzer)
        assert isinstance(analyzer_lower, StockAnalyzer)

    def test_get_analyzer_with_whitespace(self):
        """Test that whitespace is handled."""
        analyzer = AnalyzerFactory.get_analyzer("  stock  ")
        assert isinstance(analyzer, StockAnalyzer)

    def test_get_analyzer_unknown_asset_class(self):
        """Test error handling for unknown asset class."""
        with pytest.raises(ValueError) as exc_info:
            AnalyzerFactory.get_analyzer("bond")

        error_message = str(exc_info.value)
        assert "Unknown asset class" in error_message
        assert "bond" in error_message
        assert "stock" in error_message
        assert "etf" in error_message
        assert "crypto" in error_message

    def test_get_supported_asset_classes(self):
        """Test getting list of supported asset classes."""
        supported = AnalyzerFactory.get_supported_asset_classes()

        assert isinstance(supported, list)
        assert "stock" in supported
        assert "etf" in supported
        assert "crypto" in supported
        assert len(supported) == 3
