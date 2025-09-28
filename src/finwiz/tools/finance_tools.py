"""
Finance tool initialization module for FinWiz crews.

This module provides convenient functions to initialize and register
financial data tools for use in FinWiz crews.
"""

from crewai.tools import BaseTool

from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.alpha_vantage_news_tool import AlphaVantageNewsSentimentTool
from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.backtesting_tool import BacktestingTool
from finwiz.tools.chart_img_tool import ChartImgTool
from finwiz.tools.defi_metrics_tool import DeFiMetricsTool
from finwiz.tools.enhanced_crypto_tool import (
    CryptoRiskScoringTool,
    CryptoThesisGeneratorTool,
    EnhancedCryptoAnalysisTool,
)
from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool, ETFTrackingAnalysisTool
from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool, StandardizedRiskScoringTool
from finwiz.tools.kraken_api_tool import KrakenTickerInfoTool
from finwiz.tools.market_screening_tool import MarketScreeningTool
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
from finwiz.tools.regulatory_compliance_tool import RegulatoryComplianceTool
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
        # DeFi and regulatory analysis tools
        DeFiMetricsTool(),
        RegulatoryComplianceTool(),
        # Risk scoring tools
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


def get_investment_discovery_tools() -> list[BaseTool]:
    """
    Get tools optimized for A+ investment discovery.

    Returns:
        list[BaseTool]: A list of tools focused on discovering A+ grade investments.

    """
    return [
        APlusScoringTool(),
        MarketScreeningTool(),
        BacktestingTool(),
        TickerExistenceValidationTool(),
        StandardizedRiskScoringTool(),
        StandardizedSentimentAnalysisTool(),
        CrossAssetSentimentComparatorTool(),
    ]


def get_stock_discovery_tools() -> list[BaseTool]:
    """
    Get tools optimized for stock discovery with fundamental analysis and screening.

    Provides the fundamental_analysis_tool, stock_screening_tool, and a_plus_scoring_tool
    capabilities required for stock discovery agents.

    Returns:
        list[BaseTool]: A list of tools focused on stock discovery and fundamental analysis.

    """
    return [
        # Core discovery tools
        MarketScreeningTool(),  # Provides stock_screening_tool functionality
        APlusScoringTool(),  # Provides a_plus_scoring_tool functionality
        # Fundamental analysis tools (provides fundamental_analysis_tool functionality)
        EnhancedSECAnalysisTool(),  # 10-K/10-Q analysis for fundamental insights
        YahooFinanceCompanyInfoTool(),  # Company fundamentals and metrics
        YahooFinanceTickerInfoTool(),  # Financial ratios and key metrics
        AlphaVantageCompanyOverviewTool(),  # Additional fundamental data
        # Supporting analysis tools
        QuantitativeAnalysisTool(),  # Quantitative metrics and ratios
        StandardizedRiskScoringTool(),  # Risk assessment
        StandardizedSentimentAnalysisTool(),  # Market sentiment analysis
        TickerExistenceValidationTool(),  # Ticker validation
        # Historical and technical analysis
        YahooFinanceHistoryTool(),  # Price history for trend analysis
        TwelveDataIndicatorTool(),  # Technical indicators
        # News and sentiment
        YahooFinanceNewsTool(),  # Company news analysis
        AlphaVantageNewsSentimentTool(),  # News sentiment scoring
    ]


# Tool aliases for backward compatibility and explicit naming
def fundamental_analysis_tool() -> BaseTool:
    """
    Alias for Enhanced SEC Analysis Tool - provides fundamental analysis capabilities.

    Returns:
        BaseTool: Enhanced SEC Analysis Tool for fundamental analysis.

    """
    return EnhancedSECAnalysisTool()


def stock_screening_tool() -> BaseTool:
    """
    Alias for Market Screening Tool configured for stocks.

    Returns:
        BaseTool: Market Screening Tool for stock screening.

    """
    return MarketScreeningTool()
