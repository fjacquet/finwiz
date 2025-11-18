"""
Opportunity extractors for A+ investment discovery.

This module provides asset-specific extractors using the Template Method pattern
to eliminate duplicate extraction logic across stock, ETF, and crypto opportunities.
"""

from finwiz.integration.opportunity_extractors.base import OpportunityExtractor
from finwiz.integration.opportunity_extractors.crypto_extractor import CryptoOpportunityExtractor
from finwiz.integration.opportunity_extractors.etf_extractor import ETFOpportunityExtractor
from finwiz.integration.opportunity_extractors.stock_extractor import StockOpportunityExtractor

__all__ = [
    "OpportunityExtractor",
    "StockOpportunityExtractor",
    "ETFOpportunityExtractor",
    "CryptoOpportunityExtractor",
]
