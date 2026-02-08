"""
Response formatting utilities for sentiment analysis.

This module contains utilities for formatting sentiment analysis results
into comprehensive, user-friendly responses.
"""

from finwiz.schemas.perplexity import SonarArticle
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SentimentResponseFormatter:
    """Handles formatting of sentiment analysis responses."""

    def __init__(self) -> None:
        """Initialize sentiment response formatter."""
        self.logger = logger

    def format_comprehensive_response(
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
                # Use correct field names from sentiment_calculations.py
                # Fields are: mention_count (not article_count), relevance_score (not average_relevance)
                count = topic.get("mention_count", topic.get("article_count", 0))
                relevance = topic.get("relevance_score", topic.get("average_relevance", 0.0))
                response += f"{i}. **{topic['topic']}** - {count} articles (relevance: {relevance:.2f})\n"
        else:
            response += "No significant trending topics identified.\n"

        response += "\n## 📰 Most Impactful Articles\n"

        if impact_scores:
            for i, article in enumerate(impact_scores[:5], 1):
                sentiment_emoji = "📈" if article["sentiment"] == "bullish" else "📉" if article["sentiment"] == "bearish" else "⚖️"
                # Add source attribution for each article
                source_tag = ""
                if article.get("source") == "perplexity_sonar":
                    source_tag = " 🔍"
                elif article.get("source") == "yahoo_finance":
                    source_tag = " 📊"

                response += f"{i}. {sentiment_emoji} **{article['title']}**{source_tag}\n"
                response += f"   - Publisher: {article['publisher']}\n"
                response += f"   - Impact Score: {article['impact_score']:.3f}\n"
                response += f"   - Date: {article.get('date', article.get('published_date', 'Unknown'))}\n"

                # Add Sonar-specific metrics if available
                if article.get("source") == "perplexity_sonar":
                    if article.get("relevance_score"):
                        response += f"   - Relevance: {article['relevance_score']:.2f}\n"
                    if article.get("content_type"):
                        response += f"   - Content Type: {article['content_type'].title()}\n"
                    if article.get("sonar_boost"):
                        response += f"   - Sonar Enhancement: {article['sonar_boost']:.2f}x\n"

                response += f"   - URL: {article['url']}\n\n"
        else:
            response += "No high-impact articles identified.\n"

        # Add data quality and methodology notes
        response += "\n## 📋 Analysis Methodology\n"
        response += "- **Sentiment Scoring**: Multi-factor analysis including keyword sentiment, source credibility, and recency\n"
        response += "- **Impact Calculation**: Weighted by publisher credibility, article recency, and sentiment strength\n"
        response += f"- **Confidence Metric**: Based on sample size ({article_count} articles) and sentiment consistency\n"

        if sonar_articles:
            response += f"- **Sonar Enhancement**: {len(sonar_articles)} articles with relevance scoring and content type analysis\n"

        if sonar_fallback_used:
            response += "\n⚠️ **Note**: Perplexity Sonar integration encountered issues; analysis based on Yahoo Finance data only.\n"

        # Add disclaimer
        response += "\n---\n"
        response += "*This analysis is for informational purposes only and should not be considered as investment advice. "
        response += "Market sentiment can change rapidly, and past sentiment does not predict future performance.*\n"

        return response.strip()

    def format_no_data_response(self, ticker: str, asset_type: str) -> str:
        """Format response when no news data is available."""
        return f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## ⚠️ No Data Available

Unfortunately, no recent news articles were found for {ticker}. This could be due to:

- Limited news coverage for this {asset_type}
- Temporary data source issues
- Invalid or delisted ticker symbol

Please verify the ticker symbol and try again later.
"""

    def format_no_recent_news_response(self, ticker: str, asset_type: str, days_back: int) -> str:
        """Format response when no recent news is available."""
        return f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## ⚠️ No Recent News Found

No news articles were found for {ticker} within the last {days_back} days.

**Suggestions:**
- Try increasing the time range (days_back parameter)
- Check if this is an actively traded {asset_type}
- Verify the ticker symbol is correct

**Alternative Analysis:**
- Consider analyzing related sector ETFs or major holdings
- Look for broader market sentiment affecting this asset class
"""

    def format_error_response(self, ticker: str, asset_type: str, error_message: str) -> str:
        """Format error response for sentiment analysis failures."""
        return f"""
# Enhanced Sentiment Analysis Error for {ticker} ({asset_type.upper()})

## ❌ Analysis Failed

An error occurred while performing sentiment analysis:

**Error Details:** {error_message}

**Troubleshooting:**
- Verify the ticker symbol is valid
- Check your internet connection
- Try again in a few minutes
- Contact support if the issue persists

**Alternative Options:**
- Try analyzing a related asset or sector ETF
- Use a different time range or article limit
- Check manual news sources for this asset
"""

    def format_limited_data_response(
        self,
        ticker: str,
        asset_type: str,
        sentiment_analysis: dict,
        article_count: int,
        warning_message: str = "",
    ) -> str:
        """Format response when data is limited but some analysis is possible."""
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        score = sentiment_analysis.get("sentiment_score", 0.0)
        confidence = sentiment_analysis.get("confidence", 0.0)

        response = f"""
# Enhanced Sentiment Analysis for {ticker} ({asset_type.upper()})

## ⚠️ Limited Data Analysis

**Warning:** {warning_message or f"Only {article_count} articles found - results may be less reliable."}

## 📊 Preliminary Sentiment
- **Overall Sentiment**: {sentiment.title()} ({score:+.4f})
- **Confidence Level**: {confidence:.1%} (Low due to limited data)
- **Articles Analyzed**: {article_count}

## 💡 Recommendations
- Results should be interpreted with caution due to limited sample size
- Consider expanding the time range or checking multiple sources
- Look for additional context from sector or market-wide sentiment
- Monitor for additional news coverage before making decisions

---
*This analysis is based on limited data and should be supplemented with additional research.*
"""
        return response.strip()

    def format_source_attribution(self, data_sources: list[str], article_counts: dict[str, int]) -> str:
        """Format source attribution information."""
        if not data_sources:
            return ""

        attribution = "**Data Sources:**\n"
        for source in data_sources:
            count = article_counts.get(source.lower().replace(" ", "_"), 0)
            attribution += f"- {source}: {count} articles\n"

        return attribution

    def format_confidence_explanation(self, confidence: float, article_count: int, consistency_score: float = 0.0) -> str:
        """Format explanation of confidence score."""
        explanation = f"**Confidence Score: {confidence:.1%}**\n\n"

        if confidence >= 0.8:
            explanation += "🟢 **High Confidence** - Strong agreement across multiple sources with sufficient sample size.\n"
        elif confidence >= 0.6:
            explanation += "🟡 **Medium Confidence** - Moderate agreement with reasonable sample size.\n"
        elif confidence >= 0.4:
            explanation += "🟠 **Low Confidence** - Limited agreement or small sample size.\n"
        else:
            explanation += "🔴 **Very Low Confidence** - Conflicting signals or very limited data.\n"

        explanation += f"\n*Based on {article_count} articles with sentiment consistency score of {consistency_score:.2f}*\n"

        return explanation

    def format_trending_topics_detailed(self, trending_topics: list[dict]) -> str:
        """Format detailed trending topics analysis."""
        if not trending_topics:
            return "No significant trending topics identified in current news cycle.\n"

        response = "## 🔥 Detailed Topic Analysis\n\n"

        for i, topic in enumerate(trending_topics, 1):
            response += f"### {i}. {topic['topic']}\n"
            # Use correct field names from sentiment_calculations.py
            count = topic.get("mention_count", topic.get("article_count", 0))
            relevance = topic.get("relevance_score", topic.get("average_relevance", 0.0))
            response += f"- **Mentions**: {count} articles\n"
            response += f"- **Relevance**: {relevance:.2f}/1.0\n"

            if "sample_articles" in topic:
                response += "- **Sample Headlines**:\n"
                for article in topic["sample_articles"][:2]:
                    response += f'  - "{article["title"]}" ({article["publisher"]})\n'

            response += "\n"

        return response

    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji representation for sentiment."""
        emoji_map = {
            "positive": "📈",
            "bullish": "📈",
            "negative": "📉",
            "bearish": "📉",
            "neutral": "⚖️",
        }
        return emoji_map.get(sentiment.lower(), "⚖️")

    def format_impact_score_explanation(self, impact_score: float) -> str:
        """Format explanation of impact score."""
        if impact_score >= 0.8:
            return "🔴 Very High Impact"
        elif impact_score >= 0.6:
            return "🟠 High Impact"
        elif impact_score >= 0.4:
            return "🟡 Medium Impact"
        elif impact_score >= 0.2:
            return "🟢 Low Impact"
        else:
            return "⚪ Minimal Impact"
