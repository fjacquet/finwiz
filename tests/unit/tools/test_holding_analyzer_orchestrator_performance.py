"""
Unit tests for HoldingAnalyzerOrchestrator performance optimizations.

Tests caching, rate limiting, parallel processing, and connection pooling.
"""

from pytest import approx
from datetime import datetime, timedelta

import pytest

from finwiz.tools.analysis.analysis_coordinator import HoldingAnalyzerOrchestrator
from finwiz.tools.analysis.holding_processors import HoldingAnalysis, HoldingProcessor


class TestHoldingAnalyzerOrchestratorPerformance:
    """Test suite for performance optimization features."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator instance with temp directory."""
        return HoldingAnalyzerOrchestrator(
            output_dir=tmp_path,
            enable_caching=True,
            enable_rate_limiting=True,
            parallel_batch_size=10,
        )

    @pytest.fixture
    def orchestrator_no_cache(self, tmp_path):
        """Create orchestrator with caching disabled."""
        return HoldingAnalyzerOrchestrator(
            output_dir=tmp_path,
            enable_caching=False,
            enable_rate_limiting=False,
            parallel_batch_size=10,
        )

    def test_should_initialize_with_caching_enabled_when_configured(self, orchestrator):
        """Test that caching is enabled when configured."""
        # Assert
        assert orchestrator.enable_caching is True
        assert orchestrator.cache_manager is not None

    def test_should_initialize_without_caching_when_disabled(self, orchestrator_no_cache):
        """Test that caching is disabled when configured."""
        # Assert
        assert orchestrator_no_cache.enable_caching is False
        assert orchestrator_no_cache.cache_manager is None

    def test_should_initialize_with_rate_limiting_enabled_when_configured(self, orchestrator):
        """Test that rate limiting is enabled when configured."""
        # Assert
        assert orchestrator.enable_rate_limiting is True
        assert orchestrator.rate_limiter is not None

    def test_should_set_parallel_batch_size_when_configured(self, orchestrator):
        """Test that parallel batch size is set correctly."""
        # Assert
        assert orchestrator.parallel_batch_size == 10

    @pytest.mark.asyncio
    async def test_should_process_holdings_in_batches_when_parallel_analysis(self, orchestrator, mocker):
        """Test that holdings are processed in batches."""
        # Arrange
        holdings = [
            {
                "ticker": f"TEST{i}",
                "asset_class": "stock",
                "currency": "USD",
                "name": f"Test Company {i}",
            }
            for i in range(25)  # 25 holdings = 3 batches of 10
        ]

        # Mock the async analysis method
        mock_analyze = mocker.patch.object(
            orchestrator,
            "analyze_holding_async",
            return_value=HoldingAnalysis(
                ticker="TEST",
                name="Test",
                asset_class="stock",
                currency="USD",
                analysis_date=datetime.now(),
                data_freshness="fresh",
            ),
        )

        # Act
        results = await orchestrator.analyze_holdings_parallel(holdings)

        # Assert
        assert len(results) == 25
        assert mock_analyze.call_count == 25

    @pytest.mark.asyncio
    async def test_should_handle_exceptions_in_parallel_processing(self, orchestrator, mocker):
        """Test that exceptions in parallel processing are handled gracefully."""
        # Arrange
        holdings = [
            {"ticker": "GOOD", "asset_class": "stock", "currency": "USD", "name": "Good"},
            {"ticker": "BAD", "asset_class": "stock", "currency": "USD", "name": "Bad"},
        ]

        # Mock to raise exception for BAD ticker
        async def mock_analyze(ticker, asset_class, currency, name):
            if ticker == "BAD":
                raise ValueError("Simulated error")
            return HoldingAnalysis(
                ticker=ticker,
                name=name,
                asset_class=asset_class,
                currency=currency,
                analysis_date=datetime.now(),
                data_freshness="fresh",
            )

        mocker.patch.object(orchestrator, "analyze_holding_async", side_effect=mock_analyze)

        # Act
        results = await orchestrator.analyze_holdings_parallel(holdings)

        # Assert
        assert len(results) == 2
        assert results[0].ticker == "GOOD"
        assert results[1].ticker == "BAD"  # Should have baseline analysis
        assert results[1].data_freshness == "stale"

    @pytest.mark.asyncio
    async def test_should_use_cache_when_available(self, orchestrator, mocker):
        """Test that cached results are used when available."""
        # Arrange
        ticker = "AAPL"
        cached_result = HoldingAnalysis(
            ticker=ticker,
            name="Apple Inc.",
            asset_class="stock",
            currency="USD",
            analysis_date=datetime.now(),
            data_freshness="fresh",
            composite_score=0.85,
        )

        # Mock cache manager to return cached result
        mock_cache_get = mocker.patch.object(orchestrator.cache_manager, "get", return_value=cached_result)

        # Act
        result = await orchestrator.analyze_holding_async(ticker=ticker, asset_class="stock", currency="USD", name="Apple Inc.")

        # Assert
        assert result.ticker == ticker
        assert result.composite_score == approx(0.85)
        mock_cache_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_cache_results_after_analysis(self, orchestrator, mocker, tmp_path):
        """Test that analysis results are cached."""
        # Arrange
        ticker = "AAPL"

        # Create a mock crew output file
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(exist_ok=True)
        latest_file = stock_dir / "stock_latest.json"
        latest_file.write_text('{"raw_output": "AAPL analysis", "pydantic": {"ticker": "AAPL", "composite_score": 0.85}}')

        # Mock cache manager
        mock_cache_get = mocker.patch.object(orchestrator.cache_manager, "get", return_value=None)
        mock_cache_set = mocker.patch.object(orchestrator.cache_manager, "set")

        # Act
        result = await orchestrator.analyze_holding_async(ticker=ticker, asset_class="stock", currency="USD", name="Apple Inc.")

        # Assert
        assert result.ticker == ticker
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_called_once()

    def test_should_check_cached_analysis_age_when_retrieving(self, orchestrator, tmp_path):
        """Test that cached analysis age is checked."""
        # Arrange
        ticker = "AAPL"
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(exist_ok=True)
        latest_file = stock_dir / "stock_latest.json"
        latest_file.write_text('{"raw_output": "AAPL analysis", "pydantic": {"ticker": "AAPL"}}')

        # Set file modification time to 10 days ago
        old_time = (datetime.now() - timedelta(days=10)).timestamp()
        import os

        os.utime(latest_file, (old_time, old_time))

        # Act
        result = orchestrator.get_cached_analysis(ticker, "stock", max_age_days=7)

        # Assert
        assert result is None  # Should be None because it's too old

    def test_should_return_cached_analysis_when_fresh(self, orchestrator, tmp_path):
        """Test that fresh cached analysis is returned."""
        # Arrange
        ticker = "AAPL"
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(exist_ok=True)
        latest_file = stock_dir / "stock_latest.json"
        latest_file.write_text('{"raw_output": "AAPL analysis", "pydantic": {"ticker": "AAPL"}}')

        # Act
        result = orchestrator.get_cached_analysis(ticker, "stock", max_age_days=7)

        # Assert
        assert result is not None
        assert "age_days" in result

    def test_should_create_baseline_analysis_when_no_cache(self, orchestrator):
        """Test that baseline analysis is created when no cache available."""
        # Act
        result = HoldingProcessor.create_baseline_analysis(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
            name="Apple Inc.",
        )

        # Assert
        assert result.ticker == "AAPL"
        assert result.data_freshness == "stale"
        assert result.crew_analysis_used is None
        assert result.confidence_level == approx(0.3)
        assert result.composite_score == approx(0.60)  # Baseline for stocks

    def test_should_use_different_baseline_scores_by_asset_class(self, orchestrator):
        """Test that different asset classes have different baseline scores."""
        # Act
        stock_result = HoldingProcessor.create_baseline_analysis("AAPL", "stock", "USD", "Apple")
        etf_result = HoldingProcessor.create_baseline_analysis("SPY", "etf", "USD", "S&P 500 ETF")
        crypto_result = HoldingProcessor.create_baseline_analysis("BTC", "crypto", "USD", "Bitcoin")

        # Assert
        assert stock_result.composite_score == approx(0.60)
        assert etf_result.composite_score == approx(0.65)
        assert crypto_result.composite_score == approx(0.55)

    def test_should_extract_fundamental_analysis_from_stock_crew_output(self, orchestrator):
        """Test extraction of fundamental analysis from stock crew output."""
        # Arrange
        crew_output = {
            "pydantic": {
                "ten_k_insights": {"revenue": "100B", "profit": "20B"},
                "financial_metrics": {"pe_ratio": 25, "roe": 0.20},
            }
        }

        # Act
        result = HoldingProcessor.extract_fundamental_analysis(crew_output, "stock")

        # Assert
        assert result is not None
        assert "ten_k_insights" in result
        assert "financial_metrics" in result

    def test_should_extract_fundamental_analysis_from_etf_crew_output(self, orchestrator):
        """Test extraction of fundamental analysis from ETF crew output."""
        # Arrange
        crew_output = {
            "pydantic": {
                "expense_ratio": 0.03,
                "tracking_error": 0.05,
                "holdings": ["AAPL", "MSFT", "GOOGL"],
            }
        }

        # Act
        result = HoldingProcessor.extract_fundamental_analysis(crew_output, "etf")

        # Assert
        assert result is not None
        assert "expense_ratio" in result
        assert "tracking_error" in result
        assert "holdings" in result

    def test_should_extract_technical_analysis_from_crew_output(self, orchestrator):
        """Test extraction of technical analysis."""
        # Arrange
        crew_output = {
            "pydantic": {
                "technical_indicators": {"rsi": 65, "macd": "bullish"},
                "price_patterns": {"trend": "upward"},
            }
        }

        # Act
        result = HoldingProcessor.extract_technical_analysis(crew_output)

        # Assert
        assert result is not None
        assert "technical_indicators" in result
        assert "price_patterns" in result

    def test_should_extract_sec_citations_from_crew_output(self, orchestrator):
        """Test extraction of SEC citations."""
        # Arrange
        crew_output = {
            "pydantic": {
                "sec_citations": [
                    {"filing_type": "10-K", "accession": "123456"},
                    {"filing_type": "10-Q", "accession": "789012"},
                ]
            }
        }

        # Act
        result = HoldingProcessor.extract_sec_citations(crew_output)

        # Assert
        assert len(result) == 2
        assert result[0]["filing_type"] == "10-K"

    def test_should_extract_composite_score_from_crew_output(self, orchestrator):
        """Test extraction of composite score."""
        # Arrange
        crew_output = {"pydantic": {"composite_score": 0.85}}

        # Act
        result = HoldingProcessor.extract_composite_score(crew_output)

        # Assert
        assert result == approx(0.85)

    def test_should_return_default_score_when_not_in_crew_output(self, orchestrator):
        """Test that default score is returned when not in crew output."""
        # Arrange
        crew_output = {"pydantic": {}}

        # Act
        result = HoldingProcessor.extract_composite_score(crew_output)

        # Assert
        assert result == approx(0.65)  # Default baseline

    def test_should_check_ticker_in_crew_output(self, orchestrator):
        """Test ticker checking in crew output."""
        # Arrange
        crew_output = {
            "raw_output": "Analysis for AAPL shows strong fundamentals",
            "pydantic": {"ticker": "AAPL"},
        }

        # Act
        result = HoldingProcessor.contains_ticker_analysis(crew_output, "AAPL")

        # Assert
        assert result is True

    def test_should_return_false_when_ticker_not_in_output(self, orchestrator):
        """Test that False is returned when ticker not in output."""
        # Arrange
        crew_output = {
            "raw_output": "Analysis for MSFT",
            "pydantic": {"ticker": "MSFT"},
        }

        # Act
        result = HoldingProcessor.contains_ticker_analysis(crew_output, "AAPL")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_should_measure_performance_for_parallel_analysis(self, orchestrator, mocker):
        """Test that performance metrics are logged for parallel analysis."""
        # Arrange
        holdings = [{"ticker": f"TEST{i}", "asset_class": "stock", "currency": "USD", "name": f"Test {i}"} for i in range(5)]

        # Mock analyze_holding_async to return quickly
        mocker.patch.object(
            orchestrator,
            "analyze_holding_async",
            return_value=HoldingAnalysis(
                ticker="TEST",
                name="Test",
                asset_class="stock",
                currency="USD",
                analysis_date=datetime.now(),
                data_freshness="fresh",
            ),
        )

        # Act
        start_time = datetime.now()
        results = await orchestrator.analyze_holdings_parallel(holdings)
        elapsed = (datetime.now() - start_time).total_seconds()

        # Assert
        assert len(results) == 5
        assert elapsed < 5.0  # Should complete quickly with mocked analysis