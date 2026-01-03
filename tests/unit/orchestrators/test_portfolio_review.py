"""
Unit tests for portfolio review orchestrator.
"""

import json
from pathlib import Path

from finwiz.orchestrators.portfolio_review_orchestrator import (
    build_portfolio_review,
    get_csv_paths,
    save_review_json,
)


class TestPortfolioReview:
    """Test suite for portfolio review orchestrator."""

    async def test_should_process_all_holdings_from_csv(self, tmp_path, mocker):
        """Test that all holdings from CSV files are processed."""
        # Arrange - Create test CSV files
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nApple Inc.,AAPL,USD\nMicrosoft Corp.,MSFT,USD\nInvalid Stock,INVALID,USD\n")

        etf_csv = tmp_path / "etf.csv"
        etf_csv.write_text("Name,Ticker,Currency\nS&P 500 ETF,SPY,USD\nTech ETF,QQQ,USD\n")

        crypto_csv = tmp_path / "crypto.csv"
        crypto_csv.write_text("Name,Ticker,Currency\nBitcoin,BTC-USD,USD\n")

        # Mock validation to return success for known tickers
        def mock_validate(symbol, asset_class):
            if symbol in ["AAPL", "MSFT", "SPY", "QQQ", "BTC-USD"]:
                return {"valid": True, "meta": {"source": "yahoo"}}
            return {"valid": False, "reason": "Ticker not found"}

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.side_effect = mock_validate

        # Act
        review, summary = await build_portfolio_review(
            stock_csv=stock_csv,
            etf_csv=etf_csv,
            crypto_csv=crypto_csv,
        )

        # Assert - All holdings should be processed
        assert summary.total_holdings == 6
        assert len(review.holdings) == 6

        # Check that all tickers are present
        tickers = {h.ticker for h in review.holdings}
        assert tickers == {"AAPL", "MSFT", "INVALID", "SPY", "QQQ", "BTC-USD"}

    async def test_should_include_validation_status_for_each_holding(self, tmp_path, mocker):
        """Test that validation status is included for each holding."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nApple Inc.,AAPL,USD\nInvalid,BAD,USD\n")

        def mock_validate(symbol, asset_class):
            if symbol == "AAPL":
                return {"valid": True, "meta": {"source": "yahoo"}}
            return {"valid": False, "reason": "Not found"}

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.side_effect = mock_validate

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Assert
        assert len(review.holdings) == 2

        # Check validation status
        aapl = next(h for h in review.holdings if h.ticker == "AAPL")
        assert aapl.data_freshness == "fresh"

        bad = next(h for h in review.holdings if h.ticker == "BAD")
        assert bad.data_freshness == "stale"

    async def test_should_log_count_of_holdings_processed(self, tmp_path, mocker, caplog):
        """Test that count of holdings processed vs CSV is logged."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nApple Inc.,AAPL,USD\nMicrosoft,MSFT,USD\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Assert
        assert summary.total_holdings == 2
        assert len(review.holdings) == 2

        # Check that processing was logged
        assert summary.processed_successfully == 2

    async def test_should_include_processing_summary_in_report_data(self, tmp_path, mocker):
        """Test that processing summary is saved to separate file."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nApple Inc.,AAPL,USD\nInvalid,BAD,USD\n")

        def mock_validate(symbol, asset_class):
            if symbol == "AAPL":
                return {"valid": True, "meta": {"source": "yahoo"}}
            return {"valid": False, "reason": "Not found"}

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.side_effect = mock_validate

        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Act - Save with summary
        out_path = tmp_path / "review.json"
        save_review_json(review, out_path, summary)

        # Assert - Main review file exists
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert "holdings" in data

        # Assert - Processing summary saved to separate file
        summary_path = tmp_path / "portfolio_processing_summary.json"
        assert summary_path.exists()
        summary_data = json.loads(summary_path.read_text())

        assert summary_data["total_holdings"] == 2
        assert summary_data["processed_successfully"] == 1
        assert summary_data["processed_with_warnings"] == 1

        # Check validation failures are included
        assert len(summary_data["validation_failures"]) == 1
        assert summary_data["validation_failures"][0]["ticker"] == "BAD"

    async def test_should_process_holdings_even_if_validation_fails(self, tmp_path, mocker):
        """Test that holdings are included even if validation fails."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nInvalid Stock,INVALID,USD\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {
            "valid": False,
            "reason": "Ticker not found",
        }

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Assert - Holding should still be included
        assert len(review.holdings) == 1
        assert review.holdings[0].ticker == "INVALID"
        assert review.holdings[0].data_freshness == "stale"
        # Check that rationale bullets exist (may be in French or English)
        assert len(review.holdings[0].rationale_bullets) > 0

    async def test_should_handle_empty_csv_files(self, tmp_path, mocker):
        """Test handling of empty CSV files."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\n")  # Header only

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Assert
        assert summary.total_holdings == 0
        assert len(review.holdings) == 0

    async def test_should_handle_missing_csv_files(self, tmp_path, mocker):
        """Test handling of missing CSV files."""
        # Arrange
        stock_csv = tmp_path / "nonexistent.csv"

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv)

        # Assert
        assert summary.total_holdings == 0
        assert len(review.holdings) == 0

    async def test_should_track_by_asset_class(self, tmp_path, mocker):
        """Test that holdings are tracked by asset class."""
        # Arrange
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency\nApple,AAPL,USD\nMicrosoft,MSFT,USD\n")

        etf_csv = tmp_path / "etf.csv"
        etf_csv.write_text("Name,Ticker,Currency\nS&P 500,SPY,USD\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = {"valid": True, "meta": {"source": "yahoo"}}

        # Act
        review, summary = await build_portfolio_review(stock_csv=stock_csv, etf_csv=etf_csv)

        # Assert
        assert summary.by_asset_class == {"stock": 2, "etf": 1}

    def test_get_csv_paths_should_return_three_paths(self):
        """Test that get_csv_paths returns paths for stock, ETF, and crypto."""
        # Act
        etf_csv, stock_csv, crypto_csv = get_csv_paths()

        # Assert
        assert isinstance(etf_csv, Path)
        assert isinstance(stock_csv, Path)
        assert isinstance(crypto_csv, Path)
        assert "etf.csv" in str(etf_csv)
        assert "stock.csv" in str(stock_csv)
        assert "crypto.csv" in str(crypto_csv)
