"""
Financial news search for sentiment, technical and fundamental analysis.

Historically a wrapper over ``PerplexitySearchTool``; the class and module
names are kept because four tool modules import them. The search itself now
goes through ``research_with_retry`` (OpenRouter web plugin with a small
``NewsDigest`` schema, Perplexity as fallback) and the reply is fed through
the same citation parser as before, so ``SonarArticle`` / ``SonarSearchResult``
and their consumers are untouched.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from crewai_custom_tools.core.results import ToolResultError, ok, parse_tool_result

from finwiz.infrastructure.research.openrouter_structured import ResearchResult
from finwiz.infrastructure.resilience.research_retry import has_openrouter_key, has_perplexity_key, research_with_retry
from finwiz.schemas.perplexity import (
    NewsDigest,
    PerplexityConfig,
    SonarArticle,
    SonarSearchResult,
)
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import (
    PerplexityAPIError,
    PerplexityFallbackManager,
)
from finwiz.tools.perplexity_logging import (
    PerplexityOperationLogger,
)
from finwiz.tools.perplexity_performance import PerplexityPerformanceMonitor

logger = get_logger(__name__)

# Type aliases for Literal types
AssetType = Literal["stock", "etf", "crypto"]
AnalysisType = Literal["sentiment", "technical", "fundamental", "general"]
ContentType = Literal["news", "filing", "analysis", "earnings", "regulatory"]

_NEWS_SYSTEM = (
    "Tu es un assistant de veille financière. Tu réponds UNIQUEMENT en JSON conforme au schéma fourni. "
    "Chaque titre doit provenir d'une page web réelle que tu as consultée, avec son URL exacte. "
    "Aucun titre inventé ; si tu ne trouves rien de fiable, renvoie une liste vide."
)


class PerplexityAnalysisIntegration:
    """
    Integration wrapper for Perplexity tool with multiple analysis types.

    This class provides structured search methods for different financial analysis
    contexts (sentiment, technical, fundamental) and parses raw Perplexity responses
    into structured SonarArticle objects.
    """

    def __init__(self, config: PerplexityConfig | None = None) -> None:
        """Initialize the integration wrapper."""
        self.config = config or self._create_default_config()

        # Available when either research provider has a key configured -- the
        # same key-presence rule research_with_retry itself uses to decide
        # whether to call OpenRouter first or go straight to the Perplexity
        # fallback. No tool construction needed just to probe for a key.
        self._api_available = has_openrouter_key() or has_perplexity_key()
        if not self._api_available:
            logger.warning("Neither OPENROUTER_API_KEY nor PERPLEXITY_API_KEY/PPLX_API_KEY found; news research will be disabled")

    def _create_default_config(self) -> PerplexityConfig:
        """Create default configuration."""
        api_key = os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY") or ""
        return PerplexityConfig(api_key=api_key, timeout_seconds=30.0, max_retries=3, backoff_factor=2.0, rate_limit_buffer=5, default_max_results=10)

    @property
    def is_available(self) -> bool:
        """Check if Perplexity integration is available."""
        return self._api_available

    async def search_financial_news(self, query: str, ticker: str, asset_type: AssetType, analysis_type: AnalysisType = "general", max_results: int = 10) -> SonarSearchResult:
        """
        Search for financial news using Perplexity Sonar.

        Args:
            query: Search query string
            ticker: Asset ticker symbol
            asset_type: Type of asset (stock, etf, crypto)
            analysis_type: Type of analysis (sentiment, technical, fundamental, general)
            max_results: Maximum number of results to return

        Returns:
            SonarSearchResult with parsed articles

        """
        if not self.is_available:
            PerplexityOperationLogger.log_api_failure(ticker, "Perplexity API key not available")
            return SonarSearchResult(
                query=query,
                ticker=ticker,
                asset_type=asset_type,
                analysis_type=analysis_type,
                success=False,
                error_message="Perplexity API key not available",
            )

        # Start performance monitoring
        start_time = PerplexityPerformanceMonitor.start_operation_timer()

        try:
            enhanced_query = self._create_enhanced_query(query, ticker, asset_type, analysis_type)
            PerplexityOperationLogger.log_search_request(ticker, analysis_type, len(enhanced_query))
            search_filters = self._get_search_filters(analysis_type)

            research = await research_with_retry(
                prompt=self._news_prompt(enhanced_query, max_results, search_filters),
                schema=NewsDigest,
                system=_NEWS_SYSTEM,
                search_recency_filter="week",
                timeout=self.config.timeout_seconds,
                max_attempts=self.config.max_retries + 1,
                kind="news",
                cache_key=f"{ticker}|{asset_type}|{analysis_type}|{max_results}|{query}",
            )
            if research is None:
                raise PerplexityAPIError(None, "web research returned no result")

            citations = self._citations_from_research(research, max_results)
            if not citations:
                raise PerplexityAPIError(None, "web research returned no headlines")

            # Same envelope the parser always consumed, so _create_sonar_article
            # and everything downstream stay untouched.
            raw_response = ok({"citations": citations, "results": []})
            retry_count = 0
            articles = self._parse_perplexity_response(raw_response, analysis_type, ticker)

            # Calculate performance metrics
            search_time_ms = PerplexityPerformanceMonitor.calculate_operation_time(start_time)

            # Log performance metrics with baseline comparison
            PerplexityPerformanceMonitor.log_performance_metrics(ticker, analysis_type, search_time_ms, len(articles))

            # Log successful search with metrics
            PerplexityOperationLogger.log_search_success(ticker, analysis_type, search_time_ms, len(articles))

            return SonarSearchResult(
                query=query,
                ticker=ticker,
                asset_type=asset_type,
                analysis_type=analysis_type,
                results=articles,
                total_results=len(articles),
                search_time_ms=search_time_ms,
                success=True,
                retry_count=retry_count,
            )

        except Exception as e:
            # Calculate performance metrics even for failures
            search_time_ms = PerplexityPerformanceMonitor.calculate_operation_time(start_time)

            # Determine error type for structured logging
            error_type = self._classify_error(e)
            http_status = self._extract_http_status(e)

            # Log failure with structured data
            PerplexityOperationLogger.log_search_failure(ticker, analysis_type, search_time_ms, error_type, http_status)

            # Create fallback result with graceful degradation
            return PerplexityFallbackManager.create_fallback_result(query, ticker, asset_type, analysis_type, str(e))

    def _create_enhanced_query(self, base_query: str, ticker: str, asset_type: AssetType, analysis_type: AnalysisType) -> str:
        """Create enhanced search query based on analysis type."""
        # Base query with ticker
        enhanced_query = f"{ticker} {base_query}"

        # Add analysis-specific terms
        if analysis_type == "sentiment":
            enhanced_query += " news sentiment market reaction investor opinion"
        elif analysis_type == "technical":
            enhanced_query += " technical analysis price target analyst rating chart pattern"
        elif analysis_type == "fundamental":
            enhanced_query += " earnings financial results SEC filing fundamental analysis"

        # Add asset-specific terms
        if asset_type == "stock":
            enhanced_query += " stock equity shares"
        elif asset_type == "etf":
            enhanced_query += " ETF fund holdings expense ratio"
        elif asset_type == "crypto":
            enhanced_query += " cryptocurrency crypto digital asset"

        return enhanced_query

    def _get_search_filters(self, analysis_type: AnalysisType) -> dict[str, str]:
        """Get search filters based on analysis type."""
        if analysis_type == "fundamental":
            return self.config.sec_filing_filters.copy()
        else:
            return self.config.financial_news_filters.copy()

    def _news_prompt(self, enhanced_query: str, max_results: int, search_filters: dict[str, str]) -> str:
        preferred = search_filters.get("site", "").replace(",", ", ")
        wanted = max(1, min(max_results, 10))
        lines = [
            f"Recherche les actualités récentes pour : {enhanced_query}.",
            f"Retourne au plus {wanted} titres, chacun avec son URL source exacte et un résumé d'une phrase.",
        ]
        if preferred:
            lines.append(f"Privilégie ces sources : {preferred}.")
        return "\n".join(lines)

    @staticmethod
    def _citations_from_research(research: ResearchResult[NewsDigest], max_results: int) -> list[dict[str, Any]]:
        """Digest headlines first, then annotation citations not already named; URL-deduplicated."""
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for headline in research.data.headlines:
            url = headline.url.strip()
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({"title": headline.title, "url": url, "snippet": headline.one_line_summary})
        for cite in research.citations:
            if not cite.url or cite.url in seen:
                continue
            seen.add(cite.url)
            out.append({"title": cite.title or cite.url, "url": cite.url, "snippet": cite.content})
        return out[: max(1, max_results)]

    def _classify_error(self, error: Exception) -> str:
        """Classify error type for structured logging."""
        error_str = str(error).lower()

        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "connection" in error_str or "network" in error_str:
            return "connection_error"
        elif "authentication" in error_str or "401" in error_str:
            return "authentication_error"
        elif "api key" in error_str:
            return "api_key_error"
        elif "json" in error_str or "parse" in error_str:
            return "parsing_error"
        else:
            return "unknown_error"

    def _extract_http_status(self, error: Exception) -> int | None:
        """Extract HTTP status code from error if available."""
        error_str = str(error)

        # Look for common HTTP status patterns
        import re

        status_match = re.search(r"\b(4\d{2}|5\d{2})\b", error_str)
        if status_match:
            try:
                return int(status_match.group(1))
            except ValueError:
                pass

        return None

    def _parse_perplexity_response(self, raw_response: str, analysis_type: AnalysisType, ticker: str | None = None) -> list[SonarArticle]:
        """
        Parse raw Perplexity response into structured SonarArticle objects.

        Args:
            raw_response: Raw JSON response from Perplexity API
            analysis_type: Type of analysis for context
            ticker: Asset ticker for logging context

        Returns:
            List of parsed SonarArticle objects

        """
        articles = []
        raw_response_size = len(raw_response.encode("utf-8"))

        try:
            data = parse_tool_result(raw_response)

            # Citations come straight from the envelope now.
            citations = (data or {}).get("citations", [])

            for i, citation in enumerate(citations):
                try:
                    article = self._create_sonar_article(citation, analysis_type, i)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse citation {i}: {e!s}")
                    continue

            if ticker:
                PerplexityOperationLogger.log_parsing_metrics(ticker, raw_response_size, len(articles))

        except ToolResultError as e:
            logger.error(f"Perplexity tool returned an error envelope: {e!s}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"Tool error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error parsing Perplexity response: {e!s}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"Response parsing error: {e!s}")

        return articles

    def _create_sonar_article(self, citation: dict[str, Any], analysis_type: AnalysisType, index: int) -> SonarArticle | None:
        """Create SonarArticle from citation data."""
        try:
            # Extract basic fields
            title = citation.get("title", f"Article {index + 1}")
            url = citation.get("url", "")

            # Skip if no URL (invalid citation)
            if not url:
                return None

            # Extract other fields with defaults
            summary = citation.get("snippet", citation.get("text", ""))

            # Try to extract publisher from URL or citation
            publisher = self._extract_publisher(citation, url)

            # Try to extract date
            published_date = self._extract_published_date(citation)

            # Calculate relevance score based on position
            relevance_score = max(0.1, 1.0 - (index * 0.1))

            # Determine content type based on URL and title
            content_type = self._determine_content_type(url, title)

            return SonarArticle(
                title=title,
                url=url,
                summary=summary[:2000],  # Truncate to max length
                publisher=publisher,
                published_date=published_date,
                relevance_score=relevance_score,
                content_type=content_type,
                analysis_type=analysis_type,
            )

        except Exception as e:
            logger.warning(f"Failed to create SonarArticle from citation: {e!s}")
            return None

    def _extract_publisher(self, citation: dict[str, Any], url: str) -> str:
        """Extract publisher name from citation or URL."""
        # Try to get publisher from citation
        publisher = citation.get("publisher", citation.get("source", ""))

        if not publisher and url:
            # Extract from URL domain
            try:
                from urllib.parse import urlparse

                domain = urlparse(url).netloc

                # Clean up domain to get publisher name
                if domain.startswith("www."):
                    domain = domain[4:]

                # Map common domains to publisher names
                domain_mapping = {
                    "bloomberg.com": "Bloomberg",
                    "reuters.com": "Reuters",
                    "wsj.com": "Wall Street Journal",
                    "ft.com": "Financial Times",
                    "cnbc.com": "CNBC",
                    "marketwatch.com": "MarketWatch",
                    "yahoo.com": "Yahoo Finance",
                    "sec.gov": "SEC",
                }

                publisher = domain_mapping.get(domain, domain.replace(".com", "").title())

            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to extract publisher from URL: {e}")
                publisher = "Unknown"

        return publisher or "Unknown"

    def _extract_published_date(self, citation: dict[str, Any]) -> str | None:
        """Extract published date from citation."""
        # Try various date fields
        date_fields = ["published_date", "date", "publish_date", "timestamp"]

        for field in date_fields:
            date_value = citation.get(field)
            if date_value:
                try:
                    # Try to parse and format as ISO string
                    if isinstance(date_value, (int, float)):
                        # Assume timestamp
                        from datetime import datetime

                        dt = datetime.fromtimestamp(date_value)
                        return dt.isoformat()
                    elif isinstance(date_value, str):
                        # Return as-is if string
                        return date_value
                except (ValueError, TypeError, OverflowError) as e:
                    logger.warning(f"Failed to parse published date from field '{field}': {e}")
                    continue

        return None

    def _determine_content_type(self, url: str, title: str) -> ContentType:
        """Determine content type based on URL and title."""
        url_lower = url.lower()
        title_lower = title.lower()

        if "sec.gov" in url_lower or "filing" in title_lower:
            return "filing"
        elif "earnings" in title_lower or "quarterly" in title_lower:
            return "earnings"
        elif "regulation" in title_lower or "regulatory" in title_lower:
            return "regulatory"
        elif any(term in title_lower for term in ["analysis", "outlook", "forecast"]):
            return "analysis"
        else:
            return "news"

    # Convenience methods for specific analysis types

    async def search_sentiment_news(self, ticker: str, asset_type: AssetType, max_results: int = 10) -> SonarSearchResult:
        """Search for sentiment-focused financial news."""
        query = f"{ticker} market sentiment investor reaction news"
        return await self.search_financial_news(query, ticker, asset_type, "sentiment", max_results)

    async def search_technical_analysis(self, ticker: str, asset_type: AssetType, max_results: int = 10) -> SonarSearchResult:
        """Search for technical analysis and price targets."""
        query = f"{ticker} technical analysis price target analyst rating"
        return await self.search_financial_news(query, ticker, asset_type, "technical", max_results)

    async def search_fundamental_analysis(self, ticker: str, asset_type: AssetType, max_results: int = 10) -> SonarSearchResult:
        """Search for fundamental analysis and earnings data."""
        query = f"{ticker} earnings financial results SEC filing fundamental"
        return await self.search_financial_news(query, ticker, asset_type, "fundamental", max_results)
