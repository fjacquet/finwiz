"""Integration tests for stock analysis workflow."""

import pytest

from finwiz.crews.stock_crew.stock_crew import StockCrew


@pytest.mark.integration
class TestStockAnalysisFlow:
    """Integration tests for complete stock analysis workflow."""

    def test_should_complete_full_analysis_when_valid_ticker_provided(self, test_date_inputs):
        """Test complete stock analysis flow with real API calls."""
        # Arrange
        crew = StockCrew().crew()
        inputs = {**test_date_inputs, "ticker": "AAPL"}

        # Act
        result = crew.kickoff(inputs=inputs)

        # Assert
        assert result is not None
        assert "AAPL" in str(result)
        # Add more specific assertions based on expected output structure

    @pytest.mark.slow
    def test_should_handle_multiple_tickers_sequentially(self, test_date_inputs):
        """Test analysis of multiple tickers in sequence."""
        # Arrange
        tickers = ["AAPL", "MSFT", "GOOGL"]
        crew = StockCrew().crew()
        results = []

        # Act
        for ticker in tickers:
            inputs = {**test_date_inputs, "ticker": ticker}
            result = crew.kickoff(inputs=inputs)
            results.append(result)

        # Assert
        assert len(results) == 3
        for i, result in enumerate(results):
            assert tickers[i] in str(result)

    def test_should_fail_gracefully_with_invalid_ticker(self, test_date_inputs):
        """Test graceful failure handling with invalid ticker."""
        # Arrange
        crew = StockCrew().crew()
        inputs = {**test_date_inputs, "ticker": "INVALID123"}

        # Act & Assert
        # Should not raise exception, but handle gracefully
        result = crew.kickoff(inputs=inputs)
        assert result is not None  # Should return some error message
