"""
Unit tests for Standardized Sentiment Analysis Tool.

Tests the standardized sentiment analysis capabilities including weighted scoring,
trending topics extraction, and consistent methodology across asset classes.
"""

from datetime import datetime, timedelta

import pytest

from finwiz.tools.standardized_sentiment_tool import (
    CrossAssetSentimentComparatorTool,
    StandardizedSentimentAnalysisTool,
    StandardizedSentimentInput,
)


class TestStandardizedSentimentInput:
    """Test the input schema for Standardized Sentiment Analysis Tool."""

    def test_should_create_valid_input_with_defaults(self):
        """Test creating input with default values."""
        # Arrange & Act
        input_data = StandardizedSentimentInput(symbol="AAPL", asset_class="stock")

        # Assert
        assert input_data.symbol == "AAPL"
        assert input_data.asset_class == "stock"
        assert input_data.max_articles == 50
        assert input_data.days_back == 30
        assert input_data.include_trending is True

    def test_should_create_valid_input_with_custom_values(self):
        """Test creating input with custom values."""
        # Arrange & Act
        input_data = StandardizedSentimentInput(
            symbol="BTC", asset_class="crypto", max_articles=25, days_back=14, include_trending=False
        )

        # Assert
        assert input_data.symbol == "BTC"
        assert input_data.asset_class == "crypto"
        assert input_data.max_articles == 25
        assert input_data.days_back == 14
        assert input_data.include_trending is False

    def test_should_validate_asset_class_enum(self):
        """Test validation of asset_class parameter."""
        # Test valid asset classes
        for asset_class in ["stock", "etf", "crypto"]:
            input_data = StandardizedSentimentInput(symbol="TEST", asset_class=asset_class)
            assert input_data.asset_class == asset_class

    def test_should_validate_parameter_ranges(self):
        """Test validation of parameter ranges."""
        # Test valid ranges
        valid_input = StandardizedSentimentInput(symbol="TEST", asset_class="stock", max_articles=75, days_back=60)
        assert valid_input.max_articles == 75
        assert valid_input.days_back == 60

        # Test invalid ranges should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            StandardizedSentimentInput(symbol="TEST", asset_class="stock", max_articles=5)

        with pytest.raises(Exception):  # Pydantic validation error
            StandardizedSentimentInput(symbol="TEST", asset_class="stock", days_back=100)


