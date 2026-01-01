"""
Tool routing helpers for CrewAI crews.

This module provides functions for routing tools based on asset class
and optimization mode. These functions are externalized from crew classes
to make them testable and reusable.
"""

from typing import Any

from crewai.tools import BaseTool

from finwiz.tools.logger import get_logger
from finwiz.tools.robust_tool_wrapper import make_tools_robust
from finwiz.tools.tool_factories import (
    get_crypto_crew_tools,
    get_etf_crew_tools,
    get_stock_crew_tools,
)
from finwiz.utils.performance_config import get_performance_config_manager

logger = get_logger(__name__)


def get_tools_for_asset_class(
    asset_class: str,
    minimal: bool = False,
    prefetched_data: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Route to appropriate tool set based on asset class and optimization mode.

    If pre-fetched data is available, tools will be configured to use it
    instead of making live API calls.

    Args:
        asset_class: One of "stock", "etf", "crypto"
        minimal: If True, return minimal tool set (for risk assessment only)
        prefetched_data: Optional pre-fetched data for batch mode

    Returns:
        List of tools appropriate for the asset class

    Raises:
        ValueError: If asset_class is not valid

    """
    asset_class_lower = asset_class.lower()

    # Check optimization mode for tool selection
    perf_config = get_performance_config_manager()
    use_minimal_tools = minimal or perf_config.should_use_minimal_tools()

    # ⚡ OPTIMIZATION: Minimal tool set for maximum speed mode
    if use_minimal_tools:
        return get_minimal_risk_tools(asset_class_lower, prefetched_data)

    if asset_class_lower == "stock":
        raw_tools = get_stock_crew_tools(
            include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
            include_quantitative=True,
            collection_suffix="stock_deep",
            prefetched_data=prefetched_data,
        )
    elif asset_class_lower == "etf":
        raw_tools = get_etf_crew_tools(
            include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
            include_quantitative=True,
            collection_suffix="etf_deep",
            prefetched_data=prefetched_data,
        )
    elif asset_class_lower == "crypto":
        raw_tools = get_crypto_crew_tools(
            include_rag=False,  # ⚡ OPTIMIZED: Disabled RAG for faster execution
            include_quantitative=True,
            collection_suffix="crypto_deep",
            prefetched_data=prefetched_data,
        )
    else:
        raise ValueError(f"Invalid asset_class: {asset_class}. Must be one of: stock, etf, crypto")

    # Apply robust wrapper for error handling
    tools = make_tools_robust(raw_tools)

    # Log batch mode status
    if prefetched_data:
        logger.info(f"Loaded {len(tools)} tools for asset_class: {asset_class} (BATCH MODE with pre-fetched data)")
    else:
        logger.info(f"Loaded {len(tools)} tools for asset_class: {asset_class} (LIVE MODE)")

    return tools


def get_minimal_risk_tools(
    asset_class: str,
    prefetched_data: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """
    Get minimal tool set for risk assessment only (Phase 2 optimization).

    This reduces tool initialization overhead and focuses on essential tools
    needed for risk calculation.

    Args:
        asset_class: One of "stock", "etf", "crypto"
        prefetched_data: Optional pre-fetched data for batch mode

    Returns:
        Minimal list of tools for risk assessment

    """
    from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool
    from finwiz.tools.enhanced_etf_tool import EnhancedETFAnalysisTool
    from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool
    from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
    from finwiz.tools.ticker_validation_tool import TickerExistenceValidationTool

    tools: list[BaseTool] = []

    # Always include quantitative analysis (core risk metrics)
    tools.append(QuantitativeAnalysisTool(asset_class=asset_class, prefetched_data=prefetched_data))

    # Always include ticker validation
    tools.append(TickerExistenceValidationTool())

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
