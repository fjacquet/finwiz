"""
Perplexity Analysis Integration Wrapper.

Provides a wrapper class that uses the existing PerplexitySearchTool to perform
different types of financial analysis (sentiment, technical, fundamental) with
structured data parsing and error handling.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from finwiz.schemas.perplexity import (
    PerplexityConfig,
    SonarArticle,
    SonarSearchResult,
)
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import (
    PerplexityAPIError,
    PerplexityConnectionError,
    PerplexityFallbackManager,
    PerplexityRateLimitError,
    PerplexityTimeoutError,
)
from finwiz.tools.perplexity_logging import (
    PerplexityOperationLogger,
)
from finwiz.tools.perplexity_performance import PerplexityPerformanceMonitor
from finwiz.tools.perplexity_search_tool import PerplexitySearchTool

logger = get_logger(__name__)


class PerplexityAnalysisIntegration:
    """
    Integration wrapper for Perplexity tool with multiple analysis types.

    This class provides structured search methods for different financial analysis
    contexts (sentiment, technical, fundamental) and parses raw Perplexity responses
    into structured SonarArticle objects.
    """

    def __init__(self, config: PerplexityConfig | None = None) -> None:
        """Initialize the integration wrapper."""
        self.perplexity_tool = PerplexitySearchTool()
        self.config = config or self._create_default_config()

        # Validate API key availability
        api_key = os.getenv("PPLX_API_KEY")
        if not api_key:
            logger.warning("PPLX_API_KEY not found, Perplexity integration will be disabled")
            self._api_available = False
        else:
            self._api_available = True

    def _create_default_config(self) -> PerplexityConfig:
        """Create default configuration."""
        api_key = os.getenv("PPLX_API_KEY", "")
        return PerplexityConfig(api_key=api_key, timeout_seconds=30.0, max_retries=3, backoff_factor=2.0, rate_limit_buffer=5, default_max_results=10)

    @property
    def is_available(self) -> bool:
        """Check if Perplexity integration is available."""
        return self._api_available

    async def search_financial_news(self, query: str, ticker: str, asset_type: str, analysis_type: str = "general", max_results: int = 10) -> SonarSearchResult:
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
            # Create enhanced query based on analysis type
            enhanced_query = self._create_enhanced_query(query, ticker, asset_type, analysis_type)

            # Log search request with redacted content
            PerplexityOperationLogger.log_search_request(ticker, analysis_type, len(enhanced_query))

            # Get search filters for the analysis type
            search_filters = self._get_search_filters(analysis_type)

            # Execute search with retry logic
            raw_response, retry_count = await self._execute_search_with_retry(enhanced_query, max_results, search_filters)

            # Parse response into structured articles
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

    def _create_enhanced_query(self, base_query: str, ticker: str, asset_type: str, analysis_type: str) -> str:
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

    def _get_search_filters(self, analysis_type: str) -> dict[str, str]:
        """Get search filters based on analysis type."""
        if analysis_type == "fundamental":
            return self.config.sec_filing_filters.copy()
        else:
            return self.config.financial_news_filters.copy()

    async def _execute_search_with_retry(self, query: str, max_results: int, search_filters: dict[str, str]) -> tuple[str, int]:
        """Execute Perplexity search with comprehensive retry and fallback logic."""
        ticker = self._extract_ticker_from_query(query)
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                # Prepare search parameters
                search_params = {
                    "query": query,
                    "model": "sonar-small-chat",
                    "top_k": min(max_results, 10),  # Perplexity API limit
                }

                # Add filters if available
                if "site" in search_filters:
                    search_params["search_domain_filter"] = search_filters["site"].split(",")

                if "date" in search_filters:
                    search_params["search_recency"] = search_filters["date"]

                # Execute search using Perplexity Search API (not chat completions)
                import json

                import requests

                api_key = os.getenv("PPLX_API_KEY")
                if not api_key:
                    raise PerplexityAPIError(401, "PPLX_API_KEY not set")

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

                # Use the /search endpoint for structured results
                payload = {
                    "query": search_params["query"],
                    "max_results": min(search_params.get("top_k", 10), 20),  # API max is 20
                    "max_tokens_per_page": 1024,
                }

                # Add country filter if available
                if "country" in search_filters:
                    payload["country"] = search_filters["country"]

                http_response = requests.post("https://api.perplexity.ai/search", headers=headers, data=json.dumps(payload), timeout=30)
                http_response.raise_for_status()

                # Convert search results to the format expected by the parser
                search_data = http_response.json()

                # Transform search results into citation format for compatibility
                citations = []
                for result in search_data.get("results", []):
                    citations.append(
                        {
                            "title": result.get("title", ""),
                            "url": result.get("url", ""),
                            "snippet": result.get("snippet", ""),
                            "date": result.get("date", ""),
                            "last_updated": result.get("last_updated", ""),
                        }
                    )

                # Create response in expected format
                response_data = {"citations": citations, "results": search_data.get("results", [])}
                response = json.dumps(response_data, indent=2, ensure_ascii=False)

                if response.startswith("Error:"):
                    # Convert tool error to proper exception
                    error_msg = response[6:].strip()  # Remove "Error:" prefix

                    # Classify the error type
                    if "api key" in error_msg.lower():
                        raise PerplexityAPIError(401, error_msg)
                    elif "rate limit" in error_msg.lower() or "429" in error_msg:
                        retry_after = self._extract_retry_after_from_message(error_msg)
                        raise PerplexityRateLimitError(retry_after, error_msg)
                    elif "timeout" in error_msg.lower():
                        raise PerplexityTimeoutError(error_msg)
                    elif "connection" in error_msg.lower():
                        raise PerplexityConnectionError(error_msg)
                    else:
                        raise PerplexityAPIError(None, error_msg)

                return response, attempt

            except Exception as e:
                last_exception = e

                # Extract rate limit information
                rate_limit_info = PerplexityFallbackManager.extract_rate_limit_info(e)

                # Log rate limit warnings
                if rate_limit_info["is_rate_limit"] and ticker:
                    retry_after = rate_limit_info.get("retry_after")
                    PerplexityOperationLogger.log_rate_limit_warning(ticker, retry_after)

                # Check if we should retry
                if not PerplexityFallbackManager.should_retry_error(e, attempt, self.config.max_retries):
                    if ticker:
                        PerplexityOperationLogger.log_api_failure(ticker, str(e), attempt + 1)
                    break

                # Calculate backoff delay
                if rate_limit_info["is_rate_limit"] and "retry_after" in rate_limit_info:
                    # Use server-provided retry-after value
                    wait_time = rate_limit_info["retry_after"] + self.config.rate_limit_buffer
                else:
                    # Use exponential backoff
                    wait_time = PerplexityFallbackManager.calculate_backoff_delay(attempt, self.config.backoff_factor, 60.0)

                logger.warning(f"Perplexity search attempt {attempt + 1} failed, retrying in {wait_time:.2f}s: {str(e)}")
                await asyncio.sleep(wait_time)

        # All retries exhausted, raise the last exception
        if ticker:
            PerplexityOperationLogger.log_api_failure(ticker, str(last_exception), self.config.max_retries + 1)

        raise last_exception or Exception("Max retries exceeded for Perplexity search")

    def _extract_retry_after_from_message(self, message: str) -> int | None:
        """Extract retry-after value from error message."""
        import re

        retry_match = re.search(r"retry[_\s]*after[:\s]*(\d+)", message, re.IGNORECASE)
        if retry_match:
            try:
                return int(retry_match.group(1))
            except ValueError:
                pass

        return None

    def _extract_ticker_from_query(self, query: str) -> str | None:
        """Extract ticker symbol from query for logging context."""
        import re

        # Look for ticker-like patterns (1-5 uppercase letters, possibly with numbers/dashes)
        ticker_match = re.search(r"\b([A-Z]{1,5}(?:-[A-Z]{1,3})?)\b", query)
        if ticker_match:
            return ticker_match.group(1)

        return None

    def _extract_retry_after(self, error: Exception) -> int | None:
        """Extract retry-after value from rate limit error."""
        error_str = str(error)

        import re

        retry_match = re.search(r"retry[_\s]*after[:\s]*(\d+)", error_str, re.IGNORECASE)
        if retry_match:
            try:
                return int(retry_match.group(1))
            except ValueError:
                pass

        return None

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

    def _parse_perplexity_response(self, raw_response: str, analysis_type: str, ticker: str | None = None) -> list[SonarArticle]:
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
            # Parse JSON response
            response_data = json.loads(raw_response)

            # Extract citations from response
            citations = response_data.get("citations", [])
            if not citations:
                # Try to extract from choices if citations not at root level
                choices = response_data.get("choices", [])
                if choices and "citations" in choices[0]:
                    citations = choices[0]["citations"]

            # Convert citations to SonarArticle objects
            for i, citation in enumerate(citations):
                try:
                    article = self._create_sonar_article(citation, analysis_type, i)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse citation {i}: {str(e)}")
                    continue

            # If no citations found, try to extract from message content
            if not articles:
                articles = self._extract_articles_from_content(response_data, analysis_type)

            # Log parsing metrics with content redaction
            if ticker:
                PerplexityOperationLogger.log_parsing_metrics(ticker, raw_response_size, len(articles))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Perplexity JSON response: {str(e)}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"JSON parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing Perplexity response: {str(e)}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"Response parsing error: {str(e)}")

        return articles

    def _create_sonar_article(self, citation: dict[str, Any], analysis_type: str, index: int) -> SonarArticle | None:
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
            logger.warning(f"Failed to create SonarArticle from citation: {str(e)}")
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

            except Exception:
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
                except Exception:
                    continue

        return None

    def _determine_content_type(self, url: str, title: str) -> str:
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

    def _extract_articles_from_content(self, response_data: dict[str, Any], analysis_type: str) -> list[SonarArticle]:
        """Extract articles from response content when citations are not available."""
        articles = []

        try:
            # Try to extract from choices content
            choices = response_data.get("choices", [])
            if not choices:
                return articles

            content = choices[0].get("message", {}).get("content", "")

            # Look for URL patterns in content
            import re

            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, content)

            # Create basic articles from found URLs
            for i, url in enumerate(urls[:10]):  # Limit to 10 URLs
                try:
                    # Extract domain for title/publisher
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc

                    article = SonarArticle(
                        title=f"Article from {domain}",
                        url=url,
                        summary="",
                        publisher=self._extract_publisher({}, url),
                        published_date=None,
                        relevance_score=max(0.1, 1.0 - (i * 0.1)),
                        content_type="news",
                        analysis_type=analysis_type,
                    )
                    articles.append(article)

                except Exception as e:
                    logger.warning(f"Failed to create article from URL {url}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Failed to extract articles from content: {str(e)}")

        return articles

    # Convenience methods for specific analysis types

    async def search_sentiment_news(self, ticker: str, asset_type: str, max_results: int = 10) -> SonarSearchResult:
        """Search for sentiment-focused financial news."""
        query = f"{ticker} market sentiment investor reaction news"
        return await self.search_financial_news(query, ticker, asset_type, "sentiment", max_results)

    async def search_technical_analysis(self, ticker: str, asset_type: str, max_results: int = 10) -> SonarSearchResult:
        """Search for technical analysis and price targets."""
        query = f"{ticker} technical analysis price target analyst rating"
        return await self.search_financial_news(query, ticker, asset_type, "technical", max_results)

    async def search_fundamental_analysis(self, ticker: str, asset_type: str, max_results: int = 10) -> SonarSearchResult:
        """Search for fundamental analysis and earnings data."""
        query = f"{ticker} earnings financial results SEC filing fundamental"
        return await self.search_financial_news(query, ticker, asset_type, "fundamental", max_results)
