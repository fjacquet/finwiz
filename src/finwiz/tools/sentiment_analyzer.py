"""
Multi-Source Sentiment Analysis Tool.

This module provides comprehensive sentiment analysis by integrating multiple data sources
including Alpha Vantage, Yahoo Finance, and CoinMarketCap to provide weighted sentiment
scoring, trending topic extraction, and relevance scoring.
"""

from __future__ import annotations

import asyncio
import datetime
import os
import re
from typing import Any

import aiohttp
import yfinance as yf  # yfinance has no official type stubs
from pydantic import BaseModel, ConfigDict, Field

from finwiz.config.endpoints import ALPHA_VANTAGE_BASE, CMC_BASE
from finwiz.schemas.stock import MarketSentiment, SentimentItem
from finwiz.tools.logger import get_logger
from finwiz.tools.sentiment.sentiment_aggregators import SentimentAggregators
from finwiz.tools.sentiment.sentiment_calculators import SentimentCalculators

logger = get_logger(__name__)


class TrendingTopic(BaseModel):
    """Model for trending topics extracted from news articles."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    topic: str = Field(..., description="The trending topic name")
    article_count: int = Field(..., ge=0, description="Number of articles mentioning this topic")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score for the topic")
    keywords: list[str] = Field(default_factory=list, description="Keywords associated with this topic")


class SentimentSource(BaseModel):
    """Model for sentiment data from a specific source."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source: str = Field(..., description="Name of the data source")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from this source")
    article_count: int = Field(..., ge=0, description="Number of articles analyzed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the sentiment score")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of this source in final calculation")


