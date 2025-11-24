"""
Historical Analysis integration utilities for CrewAI crews.

Provides helper functions to integrate HISTORICAL ANALYSIS context from Supabase
into crew task descriptions. This is separate from the existing document RAG tools.

Purpose: Enable agents to learn from past analyses of similar assets by including
historical context (grades, recommendations, scores) in their task descriptions.

IMPORTANT DISTINCTION:
- Document RAG Tools: Agent tools for retrieving documents from vector databases
- Historical Analysis Service: Python service for retrieving past analysis results

This module provides the Historical Analysis Service (not document RAG).
"""

import logging
import os
from typing import Any

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.repositories.vector_repository import VectorRepository
from finwiz.supabase.services.embedding_service import EmbeddingService
from finwiz.supabase.services.rag_service import HistoricalAnalysisService

logger = logging.getLogger(__name__)


def is_historical_analysis_enabled() -> bool:
    """
    Check if historical analysis service is enabled via environment variable.

    Returns:
        True if enabled, False otherwise

    """
    enabled = os.getenv("SUPABASE_ENABLED", "false").lower() == "true"
    return enabled


def get_historical_analysis_service() -> HistoricalAnalysisService | None:
    """
    Get Historical Analysis Service instance if enabled.

    Returns:
        HistoricalAnalysisService instance if enabled and available, None otherwise

    """
    if not is_historical_analysis_enabled():
        logger.debug("Historical analysis service disabled (SUPABASE_ENABLED=false)")
        return None

    try:
        # Initialize Supabase client
        client = SupabaseClient()

        # Check if client is available
        if not client.get_client():
            logger.warning("Supabase client unavailable, historical analysis service disabled")
            return None

        # Initialize repositories
        embedding_service = EmbeddingService()
        vector_repo = VectorRepository(client, embedding_service)
        analysis_repo = AnalysisRepository(client)

        # Create Historical Analysis Service
        service = HistoricalAnalysisService(vector_repo, analysis_repo)

        logger.info("Historical Analysis Service initialized successfully")
        return service

    except Exception as e:
        logger.error(f"Failed to initialize Historical Analysis Service: {e}")
        return None


async def enhance_task_description_with_historical_context(
    base_description: str,
    ticker: str,
    asset_class: str,
    service: HistoricalAnalysisService | None = None,
    limit: int = 3,
) -> str:
    """
    Enhance task description with historical analysis context.

    Retrieves similar historical analyses and appends formatted context
    to the task description. Falls back gracefully if service is unavailable.

    Args:
        base_description: Original task description
        ticker: Asset ticker symbol
        asset_class: Asset class (stock, etf, crypto)
        service: Optional HistoricalAnalysisService instance (creates new if None)
        limit: Maximum number of similar analyses to include (default: 3)

    Returns:
        Enhanced task description with historical context, or original description
        if service is unavailable

    """
    # Check if service is enabled
    if not is_historical_analysis_enabled():
        logger.debug("Historical analysis disabled, using base task description")
        return base_description

    # Get or create service
    if service is None:
        service = get_historical_analysis_service()

    if service is None:
        logger.debug("Historical analysis service unavailable, using base task description")
        return base_description

    try:
        # Get historical context for ticker
        context = await service.get_context_for_ticker(
            ticker=ticker,
            asset_class=asset_class,
            limit=limit,
        )

        if not context:
            logger.debug(f"No historical context found for {ticker}, using base task description")
            return base_description

        # Format context for agent consumption
        formatted_context = service.format_context_for_agent(
            context=context,
            query=f"{ticker} {asset_class} analysis",
        )

        # Append context to task description
        enhanced_description = f"{base_description}\n\n{formatted_context}"

        logger.info(f"Enhanced task description with {len(context)} historical analyses for {ticker}")
        return enhanced_description

    except Exception as e:
        logger.error(f"Failed to enhance task description with historical context: {e}")
        return base_description


