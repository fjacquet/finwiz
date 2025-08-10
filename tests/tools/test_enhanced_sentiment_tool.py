"""Tests for Enhanced Sentiment Analysis Tool."""

import datetime
from unittest.mock import Mock, patch

import pytest

from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool


class TestEnhancedSentimentAnalysisTool:
    """Test suite for Enhanced Sentiment Analysis Tool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = EnhancedSentimentAnalysisTool()

        # Mock news data for testing
        self.mock_news_data = [
            {
                "title": "Company Reports Strong Quarterly Earnings Growth",
                "publisher": "Reuters",
                "link": "https://example.com/news1",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "The company exceeded analyst expectations with strong revenue growth and positive outlook.",
            },
            {
                "title": "Stock Faces Regulatory Concerns and Potential Downgrade",
                "publisher": "Bloomberg",
                "link": "https://example.com/news2",
                "published_time": (datetime.datetime.now() - datetime.timedelta(days=2)).timestamp(),
                "summary": "Regulatory issues may impact future performance with analysts considering downgrades.",
            },
            {
                "title": "Market Analysis: Neutral Outlook for Technology Sector",
                "publisher": "Wall Street Journal",
                "link": "https://example.com/news3",
                "published_time": (datetime.datetime.now() - datetime.timedelta(days=1)).timestamp(),
                "summary": "Technology sector shows mixed signals with balanced risk-reward profile.",
            },
        ]

    @patch("yfinance.Ticker")
    def test_successful_sentiment_analysis_stock(self, mock_ticker):
        """Test successful sentiment analysis for stock."""
        # Mock yfinance response
        mock_ticker_obj = Mock()
        mock_ticker_obj.news = [
            {
                "title": "Strong earnings beat expectations",
                "publisher": "Reuters",
                "link": "https://example.com/news1",
                "providerPublishTime": datetime.datetime.now().timestamp(),
                "summary": "Company reports strong growth and positive outlook",
            }
        ]
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("AAPL", "stock", 7, 10)

        assert "Enhanced Sentiment Analysis for AAPL (STOCK)" in result
        assert "Sentiment Overview" in result
        assert "Market Outlook" in result
        assert "Articles Analyzed: 1" in result

    @patch("yfinance.Ticker")
    def test_successful_sentiment_analysis_etf(self, mock_ticker):
        """Test successful sentiment analysis for ETF."""
        mock_ticker_obj = Mock()
        mock_ticker_obj.news = [
            {
                "title": "ETF sees strong inflows amid market rally",
                "publisher": "Bloomberg",
                "link": "https://example.com/etf-news",
                "providerPublishTime": datetime.datetime.now().timestamp(),
                "summary": "Technology ETF attracts investor interest with sector rotation",
            }
        ]
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("VTI", "etf", 7, 10)

        assert "Enhanced Sentiment Analysis for VTI (ETF)" in result
        assert "Sentiment Overview" in result

    @patch("yfinance.Ticker")
    def test_successful_sentiment_analysis_crypto(self, mock_ticker):
        """Test successful sentiment analysis for crypto."""
        mock_ticker_obj = Mock()
        mock_ticker_obj.news = [
            {
                "title": "Bitcoin rallies on institutional adoption",
                "publisher": "CNBC",
                "link": "https://example.com/crypto-news",
                "providerPublishTime": datetime.datetime.now().timestamp(),
                "summary": "Cryptocurrency gains momentum with growing institutional interest",
            }
        ]
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("BTC-USD", "crypto", 7, 10)

        assert "Enhanced Sentiment Analysis for BTC-USD (CRYPTO)" in result
        assert "Sentiment Overview" in result

    @patch("yfinance.Ticker")
    def test_no_news_available(self, mock_ticker):
        """Test handling when no news is available."""
        mock_ticker_obj = Mock()
        mock_ticker_obj.news = []
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("UNKNOWN", "stock", 7, 10)

        assert "No Data Available" in result
        assert "No recent news articles found" in result

    @patch("yfinance.Ticker")
    def test_no_recent_news(self, mock_ticker):
        """Test handling when no recent news is available."""
        # Create old news (beyond date filter)
        old_timestamp = (datetime.datetime.now() - datetime.timedelta(days=10)).timestamp()

        mock_ticker_obj = Mock()
        mock_ticker_obj.news = [
            {
                "title": "Old news article",
                "publisher": "Reuters",
                "link": "https://example.com/old-news",
                "providerPublishTime": old_timestamp,
                "summary": "This is old news beyond the filter range",
            }
        ]
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("AAPL", "stock", 7, 10)

        assert "No Recent News" in result
        assert "in the past 7 days" in result

    def test_filter_news_by_date(self):
        """Test news filtering by date range."""
        # Create test data with different dates
        now = datetime.datetime.now()
        test_news = [
            {"title": "Recent news", "published_time": now.timestamp()},
            {"title": "Old news", "published_time": (now - datetime.timedelta(days=10)).timestamp()},
            {"title": "Very recent news", "published_time": (now - datetime.timedelta(hours=1)).timestamp()},
        ]

        filtered = self.tool._filter_news_by_date(test_news, 7)

        # Should only include recent news (within 7 days)
        assert len(filtered) == 2
        assert filtered[0]["title"] == "Recent news"
        assert filtered[1]["title"] == "Very recent news"

    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis with positive news."""
        positive_news = [
            {
                "title": "Strong earnings growth and profit surge",
                "summary": "Company beats expectations with strong revenue growth",
                "publisher": "Reuters",
            }
        ]

        result = self.tool._analyze_sentiment(positive_news, "AAPL", "stock")

        assert result["overall_sentiment"] == "positive"
        assert result["sentiment_score"] > 0
        assert result["sentiment_distribution"]["bullish"] == 1

    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis with negative news."""
        negative_news = [
            {
                "title": "Stock plunges on weak earnings and concerns",
                "summary": "Company faces decline with negative outlook and risks",
                "publisher": "Bloomberg",
            }
        ]

        result = self.tool._analyze_sentiment(negative_news, "AAPL", "stock")

        assert result["overall_sentiment"] == "negative"
        assert result["sentiment_score"] < 0
        assert result["sentiment_distribution"]["bearish"] == 1

    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis with neutral news."""
        neutral_news = [
            {
                "title": "Company reports quarterly results",
                "summary": "Standard quarterly report with mixed indicators",
                "publisher": "MarketWatch",
            }
        ]

        result = self.tool._analyze_sentiment(neutral_news, "AAPL", "stock")

        assert result["overall_sentiment"] == "neutral"
        assert result["sentiment_score"] == 0.0
        assert result["sentiment_distribution"]["neutral"] == 1

    def test_extract_trending_topics(self):
        """Test trending topics extraction."""
        news_with_topics = [
            {
                "title": "Company reports strong earnings results",
                "summary": "Quarterly earnings beat expectations with revenue growth",
            },
            {
                "title": "New product launch drives innovation",
                "summary": "Technology company announces major product release",
            },
            {
                "title": "Earnings guidance updated for next quarter",
                "summary": "Management provides positive earnings outlook",
            },
        ]

        topics = self.tool._extract_trending_topics(news_with_topics)

        # Should identify earnings and product launch topics
        topic_names = [topic["topic"] for topic in topics]
        assert "Earnings" in topic_names or "Financial Results" in topic_names

        # Check topic structure
        if topics:
            assert "article_count" in topics[0]
            assert "average_relevance" in topics[0]
            assert topics[0]["article_count"] >= 2  # Only topics with multiple articles

    def test_calculate_impact_scores(self):
        """Test impact score calculation."""
        news_with_sentiment = [
            {
                "title": "Major earnings beat drives stock surge",
                "publisher": "Reuters",
                "link": "https://example.com/news1",
                "published_time": datetime.datetime.now().timestamp(),
                "sentiment": "bullish",
                "sentiment_score": 0.6,
            },
            {
                "title": "Minor market update",
                "publisher": "Unknown",
                "link": "https://example.com/news2",
                "published_time": datetime.datetime.now().timestamp(),
                "sentiment": "neutral",
                "sentiment_score": 0.1,
            },
        ]

        sentiment_analysis = {"overall_sentiment": "positive"}
        impact_scores = self.tool._calculate_impact_scores(news_with_sentiment, sentiment_analysis)

        # Should prioritize high-impact articles
        if impact_scores:
            assert impact_scores[0]["title"] == "Major earnings beat drives stock surge"
            assert "impact_score" in impact_scores[0]
            assert impact_scores[0]["impact_score"] > 0

    def test_format_article_date(self):
        """Test article date formatting."""
        # Test valid timestamp
        now = datetime.datetime.now()
        timestamp = now.timestamp()
        formatted = self.tool._format_article_date(timestamp)
        expected = now.strftime("%Y-%m-%d")
        assert formatted == expected

        # Test None timestamp
        assert self.tool._format_article_date(None) == "Unknown date"

        # Test invalid timestamp
        assert self.tool._format_article_date(-1) == "Unknown date"

    def test_generate_market_outlook(self):
        """Test market outlook generation."""
        positive_sentiment = {"overall_sentiment": "positive", "sentiment_score": 0.4, "confidence": 0.8}

        trending_topics = [
            {"topic": "Earnings", "article_count": 5},
            {"topic": "Technology", "article_count": 3},
        ]

        outlook = self.tool._generate_market_outlook(positive_sentiment, trending_topics, "stock")

        assert "positive sentiment" in outlook.lower()
        assert "earnings" in outlook.lower()
        assert "technology" in outlook.lower()

    @patch("yfinance.Ticker")
    def test_error_handling(self, mock_ticker):
        """Test error handling in sentiment analysis."""
        # Mock yfinance to raise an exception
        mock_ticker.side_effect = Exception("API Error")

        result = self.tool._run("INVALID", "stock", 7, 10)

        assert "Error performing enhanced sentiment analysis" in result
        assert "INVALID" in result

    def test_input_validation(self):
        """Test input parameter validation."""
        # Test with valid inputs
        try:
            from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentInput

            valid_input = EnhancedSentimentInput(
                ticker="AAPL", asset_type="stock", days_back=7, max_articles=20
            )
            assert valid_input.ticker == "AAPL"
            assert valid_input.asset_type == "stock"
            assert valid_input.days_back == 7
            assert valid_input.max_articles == 20

        except Exception as e:
            pytest.fail(f"Valid input should not raise exception: {e}")

    @pytest.mark.integration
    @patch("yfinance.Ticker")
    def test_full_workflow_integration(self, mock_ticker):
        """Integration test for complete sentiment analysis workflow."""
        # Mock comprehensive news data
        mock_ticker_obj = Mock()
        mock_ticker_obj.news = [
            {
                "title": "Apple reports record quarterly earnings with strong iPhone sales",
                "publisher": "Reuters",
                "link": "https://example.com/apple-earnings",
                "providerPublishTime": datetime.datetime.now().timestamp(),
                "summary": "Apple exceeded analyst expectations with strong revenue growth and positive guidance for next quarter",
            },
            {
                "title": "Technology sector faces regulatory scrutiny",
                "publisher": "Bloomberg",
                "link": "https://example.com/tech-regulation",
                "providerPublishTime": (datetime.datetime.now() - datetime.timedelta(days=1)).timestamp(),
                "summary": "New regulations may impact technology companies with compliance costs and operational changes",
            },
            {
                "title": "Apple announces new product innovation in AI technology",
                "publisher": "Wall Street Journal",
                "link": "https://example.com/apple-ai",
                "providerPublishTime": (datetime.datetime.now() - datetime.timedelta(hours=12)).timestamp(),
                "summary": "Company unveils breakthrough AI technology integration across product lineup",
            },
        ]
        mock_ticker.return_value = mock_ticker_obj

        result = self.tool._run("AAPL", "stock", 7, 20)

        # Verify comprehensive response structure
        assert "Enhanced Sentiment Analysis for AAPL (STOCK)" in result
        assert "📊 Sentiment Overview" in result
        assert "🔍 Market Outlook" in result
        assert "🔥 Trending Topics" in result
        assert "📰 Most Impactful Articles" in result
        assert "📈 Analysis Summary" in result

        # Verify data processing
        assert "Articles Analyzed: 3" in result
        assert "Sentiment Distribution:" in result

        # Should identify earnings and technology topics
        assert (
            "Earnings" in result
            or "Financial Results" in result
            or "Technology" in result
            or "Product Launch" in result
        )


if __name__ == "__main__":
    pytest.main([__file__])
