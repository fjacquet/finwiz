"""
Search tool factory with Perplexity prioritization.

This module provides a factory for creating search tools with Perplexity as the
primary search provider and SerperDevTool as fallback.
"""

from typing import Any

from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.utils.feature_flags import get_feature_flags

# Ensure environment variables are loaded
load_dotenv()

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

    def _run(self, query: str = None, search_query: str = None) -> str:
        """Run the search query through Perplexity."""
        # Handle both parameter names for compatibility
        search_term = query or search_query
        if not search_term:
            logger.error("No search query provided")
            return "[]"

        try:
            # Check if Perplexity integration is available
            if not self._integration.is_available:
                logger.warning("Perplexity API key not available, returning empty results")
                return "[]"

            # Use the synchronous PerplexitySearchTool directly to avoid async issues
            from finwiz.tools.perplexity_search_tool import PerplexitySearchTool

            perplexity_tool = PerplexitySearchTool()

            # Create enhanced query for financial context
            enhanced_query = f"{search_term} financial analysis market data"

            # Call the synchronous tool directly
            raw_result = perplexity_tool._run(
                query=enhanced_query,
                model="sonar-pro",
                top_k=min(self._max_results, 10),
                search_recency="week" if self._search_type == "news" else None,
            )

            # Check if result is an error
            if raw_result.startswith("Error:"):
                logger.warning(f"Perplexity search failed: {raw_result}")
                return "[]"

            # Parse the JSON response and format for SerperDevTool compatibility
            import json

            try:
                response_data = json.loads(raw_result)
                formatted_results = []

                # Extract search results from response (these contain structured data)
                search_results = response_data.get("search_results", [])

                # Convert search results to SerperDevTool format
                for i, result in enumerate(search_results[: self._max_results]):
                    try:
                        title = result.get("title", f"Article {i + 1}")
                        url = result.get("url", "")
                        snippet = result.get("snippet", "")[:200]
                        source = result.get("source", "")
                        date = result.get("date", result.get("last_updated"))

                        # Extract publisher from source or URL if not provided
                        if not source and url:
                            from urllib.parse import urlparse

                            domain = urlparse(url).netloc
                            if domain.startswith("www."):
                                domain = domain[4:]
                            source = domain.replace(".com", "").title()

                        formatted_results.append(
                            {"title": title, "link": url, "snippet": snippet, "source": source or "Unknown", "date": date}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to parse search result {i}: {e}")
                        continue

                if formatted_results:
                    logger.info(f"Perplexity search returned {len(formatted_results)} results")
                    return str(formatted_results)
                else:
                    logger.warning("No valid search results found in Perplexity response")
                    return "[]"

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Perplexity JSON response: {e}")
                return "[]"

        except Exception as e:
            logger.error(f"Perplexity search error: {e}")
            return "[]"


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
