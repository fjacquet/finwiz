"""
Data source integration utilities for sentiment analysis.

This module handles integration with various data sources including
Yahoo Finance, Perplexity Sonar, and other news providers.
"""

import datetime
from typing import Any, Literal, cast

import yfinance as yf  # yfinance has no official type stubs

from finwiz.config.features.flags import get_feature_flags
from finwiz.schemas.perplexity import SonarArticle
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.validation.url import get_url_validator

logger = get_logger(__name__)


class SentimentDataSources:
    """Handles integration with various sentiment data sources."""

    # Forbidden URL patterns that indicate hallucinations
    FORBIDDEN_URL_PATTERNS = [
        "example.com",
        "test.com",
        "sample.com",
        "placeholder.com",
        "dummy.com",
        "fake.com",
        "mock.com",
    ]

    def __init__(self) -> None:
        """Initialize sentiment data sources."""
        self.logger = logger
        self.url_validator = get_url_validator()

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate that URL is real and not a placeholder.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise

        """
        # Use centralized URL validator
        return self.url_validator.is_valid_url(url, "sentiment article")

    def _filter_valid_articles(self, articles: list[dict]) -> list[dict]:
        """
        Filter out articles with invalid URLs.

        Args:
            articles: List of article dictionaries

        Returns:
            Filtered list with only valid articles

        """
        valid_articles = []
        rejected_count = 0

        for article in articles:
            url = article.get("link", "")
            if self._is_valid_url(url):
                valid_articles.append(article)
            else:
                rejected_count += 1
                self.logger.debug(f"Rejected article with invalid URL: {article.get('title', 'Unknown')}")

        if rejected_count > 0:
            self.logger.info(f"Filtered out {rejected_count} articles with invalid URLs")

        return valid_articles

    def get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
        """Get Perplexity integration instance if enabled."""
        feature_flags = get_feature_flags()

        # Check feature flag status and log for debugging
        is_enabled = feature_flags.is_enabled("perplexity_research")
        fallback_strategy = feature_flags.get_fallback_strategy("perplexity_research").value

        from finwiz.tools.perplexity_analysis_integration import PerplexityOperationLogger

        PerplexityOperationLogger.log_feature_flag_status("sentiment_analysis", is_enabled, fallback_strategy)

        if not is_enabled:
            return None

        try:
            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                self.logger.debug("Perplexity Sonar integration available for sentiment analysis")
                return integration
            else:
                self.logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            self.logger.error(f"Failed to initialize Perplexity integration: {e!s}")
            return None

    def get_news_data(self, ticker: str, max_articles: int) -> list[dict]:
        """Get news data from Yahoo Finance."""
        try:
            self.logger.debug(f"Fetching news data for {ticker} (max {max_articles} articles)")

            # Create yfinance ticker object
            stock = yf.Ticker(ticker)

            # Get news data
            news = stock.news

            if not news:
                self.logger.warning(f"No news data found for ticker {ticker}")
                return []

            # Limit to max_articles
            limited_news = news[:max_articles]

            # Filter out articles with invalid URLs
            valid_news = self._filter_valid_articles(limited_news)

            self.logger.info(f"Retrieved {len(valid_news)} valid news articles for {ticker} (filtered from {len(limited_news)})")
            return valid_news

        except Exception as e:
            self.logger.error(f"Error fetching news data for {ticker}: {e}")
            raise

    def filter_news_by_date(self, news_data: list[dict], days_back: int) -> list[dict]:
        """Filter news articles by date range."""
        if not news_data:
            return []

        # Calculate cutoff timestamp
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
        cutoff_timestamp = cutoff_date.timestamp()

        filtered_news = []
        for article in news_data:
            published_time = article.get("providerPublishTime")
            if published_time and published_time >= cutoff_timestamp:
                filtered_news.append(article)

        self.logger.debug(f"Filtered {len(news_data)} articles to {len(filtered_news)} within {days_back} days")
        return filtered_news

    def filter_sonar_articles_by_date(self, sonar_articles: list[SonarArticle], days_back: int) -> list[SonarArticle]:
        """Filter Sonar articles by date range."""
        if not sonar_articles:
            return []

        # Calculate cutoff date
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)

        filtered_articles = []
        for article in sonar_articles:
            try:
                # Parse the published date from Sonar article
                if hasattr(article, "published_date") and article.published_date:
                    # Assume published_date is a datetime object or ISO string
                    if isinstance(article.published_date, str):
                        published_date = datetime.datetime.fromisoformat(article.published_date.replace("Z", "+00:00"))
                    else:
                        published_date = article.published_date

                    if published_date >= cutoff_date:
                        filtered_articles.append(article)
                else:
                    # If no date available, include the article
                    filtered_articles.append(article)
            except Exception as e:
                self.logger.warning(f"Error parsing date for Sonar article: {e}")
                # Include article if date parsing fails
                filtered_articles.append(article)

        self.logger.debug(f"Filtered {len(sonar_articles)} Sonar articles to {len(filtered_articles)} within {days_back} days")
        return filtered_articles

    def combine_article_sources(self, yahoo_articles: list[dict], sonar_articles: list[SonarArticle]) -> list[dict]:
        """Combine Yahoo Finance and Sonar articles into unified format."""
        combined_articles = yahoo_articles.copy()

        # Convert Sonar articles to Yahoo Finance format
        for sonar_article in sonar_articles:
            try:
                # Get URL and validate it
                url = getattr(sonar_article, "url", "")
                if not self._is_valid_url(url):
                    self.logger.debug(f"Skipping Sonar article with invalid URL: {getattr(sonar_article, 'title', 'Unknown')}")
                    continue

                # Convert Sonar article to unified format
                unified_article = {
                    "title": getattr(sonar_article, "title", ""),
                    "summary": getattr(sonar_article, "summary", ""),
                    "publisher": getattr(sonar_article, "domain", "Perplexity Sonar"),
                    "link": url,
                    "providerPublishTime": self._convert_sonar_timestamp(sonar_article),
                    "source": "perplexity_sonar",
                }

                # Avoid duplicates by checking title similarity
                if not self._is_duplicate_article(unified_article, combined_articles):
                    combined_articles.append(unified_article)

            except Exception as e:
                self.logger.warning(f"Error converting Sonar article: {e}")
                continue

        self.logger.info(f"Combined {len(yahoo_articles)} Yahoo articles with {len(sonar_articles)} Sonar articles, total: {len(combined_articles)}")
        return combined_articles

    def _convert_sonar_timestamp(self, sonar_article: SonarArticle) -> float | None:
        """Convert Sonar article timestamp to Unix timestamp."""
        try:
            if hasattr(sonar_article, "published_date") and sonar_article.published_date:
                if isinstance(sonar_article.published_date, str):
                    # Parse ISO format date
                    date = datetime.datetime.fromisoformat(sonar_article.published_date.replace("Z", "+00:00"))
                    return date.timestamp()
                elif hasattr(sonar_article.published_date, "timestamp"):
                    return sonar_article.published_date.timestamp()
            return None
        except Exception as e:
            self.logger.warning(f"Error converting Sonar timestamp: {e}")
            return None

    def _is_duplicate_article(self, new_article: dict, existing_articles: list[dict]) -> bool:
        """Check if article is a duplicate based on title similarity."""
        new_title = new_article.get("title", "").lower()
        if not new_title:
            return False

        for existing in existing_articles:
            existing_title = existing.get("title", "").lower()
            if not existing_title:
                continue

            # Simple similarity check - if titles share significant words
            new_words = set(new_title.split())
            existing_words = set(existing_title.split())

            # Remove common words
            common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            new_words -= common_words
            existing_words -= common_words

            if len(new_words) > 0 and len(existing_words) > 0:
                # Calculate Jaccard similarity
                intersection = len(new_words & existing_words)
                union = len(new_words | existing_words)
                similarity = intersection / union if union > 0 else 0

                if similarity > 0.6:  # 60% similarity threshold
                    return True

        return False

    def get_data_sources_list(self, yahoo_articles: list[dict], sonar_articles: list[SonarArticle]) -> list[str]:
        """Get list of data sources used in analysis."""
        sources = []

        if yahoo_articles:
            sources.append("Yahoo Finance")

        if sonar_articles:
            sources.append("Perplexity Sonar")

        return sources

    def validate_ticker_format(self, ticker: str, asset_type: str) -> str:
        """Validate and format ticker symbol for different asset types."""
        ticker = ticker.upper().strip()

        if asset_type == "crypto":
            # Ensure crypto tickers have proper format
            if not ticker.endswith("-USD") and ticker not in ["BTC", "ETH", "ADA", "DOT"]:
                # Common crypto symbols that might need USD suffix
                crypto_symbols = ["BTC", "ETH", "ADA", "DOT", "LINK", "UNI", "AAVE", "COMP"]
                if any(ticker.startswith(symbol) for symbol in crypto_symbols):
                    ticker = f"{ticker}-USD"

        elif asset_type == "stock":
            # Remove any suffixes that might interfere with Yahoo Finance
            ticker = ticker.split(".")[0]  # Remove exchange suffixes like .L, .TO

        elif asset_type == "etf":
            # ETFs typically don't need special formatting
            pass

        return ticker

    def get_asset_specific_search_terms(self, ticker: str, asset_type: str) -> list[str]:
        """Get asset-specific search terms for enhanced news discovery."""
        base_terms = [ticker]

        if asset_type == "crypto":
            # Add cryptocurrency-specific terms
            crypto_names = {
                "BTC": ["Bitcoin", "BTC"],
                "ETH": ["Ethereum", "ETH"],
                "ADA": ["Cardano", "ADA"],
                "DOT": ["Polkadot", "DOT"],
            }

            base_symbol = ticker.replace("-USD", "")
            if base_symbol in crypto_names:
                base_terms.extend(crypto_names[base_symbol])

        elif asset_type == "stock":
            # For stocks, we might want to add company name
            # This would require a lookup table or API call
            pass

        elif asset_type == "etf":
            # For ETFs, we might want to add fund name
            # This would require a lookup table or API call
            pass

        return base_terms

    def get_source_reliability_score(self, publisher: str) -> float:
        """Get reliability score for a news source."""
        if not publisher:
            return 0.5

        publisher_lower = publisher.lower()

        # Tier 1: Highest reliability (Financial news specialists)
        tier1_sources = [
            "bloomberg",
            "reuters",
            "wall street journal",
            "financial times",
            "marketwatch",
            "yahoo finance",
            "cnbc",
            "seeking alpha",
            "barron's",
        ]

        # Tier 2: High reliability (Major news outlets)
        tier2_sources = [
            "associated press",
            "bbc",
            "npr",
            "washington post",
            "new york times",
            "guardian",
            "axios",
            "forbes",
            "fortune",
        ]

        # Tier 3: Medium reliability (General news)
        tier3_sources = ["cnn", "usa today", "politico", "time", "newsweek", "abc news", "cbs news", "nbc news", "fox business"]

        # Check tiers
        for source in tier1_sources:
            if source in publisher_lower:
                return 1.0

        for source in tier2_sources:
            if source in publisher_lower:
                return 0.8

        for source in tier3_sources:
            if source in publisher_lower:
                return 0.6

        # Special handling for Perplexity Sonar
        if "perplexity" in publisher_lower or "sonar" in publisher_lower:
            return 0.9

        # Default for unknown sources
        return 0.4

    def estimate_article_reach(self, article: dict[str, Any]) -> str:
        """Estimate the potential reach/impact of an article based on source."""
        publisher = article.get("publisher", "").lower()

        # High reach sources
        high_reach = ["bloomberg", "reuters", "cnbc", "yahoo finance", "marketwatch"]
        medium_reach = ["seeking alpha", "barron's", "financial times", "wall street journal"]

        if any(source in publisher for source in high_reach):
            return "High"
        elif any(source in publisher for source in medium_reach):
            return "Medium"
        else:
            return "Low"

    async def get_enhanced_news_data(self, ticker: str, asset_type: str, max_articles: int) -> dict[str, Any]:
        """Get enhanced news data from multiple sources including Sonar."""
        # Get existing Yahoo Finance data
        yahoo_data = self.get_news_data(ticker, max_articles)

        # Optionally enhance with Sonar data with graceful fallback
        sonar_data = []
        sonar_fallback_used = False
        perplexity_integration = self.get_perplexity_integration()

        if perplexity_integration:
            try:
                sonar_result = await perplexity_integration.search_sentiment_news(
                    ticker=ticker, asset_type=cast(Literal["stock", "etf", "crypto"], asset_type), max_results=max_articles // 2
                )

                if sonar_result.success:
                    sonar_data = sonar_result.results
                    self.logger.info(f"Retrieved {len(sonar_data)} Sonar articles for {ticker}")
                    # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
                else:
                    # Sonar failed but we continue with existing data
                    sonar_fallback_used = True
                    self.logger.warning(f"Sonar search failed for {ticker}, continuing with Yahoo Finance only: {sonar_result.error_message}")
                    # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure

            except Exception as e:
                # Any exception in Sonar integration should not break the reporter flow
                sonar_fallback_used = True
                self.logger.warning(f"Sonar integration error for {ticker}, continuing with Yahoo Finance only: {e!s}")

                # Record failure for feature flag tracking
                from finwiz.tools.perplexity_logging import PerplexityFeatureFlagTracker

                PerplexityFeatureFlagTracker.record_operation_failure(ticker, "sentiment", "integration_error")
        else:
            # Perplexity integration not available, continue normally
            self.logger.debug(f"Perplexity integration not available for {ticker}, using Yahoo Finance only")

        return {
            "yahoo_articles": yahoo_data,
            "sonar_articles": sonar_data,
            "combined_count": len(yahoo_data) + len(sonar_data),
            "sonar_fallback_used": sonar_fallback_used,
        }

    def format_news_article(self, raw_article: dict[str, Any]) -> dict[str, Any]:
        """Format raw news article into standardized format."""
        return {
            "title": raw_article.get("title", "No title"),
            "publisher": raw_article.get("publisher", "Unknown"),
            "link": raw_article.get("link", ""),
            "published_time": raw_article.get("providerPublishTime", None),
            "summary": raw_article.get("summary", ""),
            "raw_item": raw_article,
            "source": "yahoo_finance",
        }
