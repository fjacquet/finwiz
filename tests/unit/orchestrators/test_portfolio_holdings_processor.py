"""
Unit tests for Portfolio Holdings Processor.

Tests the PortfolioHoldingsProcessor class for loading holdings from CSV files,
processing all holdings including failed validations, and generating processing summaries.
"""

import csv

import pytest
from pytest import approx

from finwiz.orchestrators.portfolio_holdings_processor import (
    PortfolioHoldingsProcessor,
    RawHolding,
)


class TestPortfolioHoldingsProcessor:
    """Test suite for PortfolioHoldingsProcessor."""

    @pytest.fixture
    def processor(self):
        """Create processor instance for testing."""
        return PortfolioHoldingsProcessor()

    @pytest.fixture
    def sample_stock_csv(self, tmp_path):
        """Create sample stock CSV file."""
        csv_file = tmp_path / "stock.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Ticker", "Currency"])
            writer.writeheader()
            writer.writerow({"Name": "Apple Inc.", "Ticker": "AAPL", "Currency": "USD"})
            writer.writerow({"Name": "Microsoft Corp.", "Ticker": "MSFT", "Currency": "USD"})
        return csv_file

    @pytest.fixture
    def sample_etf_csv(self, tmp_path):
        """Create sample ETF CSV file."""
        csv_file = tmp_path / "etf.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Ticker", "Currency"])
            writer.writeheader()
            writer.writerow({"Name": "S&P 500 ETF", "Ticker": "SPY", "Currency": "USD"})
        return csv_file

    @pytest.fixture
    def sample_crypto_csv(self, tmp_path):
        """Create sample crypto CSV file."""
        csv_file = tmp_path / "crypto.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Ticker", "Currency"])
            writer.writeheader()
            writer.writerow({"Name": "Bitcoin", "Ticker": "BTC-USD", "Currency": "USD"})
        return csv_file

    def test_should_initialize_processor(self, processor):
        """Test processor initialization."""
        # Assert
        assert processor.validator is not None
        assert processor.processing_results == []

    def test_should_normalize_ticker_without_prefix(self, processor):
        """Test ticker normalization without prefix."""
        # Act
        result = processor.normalize_ticker("AAPL")

        # Assert
        assert result == "AAPL"

    def test_should_normalize_ticker_with_yahoo_prefix(self, processor):
        """Test ticker normalization with YAHOO: prefix."""
        # Act
        result = processor.normalize_ticker("YAHOO:AAPL")

        # Assert
        assert result == "AAPL"

    def test_should_handle_empty_ticker(self, processor):
        """Test ticker normalization with empty string."""
        # Act
        result = processor.normalize_ticker("")

        # Assert
        assert result == ""

    def test_should_handle_none_ticker(self, processor):
        """Test ticker normalization with None."""
        # Act
        result = processor.normalize_ticker(None)

        # Assert
        assert result == ""

    def test_should_load_stock_holdings(self, processor, sample_stock_csv):
        """Test loading stock holdings from CSV."""
        # Act
        holdings = processor.load_all_holdings(stock_csv=sample_stock_csv)

        # Assert
        assert len(holdings) == 2
        assert holdings[0].asset_class == "stock"
        assert holdings[0].ticker == "AAPL"
        assert holdings[0].name == "Apple Inc."
        assert holdings[0].currency == "USD"
        assert holdings[1].ticker == "MSFT"

    def test_should_load_etf_holdings(self, processor, sample_etf_csv):
        """Test loading ETF holdings from CSV."""
        # Act
        holdings = processor.load_all_holdings(etf_csv=sample_etf_csv)

        # Assert
        assert len(holdings) == 1
        assert holdings[0].asset_class == "etf"
        assert holdings[0].ticker == "SPY"
        assert holdings[0].name == "S&P 500 ETF"

    def test_should_load_crypto_holdings(self, processor, sample_crypto_csv):
        """Test loading crypto holdings from CSV."""
        # Act
        holdings = processor.load_all_holdings(crypto_csv=sample_crypto_csv)

        # Assert
        assert len(holdings) == 1
        assert holdings[0].asset_class == "crypto"
        assert holdings[0].ticker == "BTC-USD"
        assert holdings[0].name == "Bitcoin"

    def test_should_load_all_holdings_from_multiple_files(self, processor, sample_stock_csv, sample_etf_csv, sample_crypto_csv):
        """Test loading holdings from all CSV files."""
        # Act
        holdings = processor.load_all_holdings(
            stock_csv=sample_stock_csv,
            etf_csv=sample_etf_csv,
            crypto_csv=sample_crypto_csv,
        )

        # Assert
        assert len(holdings) == 4
        stock_holdings = [h for h in holdings if h.asset_class == "stock"]
        etf_holdings = [h for h in holdings if h.asset_class == "etf"]
        crypto_holdings = [h for h in holdings if h.asset_class == "crypto"]
        assert len(stock_holdings) == 2
        assert len(etf_holdings) == 1
        assert len(crypto_holdings) == 1

    def test_should_handle_missing_csv_file(self, processor, tmp_path):
        """Test handling of missing CSV file."""
        # Arrange
        missing_file = tmp_path / "missing.csv"

        # Act
        holdings = processor.load_all_holdings(stock_csv=missing_file)

        # Assert
        assert len(holdings) == 0

    def test_should_skip_empty_rows(self, processor, tmp_path):
        """Test that empty rows are skipped."""
        # Arrange
        csv_file = tmp_path / "stock.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Ticker", "Currency"])
            writer.writeheader()
            writer.writerow({"Name": "Apple Inc.", "Ticker": "AAPL", "Currency": "USD"})
            writer.writerow({"Name": "", "Ticker": "", "Currency": ""})
            writer.writerow({"Name": "Microsoft Corp.", "Ticker": "MSFT", "Currency": "USD"})

        # Act
        holdings = processor.load_all_holdings(stock_csv=csv_file)

        # Assert
        assert len(holdings) == 2
        assert holdings[0].ticker == "AAPL"
        assert holdings[1].ticker == "MSFT"

    def test_should_handle_incomplete_data(self, processor, tmp_path):
        """Test handling of incomplete data in CSV."""
        # Arrange
        csv_file = tmp_path / "stock.csv"
        with csv_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Ticker", "Currency"])
            writer.writeheader()
            writer.writerow({"Name": "Apple Inc.", "Ticker": "AAPL", "Currency": ""})
            writer.writerow({"Name": "", "Ticker": "MSFT", "Currency": "USD"})

        # Act
        holdings = processor.load_all_holdings(stock_csv=csv_file)

        # Assert
        assert len(holdings) == 2
        assert holdings[0].currency == "USD"  # Default
        assert holdings[1].name == "Unknown"  # Default

    async def test_should_process_holdings_with_valid_ticker(self, processor, mocker):
        """Test processing holdings with valid ticker."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "Ticker exists",
            "meta": {"source": "yahoo"},
        }

        # Act - Pass lower threshold to get KEEP (stock score is 0.6)
        decisions = await processor.process_holdings(holdings, keep_threshold=0.55)

        # Assert
        assert len(decisions) == 1
        assert decisions[0].ticker == "AAPL"
        assert decisions[0].decision == "KEEP"  # 0.6 > 0.55 threshold
        assert decisions[0].composite_score == approx(0.6)  # Stocks get 0.6 with shallow validation
        assert decisions[0].data_freshness == "fresh"

    async def test_should_process_holdings_with_invalid_ticker(self, processor, mocker):
        """Test processing holdings with invalid ticker."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Invalid Stock",
                ticker="INVALID",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": False,
            "reason": "Ticker not found",
            "meta": {},
        }

        # Act
        decisions = await processor.process_holdings(holdings)

        # Assert
        assert len(decisions) == 1
        assert decisions[0].ticker == "INVALID"
        assert decisions[0].decision == "SELL"
        assert decisions[0].data_freshness == "stale"
        # Check for validation failure message
        rationale_text = " ".join(decisions[0].rationale_bullets).lower()
        assert "unable to validate" in rationale_text

    async def test_should_include_all_holdings_even_with_errors(self, processor, mocker):
        """Test that all holdings are included even if processing fails."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            ),
            RawHolding(
                asset_class="stock",
                name="Error Stock",
                ticker="ERROR",
                currency="USD",
                source_file="stock.csv",
                line_number=3,
            ),
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.side_effect = [
            {"valid": True, "reason": "OK", "meta": {"source": "yahoo"}},
            Exception("Validation error"),
        ]

        # Act
        decisions = await processor.process_holdings(holdings)

        # Assert
        assert len(decisions) == 2
        assert decisions[0].ticker == "AAPL"
        assert decisions[1].ticker == "ERROR"
        assert decisions[1].decision == "SELL"
        # When validation fails, score is 0.3 (invalid ticker base score)
        assert decisions[1].composite_score == approx(0.3)

    async def test_should_generate_processing_summary(self, processor, mocker):
        """Test generation of processing summary."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            ),
            RawHolding(
                asset_class="etf",
                name="S&P 500 ETF",
                ticker="SPY",
                currency="USD",
                source_file="etf.csv",
                line_number=2,
            ),
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "OK",
            "meta": {"source": "yahoo"},
        }

        # Act
        await processor.process_holdings(holdings)
        summary = processor.get_processing_summary()

        # Assert
        assert summary.total_holdings == 2
        assert summary.processed_successfully == 2
        assert summary.processed_with_warnings == 0
        assert summary.failed_to_process == 0
        assert summary.by_asset_class["stock"] == 1
        assert summary.by_asset_class["etf"] == 1

    async def test_should_track_validation_failures_in_summary(self, processor, mocker):
        """Test that validation failures are tracked in summary."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Invalid Stock",
                ticker="INVALID",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": False,
            "reason": "Ticker not found",
            "meta": {},
        }

        # Act
        await processor.process_holdings(holdings)
        summary = processor.get_processing_summary()

        # Assert
        assert len(summary.validation_failures) == 1
        assert summary.validation_failures[0][0] == "INVALID"
        # The reason is "Validation failed" not the original reason
        assert "validation failed" in summary.validation_failures[0][1].lower()

    async def test_should_track_processing_errors_in_summary(self, processor, mocker):
        """Test that processing errors are tracked in summary."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Error Stock",
                ticker="ERROR",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.side_effect = Exception("Processing error")

        # Act
        await processor.process_holdings(holdings)
        summary = processor.get_processing_summary()

        # Assert
        # When validation throws exception, it's caught and treated as validation failure
        # The holding is still processed with stale status, not failed
        assert summary.processed_with_warnings == 1
        assert len(summary.validation_failures) == 1
        assert summary.validation_failures[0][0] == "ERROR"

    async def test_should_apply_keep_threshold(self, processor, mocker):
        """Test that keep threshold is applied correctly."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "OK",
            "meta": {"source": "yahoo"},
        }

        # Act - with high threshold
        decisions = await processor.process_holdings(holdings, keep_threshold=0.9)

        # Assert
        assert decisions[0].decision == "SELL"  # Score is 0.6, below 0.9

    async def test_should_use_base_currency(self, processor, mocker):
        """Test that base currency is used when not specified."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="",
                source_file="stock.csv",
                line_number=2,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "OK",
            "meta": {"source": "yahoo"},
        }

        # Act
        decisions = await processor.process_holdings(holdings, base_currency="EUR")

        # Assert
        assert decisions[0].currency == "EUR"

    async def test_should_boost_etf_score(self, processor, mocker):
        """Test that ETFs get a score boost."""
        # Arrange
        stock_holding = RawHolding(
            asset_class="stock",
            name="Apple Inc.",
            ticker="AAPL",
            currency="USD",
            source_file="stock.csv",
            line_number=2,
        )
        etf_holding = RawHolding(
            asset_class="etf",
            name="S&P 500 ETF",
            ticker="SPY",
            currency="USD",
            source_file="etf.csv",
            line_number=2,
        )

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "OK",
            "meta": {"source": "yahoo"},
        }

        # Act
        stock_decisions = await processor.process_holdings([stock_holding])
        etf_decisions = await processor.process_holdings([etf_holding])

        # Assert
        assert etf_decisions[0].composite_score > stock_decisions[0].composite_score

    async def test_should_include_validation_status_in_rationale(self, processor, mocker):
        """Test that validation status is included in rationale."""
        # Arrange
        holdings = [
            RawHolding(
                asset_class="stock",
                name="Apple Inc.",
                ticker="AAPL",
                currency="USD",
                source_file="/path/to/stock.csv",
                line_number=5,
            )
        ]

        mock_validator = mocker.patch.object(processor.validator, "_run")
        mock_validator.return_value = {
            "valid": True,
            "reason": "OK",
            "meta": {"source": "yahoo"},
        }

        # Act
        decisions = await processor.process_holdings(holdings)

        # Assert - Rationale indicates validated status and pending deep analysis
        rationale = " ".join(decisions[0].rationale_bullets).lower()
        assert "validated stock" in rationale
        assert "pending deep analysis" in rationale

    def test_should_handle_csv_read_error(self, processor, tmp_path, mocker):
        """Test handling of CSV read errors."""
        # Arrange
        csv_file = tmp_path / "corrupt.csv"
        csv_file.write_text("invalid,csv,data\n", encoding="utf-8")

        # Mock open to raise an exception
        mocker.patch("builtins.open", side_effect=Exception("Read error"))

        # Act
        holdings = processor.load_all_holdings(stock_csv=csv_file)

        # Assert
        assert len(holdings) == 0


class TestQuantityIngestion:
    """CSV `Quantity` column parsing into RawHolding.quantity."""

    def test_parses_valid_quantity(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,10.5\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert len(holdings) == 1
        assert holdings[0].quantity == 10.5

    def test_blank_quantity_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_garbage_quantity_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,Yahoo:AAPL,USD,true,abc\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_missing_quantity_column_is_none(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "stock.csv"
        csv.write_text("Name,Ticker,Currency,Active\nApple,Yahoo:AAPL,USD,true\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "stock")

        assert holdings[0].quantity is None

    def test_crypto_quantity_parsed(self, tmp_path):
        from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

        csv = tmp_path / "crypto.csv"
        csv.write_text("Name,Ticker,Active,Quantity\nBitcoin,BTC,true,0.25\n")
        processor = PortfolioHoldingsProcessor()

        holdings = processor._read_csv_holdings(csv, "crypto")

        assert holdings[0].quantity == 0.25
        assert holdings[0].ticker == "BTC-USD"  # crypto normalization still applies
