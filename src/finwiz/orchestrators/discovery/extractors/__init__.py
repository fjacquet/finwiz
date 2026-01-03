"""
Opportunity extractors for A+ investment discovery.

This module provides asset-specific extractors using the Template Method pattern
to eliminate duplicate extraction logic across stock, ETF, and crypto opportunities.
"""

from finwiz.orchestrators.discovery.extractors.base import OpportunityExtractor
from finwiz.orchestrators.discovery.extractors.crypto_extractor import CryptoOpportunityExtractor
from finwiz.orchestrators.discovery.extractors.etf_extractor import ETFOpportunityExtractor
from finwiz.orchestrators.discovery.extractors.stock_extractor import StockOpportunityExtractor

__all__ = [
    "OpportunityExtractor",
    "StockOpportunityExtractor",
    "ETFOpportunityExtractor",
    "CryptoOpportunityExtractor",
]
