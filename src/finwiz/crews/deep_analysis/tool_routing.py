"""
Tool routing for DeepAnalysisCrew.

Provides dynamic tool selection based on asset class and optimization mode.
Extracted from deep_analysis.py for maintainability.
"""

from typing import Any

from finwiz.tools.logger import get_logger
from finwiz.tools.robust_tool_wrapper import make_tools_robust

logger = get_logger(__name__)


def get_tools_for_asset_class(
    asset_class: str,
    minimal: bool = False,
    prefetched_data: dict[str, dict[str, Any]] | None = None,
    use_minimal_tools: bool = False,
) -> list[Any]:
    """
    Route to appropriate tool set based on asset class and optimization mode.

    For deep analysis crew, we use a LEAN tool set that excludes file/directory
    reading tools to prevent context overflow. The AI receives summarized metrics
    as input and only needs web search/research tools for qualitative analysis.

    Args:
        asset_class: One of "stock", "etf", "crypto"
        minimal: If True, return minimal tool set (for risk assessment only)
        prefetched_data: Pre-fetched data for batch mode
        use_minimal_tools: If True, use minimal tools regardless of minimal flag

    Returns:
        List of tools appropriate for the asset class

    Raises:
        ValueError: If asset_class is not valid

    """
    asset_class_lower = asset_class.lower()

    # Use minimal tool set for maximum speed mode
    if minimal or use_minimal_tools:
        return _get_minimal_risk_tools(asset_class_lower, prefetched_data)

    # Get LEAN tools for deep analysis (excludes DirectoryReadTool/FileReadTool)
    # to prevent context overflow from reading large files
    raw_tools = _get_lean_analysis_tools(asset_class_lower, prefetched_data)

    # Apply robust wrapper for error handling
    tools = make_tools_robust(raw_tools)

    # Log batch mode status
    if prefetched_data:
        logger.info(f"Loaded {len(tools)} LEAN tools for asset_class: {asset_class} (BATCH MODE)")
    else:
        logger.info(f"Loaded {len(tools)} LEAN tools for asset_class: {asset_class} (LIVE MODE)")

    return tools


def _get_lean_analysis_tools(
    asset_class: str,
    prefetched_data: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Get LEAN tool set for deep qualitative analysis.

    This function provides essential research tools while EXCLUDING
    DirectoryReadTool and FileReadTool to prevent context overflow.
    The AI receives summarized Python metrics as input and only needs
    research tools for qualitative insights.

    CRITICAL: This prevents the 300K+ token overflow error by excluding
    tools that could read arbitrary large files.

    Args:
        asset_class: One of "stock", "etf", "crypto"
        prefetched_data: Pre-fetched data for batch mode

    Returns:
        Lean list of tools for qualitative analysis

    """
    from finwiz.tools.finance_tools import (
        get_crypto_research_tools,
        get_etf_research_tools,
        get_stock_research_tools,
    )
    from finwiz.tools.quantitative_analysis_tool import get_quantitative_analysis_tool
    from finwiz.tools.valuation_tool import get_valuation_tool

    tools: list[Any] = []

    # Core research tools (NO file/directory reading)
    if asset_class == "stock":
        tools.extend(get_stock_research_tools())
    elif asset_class == "etf":
        tools.extend(get_etf_research_tools())
    elif asset_class == "crypto":
        tools.extend(get_crypto_research_tools())
    else:
        raise ValueError(f"Invalid asset_class: {asset_class}. Must be one of: stock, etf, crypto")

    # Include quantitative and valuation tools
    tools.append(get_quantitative_analysis_tool())
    tools.append(get_valuation_tool())

    # EXCLUDED to prevent context overflow:
    # - DirectoryReadTool (can read entire directories)
    # - FileReadTool (can read arbitrary files)
    # - RAG tools (disabled by design)

    logger.info(f"⚡ LEAN TOOLS: Loaded {len(tools)} tools for {asset_class} qualitative analysis (DirectoryReadTool/FileReadTool EXCLUDED to prevent context overflow)")
    return tools


def _get_minimal_risk_tools(
    asset_class: str,
    prefetched_data: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Get minimal tool set for risk assessment only (Phase 2 optimization).

    Reduces tool initialization overhead and focuses on essential tools
    needed for risk calculation.

    Args:
        asset_class: One of "stock", "etf", "crypto"
        prefetched_data: Pre-fetched data for batch mode

    Returns:
        Minimal list of tools for risk assessment

    """
    from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool
    from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool
    from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool
    from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
    from finwiz.tools.ticker_validation_tool import TickerValidationTool

    tools: list[Any] = []

    # Always include quantitative analysis (core risk metrics)
    tools.append(QuantitativeAnalysisTool(asset_class=asset_class, prefetched_data=prefetched_data))

    # Always include ticker validation
    tools.append(TickerValidationTool())

    # Asset-specific tools (only essential ones)
    if asset_class == "stock":
        tools.append(EnhancedSECAnalysisTool(prefetched_data=prefetched_data))
    elif asset_class == "etf":
        tools.append(EnhancedETFAnalysisTool(prefetched_data=prefetched_data))
    elif asset_class == "crypto":
        tools.append(EnhancedCryptoAnalysisTool(prefetched_data=prefetched_data))

    # Apply robust wrapper
    tools = make_tools_robust(tools)

    logger.info(f"⚡ PHASE 2: Loaded {len(tools)} minimal tools for risk assessment ({asset_class})")
    return tools
