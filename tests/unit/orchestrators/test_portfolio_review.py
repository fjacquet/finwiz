"""
Unit tests for portfolio review orchestrator.
"""

import json
from pathlib import Path

import pytest
from crewai_custom_tools.core.results import ok

from finwiz.orchestrators.portfolio_review_orchestrator import (
    build_portfolio_review,
    get_csv_paths,
    save_review_json,
)
from finwiz.schemas.portfolio_processing import RawHolding


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
                return ok({"valid": True, "meta": {"source": "yahoo"}})
            return ok({"valid": False, "reason": "Ticker not found"})

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
                return ok({"valid": True, "meta": {"source": "yahoo"}})
            return ok({"valid": False, "reason": "Not found"})

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
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

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
                return ok({"valid": True, "meta": {"source": "yahoo"}})
            return ok({"valid": False, "reason": "Not found"})

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
        mock_validator.return_value._run.return_value = ok(
            {
                "valid": False,
                "reason": "Ticker not found",
            }
        )

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
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

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


class TestAllocationWiring:
    """build_portfolio_review stamps weights and total_value_eur when quantities exist."""

    async def test_weights_stamped_from_quantities(self, tmp_path, mocker):
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,AAPL,USD,true,10\nMicrosoft,MSFT,USD,true,10\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

        from finwiz.schemas.rebalancing.core import PriceData

        async def fake_get_current_prices(symbols, asset_classes=None):
            return {s: PriceData(symbol=s, price=100.0, currency="EUR") for s in symbols}

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        price_service.return_value.get_current_prices = fake_get_current_prices

        mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.get_fx_rate", return_value=1.0)

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        weights = {h.ticker: h.weight for h in review.holdings}
        assert weights["AAPL"] == pytest.approx(0.5)
        assert weights["MSFT"] == pytest.approx(0.5)
        assert review.total_value_eur == pytest.approx(2000.0)
        aapl = next(h for h in review.holdings if h.ticker == "AAPL")
        assert aapl.quantity == 10.0
        assert aapl.eur_value == pytest.approx(1000.0)

    async def test_no_quantities_means_no_price_fetch_and_none_weights(self, tmp_path, mocker):
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active\nApple,AAPL,USD,true\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        price_service.assert_not_called()
        assert review.holdings[0].weight is None
        assert review.total_value_eur is None

    async def test_valuation_failure_is_graceful(self, tmp_path, mocker):
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,AAPL,USD,true,10\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        price_service.return_value.get_current_prices = mocker.AsyncMock(side_effect=RuntimeError("boom"))

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        assert len(review.holdings) == 1
        assert review.holdings[0].weight is None
        assert review.total_value_eur is None

    async def test_partial_pricing_unpriced_holding_has_none_weight(self, tmp_path, mocker):
        stock_csv = tmp_path / "stock.csv"
        stock_csv.write_text("Name,Ticker,Currency,Active,Quantity\nApple,AAPL,USD,true,10\nMicrosoft,MSFT,USD,true,10\n")

        mock_validator = mocker.patch("finwiz.orchestrators.portfolio_holdings_processor.TickerExistenceValidationTool")
        mock_validator.return_value._run.return_value = ok({"valid": True, "meta": {"source": "yahoo"}})

        from finwiz.schemas.rebalancing.core import PriceData

        async def fake_get_current_prices(symbols, asset_classes=None):
            return {"AAPL": PriceData(symbol="AAPL", price=100.0, currency="EUR")}

        price_service = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        price_service.return_value.get_current_prices = fake_get_current_prices

        mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.get_fx_rate", return_value=1.0)

        review, _summary = await build_portfolio_review(stock_csv=stock_csv)

        aapl = next(h for h in review.holdings if h.ticker == "AAPL")
        msft = next(h for h in review.holdings if h.ticker == "MSFT")

        assert msft.weight is None
        assert msft.eur_value is None
        assert aapl.weight == pytest.approx(1.0)
        assert review.total_value_eur == pytest.approx(aapl.eur_value)


class TestValuePortfolioAssetClassRouting:
    """Regression coverage for the asset-class routing defect: `_value_portfolio`
    must pass each holding's known asset_class through to the price service
    instead of letting it re-guess (and misclassify) from the ticker text."""

    @staticmethod
    def _make_holding(ticker: str, asset_class: str, currency: str = "EUR") -> RawHolding:
        return RawHolding(
            asset_class=asset_class,  # type: ignore[arg-type]
            name=ticker,
            ticker=ticker,
            currency=currency,
            source_file=f"{asset_class}.csv",
            line_number=1,
            quantity=1.0,
        )

    async def test_should_pass_known_asset_class_per_ticker_to_price_service(self, mocker):
        """Long European tickers must be routed as stock/etf, not guessed as crypto."""
        from finwiz.orchestrators.portfolio_review_orchestrator import _value_portfolio
        from finwiz.schemas.rebalancing.core import PriceData

        holdings = [
            self._make_holding("NESN.SW", "stock"),
            self._make_holding("VUSA.L", "etf"),
            self._make_holding("BTC-USD", "crypto"),
        ]

        mock_service_cls = mocker.patch("finwiz.orchestrators.portfolio_review_orchestrator.PortfolioPriceService")
        mock_service = mock_service_cls.return_value
        mock_service.get_current_prices = mocker.AsyncMock(
            return_value={
                "NESN.SW": PriceData(symbol="NESN.SW", price=95.0, currency="EUR"),
                "VUSA.L": PriceData(symbol="VUSA.L", price=88.0, currency="EUR"),
                "BTC-USD": PriceData(symbol="BTC-USD", price=50000.0, currency="EUR"),
            }
        )

        result = await _value_portfolio(holdings)

        assert result is not None
        mock_service.get_current_prices.assert_awaited_once()
        _args, kwargs = mock_service.get_current_prices.call_args
        assert kwargs["asset_classes"] == {
            "NESN.SW": "stock",
            "VUSA.L": "etf",
            "BTC-USD": "crypto",
        }

        # And every holding actually got priced/weighted (none silently dropped).
        weights = {ticker: hv.weight for ticker, hv in result.per_ticker.items()}
        assert weights["NESN.SW"] is not None
        assert weights["VUSA.L"] is not None
        assert weights["BTC-USD"] is not None
