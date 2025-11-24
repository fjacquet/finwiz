"""
Unit tests for data lineage schema.

Tests the DataSource, Transformation, CalculationStep, and DataLineage models
to ensure proper validation and functionality.
"""

from pytest import approx
from datetime import datetime

import pytest
from pydantic import ValidationError

from finwiz.schemas.data_lineage import CalculationStep, DataLineage, DataSource, Transformation


class TestDataSource:
    """Test suite for DataSource model."""

    def test_should_create_valid_data_source(self):
        """Test creating a valid DataSource."""
        source = DataSource(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            timestamp=datetime.now().isoformat(),
            raw_value=0.25,
            field_name="volatility",
            metadata={"endpoint": "/quote"},
        )

        assert source.source_id == "src_1"
        assert source.source_type == "api"
        assert source.source_name == "Yahoo Finance"
        assert source.raw_value == approx(0.25)
        assert source.field_name == "volatility"
        assert source.metadata["endpoint"] == "/quote"

    def test_should_validate_source_type(self):
        """Test that source_type must be one of allowed values."""
        # Valid source types
        valid_types = ["api", "cache", "calculation", "user_input", "default"]
        for source_type in valid_types:
            source = DataSource(
                source_id="src_1",
                source_type=source_type,
                source_name="Test Source",
                timestamp=datetime.now().isoformat(),
                raw_value=1.0,
                field_name="test_field",
            )
            assert source.source_type == source_type

        # Invalid source type
        with pytest.raises(ValidationError):
            DataSource(
                source_id="src_1",
                source_type="invalid_type",
                source_name="Test Source",
                timestamp=datetime.now().isoformat(),
                raw_value=1.0,
                field_name="test_field",
            )

    def test_should_require_all_required_fields(self):
        """Test that all required fields must be provided."""
        # Missing source_id
        with pytest.raises(ValidationError):
            DataSource(
                source_type="api",
                source_name="Test",
                timestamp=datetime.now().isoformat(),
                raw_value=1.0,
                field_name="test",
            )

        # Missing field_name
        with pytest.raises(ValidationError):
            DataSource(
                source_id="src_1",
                source_type="api",
                source_name="Test",
                timestamp=datetime.now().isoformat(),
                raw_value=1.0,
            )

    def test_should_allow_any_raw_value_type(self):
        """Test that raw_value can be any type."""
        # Float
        source1 = DataSource(
            source_id="src_1",
            source_type="api",
            source_name="Test",
            timestamp=datetime.now().isoformat(),
            raw_value=0.25,
            field_name="test",
        )
        assert source1.raw_value == approx(0.25)

        # String
        source2 = DataSource(
            source_id="src_2",
            source_type="api",
            source_name="Test",
            timestamp=datetime.now().isoformat(),
            raw_value="A+",
            field_name="grade",
        )
        assert source2.raw_value == "A+"

        # Dict
        source3 = DataSource(
            source_id="src_3",
            source_type="api",
            source_name="Test",
            timestamp=datetime.now().isoformat(),
            raw_value={"key": "value"},
            field_name="data",
        )
        assert source3.raw_value == {"key": "value"}

    def test_should_have_default_empty_metadata(self):
        """Test that metadata defaults to empty dict."""
        source = DataSource(
            source_id="src_1",
            source_type="api",
            source_name="Test",
            timestamp=datetime.now().isoformat(),
            raw_value=1.0,
            field_name="test",
        )

        assert source.metadata == {}

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            DataSource(
                source_id="src_1",
                source_type="api",
                source_name="Test",
                timestamp=datetime.now().isoformat(),
                raw_value=1.0,
                field_name="test",
                extra_field="not_allowed",
            )


class TestTransformation:
    """Test suite for Transformation model."""

    def test_should_create_valid_transformation(self):
        """Test creating a valid Transformation."""
        transform = Transformation(
            transformation_id="trans_1",
            operation="type_conversion",
            input_values={"volatility": "0.25"},
            output_value=0.25,
            formula="float(value)",
        )

        assert transform.transformation_id == "trans_1"
        assert transform.operation == "type_conversion"
        assert transform.input_values == {"volatility": "0.25"}
        assert transform.output_value == approx(0.25)
        assert transform.formula == "float(value)"

    def test_should_auto_generate_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        transform = Transformation(
            transformation_id="trans_1",
            operation="normalization",
            input_values={"value": 100},
            output_value=1.0,
        )

        assert transform.timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(transform.timestamp)

    def test_should_allow_custom_timestamp(self):
        """Test that custom timestamp can be provided."""
        custom_time = "2025-10-29T10:00:00"
        transform = Transformation(
            transformation_id="trans_1",
            operation="scaling",
            input_values={"value": 50},
            output_value=0.5,
            timestamp=custom_time,
        )

        assert transform.timestamp == custom_time

    def test_should_allow_optional_formula(self):
        """Test that formula is optional."""
        transform = Transformation(
            transformation_id="trans_1",
            operation="normalization",
            input_values={"value": 100},
            output_value=1.0,
        )

        assert transform.formula is None

    def test_should_require_all_required_fields(self):
        """Test that all required fields must be provided."""
        # Missing transformation_id
        with pytest.raises(ValidationError):
            Transformation(
                operation="test",
                input_values={"x": 1},
                output_value=2,
            )

        # Missing input_values
        with pytest.raises(ValidationError):
            Transformation(
                transformation_id="trans_1",
                operation="test",
                output_value=2,
            )

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            Transformation(
                transformation_id="trans_1",
                operation="test",
                input_values={"x": 1},
                output_value=2,
                extra_field="not_allowed",
            )


