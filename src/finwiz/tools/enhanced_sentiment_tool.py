"""
Enhanced Sentiment Analysis Tool with Multi-Source Integration.

This tool implements the n8n workflow sentiment analysis logic adapted for FinWiz,
providing comprehensive sentiment analysis across stocks, ETFs, and crypto assets.
"""

import asyncio
from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.tools.logger import get_logger
from finwiz.tools.sentiment_calculations import SentimentCalculator
from finwiz.tools.sentiment_formatting import SentimentResponseFormatter
from finwiz.tools.sentiment_sources import SentimentDataSources

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

    def __init__(self, **kwargs) -> None:
        """Initialize the enhanced sentiment analysis tool."""
        super().__init__(**kwargs)
        # Initialize components after parent initialization
        object.__setattr__(self, "calculator", SentimentCalculator())
        object.__setattr__(self, "data_sources", SentimentDataSources())
        object.__setattr__(self, "formatter", SentimentResponseFormatter())

    def _get_perplexity_integration(self) -> Any:
        """Get Perplexity integration instance if enabled."""
        return self.data_sources.get_perplexity_integration()

    def _run(self, ticker: str, asset_type: str = "stock", days_back: int = 7, max_articles: int = 20) -> str:
        """Execute enhanced sentiment analysis."""
        try:
            logger.info(f"Starting enhanced sentiment analysis for {ticker} ({asset_type})")

            # Get enhanced news data from multiple sources including Sonar
            enhanced_news_data = asyncio.run(self.data_sources.get_enhanced_news_data(ticker, asset_type, max_articles))

            yahoo_articles = enhanced_news_data.get("yahoo_articles", [])
            sonar_articles = enhanced_news_data.get("sonar_articles", [])
            combined_count = enhanced_news_data.get("combined_count", 0)
            sonar_fallback_used = enhanced_news_data.get("sonar_fallback_used", False)

            if combined_count == 0:
                return self.formatter.format_no_data_response(ticker, asset_type)

            # Filter news by date range
            filtered_yahoo = self.data_sources.filter_news_by_date(yahoo_articles, days_back)
            filtered_sonar = self.data_sources.filter_sonar_articles_by_date(sonar_articles, days_back)

            if not filtered_yahoo and not filtered_sonar:
                return self.formatter.format_no_recent_news_response(ticker, asset_type, days_back)

            # Combine filtered articles for analysis
            combined_articles = self.data_sources.combine_article_sources(filtered_yahoo, filtered_sonar)

            # Perform sentiment analysis using n8n workflow logic
            sentiment_analysis = self.calculator.analyze_sentiment(combined_articles, ticker, asset_type)

            # Extract trending topics
            trending_topics = self.calculator.extract_trending_topics(combined_articles)

            # Calculate impact scores
            impact_scores = self.calculator.calculate_impact_scores(combined_articles, sentiment_analysis)

            # Generate market outlook
            market_outlook = self.calculator.generate_market_outlook(sentiment_analysis, trending_topics, asset_type)

            # Format comprehensive response with Sonar integration
            return self.formatter.format_comprehensive_response(
                ticker=ticker,
                asset_type=asset_type,
                sentiment_analysis=sentiment_analysis,
                trending_topics=trending_topics,
                impact_scores=impact_scores,
                market_outlook=market_outlook,
                article_count=len(combined_articles),
                sonar_articles=filtered_sonar,
                data_sources=self.data_sources.get_data_sources_list(filtered_yahoo, filtered_sonar),
                sonar_fallback_used=sonar_fallback_used,
            )

        except Exception as e:
            logger.error(f"Error in enhanced sentiment analysis for {ticker}: {str(e)}")
            return self.formatter.format_error_response(ticker, asset_type, str(e))
