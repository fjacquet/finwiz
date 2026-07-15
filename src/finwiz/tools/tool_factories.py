"""
Tool factory module for standardized tool initialization across FinWiz crews.

This module provides factory functions to create consistent tool sets for
different crew types (stock, crypto, ETF), eliminating code duplication and
ensuring uniform tool configuration.
"""

from crewai.tools import BaseTool
from crewai_custom_tools import DirectoryReadTool, FileReadTool

from finwiz.tools.etf_analysis_tool import get_etf_analysis_tool
from finwiz.tools.finance_tools import (
    get_crypto_research_tools,
    get_etf_research_tools,
    get_stock_research_tools,
)
from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
from finwiz.tools.valuation_tool import get_valuation_tool


def get_stock_crew_tools(
    include_quantitative: bool = True,
    include_valuation: bool = True,
    prefetched_data: dict | None = None,
) -> list[BaseTool]:
    """
    Get standardized tool set for Stock Crew.

    Args:
        include_quantitative: Whether to include quantitative analysis tool
        include_valuation: Whether to include valuation tool (DCF, P/E, technical targets)
        prefetched_data: Optional pre-fetched data for batch mode (Requirements 17.48, 17.49, 17.50)
            When None, tools use live API calls (single-ticker mode)
            When provided, tools use pre-fetched data (batch mode)

    Returns:
        List of configured tools for stock analysis

    """
    tools: list[BaseTool] = []

    # Core research tools
    tools.extend(get_stock_research_tools())

    # Optional quantitative analysis tool
    if include_quantitative:
        tools.append(get_quantitative_analysis_tool())

    # Optional valuation tool
    if include_valuation:
        tools.append(get_valuation_tool())

    # Schema and contract reading tools
    tools.extend(
        [
            DirectoryReadTool(directory="output/stock"),
            DirectoryReadTool(directory="docs/schemas"),
            DirectoryReadTool(directory="docs/schemas/examples"),
            FileReadTool(file_path="docs/schemas/MarketSentiment.schema.json"),
            FileReadTool(file_path="docs/schemas/TenKInsight.schema.json"),
            FileReadTool(file_path="docs/schemas/examples/market_sentiment.example.json"),
            FileReadTool(file_path="docs/schemas/examples/tenk_insight.example.json"),
        ]
    )

    return tools


def get_crypto_crew_tools(
    include_quantitative: bool = True,
    prefetched_data: dict | None = None,
) -> list[BaseTool]:
    """
    Get standardized tool set for Crypto Crew.

    Args:
        include_quantitative: Whether to include quantitative analysis tool
        prefetched_data: Optional pre-fetched data for batch mode (Requirements 17.48, 17.49, 17.50)
            When None, tools use live API calls (single-ticker mode)
            When provided, tools use pre-fetched data (batch mode)

    Returns:
        List of configured tools for crypto analysis

    """
    tools: list[BaseTool] = []

    # Core research tools
    tools.extend(get_crypto_research_tools())

    # Optional quantitative analysis tool
    if include_quantitative:
        tools.append(get_quantitative_analysis_tool())

    # Schema and contract reading tools
    tools.extend(
        [
            DirectoryReadTool(directory="output/crypto"),
            DirectoryReadTool(directory="docs/schemas"),
            DirectoryReadTool(directory="docs/schemas/examples"),
            FileReadTool(file_path="docs/schemas/CryptoThesis.schema.json"),
            FileReadTool(file_path="docs/schemas/RiskAssessmentStandardized.schema.json"),
            FileReadTool(file_path="docs/schemas/examples/crypto_thesis.example.json"),
        ]
    )

    return tools


def get_etf_crew_tools(
    include_quantitative: bool = True,
    include_etf_analysis: bool = True,
    prefetched_data: dict | None = None,
) -> list[BaseTool]:
    """
    Get standardized tool set for ETF Crew.

    Args:
        include_quantitative: Whether to include quantitative analysis tool
        include_etf_analysis: Whether to include ETF-specific analysis tool (tracking error, liquidity, etc.)
        prefetched_data: Optional pre-fetched data for batch mode (Requirements 17.48, 17.49, 17.50)
            When None, tools use live API calls (single-ticker mode)
            When provided, tools use pre-fetched data (batch mode)

    Returns:
        List of configured tools for ETF analysis

    """
    tools: list[BaseTool] = []

    # Core research tools
    tools.extend(get_etf_research_tools())

    # Optional quantitative analysis tool
    if include_quantitative:
        tools.append(get_quantitative_analysis_tool())

    # Optional ETF-specific analysis tool
    if include_etf_analysis:
        tools.append(get_etf_analysis_tool())

    # Schema and contract reading tools
    tools.extend(
        [
            DirectoryReadTool(directory="output/etf"),
            DirectoryReadTool(directory="docs/schemas"),
            DirectoryReadTool(directory="docs/schemas/examples"),
            FileReadTool(file_path="docs/schemas/ETFFactsheet.schema.json"),
            FileReadTool(file_path="docs/schemas/ETFTopHolding.schema.json"),
            FileReadTool(file_path="docs/schemas/examples/etf_factsheet.example.json"),
            FileReadTool(file_path="docs/schemas/RiskAssessmentStandardized.schema.json"),
        ]
    )

    return tools
