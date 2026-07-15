"""
Finance tool initialization module for FinWiz crews.

This module provides convenient functions to initialize and register
financial data tools for use in FinWiz crews.
"""

from crewai.tools import BaseTool
from crewai_custom_tools import (
    AlphaVantageNewsSentimentTool,
    ChartImgTool,
    DeFiMetricsTool,
    KrakenTickerInfoTool,
    StandardizedRiskScoringTool,
    TickerExistenceValidationTool,
    YahooFinanceCompanyInfoTool,
    YahooFinanceETFHoldingsTool,
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)

from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.tools.alpha_vantage_tool import AlphaVantageCompanyOverviewTool
from finwiz.tools.backtesting_tool import BacktestingTool
from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool
from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool
from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool
from finwiz.tools.logger import get_logger
from finwiz.tools.market_screening_tool import MarketScreeningTool
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
from finwiz.tools.regulatory_compliance_tool import RegulatoryComplianceTool
from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool
from finwiz.tools.twelve_data_tool import TwelveDataIndicatorTool

_logger = get_logger(__name__)


def _safe_init(tool_class: type[BaseTool]) -> BaseTool | None:
    """Instantiate a tool, returning None if a required API key is missing."""
    try:
        return tool_class()
    except ValueError as exc:
        _logger.info("Skipping %s: %s", tool_class.__name__, exc)
        return None


def get_stock_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for stock research.

    Returns:
        list[BaseTool]: A list of tools focused on stock analysis.

    """
    # Public API tools (no key required) + central tools that check keys lazily in _run
    tools: list[BaseTool] = [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceCompanyInfoTool(),
        YahooFinanceNewsTool(),
        TickerExistenceValidationTool(),
        EnhancedSECAnalysisTool(),
        StandardizedRiskScoringTool(),
        StandardizedSentimentAnalysisTool(),
        AlphaVantageNewsSentimentTool(),
        ChartImgTool(),
    ]
    # API-key-gated tools (skip if key missing; these still fail fast at construction)
    for cls in (AlphaVantageCompanyOverviewTool, TwelveDataIndicatorTool):
        t = _safe_init(cls)
        if t:
            tools.append(t)
    return tools


def get_crypto_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for crypto research.

    Returns:
        list[BaseTool]: A list of tools focused on crypto analysis.

    """
    tools: list[BaseTool] = [
        YahooFinanceHistoryTool(),
        YahooFinanceNewsTool(),
        YahooFinanceTickerInfoTool(),
        KrakenTickerInfoTool(),
        TickerExistenceValidationTool(),
        EnhancedCryptoAnalysisTool(),
        DeFiMetricsTool(),
        RegulatoryComplianceTool(),
        StandardizedRiskScoringTool(),
        StandardizedSentimentAnalysisTool(),
        AlphaVantageNewsSentimentTool(),
        ChartImgTool(),
    ]
    t = _safe_init(TwelveDataIndicatorTool)
    if t:
        tools.append(t)
    return tools


def get_etf_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for ETF research.

    Returns:
        list[BaseTool]: A list of tools focused on ETF analysis.

    """
    tools: list[BaseTool] = [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceETFHoldingsTool(),
        YahooFinanceNewsTool(),
        TickerExistenceValidationTool(),
        EnhancedETFAnalysisTool(),
        StandardizedRiskScoringTool(),
        StandardizedSentimentAnalysisTool(),
        AlphaVantageNewsSentimentTool(),
        ChartImgTool(),
    ]
    t = _safe_init(TwelveDataIndicatorTool)
    if t:
        tools.append(t)
    return tools


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
    ]


def get_stock_discovery_tools() -> list[BaseTool]:
    """
    Get tools optimized for stock discovery with fundamental analysis and screening.

    Provides the fundamental_analysis_tool, stock_screening_tool, and a_plus_scoring_tool
    capabilities required for stock discovery agents.

    Returns:
        list[BaseTool]: A list of tools focused on stock discovery and fundamental analysis.

    """
    # Public API tools (no key required)
    tools: list[BaseTool] = [
        # Core discovery tools
        MarketScreeningTool(),  # Provides stock_screening_tool functionality
        APlusScoringTool(),  # Provides a_plus_scoring_tool functionality
        # Fundamental analysis tools (provides fundamental_analysis_tool functionality)
        EnhancedSECAnalysisTool(),  # 10-K/10-Q analysis for fundamental insights
        YahooFinanceCompanyInfoTool(),  # Company fundamentals and metrics
        YahooFinanceTickerInfoTool(),  # Financial ratios and key metrics
        # Supporting analysis tools
        QuantitativeAnalysisTool(),  # Quantitative metrics and ratios
        StandardizedRiskScoringTool(),  # Risk assessment
        StandardizedSentimentAnalysisTool(),  # Market sentiment analysis
        TickerExistenceValidationTool(),  # Ticker validation
        # Historical and technical analysis
        YahooFinanceHistoryTool(),  # Price history for trend analysis
        # News and sentiment
        YahooFinanceNewsTool(),  # Company news analysis
        AlphaVantageNewsSentimentTool(),  # Central tool: checks key lazily in _run, always included
    ]
    # API-key-gated tools (skip if key missing; these still fail fast at construction)
    for cls in (AlphaVantageCompanyOverviewTool, TwelveDataIndicatorTool):
        t = _safe_init(cls)
        if t:
            tools.append(t)
    return tools


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
