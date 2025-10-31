"""
Sentiment calculation utilities for enhanced sentiment analysis.

This module contains the core sentiment analysis algorithms, impact scoring,
and trending topic extraction logic.
"""

import datetime

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SentimentCalculator:
    """Handles sentiment calculations and analysis algorithms."""

    def __init__(self) -> None:
        """Initialize sentiment calculator."""
        self.logger = logger

    def analyze_sentiment(self, news_data: list[dict], ticker: str, asset_type: str) -> dict:
        """
        Analyze sentiment using n8n workflow logic.

        Implements weighted sentiment scoring with:
        - Source reliability weighting
        - Recency weighting
        - Asset-specific adjustments
        - Confidence scoring

        Args:
            news_data: List of news articles
            ticker: Asset ticker symbol
            asset_type: Type of asset (stock, etf, crypto)

        Returns:
            Dictionary with sentiment analysis results

        """
        if not news_data:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "positive_ratio": 0.0,
                "negative_ratio": 0.0,
                "neutral_ratio": 0.0,
                "total_articles": 0,
                "weighted_score": 0.0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
            }

        # Initialize sentiment counters
        sentiment_scores = []
        sentiment_weights = []
        sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}

        for article in news_data:
            # Extract sentiment indicators from title and summary
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            content = f"{title} {summary}"

            # Calculate base sentiment score
            sentiment_score = self._calculate_base_sentiment(content)

            # Apply source weighting
            source_weight = self._get_source_weight(article.get("publisher", ""))

            # Apply recency weighting
            recency_weight = self.calculate_recency_factor(article.get("providerPublishTime"))

            # Apply asset-specific adjustments
            adjusted_score = self._apply_asset_adjustments(sentiment_score, asset_type, content)

            # Calculate final weighted score
            final_weight = source_weight * recency_weight
            weighted_score = adjusted_score * final_weight

            sentiment_scores.append(weighted_score)
            sentiment_weights.append(final_weight)

            # Update distribution
            if adjusted_score > 0.1:
                sentiment_distribution["positive"] += 1
            elif adjusted_score < -0.1:
                sentiment_distribution["negative"] += 1
            else:
                sentiment_distribution["neutral"] += 1

        # Calculate overall metrics
        total_articles = len(news_data)
        if total_articles == 0:
            return self._get_empty_sentiment_result()

        # Weighted average sentiment
        total_weight = sum(sentiment_weights)
        if total_weight > 0:
            overall_score = sum(sentiment_scores) / total_weight
        else:
            overall_score = sum(sentiment_scores) / len(sentiment_scores)

        # Calculate confidence based on article count and score consistency
        confidence = self._calculate_confidence(sentiment_scores, total_articles)

        # Determine overall sentiment category
        if overall_score > 0.15:
            overall_sentiment = "positive"
        elif overall_score < -0.15:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"

        # Calculate ratios
        positive_ratio = sentiment_distribution["positive"] / total_articles
        negative_ratio = sentiment_distribution["negative"] / total_articles
        neutral_ratio = sentiment_distribution["neutral"] / total_articles

        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(overall_score, 3),
            "confidence": round(confidence, 3),
            "positive_ratio": round(positive_ratio, 3),
            "negative_ratio": round(negative_ratio, 3),
            "neutral_ratio": round(neutral_ratio, 3),
            "total_articles": total_articles,
            "weighted_score": round(overall_score, 3),
            "sentiment_distribution": sentiment_distribution,
        }

    def _calculate_base_sentiment(self, content: str) -> float:
        """Calculate base sentiment score from content."""
        # Positive indicators
        positive_words = [
            "bullish",
            "buy",
            "strong",
            "growth",
            "profit",
            "gain",
            "rise",
            "surge",
            "rally",
            "outperform",
            "upgrade",
            "beat",
            "exceed",
            "positive",
            "optimistic",
            "confident",
            "breakthrough",
            "innovation",
            "expansion",
            "success",
            "record",
            "high",
            "soar",
        ]

        # Negative indicators
        negative_words = [
            "bearish",
            "sell",
            "weak",
            "decline",
            "loss",
            "fall",
            "drop",
            "crash",
            "plunge",
            "underperform",
            "downgrade",
            "miss",
            "disappoint",
            "negative",
            "pessimistic",
            "concern",
            "risk",
            "warning",
            "cut",
            "reduce",
            "low",
            "worst",
            "struggle",
            "challenge",
        ]

        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)

        # Calculate base score
        total_words = len(content.split())
        if total_words == 0:
            return 0.0

        positive_ratio = positive_count / max(total_words, 1)
        negative_ratio = negative_count / max(total_words, 1)

        # Normalize to [-1, 1] range
        base_score = (positive_ratio - negative_ratio) * 10
        return max(-1.0, min(1.0, base_score))

    def _get_source_weight(self, publisher: str) -> float:
        """Get reliability weight for news source."""
        if not publisher:
            return 0.5

        publisher_lower = publisher.lower()

        # High reliability sources
        high_reliability = [
            "reuters",
            "bloomberg",
            "wall street journal",
            "financial times",
            "cnbc",
            "marketwatch",
            "yahoo finance",
            "seeking alpha",
            "barron's",
            "forbes",
        ]

        # Medium reliability sources
        medium_reliability = [
            "cnn",
            "bbc",
            "associated press",
            "npr",
            "usa today",
            "washington post",
            "new york times",
            "guardian",
            "axios",
            "politico",
        ]

        # Check for high reliability
        for source in high_reliability:
            if source in publisher_lower:
                return 1.0

        # Check for medium reliability
        for source in medium_reliability:
            if source in publisher_lower:
                return 0.8

        # Default weight for unknown sources
        return 0.6

    def calculate_recency_factor(self, published_time: float | None) -> float:
        """Calculate recency factor for impact scoring with time decay."""
        if published_time is None:
            return 0.5

        try:
            # Convert timestamp to datetime
            if published_time > 1e10:  # Milliseconds
                published_time = published_time / 1000

            published_date = datetime.datetime.fromtimestamp(published_time)
            current_date = datetime.datetime.now()

            # Calculate hours since publication
            time_diff = current_date - published_date
            hours_since = time_diff.total_seconds() / 3600

            # Apply exponential decay (half-life of 24 hours)
            if hours_since <= 0:
                return 1.0
            elif hours_since <= 6:
                return 1.0  # Full weight for first 6 hours
            elif hours_since <= 24:
                return 0.9  # High weight for first day
            elif hours_since <= 72:
                return 0.7  # Medium weight for first 3 days
            elif hours_since <= 168:  # 1 week
                return 0.5  # Lower weight for first week
            else:
                return 0.3  # Minimal weight for older news

        except (ValueError, OSError, OverflowError):
            return 0.8  # Default for invalid timestamps

    def _apply_asset_adjustments(self, sentiment_score: float, asset_type: str, content: str) -> float:
        """Apply asset-specific sentiment adjustments."""
        adjusted_score = sentiment_score

        if asset_type == "crypto":
            # Crypto is more volatile, amplify sentiment
            crypto_keywords = ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "nft"]
            if any(keyword in content for keyword in crypto_keywords):
                adjusted_score *= 1.2

        elif asset_type == "etf":
            # ETFs are more stable, dampen extreme sentiment
            adjusted_score *= 0.8

        # Clamp to [-1, 1] range
        return max(-1.0, min(1.0, adjusted_score))

    def _calculate_confidence(self, sentiment_scores: list[float], total_articles: int) -> float:
        """Calculate confidence score based on consistency and sample size."""
        if not sentiment_scores or total_articles == 0:
            return 0.0

        # Base confidence from sample size
        size_confidence = min(1.0, total_articles / 20.0)  # Max confidence at 20+ articles

        # Consistency confidence (lower variance = higher confidence)
        if len(sentiment_scores) > 1:
            mean_score = sum(sentiment_scores) / len(sentiment_scores)
            variance = sum((score - mean_score) ** 2 for score in sentiment_scores) / len(sentiment_scores)
            consistency_confidence = max(0.0, 1.0 - variance)
        else:
            consistency_confidence = 0.5

        # Combined confidence
        return (size_confidence + consistency_confidence) / 2

    def _get_empty_sentiment_result(self) -> dict:
        """Get empty sentiment result structure."""
        return {
            "overall_sentiment": "neutral",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "neutral_ratio": 0.0,
            "total_articles": 0,
            "weighted_score": 0.0,
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
        }

    def extract_trending_topics(self, news_data: list[dict]) -> list[dict]:
        """Extract trending topics from news articles."""
        if not news_data:
            return []

        # Keywords to track
        topic_keywords = {
            "earnings": ["earnings", "revenue", "profit", "eps", "guidance", "results"],
            "merger_acquisition": ["merger", "acquisition", "buyout", "takeover", "deal"],
            "regulation": ["regulation", "regulatory", "sec", "fda", "government", "policy"],
            "technology": ["ai", "artificial intelligence", "tech", "innovation", "digital"],
            "market_trends": ["market", "trend", "sector", "industry", "economic"],
            "financial_performance": ["performance", "growth", "decline", "forecast", "outlook"],
            "leadership": ["ceo", "executive", "management", "leadership", "appointment"],
            "product_launch": ["launch", "product", "service", "release", "announcement"],
            "partnership": ["partnership", "collaboration", "alliance", "joint venture"],
            "investment": ["investment", "funding", "capital", "ipo", "valuation"],
        }

        # Count topic occurrences
        topic_counts = {}
        topic_articles = {}

        for article in news_data:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            content = f"{title} {summary}"

            for topic, keywords in topic_keywords.items():
                for keyword in keywords:
                    if keyword in content:
                        topic_counts[topic] = topic_counts.get(topic, 0) + 1
                        if topic not in topic_articles:
                            topic_articles[topic] = []
                        topic_articles[topic].append(article)
                        break  # Count each article only once per topic

        # Create trending topics list
        trending_topics = []
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
            if count >= 2:  # Only include topics with at least 2 mentions
                trending_topics.append(
                    {
                        "topic": topic.replace("_", " ").title(),
                        "mention_count": count,
                        "relevance_score": round(count / len(news_data), 3),
                        "sample_articles": [
                            {
                                "title": article.get("title", ""),
                                "publisher": article.get("publisher", ""),
                            }
                            for article in topic_articles[topic][:2]  # Include 2 sample articles
                        ],
                    }
                )

        return trending_topics[:5]  # Return top 5 topics

    def calculate_impact_scores(self, news_data: list[dict], sentiment_analysis: dict) -> list[dict]:
        """Calculate enhanced impact scores for articles including Sonar data."""
        if not news_data:
            return []

        impact_articles = []

        for article in news_data:
            # Base impact factors
            title_length = len(article.get("title", ""))
            has_summary = bool(article.get("summary", ""))

            # Source credibility (reuse from sentiment analysis)
            source_weight = self._get_source_weight(article.get("publisher", ""))

            # Recency factor
            recency_factor = self.calculate_recency_factor(article.get("providerPublishTime"))

            # Sentiment strength (absolute value)
            content = f"{article.get('title', '')} {article.get('summary', '')}".lower()
            sentiment_strength = abs(self._calculate_base_sentiment(content))

            # Calculate composite impact score
            impact_score = (
                (title_length / 100) * 0.2  # Title informativeness
                + (1.0 if has_summary else 0.5) * 0.2  # Content completeness
                + source_weight * 0.3  # Source credibility
                + recency_factor * 0.2  # Recency
                + sentiment_strength * 0.1  # Sentiment strength
            )

            # Normalize to 0-1 range
            impact_score = min(1.0, max(0.0, impact_score))

            # Add to results
            impact_articles.append(
                {
                    "title": article.get("title", ""),
                    "publisher": article.get("publisher", ""),
                    "published_date": self.format_article_date(article.get("providerPublishTime")),
                    "impact_score": round(impact_score, 3),
                    "url": article.get("link", ""),
                    "summary": (article.get("summary", "")[:200] + "..." if len(article.get("summary", "")) > 200 else article.get("summary", "")),
                }
            )

        # Sort by impact score
        impact_articles.sort(key=lambda x: x["impact_score"], reverse=True)

        return impact_articles[:10]  # Return top 10 impactful articles

    def format_article_date(self, timestamp: float | None) -> str:
        """Format article timestamp to readable date."""
        if timestamp is None:
            return "Unknown date"

        try:
            if timestamp > 1e10:  # Milliseconds
                timestamp = timestamp / 1000

            date = datetime.datetime.fromtimestamp(timestamp)
            return date.strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError, OverflowError):
            return "Unknown date"

    def generate_market_outlook(self, sentiment_analysis: dict, trending_topics: list[dict], asset_type: str) -> str:
        """Generate market outlook based on sentiment and topics."""
        sentiment = sentiment_analysis.get("overall_sentiment", "neutral")
        confidence = sentiment_analysis.get("confidence", 0.0)

        # Base outlook based on sentiment
        if sentiment == "positive" and confidence > 0.7:
            outlook = f"Strong positive sentiment detected with high confidence. Market conditions appear favorable for {asset_type} investments."
        elif sentiment == "positive":
            outlook = f"Moderate positive sentiment observed. {asset_type.title()} shows promising signals but with some uncertainty."
        elif sentiment == "negative" and confidence > 0.7:
            outlook = f"Strong negative sentiment with high confidence. Caution advised for {asset_type} positions."
        elif sentiment == "negative":
            outlook = f"Moderate negative sentiment detected. {asset_type.title()} faces some headwinds but situation remains fluid."
        else:
            outlook = f"Neutral sentiment prevails. {asset_type.title()} market appears to be in a wait-and-see mode."

        # Add trending topics context
        if trending_topics:
            top_topic = trending_topics[0]["topic"]
            outlook += f" Key focus area: {top_topic} is driving current market discussions."

        return outlook
