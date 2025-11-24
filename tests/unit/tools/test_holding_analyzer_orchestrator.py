"""Unit tests for HoldingAnalyzerOrchestrator."""

from pytest import approx
import json
from pathlib import Path

import pytest

from finwiz.tools.analysis.analysis_coordinator import HoldingAnalyzerOrchestrator
from finwiz.tools.analysis.holding_processors import HoldingAnalysis, HoldingProcessor


class TestHoldingAnalyzerOrchestrator:
    """Test suite for HoldingAnalyzerOrchestrator."""

    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with temporary output directory."""
        return HoldingAnalyzerOrchestrator(output_dir=tmp_path)

    @pytest.fixture
    def mock_stock_output(self, tmp_path):
        """Create mock stock crew output file."""
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "raw_output": "Analysis for AAPL ticker with strong fundamentals",
            "pydantic": {
                "ticker": "AAPL",
                "composite_score": 0.85,
                "ten_k_insights": {
                    "revenue_growth": 0.15,
                    "profit_margin": 0.25,
                },
                "technical_indicators": {
                    "rsi": 65,
                    "macd": "bullish",
                },
                "sec_citations": [
                    {
                        "filing_type": "10-K",
                        "accession_number": "0000320193-24-000123",
                        "filing_date": "2024-10-30",
                    }
                ],
            },
        }

        latest_file = stock_dir / "stock_latest.json"
        with open(latest_file, "w") as f:
            json.dump(output_data, f)

        return latest_file

    def test_should_create_orchestrator_with_default_output_dir(self):
        """Test orchestrator creation with default output directory."""
        # Act
        orchestrator = HoldingAnalyzerOrchestrator()

        # Assert
        assert orchestrator.output_dir == Path("output")
        assert orchestrator.stock_output_dir == Path("output/stock")
        assert orchestrator.etf_output_dir == Path("output/etf")
        assert orchestrator.crypto_output_dir == Path("output/crypto")

    def test_should_create_orchestrator_with_custom_output_dir(self, tmp_path):
        """Test orchestrator creation with custom output directory."""
        # Arrange
        custom_dir = tmp_path / "custom_output"

        # Act
        orchestrator = HoldingAnalyzerOrchestrator(output_dir=custom_dir)

        # Assert
        assert orchestrator.output_dir == custom_dir
        assert orchestrator.stock_output_dir == custom_dir / "stock"

    def test_should_return_baseline_analysis_when_no_cache_exists(self, orchestrator):
        """Test baseline analysis creation when no cached data exists."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
            name="Apple Inc.",
        )

        # Assert
        assert isinstance(result, HoldingAnalysis)
        assert result.ticker == "AAPL"
        assert result.name == "Apple Inc."
        assert result.asset_class == "stock"
        assert result.currency == "USD"
        assert result.data_freshness == "stale"
        assert result.crew_analysis_used is None
        assert result.composite_score == approx(0.60)  # Baseline for stocks
        assert result.confidence_level == approx(0.3)  # Low confidence for baseline

    def test_should_use_cached_analysis_when_fresh(self, orchestrator, mock_stock_output):
        """Test using cached analysis when it's fresh."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
            name="Apple Inc.",
        )

        # Assert
        assert isinstance(result, HoldingAnalysis)
        assert result.ticker == "AAPL"
        assert result.data_freshness in ["fresh", "recent"]
        assert result.crew_analysis_used == "stock_crew"
        assert result.composite_score == approx(0.85)
        assert result.confidence_level >= 0.6

    def test_should_extract_fundamental_analysis_from_stock_crew(self, orchestrator, mock_stock_output):
        """Test extraction of fundamental analysis from stock crew output."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
        )

        # Assert
        assert result.fundamental_analysis is not None
        assert "ten_k_insights" in result.fundamental_analysis
        assert result.fundamental_analysis["ten_k_insights"]["revenue_growth"] == approx(0.15)

    def test_should_extract_technical_analysis_from_crew_output(self, orchestrator, mock_stock_output):
        """Test extraction of technical analysis from crew output."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
        )

        # Assert
        assert result.technical_analysis is not None
        assert "technical_indicators" in result.technical_analysis
        assert result.technical_analysis["technical_indicators"]["rsi"] == 65

    def test_should_extract_sec_citations_from_crew_output(self, orchestrator, mock_stock_output):
        """Test extraction of SEC citations from crew output."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
        )

        # Assert
        assert len(result.sec_citations) == 1
        assert result.sec_citations[0]["filing_type"] == "10-K"
        assert result.sec_citations[0]["accession_number"] == "0000320193-24-000123"

    def test_should_return_baseline_for_etf_when_no_cache(self, orchestrator):
        """Test baseline analysis for ETF asset class."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="VUSA.L",
            asset_class="etf",
            currency="USD",
        )

        # Assert
        assert result.asset_class == "etf"
        assert result.composite_score == approx(0.65)  # Baseline for ETFs
        assert result.data_freshness == "stale"

    def test_should_return_baseline_for_crypto_when_no_cache(self, orchestrator):
        """Test baseline analysis for crypto asset class."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="BTC",
            asset_class="crypto",
            currency="USD",
        )

        # Assert
        assert result.asset_class == "crypto"
        assert result.composite_score == approx(0.55)  # Baseline for crypto
        assert result.data_freshness == "stale"

    def test_should_handle_missing_pydantic_output_gracefully(self, orchestrator, tmp_path):
        """Test handling of crew output without pydantic field."""
        # Arrange
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "raw_output": "Analysis for MSFT ticker",
            # No pydantic field
        }

        latest_file = stock_dir / "stock_latest.json"
        with open(latest_file, "w") as f:
            json.dump(output_data, f)

        # Act
        result = orchestrator.analyze_holding(
            ticker="MSFT",
            asset_class="stock",
            currency="USD",
        )

        # Assert
        assert result.ticker == "MSFT"
        assert result.crew_analysis_used == "stock_crew"
        assert result.fundamental_analysis is None
        assert result.technical_analysis is None

    def test_should_determine_freshness_correctly(self, orchestrator):
        """Test freshness determination based on age."""
        # Test fresh (0-2 days)
        cached_data = {"age_days": 1, "pydantic": {}}
        result = HoldingProcessor.map_cached_to_holding_analysis(
            ticker="TEST",
            asset_class="stock",
            currency="USD",
            name="Test",
            cached_data=cached_data,
        )
        assert result.data_freshness == "fresh"

        # Test recent (3-7 days)
        cached_data = {"age_days": 5, "pydantic": {}}
        result = HoldingProcessor.map_cached_to_holding_analysis(
            ticker="TEST",
            asset_class="stock",
            currency="USD",
            name="Test",
            cached_data=cached_data,
        )
        assert result.data_freshness == "recent"

        # Test stale (>7 days)
        cached_data = {"age_days": 10, "pydantic": {}}
        result = HoldingProcessor.map_cached_to_holding_analysis(
            ticker="TEST",
            asset_class="stock",
            currency="USD",
            name="Test",
            cached_data=cached_data,
        )
        assert result.data_freshness == "stale"

    def test_should_not_trigger_crew_analysis(self, orchestrator):
        """Test that trigger_crew_analysis raises NotImplementedError."""
        # Act & Assert
        with pytest.raises(NotImplementedError):
            orchestrator.trigger_crew_analysis(ticker="AAPL", asset_class="stock")

    def test_should_handle_corrupted_cache_file_gracefully(self, orchestrator, tmp_path):
        """Test handling of corrupted cache file."""
        # Arrange
        stock_dir = tmp_path / "stock"
        stock_dir.mkdir(parents=True, exist_ok=True)

        latest_file = stock_dir / "stock_latest.json"
        with open(latest_file, "w") as f:
            f.write("invalid json {{{")

        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
        )

        # Assert - should fall back to baseline
        assert result.data_freshness == "stale"
        assert result.crew_analysis_used is None

    def test_should_use_ticker_as_name_when_name_not_provided(self, orchestrator):
        """Test that ticker is used as name when name is not provided."""
        # Act
        result = orchestrator.analyze_holding(
            ticker="AAPL",
            asset_class="stock",
            currency="USD",
        )

        # Assert
        assert result.name == "AAPL"

    def test_should_extract_etf_specific_fundamental_data(self, orchestrator, tmp_path):
        """Test extraction of ETF-specific fundamental data."""
        # Arrange
        etf_dir = tmp_path / "etf"
        etf_dir.mkdir(parents=True, exist_ok=True)

        output_data = {
            "raw_output": "Analysis for VUSA.L",
            "pydantic": {
                "ticker": "VUSA.L",
                "expense_ratio": 0.07,
                "tracking_error": 0.02,
                "holdings": [
                    {"ticker": "AAPL", "weight": 7.5},
                    {"ticker": "MSFT", "weight": 6.8},
                ],
            },
        }

        latest_file = etf_dir / "etf_latest.json"
        with open(latest_file, "w") as f:
            json.dump(output_data, f)

        # Act
        result = orchestrator.analyze_holding(
            ticker="VUSA.L",
            asset_class="etf",
            currency="USD",
        )

        # Assert
        assert result.fundamental_analysis is not None
        assert result.fundamental_analysis["expense_ratio"] == approx(0.07)
        assert result.fundamental_analysis["tracking_error"] == approx(0.02)
        assert len(result.fundamental_analysis["holdings"]) == 2