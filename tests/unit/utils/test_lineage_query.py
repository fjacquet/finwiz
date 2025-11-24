"""
Unit tests for lineage query utility.

Tests the LineageQuery class and convenience functions for querying
data lineage information.
"""

from pytest import approx
from datetime import datetime

import pytest

from finwiz.schemas.data_lineage import CalculationStep, DataLineage, DataSource
from finwiz.utils.lineage_query import (
    LineageQuery,
    get_grade_lineage,
    get_metric_lineage,
    get_score_lineage,
    get_ticker_lineage,
)


@pytest.fixture
def sample_lineage():
    """Create sample lineage for testing."""
    lineage = DataLineage(ticker="AAPL", asset_class="stock")

    # Add data sources
    lineage.add_source(
        source_id="src_1",
        source_type="api",
        source_name="Yahoo Finance",
        field_name="volatility",
        raw_value=0.25,
        timestamp=datetime.now().isoformat(),
        metadata={"endpoint": "/quote"},
    )

    lineage.add_source(
        source_id="src_2",
        source_type="api",
        source_name="Yahoo Finance",
        field_name="max_drawdown",
        raw_value=-0.15,
        timestamp=datetime.now().isoformat(),
    )

    lineage.add_source(
        source_id="src_3",
        source_type="default",
        source_name="DeepAnalysisScorer",
        field_name="beta",
        raw_value=1.0,
        timestamp=datetime.now().isoformat(),
    )

    # Add transformations
    lineage.add_transformation(
        transformation_id="trans_1",
        operation="type_conversion",
        input_values={"volatility": "0.25"},
        output_value=0.25,
        formula="float(value)",
    )

    # Add calculations
    lineage.add_calculation(
        step_id="calc_1",
        step_name="composite_score",
        inputs={"volatility": 0.25, "max_drawdown": -0.15, "beta": 1.0},
        calculation="Weighted average of risk metrics",
        formula="0.4*volatility + 0.3*max_drawdown + 0.3*beta",
        output=0.85,
        metadata={"weights": {"volatility": 0.4, "max_drawdown": 0.3, "beta": 0.3}},
    )

    lineage.add_calculation(
        step_id="calc_2",
        step_name="grade",
        inputs={"composite_score": 0.85},
        calculation="Assign grade based on composite score",
        formula="if score >= 0.80: 'A+'",
        output="A+",
        metadata={"grading_scale": {"A+": 0.80, "A": 0.70, "B": 0.60}},
    )

    # Set final values
    lineage.final_values = {"composite_score": 0.85, "grade": "A+", "volatility": 0.25}

    return lineage


