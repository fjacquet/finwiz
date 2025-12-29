"""Tests for crew-specific report generators.

Tests ONLY deterministic Python mechanics:
- Template loading
- Data validation
- Jinja2 rendering
- Sample data generation

Does NOT test AI agent outputs (non-deterministic).
"""

from datetime import datetime

import pytest
from faker import Faker

from finwiz.reporting import (
    CREW_GENERATORS,
    BaseReportGenerator,
    CryptoReportGenerator,
    DiscoveryReportGenerator,
    ETFReportGenerator,
    RebalancingReportGenerator,
    StockReportGenerator,
    get_generator_for_crew,
)

fake = Faker()


class TestBaseReportGeneratorInterface:
    """Tests for the BaseReportGenerator abstract interface."""

    def test_base_cannot_be_instantiated(self):
        """Test that BaseReportGenerator cannot be directly instantiated."""
        with pytest.raises(TypeError):
            BaseReportGenerator()

    def test_all_generators_inherit_from_base(self):
        """Test that all generators inherit from BaseReportGenerator."""
        generators = [
            StockReportGenerator,
            ETFReportGenerator,
            CryptoReportGenerator,
            DiscoveryReportGenerator,
            RebalancingReportGenerator,
        ]
        for gen_class in generators:
            assert issubclass(gen_class, BaseReportGenerator)


class TestCrewGeneratorsRegistry:
    """Tests for the CREW_GENERATORS registry."""

    def test_registry_contains_expected_crews(self):
        """Test that registry contains all expected crew mappings."""
        expected_crews = [
            "stock_crew",
            "etf_crew",
            "crypto_crew",
            "discovery_crew",
            "investment_discovery_crew",
            "rebalancing_crew",
            "portfolio_rebalancing_crew",
        ]
        for crew in expected_crews:
            assert crew in CREW_GENERATORS

    def test_get_generator_for_valid_crew(self):
        """Test get_generator_for_crew returns correct generator."""
        generator = get_generator_for_crew("stock_crew")
        assert isinstance(generator, StockReportGenerator)

        generator = get_generator_for_crew("etf_crew")
        assert isinstance(generator, ETFReportGenerator)

    def test_get_generator_for_invalid_crew(self):
        """Test get_generator_for_crew returns None for unknown crew."""
        generator = get_generator_for_crew("nonexistent_crew")
        assert generator is None


class TestStockReportGenerator:
    """Tests for StockReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a StockReportGenerator instance."""
        return StockReportGenerator()

    def test_template_name(self, generator):
        """Test correct template name is returned."""
        assert generator.get_template_name() == "crew_reports/stock_report.html"

    def test_required_fields(self, generator):
        """Test required fields list."""
        required = generator.get_required_fields()
        assert "ticker" in required
        assert "composite_score" in required
        assert "grade" in required
        assert "recommendation" in required

    def test_validate_data_with_valid_data(self, generator):
        """Test validation passes with valid data."""
        data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals.",
        }
        assert generator.validate_data(data) is True

    def test_validate_data_with_missing_fields(self, generator):
        """Test validation fails with missing required fields."""
        data = {"ticker": "AAPL"}  # Missing required fields
        with pytest.raises(ValueError, match="Missing required fields"):
            generator.validate_data(data)

    def test_prepare_template_variables_adds_defaults(self, generator):
        """Test that prepare_template_variables adds missing defaults."""
        data = {
            "ticker": "AAPL",
            "asset_class": "stock",
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals.",
        }
        prepared = generator.prepare_template_variables(data)

        assert "session_id" in prepared
        assert "analysis_date" in prepared
        assert "data_sources" in prepared
        assert isinstance(prepared["data_sources"], list)

    def test_generate_report_with_sample_data(self, generator):
        """Test that report generation works with sample data."""
        sample = generator.get_sample_data()
        html = generator.generate_report(sample)

        assert len(html) > 100
        assert "AAPL" in html
        assert "BUY" in html

    def test_validate_template(self, generator):
        """Test template validation with sample data."""
        assert generator.validate_template() is True


class TestETFReportGenerator:
    """Tests for ETFReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create an ETFReportGenerator instance."""
        return ETFReportGenerator()

    def test_template_name(self, generator):
        """Test correct template name is returned."""
        assert generator.get_template_name() == "crew_reports/etf_report.html"

    def test_required_fields_includes_expense_ratio(self, generator):
        """Test required fields includes ETF-specific fields."""
        required = generator.get_required_fields()
        assert "expense_ratio" in required

    def test_prepare_template_variables_adds_etf_defaults(self, generator):
        """Test ETF-specific defaults are added."""
        data = {
            "ticker": "VOO",
            "asset_class": "etf",
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Low-cost tracker.",
            "expense_ratio": 0.0003,
        }
        prepared = generator.prepare_template_variables(data)

        assert "tracking_error" in prepared
        assert "factsheet" in prepared

    def test_generate_report_with_sample_data(self, generator):
        """Test that report generation works with sample data."""
        sample = generator.get_sample_data()
        html = generator.generate_report(sample)

        assert len(html) > 100
        assert "VOO" in html