class TestCalculationStep:
    """Test suite for CalculationStep model."""

    def test_should_create_valid_calculation_step(self):
        """Test creating a valid CalculationStep."""
        calc = CalculationStep(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.25, "max_drawdown": -0.15},
            calculation="Weighted average of risk metrics",
            formula="0.4*volatility + 0.3*max_drawdown",
            output=0.85,
            metadata={"weights": {"volatility": 0.4, "max_drawdown": 0.3}},
        )

        assert calc.step_id == "calc_1"
        assert calc.step_name == "composite_score"
        assert calc.inputs == {"volatility": 0.25, "max_drawdown": -0.15}
        assert calc.calculation == "Weighted average of risk metrics"
        assert calc.formula == "0.4*volatility + 0.3*max_drawdown"
        assert calc.output == approx(0.85)
        assert calc.metadata["weights"]["volatility"] == approx(0.4)

    def test_should_auto_generate_timestamp(self):
        """Test that timestamp is auto-generated if not provided."""
        calc = CalculationStep(
            step_id="calc_1",
            step_name="test_score",
            inputs={"x": 1},
            calculation="Test calculation",
            output=2,
        )

        assert calc.timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(calc.timestamp)

    def test_should_allow_optional_formula(self):
        """Test that formula is optional."""
        calc = CalculationStep(
            step_id="calc_1",
            step_name="test_score",
            inputs={"x": 1},
            calculation="Test calculation",
            output=2,
        )

        assert calc.formula is None

    def test_should_have_default_empty_metadata(self):
        """Test that metadata defaults to empty dict."""
        calc = CalculationStep(
            step_id="calc_1",
            step_name="test_score",
            inputs={"x": 1},
            calculation="Test calculation",
            output=2,
        )

        assert calc.metadata == {}

    def test_should_require_all_required_fields(self):
        """Test that all required fields must be provided."""
        # Missing step_name
        with pytest.raises(ValidationError):
            CalculationStep(
                step_id="calc_1",
                inputs={"x": 1},
                calculation="Test",
                output=2,
            )

        # Missing inputs
        with pytest.raises(ValidationError):
            CalculationStep(
                step_id="calc_1",
                step_name="test",
                calculation="Test",
                output=2,
            )

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            CalculationStep(
                step_id="calc_1",
                step_name="test",
                inputs={"x": 1},
                calculation="Test",
                output=2,
                extra_field="not_allowed",
            )