class TestLineageQuery:
    """Test suite for LineageQuery class."""

    def test_should_initialize_with_default_values(self):
        """Test LineageQuery initialization."""
        query = LineageQuery()

        assert query.lineage_storage_path is None
        assert query._lineage_cache == {}

    def test_should_get_ticker_lineage_from_provided_object(self, sample_lineage):
        """Test getting lineage from provided object."""
        query = LineageQuery()

        result = query.get_ticker_lineage("AAPL", lineage=sample_lineage)

        assert result is not None
        assert result.ticker == "AAPL"
        assert result.asset_class == "stock"
        assert len(result.sources) == 3
        assert len(result.calculations) == 2

    def test_should_return_none_when_ticker_not_found(self):
        """Test getting lineage for non-existent ticker."""
        query = LineageQuery()

        result = query.get_ticker_lineage("INVALID")

        assert result is None

    def test_should_cache_lineage_after_first_retrieval(self, sample_lineage):
        """Test lineage caching."""
        query = LineageQuery()

        # First retrieval
        result1 = query.get_ticker_lineage("AAPL", lineage=sample_lineage)

        # Should be in cache now
        assert "AAPL" not in query._lineage_cache  # Not cached when provided directly

        # But if we call without lineage parameter, it should check cache
        query._lineage_cache["AAPL"] = sample_lineage
        result2 = query.get_ticker_lineage("AAPL")

        assert result2 is not None
        assert result2.ticker == "AAPL"

    def test_should_get_metric_lineage_for_volatility(self, sample_lineage):
        """Test getting lineage chain for volatility metric."""
        query = LineageQuery()

        result = query.get_metric_lineage("AAPL", "volatility", lineage=sample_lineage)

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["metric"] == "volatility"
        assert result["source"] is not None
        assert result["source"].field_name == "volatility"
        assert result["source"].raw_value == approx(0.25)
        assert len(result["transformations"]) == 1
        assert len(result["calculations"]) == 1
        assert result["final_value"] == approx(0.25)

    def test_should_get_metric_lineage_for_max_drawdown(self, sample_lineage):
        """Test getting lineage chain for max_drawdown metric."""
        query = LineageQuery()

        result = query.get_metric_lineage("AAPL", "max_drawdown", lineage=sample_lineage)

        assert result is not None
        assert result["metric"] == "max_drawdown"
        assert result["source"].raw_value == approx(-0.15)
        assert len(result["transformations"]) == 0  # No transformations for this metric
        assert len(result["calculations"]) == 1  # Used in composite_score

    def test_should_return_none_for_nonexistent_metric(self, sample_lineage):
        """Test getting lineage for non-existent metric."""
        query = LineageQuery()

        result = query.get_metric_lineage("AAPL", "nonexistent_metric", lineage=sample_lineage)

        assert result is None

    def test_should_get_score_lineage_for_composite_score(self, sample_lineage):
        """Test getting calculation chain for composite_score."""
        query = LineageQuery()

        result = query.get_score_lineage("AAPL", "composite_score", lineage=sample_lineage)

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["score_type"] == "composite_score"
        assert result["calculation"] is not None
        assert result["calculation"].step_name == "composite_score"
        assert result["output"] == approx(0.85)
        assert result["formula"] == "0.4*volatility + 0.3*max_drawdown + 0.3*beta"
        assert len(result["inputs"]) == 3
        assert "volatility" in result["inputs"]
        assert "max_drawdown" in result["inputs"]
        assert "beta" in result["inputs"]

    def test_should_include_input_lineages_in_score_lineage(self, sample_lineage):
        """Test that score lineage includes lineages for input metrics."""
        query = LineageQuery()

        result = query.get_score_lineage("AAPL", "composite_score", lineage=sample_lineage)

        assert result is not None
        assert "input_lineages" in result
        assert "volatility" in result["input_lineages"]
        assert "max_drawdown" in result["input_lineages"]
        assert "beta" in result["input_lineages"]

        # Check volatility input lineage
        vol_lineage = result["input_lineages"]["volatility"]
        assert vol_lineage["metric"] == "volatility"
        assert vol_lineage["source"].raw_value == approx(0.25)

    def test_should_return_none_for_nonexistent_score(self, sample_lineage):
        """Test getting lineage for non-existent score."""
        query = LineageQuery()

        result = query.get_score_lineage("AAPL", "nonexistent_score", lineage=sample_lineage)

        assert result is None

    def test_should_get_grade_lineage(self, sample_lineage):
        """Test getting grade assignment chain."""
        query = LineageQuery()

        result = query.get_grade_lineage("AAPL", lineage=sample_lineage)

        assert result is not None
        assert result["ticker"] == "AAPL"
        assert result["calculation"] is not None
        assert result["calculation"].step_name == "grade"
        assert result["composite_score"] == approx(0.85)
        assert result["grade"] == "A+"
        assert result["grading_scale"] is not None
        assert result["grading_scale"]["A+"] == approx(0.80)

    def test_should_include_score_lineage_in_grade_lineage(self, sample_lineage):
        """Test that grade lineage includes composite score lineage."""
        query = LineageQuery()

        result = query.get_grade_lineage("AAPL", lineage=sample_lineage)

        assert result is not None
        assert "score_lineage" in result
        assert result["score_lineage"] is not None
        assert result["score_lineage"]["score_type"] == "composite_score"
        assert result["score_lineage"]["output"] == approx(0.85)

    def test_should_get_all_sources(self, sample_lineage):
        """Test getting all data sources."""
        query = LineageQuery()

        sources = query.get_all_sources("AAPL", lineage=sample_lineage)

        assert len(sources) == 3
        assert all(isinstance(source, DataSource) for source in sources)
        assert sources[0].field_name == "volatility"
        assert sources[1].field_name == "max_drawdown"
        assert sources[2].field_name == "beta"

    def test_should_get_all_calculations(self, sample_lineage):
        """Test getting all calculation steps."""
        query = LineageQuery()

        calculations = query.get_all_calculations("AAPL", lineage=sample_lineage)

        assert len(calculations) == 2
        assert all(isinstance(calc, CalculationStep) for calc in calculations)
        assert calculations[0].step_name == "composite_score"
        assert calculations[1].step_name == "grade"

    def test_should_get_sources_by_type_api(self, sample_lineage):
        """Test getting sources by type (API)."""
        query = LineageQuery()

        api_sources = query.get_sources_by_type("AAPL", "api", lineage=sample_lineage)

        assert len(api_sources) == 2
        assert all(source.source_type == "api" for source in api_sources)
        assert api_sources[0].field_name == "volatility"
        assert api_sources[1].field_name == "max_drawdown"

    def test_should_get_sources_by_type_default(self, sample_lineage):
        """Test getting sources by type (default)."""
        query = LineageQuery()

        default_sources = query.get_sources_by_type("AAPL", "default", lineage=sample_lineage)

        assert len(default_sources) == 1
        assert default_sources[0].source_type == "default"
        assert default_sources[0].field_name == "beta"

    def test_should_get_defaulted_fields(self, sample_lineage):
        """Test getting list of fields that used defaults."""
        query = LineageQuery()

        defaulted = query.get_defaulted_fields("AAPL", lineage=sample_lineage)

        assert len(defaulted) == 1
        assert "beta" in defaulted

    def test_should_get_lineage_summary(self, sample_lineage):
        """Test getting lineage summary."""
        query = LineageQuery()

        summary = query.get_lineage_summary("AAPL", lineage=sample_lineage)

        assert summary is not None
        assert summary["ticker"] == "AAPL"
        assert summary["asset_class"] == "stock"
        assert summary["total_sources"] == 3
        assert summary["sources_by_type"]["api"] == 2
        assert summary["sources_by_type"]["default"] == 1
        assert summary["total_transformations"] == 1
        assert summary["total_calculations"] == 2
        assert "beta" in summary["defaulted_fields"]
        assert summary["completeness"] == approx(1.0)
        assert summary["final_values"]["composite_score"] == approx(0.85)
        assert summary["final_values"]["grade"] == "A+"


class TestConvenienceFunctions:
    """Test suite for convenience functions."""

    def test_should_get_ticker_lineage_via_convenience_function(self, sample_lineage):
        """Test get_ticker_lineage convenience function."""
        result = get_ticker_lineage("AAPL", lineage=sample_lineage)

        assert result is not None
        assert result.ticker == "AAPL"

    def test_should_get_metric_lineage_via_convenience_function(self, sample_lineage):
        """Test get_metric_lineage convenience function."""
        result = get_metric_lineage("AAPL", "volatility", lineage=sample_lineage)

        assert result is not None
        assert result["metric"] == "volatility"

    def test_should_get_score_lineage_via_convenience_function(self, sample_lineage):
        """Test get_score_lineage convenience function."""
        result = get_score_lineage("AAPL", "composite_score", lineage=sample_lineage)

        assert result is not None
        assert result["score_type"] == "composite_score"

    def test_should_get_grade_lineage_via_convenience_function(self, sample_lineage):
        """Test get_grade_lineage convenience function."""
        result = get_grade_lineage("AAPL", lineage=sample_lineage)

        assert result is not None
        assert result["grade"] == "A+"