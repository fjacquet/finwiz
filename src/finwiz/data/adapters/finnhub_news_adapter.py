"""Finnhub news adapter with waterfall fallback (Finnhub -> gnews -> RSS).

Uses Finnhub pre-computed sentiment when available, falls back to VADER
for articles from secondary sources (gnews, RSS).
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from typing import Literal

from finwiz.config.endpoints import FINNHUB_BASE
from finwiz.data.news_utils import (
    calculate_weighted_sentiment,
    deduplicate_articles,
    get_source_reliability,
)
from finwiz.schemas.sentiment import NewsArticle, NewsSentimentResult
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Minimum article counts before cascading to next source
_MIN_FINNHUB_ARTICLES = 5
_MIN_TOTAL_ARTICLES = 3


def _content_hash(title: str, summary: str) -> str:
    """Generate a content hash for deduplication."""
    text = f"{title.lower().strip()}|{summary.lower().strip()}"
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _sentiment_to_label(score: float) -> Literal["bullish", "bearish", "neutral"]:
    """Convert numeric sentiment score to label."""
    if score > 0.05:
        return "bullish"
    if score < -0.05:
        return "bearish"
    return "neutral"


class FinnhubNewsAdapter:
    """News adapter with waterfall fallback: Finnhub -> gnews -> RSS.

    Does NOT extend BaseDataAdapter (which is for fundamental data).
    """

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.finnhub_key: str | None = os.getenv("FINNHUB_API_KEY")
        self.gnews_key: str | None = os.getenv("GNEWS_API_KEY")

    def is_available(self) -> bool:
        """At least RSS is always available."""
        return True

    def get_news_sentiment(self, ticker: str, days: int = 7) -> NewsSentimentResult:
        """Get news with waterfall: Finnhub -> gnews -> RSS."""
        articles: list[NewsArticle] = []

        # Level 1: Finnhub (has pre-computed sentiment)
        # Per-source failures are expected steps in the waterfall (the next level
        # picks up the slack), so they log at DEBUG, not WARNING.
        if self.finnhub_key:
            try:
                articles.extend(self._fetch_finnhub(ticker, days))
            except Exception as e:
                logger.debug(f"Finnhub failed for {ticker}: {e}")

        # Level 2: gnews (needs VADER sentiment)
        if len(articles) < _MIN_FINNHUB_ARTICLES and self.gnews_key:
            try:
                articles.extend(self._fetch_gnews(ticker, days))
            except Exception as e:
                logger.debug(f"gnews failed for {ticker}: {e}")

        # Level 3: RSS (needs VADER sentiment)
        if len(articles) < _MIN_TOTAL_ARTICLES:
            try:
                articles.extend(self._fetch_rss(ticker))
            except Exception as e:
                logger.debug(f"RSS failed for {ticker}: {e}")

        # Apply VADER to articles without sentiment
        articles = self._apply_vader_fallback(articles)

        # Apply source reliability weights
        for article in articles:
            article.source_reliability = get_source_reliability(article.source)

        # Deduplicate
        articles = deduplicate_articles(articles)

        return self._build_result(ticker, articles)

    def _fetch_finnhub(self, ticker: str, days: int) -> list[NewsArticle]:
        """Fetch from Finnhub API with pre-computed sentiment."""
        import finnhub

        client = finnhub.Client(api_key=self.finnhub_key)
        end = datetime.now(tz=UTC)
        start = end - timedelta(days=days)

        news = client.company_news(
            ticker,
            _from=start.strftime("%Y-%m-%d"),
            to=end.strftime("%Y-%m-%d"),
        )

        articles: list[NewsArticle] = []
        for item in news or []:
            title = item.get("headline", "")
            summary = item.get("summary", "")
            if not title:
                continue

            # Finnhub sentiment: mspr field (normalized -1 to +1 in API response)
            sentiment_score: float | None = None
            sentiment_label: Literal["bullish", "bearish", "neutral"] | None = None
            if item.get("sentiment"):
                sentiment_score = max(-1.0, min(1.0, float(item["sentiment"])))
                sentiment_label = _sentiment_to_label(sentiment_score)

            published_ts = item.get("datetime", 0)
            published_at = datetime.fromtimestamp(published_ts, tz=UTC) if published_ts else datetime.now(tz=UTC)

            articles.append(
                NewsArticle(
                    title=title[:500],
                    url=item.get("url", f"{FINNHUB_BASE}/news/{ticker}"),
                    source="finnhub",
                    published_at=published_at,
                    summary=summary[:2000],
                    ticker=ticker,
                    sentiment_score=sentiment_score,
                    sentiment_label=sentiment_label,
                    content_hash=_content_hash(title, summary),
                )
            )
        logger.info(f"Finnhub returned {len(articles)} articles for {ticker}")
        return articles

    def _fetch_gnews(self, ticker: str, days: int) -> list[NewsArticle]:
        """Fetch from gnews API. No built-in sentiment -- needs VADER."""
        from gnews import GNews

        google_news = GNews(
            language="en",
            country="US",
            max_results=10,
            period=f"{days}d",
        )

        results = google_news.get_news(f"{ticker} stock")
        articles: list[NewsArticle] = []
        for item in results or []:
            title = item.get("title", "")
            if not title:
                continue

            published_str = item.get("published date", "")
            try:
                published_at = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=UTC)
            except (ValueError, TypeError):
                published_at = datetime.now(tz=UTC)

            summary = item.get("description", "")
            articles.append(
                NewsArticle(
                    title=title[:500],
                    url=item.get("url", ""),
                    source="gnews",
                    published_at=published_at,
                    summary=(summary or "")[:2000],
                    ticker=ticker,
                    content_hash=_content_hash(title, summary or ""),
                )
            )
        logger.info(f"gnews returned {len(articles)} articles for {ticker}")
        return articles

    def _fetch_rss(self, ticker: str) -> list[NewsArticle]:
        """Fetch from Yahoo Finance RSS feed. No sentiment -- needs VADER."""
        import feedparser

        feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        feed = feedparser.parse(feed_url)

        articles: list[NewsArticle] = []
        for entry in feed.entries[:10]:
            title = entry.get("title", "")
            if not title:
                continue

            summary = entry.get("summary", "")
            published_str = entry.get("published", "")
            try:
                from email.utils import parsedate_to_datetime

                published_at = parsedate_to_datetime(published_str).replace(tzinfo=UTC)
            except (ValueError, TypeError):
                published_at = datetime.now(tz=UTC)

            articles.append(
                NewsArticle(
                    title=title[:500],
                    url=entry.get("link", ""),
                    source="rss",
                    published_at=published_at,
                    summary=(summary or "")[:2000],
                    ticker=ticker,
                    content_hash=_content_hash(title, summary or ""),
                )
            )
        logger.info(f"RSS returned {len(articles)} articles for {ticker}")
        return articles

    def _apply_vader_fallback(self, articles: list[NewsArticle]) -> list[NewsArticle]:
        """Apply VADER sentiment to articles missing sentiment_score."""
        needs_vader = [a for a in articles if a.sentiment_score is None]
        if not needs_vader:
            return articles

        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        analyzer = SentimentIntensityAnalyzer()
        for article in needs_vader:
            text = f"{article.title}. {article.summary}".strip()
            scores = analyzer.polarity_scores(text)
            article.sentiment_score = max(-1.0, min(1.0, scores["compound"]))
            article.sentiment_label = _sentiment_to_label(scores["compound"])
        return articles

    def _build_result(self, ticker: str, articles: list[NewsArticle]) -> NewsSentimentResult:
        """Build aggregated sentiment result from articles."""
        scored = [a for a in articles if a.sentiment_score is not None]

        bullish = sum(1 for a in scored if a.sentiment_label == "bullish")
        bearish = sum(1 for a in scored if a.sentiment_label == "bearish")
        neutral = sum(1 for a in scored if a.sentiment_label == "neutral")

        # Source breakdown
        source_breakdown: dict[str, int] = {}
        for a in articles:
            source_breakdown[a.source] = source_breakdown.get(a.source, 0) + 1

        # Aggregate sentiment (simple average)
        aggregate = 0.0
        if scored:
            aggregate = sum(a.sentiment_score for a in scored if a.sentiment_score is not None) / len(scored)

        # Data freshness
        freshness_hours = 0.0
        if articles:
            newest = max(a.published_at for a in articles)
            freshness_hours = (datetime.now(tz=newest.tzinfo) - newest).total_seconds() / 3600

        return NewsSentimentResult(
            ticker=ticker,
            articles=articles,
            aggregate_sentiment=max(-1.0, min(1.0, aggregate)),
            weighted_sentiment=max(-1.0, min(1.0, calculate_weighted_sentiment(articles))),
            article_count=len(articles),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            source_breakdown=source_breakdown,
            data_freshness_hours=max(0.0, freshness_hours),
        )
