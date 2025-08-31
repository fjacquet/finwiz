"""
Finance tool initialization module for FinWiz crews.

This module provides convenient functions to initialize and register
financial data tools for use in FinWiz crews.
"""

from crewai.tools import BaseTool

from finwiz.tools.alpha_vantage_news_tool import AlphaVantageNewsSentimentTool
from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.chart_img_tool import ChartImgTool
from finwiz.tools.enhanced_crypto_tool import (
    CryptoRiskScoringTool,
    CryptoThesisGeneratorTool,
    EnhancedCryptoAnalysisTool,
)
from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool, ETFTrackingAnalysisTool
from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool, StandardizedRiskScoringTool
from finwiz.tools.kraken_api_tool import KrakenTickerInfoTool
from finwiz.tools.sec_tool import SECFilingSearchTool
from finwiz.tools.standardized_sentiment_tool import (
    CrossAssetSentimentComparatorTool,
    StandardizedSentimentAnalysisTool,
)
from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool
from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool
from finwiz.tools.yahoo_finance_company_info_tool import YahooFinanceCompanyInfoTool
from finwiz.tools.yahoo_finance_etf_holdings_tool import YahooFinanceETFHoldingsTool
from finwiz.tools.yahoo_finance_history_tool import YahooFinanceHistoryTool
from finwiz.tools.yahoo_finance_news_tool import YahooFinanceNewsTool
from finwiz.tools.yahoo_finance_ticker_info_tool import YahooFinanceTickerInfoTool


def get_yahoo_finance_tools() -> list[BaseTool]:
    """
    Initialize and return all Yahoo Finance tools.

    Returns:
        list[BaseTool]: A list of initialized Yahoo Finance tools ready for crew usage.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceCompanyInfoTool(),
        YahooFinanceETFHoldingsTool(),
        YahooFinanceNewsTool(),
    ]


def get_stock_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for stock research.

    Returns:
        list[BaseTool]: A list of tools focused on stock analysis.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceCompanyInfoTool(),
        YahooFinanceNewsTool(),
        AlphaVantageCompanyOverviewTool(),
        AlphaVantageNewsSentimentTool(),
        TwelveDataIndicatorTool(),
        ChartImgTool(),
        TickerExistenceValidationTool(),
        # Enhanced SEC analysis tools
        EnhancedSECAnalysisTool(),
        SECFilingSearchTool(),
        StandardizedRiskScoringTool(),
        # Standardized sentiment analysis
        StandardizedSentimentAnalysisTool(),
        CrossAssetSentimentComparatorTool(),
    ]


def get_crypto_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for crypto research.

    Returns:
        list[BaseTool]: A list of tools focused on crypto analysis.

    """
    return [
        YahooFinanceHistoryTool(),
        YahooFinanceNewsTool(),
        YahooFinanceTickerInfoTool(),
        KrakenTickerInfoTool(),
        AlphaVantageNewsSentimentTool(),
        TwelveDataIndicatorTool(),
        ChartImgTool(),
        TickerExistenceValidationTool(),
        # Enhanced crypto analysis tools
        EnhancedCryptoAnalysisTool(),
        CryptoThesisGeneratorTool(),
        CryptoRiskScoringTool(),
        StandardizedRiskScoringTool(),
        # Standardized sentiment analysis
        StandardizedSentimentAnalysisTool(),
        CrossAssetSentimentComparatorTool(),
    ]


def get_etf_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for ETF research.

    Returns:
        list[BaseTool]: A list of tools focused on ETF analysis.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceETFHoldingsTool(),
        YahooFinanceNewsTool(),
        AlphaVantageNewsSentimentTool(),
        TwelveDataIndicatorTool(),
        ChartImgTool(),
        TickerExistenceValidationTool(),
        # Enhanced ETF analysis tools
        EnhancedETFAnalysisTool(),
        ETFTrackingAnalysisTool(),
        StandardizedRiskScoringTool(),
        # Standardized sentiment analysis
        StandardizedSentimentAnalysisTool(),
        CrossAssetSentimentComparatorTool(),
    ]
