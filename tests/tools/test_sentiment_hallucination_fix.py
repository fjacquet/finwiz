"""
Test to ensure sentiment analysis tools don't generate hallucinated URLs.

This test verifies that the fix for hallucinated URLs in sentiment analysis
is working correctly and prevents fake news articles from being generated.
"""

from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool


class TestSentimentHallucinationFix:
    """Test that sentiment tools don't generate fake URLs."""

    def test_should_not_generate_fake_urls(self):
        """Test that sentiment analysis doesn't generate hallucinated URLs."""
        # Arrange
        tool = StandardizedSentimentAnalysisTool()

        # Act
        result = tool._run(symbol="MSFT", asset_class="stock")

        # Assert
        assert isinstance(result, dict)
        assert "top_pos" in result
        assert "top_neg" in result

        # Verify no fake URLs are generated
        for article in result["top_pos"]:
            if "url" in article:
                url = article["url"]
                # Check for obvious fake URL patterns
                assert "xyz12345" not in url, f"Found fake URL pattern in: {url}"
                assert not url.endswith(f"/{article.get('symbol', '').lower()}-challenges"), f"Found templated fake URL: {url}"

        for article in result["top_neg"]:
            if "url" in article:
                url = article["url"]
                # Check for obvious fake URL patterns
                assert "xyz12345" not in url, f"Found fake URL pattern in: {url}"
                assert not url.endswith(f"/{article.get('symbol', '').lower()}-challenges"), f"Found templated fake URL: {url}"

    def test_should_return_empty_lists_when_no_real_data(self, mocker):
        """Test that tool returns empty lists instead of fake data when no real sources available."""
        # Arrange
        tool = StandardizedSentimentAnalysisTool()

        # Mock the news collection to return no articles
        mocker.patch.object(tool, "_collect_news_articles", return_value=[])

        # Act
        result = tool._run(symbol="TESTFAKE", asset_class="stock")

        # Assert
        assert isinstance(result, dict)
        assert result["top_pos"] == []
        assert result["top_neg"] == []
        assert result["mean_score"] == 0.0
        assert result["counts"]["pos"] == 0
        assert result["counts"]["neg"] == 0
        assert result["counts"]["neu"] == 0

    def test_should_not_use_deprecated_sample_methods(self):
        """Test that deprecated sample article methods return empty lists."""
        # Arrange
        tool = StandardizedSentimentAnalysisTool()

        # Act & Assert
        financial_articles = tool._create_sample_financial_articles("MSFT", "test")
        crypto_articles = tool._create_sample_crypto_articles("BTC", "test")
        general_articles = tool._create_sample_general_articles("MSFT", "test")
        sample_articles = tool._create_sample_articles("MSFT", "stock")

        # All should return empty lists now
        assert financial_articles == []
        assert crypto_articles == []
        assert general_articles == []
        assert sample_articles == []

    def test_should_handle_different_asset_classes_without_fake_data(self, mocker):
        """Test that all asset classes return empty data instead of fake articles."""
        # Arrange
        tool = StandardizedSentimentAnalysisTool()

        # Mock the news collection to return no articles for all asset classes
        mocker.patch.object(tool, "_collect_news_articles", return_value=[])

        # Act & Assert for different asset classes
        for asset_class in ["stock", "etf", "crypto"]:
            result = tool._run(symbol="TEST", asset_class=asset_class)

            assert isinstance(result, dict)
            assert result["top_pos"] == []
            assert result["top_neg"] == []

            # Verify no articles contain fake URL patterns
            all_articles = result["top_pos"] + result["top_neg"]
            for article in all_articles:
                if "url" in article and article["url"]:
                    url = article["url"]
                    # Should not contain obvious fake patterns
                    assert "xyz12345" not in url
                    assert not any(fake_pattern in url for fake_pattern in ["-challenges", "-upgrade", "-analysis", "-institutional-adoption"] if url.endswith(fake_pattern))