class TestCryptoReportGenerator:
    """Tests for CryptoReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a CryptoReportGenerator instance."""
        return CryptoReportGenerator()

    def test_template_name(self, generator):
        """Test correct template name is returned."""
        assert generator.get_template_name() == "crew_reports/crypto_report.html"

    def test_required_fields_includes_volatility(self, generator):
        """Test required fields includes crypto-specific fields."""
        required = generator.get_required_fields()
        assert "volatility_30d" in required
        assert "max_drawdown" in required

    def test_generate_report_with_sample_data(self, generator):
        """Test that report generation works with sample data."""
        sample = generator.get_sample_data()
        html = generator.generate_report(sample)

        assert len(html) > 100
        assert "BTC-USD" in html


class TestDiscoveryReportGenerator:
    """Tests for DiscoveryReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a DiscoveryReportGenerator instance."""
        return DiscoveryReportGenerator()

    def test_template_name(self, generator):
        """Test correct template name is returned."""
        assert generator.get_template_name() == "crew_reports/discovery_report.html"

    def test_required_fields(self, generator):
        """Test required fields for discovery reports."""
        required = generator.get_required_fields()
        assert "opportunities" in required

    def test_generate_report_with_sample_data(self, generator):
        """Test that report generation works with sample data."""
        sample = generator.get_sample_data()
        html = generator.generate_report(sample)

        assert len(html) > 100
        assert "NVDA" in html  # Sample opportunity


class TestRebalancingReportGenerator:
    """Tests for RebalancingReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create a RebalancingReportGenerator instance."""
        return RebalancingReportGenerator()

    def test_template_name(self, generator):
        """Test correct template name is returned."""
        assert generator.get_template_name() == "crew_reports/rebalancing_report.html"

    def test_required_fields(self, generator):
        """Test required fields for rebalancing reports."""
        required = generator.get_required_fields()
        assert "current_allocation" in required
        assert "target_allocation" in required
        assert "sharpe_ratio" in required

    def test_generate_report_with_sample_data(self, generator):
        """Test that report generation works with sample data."""
        sample = generator.get_sample_data()
        html = generator.generate_report(sample)

        assert len(html) > 100


class TestCommonFilters:
    """Tests for common Jinja2 filters."""

    @pytest.fixture
    def generator(self):
        """Use any generator to access filters."""
        return StockReportGenerator()

    def test_format_percentage_filter(self, generator):
        """Test format_percentage filter."""
        assert generator._format_percentage(0.85) == "85.0%"
        assert generator._format_percentage(0.123, decimals=2) == "12.30%"
        assert generator._format_percentage(None) == "N/A"

    def test_format_currency_filter(self, generator):
        """Test format_currency filter."""
        assert generator._format_currency(1234.56) == "$1,234.56"
        assert generator._format_currency(1000000) == "$1,000,000.00"
        assert generator._format_currency(None) == "N/A"

    def test_format_date_filter(self, generator):
        """Test format_date filter."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        assert generator._format_date(dt) == "2025-01-15"
        assert generator._format_date("2025-01-15T10:30:00") == "2025-01-15"
        assert generator._format_date(None) == "N/A"

    def test_format_number_filter(self, generator):
        """Test format_number filter."""
        assert generator._format_number(1234567.89) == "1,234,567.89"
        assert generator._format_number(None) == "N/A"

    def test_grade_color_filter(self, generator):
        """Test grade_color filter returns CSS classes."""
        assert "emerald" in generator._grade_color("A+")
        assert "green" in generator._grade_color("A")
        assert "yellow" in generator._grade_color("C")
        assert "red" in generator._grade_color("F")


class TestGenerateAndSaveReport:
    """Tests for generate_and_save_report method."""

    @pytest.fixture
    def generator(self):
        """Create a StockReportGenerator instance."""
        return StockReportGenerator()

    def test_generate_and_save_creates_file(self, generator, tmp_path):
        """Test that generate_and_save_report creates the HTML file."""
        sample = generator.get_sample_data()
        output_path = tmp_path / "reports" / "test_report.html"

        html_content = generator.generate_and_save_report(sample, output_path)

        assert output_path.exists()
        assert len(html_content) > 100
        assert "AAPL" in output_path.read_text()

    def test_generate_and_save_creates_parent_dirs(self, generator, tmp_path):
        """Test that parent directories are created if missing."""
        sample = generator.get_sample_data()
        output_path = tmp_path / "nested" / "dirs" / "report.html"

        generator.generate_and_save_report(sample, output_path)

        assert output_path.exists()


class TestErrorHandling:
    """Tests for error handling in report generators."""

    @pytest.fixture
    def generator(self):
        """Create a StockReportGenerator instance."""
        return StockReportGenerator()

    def test_missing_required_field_raises_runtime_error(self, generator):
        """Test that missing required fields raise RuntimeError (wrapped)."""
        data = {
            "ticker": "AAPL",
            # Missing other required fields
        }
        with pytest.raises(RuntimeError, match="Failed to generate report"):
            generator.generate_report(data)

    def test_none_value_for_required_field_raises_error(self, generator):
        """Test that None value for required field raises error."""
        data = {
            "ticker": None,  # None value
            "asset_class": "stock",
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Test.",
        }
        with pytest.raises(RuntimeError, match="Failed to generate report"):
            generator.generate_report(data)
