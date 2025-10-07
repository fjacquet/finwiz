"""
Integration tests for portfolio review with holdings processor.
"""

import json
from pathlib import Path

import pytest

from finwiz.orchestrators.portfolio_review import run


@pytest.mark.integration
class TestPortfolioReviewIntegration:
    """Integration tests for portfolio review."""

    def test_should_run_complete_portfolio_review(self, tmp_path, mocker):
        """Test complete portfolio review flow."""
        # Arrange - Create test CSV files
        project_root = tmp_path
        data_dir = project_root / "data"
        data_dir.mkdir()

        stock_csv = data_dir / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\n" "Apple Inc.,AAPL,USD\n")

        etf_csv = data_dir / "etf.csv"
        etf_csv.write_text("Name,Ticker,Currency\n" "S&P 500,SPY,USD\n")

        crypto_csv = data_dir / "crypto.csv"
        crypto_csv.write_text("Name,Ticker,Currency\n" "Bitcoin,BTC-USD,USD\n")

        # Mock environment variables
        mocker.patch.dict(
            "os.environ",
            {
                "PORTFOLIO_STOCK_CSV": str(stock_csv),
                "PORTFOLIO_ETF_CSV": str(etf_csv),
                "PORTFOLIO_CRYPTO_CSV": str(crypto_csv),
            },
        )

        # Mock validation
        mock_validator = mocker.patch(
            "finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool"
        )
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        # Mock output path
        output_dir = project_root / "output" / "portfolio"
        output_dir.mkdir(parents=True)
        expected_output = output_dir / "portfolio_review.json"

        mocker.patch("finwiz.orchestrators.portfolio_review.Path.__file__", str(project_root / "src"))

        # Act
        result_path = run()

        # Assert
        assert result_path.exists()
        data = json.loads(result_path.read_text())

        # Check structure
        assert "portfolio_review" in data
        assert "processing_summary" in data

        # Check portfolio review
        review = data["portfolio_review"]
        assert "holdings" in review
        assert len(review["holdings"]) == 3

        # Check processing summary
        summary = data["processing_summary"]
        assert summary["total_holdings"] == 3
        assert summary["by_asset_class"]["stock"] == 1
        assert summary["by_asset_class"]["etf"] == 1
        assert summary["by_asset_class"]["crypto"] == 1
