"""
Finance tool initialization module for FinWiz crews.

This module provides convenient functions to initialize and register
financial data tools for use in FinWiz crews.
"""

from crewai.tools import BaseTool

from finwiz.tools.yahoo_finance_tool import (
    YahooFinanceCompanyInfoTool,
    YahooFinanceETFHoldingsTool,
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)


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
    ]


def get_crypto_research_tools() -> list[BaseTool]:
    """
    Get tools optimized for cryptocurrency research.

    Returns:
        list[BaseTool]: A list of tools focused on cryptocurrency analysis.

    """
    return [
        YahooFinanceTickerInfoTool(),
        YahooFinanceHistoryTool(),
        YahooFinanceNewsTool(),
    ]

