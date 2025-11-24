"""
Unit tests for lineage HTML integration.

Tests the HTML integration functions for data lineage in reports.
"""

from datetime import datetime

import pytest
from pytest import approx

from finwiz.schemas.data_lineage import DataLineage
from finwiz.utils.lineage_html_integration import (
    add_lineage_to_report_data,
    generate_lineage_section_html,
    get_lineage_quality_badge,
)


@pytest.fixture
def sample_lineage_dict():
    """Create sample lineage dictionary for testing."""
    lineage = DataLineage(
        ticker="AAPL",
        asset_class="stock",
        scorer_version="1.0.0",
        formula_version="1.0.0",
    )

    lineage.add_source(
        source_id="src_1",
        source_type="api",
        source_name="Yahoo Finance",
        field_name="volatility",
        raw_value=0.25,
        timestamp=datetime.now().isoformat(),
    )

    lineage.add_source(
        source_id="src_2",
        source_type="default",
        source_name="Default",
        field_name="beta",
        raw_value=1.0,
        timestamp=datetime.now().isoformat(),
    )

    lineage.add_calculation(
        step_id="calc_1",
        step_name="composite_score",
        inputs={"volatility": 0.25, "beta": 1.0},
        calculation="Weighted average",
        formula="0.5*volatility + 0.5*beta",
        output=0.625,
    )

    lineage.final_values = {"composite_score": 0.625, "grade": "B"}

    return lineage.model_dump()


class TestGenerateLineageSectionHTML:
    """Test suite for generate_lineage_section_html function."""

    def test_should_generate_html_with_lineage(self, sample_lineage_dict):
        """Test generating HTML section with valid lineage."""
        html = generate_lineage_section_html(sample_lineage_dict, "AAPL")

        assert "Data Lineage" in html
        assert "AAPL" in html
        assert "stock" in html
        assert "volatility" in html
        assert "beta" in html
        assert "mermaid" in html
        assert "flowchart" in html

    def test_should_show_defaulted_fields_warning(self, sample_lineage_dict):
        """Test that defaulted fields show warning."""
        html = generate_lineage_section_html(sample_lineage_dict, "AAPL")

        assert "⚠️ Note:" in html
        assert "default values" in html
        assert "beta" in html

    def test_should_show_sources_by_type(self, sample_lineage_dict):
        """Test that sources are grouped by type."""
        html = generate_lineage_section_html(sample_lineage_dict, "AAPL")

        assert "Data Sources by Type" in html
        assert "api" in html
        assert "default" in html

    def test_should_include_mermaid_script(self, sample_lineage_dict):
        """Test that Mermaid.js script is included."""
        html = generate_lineage_section_html(sample_lineage_dict, "AAPL")

        assert "mermaid.min.js" in html
        assert "mermaid.initialize" in html

    def test_should_handle_none_lineage(self):
        """Test handling None lineage."""
        html = generate_lineage_section_html(None, "AAPL")

        assert "Data Lineage" in html
        assert "not available" in html

    def test_should_handle_empty_lineage_dict(self):
        """Test handling empty lineage dictionary."""
        html = generate_lineage_section_html({}, "AAPL")

        # Should show error or not available message
        assert "Data Lineage" in html


class TestAddLineageToReportData:
    """Test suite for add_lineage_to_report_data function."""

    def test_should_add_lineage_to_report_data(self, sample_lineage_dict):
        """Test adding lineage to report data."""
        report_data = {"ticker": "AAPL", "grade": "B"}

        result = add_lineage_to_report_data(report_data, sample_lineage_dict)

        assert result["has_lineage"] is True
        assert "lineage" in result
        assert "lineage_summary" in result
        assert "lineage_html" in result

    def test_should_include_lineage_summary(self, sample_lineage_dict):
        """Test that lineage summary is included."""
        report_data = {"ticker": "AAPL"}

        result = add_lineage_to_report_data(report_data, sample_lineage_dict)

        summary = result["lineage_summary"]
        assert summary["total_sources"] == 2
        assert summary["total_calculations"] == 1
        assert summary["completeness"] == approx(1.0)
        assert "beta" in summary["defaulted_fields"]

    def test_should_generate_lineage_html(self, sample_lineage_dict):
        """Test that lineage HTML is generated."""
        report_data = {"ticker": "AAPL"}

        result = add_lineage_to_report_data(report_data, sample_lineage_dict)

        assert result["lineage_html"]
        assert "Data Lineage" in result["lineage_html"]
        assert "mermaid" in result["lineage_html"]

    def test_should_handle_none_lineage(self):
        """Test handling None lineage."""
        report_data = {"ticker": "AAPL"}

        result = add_lineage_to_report_data(report_data, None)

        assert result["has_lineage"] is False
        assert result["lineage_html"] == ""

    def test_should_preserve_existing_report_data(self, sample_lineage_dict):
        """Test that existing report data is preserved."""
        report_data = {"ticker": "AAPL", "grade": "B", "score": 0.8}

        result = add_lineage_to_report_data(report_data, sample_lineage_dict)

        assert result["ticker"] == "AAPL"
        assert result["grade"] == "B"
        assert result["score"] == approx(0.8)


class TestGetLineageQualityBadge:
    """Test suite for get_lineage_quality_badge function."""

    def test_should_return_high_quality_badge_for_no_defaults(self):
        """Test high quality badge when no defaults."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")
        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
            timestamp=datetime.now().isoformat(),
        )

        badge = get_lineage_quality_badge(lineage.model_dump())

        assert "✅ High Quality Data" in badge
        assert "#28a745" in badge  # Green color

    def test_should_return_some_estimates_badge_for_few_defaults(self, sample_lineage_dict):
        """Test some estimates badge when <30% defaults."""
        badge = get_lineage_quality_badge(sample_lineage_dict)

        # 1 default out of 2 sources = 50%, should show "Some Estimates"
        assert "⚠️" in badge

    def test_should_return_limited_data_badge_for_many_defaults(self):
        """Test limited data badge when >=30% defaults."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")
        lineage.add_source(
            source_id="src_1",
            source_type="default",
            source_name="Default",
            field_name="volatility",
            raw_value=0.2,
            timestamp=datetime.now().isoformat(),
        )
        lineage.add_source(
            source_id="src_2",
            source_type="default",
            source_name="Default",
            field_name="beta",
            raw_value=1.0,
            timestamp=datetime.now().isoformat(),
        )

        badge = get_lineage_quality_badge(lineage.model_dump())

        assert "⚠️ Limited Data" in badge
        assert "#dc3545" in badge  # Red color

    def test_should_handle_none_lineage(self):
        """Test handling None lineage."""
        badge = get_lineage_quality_badge(None)

        assert "ℹ️ No Lineage" in badge
        assert "#6c757d" in badge  # Gray color

    def test_should_handle_empty_sources(self):
        """Test handling lineage with no sources."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        badge = get_lineage_quality_badge(lineage.model_dump())

        assert "ℹ️ No Data" in badge

    def test_should_include_badge_styling(self):
        """Test that badge includes proper styling."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")
        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
            timestamp=datetime.now().isoformat(),
        )

        badge = get_lineage_quality_badge(lineage.model_dump())

        assert "badge" in badge
        assert "padding" in badge
        assert "border-radius" in badge
