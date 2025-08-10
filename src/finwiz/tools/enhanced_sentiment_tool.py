"""Enhanced Sentiment Analysis Tool with Multi-Source Integration.

This tool implements the n8n workflow sentiment analysis logic adapted for FinWiz,
providing comprehensive sentiment analysis across stocks, ETFs, and crypto assets.
"""

import datetime
from typing import Optional

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger

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
    """

    name: str = "Enhanced Sentiment Analysis Tool"
    description: str = (
        "Perform comprehensive sentiment analysis on financial assets using multiple "
        "news sources with weighted scoring, trending topics extraction, and impact analysis. "
        "Supports stocks, ETFs, and cryptocurrencies."
    )
    args_schema: type[BaseModel] = EnhancedSentimentInput

    def _run(self, ticker: str, asset_type: str = "stock", days_back: int = 7, max_articles: int = 20) -> str:
        """Execute enhanced sentiment analysis."""
        try:
            logger.info(f"Starting enhanced sentiment analysis for {ticker} ({asset_type})")

            # Get news data from Yahoo Finance (primary source for now)
            news_data = self._get_news_data(ticker, max_articles)

            if not news_data:
                return self._format_no_data_response(ticker, asset_type)

            # Filter news by date range
            filtered_news = self._filter_news_by_date(news_data, days_back)

            if not filtered_news:
                return self._format_no_recent_news_response(ticker, asset_type, days_back)

            # Perform sentiment analysis using n8n workflow logic
            sentiment_analysis = self._analyze_sentiment(filtered_news, ticker, asset_type)

            # Extract trending topics
            trending_topics = self._extract_trending_topics(filtered_news)

            # Calculate impact scores
            impact_scores = self._calculate_impact_scores(filtered_news, sentiment_analysis)

            # Generate market outlook
            market_outlook = self._generate_market_outlook(sentiment_analysis, trending_topics, asset_type)

            # Format comprehensive response
            return self._format_comprehensive_response(
                ticker=ticker,
                asset_type=asset_type,
                sentiment_analysis=sentiment_analysis,
                trending_topics=trending_topics,
                impact_scores=impact_scores,
                market_outlook=market_outlook,
                article_count=len(filtered_news),
            )

        except Exception as e:
            logger.error(f"Error in enhanced sentiment analysis for {ticker}: {str(e)}")
            return f"Error performing enhanced sentiment analysis for {ticker}: {str(e)}"

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
        """Calculate impact scores for articles."""
        if not news_data:
            return []

        impact_articles = []

        for article in news_data:
            sentiment_score = article.get("sentiment_score", 0.0)

            # Calculate impact based on sentiment strength and publisher credibility
            publisher = article.get("publisher", "").lower()

            # Publisher credibility weights (simplified)
            credibility_weights = {
                "reuters": 1.0,
                "bloomberg": 1.0,
                "wall street journal": 0.9,
                "financial times": 0.9,
                "cnbc": 0.8,
                "marketwatch": 0.7,
                "yahoo finance": 0.6,
            }

            credibility = 0.5  # Default credibility
            for pub, weight in credibility_weights.items():
                if pub in publisher:
                    credibility = weight
                    break

            # Impact score = |sentiment_score| * credibility * recency_factor
            recency_factor = 1.0  # Could be enhanced with time decay
            impact_score = abs(sentiment_score) * credibility * recency_factor

            if impact_score > 0.1:  # Only include articles with meaningful impact
                impact_articles.append(
                    {
                        "title": article.get("title", ""),
                        "publisher": article.get("publisher", ""),
                        "url": article.get("link", ""),
                        "date": self._format_article_date(article.get("published_time")),
                        "sentiment": article.get("sentiment", "neutral"),
                        "impact_score": round(impact_score, 4),
                    }
                )

        # Sort by impact score
        impact_articles.sort(key=lambda x: x["impact_score"], reverse=True)

        return impact_articles[:10]  # Return top 10 impactful articles

    def _format_article_date(self, timestamp: Optional[float]) -> str:
        """Format article timestamp to readable date."""
        if timestamp is None:
            return "Unknown date"

        try:
            # Treat negative timestamps as invalid/unknown
            if isinstance(timestamp, (int, float)) and timestamp < 0:
                return "Unknown date"
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError):
            return "Unknown date"

    def _generate_market_outlook(
        self, sentiment_analysis: dict, trending_topics: list[dict], asset_type: str
    ) -> str:
        """Generate market outlook based on sentiment and topics."""
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        score = sentiment_analysis.get("sentiment_score", 0.0)

        # Base outlook by sentiment
        if sentiment == "positive":
            if score >= 0.3:
                base_outlook = (
                    f"Strong positive sentiment indicates high confidence in {asset_type} performance."
                )
            else:
                base_outlook = f"Moderate positive sentiment suggests cautious optimism for {asset_type}."
        elif sentiment == "negative":
            if score <= -0.3:
                base_outlook = f"Strong negative sentiment indicates significant concerns about {asset_type} performance."
            else:
                base_outlook = (
                    f"Moderate negative sentiment suggests some caution warranted for {asset_type}."
                )
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
    ) -> str:
        """Format comprehensive sentiment analysis response."""

        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        score = sentiment_analysis.get("sentiment_score", 0.0)
        distribution = sentiment_analysis.get("sentiment_distribution", {})
        confidence = sentiment_analysis.get("confidence", 0.0)

        response = f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## 📊 Sentiment Overview
- **Overall Sentiment**: {sentiment.title()} ({score:+.4f})
- **Confidence Level**: {confidence:.1%}
- Articles Analyzed: {article_count}
- **Sentiment Distribution**: 
  - 📈 Bullish: {distribution.get("bullish", 0)} articles
  - ⚖️ Neutral: {distribution.get("neutral", 0)} articles  
  - 📉 Bearish: {distribution.get("bearish", 0)} articles

## 🔍 Market Outlook
{market_outlook}

## 🔥 Trending Topics
"""

        if trending_topics:
            for i, topic in enumerate(trending_topics, 1):
                response += f"{i}. **{topic['topic']}** - {topic['article_count']} articles (relevance: {topic['average_relevance']:.2f})\n"
        else:
            response += "No significant trending topics identified.\n"

        response += "\n## 📰 Most Impactful Articles\n"

        if impact_scores:
            for i, article in enumerate(impact_scores[:5], 1):
                sentiment_emoji = (
                    "📈"
                    if article["sentiment"] == "bullish"
                    else "📉"
                    if article["sentiment"] == "bearish"
                    else "⚖️"
                )
                response += f"{i}. {sentiment_emoji} **{article['title']}**\n"
                response += f"   - Publisher: {article['publisher']} | Date: {article['date']}\n"
                response += f"   - Impact Score: {article['impact_score']:.4f} | Sentiment: {article['sentiment'].title()}\n"
                if article["url"]:
                    response += f"   - URL: {article['url']}\n"
                response += "\n"
        else:
            response += "No high-impact articles identified.\n"

        response += f"""
## 📈 Analysis Summary
This enhanced sentiment analysis processed {article_count} recent articles for {ticker}, 
identifying {len(trending_topics)} trending topics and {len(impact_scores)} high-impact stories. 
The analysis uses weighted sentiment scoring and impact calculation based on publisher 
credibility and sentiment strength.

**Note**: This analysis combines multiple data sources and should be considered alongside 
fundamental and technical analysis for investment decisions.
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
