"""
Search tool factory with Perplexity prioritization.

This module provides a factory for creating search tools with Perplexity as the
primary search provider and SerperDevTool as fallback.
"""

from typing import Any

from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.utils.feature_flags import get_feature_flags

logger = get_logger(__name__)


class SearchToolFactory:
    """Factory for creating prioritized search tools."""

    def __init__(self) -> None:
        """Initialize the search tool factory."""
        self.feature_flags = get_feature_flags()
        self._perplexity_integration = None
        self._serper_tools = {}

    def get_primary_search_tool(self, search_type: str = "search", n_results: int = 10) -> Any:
        """
        Get the primary search tool with Perplexity prioritization.

        Args:
            search_type: Type of search ("search", "news")
            n_results: Number of results to return

        Returns:
            Search tool instance (Perplexity wrapper or SerperDevTool)

        """
        if self.feature_flags.is_enabled("perplexity_research"):
            if self._perplexity_integration is None:
                try:
                    self._perplexity_integration = PerplexityAnalysisIntegration()
                except Exception as e:
                    logger.warning(f"Failed to initialize Perplexity search: {e}")
                    self._perplexity_integration = None

            if self._perplexity_integration and self._perplexity_integration.is_available:
                logger.info("Using Perplexity as primary search tool")
                return PerplexitySearchWrapper(self._perplexity_integration, search_type=search_type, max_results=n_results)
            elif self._perplexity_integration:
                # Always return Perplexity wrapper when feature is enabled, even if API key is missing
                # This ensures consistent behavior and proper fallback handling
                logger.info("Using Perplexity wrapper (API key validation at runtime)")
                return PerplexitySearchWrapper(self._perplexity_integration, search_type=search_type, max_results=n_results)

        # Fallback to SerperDevTool
        cache_key = f"{search_type}_{n_results}"
        if cache_key not in self._serper_tools:
            fallback_or_primary = "fallback" if self.feature_flags.is_enabled("perplexity_research") else "primary"
            logger.info(f"Using SerperDevTool as {fallback_or_primary} search tool")
            self._serper_tools[cache_key] = SerperDevTool(n_results=n_results, search_type=search_type)

        return self._serper_tools[cache_key]

    def get_news_search_tool(self, n_results: int = 10) -> Any:
        """Get news-specific search tool."""
        return self.get_primary_search_tool("news", n_results)

    def get_web_search_tool(self, n_results: int = 10) -> Any:
        """Get general web search tool."""
        return self.get_primary_search_tool("search", n_results)


class PerplexitySearchInput(BaseModel):
    """Input schema for PerplexitySearchWrapper."""

    query: str = Field(..., description="Search query for financial research")


class PerplexitySearchWrapper(BaseTool):
    """
    Wrapper to make Perplexity integration compatible with CrewAI tool interface.

    This wrapper adapts the PerplexityAnalysisIntegration to work as a drop-in
    replacement for SerperDevTool in CrewAI crews.
    """

    name: str = "perplexity_search_tool"
    description: str = "Perplexity-powered search tool for enhanced financial research"
    args_schema: type[BaseModel] = PerplexitySearchInput

    def __init__(self, integration: PerplexityAnalysisIntegration, search_type: str = "search", max_results: int = 10) -> None:
        """Initialize the wrapper."""
        super().__init__()

        # Store configuration as private attributes after calling super().__init__()
        self._integration = integration
        self._search_type = search_type
        self._max_results = max_results

    def _run(self, query: str) -> str:
        """Run the search query through Perplexity."""
        import asyncio

        async def _async_run() -> str:
            try:
                if self._search_type == "news":
                    result = await self._integration.search_financial_news(
                        query=query,
                        ticker="AAPL",  # Use a valid ticker for validation
                        asset_type="stock",
                        analysis_type="news",
                        max_results=self._max_results,
                    )
                else:
                    result = await self._integration.search_financial_news(
                        query=query,
                        ticker="AAPL",  # Use a valid ticker for validation
                        asset_type="stock",
                        analysis_type="general",
                        max_results=self._max_results,
                    )

                if result.success and result.results:
                    # Format results similar to SerperDevTool output
                    formatted_results = []
                    for article in result.results:
                        formatted_results.append(
                            {
                                "title": article.title,
                                "link": article.url,
                                "snippet": article.content[:200] + "..." if len(article.content) > 200 else article.content,
                                "source": article.source,
                                "date": article.published_date,
                            }
                        )

                    return str(formatted_results)
                else:
                    logger.warning(f"Perplexity search failed: {result.error_message}")
                    return "[]"

            except Exception as e:
                logger.error(f"Perplexity search error: {e}")
                return "[]"

        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_async_run())
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_async_run())
            finally:
                loop.close()


# Global factory instance
_search_factory = None


def get_search_factory() -> SearchToolFactory:
    """Get the global search tool factory instance."""
    global _search_factory
    if _search_factory is None:
        _search_factory = SearchToolFactory()
    return _search_factory


def get_primary_search_tool(search_type: str = "search", n_results: int = 10) -> Any:
    """Get the primary search tool (Perplexity-first)."""
    return get_search_factory().get_primary_search_tool(search_type, n_results)


def get_news_search_tool(n_results: int = 10) -> Any:
    """Get news search tool (Perplexity-first)."""
    return get_search_factory().get_news_search_tool(n_results)


def get_web_search_tool(n_results: int = 10) -> Any:
    """Get web search tool (Perplexity-first)."""
    return get_search_factory().get_web_search_tool(n_results)