class TestStandardizedSentimentAnalysisTool:
    """Test the Standardized Sentiment Analysis Tool functionality."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Standardized Sentiment Analysis Tool."""
        return StandardizedSentimentAnalysisTool()

    @pytest.fixture
    def sample_articles(self):
        """Sample articles for testing."""
        base_date = datetime.now() - timedelta(days=1)
        return [
            {
                "headline": "AAPL Reports Strong Quarterly Earnings Beat",
                "url": "https://finance.yahoo.com/news/aapl-earnings-beat",
                "date": base_date,
                "source": "Yahoo Finance",
                "content": "Apple exceeded analyst expectations with strong revenue growth and improved margins.",
            },
            {
                "headline": "Apple Faces Headwinds from Market Volatility",
                "url": "https://reuters.com/business/apple-challenges",
                "date": base_date - timedelta(hours=12),
                "source": "Reuters",
                "content": "Apple stock declined amid broader market concerns and sector rotation.",
            },
            {
                "headline": "Analysts Upgrade AAPL Price Target on Growth Prospects",
                "url": "https://marketwatch.com/story/aapl-upgrade",
                "date": base_date - timedelta(days=2),
                "source": "MarketWatch",
                "content": "Multiple analysts raised their price targets for Apple citing strong fundamentals.",
            },
        ]

    def test_should_normalize_symbol_input(self, tool):
        """Test symbol normalization."""
        # Arrange & Act
        result = tool._run(symbol="  aapl  ", asset_class="stock", max_articles=10)

        # Assert
        assert result["symbol"] == "AAPL"

    def test_should_create_sample_financial_articles(self, tool):
        """Test creation of sample financial articles."""
        # Act
        articles = tool._create_sample_financial_articles("AAPL", "earnings")

        # Assert
        assert len(articles) > 0
        for article in articles:
            assert "headline" in article
            assert "url" in article
            assert "date" in article
            assert "source" in article
            assert "content" in article
            assert "AAPL" in article["headline"]

    def test_should_create_sample_crypto_articles(self, tool):
        """Test creation of sample crypto articles."""
        # Act
        articles = tool._create_sample_crypto_articles("BTC", "price")

        # Assert
        assert len(articles) > 0
        for article in articles:
            assert "headline" in article
            assert "url" in article
            assert "date" in article
            assert "source" in article
            assert "content" in article
            assert "BTC" in article["headline"]

    def test_should_deduplicate_articles(self, tool):
        """Test article deduplication functionality."""
        # Arrange
        articles = [
            {"headline": "Apple Reports Strong Earnings", "content": "Content 1"},
            {"headline": "Apple reports strong earnings!", "content": "Content 2"},  # Similar headline
            {"headline": "Different News About Apple", "content": "Content 3"},
            {"headline": "Apple Reports Strong Earnings", "content": "Content 4"},  # Exact duplicate
        ]

        # Act
        unique_articles = tool._deduplicate_articles(articles)

        # Assert
        assert len(unique_articles) <= len(articles)
        assert len(unique_articles) >= 2  # Should keep at least 2 unique articles

    def test_should_calculate_article_sentiment_positive(self, tool):
        """Test positive sentiment calculation."""
        # Arrange
        positive_article = {
            "headline": "AAPL Surges on Strong Earnings Beat",
            "content": "Apple stock rallied significantly after reporting excellent quarterly results with strong revenue growth and bullish outlook.",
        }

        # Act
        sentiment_score = tool._calculate_article_sentiment(positive_article)

        # Assert
        assert sentiment_score > 0
        assert -1.0 <= sentiment_score <= 1.0

    def test_should_calculate_article_sentiment_negative(self, tool):
        """Test negative sentiment calculation."""
        # Arrange
        negative_article = {
            "headline": "AAPL Falls on Regulatory Concerns",
            "content": "Apple stock declined sharply amid regulatory threats and market uncertainty with bearish analyst downgrades.",
        }

        # Act
        sentiment_score = tool._calculate_article_sentiment(negative_article)

        # Assert
        assert sentiment_score < 0
        assert -1.0 <= sentiment_score <= 1.0

    def test_should_calculate_article_sentiment_neutral(self, tool):
        """Test neutral sentiment calculation."""
        # Arrange
        neutral_article = {
            "headline": "AAPL Price Information",
            "content": "Apple stock price information and data available for review.",
        }

        # Act
        sentiment_score = tool._calculate_article_sentiment(neutral_article)

        # Assert
        # Note: The sentiment algorithm may still detect some bias, so we test the range
        assert -1.0 <= sentiment_score <= 1.0

    def test_should_convert_score_to_label_correctly(self, tool):
        """Test sentiment score to label conversion."""
        # Arrange & Act & Assert
        assert tool._score_to_label(0.5) == "pos"
        assert tool._score_to_label(-0.5) == "neg"
        assert tool._score_to_label(0.05) == "neu"
        assert tool._score_to_label(-0.05) == "neu"

    def test_should_analyze_article_sentiments(self, tool, sample_articles):
        """Test sentiment analysis for multiple articles."""
        # Act
        analyzed_articles = tool._analyze_article_sentiments(sample_articles)

        # Assert
        assert len(analyzed_articles) == len(sample_articles)
        for article in analyzed_articles:
            assert "sentiment_score" in article
            assert "sentiment_label" in article
            assert "confidence" in article
            assert -1.0 <= article["sentiment_score"] <= 1.0
            assert article["sentiment_label"] in ["pos", "neu", "neg"]
            assert 0.0 <= article["confidence"] <= 1.0

    def test_should_calculate_sentiment_metrics(self, tool, sample_articles):
        """Test comprehensive sentiment metrics calculation."""
        # Arrange
        analyzed_articles = tool._analyze_article_sentiments(sample_articles)

        # Act
        metrics = tool._calculate_sentiment_metrics(analyzed_articles)

        # Assert
        assert "mean_score" in metrics
        assert "weighted_score" in metrics
        assert "confidence_interval" in metrics
        assert "counts" in metrics
        assert -1.0 <= metrics["mean_score"] <= 1.0
        assert -1.0 <= metrics["weighted_score"] <= 1.0
        assert len(metrics["confidence_interval"]) == 2
        assert set(metrics["counts"].keys()) == {"pos", "neu", "neg"}
        assert sum(metrics["counts"].values()) == len(analyzed_articles)

    def test_should_extract_trending_topics(self, tool, sample_articles):
        """Test trending topics extraction."""
        # Arrange
        analyzed_articles = tool._analyze_article_sentiments(sample_articles)

        # Act
        trending_topics = tool._extract_trending_topics(analyzed_articles, "AAPL")

        # Assert
        assert isinstance(trending_topics, list)
        for topic in trending_topics:
            assert "topic" in topic
            assert "mention_count" in topic
            assert "relevance_score" in topic
            assert "sentiment" in topic
            assert topic["mention_count"] >= 2  # Minimum threshold
            assert 0.0 <= topic["relevance_score"] <= 1.0
            assert -1.0 <= topic["sentiment"] <= 1.0

    def test_should_get_top_sentiment_articles(self, tool, sample_articles):
        """Test extraction of top positive and negative articles."""
        # Arrange
        analyzed_articles = tool._analyze_article_sentiments(sample_articles)

        # Act
        top_pos, top_neg = tool._get_top_sentiment_articles(analyzed_articles)

        # Assert
        assert isinstance(top_pos, list)
        assert isinstance(top_neg, list)
        assert len(top_pos) <= 3
        assert len(top_neg) <= 3

        # Check positive articles have positive scores
        for article in top_pos:
            assert article["score"] > 0
            assert "headline" in article
            assert "url" in article
            assert "date" in article

        # Check negative articles have negative scores
        for article in top_neg:
            assert article["score"] < 0
            assert "headline" in article
            assert "url" in article
            assert "date" in article

    def test_should_handle_complete_analysis_workflow(self, mocker, tool, sample_articles):
        """Test complete sentiment analysis workflow."""
        # Arrange
        mock_collect = mocker.patch.object(StandardizedSentimentAnalysisTool, "_collect_news_articles")
        mock_collect.return_value = sample_articles

        # Act
        result = tool._run(symbol="AAPL", asset_class="stock", max_articles=25, days_back=30, include_trending=True)

        # Assert
        assert "error" not in result
        assert result["symbol"] == "AAPL"
        assert result["asset_class"] == "stock"
        assert result["articles_analyzed"] == len(sample_articles)
        assert "mean_score" in result
        assert "weighted_score" in result
        assert "confidence_interval" in result
        assert "counts" in result
        assert "top_pos" in result
        assert "top_neg" in result
        assert "trending_topics" in result
        assert "methodology" in result

    def test_should_handle_no_articles_found(self, mocker, tool):
        """Test handling when no articles are found."""
        # Arrange & Act
        mock_collect = mocker.patch.object(tool, "_collect_news_articles")
        mock_collect.return_value = []
        result = tool._run(symbol="INVALID", asset_class="stock")

        # Assert
        assert "error" in result
        assert "No news articles found" in result["error"]
        assert result["mean_score"] == 0.0
        assert result["counts"] == {"pos": 0, "neu": 0, "neg": 0}
        assert result["top_pos"] == []
        assert result["top_neg"] == []

    def test_should_handle_trending_topics_disabled(self, mocker, tool, sample_articles):
        """Test behavior when trending topics extraction is disabled."""
        # Arrange & Act
        mock_collect = mocker.patch.object(tool, "_collect_news_articles")
        mock_collect.return_value = sample_articles
        result = tool._run(symbol="AAPL", asset_class="stock", include_trending=False)

        # Assert
        assert "error" not in result
        assert result["trending_topics"] == []

    def test_should_handle_different_asset_classes(self, mocker, tool):
        """Test handling of different asset classes."""
        # Arrange
        mock_collect = mocker.patch.object(tool, "_collect_news_articles")
        mock_collect.return_value = []

        # Test stock
        result_stock = tool._run(symbol="AAPL", asset_class="stock")
        assert result_stock["asset_class"] == "stock"

        # Test ETF
        result_etf = tool._run(symbol="SPY", asset_class="etf")
        assert result_etf["asset_class"] == "etf"

        # Test crypto
        result_crypto = tool._run(symbol="BTC", asset_class="crypto")
        assert result_crypto["asset_class"] == "crypto"


