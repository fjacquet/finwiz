"""Unit tests for StandardizedSentimentTool."""

from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool


class TestStandardizedSentimentTool:
    """Test suite for StandardizedSentimentAnalysisTool following FinWiz standards."""

    def setup_method(self):
        """Set up test instance before each test method."""
        self.tool = StandardizedSentimentAnalysisTool()

    def test_should_return_analysis_when_valid_input(self):
        """Test that tool returns analysis with valid input."""
        # Act
        result = self.tool._run(symbol="AAPL", asset_class="stock")

        # Assert
        assert isinstance(result, dict)
        assert "symbol" in result
        assert result["symbol"] == "AAPL"

    def test_should_return_sentiment_analysis_when_valid_input(self):
        """Test successful sentiment analysis with valid input."""
        # Act
        result = self.tool._run(symbol="AAPL", asset_class="stock", max_articles=10)

        # Assert
        assert isinstance(result, dict)
        assert "symbol" in result
        assert "asset_class" in result
        assert result["symbol"] == "AAPL"
        assert result["asset_class"] == "stock"

    def test_should_handle_no_articles_gracefully(self):
        """Test graceful handling when no articles are found."""
        # Act
        result = self.tool._run(symbol="NONEXISTENT", asset_class="stock")

        # Assert
        assert isinstance(result, dict)
        assert "symbol" in result
        assert result["symbol"] == "NONEXISTENT"

    def test_should_validate_input_parameters(self):
        """Test input parameter validation."""
        # Act & Assert - Empty symbol should be handled
        result = self.tool._run(symbol="", asset_class="stock")
        assert isinstance(result, dict)

    def test_should_handle_different_asset_classes(self):
        """Test handling of different asset classes."""
        # Test stock
        result_stock = self.tool._run(symbol="AAPL", asset_class="stock")
        assert result_stock["asset_class"] == "stock"

        # Test ETF
        result_etf = self.tool._run(symbol="SPY", asset_class="etf")
        assert result_etf["asset_class"] == "etf"

        # Test crypto
        result_crypto = self.tool._run(symbol="BTC", asset_class="crypto")
        assert result_crypto["asset_class"] == "crypto"

    def test_should_return_expected_structure(self):
        """Test that the tool returns expected data structure."""
        # Act
        result = self.tool._run(symbol="AAPL", asset_class="stock")

        # Assert
        assert isinstance(result, dict)
        expected_keys = ["symbol", "asset_class", "mean_score", "counts"]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
