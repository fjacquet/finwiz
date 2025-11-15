"""
Sentiment aggregation utilities for multi-source sentiment analysis.

This module provides functions for extracting trending topics, aggregating articles,
and processing sentiment data from multiple sources.
"""

from __future__ import annotations

import datetime
from typing import Any

from finwiz.schemas.stock import SentimentItem
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class SentimentAggregators:
    """Utilities for aggregating and processing sentiment data from multiple sources."""

    def __init__(self, topic_keywords: dict[str, list[str]]) -> None:
        """
        Initialize sentiment aggregators with topic keywords.

        Args:
            topic_keywords: Dictionary mapping topic names to keyword lists
        """
        self.topic_keywords = topic_keywords

    def extract_trending_topics(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Extract trending topics from articles.

        Args:
            articles: List of article dictionaries with title and summary

        Returns:
            List of trending topic dictionaries sorted by relevance
        """
        if not articles:
            return []

        topic_counts = {}
        topic_relevance = {}

        for article in articles:
            title = article.get("title", "").lower()
            summary = article.get("summary", "").lower()
            text = f"{title} {summary}"

            for topic, keywords in self.topic_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in text)
                if matches > 0:
                    if topic not in topic_counts:
                        topic_counts[topic] = 0
                        topic_relevance[topic] = []

                    topic_counts[topic] += 1
                    topic_relevance[topic].append(matches / len(keywords))

        # Create trending topics
        trending_topics = []
        for topic, count in topic_counts.items():
            if count >= 2:  # Only include topics mentioned in multiple articles
                avg_relevance = sum(topic_relevance[topic]) / len(topic_relevance[topic])
                trending_topics.append(
                    {
                        "topic": topic.replace("_", " ").title(),
                        "article_count": count,
                        "relevance_score": round(avg_relevance, 3),
                        "keywords": self.topic_keywords[topic][:3],  # Top 3 keywords
                    }
                )

        # Sort by relevance and article count
        trending_topics.sort(key=lambda x: (x["relevance_score"], x["article_count"]), reverse=True)
        return trending_topics[:5]

    def get_top_articles(self, articles: list[dict[str, Any]]) -> tuple[list[SentimentItem], list[SentimentItem]]:
        """
        Get top positive and negative articles from a list.

        Args:
            articles: List of article dictionaries with sentiment_score

        Returns:
            Tuple of (top_positive_articles, top_negative_articles)
        """
        if not articles:
            return [], []

        # Sort articles by sentiment score
        sorted_articles = sorted(articles, key=lambda x: x.get("sentiment_score", 0))

        # Get top negative (most negative scores)
        top_negative = []
        for article in sorted_articles[:5]:
            if article.get("sentiment_score", 0) < -0.1:
                try:
                    # Parse datetime
                    published_time = article.get("published_time", "")
                    if published_time:
                        if isinstance(published_time, str):
                            # Try to parse ISO format or timestamp
                            try:
                                dt = datetime.datetime.fromisoformat(published_time.replace("Z", "+00:00"))
                            except ValueError:
                                dt = datetime.datetime.now()
                        else:
                            dt = datetime.datetime.fromtimestamp(published_time)
                    else:
                        dt = datetime.datetime.now()

                    top_negative.append(
                        SentimentItem(
                            headline=article.get("title", "")[:200],  # Limit length
                            url=article.get("url", ""),
                            date=dt,
                            score=article.get("sentiment_score", 0),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error creating SentimentItem: {e}")
                    continue

        # Get top positive (most positive scores)
        top_positive = []
        for article in reversed(sorted_articles[-5:]):
            if article.get("sentiment_score", 0) > 0.1:
                try:
                    # Parse datetime
                    published_time = article.get("published_time", "")
                    if published_time:
                        if isinstance(published_time, str):
                            try:
                                dt = datetime.datetime.fromisoformat(published_time.replace("Z", "+00:00"))
                            except ValueError:
                                dt = datetime.datetime.now()
                        else:
                            dt = datetime.datetime.fromtimestamp(published_time)
                    else:
                        dt = datetime.datetime.now()

                    top_positive.append(
                        SentimentItem(
                            headline=article.get("title", "")[:200],  # Limit length
                            url=article.get("url", ""),
                            date=dt,
                            score=article.get("sentiment_score", 0),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Error creating SentimentItem: {e}")
                    continue

        return top_positive, top_negative
