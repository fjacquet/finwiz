"""
Unit tests for JSON to HTML converter.
"""

import json
from pathlib import Path

import pytest
from pytest import approx

from finwiz.infrastructure.json.to_html_converter import JsonToHtmlConverter


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

    def test_should_convert_deep_analysis_json_without_processing_time(self, converter, sample_deep_analysis_json):
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
        raw_output = "ticker='AAPL' composite_score=0.85 grade='A' risk_details={'volatility': 0.25, 'beta': 1.0}"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["composite_score"] == approx(0.85)
        assert result["grade"] == "A"
        assert "risk_details" in result
        assert result["risk_details"]["volatility"] == approx(0.25)

    def test_should_provide_default_values_for_missing_fields(self, converter, sample_deep_analysis_json):
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


class TestParseRawOutput:
    """Comprehensive tests for _parse_raw_output method."""

    @pytest.fixture
    def converter(self):
        """Create converter instance."""
        return JsonToHtmlConverter()

    def test_should_parse_nested_dict_with_multiple_levels(self, converter):
        """Test parsing deeply nested dictionaries (main bug fix)."""
        # Arrange - Real-world data_quality structure with nested field_tracking
        raw_output = "ticker='CVLT' data_quality={'quality_score': 0.95, 'field_tracking': {'calculated': 12, 'fetched': 5, 'missing': 2}}"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "CVLT"
        assert "data_quality" in result
        assert result["data_quality"]["quality_score"] == approx(0.95)
        assert result["data_quality"]["field_tracking"]["calculated"] == 12
        assert result["data_quality"]["field_tracking"]["fetched"] == 5
        assert result["data_quality"]["field_tracking"]["missing"] == 2

    def test_should_parse_risk_details_with_all_fields(self, converter):
        """Test parsing risk_details dictionary with all fields."""
        # Arrange
        raw_output = (
            "risk_details={'volatility': 0.487, 'volatility_score': 0.4, "
            "'max_drawdown': -0.35, 'max_drawdown_score': 0.3, 'beta': 1.8, "
            "'beta_score': 0.2, 'overall_risk_score': 0.3}"
        )
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert "risk_details" in result
        risk = result["risk_details"]
        assert risk["volatility"] == approx(0.487)
        assert risk["volatility_score"] == approx(0.4)
        assert risk["max_drawdown"] == approx(-0.35)
        assert risk["beta"] == approx(1.8)
        assert risk["overall_risk_score"] == approx(0.3)

    def test_should_parse_fundamental_details_with_all_fields(self, converter):
        """Test parsing fundamental_details dictionary."""
        # Arrange
        raw_output = "fundamental_details={'roe': 0.18, 'roe_score': 0.7, 'revenue_growth': 0.15, 'revenue_growth_score': 0.6, 'debt_to_equity': 0.5, 'debt_to_equity_score': 0.8}"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert "fundamental_details" in result
        fundamental = result["fundamental_details"]
        assert fundamental["roe"] == approx(0.18)
        assert fundamental["revenue_growth"] == approx(0.15)
        assert fundamental["debt_to_equity"] == approx(0.5)

    def test_should_parse_technical_details_with_all_fields(self, converter):
        """Test parsing technical_details dictionary."""
        # Arrange
        raw_output = "technical_details={'rsi': 66.15, 'rsi_score': 0.5, 'macd': 0.25, 'macd_score': 0.6, 'trend': 'bullish'}"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert "technical_details" in result
        tech = result["technical_details"]
        assert tech["rsi"] == approx(66.15)
        assert tech["macd"] == approx(0.25)
        assert tech["trend"] == "bullish"

    def test_should_parse_list_values(self, converter):
        """Test parsing list values."""
        # Arrange
        raw_output = "competitive_advantages=['Scale', 'Brand', 'Distribution'] ticker='AAPL'"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert "competitive_advantages" in result
        assert result["competitive_advantages"] == ["Scale", "Brand", "Distribution"]
        assert result["ticker"] == "AAPL"

    def test_should_parse_list_with_nested_dicts(self, converter):
        """Test parsing lists containing dictionaries."""
        # Arrange
        raw_output = "scenarios=[{'name': 'bull', 'probability': 0.3}, {'name': 'bear', 'probability': 0.2}]"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert "scenarios" in result
        assert len(result["scenarios"]) == 2
        assert result["scenarios"][0]["name"] == "bull"
        assert result["scenarios"][0]["probability"] == approx(0.3)

    def test_should_parse_boolean_values(self, converter):
        """Test parsing Python-style boolean values."""
        # Arrange
        raw_output = "is_valid=True is_risky=False has_data=True"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["is_valid"] is True
        assert result["is_risky"] is False
        assert result["has_data"] is True

    def test_should_parse_none_values(self, converter):
        """Test parsing None values."""
        # Arrange
        raw_output = "ticker='AAPL' previous_grade=None"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["previous_grade"] is None

    def test_should_parse_integer_and_float_values(self, converter):
        """Test parsing numeric values (int and float)."""
        # Arrange
        raw_output = "count=42 score=0.85 negative=-15 decimal=3.14159"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["count"] == 42
        assert result["score"] == approx(0.85)
        assert result["negative"] == -15
        assert result["decimal"] == approx(3.14159)

    def test_should_parse_single_quoted_strings(self, converter):
        """Test parsing single-quoted string values."""
        # Arrange
        raw_output = "ticker='AAPL' grade='A+' recommendation='STRONG BUY'"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "AAPL"
        assert result["grade"] == "A+"
        assert result["recommendation"] == "STRONG BUY"

    def test_should_parse_double_quoted_strings(self, converter):
        """Test parsing double-quoted string values."""
        # Arrange
        raw_output = 'ticker="MSFT" grade="B" reason="Stable growth"'
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["ticker"] == "MSFT"
        assert result["grade"] == "B"
        assert result["reason"] == "Stable growth"

    def test_should_handle_real_world_complex_output(self, converter):
        """Test parsing real-world complex raw_output string."""
        # Arrange - Actual format from deep analysis crew
        raw_output = (
            "ticker='RBRK' asset_class='stock' composite_score=0.67 grade='C' "
            "recommendation='HOLD' rationale='Mixed signals' "
            "risk_details={'volatility': 0.487, 'volatility_score': 0.4, 'max_drawdown': -0.35, "
            "'max_drawdown_score': 0.3, 'beta': 1.8, 'beta_score': 0.2} "
            "fundamental_details={'roe': 0.18, 'roe_score': 0.7, 'debt_to_equity': 0.5} "
            "technical_details={'rsi': 66.15, 'rsi_score': 0.5, 'macd': 0.25} "
            "data_quality={'quality_score': 0.95, 'field_tracking': {'calculated': 12, 'fetched': 5}}"
        )
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert - Verify all top-level fields
        assert result["ticker"] == "RBRK"
        assert result["asset_class"] == "stock"
        assert result["composite_score"] == approx(0.67)
        assert result["grade"] == "C"
        assert result["recommendation"] == "HOLD"

        # Assert - Verify nested dictionaries
        assert result["risk_details"]["volatility"] == approx(0.487)
        assert result["risk_details"]["beta"] == approx(1.8)
        assert result["fundamental_details"]["roe"] == approx(0.18)
        assert result["technical_details"]["rsi"] == approx(66.15)

        # Assert - Verify deeply nested data_quality
        assert result["data_quality"]["quality_score"] == approx(0.95)
        assert result["data_quality"]["field_tracking"]["calculated"] == 12
        assert result["data_quality"]["field_tracking"]["fetched"] == 5

    def test_should_preserve_existing_context(self, converter):
        """Test that existing context values are preserved."""
        # Arrange
        raw_output = "ticker='AAPL' score=0.9"
        context = {"existing_key": "existing_value", "ticker": "OLD_VALUE"}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["existing_key"] == "existing_value"
        assert result["ticker"] == "AAPL"  # Overwritten
        assert result["score"] == approx(0.9)

    def test_should_handle_empty_dicts_and_lists(self, converter):
        """Test parsing empty dictionaries and lists."""
        # Arrange
        raw_output = "empty_dict={} empty_list=[] ticker='TEST'"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["empty_dict"] == {}
        assert result["empty_list"] == []
        assert result["ticker"] == "TEST"

    def test_should_handle_strings_with_equals_sign(self, converter):
        """Test parsing strings that contain equals sign."""
        # Arrange
        raw_output = "formula='a=b+c' equation='x=1'"
        context = {}

        # Act
        result = converter._parse_raw_output(raw_output, context)

        # Assert
        assert result["formula"] == "a=b+c"
        assert result["equation"] == "x=1"

    def test_should_not_map_the_retired_discovery_latest_name(self, converter):
        """discovery_latest.json has no writer anywhere; the mapping entry is dead (task-11, 11a)."""
        assert "discovery_latest.json" not in converter.TEMPLATE_MAPPING

    def test_should_still_map_discovery_output_glob_to_the_same_template(self, converter):
        """The glob pattern discovery actually writes files under stays mapped."""
        assert converter.TEMPLATE_MAPPING["discovery_output_*.json"] == "discovery_latest.html"