def create_historical_context_enhanced_task_config(
    task_config: dict[str, Any],
    ticker: str,
    asset_class: str,
    service: HistoricalAnalysisService | None = None,
) -> dict[str, Any]:
    """
    Create historical context-enhanced task configuration.

    This is a synchronous wrapper that can be used in crew initialization.
    Note: This function cannot use async/await, so it returns the original
    config. For async enhancement, use enhance_task_description_with_historical_context
    directly in an async context.

    Args:
        task_config: Original task configuration dict
        ticker: Asset ticker symbol
        asset_class: Asset class (stock, etf, crypto)
        service: Optional HistoricalAnalysisService instance

    Returns:
        Task configuration (unchanged in sync context)

    """
    # In synchronous context, we cannot enhance with historical context
    # This function is provided for API compatibility but returns original config
    logger.debug("Historical context enhancement requires async context, returning original task config")
    return task_config


def get_historical_context_for_inputs(
    ticker: str,
    asset_class: str,
    limit: int = 3,
) -> str:
    """
    Get historical analysis context to include in crew inputs.

    This is a PYTHON SERVICE function (not an agent tool) that retrieves
    historical analysis results from Supabase and formats them for inclusion
    in task descriptions.

    Call this in crew kickoff() BEFORE executing the crew to add historical
    context to the inputs dict.

    Args:
        ticker: Asset ticker symbol
        asset_class: Asset class (stock, etf, crypto)
        limit: Maximum number of similar analyses to include (default: 3)

    Returns:
        Formatted historical context string, or empty string if unavailable

    """
    import asyncio

    # Check if service is enabled
    if not is_historical_analysis_enabled():
        logger.debug("Historical analysis service disabled, no historical context available")
        return ""

    # Get service
    service = get_historical_analysis_service()
    if service is None:
        logger.debug("Historical analysis service unavailable, no historical context")
        return ""

    try:
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we can't use it
            logger.warning("Event loop already running, cannot fetch historical context synchronously")
            return ""

        context = loop.run_until_complete(
            service.get_context_for_ticker(
                ticker=ticker,
                asset_class=asset_class,
                limit=limit,
            )
        )

        if not context:
            logger.debug(f"No historical analyses found for {ticker}")
            return ""

        # Format context for agent consumption
        formatted_context = service.format_context_for_agent(
            context=context,
            query=f"{ticker} {asset_class} analysis",
        )

        logger.info(f"Retrieved historical context with {len(context)} past analyses for {ticker}")
        return formatted_context

    except Exception as e:
        logger.error(f"Failed to get historical context from Supabase: {e}")
        return ""


# Example usage in crew kickoff:
"""
INTEGRATION PATTERN - Add to crew kickoff() method:

```python
from finwiz.supabase.utils.rag_integration import get_historical_context_for_inputs

class StockCrew:
    def kickoff(self, inputs: dict[str, Any] | None = None) -> Any:
        if inputs is None:
            inputs = {}

        # PYTHON SERVICE: Get historical analysis context from Supabase
        # This is NOT an agent tool - it's called before crew execution
        ticker = inputs.get("ticker", "")
        asset_class = inputs.get("asset_class", "stock")

        historical_context = get_historical_context_for_inputs(ticker, asset_class)
        if historical_context:
            # Add to inputs so task descriptions can reference it
            inputs["historical_context"] = historical_context
            logger.info(f"Added historical analysis context for {ticker}")
        else:
            # Graceful fallback - empty string if unavailable
            inputs["historical_context"] = ""

        # Execute crew with enhanced inputs
        crew_instance = self.crew()
        result = crew_instance.kickoff(inputs=inputs)
        return result
```

Then in task descriptions (config/tasks.yaml), reference the historical context:

```yaml
analysis_task:
  description: >
    Analyze {ticker} ({asset_class}) with comprehensive research.

    {historical_context}

    Perform the following analysis steps:
    1. Validate ticker using TickerValidationTool
    2. Fetch financial data
    3. Calculate metrics
    4. Generate recommendation
```

The {historical_context} placeholder will be replaced with:
- Historical analysis context if Supabase is enabled and similar analyses exist
- Empty string if Supabase is disabled or no similar analyses found

This provides graceful fallback - crews work with or without Supabase.
"""