class TestDataLineage:
    """Test suite for DataLineage model."""

    def test_should_create_valid_data_lineage(self):
        """Test creating a valid DataLineage."""
        lineage = DataLineage(
            ticker="AAPL",
            asset_class="stock",
        )

        assert lineage.ticker == "AAPL"
        assert lineage.asset_class == "stock"
        assert lineage.sources == []
        assert lineage.transformations == []
        assert lineage.calculations == []
        assert lineage.final_values == {}
        assert lineage.completeness == approx(1.0)

    def test_should_auto_generate_analysis_timestamp(self):
        """Test that analysis_timestamp is auto-generated."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        assert lineage.analysis_timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(lineage.analysis_timestamp)

    def test_should_allow_optional_fields(self):
        """Test that optional fields can be None."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        assert lineage.scorer_version is None
        assert lineage.formula_version is None

    def test_should_validate_completeness_range(self):
        """Test that completeness must be between 0.0 and 1.0."""
        # Valid completeness
        lineage1 = DataLineage(ticker="AAPL", asset_class="stock", completeness=0.0)
        assert lineage1.completeness == approx(0.0)

        lineage2 = DataLineage(ticker="AAPL", asset_class="stock", completeness=0.5)
        assert lineage2.completeness == approx(0.5)

        lineage3 = DataLineage(ticker="AAPL", asset_class="stock", completeness=1.0)
        assert lineage3.completeness == approx(1.0)

        # Invalid completeness (< 0)
        with pytest.raises(ValidationError):
            DataLineage(ticker="AAPL", asset_class="stock", completeness=-0.1)

        # Invalid completeness (> 1)
        with pytest.raises(ValidationError):
            DataLineage(ticker="AAPL", asset_class="stock", completeness=1.1)

    def test_should_add_source_via_helper_method(self):
        """Test adding a data source using add_source() method."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
            metadata={"endpoint": "/quote"},
        )

        assert len(lineage.sources) == 1
        assert lineage.sources[0].source_id == "src_1"
        assert lineage.sources[0].field_name == "volatility"
        assert lineage.sources[0].raw_value == approx(0.25)

    def test_should_add_transformation_via_helper_method(self):
        """Test adding a transformation using add_transformation() method."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        lineage.add_transformation(
            transformation_id="trans_1",
            operation="type_conversion",
            input_values={"volatility": "0.25"},
            output_value=0.25,
            formula="float(value)",
        )

        assert len(lineage.transformations) == 1
        assert lineage.transformations[0].transformation_id == "trans_1"
        assert lineage.transformations[0].operation == "type_conversion"

    def test_should_add_calculation_via_helper_method(self):
        """Test adding a calculation using add_calculation() method."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        lineage.add_calculation(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.25},
            calculation="Test calculation",
            output=0.85,
            formula="0.4*volatility",
            metadata={"weights": {"volatility": 0.4}},
        )

        assert len(lineage.calculations) == 1
        assert lineage.calculations[0].step_id == "calc_1"
        assert lineage.calculations[0].step_name == "composite_score"

    def test_should_get_source_by_field_name(self):
        """Test getting a data source by field name."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
        )

        lineage.add_source(
            source_id="src_2",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="max_drawdown",
            raw_value=-0.15,
        )

        # Get existing source
        source = lineage.get_source_by_field("volatility")
        assert source is not None
        assert source.field_name == "volatility"
        assert source.raw_value == approx(0.25)

        # Get non-existent source
        source = lineage.get_source_by_field("nonexistent")
        assert source is None

    def test_should_get_calculation_by_name(self):
        """Test getting a calculation step by name."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        lineage.add_calculation(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.25},
            calculation="Test",
            output=0.85,
        )

        lineage.add_calculation(
            step_id="calc_2",
            step_name="grade",
            inputs={"composite_score": 0.85},
            calculation="Test",
            output="A+",
        )

        # Get existing calculation
        calc = lineage.get_calculation_by_name("composite_score")
        assert calc is not None
        assert calc.step_name == "composite_score"
        assert calc.output == approx(0.85)

        # Get non-existent calculation
        calc = lineage.get_calculation_by_name("nonexistent")
        assert calc is None

    def test_should_get_lineage_chain_for_field(self):
        """Test getting complete lineage chain for a field."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        # Add source
        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
        )

        # Add transformation
        lineage.add_transformation(
            transformation_id="trans_1",
            operation="type_conversion",
            input_values={"volatility": "0.25"},
            output_value=0.25,
        )

        # Add calculation
        lineage.add_calculation(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.25, "max_drawdown": -0.15},
            calculation="Test",
            output=0.85,
        )

        # Get lineage chain
        chain = lineage.get_lineage_chain("volatility")

        assert len(chain) == 3
        assert isinstance(chain[0], DataSource)
        assert isinstance(chain[1], Transformation)
        assert isinstance(chain[2], CalculationStep)

    def test_should_return_empty_chain_for_nonexistent_field(self):
        """Test that empty chain is returned for non-existent field."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        chain = lineage.get_lineage_chain("nonexistent")

        assert chain == []

    def test_should_forbid_extra_fields(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError):
            DataLineage(
                ticker="AAPL",
                asset_class="stock",
                extra_field="not_allowed",
            )

    def test_should_require_ticker_and_asset_class(self):
        """Test that ticker and asset_class are required."""
        # Missing ticker
        with pytest.raises(ValidationError):
            DataLineage(asset_class="stock")

        # Missing asset_class
        with pytest.raises(ValidationError):
            DataLineage(ticker="AAPL")

    def test_should_handle_complex_lineage_chain(self):
        """Test handling a complex lineage with multiple sources and calculations."""
        lineage = DataLineage(ticker="AAPL", asset_class="stock")

        # Add multiple sources
        lineage.add_source(
            source_id="src_1",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="volatility",
            raw_value=0.25,
        )

        lineage.add_source(
            source_id="src_2",
            source_type="api",
            source_name="Yahoo Finance",
            field_name="max_drawdown",
            raw_value=-0.15,
        )

        lineage.add_source(
            source_id="src_3",
            source_type="default",
            source_name="DeepAnalysisScorer",
            field_name="beta",
            raw_value=1.0,
        )

        # Add calculations
        lineage.add_calculation(
            step_id="calc_1",
            step_name="composite_score",
            inputs={"volatility": 0.25, "max_drawdown": -0.15, "beta": 1.0},
            calculation="Weighted average",
            output=0.85,
            formula="0.4*volatility + 0.3*max_drawdown + 0.3*beta",
        )

        lineage.add_calculation(
            step_id="calc_2",
            step_name="grade",
            inputs={"composite_score": 0.85},
            calculation="Grade assignment",
            output="A+",
        )

        # Set final values
        lineage.final_values = {"composite_score": 0.85, "grade": "A+"}

        # Verify structure
        assert len(lineage.sources) == 3
        assert len(lineage.calculations) == 2
        assert lineage.final_values["grade"] == "A+"

        # Verify lineage chains
        vol_chain = lineage.get_lineage_chain("volatility")
        assert len(vol_chain) == 2  # Source + calculation

        beta_chain = lineage.get_lineage_chain("beta")
        assert len(beta_chain) == 2  # Source + calculation