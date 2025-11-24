"""
Unit tests for JSON to HTML converter.
"""

import json
from pathlib import Path

import pytest
from pytest import approx

from finwiz.utils.json_to_html_converter import JsonToHtmlConverter


class TestJsonToHtmlConverter:
    """Test suite for JsonToHtmlConverter."""

    @pytest.fixture
    def converter(self, tmp_path):
        """Create converter instance with temp directory."""
        return JsonToHtmlConverter()

    @pytest.fixture
    def sample_deep_analysis_json(self, tmp_path):
        """Create sample deep analysis JSON file."""
        json_data = {
            "raw_output": "ticker='AAPL' asset_class='stock' crew_name='python_scorer' "
            "analysis_timestamp='2025-11-23T21:11:39.132143' composite_score=0.85 "
            "grade='A' recommendation='BUY' rationale='Strong fundamentals' "
            "risk_details={'volatility': 0.25, 'max_drawdown': -0.15, 'beta': 1.0} "
            "fundamental_score=0.9 technical_score=0.8 risk_score=0.85 "
            "fundamental_details={'roe': 0.25, 'debt_to_equity': 0.2} "
            "technical_details={'rsi': 55.0, 'macd': 0.5}",
            "metadata": {
                "crew_name": "deep_analysis_stock",
                "storage_timestamp": "2025-11-23T21:11:39.133361",
            },
        }

        json_path = tmp_path / "deep_analysis_stock_output_test.json"
        json_path.write_text(json.dumps(json_data))
        return json_path

    def test_should_convert_deep_analysis_json_without_processing_time(
        self, converter, sample_deep_analysis_json
    ):
        """Test conversion of deep analysis JSON without processing_time_seconds field."""
        # Act
        result = converter.convert_file(sample_deep_analysis_json)

        # Assert
        assert result is not None
        html_path = Path(result)
        assert html_path.exists()
        assert html_path.suffix == ".html"

        # Verify HTML content
        html_content = html_path.read_text()
        assert "AAPL" in html_content
        assert "BUY" in html_content
        assert "Grade A" in html_content

    def test_should_parse_raw_output_fields(self, converter):
        """Test parsing of raw_output string to extract fields."""
        # Arrange
        raw_output = (
            "ticker='AAPL' composite_score=0.85 grade='A' "
            "risk_details={'volatility': 0.25, 'beta': 1.0}"
        )
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["composite_score"] == approx(0.85)
        assert result["grade"] == "A"
        assert "risk_details" in result
        assert result["risk_details"]["volatility"] == approx(0.25)

    def test_should_provide_default_values_for_missing_fields(
        self, converter, sample_deep_analysis_json
    ):
        """Test that missing template fields get default values."""
        # Act
        result = converter.convert_file(sample_deep_analysis_json)

        # Assert - should not fail even with missing fields
        assert result is not None

    def test_should_handle_malformed_json(self, converter, tmp_path):
        """Test handling of malformed JSON files."""
        # Arrange
        json_path = tmp_path / "malformed.json"
        json_path.write_text("{invalid json")

        # Act
        result = converter.convert_file(json_path)

        # Assert
        assert result is None  # Should return None for malformed JSON

    def test_should_skip_empty_json(self, converter, tmp_path):
        """Test handling of empty JSON files."""
        # Arrange
        json_path = tmp_path / "empty.json"
        json_path.write_text("{}")

        # Act
        result = converter.convert_file(json_path)

        # Assert
        assert result is None  # Should skip empty files

    def test_should_infer_asset_class_from_filename(self, converter):
        """Test asset class inference from file path."""
        # Test stock
        assert converter._infer_asset_class(Path("deep_analysis_stock_output.json")) == "stock"

        # Test ETF
        assert converter._infer_asset_class(Path("deep_analysis_etf_output.json")) == "etf"

        # Test crypto
        assert converter._infer_asset_class(Path("deep_analysis_crypto_output.json")) == "crypto"

        # Test unknown
        assert converter._infer_asset_class(Path("unknown_output.json")) == "mixed"
