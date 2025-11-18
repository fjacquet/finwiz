"""
Tests for Perplexity integration wrapper.

This module tests the PerplexityAnalysisIntegration wrapper class, including
JSON response parsing, error handling, and SonarArticle model validation.
"""

import asyncio
import json
import os

import pytest
from pydantic import ValidationError

from finwiz.schemas.perplexity import (
    PerplexityConfig,
    SonarArticle,
    SonarSearchResult,
)
from finwiz.tools.perplexity_analysis_integration import (
    PerplexityAnalysisIntegration,
)


class TestPerplexityIntegrationWrapper:
    """Test Perplexity integration wrapper functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.config = PerplexityConfig(api_key="test-key", timeout_seconds=30.0, max_retries=3, backoff_factor=2.0, rate_limit_buffer=5)

    def test_should_initialize_with_api_key_available(self, mocker):
        """Test initialization when API key is available."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        # Act
        integration = PerplexityAnalysisIntegration(self.config)

        # Assert
        assert integration.is_available is True
        assert integration.config.api_key == "test-key"

    def test_should_initialize_without_api_key(self, mocker):
        """Test initialization when API key is missing."""
        # Arrange
        mocker.patch.dict(os.environ, {}, clear=True)

        # Mock the config creation to avoid validation error
        mock_config = PerplexityConfig(
            api_key="dummy",  # Provide dummy key to pass validation
            timeout_seconds=30.0,
            max_retries=3,
            backoff_factor=2.0,
            rate_limit_buffer=5,
        )

        # Act - Create integration but it should detect missing env var
        integration = PerplexityAnalysisIntegration(mock_config)

        # Assert
        assert integration.is_available is False

    def test_should_create_default_config_when_none_provided(self, mocker):
        """Test default configuration creation."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        # Act
        integration = PerplexityAnalysisIntegration()

        # Assert
        assert integration.config is not None
        assert integration.config.api_key == "test-key"
        assert integration.config.timeout_seconds == 30.0
        assert integration.config.max_retries == 3

    def test_should_search_financial_news_successfully(self, mocker):
        """Test successful financial news search."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        # Mock the search API response directly
        mock_search_response = {
            "results": [
                {
                    "title": "Apple Reports Strong Q4 Earnings",
                    "url": "https://example.com/apple-earnings",
                    "snippet": "Apple exceeded expectations with record revenue",
                    "date": "2024-01-01",
                    "last_updated": "2024-01-01T12:00:00Z",
                }
            ]
        }

        mock_http_response = mocker.Mock()
        mock_http_response.json.return_value = mock_search_response
        mock_http_response.raise_for_status = mocker.Mock()

        # Patch requests.post to avoid actual HTTP calls
        mocker.patch("requests.post", return_value=mock_http_response)

        integration = PerplexityAnalysisIntegration(self.config)

        # Act
        result = asyncio.run(integration.search_financial_news(query="AAPL earnings analysis", ticker="AAPL", asset_type="stock", analysis_type="sentiment", max_results=10))

        # Assert
        assert isinstance(result, SonarSearchResult)
        assert result.success is True
        assert result.ticker == "AAPL"
        assert result.asset_type == "stock"
        assert result.analysis_type == "sentiment"
        assert len(result.results) == 1
        assert result.results[0].title == "Apple Reports Strong Q4 Earnings"
        assert result.results[0].publisher == "Example"  # Extracted from example.com domain

    def test_should_handle_api_key_missing_gracefully(self, mocker):
        """Test graceful handling when API key is missing."""
        # Arrange
        mocker.patch.dict(os.environ, {}, clear=True)

        # Create config with dummy key to pass validation, but integration will detect missing env var
        config = PerplexityConfig(api_key="dummy", timeout_seconds=30.0, max_retries=3, backoff_factor=2.0, rate_limit_buffer=5)

        integration = PerplexityAnalysisIntegration(config)

        # Act
        result = asyncio.run(integration.search_financial_news(query="AAPL analysis", ticker="AAPL", asset_type="stock"))

        # Assert
        assert isinstance(result, SonarSearchResult)
        assert result.success is False
        assert result.error_message == "Perplexity API key not available"
        assert len(result.results) == 0

    def test_should_parse_perplexity_response_with_citations(self):
        """Test JSON response parsing with citations."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        raw_response = json.dumps(
            {
                "citations": [
                    {
                        "title": "Apple Stock Analysis",
                        "url": "https://bloomberg.com/apple-analysis",
                        "snippet": "Technical analysis shows bullish trend",
                        "publisher": "Bloomberg",
                    },
                    {
                        "title": "Market Update",
                        "url": "https://reuters.com/market-update",
                        "text": "Market shows positive sentiment",
                        "source": "Reuters",
                    },
                ]
            }
        )

        # Act
        articles = integration._parse_perplexity_response(raw_response, "sentiment", "AAPL")

        # Assert
        assert len(articles) == 2
        assert isinstance(articles[0], SonarArticle)
        assert articles[0].title == "Apple Stock Analysis"
        assert articles[0].publisher == "Bloomberg"
        assert articles[0].analysis_type == "sentiment"
        assert articles[1].publisher == "Reuters"

    def test_should_parse_response_with_choices_citations(self):
        """Test parsing response where citations are nested in choices."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        raw_response = json.dumps(
            {
                "choices": [
                    {
                        "citations": [
                            {
                                "title": "SEC Filing Analysis",
                                "url": "https://sec.gov/filing-123",
                                "snippet": "Company reports strong fundamentals",
                            }
                        ]
                    }
                ]
            }
        )

        # Act
        articles = integration._parse_perplexity_response(raw_response, "fundamental", "AAPL")

        # Assert
        assert len(articles) == 1
        assert articles[0].title == "SEC Filing Analysis"
        assert articles[0].analysis_type == "fundamental"

    def test_should_handle_invalid_json_response(self):
        """Test handling of invalid JSON responses."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Act
        articles = integration._parse_perplexity_response("invalid json", "sentiment", "AAPL")

        # Assert
        assert articles == []

    def test_should_handle_response_without_citations(self):
        """Test handling of response without citations."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        raw_response = json.dumps({"choices": [{"message": {"content": "No citations available"}}]})

        # Act
        articles = integration._parse_perplexity_response(raw_response, "sentiment", "AAPL")

        # Assert
        assert articles == []

    def test_should_create_sonar_article_from_citation(self):
        """Test SonarArticle creation from citation data."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        citation = {
            "title": "Apple Earnings Report",
            "url": "https://example.com/apple-earnings",
            "snippet": "Apple reports record quarterly earnings",
            "publisher": "Financial Times",
        }

        # Act
        article = integration._create_sonar_article(citation, "fundamental", 0)

        # Assert
        assert isinstance(article, SonarArticle)
        assert article.title == "Apple Earnings Report"
        assert str(article.url) == "https://example.com/apple-earnings"
        assert article.summary == "Apple reports record quarterly earnings"
        assert article.publisher == "Financial Times"
        assert article.analysis_type == "fundamental"
        assert article.relevance_score == 1.0  # First article gets max relevance

    def test_should_skip_citation_without_url(self):
        """Test skipping citations without URLs."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        citation = {"title": "Invalid Citation", "snippet": "No URL provided"}

        # Act
        article = integration._create_sonar_article(citation, "sentiment", 0)

        # Assert
        assert article is None

    def test_should_extract_publisher_from_url_when_missing(self):
        """Test publisher extraction from URL when not provided."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        citation = {
            "title": "Market Analysis",
            "url": "https://www.bloomberg.com/news/article",
            "snippet": "Market shows positive trends",
        }

        # Act
        article = integration._create_sonar_article(citation, "technical", 0)

        # Assert
        assert article is not None
        assert article.publisher == "Bloomberg"

    def test_should_determine_content_type_from_url(self):
        """Test content type determination from URL patterns."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test SEC filing
        sec_url = "https://sec.gov/Archives/edgar/data/filing.pdf"
        content_type = integration._determine_content_type(sec_url, "SEC Filing")
        assert content_type == "filing"

        # Test earnings report
        earnings_url = "https://example.com/earnings-report"
        content_type = integration._determine_content_type(earnings_url, "Q4 Earnings Report")
        assert content_type == "earnings"

        # Test regular news
        news_url = "https://reuters.com/business/news"
        content_type = integration._determine_content_type(news_url, "Market News")
        assert content_type == "news"

    def test_should_calculate_relevance_score_by_position(self):
        """Test relevance score calculation based on citation position."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        citation = {"title": "Test Article", "url": "https://example.com/test", "snippet": "Test content"}

        # Act & Assert
        article_0 = integration._create_sonar_article(citation, "sentiment", 0)
        assert article_0.relevance_score == 1.0

        article_5 = integration._create_sonar_article(citation, "sentiment", 5)
        assert article_5.relevance_score == 0.5

        article_10 = integration._create_sonar_article(citation, "sentiment", 10)
        assert article_10.relevance_score == 0.1  # Minimum relevance

    def test_should_create_enhanced_query_for_different_analysis_types(self):
        """Test enhanced query creation for different analysis types."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test sentiment analysis
        sentiment_query = integration._create_enhanced_query("financial news", "AAPL", "stock", "sentiment")
        assert "sentiment" in sentiment_query
        assert "market reaction" in sentiment_query
        assert "AAPL" in sentiment_query

        # Test technical analysis
        technical_query = integration._create_enhanced_query("price analysis", "AAPL", "stock", "technical")
        assert "technical analysis" in technical_query
        assert "price target" in technical_query

        # Test fundamental analysis
        fundamental_query = integration._create_enhanced_query("company analysis", "AAPL", "stock", "fundamental")
        assert "earnings" in fundamental_query
        assert "SEC filing" in fundamental_query

    def test_should_get_appropriate_search_filters(self):
        """Test search filter selection based on analysis type."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test fundamental analysis filters (SEC filings)
        fundamental_filters = integration._get_search_filters("fundamental")
        assert "sec.gov" in fundamental_filters.get("site", "")

        # Test other analysis types (financial news)
        sentiment_filters = integration._get_search_filters("sentiment")
        assert "bloomberg.com" in sentiment_filters.get("site", "")

    def test_should_retry_on_rate_limit_error(self, mocker):
        """Test retry logic for rate limit errors."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        integration = PerplexityAnalysisIntegration(self.config)

        # Mock HTTP responses: first fails with 429, then succeeds
        mock_error_response = mocker.Mock()
        mock_error_response.raise_for_status.side_effect = Exception("429 Rate limit exceeded")

        mock_success_response = mocker.Mock()
        mock_success_response.json.return_value = {"results": []}
        mock_success_response.raise_for_status = mocker.Mock()

        mocker.patch("requests.post", side_effect=[mock_error_response, mock_success_response])

        # Mock sleep to avoid actual delays
        mocker.patch("asyncio.sleep", new_callable=mocker.AsyncMock)

        # Act
        result = asyncio.run(integration.search_financial_news(query="test query", ticker="AAPL", asset_type="stock"))

        # Assert
        assert result.success is True
        assert result.retry_count == 1

    def test_should_handle_timeout_error(self, mocker):
        """Test handling of timeout errors."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        integration = PerplexityAnalysisIntegration(self.config)

        # Mock HTTP request timeout
        mocker.patch("requests.post", side_effect=Exception("Request timeout"))

        # Act
        result = asyncio.run(integration.search_financial_news(query="test query", ticker="AAPL", asset_type="stock"))

        # Assert
        assert result.success is False
        assert "timeout" in result.error_message.lower()

    def test_should_handle_connection_error(self, mocker):
        """Test handling of connection errors."""
        # Arrange
        mocker.patch.dict(os.environ, {"PPLX_API_KEY": "test-key"})

        integration = PerplexityAnalysisIntegration(self.config)

        # Mock HTTP connection error
        mocker.patch("requests.post", side_effect=Exception("Connection failed"))

        # Act
        result = asyncio.run(integration.search_financial_news(query="test query", ticker="AAPL", asset_type="stock"))

        # Assert
        assert result.success is False
        assert "connection" in result.error_message.lower()

    def test_should_classify_error_types_correctly(self):
        """Test error type classification."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test rate limit error
        rate_limit_error = Exception("Rate limit exceeded")
        error_type = integration._classify_error(rate_limit_error)
        assert error_type == "rate_limit"

        # Test timeout error
        timeout_error = Exception("Request timeout")
        error_type = integration._classify_error(timeout_error)
        assert error_type == "timeout"

        # Test connection error
        connection_error = Exception("Connection failed")
        error_type = integration._classify_error(connection_error)
        assert error_type == "connection_error"

        # Test unknown error
        unknown_error = Exception("Unknown issue")
        error_type = integration._classify_error(unknown_error)
        assert error_type == "unknown_error"

    def test_should_extract_http_status_from_error(self):
        """Test HTTP status code extraction from errors."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test 429 status
        error_429 = Exception("HTTP 429: Too Many Requests")
        status = integration._extract_http_status(error_429)
        assert status == 429

        # Test 500 status
        error_500 = Exception("Server error 500")
        status = integration._extract_http_status(error_500)
        assert status == 500

        # Test no status
        error_no_status = Exception("Generic error")
        status = integration._extract_http_status(error_no_status)
        assert status is None

    def test_should_extract_ticker_from_query(self):
        """Test ticker extraction from query strings."""
        # Arrange
        integration = PerplexityAnalysisIntegration(self.config)

        # Test simple ticker
        ticker = integration._extract_ticker_from_query("AAPL financial news")
        assert ticker == "AAPL"

        # Test ticker with dash
        ticker = integration._extract_ticker_from_query("BRK-A earnings report")
        assert ticker == "BRK-A"

        # Test no ticker
        ticker = integration._extract_ticker_from_query("general market news")
        assert ticker is None


class TestSonarArticleValidation:
    """Test SonarArticle model validation and serialization."""

    def test_should_create_valid_sonar_article(self):
        """Test creation of valid SonarArticle."""
        # Arrange & Act
        article = SonarArticle(
            title="Apple Reports Strong Earnings",
            url="https://example.com/apple-earnings",
            summary="Apple exceeded expectations with record revenue",
            publisher="Reuters",
            published_date="2022-01-01T12:00:00Z",
            relevance_score=0.95,
            content_type="earnings",
            analysis_type="fundamental",
        )

        # Assert
        assert article.title == "Apple Reports Strong Earnings"
        assert str(article.url) == "https://example.com/apple-earnings"
        assert article.publisher == "Reuters"
        assert article.relevance_score == 0.95
        assert article.content_type == "earnings"
        assert article.analysis_type == "fundamental"

    def test_should_validate_title_length(self):
        """Test title length validation."""
        # Test empty title
        with pytest.raises(ValidationError):
            SonarArticle(title="", url="https://example.com/test")

        # Test title too long
        with pytest.raises(ValidationError):
            SonarArticle(
                title="x" * 501,  # Exceeds 500 character limit
                url="https://example.com/test",
            )

    def test_should_validate_url_format(self):
        """Test URL format validation."""
        # Test invalid URL
        with pytest.raises(ValidationError):
            SonarArticle(title="Test Article", url="not-a-valid-url")

    def test_should_validate_relevance_score_range(self):
        """Test relevance score range validation."""
        # Test negative score
        with pytest.raises(ValidationError):
            SonarArticle(title="Test Article", url="https://example.com/test", relevance_score=-0.1)

        # Test score too high
        with pytest.raises(ValidationError):
            SonarArticle(title="Test Article", url="https://example.com/test", relevance_score=1.1)

    def test_should_validate_content_type_enum(self):
        """Test content type enum validation."""
        # Test invalid content type
        with pytest.raises(ValidationError):
            SonarArticle(title="Test Article", url="https://example.com/test", content_type="invalid_type")

    def test_should_validate_analysis_type_enum(self):
        """Test analysis type enum validation."""
        # Test invalid analysis type
        with pytest.raises(ValidationError):
            SonarArticle(title="Test Article", url="https://example.com/test", analysis_type="invalid_analysis")

    def test_should_strip_whitespace_from_strings(self):
        """Test automatic whitespace stripping."""
        # Arrange & Act
        article = SonarArticle(title="  Apple Earnings  ", url="https://example.com/test", summary="  Summary with spaces  ", publisher="  Reuters  ")

        # Assert
        assert article.title == "Apple Earnings"
        assert article.summary == "Summary with spaces"
        assert article.publisher == "Reuters"

    def test_should_validate_published_date_format(self):
        """Test published date format validation."""
        # Test valid ISO format
        article = SonarArticle(title="Test Article", url="https://example.com/test", published_date="2022-01-01T12:00:00Z")
        assert article.published_date == "2022-01-01T12:00:00Z"

        # Test invalid format (should still accept but may log warning)
        article = SonarArticle(title="Test Article", url="https://example.com/test", published_date="invalid-date")
        assert article.published_date == "invalid-date"


class TestSonarSearchResultValidation:
    """Test SonarSearchResult model validation and serialization."""

    def test_should_create_valid_search_result(self):
        """Test creation of valid SonarSearchResult."""
        # Arrange
        articles = [SonarArticle(title="Apple Earnings", url="https://example.com/apple", analysis_type="fundamental")]

        # Act
        result = SonarSearchResult(
            query="AAPL earnings analysis",
            ticker="AAPL",
            asset_type="stock",
            analysis_type="fundamental",
            results=articles,
            total_results=1,
            search_time_ms=250,
            success=True,
        )

        # Assert
        assert result.query == "AAPL earnings analysis"
        assert result.ticker == "AAPL"
        assert result.asset_type == "stock"
        assert result.analysis_type == "fundamental"
        assert len(result.results) == 1
        assert result.success is True

    def test_should_validate_ticker_format(self):
        """Test ticker format validation and normalization."""
        # Test valid ticker - should be normalized to uppercase
        result = SonarSearchResult(
            query="test query",
            ticker="AAPL",  # Already uppercase
            asset_type="stock",
            analysis_type="sentiment",
        )
        assert result.ticker == "AAPL"

        # Test invalid ticker
        with pytest.raises(ValidationError):
            SonarSearchResult(query="test query", ticker="invalid_ticker_too_long", asset_type="stock", analysis_type="sentiment")

    def test_should_validate_asset_type_enum(self):
        """Test asset type enum validation."""
        # Test invalid asset type
        with pytest.raises(ValidationError):
            SonarSearchResult(query="test query", ticker="AAPL", asset_type="invalid_asset", analysis_type="sentiment")

    def test_should_validate_non_negative_integers(self):
        """Test validation of non-negative integer fields."""
        # Test negative total_results
        with pytest.raises(ValidationError):
            SonarSearchResult(query="test query", ticker="AAPL", asset_type="stock", analysis_type="sentiment", total_results=-1)

        # Test negative search_time_ms
        with pytest.raises(ValidationError):
            SonarSearchResult(query="test query", ticker="AAPL", asset_type="stock", analysis_type="sentiment", search_time_ms=-100)
