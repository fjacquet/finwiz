"""
Unit tests for Report Consolidator.

Tests Python-based consolidation of crew JSON exports (NO AI).
Following AI Minimalism principle: deterministic Python, not AI agents.
"""

import json
from datetime import UTC, datetime

import pytest

from finwiz.schemas.crew_exports import (
    ConsolidatedReportExport,
    StockCrewExport,
)
from finwiz.utils.report_consolidator import ReportConsolidator
from finwiz.utils.report_export_loaders import load_exports


class TestReportConsolidator:
    """Test suite for ReportConsolidator."""

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "reports" / "test-session"
        output_dir.mkdir(parents=True)
        return output_dir

    @pytest.fixture
    def consolidator(self, temp_output_dir):
        """Create ReportConsolidator instance."""
        return ReportConsolidator(session_id="test-session-123", output_dir=temp_output_dir)

    @pytest.fixture
    def mock_stock_export_file(self, tmp_path):
        """Create mock stock export JSON file."""
        export_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test-session-123",
            "analysis_date": datetime.now(UTC).isoformat(),
            "fundamental_analysis": {
                "ticker": "AAPL",
                "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
                "filed_at": datetime.now(UTC).isoformat(),
                "section": "Item 1A",
                "excerpt": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                "sec_citation": "10-K (2024), Item 1A, p. 17",
            },
            "risk_assessment": {
                "score": 3.5,
                "level": "Medium",
                "risk_factors": ["Market competition", "Regulatory changes"],
            },
            "technical_indicators": {"rsi": 65, "macd": 0.5},
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects and solid balance sheet.",
            "data_sources": ["Yahoo Finance", "SEC EDGAR"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        file_path = tmp_path / "stock_export.json"
        file_path.write_text(json.dumps(export_data), encoding="utf-8")
        return file_path

    @pytest.fixture
    def mock_etf_export_file(self, tmp_path):
        """Create mock ETF export JSON file."""
        export_data = {
            "crew_name": "etf_crew",
            "ticker": "SPY",
            "asset_class": "etf",
            "session_id": "test-session-123",
            "analysis_date": datetime.now(UTC).isoformat(),
            "factsheet": {
                "ticker": "SPY",
                "issuer": "State Street Global Advisors",
                "expense_ratio": 0.09,
                "factsheet_url": "https://www.ssga.com/us/en/individual/etfs/funds/spdr-sp-500-etf-trust-spy",
                "as_of": datetime.now().date().isoformat(),
            },
            "top_holdings": [
                {
                    "ticker": "AAPL",
                    "weight_pct": 7.5,
                    "source_url": "https://www.ssga.com/holdings",
                    "as_of": datetime.now().date().isoformat(),
                },
                {
                    "ticker": "MSFT",
                    "weight_pct": 6.8,
                    "source_url": "https://www.ssga.com/holdings",
                    "as_of": datetime.now().date().isoformat(),
                },
            ],
            "risk_assessment": {
                "score": 4.0,
                "level": "High",
                "risk_factors": ["Market volatility"],
            },
            "composite_score": 0.78,
            "grade": "B",
            "expense_ratio": 0.09,
            "tracking_error": 0.05,
            "recommendation": "HOLD",
            "confidence": 0.85,
            "rationale": "Solid tracking performance with low expense ratio and good diversification.",
            "data_sources": ["Yahoo Finance", "ETF.com"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        file_path = tmp_path / "etf_export.json"
        file_path.write_text(json.dumps(export_data), encoding="utf-8")
        return file_path

    @pytest.fixture
    def mock_crypto_export_file(self, tmp_path):
        """Create mock crypto export JSON file."""
        export_data = {
            "crew_name": "crypto_crew",
            "ticker": "BTC",
            "asset_class": "crypto",
            "session_id": "test-session-123",
            "analysis_date": datetime.now(UTC).isoformat(),
            "thesis": {
                "symbol": "BTC",
                "thesis_bullets": ["Digital gold with strong network effects", "First mover advantage", "Network security"],
                "references": ["https://bitcoin.org/bitcoin.pdf"],
            },
            "risk_assessment": {
                "score": 5.0,
                "level": "Very High",
                "risk_factors": ["High volatility", "Regulatory risk"],
            },
            "technical_analysis": {"support": 40000, "resistance": 50000},
            "composite_score": 0.72,
            "grade": "C+",
            "volatility_30d": 0.65,
            "max_drawdown": -0.35,
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "High volatility but strong network effects and institutional adoption.",
            "data_sources": ["CoinMarketCap", "Kraken"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        file_path = tmp_path / "crypto_export.json"
        file_path.write_text(json.dumps(export_data), encoding="utf-8")
        return file_path

    def test_should_consolidate_stock_exports_when_valid_files(self, consolidator, mock_stock_export_file):
        """Test consolidating stock crew exports."""
        # Arrange
        crew_export_paths = {"stock_crew": [str(mock_stock_export_file)]}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert isinstance(result, ConsolidatedReportExport)
        assert result.session_id == "test-session-123"
        assert len(result.stock_analyses) == 1
        assert result.stock_analyses[0].ticker == "AAPL"
        assert result.stock_analyses[0].grade == "A"
        assert result.crew_execution_status["stock_crew"] == "completed"

    def test_should_consolidate_multiple_crew_types(
        self,
        consolidator,
        mock_stock_export_file,
        mock_etf_export_file,
        mock_crypto_export_file,
    ):
        """Test consolidating multiple crew types."""
        # Arrange
        crew_export_paths = {
            "stock_crew": [str(mock_stock_export_file)],
            "etf_crew": [str(mock_etf_export_file)],
            "crypto_crew": [str(mock_crypto_export_file)],
        }

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert len(result.stock_analyses) == 1
        assert len(result.etf_analyses) == 1
        assert len(result.crypto_analyses) == 1
        assert result.crew_execution_status["stock_crew"] == "completed"
        assert result.crew_execution_status["etf_crew"] == "completed"
        assert result.crew_execution_status["crypto_crew"] == "completed"

    def test_should_handle_missing_files_gracefully(self, consolidator):
        """Test handling of missing export files."""
        # Arrange
        crew_export_paths = {
            "stock_crew": ["/nonexistent/file.json"],
        }

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert len(result.stock_analyses) == 0
        assert result.crew_execution_status["stock_crew"] == "failed"
        assert len(result.errors) > 0
        assert any("not found" in error.lower() for error in result.errors)

    def test_should_handle_invalid_json_gracefully(self, consolidator, tmp_path):
        """Test handling of invalid JSON files."""
        # Arrange
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }", encoding="utf-8")
        crew_export_paths = {"stock_crew": [str(invalid_file)]}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert len(result.stock_analyses) == 0
        assert result.crew_execution_status["stock_crew"] == "failed"
        assert len(result.errors) > 0

    def test_should_handle_validation_errors_gracefully(self, consolidator, tmp_path):
        """Test handling of Pydantic validation errors."""
        # Arrange
        invalid_export = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            # Missing required fields
            "composite_score": 1.5,  # Invalid: > 1.0
            "grade": "INVALID",  # Invalid grade
        }
        invalid_file = tmp_path / "invalid_export.json"
        invalid_file.write_text(json.dumps(invalid_export), encoding="utf-8")
        crew_export_paths = {"stock_crew": [str(invalid_file)]}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert len(result.stock_analyses) == 0
        assert result.crew_execution_status["stock_crew"] == "failed"
        assert len(result.errors) > 0
        assert any("validation" in error.lower() for error in result.errors)

    def test_should_save_consolidated_report_to_json(self, consolidator, mock_stock_export_file, temp_output_dir):
        """Test that consolidated report is saved to JSON file."""
        # Arrange
        crew_export_paths = {"stock_crew": [str(mock_stock_export_file)]}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        output_file = temp_output_dir / "consolidated_report.json"
        assert output_file.exists()

        # Verify JSON content
        saved_data = json.loads(output_file.read_text(encoding="utf-8"))
        assert saved_data["session_id"] == "test-session-123"
        assert len(saved_data["stock_analyses"]) == 1

    def test_should_track_execution_time(self, consolidator, mock_stock_export_file):
        """Test that execution time is tracked."""
        # Arrange
        crew_export_paths = {"stock_crew": [str(mock_stock_export_file)]}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert result.total_execution_time > 0
        assert result.total_execution_time < 1.0  # Should be fast (< 1 second)

    def test_should_continue_with_partial_failures(self, consolidator, mock_stock_export_file, tmp_path):
        """Test that consolidation continues with valid exports when some fail."""
        # Arrange
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid }", encoding="utf-8")

        crew_export_paths = {
            "stock_crew": [str(mock_stock_export_file), str(invalid_file)],
        }

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert len(result.stock_analyses) == 1  # One valid export loaded
        assert result.stock_analyses[0].ticker == "AAPL"
        assert len(result.errors) > 0  # Error tracked for invalid file

    def test_should_handle_empty_crew_paths(self, consolidator):
        """Test handling of empty crew export paths."""
        # Arrange
        crew_export_paths = {}

        # Act
        result = consolidator.consolidate_reports(crew_export_paths)

        # Assert
        assert isinstance(result, ConsolidatedReportExport)
        assert len(result.stock_analyses) == 0
        assert len(result.etf_analyses) == 0
        assert len(result.crypto_analyses) == 0
        assert result.total_execution_time >= 0


class TestReportConsolidatorLoadExports:
    """Test the load_exports helper function."""

    def test_should_load_valid_exports(self, tmp_path):
        """Test loading valid export files."""
        # Arrange
        export_data = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test",
            "analysis_date": datetime.now(UTC).isoformat(),
            "fundamental_analysis": {
                "ticker": "AAPL",
                "filing_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193",
                "filed_at": datetime.now(UTC).isoformat(),
                "section": "Item 1A",
                "excerpt": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.",
                "sec_citation": "10-K (2024), Item 1A, p. 17",
            },
            "risk_assessment": {
                "score": 3.0,
                "level": "Medium",
                "risk_factors": [],
            },
            "technical_indicators": {},
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects and solid balance sheet.",
            "data_sources": [],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

        file_path = tmp_path / "export.json"
        file_path.write_text(json.dumps(export_data), encoding="utf-8")

        # Act
        validation_errors: list[dict] = []
        exports = load_exports([str(file_path)], StockCrewExport, crew_name="stock_crew", session_id="test", validation_errors=validation_errors)

        # Assert
        assert len(exports) == 1
        assert isinstance(exports[0], StockCrewExport)
        assert exports[0].ticker == "AAPL"

    def test_should_return_empty_list_when_all_files_invalid(self, tmp_path):
        """Test that empty list is returned when all files are invalid."""
        # Arrange
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }", encoding="utf-8")

        # Act
        validation_errors: list[dict] = []
        exports = load_exports([str(invalid_file)], StockCrewExport, crew_name="stock_crew", session_id="test", validation_errors=validation_errors)

        # Assert
        assert len(exports) == 0

    def test_should_track_validation_errors(self, tmp_path):
        """Test that validation errors are tracked."""
        # Arrange
        invalid_export = {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "composite_score": 1.5,  # Invalid: > 1.0
        }
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text(json.dumps(invalid_export), encoding="utf-8")

        # Act
        validation_errors: list[dict] = []
        exports = load_exports([str(invalid_file)], StockCrewExport, crew_name="stock_crew", session_id="test", validation_errors=validation_errors)

        # Assert
        assert len(exports) == 0
        assert len(validation_errors) > 0
        assert validation_errors[0]["crew"] == "stock_crew"
        assert validation_errors[0]["error_type"] == "validation_error"
