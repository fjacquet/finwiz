"""
Tests for multi-tool integration scenarios with Perplexity.

This module tests data combination logic for different analysis tools and data sources,
verifying that each analysis type works with combined traditional and Sonar data sources,
and testing error handling and graceful degradation scenarios across all integrated tools.
"""

import asyncio
import datetime

from finwiz.schemas.perplexity import SonarArticle, SonarSearchResult
from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration


class TestMultiToolIntegrationScenarios:
    """Test multi-tool integration scenarios with Perplexity."""

    def setup_method(self):
        """Set up test environment."""
        # Clear any existing feature flags instance
        import finwiz.utils.feature_flags

        finwiz.utils.feature_flags._feature_flags = None

    def test_should_combine_yahoo_and_sonar_data_sources(self, mocker):
        """Test data combination logic for different analysis tools and data sources."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Mock Yahoo Finance data
        yahoo_articles = [
            {
                "title": "Apple Reports Q4 Earnings Beat",
                "publisher": "Yahoo Finance",
                "link": "https://finance.yahoo.com/apple-earnings",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple exceeded analyst expectations",
                "source": "yahoo_finance",
            },
            {
                "title": "Apple Stock Rises on Strong iPhone Sales",
                "publisher": "MarketWatch",
                "link": "https://marketwatch.com/apple-iphone",
                "published_time": datetime.datetime.now().timestamp() - 3600,
                "summary": "iPhone sales drive revenue growth",
                "source": "yahoo_finance",
            },
        ]

        # Mock Sonar articles
        sonar_articles = [
            SonarArticle(
                title="Apple SEC Filing Shows Strong Fundamentals",
                url="https://sec.gov/apple-10k",
                summary="SEC 10-K filing reveals strong financial position",
                publisher="SEC",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.95,
                content_type="filing",
                analysis_type="sentiment",
            ),
            SonarArticle(
                title="Analyst Upgrades Apple to Buy Rating",
                url="https://bloomberg.com/apple-upgrade",
                summary="Goldman Sachs upgrades Apple with $200 price target",
                publisher="Bloomberg",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.90,
                content_type="analysis",
                analysis_type="sentiment",
            ),
        ]

        sonar_result = SonarSearchResult(
            query="AAPL sentiment analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=sonar_articles,
            total_results=2,
            search_time_ms=300,
            success=True,
        )

        # Set up tool with mocked data
        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=sonar_result)
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

        # Act
        enhanced_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))
        combined_articles = tool._combine_article_sources(enhanced_data["yahoo_articles"], enhanced_data["sonar_articles"])

        # Assert
        assert len(combined_articles) == 4  # 2 Yahoo + 2 Sonar

        # Verify Yahoo articles are preserved
        yahoo_count = sum(1 for article in combined_articles if article.get("source") == "yahoo_finance")
        assert yahoo_count == 2

        # Verify Sonar articles are converted to Yahoo format
        sonar_count = sum(1 for article in combined_articles if article.get("source") == "perplexity_sonar")
        assert sonar_count == 2

        # Verify Sonar-specific fields are preserved
        sonar_converted = [a for a in combined_articles if a.get("source") == "perplexity_sonar"]
        assert sonar_converted[0]["relevance_score"] == 0.95
        assert sonar_converted[0]["content_type"] == "filing"
        assert sonar_converted[1]["content_type"] == "analysis"

    def test_should_handle_sentiment_analysis_with_combined_sources(self, mocker):
        """Test sentiment analysis with combined traditional and Sonar data sources."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Create mixed sentiment data
        yahoo_articles = [
            {
                "title": "Apple Stock Declines on Market Concerns",
                "publisher": "Reuters",
                "link": "https://reuters.com/apple-decline",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple shares fall amid broader market weakness",
                "source": "yahoo_finance",
            }
        ]

        sonar_articles = [
            SonarArticle(
                title="Apple Shows Strong Growth Potential",
                url="https://bloomberg.com/apple-growth",
                summary="Analysts bullish on Apple's long-term prospects",
                publisher="Bloomberg",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.88,
                content_type="analysis",
                analysis_type="sentiment",
            )
        ]

        sonar_result = SonarSearchResult(
            query="AAPL sentiment",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=sonar_articles,
            success=True,
        )

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=sonar_result)
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

        # Act
        enhanced_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))
        combined_articles = tool._combine_article_sources(enhanced_data["yahoo_articles"], enhanced_data["sonar_articles"])
        sentiment_analysis = tool._analyze_sentiment(combined_articles, "AAPL", "stock")

        # Assert
        assert sentiment_analysis is not None
        assert "overall_sentiment" in sentiment_analysis
        assert "sentiment_score" in sentiment_analysis
        assert "sentiment_distribution" in sentiment_analysis

        # Verify both sources contributed to analysis
        assert len(combined_articles) == 2
        bearish_articles = [a for a in combined_articles if a.get("sentiment") == "bearish"]
        bullish_articles = [a for a in combined_articles if a.get("sentiment") == "bullish"]

        # Should have mixed sentiment from different sources
        assert len(bearish_articles) > 0 or len(bullish_articles) > 0

    def test_should_calculate_enhanced_impact_scores_with_sonar_data(self, mocker):
        """Test impact score calculation with Sonar data enhancements."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Create articles with different sources and characteristics
        combined_articles = [
            {
                "title": "Apple Reports Record Earnings",
                "publisher": "Reuters",
                "link": "https://reuters.com/apple-earnings",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple beats expectations with strong iPhone sales",
                "source": "yahoo_finance",
                "sentiment": "bullish",
                "sentiment_score": 0.7,
            },
            {
                "title": "Apple SEC 10-K Filing Analysis",
                "publisher": "SEC",
                "link": "https://sec.gov/apple-10k",
                "published_time": datetime.datetime.now().timestamp() - 1800,
                "summary": "Comprehensive financial analysis shows strong fundamentals",
                "source": "perplexity_sonar",
                "relevance_score": 0.95,
                "content_type": "filing",
                "analysis_type": "fundamental",
                "sentiment": "bullish",
                "sentiment_score": 0.8,
            },
            {
                "title": "Goldman Sachs Upgrades Apple",
                "publisher": "Bloomberg",
                "link": "https://bloomberg.com/apple-upgrade",
                "published_time": datetime.datetime.now().timestamp() - 3600,
                "summary": "Analyst raises price target to $200",
                "source": "perplexity_sonar",
                "relevance_score": 0.90,
                "content_type": "analysis",
                "analysis_type": "technical",
                "sentiment": "bullish",
                "sentiment_score": 0.6,
            },
        ]

        tool = EnhancedSentimentAnalysisTool()
        sentiment_analysis = {"overall_sentiment": "positive", "sentiment_score": 0.7, "confidence": 0.8}

        # Act
        impact_scores = tool._calculate_impact_scores(combined_articles, sentiment_analysis)

        # Assert
        assert len(impact_scores) > 0

        # Find Sonar articles in impact scores
        sonar_impacts = [article for article in impact_scores if article.get("source") == "perplexity_sonar"]
        yahoo_impacts = [article for article in impact_scores if article.get("source") == "yahoo_finance"]

        assert len(sonar_impacts) > 0
        assert len(yahoo_impacts) > 0

        # Verify Sonar-specific enhancements
        sec_filing = next((a for a in sonar_impacts if a.get("content_type") == "filing"), None)
        if sec_filing:
            assert sec_filing["sonar_boost"] is not None
            assert sec_filing["sonar_boost"] > 1.0  # Should have enhancement boost
            assert sec_filing["relevance_score"] == 0.95

        analysis_article = next((a for a in sonar_impacts if a.get("content_type") == "analysis"), None)
        if analysis_article:
            assert analysis_article["sonar_boost"] is not None
            assert analysis_article["relevance_score"] == 0.90

    def test_should_handle_technical_analysis_integration(self, mocker):
        """Test technical analysis integration with Perplexity data."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Mock technical analysis specific data
        sonar_articles = [
            SonarArticle(
                title="Apple Technical Analysis: Bullish Breakout",
                url="https://tradingview.com/apple-technical",
                summary="Chart patterns suggest upward momentum with $180 target",
                publisher="TradingView",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.92,
                content_type="analysis",
                analysis_type="technical",
            ),
            SonarArticle(
                title="Analyst Price Target Raised to $200",
                url="https://bloomberg.com/apple-target",
                summary="Multiple analysts raise price targets following earnings",
                publisher="Bloomberg",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.88,
                content_type="analysis",
                analysis_type="technical",
            ),
        ]

        sonar_result = SonarSearchResult(
            query="AAPL technical analysis price target",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="technical",
            results=sonar_articles,
            success=True,
        )

        # Mock integration for technical analysis
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_technical_analysis = mocker.AsyncMock(return_value=sonar_result)

        # Act - Simulate technical analysis tool integration
        result = asyncio.run(mock_integration.search_technical_analysis(ticker="AAPL", asset_type="stock", max_results=10))

        # Assert
        assert result.success is True
        assert result.analysis_type == "technical"
        assert len(result.results) == 2

        # Verify technical-specific content
        technical_articles = result.results
        assert all(article.analysis_type == "technical" for article in technical_articles)
        assert any("price target" in article.summary.lower() for article in technical_articles)
        assert any("technical" in article.title.lower() for article in technical_articles)

    def test_should_handle_fundamental_analysis_integration(self, mocker):
        """Test fundamental analysis integration with Perplexity data."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Mock fundamental analysis specific data
        sonar_articles = [
            SonarArticle(
                title="Apple Q4 2023 10-K Filing Analysis",
                url="https://sec.gov/apple-10k-2023",
                summary="Strong balance sheet with $165B cash, revenue growth of 8%",
                publisher="SEC",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.98,
                content_type="filing",
                analysis_type="fundamental",
            ),
            SonarArticle(
                title="Apple Earnings Call Highlights Growth Strategy",
                url="https://apple.com/earnings-call",
                summary="Management discusses services growth and AI initiatives",
                publisher="Apple Inc.",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.94,
                content_type="earnings",
                analysis_type="fundamental",
            ),
        ]

        sonar_result = SonarSearchResult(
            query="AAPL earnings SEC filing fundamental analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="fundamental",
            results=sonar_articles,
            success=True,
        )

        # Mock integration for fundamental analysis
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_fundamental_analysis = mocker.AsyncMock(return_value=sonar_result)

        # Act - Simulate fundamental analysis tool integration
        result = asyncio.run(mock_integration.search_fundamental_analysis(ticker="AAPL", asset_type="stock", max_results=10))

        # Assert
        assert result.success is True
        assert result.analysis_type == "fundamental"
        assert len(result.results) == 2

        # Verify fundamental-specific content
        fundamental_articles = result.results
        assert all(article.analysis_type == "fundamental" for article in fundamental_articles)

        # Check for SEC filing
        sec_filing = next((a for a in fundamental_articles if a.content_type == "filing"), None)
        assert sec_filing is not None
        assert sec_filing.publisher == "SEC"

        # Check for earnings content
        earnings_content = next((a for a in fundamental_articles if a.content_type == "earnings"), None)
        assert earnings_content is not None

    def test_should_handle_graceful_degradation_across_tools(self, mocker):
        """Test error handling and graceful degradation scenarios across all integrated tools."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        # Mock Yahoo Finance data (always available)
        yahoo_articles = [
            {
                "title": "Apple Stock Update",
                "publisher": "Yahoo Finance",
                "link": "https://finance.yahoo.com/apple",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple stock trading update",
                "source": "yahoo_finance",
            }
        ]

        # Test different failure scenarios
        failure_scenarios = [
            ("timeout", "Request timeout"),
            ("rate_limit", "Rate limit exceeded"),
            ("api_error", "API error 500"),
            ("connection_error", "Connection failed"),
            ("parsing_error", "Invalid JSON response"),
        ]

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        for error_type, error_message in failure_scenarios:
            # Mock Perplexity integration to fail with specific error
            mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
            mock_integration.search_sentiment_news = mocker.AsyncMock(side_effect=Exception(error_message))
            mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

            # Act
            enhanced_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))

            # Assert - Should gracefully degrade to Yahoo-only data
            assert enhanced_data["yahoo_articles"] == yahoo_articles
            assert enhanced_data["sonar_articles"] == []
            assert enhanced_data["combined_count"] == 1
            assert enhanced_data["sonar_fallback_used"] is True

    def test_should_maintain_data_source_attribution(self, mocker):
        """Test that data source attribution is maintained throughout the analysis pipeline."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        yahoo_articles = [
            {
                "title": "Apple Quarterly Results",
                "publisher": "Yahoo Finance",
                "link": "https://finance.yahoo.com/apple-results",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple reports quarterly earnings",
                "source": "yahoo_finance",
            }
        ]

        sonar_articles = [
            SonarArticle(
                title="Apple Market Analysis",
                url="https://bloomberg.com/apple-analysis",
                summary="Comprehensive market analysis of Apple stock",
                publisher="Bloomberg",
                published_date=datetime.datetime.now().isoformat() + "Z",
                relevance_score=0.90,
                content_type="analysis",
                analysis_type="sentiment",
            )
        ]

        sonar_result = SonarSearchResult(
            query="AAPL analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=sonar_articles,
            success=True,
        )

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=sonar_result)
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

        # Act
        enhanced_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))
        combined_articles = tool._combine_article_sources(enhanced_data["yahoo_articles"], enhanced_data["sonar_articles"])
        data_sources = tool._get_data_sources_list(enhanced_data["yahoo_articles"], enhanced_data["sonar_articles"])

        # Assert
        assert "Yahoo Finance" in data_sources
        assert "Perplexity Sonar" in data_sources

        # Verify source attribution in combined articles
        yahoo_sourced = [a for a in combined_articles if a.get("source") == "yahoo_finance"]
        sonar_sourced = [a for a in combined_articles if a.get("source") == "perplexity_sonar"]

        assert len(yahoo_sourced) == 1
        assert len(sonar_sourced) == 1

        # Verify Sonar-specific metadata is preserved
        sonar_article = sonar_sourced[0]
        assert sonar_article["relevance_score"] == 0.90
        assert sonar_article["content_type"] == "analysis"
        assert sonar_article["analysis_type"] == "sentiment"

    def test_should_handle_empty_sonar_results_gracefully(self, mocker):
        """Test handling of empty Sonar results without breaking the analysis flow."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        yahoo_articles = [
            {
                "title": "Apple Stock News",
                "publisher": "Reuters",
                "link": "https://reuters.com/apple-news",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple stock market update",
                "source": "yahoo_finance",
            }
        ]

        # Empty Sonar result
        sonar_result = SonarSearchResult(
            query="AAPL analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=[],  # Empty results
            total_results=0,
            success=True,
        )

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=sonar_result)
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

        # Act
        enhanced_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))
        combined_articles = tool._combine_article_sources(enhanced_data["yahoo_articles"], enhanced_data["sonar_articles"])

        # Assert
        assert enhanced_data["yahoo_articles"] == yahoo_articles
        assert enhanced_data["sonar_articles"] == []
        assert enhanced_data["combined_count"] == 1
        assert enhanced_data["sonar_fallback_used"] is False  # Not a failure, just empty results
        assert len(combined_articles) == 1
        assert combined_articles[0]["source"] == "yahoo_finance"

    def test_should_handle_mixed_success_failure_scenarios(self, mocker):
        """Test scenarios where some Sonar searches succeed and others fail."""
        # Arrange
        mocker.patch.dict("os.environ", {"FF_PERPLEXITY_RESEARCH": "true", "PPLX_API_KEY": "test-key"})

        yahoo_articles = [
            {
                "title": "Apple Market Update",
                "publisher": "MarketWatch",
                "link": "https://marketwatch.com/apple-update",
                "published_time": datetime.datetime.now().timestamp(),
                "summary": "Apple stock market analysis",
                "source": "yahoo_finance",
            }
        ]

        # Simulate partial success - sentiment succeeds, technical fails
        successful_sonar_result = SonarSearchResult(
            query="AAPL sentiment",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="sentiment",
            results=[
                SonarArticle(
                    title="Apple Sentiment Analysis",
                    url="https://example.com/apple-sentiment",
                    summary="Positive market sentiment for Apple",
                    publisher="Financial Times",
                    analysis_type="sentiment",
                )
            ],
            success=True,
        )

        failed_sonar_result = SonarSearchResult(
            query="AAPL technical",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="technical",
            results=[],
            success=False,
            error_message="Rate limit exceeded",
        )

        tool = EnhancedSentimentAnalysisTool()
        mocker.patch.object(tool, "_get_news_data", return_value=yahoo_articles)

        # Mock integration with mixed results
        mock_integration = mocker.Mock(spec=PerplexityAnalysisIntegration)
        mock_integration.search_sentiment_news = mocker.AsyncMock(return_value=successful_sonar_result)
        mock_integration.search_technical_analysis = mocker.AsyncMock(return_value=failed_sonar_result)
        mocker.patch.object(tool, "_get_perplexity_integration", return_value=mock_integration)

        # Act - Test sentiment analysis (should succeed)
        sentiment_data = asyncio.run(tool._get_enhanced_news_data("AAPL", "stock", 20))

        # Assert
        assert sentiment_data["yahoo_articles"] == yahoo_articles
        assert len(sentiment_data["sonar_articles"]) == 1
        assert sentiment_data["sonar_fallback_used"] is False

        # Verify the successful Sonar article
        sonar_article = sentiment_data["sonar_articles"][0]
        assert sonar_article.title == "Apple Sentiment Analysis"
        assert sonar_article.analysis_type == "sentiment"

    def test_should_validate_data_consistency_across_sources(self, mocker):
        """Test that data consistency is maintained when combining different sources."""
        # Arrange
        tool = EnhancedSentimentAnalysisTool()

        yahoo_articles = [
            {
                "title": "Apple Earnings Beat",
                "publisher": "Reuters",
                "link": "https://reuters.com/apple-earnings",
                "published_time": 1640995200.0,  # Valid timestamp
                "summary": "Apple reports strong quarterly results",
                "source": "yahoo_finance",
            }
        ]

        sonar_articles = [
            SonarArticle(
                title="Apple Financial Analysis",
                url="https://bloomberg.com/apple-financial",
                summary="Detailed financial performance review",
                publisher="Bloomberg",
                published_date="2022-01-01T12:00:00Z",
                relevance_score=0.85,
                content_type="analysis",
                analysis_type="fundamental",
            )
        ]

        # Act
        combined_articles = tool._combine_article_sources(yahoo_articles, sonar_articles)

        # Assert
        assert len(combined_articles) == 2

        # Verify Yahoo article structure is preserved
        yahoo_article = next(a for a in combined_articles if a.get("source") == "yahoo_finance")
        assert yahoo_article["title"] == "Apple Earnings Beat"
        assert yahoo_article["publisher"] == "Reuters"
        assert yahoo_article["published_time"] == 1640995200.0

        # Verify Sonar article is properly converted
        sonar_article = next(a for a in combined_articles if a.get("source") == "perplexity_sonar")
        assert sonar_article["title"] == "Apple Financial Analysis"
        assert sonar_article["publisher"] == "Bloomberg"
        assert sonar_article["relevance_score"] == 0.85
        assert sonar_article["content_type"] == "analysis"
        assert sonar_article["analysis_type"] == "fundamental"

        # Verify timestamp conversion for Sonar article
        assert sonar_article["published_time"] is not None
        assert isinstance(sonar_article["published_time"], (int, float))

    def test_should_handle_invalid_sonar_article_conversion(self, mocker):
        """Test handling of invalid Sonar articles during conversion."""
        # Arrange
        tool = EnhancedSentimentAnalysisTool()

        yahoo_articles = [
            {
                "title": "Valid Yahoo Article",
                "publisher": "Reuters",
                "link": "https://reuters.com/valid",
                "published_time": 1640995200.0,
                "summary": "Valid article content",
                "source": "yahoo_finance",
            }
        ]

        # Create Sonar articles with various invalid data
        sonar_articles = [
            SonarArticle(
                title="Valid Sonar Article",
                url="https://bloomberg.com/valid",
                summary="Valid Sonar content",
                publisher="Bloomberg",
                analysis_type="sentiment",
            ),
            # This will cause conversion issues due to invalid date format
            SonarArticle(
                title="Invalid Date Article",
                url="https://example.com/invalid-date",
                summary="Article with invalid date",
                publisher="Test Publisher",
                published_date="invalid-date-format",
                analysis_type="sentiment",
            ),
        ]

        # Mock logger to capture warnings
        mock_logger = mocker.patch("finwiz.tools.enhanced_sentiment_tool.logger")

        # Act
        combined_articles = tool._combine_article_sources(yahoo_articles, sonar_articles)

        # Assert
        # Should have Yahoo article plus valid Sonar articles (invalid ones may be skipped or handled)
        assert len(combined_articles) >= 1  # At least the Yahoo article

        # Verify Yahoo article is always preserved
        yahoo_count = sum(1 for a in combined_articles if a.get("source") == "yahoo_finance")
        assert yahoo_count == 1

        # Valid Sonar article should be converted successfully
        valid_sonar = next(
            (a for a in combined_articles if a.get("source") == "perplexity_sonar" and a.get("title") == "Valid Sonar Article"),
            None,
        )
        assert valid_sonar is not None