class SentimentAnalysisResult(BaseModel):
    """Comprehensive sentiment analysis result."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    ticker: str = Field(..., description="The analyzed ticker symbol")
    overall_sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Weighted overall sentiment")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the analysis")
    total_articles: int = Field(..., ge=0, description="Total number of articles analyzed")
    sources: list[SentimentSource] = Field(default_factory=list, description="Individual source results")
    trending_topics: list[TrendingTopic] = Field(default_factory=list, description="Extracted trending topics")
    top_positive_articles: list[SentimentItem] = Field(default_factory=list, description="Most positive articles")
    top_negative_articles: list[SentimentItem] = Field(default_factory=list, description="Most negative articles")
    analysis_timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)


class SentimentAnalyzer:
    """
    Multi-source sentiment analyzer that integrates Alpha Vantage, Yahoo Finance, and CoinMarketCap.

    This class provides comprehensive sentiment analysis by:
    - Fetching news from multiple sources
    - Performing weighted sentiment scoring
    - Extracting trending topics with relevance scoring
    - Providing confidence metrics
    """

    def __init__(self) -> None:
        """Initialize the sentiment analyzer with API configurations."""
        self.alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        self.coinmarketcap_api_key = os.getenv("X-CMC_PRO_API_KEY")

        # Source weights for final sentiment calculation
        self.source_weights = {"alpha_vantage": 0.4, "yahoo_finance": 0.35, "coinmarketcap": 0.25}

        # Sentiment keywords for basic analysis
        self.bullish_keywords = [
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
            "outperform",
            "momentum",
            "breakthrough",
            "expansion",
            "success",
        ]

        self.bearish_keywords = [
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
            "underperform",
            "struggle",
            "challenge",
            "warning",
            "cut",
        ]

        # Topic keywords for trending topic extraction
        self.topic_keywords = {
            "earnings": ["earnings", "profit", "revenue", "eps", "quarterly", "results"],
            "merger_acquisition": ["merger", "acquisition", "buyout", "takeover", "deal"],
            "regulation": ["regulation", "regulatory", "sec", "compliance", "policy", "legal"],
            "market_trends": ["market", "sector", "industry", "trend", "outlook", "forecast"],
            "technology": ["technology", "ai", "digital", "innovation", "tech", "software"],
            "financial_results": ["results", "performance", "guidance", "forecast", "outlook"],
            "leadership": ["ceo", "management", "leadership", "executive", "board", "director"],
            "product_launch": ["launch", "product", "service", "announcement", "release", "unveil"],
            "partnerships": ["partnership", "collaboration", "alliance", "joint", "agreement"],
            "crypto_specific": ["blockchain", "defi", "nft", "mining", "staking", "protocol"],
        }

        # Initialize helper classes
        self.calculators = SentimentCalculators(self.bullish_keywords, self.bearish_keywords)
        self.aggregators = SentimentAggregators(self.topic_keywords)

    async def analyze_sentiment(self, ticker: str, days_back: int = 7, max_articles_per_source: int = 20) -> SentimentAnalysisResult:
        """
        Perform comprehensive multi-source sentiment analysis.

        Args:
            ticker: The ticker symbol to analyze
            days_back: Number of days to look back for news
            max_articles_per_source: Maximum articles to fetch per source

        Returns:
            Comprehensive sentiment analysis result

        """
        logger.info(f"Starting multi-source sentiment analysis for {ticker}")

        # Fetch data from all sources concurrently
        tasks = [
            self._fetch_alpha_vantage_sentiment(ticker, days_back, max_articles_per_source),
            self._fetch_yahoo_finance_sentiment(ticker, max_articles_per_source),
            self._fetch_coinmarketcap_sentiment(ticker, max_articles_per_source),
        ]

        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        valid_sources: list[dict[str, Any]] = []
        all_articles: list[dict[str, Any]] = []

        for i, result in enumerate(source_results):
            if isinstance(result, BaseException):
                logger.warning(f"Source {i} failed: {result}")
                continue
            if result:
                valid_sources.append(result)
                all_articles.extend(result.get("articles", []))

        if not valid_sources:
            logger.warning(f"No valid sentiment data sources for {ticker}")
            return self._create_empty_result(ticker)

        # Calculate weighted sentiment
        weighted_sentiment = self._calculate_weighted_sentiment(valid_sources)

        # Extract trending topics
        trending_topics = self._extract_trending_topics(all_articles)

        # Get top positive and negative articles
        top_positive, top_negative = self._get_top_articles(all_articles)

        # Calculate overall confidence
        confidence = self._calculate_confidence(valid_sources, len(all_articles))

        return SentimentAnalysisResult(
            ticker=ticker,
            overall_sentiment_score=weighted_sentiment,
            confidence_level=confidence,
            total_articles=len(all_articles),
            sources=[SentimentSource(**source) for source in valid_sources],
            trending_topics=trending_topics,
            top_positive_articles=top_positive,
            top_negative_articles=top_negative,
        )

    async def _fetch_alpha_vantage_sentiment(self, ticker: str, days_back: int, max_articles: int) -> dict[str, Any] | None:
        """Fetch sentiment data from Alpha Vantage."""
        if not self.alpha_vantage_api_key:
            logger.warning("Alpha Vantage API key not available")
            return None

        try:
            # Calculate time range
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=days_back)

            params: dict[str, str] = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "sort": "LATEST",
                "limit": str(max_articles),
                "time_from": start_time.strftime("%Y%m%dT%H%M"),
                "time_to": end_time.strftime("%Y%m%dT%H%M"),
                "apikey": self.alpha_vantage_api_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    ALPHA_VANTAGE_BASE,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        logger.error(f"Alpha Vantage API error: {response.status}")
                        return None

                    data = await response.json()

                    if "feed" not in data:
                        logger.warning("No Alpha Vantage news feed data")
                        return None

                    articles = []
                    sentiment_scores = []

                    for item in data["feed"]:
                        # Extract sentiment score for the specific ticker
                        ticker_sentiment = None
                        if "ticker_sentiment" in item:
                            for ts in item["ticker_sentiment"]:
                                if ts.get("ticker") == ticker:
                                    ticker_sentiment = float(ts.get("relevance_score", 0)) * float(ts.get("ticker_sentiment_score", 0))
                                    break

                        if ticker_sentiment is None:
                            ticker_sentiment = float(item.get("overall_sentiment_score", 0))

                        sentiment_scores.append(ticker_sentiment)

                        # Create article entry
                        articles.append(
                            {
                                "title": item.get("title", ""),
                                "summary": item.get("summary", ""),
                                "url": item.get("url", ""),
                                "published_time": item.get("time_published", ""),
                                "source": item.get("source", "Alpha Vantage"),
                                "sentiment_score": ticker_sentiment,
                            }
                        )

                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                    confidence = min(1.0, len(articles) / max_articles)

                    return {
                        "source": "alpha_vantage",
                        "sentiment_score": avg_sentiment,
                        "article_count": len(articles),
                        "confidence": confidence,
                        "weight": self.source_weights["alpha_vantage"],
                        "articles": articles,
                    }

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage sentiment: {e}")
            return None

    async def _fetch_yahoo_finance_sentiment(self, ticker: str, max_articles: int) -> dict[str, Any] | None:
        """Fetch sentiment data from Yahoo Finance."""
        try:
            # Use yfinance to get news (this is synchronous, but we'll run it in executor)
            loop = asyncio.get_event_loop()
            ticker_obj = await loop.run_in_executor(None, yf.Ticker, ticker)
            news = await loop.run_in_executor(None, lambda: ticker_obj.news)

            if not news:
                logger.warning(f"No Yahoo Finance news for {ticker}")
                return None

            # Limit articles
            news = news[:max_articles]

            articles = []
            sentiment_scores = []

            for item in news:
                title = item.get("title", "")
                summary = item.get("summary", "")

                # Calculate sentiment using keyword analysis
                sentiment_score = self._calculate_keyword_sentiment(f"{title} {summary}")
                sentiment_scores.append(sentiment_score)

                # Convert timestamp
                published_time = item.get("providerPublishTime")
                if published_time:
                    published_dt = datetime.datetime.fromtimestamp(published_time)
                else:
                    published_dt = datetime.datetime.now()

                articles.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": item.get("link", ""),
                        "published_time": published_dt.isoformat(),
                        "source": item.get("publisher", "Yahoo Finance"),
                        "sentiment_score": sentiment_score,
                    }
                )

            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            confidence = min(1.0, len(articles) / max_articles)

            return {
                "source": "yahoo_finance",
                "sentiment_score": avg_sentiment,
                "article_count": len(articles),
                "confidence": confidence,
                "weight": self.source_weights["yahoo_finance"],
                "articles": articles,
            }

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance sentiment: {e}")
            return None

    async def _fetch_coinmarketcap_sentiment(self, ticker: str, max_articles: int) -> dict[str, Any] | None:
        """Fetch sentiment data from CoinMarketCap (for crypto assets)."""
        if not self.coinmarketcap_api_key:
            logger.warning("CoinMarketCap API key not available")
            return None

        # Only use CoinMarketCap for crypto-like tickers
        if not self._is_crypto_ticker(ticker):
            return None

        try:
            headers = {"X-CMC_PRO_API_KEY": self.coinmarketcap_api_key, "Accept": "application/json"}

            # First get crypto ID
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{CMC_BASE}/cryptocurrency/map",
                    headers=headers,
                    params={"symbol": ticker.replace("-USD", "")},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        logger.error(f"CoinMarketCap map API error: {response.status}")
                        return None

                    data = await response.json()
                    if not data.get("data"):
                        return None

                    crypto_id = data["data"][0]["id"]

                # Get news for the crypto
                async with session.get(
                    f"{CMC_BASE}/content/latest",
                    headers=headers,
                    params={"cryptocurrencies": crypto_id, "limit": max_articles},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        logger.error(f"CoinMarketCap news API error: {response.status}")
                        return None

                    data = await response.json()
                    if not data.get("data"):
                        return None

                    articles = []
                    sentiment_scores = []

                    for item in data["data"]:
                        title = item.get("title", "")
                        description = item.get("description", "")

                        # Calculate sentiment using keyword analysis
                        sentiment_score = self._calculate_keyword_sentiment(f"{title} {description}")
                        sentiment_scores.append(sentiment_score)

                        articles.append(
                            {
                                "title": title,
                                "summary": description,
                                "url": item.get("url", ""),
                                "published_time": item.get("published_at", ""),
                                "source": item.get("source", "CoinMarketCap"),
                                "sentiment_score": sentiment_score,
                            }
                        )

                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
                    confidence = min(1.0, len(articles) / max_articles)

                    return {
                        "source": "coinmarketcap",
                        "sentiment_score": avg_sentiment,
                        "article_count": len(articles),
                        "confidence": confidence,
                        "weight": self.source_weights["coinmarketcap"],
                        "articles": articles,
                    }

        except Exception as e:
            logger.error(f"Error fetching CoinMarketCap sentiment: {e}")
            return None

    def _calculate_keyword_sentiment(self, text: str) -> float:
        """Calculate sentiment score using keyword analysis."""
        return self.calculators.calculate_keyword_sentiment(text)

    def _calculate_weighted_sentiment(self, sources: list[dict[str, Any]]) -> float:
        """Calculate weighted average sentiment across sources."""
        return self.calculators.calculate_weighted_sentiment(sources)

    def _extract_trending_topics(self, articles: list[dict[str, Any]]) -> list[TrendingTopic]:
        """Extract trending topics from articles."""
        topics = self.aggregators.extract_trending_topics(articles)
        return [TrendingTopic(**topic) for topic in topics]

    def _get_top_articles(self, articles: list[dict[str, Any]]) -> tuple[list[SentimentItem], list[SentimentItem]]:
        """Get top positive and negative articles."""
        return self.aggregators.get_top_articles(articles)

    def _calculate_confidence(self, sources: list[dict[str, Any]], total_articles: int) -> float:
        """Calculate overall confidence in the analysis."""
        return self.calculators.calculate_confidence(sources, total_articles)

    def _is_crypto_ticker(self, ticker: str) -> bool:
        """Check if ticker appears to be a cryptocurrency."""
        crypto_patterns = [
            r".*-USD$",  # BTC-USD, ETH-USD
            r"^(BTC|ETH|ADA|SOL|DOT|LINK|UNI|AAVE|COMP|MKR|SNX|YFI|SUSHI|CRV|BAL|1INCH)$",
        ]

        for pattern in crypto_patterns:
            if re.match(pattern, ticker, re.IGNORECASE):
                return True

        return False

    def _create_empty_result(self, ticker: str) -> SentimentAnalysisResult:
        """Create an empty result when no data is available."""
        return SentimentAnalysisResult(
            ticker=ticker,
            overall_sentiment_score=0.0,
            confidence_level=0.0,
            total_articles=0,
            sources=[],
            trending_topics=[],
            top_positive_articles=[],
            top_negative_articles=[],
        )

    def to_market_sentiment(self, result: SentimentAnalysisResult) -> MarketSentiment:
        """Convert analysis result to MarketSentiment schema."""
        # Calculate sentiment distribution
        pos_count = len([a for a in result.top_positive_articles if a.score > 0.1])
        neg_count = len([a for a in result.top_negative_articles if a.score < -0.1])
        neu_count = max(0, result.total_articles - pos_count - neg_count)

        return MarketSentiment(
            ticker=result.ticker,
            mean_score=result.overall_sentiment_score,
            counts={"pos": pos_count, "neu": neu_count, "neg": neg_count},
            top_pos=result.top_positive_articles[:5],
            top_neg=result.top_negative_articles[:5],
        )
