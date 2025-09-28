"""
Enhanced Sentiment Analysis Tool with Multi-Source Integration.

This tool implements the n8n workflow sentiment analysis logic adapted for FinWiz,
providing comprehensive sentiment analysis across stocks, ETFs, and crypto assets.
"""

import asyncio
import datetime

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.schemas.perplexity import SonarArticle
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration
from finwiz.utils.feature_flags import get_feature_flags

logger = get_logger(__name__)


class EnhancedSentimentInput(BaseModel):
    """Input schema for enhanced sentiment analysis."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")
    asset_type: str = Field("stock", description="Asset type: 'stock', 'etf', or 'crypto'")
    days_back: int = Field(7, description="Number of days to look back for news (1-30)")
    max_articles: int = Field(20, description="Maximum number of articles to analyze (5-50)")


class EnhancedSentimentAnalysisTool(BaseTool):
    """
    Enhanced sentiment analysis tool with multi-source integration.

    Implements n8n workflow logic for:
    - Multi-source news aggregation
    - Weighted sentiment scoring
    - Trending topics extraction
    - Impact scoring calculation
    - Asset-specific adaptation
    - Optional Perplexity Sonar integration
    """

    name: str = "Enhanced Sentiment Analysis Tool"
    description: str = (
        "Perform comprehensive sentiment analysis on financial assets using multiple "
        "news sources with weighted scoring, trending topics extraction, and impact analysis. "
        "Supports stocks, ETFs, and cryptocurrencies with optional Perplexity Sonar integration."
    )
    args_schema: type[BaseModel] = EnhancedSentimentInput

    def _get_perplexity_integration(self) -> PerplexityAnalysisIntegration | None:
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
            from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

            integration = PerplexityAnalysisIntegration()
            if integration.is_available:
                logger.debug("Perplexity Sonar integration available for sentiment analysis")
                return integration
            else:
                logger.warning("Perplexity integration initialized but API key not available")
                return None
        except Exception as e:
            logger.error(f"Failed to initialize Perplexity integration: {str(e)}")
            return None

    def _run(self, ticker: str, asset_type: str = "stock", days_back: int = 7, max_articles: int = 20) -> str:
        """Execute enhanced sentiment analysis."""
        try:
            logger.info(f"Starting enhanced sentiment analysis for {ticker} ({asset_type})")

            # Get enhanced news data from multiple sources including Sonar
            enhanced_news_data = asyncio.run(self._get_enhanced_news_data(ticker, asset_type, max_articles))

            yahoo_articles = enhanced_news_data.get("yahoo_articles", [])
            sonar_articles = enhanced_news_data.get("sonar_articles", [])
            combined_count = enhanced_news_data.get("combined_count", 0)
            sonar_fallback_used = enhanced_news_data.get("sonar_fallback_used", False)

            if combined_count == 0:
                return self._format_no_data_response(ticker, asset_type)

            # Filter news by date range
            filtered_yahoo = self._filter_news_by_date(yahoo_articles, days_back)
            filtered_sonar = self._filter_sonar_articles_by_date(sonar_articles, days_back)

            if not filtered_yahoo and not filtered_sonar:
                return self._format_no_recent_news_response(ticker, asset_type, days_back)

            # Combine filtered articles for analysis
            combined_articles = self._combine_article_sources(filtered_yahoo, filtered_sonar)

            # Perform sentiment analysis using n8n workflow logic
            sentiment_analysis = self._analyze_sentiment(combined_articles, ticker, asset_type)

            # Extract trending topics
            trending_topics = self._extract_trending_topics(combined_articles)

            # Calculate impact scores
            impact_scores = self._calculate_impact_scores(combined_articles, sentiment_analysis)

            # Generate market outlook
            market_outlook = self._generate_market_outlook(sentiment_analysis, trending_topics, asset_type)

            # Format comprehensive response with Sonar integration
            return self._format_comprehensive_response(
                ticker=ticker,
                asset_type=asset_type,
                sentiment_analysis=sentiment_analysis,
                trending_topics=trending_topics,
                impact_scores=impact_scores,
                market_outlook=market_outlook,
                article_count=len(combined_articles),
                sonar_articles=filtered_sonar,
                data_sources=self._get_data_sources_list(filtered_yahoo, filtered_sonar),
                sonar_fallback_used=sonar_fallback_used,
            )

        except Exception as e:
            logger.error(f"Error in enhanced sentiment analysis for {ticker}: {str(e)}")
            return f"Error performing enhanced sentiment analysis for {ticker}: {str(e)}"

    async def _get_enhanced_news_data(self, ticker: str, asset_type: str, max_articles: int) -> dict:
        """Get enhanced news data from multiple sources including Sonar."""
        # Get existing Yahoo Finance data
        yahoo_data = self._get_news_data(ticker, max_articles)

        # Optionally enhance with Sonar data with graceful fallback
        sonar_data = []
        sonar_fallback_used = False
        perplexity_integration = self._get_perplexity_integration()

        if perplexity_integration:
            try:
                sonar_result = await perplexity_integration.search_sentiment_news(
                    ticker=ticker, asset_type=asset_type, max_results=max_articles // 2
                )

                if sonar_result.success:
                    sonar_data = sonar_result.results
                    logger.info(f"Retrieved {len(sonar_data)} Sonar articles for {ticker}")
                    # Success tracking is handled automatically in PerplexityOperationLogger.log_search_success
                else:
                    # Sonar failed but we continue with existing data
                    sonar_fallback_used = True
                    logger.warning(
                        f"Sonar search failed for {ticker}, continuing with Yahoo Finance only: {sonar_result.error_message}"
                    )
                    # Failure tracking is handled automatically in PerplexityOperationLogger.log_search_failure

            except Exception as e:
                # Any exception in Sonar integration should not break the reporter flow
                sonar_fallback_used = True
                logger.warning(f"Sonar integration error for {ticker}, continuing with Yahoo Finance only: {str(e)}")

                # Record failure for feature flag tracking
                from finwiz.tools.perplexity_analysis_integration import PerplexityFeatureFlagTracker

                PerplexityFeatureFlagTracker.record_operation_failure(ticker, "sentiment", "integration_error")
        else:
            # Perplexity integration not available, continue normally
            logger.debug(f"Perplexity integration not available for {ticker}, using Yahoo Finance only")

        return {
            "yahoo_articles": yahoo_data,
            "sonar_articles": sonar_data,
            "combined_count": len(yahoo_data) + len(sonar_data),
            "sonar_fallback_used": sonar_fallback_used,
        }

    def _get_news_data(self, ticker: str, max_articles: int) -> list[dict]:
        """Get news data from Yahoo Finance."""
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news

            if not news:
                return []

            # Limit articles and format
            news = news[:max_articles]
            formatted_news = []

            for item in news:
                formatted_news.append(
                    {
                        "title": item.get("title", "No title"),
                        "publisher": item.get("publisher", "Unknown"),
                        "link": item.get("link", ""),
                        "published_time": item.get("providerPublishTime", None),
                        "summary": item.get("summary", ""),
                        "raw_item": item,
                        "source": "yahoo_finance",
                    }
                )

            return formatted_news

        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {str(e)}")
            # Re-raise so outer handler can format an explicit error response
            raise

    def _filter_news_by_date(self, news_data: list[dict], days_back: int) -> list[dict]:
        """Filter news articles by date range."""
        if not news_data:
            return []

        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days_back)
        cutoff_timestamp = cutoff_time.timestamp()

        filtered_news = []
        for article in news_data:
            published_time = article.get("published_time")
            if published_time and published_time >= cutoff_timestamp:
                filtered_news.append(article)

        return filtered_news

    def _filter_sonar_articles_by_date(self, sonar_articles: list[SonarArticle], days_back: int) -> list[SonarArticle]:
        """Filter Sonar articles by date range."""
        if not sonar_articles:
            return []

        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days_back)

        filtered_articles = []
        for article in sonar_articles:
            if article.published_date:
                try:
                    # Parse ISO format date
                    article_date = datetime.datetime.fromisoformat(article.published_date.replace("Z", "+00:00"))
                    if article_date >= cutoff_time:
                        filtered_articles.append(article)
                except ValueError:
                    # If date parsing fails, include the article
                    filtered_articles.append(article)
            else:
                # If no date, include the article
                filtered_articles.append(article)

        return filtered_articles

    def _combine_article_sources(self, yahoo_articles: list[dict], sonar_articles: list[SonarArticle]) -> list[dict]:
        """Combine Yahoo Finance and Sonar articles into unified format."""
        combined_articles = yahoo_articles.copy()

        # Convert Sonar articles to Yahoo format for compatibility
        for sonar_article in sonar_articles:
            try:
                # Convert published_date to timestamp if available
                published_time = None
                if sonar_article.published_date:
                    try:
                        dt = datetime.datetime.fromisoformat(sonar_article.published_date.replace("Z", "+00:00"))
                        published_time = dt.timestamp()
                    except ValueError:
                        published_time = None

                yahoo_format_article = {
                    "title": sonar_article.title,
                    "publisher": sonar_article.publisher,
                    "link": str(sonar_article.url),
                    "published_time": published_time,
                    "summary": sonar_article.summary,
                    "source": "perplexity_sonar",
                    "relevance_score": sonar_article.relevance_score,
                    "content_type": sonar_article.content_type,
                    "analysis_type": sonar_article.analysis_type,
                }
                combined_articles.append(yahoo_format_article)
            except Exception as e:
                logger.warning(f"Failed to convert Sonar article to Yahoo format: {str(e)}")
                continue

        return combined_articles

    def _get_data_sources_list(self, yahoo_articles: list[dict], sonar_articles: list[SonarArticle]) -> list[str]:
        """Get list of data sources used in analysis."""
        sources = []
        if yahoo_articles:
            sources.append("Yahoo Finance")
        if sonar_articles:
            sources.append("Perplexity Sonar")
        return sources

    def _analyze_sentiment(self, news_data: list[dict], ticker: str, asset_type: str) -> dict:
        """
        Analyze sentiment using n8n workflow logic.

        This is a simplified implementation that would be enhanced with
        actual sentiment analysis APIs (Alpha Vantage, etc.) in production.
        """
        if not news_data:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "sentiment_distribution": {"bullish": 0, "neutral": 0, "bearish": 0},
                "confidence": 0.0,
            }

        # Simple keyword-based sentiment analysis (placeholder for API integration)
        bullish_keywords = [
            "growth",
            "profit",
            "revenue",
            "beat",
            "exceed",
            "strong",
            "positive",
            "upgrade",
            "buy",
            "bullish",
            "rally",
            "surge",
            "gain",
            "rise",
            "up",
        ]

        bearish_keywords = [
            "loss",
            "decline",
            "fall",
            "drop",
            "weak",
            "negative",
            "downgrade",
            "sell",
            "bearish",
            "crash",
            "plunge",
            "down",
            "concern",
            "risk",
        ]

        sentiment_scores = []
        sentiment_counts = {"bullish": 0, "neutral": 0, "bearish": 0}

        for article in news_data:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            text = f"{title} {summary}"

            bullish_count = sum(1 for keyword in bullish_keywords if keyword in text)
            bearish_count = sum(1 for keyword in bearish_keywords if keyword in text)

            if bullish_count > bearish_count:
                sentiment = "bullish"
                score = min(0.8, 0.1 + (bullish_count - bearish_count) * 0.1)
            elif bearish_count > bullish_count:
                sentiment = "bearish"
                score = max(-0.8, -0.1 - (bearish_count - bullish_count) * 0.1)
            else:
                sentiment = "neutral"
                score = 0.0

            sentiment_counts[sentiment] += 1
            sentiment_scores.append(score)

            # Add sentiment to article data
            article["sentiment"] = sentiment
            article["sentiment_score"] = score

        # Calculate overall metrics
        avg_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

        # Determine overall sentiment
        if avg_score >= 0.15:
            overall_sentiment = "positive"
        elif avg_score <= -0.15:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        # Calculate confidence based on article count and score consistency
        confidence = min(1.0, len(news_data) / 10.0) * (1.0 - abs(avg_score) if abs(avg_score) < 0.5 else 0.5)

        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(avg_score, 4),
            "sentiment_distribution": sentiment_counts,
            "confidence": round(confidence, 2),
        }

    def _extract_trending_topics(self, news_data: list[dict]) -> list[dict]:
        """Extract trending topics from news articles."""
        if not news_data:
            return []

        # Simple topic extraction based on common financial terms
        # In production, this would use more sophisticated NLP
        topic_keywords = {
            "earnings": ["earnings", "profit", "revenue", "eps", "quarterly"],
            "merger_acquisition": ["merger", "acquisition", "buyout", "takeover"],
            "regulation": ["regulation", "regulatory", "sec", "compliance", "policy"],
            "market_trends": ["market", "sector", "industry", "trend", "outlook"],
            "technology": ["technology", "ai", "digital", "innovation", "tech"],
            "financial_results": ["results", "performance", "guidance", "forecast"],
            "leadership": ["ceo", "management", "leadership", "executive", "board"],
            "product_launch": ["launch", "product", "service", "announcement", "release"],
        }

        topic_counts = {}
        topic_relevance = {}

        for article in news_data:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            text = f"{title} {summary}"

            for topic, keywords in topic_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    if topic not in topic_counts:
                        topic_counts[topic] = 0
                        topic_relevance[topic] = 0

                    topic_counts[topic] += 1
                    topic_relevance[topic] += matches / len(keywords)

        # Create trending topics list
        trending_topics = []
        for topic, count in topic_counts.items():
            if count >= 2:  # Only include topics mentioned in multiple articles
                avg_relevance = topic_relevance[topic] / count
                trending_topics.append(
                    {
                        "topic": topic.replace("_", " ").title(),
                        "article_count": count,
                        "average_relevance": round(avg_relevance, 2),
                    }
                )

        # Sort by article count and relevance
        trending_topics.sort(key=lambda x: (x["article_count"], x["average_relevance"]), reverse=True)

        return trending_topics[:5]  # Return top 5 topics

    def _calculate_impact_scores(self, news_data: list[dict], sentiment_analysis: dict) -> list[dict]:
        """Calculate enhanced impact scores for articles including Sonar data."""
        if not news_data:
            return []

        impact_articles = []

        for article in news_data:
            sentiment_score = article.get("sentiment_score", 0.0)
            publisher = article.get("publisher", "").lower()
            source = article.get("source", "yahoo_finance")

            # Enhanced publisher credibility weights including Sonar sources
            credibility_weights = {
                # Tier 1: Premium financial sources
                "reuters": 1.0,
                "bloomberg": 1.0,
                "wall street journal": 0.95,
                "financial times": 0.95,
                "dow jones": 0.95,
                # Tier 2: Major financial media
                "cnbc": 0.85,
                "marketwatch": 0.8,
                "seeking alpha": 0.75,
                "barron's": 0.85,
                "investor's business daily": 0.8,
                # Tier 3: General financial sources
                "yahoo finance": 0.65,
                "motley fool": 0.6,
                "benzinga": 0.65,
                "zacks": 0.7,
                # Tier 4: Specialized sources (often found via Sonar)
                "sec.gov": 0.95,  # SEC filings
                "investor.gov": 0.9,  # SEC investor resources
                "federalreserve.gov": 0.95,  # Federal Reserve
                "treasury.gov": 0.9,  # US Treasury
            }

            # Base credibility calculation
            credibility = 0.5  # Default credibility
            for pub, weight in credibility_weights.items():
                if pub in publisher:
                    credibility = weight
                    break

            # Sonar-specific enhancements
            sonar_boost = 1.0
            relevance_boost = 1.0

            if source == "perplexity_sonar":
                # Apply Sonar-specific scoring enhancements

                # 1. Relevance scoring based on Perplexity response data
                relevance_score = article.get("relevance_score", 0.0)
                if relevance_score > 0:
                    # Boost impact for highly relevant Sonar articles
                    relevance_boost = 1.0 + (relevance_score * 0.3)  # Up to 30% boost for perfect relevance

                # 2. Content type weighting for Sonar articles
                content_type = article.get("content_type", "news")
                content_type_weights = {
                    "filing": 1.2,  # SEC filings are highly impactful
                    "earnings": 1.15,  # Earnings reports are very important
                    "regulatory": 1.1,  # Regulatory news has high impact
                    "analysis": 1.05,  # Professional analysis gets slight boost
                    "news": 1.0,  # Standard news baseline
                }
                content_boost = content_type_weights.get(content_type, 1.0)

                # 3. Analysis type context weighting
                analysis_type = article.get("analysis_type", "general")
                analysis_weights = {
                    "fundamental": 1.1,  # Fundamental analysis is highly relevant
                    "technical": 1.05,  # Technical analysis gets moderate boost
                    "sentiment": 1.0,  # Sentiment analysis baseline
                    "general": 0.95,  # General content slightly lower
                }
                analysis_boost = analysis_weights.get(analysis_type, 1.0)

                # Combine Sonar-specific boosts
                sonar_boost = relevance_boost * content_boost * analysis_boost

                # Additional credibility boost for Sonar sources (they're pre-filtered for quality)
                credibility = min(1.0, credibility * 1.1)  # 10% credibility boost, capped at 1.0

            # Calculate recency factor with enhanced time decay
            recency_factor = self._calculate_recency_factor(article.get("published_time"))

            # Enhanced impact score calculation
            # Impact = |sentiment| * credibility * recency * sonar_enhancements
            base_impact = abs(sentiment_score) * credibility * recency_factor
            enhanced_impact = base_impact * sonar_boost

            # Apply minimum threshold for inclusion
            impact_threshold = 0.08 if source == "perplexity_sonar" else 0.1

            if enhanced_impact > impact_threshold:
                impact_articles.append(
                    {
                        "title": article.get("title", ""),
                        "publisher": article.get("publisher", ""),
                        "url": article.get("link", ""),
                        "date": self._format_article_date(article.get("published_time")),
                        "sentiment": article.get("sentiment", "neutral"),
                        "impact_score": round(enhanced_impact, 4),
                        "source": source,
                        "credibility_score": round(credibility, 3),
                        "relevance_score": article.get("relevance_score", 0.0),
                        "content_type": article.get("content_type", "news"),
                        "sonar_boost": round(sonar_boost, 3) if source == "perplexity_sonar" else None,
                    }
                )

        # Sort by impact score (descending)
        impact_articles.sort(key=lambda x: x["impact_score"], reverse=True)

        return impact_articles[:10]  # Return top 10 impactful articles

    def _calculate_recency_factor(self, published_time: float | None) -> float:
        """Calculate recency factor for impact scoring with time decay."""
        if published_time is None:
            return 0.8  # Default for articles without timestamps

        try:
            if isinstance(published_time, (int, float)) and published_time < 0:
                return 0.8  # Default for invalid timestamps

            current_time = datetime.datetime.now().timestamp()
            time_diff_hours = (current_time - published_time) / 3600

            # Time decay function: more recent articles get higher scores
            if time_diff_hours <= 6:
                return 1.0  # Last 6 hours: full weight
            elif time_diff_hours <= 24:
                return 0.95  # Last day: 95% weight
            elif time_diff_hours <= 72:
                return 0.9  # Last 3 days: 90% weight
            elif time_diff_hours <= 168:
                return 0.85  # Last week: 85% weight
            else:
                return 0.8  # Older: 80% weight

        except (ValueError, OSError):
            return 0.8  # Default for invalid timestamps

    def _format_article_date(self, timestamp: float | None) -> str:
        """Format article timestamp to readable date."""
        if timestamp is None:
            return "Unknown date"

        try:
            # Treat negative timestamps as invalid/unknown
            if isinstance(timestamp, int | float) and timestamp < 0:
                return "Unknown date"
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return "Unknown date"

    def _generate_market_outlook(self, sentiment_analysis: dict, trending_topics: list[dict], asset_type: str) -> str:
        """Generate market outlook based on sentiment and topics."""
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        score = sentiment_analysis.get("sentiment_score", 0.0)

        # Base outlook by sentiment
        if sentiment == "positive":
            if score >= 0.3:
                base_outlook = f"Strong positive sentiment indicates high confidence in {asset_type} performance."
            else:
                base_outlook = f"Moderate positive sentiment suggests cautious optimism for {asset_type}."
        elif sentiment == "negative":
            if score <= -0.3:
                base_outlook = f"Strong negative sentiment indicates significant concerns about {asset_type} performance."
            else:
                base_outlook = f"Moderate negative sentiment suggests some caution warranted for {asset_type}."
        else:
            base_outlook = f"Mixed sentiment indicates uncertainty in {asset_type} direction."

        # Add trending topics context
        if trending_topics:
            top_topics = [topic["topic"] for topic in trending_topics[:3]]
            topics_text = ", ".join(top_topics)
            outlook = f"{base_outlook} Key themes driving discussion include: {topics_text}."
        else:
            outlook = f"{base_outlook} Limited thematic trends identified in current news cycle."

        return outlook

    def _format_comprehensive_response(
        self,
        ticker: str,
        asset_type: str,
        sentiment_analysis: dict,
        trending_topics: list[dict],
        impact_scores: list[dict],
        market_outlook: str,
        article_count: int,
        sonar_articles: list[SonarArticle] | None = None,
        data_sources: list[str] | None = None,
        sonar_fallback_used: bool = False,
    ) -> str:
        """Format comprehensive sentiment analysis response with enhanced Sonar integration."""
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        score = sentiment_analysis.get("sentiment_score", 0.0)
        distribution = sentiment_analysis.get("sentiment_distribution", {})
        confidence = sentiment_analysis.get("confidence", 0.0)

        # Calculate source diversity metrics
        yahoo_count = article_count - (len(sonar_articles) if sonar_articles else 0)
        sonar_count = len(sonar_articles) if sonar_articles else 0
        source_diversity = len(data_sources) if data_sources else 1

        # Calculate unique publishers for diversity metric
        unique_publishers = set()
        if sonar_articles:
            unique_publishers.update(article.publisher for article in sonar_articles if article.publisher)

        # Format enhanced data sources information with metrics
        sources_info = ""
        if data_sources:
            sources_info = f"- **Data Sources**: {', '.join(data_sources)} ({source_diversity} sources)\n"
            if yahoo_count > 0:
                sources_info += f"- **Yahoo Finance Articles**: {yahoo_count}\n"
            if sonar_count > 0:
                sources_info += f"- **Perplexity Sonar Articles**: {sonar_count} from {len(unique_publishers)} publishers\n"
                sources_info += f"- **Source Diversity Score**: {min(10, source_diversity + len(unique_publishers))}/10\n"

        response = f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## 📊 Sentiment Overview
- **Overall Sentiment**: {sentiment.title()} ({score:+.4f})
- **Confidence Level**: {confidence:.1%}
- **Total Articles Analyzed**: {article_count}
{sources_info}- **Sentiment Distribution**: 
  - 📈 Bullish: {distribution.get("bullish", 0)} articles
  - ⚖️ Neutral: {distribution.get("neutral", 0)} articles  
  - 📉 Bearish: {distribution.get("bearish", 0)} articles

## 🔍 Market Outlook
{market_outlook}

## 🔥 Trending Topics
"""

        if trending_topics:
            for i, topic in enumerate(trending_topics, 1):
                response += (
                    f"{i}. **{topic['topic']}** - {topic['article_count']} articles (relevance: {topic['average_relevance']:.2f})\n"
                )
        else:
            response += "No significant trending topics identified.\n"

        response += "\n## 📰 Most Impactful Articles\n"

        if impact_scores:
            for i, article in enumerate(impact_scores[:5], 1):
                sentiment_emoji = "📈" if article["sentiment"] == "bullish" else "📉" if article["sentiment"] == "bearish" else "⚖️"
                # Add source attribution for each article
                source_tag = ""
                if article.get("source") == "perplexity_sonar":
                    source_tag = " [Sonar]"
                elif article.get("source") == "yahoo_finance":
                    source_tag = " [Yahoo]"

                response += f"{i}. {sentiment_emoji} **{article['title']}**{source_tag}\n"
                response += f"   - Publisher: {article['publisher']} | Date: {article['date']}\n"
                response += f"   - Impact Score: {article['impact_score']:.4f} | Sentiment: {article['sentiment'].title()}\n"
                if article["url"]:
                    response += f"   - URL: {article['url']}\n"
                response += "\n"
        else:
            response += "No high-impact articles identified.\n"

        # Enhanced Sonar articles section with better formatting
        if sonar_articles:
            response += f"\n## 🔍 Perplexity Sonar Research ({len(sonar_articles)} articles)\n"
            response += f"*Fresh insights from {len(unique_publishers)} specialized financial sources*\n\n"

            for i, article in enumerate(sonar_articles[:5], 1):
                content_emoji = {"news": "📰", "filing": "📋", "analysis": "📊", "earnings": "💰", "regulatory": "⚖️"}.get(
                    article.content_type, "📰"
                )

                response += f"{i}. {content_emoji} **{article.title}**\n"
                response += f"   - **Publisher**: {article.publisher} | **Type**: {article.content_type.title()}\n"
                response += f"   - **Relevance**: {article.relevance_score:.2f} | **Context**: {article.analysis_type.title()}\n"
                if article.summary:
                    response += f"   - **Summary**: {article.summary[:200]}{'...' if len(article.summary) > 200 else ''}\n"
                if article.published_date:
                    try:
                        dt = datetime.fromisoformat(article.published_date.replace("Z", "+00:00"))
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M UTC")
                        response += f"   - **Published**: {formatted_date}\n"
                    except ValueError:
                        response += f"   - **Published**: {article.published_date}\n"
                response += f"   - **Source**: {article.url}\n\n"

            if len(sonar_articles) > 5:
                response += f"*... and {len(sonar_articles) - 5} additional Sonar articles analyzed*\n\n"

        # Enhanced fallback and integration status information
        integration_status = ""
        if sonar_fallback_used:
            integration_status = (
                "\n⚠️ **Integration Status**: Perplexity Sonar encountered issues during this analysis. "
                "Analysis completed using Yahoo Finance data only. This may result in reduced coverage "
                "of recent market developments."
            )
        elif sonar_articles:
            freshness_indicator = "🟢 Fresh" if len(sonar_articles) >= 3 else "🟡 Limited"
            integration_status = (
                f"\n✅ **Enhanced Analysis**: Successfully integrated {len(sonar_articles)} Sonar articles "
                f"from {len(unique_publishers)} specialized sources. {freshness_indicator} coverage achieved."
            )
        else:
            integration_status = (
                "\n🔵 **Standard Analysis**: Analysis completed using Yahoo Finance data. "
                "Perplexity Sonar integration was not enabled for this request."
            )

        response += f"""
## 📈 Analysis Summary
This enhanced sentiment analysis processed **{article_count} articles** from **{source_diversity} data sources** for {ticker}, 
identifying **{len(trending_topics)} trending topics** and **{len(impact_scores)} high-impact stories**. 

**Methodology**: The analysis combines weighted sentiment scoring with impact calculation based on:
- Publisher credibility and source reliability
- Article relevance and recency
- Sentiment strength and consistency
- Cross-source validation when available{integration_status}

**Investment Guidance**: This multi-source sentiment analysis should be considered alongside 
fundamental valuation metrics and technical analysis patterns for comprehensive investment decisions.

---
*Analysis completed with {source_diversity} data source{"s" if source_diversity != 1 else ""} • 
{article_count} total articles • Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")}*
"""

        return response.strip()

    def _format_no_data_response(self, ticker: str, asset_type: str) -> str:
        """Format response when no news data is available."""
        return f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## ⚠️ No Data Available
No recent news articles found for {ticker}. This could indicate:
- Limited media coverage for this asset
- Ticker symbol may not be widely recognized
- Temporary data availability issues

**Recommendation**: Verify ticker symbol and consider checking again later.
"""

    def _format_no_recent_news_response(self, ticker: str, asset_type: str, days_back: int) -> str:
        """Format response when no recent news is available."""
        return f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## ⚠️ No Recent News
No news articles found for {ticker} in the past {days_back} days. 
This could indicate a quiet news period for this asset.

**Recommendation**: Consider extending the analysis period or checking for longer-term trends.
"""