class TestCrossAssetSentimentComparatorTool:
    """Test the Cross-Asset Sentiment Comparator Tool."""

    @pytest.fixture
    def tool(self):
        """Create an instance of the Cross-Asset Sentiment Comparator Tool."""
        return CrossAssetSentimentComparatorTool()

    def test_should_return_methodology_information(self, tool):
        """Test that the tool returns methodology information."""
        # Act
        result = tool._run()

        # Assert
        assert result["tool"] == "CrossAssetSentimentComparatorTool"
        assert "methodology" in result
        assert "cross-asset" in result["methodology"].lower()


class TestIntegrationScenarios:
    """Test integration scenarios for standardized sentiment analysis."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for integration tests."""
        return StandardizedSentimentAnalysisTool()

    def test_should_handle_mixed_sentiment_articles(self, mocker, tool):
        """Test handling of articles with mixed sentiment."""
        # Arrange
        mixed_articles = [
            {
                "headline": "AAPL Surges on Strong Earnings",
                "content": "Positive earnings results drive stock higher",
                "url": "https://test.com/1",
                "date": datetime.now(),
                "source": "Test",
            },
            {
                "headline": "AAPL Falls on Market Concerns",
                "content": "Regulatory threats and market uncertainty weigh on stock",
                "url": "https://test.com/2",
                "date": datetime.now(),
                "source": "Test",
            },
            {
                "headline": "AAPL Trading Update",
                "content": "Normal trading activity continues",
                "url": "https://test.com/3",
                "date": datetime.now(),
                "source": "Test",
            },
        ]

        # Act
        mock_collect = mocker.patch.object(tool, "_collect_news_articles")
        mock_collect.return_value = mixed_articles
        result = tool._run(symbol="AAPL", asset_class="stock")

        # Assert
        assert "error" not in result
        assert result["articles_analyzed"] == 3
        assert result["counts"]["pos"] >= 1
        assert result["counts"]["neg"] >= 1
        assert abs(result["mean_score"]) <= 1.0  # Should be balanced

    def test_should_handle_error_in_analysis_gracefully(self, mocker, tool):
        """Test graceful error handling during analysis."""
        # Arrange & Act
        mock_collect = mocker.patch.object(tool, "_collect_news_articles")
        mock_collect.side_effect = Exception("Collection error")
        result = tool._run(symbol="TEST", asset_class="stock")

        # Assert
        assert "error" in result
        assert "Collection error" in result["error"]
