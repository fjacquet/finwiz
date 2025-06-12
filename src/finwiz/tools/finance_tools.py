"""
Finance tool initialization module for FinWiz crews.

This module provides convenient functions to initialize and register
financial data tools for use in FinWiz crews.
"""

from crewai.tools import BaseTool

# from finwiz.tools.html_output_tool import HTMLOutputTool
# from finwiz.tools.html_parser_tool import HTMLParserTool
# from finwiz.tools.json_output_tool import JSONOutputTool
# from finwiz.tools.json_parser_tool import JSONParserTool
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


# def get_report_integration_tools() -> list[BaseTool]:
#     """
#     Get tools optimized for report integration and analysis.

#     These tools are designed for analyzing and integrating information
#     from other crews without conducting additional external research.

#     Returns:
#         list[BaseTool]: A list of tools focused on report integration and analysis.

#     """
#     return [
#         HTMLParserTool(),
#         JSONParserTool(),
#         JSONOutputTool(),
#         HTMLOutputTool(),
#     ]


# def get_data_output_tools() -> list[BaseTool]:
#     """
#     Get tools for standardized data output.

#     These tools enable crews to produce structured data outputs
#     that can be easily consumed by other crews, particularly
#     the Report Crew.

#     Returns:
#         list[BaseTool]: A list of tools for standardized data output.

#     """
#     return [
#         JSONOutputTool(),
#     ]
