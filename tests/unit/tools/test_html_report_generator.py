"""
Unit tests for HTML Report Generator.

Tests HTML generation from crew export data using Jinja2 templates.
Following AI Minimalism principle: Python templates, not AI agents.
"""

from datetime import datetime

import pytest

from finwiz.tools.html_report_generator import HTMLReportGenerator


class TestHTMLReportGenerator:
    """Test suite for HTMLReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create HTMLReportGenerator instance."""
        return HTMLReportGenerator()

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "reports"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def mock_stock_export(self):
        """Create mock stock crew export data."""
        return {
            "crew_name": "stock_crew",
            "ticker": "AAPL",
            "asset_class": "stock",
            "session_id": "test-session-123",
            "analysis_date": datetime.now().isoformat(),
            "composite_score": 0.85,
            "grade": "A",
            "recommendation": "BUY",
            "confidence": 0.90,
            "rationale": "Strong fundamentals with excellent growth prospects and solid balance sheet.",
            "data_sources": ["Yahoo Finance", "SEC EDGAR"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

    @pytest.fixture
    def mock_etf_export(self):
        """Create mock ETF crew export data."""
        return {
            "crew_name": "etf_crew",
            "ticker": "SPY",
            "asset_class": "etf",
            "session_id": "test-session-123",
            "analysis_date": datetime.now().isoformat(),
            "composite_score": 0.78,
            "grade": "B",
            "recommendation": "HOLD",
            "confidence": 0.85,
            "rationale": "Solid tracking performance with low expense ratio and good diversification.",
            "expense_ratio": 0.09,
            "tracking_error": 0.05,
            "data_sources": ["Yahoo Finance", "ETF.com"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

    @pytest.fixture
    def mock_crypto_export(self):
        """Create mock crypto crew export data."""
        return {
            "crew_name": "crypto_crew",
            "ticker": "BTC",
            "asset_class": "crypto",
            "session_id": "test-session-123",
            "analysis_date": datetime.now().isoformat(),
            "composite_score": 0.72,
            "grade": "C+",
            "recommendation": "HOLD",
            "confidence": 0.75,
            "rationale": "High volatility but strong network effects and institutional adoption.",
            "volatility_30d": 0.65,
            "max_drawdown": -0.35,
            "data_sources": ["CoinMarketCap", "Kraken"],
            "report_html_path": "/path/to/report.html",
            "report_json_path": "/path/to/export.json",
        }

    def test_should_generate_stock_crew_report_when_valid_data(self, generator, mock_stock_export, temp_output_dir, mocker):
        """Test generating stock crew HTML report from export data."""
        # Arrange
        output_path = temp_output_dir / "stock_report.html"

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Stock Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        result_path = generator.generate_crew_report(
            crew_name="stock_crew",
            export_data=mock_stock_export,
            output_path=output_path,
        )

        # Assert
        assert result_path == str(output_path)
        assert output_path.exists()
        mock_template.render.assert_called_once()
        call_kwargs = mock_template.render.call_args[1]
        assert call_kwargs["data"] == mock_stock_export
        assert "generation_date" in call_kwargs

    def test_should_generate_etf_crew_report_when_valid_data(self, generator, mock_etf_export, temp_output_dir, mocker):
        """Test generating ETF crew HTML report from export data."""
        # Arrange
        output_path = temp_output_dir / "etf_report.html"

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>ETF Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        result_path = generator.generate_crew_report(
            crew_name="etf_crew",
            export_data=mock_etf_export,
            output_path=output_path,
        )

        # Assert
        assert result_path == str(output_path)
        assert output_path.exists()
        mock_template.render.assert_called_once()

    def test_should_generate_crypto_crew_report_when_valid_data(self, generator, mock_crypto_export, temp_output_dir, mocker):
        """Test generating crypto crew HTML report from export data."""
        # Arrange
        output_path = temp_output_dir / "crypto_report.html"

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Crypto Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        result_path = generator.generate_crew_report(
            crew_name="crypto_crew",
            export_data=mock_crypto_export,
            output_path=output_path,
        )

        # Assert
        assert result_path == str(output_path)
        assert output_path.exists()

    def test_should_raise_error_when_invalid_crew_name(self, generator, mock_stock_export, temp_output_dir):
        """Test error handling for invalid crew name."""
        # Arrange
        output_path = temp_output_dir / "report.html"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid crew_name"):
            generator.generate_crew_report(
                crew_name="invalid_crew",
                export_data=mock_stock_export,
                output_path=output_path,
            )

    def test_should_raise_error_when_export_data_not_dict(self, generator, temp_output_dir):
        """Test error handling for invalid export data type."""
        # Arrange
        output_path = temp_output_dir / "report.html"
        invalid_data = "not a dictionary"

        # Act & Assert
        with pytest.raises(ValueError, match="export_data must be a dictionary"):
            generator.generate_crew_report(
                crew_name="stock_crew",
                export_data=invalid_data,
                output_path=output_path,
            )

    def test_should_create_parent_directories_when_missing(self, generator, mock_stock_export, temp_output_dir, mocker):
        """Test that parent directories are created if they don't exist."""
        # Arrange
        nested_path = temp_output_dir / "nested" / "dir" / "report.html"

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        result_path = generator.generate_crew_report(
            crew_name="stock_crew",
            export_data=mock_stock_export,
            output_path=nested_path,
        )

        # Assert
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_should_use_utf8_encoding_when_saving_file(self, generator, mock_stock_export, temp_output_dir, mocker):
        """Test that HTML files are saved with UTF-8 encoding."""
        # Arrange
        output_path = temp_output_dir / "report.html"
        html_with_emoji = "<html><body>📊 Report with emoji</body></html>"

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = html_with_emoji
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        generator.generate_crew_report(
            crew_name="stock_crew",
            export_data=mock_stock_export,
            output_path=output_path,
        )

        # Assert
        content = output_path.read_text(encoding="utf-8")
        assert "📊" in content
        assert "Report with emoji" in content

    def test_should_log_warning_when_missing_required_fields(self, generator, temp_output_dir, mocker, caplog):
        """Test warning is logged when required fields are missing."""
        # Arrange
        output_path = temp_output_dir / "report.html"
        incomplete_data = {
            "crew_name": "stock_crew",
            # Missing: ticker, asset_class, analysis_date, session_id
        }

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act
        generator.generate_crew_report(
            crew_name="stock_crew",
            export_data=incomplete_data,
            output_path=output_path,
        )

        # Assert
        assert "Missing required fields" in caplog.text


class TestHTMLReportGeneratorTemplateMapping:
    """Test template mapping for different crew types."""

    @pytest.fixture
    def generator(self):
        """Create HTMLReportGenerator instance."""
        return HTMLReportGenerator()

    def test_should_map_all_crew_types_to_templates(self, generator, mocker, tmp_path):
        """Test that all crew types have template mappings."""
        # Arrange
        crew_types = [
            "stock_crew",
            "etf_crew",
            "crypto_crew",
            "deep_analysis_crew",
            "discovery_crew",
            "rebalancing_crew",
        ]

        # Mock template rendering - patch jinja2.Environment
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env_class = mocker.patch("jinja2.Environment")
        mock_env_instance = mocker.Mock()
        mock_env_class.return_value = mock_env_instance
        mock_env_instance.get_template.return_value = mock_template

        # Act & Assert
        for crew_type in crew_types:
            # Should not raise ValueError
            try:
                generator.generate_crew_report(
                    crew_name=crew_type,
                    export_data={
                        "ticker": "TEST",
                        "asset_class": "stock",
                        "session_id": "test",
                        "analysis_date": datetime.now().isoformat(),
                    },
                    output_path=tmp_path / f"{crew_type}.html",
                )
            except ValueError as e:
                if "Invalid crew_name" in str(e):
                    pytest.fail(f"Crew type {crew_type} not mapped to template")
