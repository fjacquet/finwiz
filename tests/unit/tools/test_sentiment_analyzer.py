"""
Unit tests for the SentimentAnalyzer class.

Tests multi-source sentiment analysis with mocked API responses to ensure
proper integration, weighted scoring, and trending topic extraction.
"""

from pytest import approx
import asyncio

import pytest

from finwiz.tools.sentiment_analyzer import (
    SentimentAnalysisResult,
    SentimentAnalyzer,
    TrendingTopic,
)
from tests.fixtures.api_test_mocks import APITestMocks


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a SentimentAnalyzer instance for testing."""
        return SentimentAnalyzer()

    @pytest.fixture
    def mock_alpha_vantage_response(self):
        """Mock Alpha Vantage API response."""
        return {
            "feed": [
                {
                    "title": "Apple Reports Strong Quarterly Earnings",
                    "summary": "Apple exceeded expectations with strong revenue growth",
                    "url": "https://example.com/news1",
                    "time_published": "20240101T120000",
                    "source": "Reuters",
                    "overall_sentiment_score": "0.5",
                    "ticker_sentiment": [{"ticker": "AAPL", "relevance_score": "0.8", "ticker_sentiment_score": "0.6"}],
                },
                {
                    "title": "Market Concerns Over Apple Supply Chain",
                    "summary": "Analysts express concerns about supply chain disruptions",
                    "url": "https://example.com/news2",
                    "time_published": "20240101T100000",
                    "source": "Bloomberg",
                    "overall_sentiment_score": "-0.3",
                    "ticker_sentiment": [{"ticker": "AAPL", "relevance_score": "0.7", "ticker_sentiment_score": "-0.4"}],
                },
            ]
        }

    @pytest.fixture
    def mock_yahoo_finance_news(self):
        """Mock Yahoo Finance news data."""
        return [
            {
                "title": "Apple Stock Surges on Innovation Announcement",
                "summary": "Strong investor confidence in new product launch",
                "link": "https://finance.yahoo.com/news1",
                "publisher": "Yahoo Finance",
                "providerPublishTime": 1704110400,  # 2024-01-01 12:00:00
            },
            {
                "title": "Apple Faces Regulatory Challenges",
                "summary": "New regulations may impact future growth",
                "link": "https://finance.yahoo.com/news2",
                "publisher": "MarketWatch",
                "providerPublishTime": 1704106800,  # 2024-01-01 11:00:00
            },
        ]

    @pytest.fixture
    def mock_coinmarketcap_response(self):
        """Mock CoinMarketCap API response."""
        return {
            "map_response": {"data": [{"id": 1, "symbol": "BTC"}]},
            "news_response": {
                "data": [
                    {
                        "title": "Bitcoin Adoption Grows Among Institutions",
                        "description": "Major financial institutions embrace Bitcoin",
                        "url": "https://coinmarketcap.com/news1",
                        "source": "CoinDesk",
                        "published_at": "2024-01-01T12:00:00Z",
                    },
                    {
                        "title": "Bitcoin Price Volatility Concerns Investors",
                        "description": "High volatility raises risk concerns",
                        "url": "https://coinmarketcap.com/news2",
                        "source": "CoinTelegraph",
                        "published_at": "2024-01-01T11:00:00Z",
                    },
                ]
            },
        }

    def test_should_initialize_with_correct_weights_and_keywords(self, analyzer):
        """Test that analyzer initializes with proper configuration."""
        # Assert source weights sum to 1.0
        total_weight = sum(analyzer.source_weights.values())
        assert abs(total_weight - 1.0) < 0.01

        # Assert keyword lists are populated
        assert len(analyzer.bullish_keywords) > 0
        assert len(analyzer.bearish_keywords) > 0
        assert len(analyzer.topic_keywords) > 0

        # Assert specific keywords exist
        assert "growth" in analyzer.bullish_keywords
        assert "decline" in analyzer.bearish_keywords
        assert "earnings" in analyzer.topic_keywords

    def test_should_calculate_keyword_sentiment_correctly(self, analyzer):
        """Test keyword-based sentiment calculation."""
        # Test positive sentiment
        positive_text = "Strong growth and profit exceed expectations"
        pos_score = analyzer._calculate_keyword_sentiment(positive_text)
        assert pos_score > 0

        # Test negative sentiment
        negative_text = "Decline in revenue and weak performance concerns"
        neg_score = analyzer._calculate_keyword_sentiment(negative_text)
        assert neg_score < 0

        # Test neutral sentiment
        neutral_text = "The company announced a meeting"
        neu_score = analyzer._calculate_keyword_sentiment(neutral_text)
        assert neu_score == approx(0.0)

    def test_should_identify_crypto_tickers_correctly(self, analyzer):
        """Test cryptocurrency ticker identification."""
        # Test crypto tickers
        assert analyzer._is_crypto_ticker("BTC-USD") is True
        assert analyzer._is_crypto_ticker("ETH-USD") is True
        assert analyzer._is_crypto_ticker("BTC") is True
        assert analyzer._is_crypto_ticker("ETH") is True

        # Test non-crypto tickers
        assert analyzer._is_crypto_ticker("AAPL") is False
        assert analyzer._is_crypto_ticker("MSFT") is False
        assert analyzer._is_crypto_ticker("SPY") is False

    def test_should_calculate_weighted_sentiment_correctly(self, analyzer):
        """Test weighted sentiment calculation across sources."""
        sources = [
            {"source": "alpha_vantage", "sentiment_score": 0.6, "confidence": 0.8, "weight": 0.4},
            {"source": "yahoo_finance", "sentiment_score": -0.2, "confidence": 0.7, "weight": 0.35},
            {"source": "coinmarketcap", "sentiment_score": 0.3, "confidence": 0.6, "weight": 0.25},
        ]

        weighted_sentiment = analyzer._calculate_weighted_sentiment(sources)

        # Should be positive but less than the highest individual score
        assert -1.0 <= weighted_sentiment <= 1.0
        assert weighted_sentiment > 0  # Should be positive overall

    def test_should_extract_trending_topics_correctly(self, analyzer):
        """Test trending topic extraction from articles."""
        articles = [
            {
                "title": "Company Reports Strong Earnings Results",
                "summary": "Quarterly earnings beat expectations with revenue growth",
            },
            {
                "title": "New Product Launch Announcement",
                "summary": "Innovation in technology sector drives product release",
            },
            {
                "title": "Earnings Call Highlights Technology Advances",
                "summary": "Management discusses earnings and technology roadmap",
            },
        ]

        trending_topics = analyzer._extract_trending_topics(articles)

        # Should identify earnings and technology as trending topics
        topic_names = [topic.topic for topic in trending_topics]
        assert any("Earnings" in name for name in topic_names)
        assert any("Technology" in name for name in topic_names)

        # Check topic structure
        for topic in trending_topics:
            assert isinstance(topic, TrendingTopic)
            assert topic.article_count >= 2  # Minimum threshold
            assert 0.0 <= topic.relevance_score <= 1.0

    @pytest.mark.asyncio
    async def test_should_handle_alpha_vantage_api_success(self, mock_alpha_vantage_response, mocker):
        """Test successful Alpha Vantage API integration."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        # Create analyzer after setting environment variable
        analyzer = SentimentAnalyzer()

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_alpha_vantage_mock(mocker, ticker="AAPL", feed=mock_alpha_vantage_response["feed"])

        result = await analyzer._fetch_alpha_vantage_sentiment("AAPL", 7, 20)

        assert result is not None
        assert result["source"] == "alpha_vantage"
        assert result["article_count"] == 2
        assert -1.0 <= result["sentiment_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_should_handle_alpha_vantage_api_failure(self, analyzer, mocker):
        """Test Alpha Vantage API failure handling."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        # Use APITestMocks for error scenario
        APITestMocks.setup_http_error_mock(mocker, status_code=500, error_message="Internal Server Error")

        result = await analyzer._fetch_alpha_vantage_sentiment("AAPL", 7, 20)

        assert result is None

    @pytest.mark.asyncio
    async def test_should_handle_yahoo_finance_success(self, analyzer, mock_yahoo_finance_news, mocker):
        """Test successful Yahoo Finance integration."""
        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_yahoo_finance_mock(mocker, ticker="AAPL", news=mock_yahoo_finance_news)

        result = await analyzer._fetch_yahoo_finance_sentiment("AAPL", 20)

        assert result is not None
        assert result["source"] == "yahoo_finance"
        assert result["article_count"] == 2
        assert -1.0 <= result["sentiment_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_should_handle_yahoo_finance_no_news(self, analyzer, mocker):
        """Test Yahoo Finance when no news is available."""
        # Use APITestMocks for no news scenario
        APITestMocks.setup_yahoo_finance_mock(mocker, ticker="AAPL", news=[])

        result = await analyzer._fetch_yahoo_finance_sentiment("AAPL", 20)

        assert result is None

    @pytest.mark.asyncio
    async def test_should_handle_coinmarketcap_success_for_crypto(self, mock_coinmarketcap_response, mocker):
        """Test successful CoinMarketCap integration for crypto tickers."""
        mocker.patch.dict("os.environ", {"X-CMC_PRO_API_KEY": "test_key"})

        # Create analyzer after patching environment variable
        analyzer = SentimentAnalyzer()

        # Use APITestMocks for standardized mock setup
        APITestMocks.setup_coinmarketcap_mock(
            mocker,
            crypto_symbol="BTC",
            map_data=mock_coinmarketcap_response["map_response"]["data"],
            news_data=mock_coinmarketcap_response["news_response"]["data"],
        )

        result = await analyzer._fetch_coinmarketcap_sentiment("BTC-USD", 20)

        assert result is not None
        assert result["source"] == "coinmarketcap"
        assert result["article_count"] == 2
        assert -1.0 <= result["sentiment_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_should_skip_coinmarketcap_for_non_crypto(self, analyzer, mocker):
        """Test that CoinMarketCap is skipped for non-crypto tickers."""
        mocker.patch.dict("os.environ", {"X-CMC_PRO_API_KEY": "test_key"})
        result = await analyzer._fetch_coinmarketcap_sentiment("AAPL", 20)
        assert result is None

    @pytest.mark.asyncio
    async def test_should_perform_complete_analysis_successfully(self, analyzer, mocker):
        """Test complete sentiment analysis workflow."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key", "X-CMC_PRO_API_KEY": "test_key"})

        # Mock all source methods using mocker
        analyzer._fetch_alpha_vantage_sentiment = mocker.AsyncMock(
            return_value={
                "source": "alpha_vantage",
                "sentiment_score": 0.3,
                "article_count": 5,
                "confidence": 0.8,
                "weight": 0.4,
            }
        )

        analyzer._fetch_yahoo_finance_sentiment = mocker.AsyncMock(
            return_value={
                "source": "yahoo_finance",
                "sentiment_score": -0.1,
                "article_count": 3,
                "confidence": 0.6,
                "weight": 0.35,
            }
        )

        analyzer._fetch_coinmarketcap_sentiment = mocker.AsyncMock(return_value=None)

        result = await analyzer.analyze_sentiment("AAPL", days_back=7, max_articles_per_source=20)

        # Verify result structure
        assert isinstance(result, SentimentAnalysisResult)
        assert result.ticker == "AAPL"
        assert -1.0 <= result.overall_sentiment_score <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0
        assert result.total_articles == 0  # No articles in mock data, only source counts
        assert len(result.sources) == 2  # Alpha Vantage and Yahoo Finance

    @pytest.mark.asyncio
    async def test_should_handle_all_sources_failing(self, analyzer, mocker):
        """Test handling when all data sources fail."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key", "X-CMC_PRO_API_KEY": "test_key"})

        # Mock all sources to fail using mocker
        analyzer._fetch_alpha_vantage_sentiment = mocker.AsyncMock(return_value=None)
        analyzer._fetch_yahoo_finance_sentiment = mocker.AsyncMock(return_value=None)
        analyzer._fetch_coinmarketcap_sentiment = mocker.AsyncMock(return_value=None)

        result = await analyzer.analyze_sentiment("AAPL")

        # Should return empty result
        assert isinstance(result, SentimentAnalysisResult)
        assert result.ticker == "AAPL"
        assert result.overall_sentiment_score == approx(0.0)
        assert result.confidence_level == approx(0.0)
        assert result.total_articles == 0
        assert len(result.sources) == 0

    def test_should_convert_to_market_sentiment_schema(self, analyzer):
        """Test conversion to MarketSentiment schema."""
        # Create a sample analysis result
        result = SentimentAnalysisResult(
            ticker="AAPL",
            overall_sentiment_score=0.25,
            confidence_level=0.8,
            total_articles=10,
            sources=[],
            trending_topics=[],
            top_positive_articles=[],
            top_negative_articles=[],
        )

        market_sentiment = analyzer.to_market_sentiment(result)

        assert market_sentiment.ticker == "AAPL"
        assert market_sentiment.mean_score == approx(0.25)
        assert "pos" in market_sentiment.counts
        assert "neu" in market_sentiment.counts
        assert "neg" in market_sentiment.counts

    def test_should_calculate_confidence_correctly(self, analyzer):
        """Test confidence calculation logic."""
        # Test with multiple sources and good article count
        sources = [{"confidence": 0.8}, {"confidence": 0.7}, {"confidence": 0.9}]
        confidence = analyzer._calculate_confidence(sources, 30)
        assert 0.7 <= confidence <= 1.0

        # Test with single source and low article count
        sources = [{"confidence": 0.5}]
        confidence = analyzer._calculate_confidence(sources, 5)
        assert 0.0 <= confidence <= 0.6

        # Test with no sources
        confidence = analyzer._calculate_confidence([], 0)
        assert confidence == approx(0.0)

    def test_should_handle_missing_api_keys_gracefully(self, mocker):
        """Test handling of missing API keys."""
        # Clear environment variables and create new analyzer
        mocker.patch.dict("os.environ", {}, clear=True)
        # Create analyzer without API keys
        analyzer_no_keys = SentimentAnalyzer()

        # Alpha Vantage should return None without API key
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(analyzer_no_keys._fetch_alpha_vantage_sentiment("AAPL", 7, 20))
            assert result is None

            # CoinMarketCap should return None without API key
            result = loop.run_until_complete(analyzer_no_keys._fetch_coinmarketcap_sentiment("BTC-USD", 20))
            assert result is None
        finally:
            loop.close()

    @pytest.mark.asyncio
    async def test_should_handle_api_timeout_gracefully(self, analyzer, mocker):
        """Test handling of API timeouts."""
        mocker.patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test_key"})

        # Use APITestMocks for timeout scenario
        APITestMocks.setup_timeout_mock(mocker, timeout_error=True)

        result = await analyzer._fetch_alpha_vantage_sentiment("AAPL", 7, 20)

        assert result is None

    def test_should_validate_sentiment_score_ranges(self, analyzer):
        """Test that sentiment scores are always within valid ranges."""
        # Test extreme positive text
        extreme_positive = " ".join(analyzer.bullish_keywords * 10)
        score = analyzer._calculate_keyword_sentiment(extreme_positive)
        assert -1.0 <= score <= 1.0

        # Test extreme negative text
        extreme_negative = " ".join(analyzer.bearish_keywords * 10)
        score = analyzer._calculate_keyword_sentiment(extreme_negative)
        assert -1.0 <= score <= 1.0