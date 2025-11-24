"""
Unit tests for Final Report Generator.

Tests Python-based final report generation using Jinja2 templates (NO AI).
Following AI Minimalism principle: Python templates, not AI agents.
"""

from datetime import datetime
from pathlib import Path

import pytest
from pytest import approx

from finwiz.schemas.crew_exports import ConsolidatedReportExport
from finwiz.utils.final_report_generator import FinalReportGenerator


class TestFinalReportGenerator:
    """Test suite for FinalReportGenerator."""

    @pytest.fixture
    def generator(self):
        """Create FinalReportGenerator instance."""
        return FinalReportGenerator()

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "reports"
        output_dir.mkdir()
        return output_dir

    @pytest.fixture
    def mock_consolidated_data(self):
        """Create mock consolidated report data."""
        return ConsolidatedReportExport(
            session_id="test-session-123",
            consolidation_date=datetime.now(),
            stock_analyses=[],
            etf_analyses=[],
            crypto_analyses=[],
            deep_analyses=[],
            discovery_results=None,
            rebalancing_results=None,
            crew_execution_status={
                "stock_crew": "completed",
                "etf_crew": "completed",
                "crypto_crew": "completed",
            },
            total_execution_time=1.234,
            errors=[],
        )

    def test_should_generate_final_report_when_valid_data(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test generating final HTML report from consolidated data."""
        # Arrange
        output_path = temp_output_dir / "final_report.html"

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Final Report</body></html>"
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        result_path = generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)

        # Assert
        assert result_path == str(output_path)
        assert output_path.exists()
        mock_template.render.assert_called_once()

    def test_should_include_all_crew_results_in_template_data(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test that all crew results are passed to template."""
        # Arrange
        output_path = temp_output_dir / "final_report.html"

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)

        # Assert
        call_kwargs = mock_template.render.call_args[1]
        assert "session_id" in call_kwargs
        assert "stock_analyses" in call_kwargs
        assert "etf_analyses" in call_kwargs
        assert "crypto_analyses" in call_kwargs
        assert "deep_analyses" in call_kwargs
        assert "discovery_results" in call_kwargs
        assert "rebalancing_results" in call_kwargs
        assert "execution_status" in call_kwargs
        assert "generation_timestamp" in call_kwargs

    def test_should_create_parent_directories_when_missing(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test that parent directories are created if they don't exist."""
        # Arrange
        nested_path = temp_output_dir / "nested" / "dir" / "final_report.html"

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=nested_path)

        # Assert
        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_should_use_utf8_encoding_when_saving_file(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test that HTML files are saved with UTF-8 encoding."""
        # Arrange
        output_path = temp_output_dir / "final_report.html"
        html_with_french = "<html><body>📊 Rapport Final - Résumé Exécutif</body></html>"

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = html_with_french
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)

        # Assert
        content = output_path.read_text(encoding="utf-8")
        assert "📊" in content
        assert "Résumé Exécutif" in content

    def test_should_complete_in_milliseconds(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test that report generation completes quickly."""
        # Arrange
        output_path = temp_output_dir / "final_report.html"

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        import time

        start_time = time.time()
        generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)
        execution_time = time.time() - start_time

        # Assert
        assert execution_time < 1.0  # Should complete in less than 1 second

    def test_should_raise_error_when_template_not_found(self, generator, mock_consolidated_data, temp_output_dir, mocker):
        """Test error handling when template is not found."""
        # Arrange
        output_path = temp_output_dir / "final_report.html"

        # Mock template not found
        from jinja2 import TemplateNotFound

        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.side_effect = TemplateNotFound("final_report.html")

        # Act & Assert
        with pytest.raises(TemplateNotFound):
            generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)

    def test_should_raise_error_when_cannot_write_file(self, generator, mock_consolidated_data, mocker):
        """Test error handling when file cannot be written."""
        # Arrange
        output_path = Path("/invalid/path/final_report.html")

        # Mock template rendering
        mock_template = mocker.Mock()
        mock_template.render.return_value = "<html><body>Report</body></html>"
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act & Assert
        with pytest.raises(OSError):
            generator.generate_final_report(consolidated_data=mock_consolidated_data, output_path=output_path)


class TestFinalReportGeneratorTemplateData:
    """Test template data preparation."""

    @pytest.fixture
    def generator(self):
        """Create FinalReportGenerator instance."""
        return FinalReportGenerator()

    def test_should_prepare_complete_template_data(self, generator):
        """Test that all required data is prepared for template."""
        # Arrange
        consolidated_data = ConsolidatedReportExport(
            session_id="test-session",
            consolidation_date=datetime.now(),
            stock_analyses=[],
            etf_analyses=[],
            crypto_analyses=[],
            deep_analyses=[],
            discovery_results=None,
            rebalancing_results=None,
            crew_execution_status={"stock_crew": "completed"},
            total_execution_time=1.5,
            errors=[],
        )

        # Act
        template_data = generator._prepare_template_data(consolidated_data)

        # Assert
        assert template_data["session_id"] == "test-session"
        assert "consolidation_date" in template_data
        assert "total_time" in template_data
        assert template_data["total_time"] == approx(1.5)
        assert "stock_analyses" in template_data
        assert "etf_analyses" in template_data
        assert "crypto_analyses" in template_data
        assert "deep_analyses" in template_data
        assert "discovery_results" in template_data
        assert "rebalancing_results" in template_data
        assert "execution_status" in template_data
        assert "generation_timestamp" in template_data

    def test_should_include_execution_status(self, generator):
        """Test that execution status is included in template data."""
        # Arrange
        consolidated_data = ConsolidatedReportExport(
            session_id="test",
            crew_execution_status={
                "stock_crew": "completed",
                "etf_crew": "failed",
                "crypto_crew": "completed",
            },
            total_execution_time=1.0,
        )

        # Act
        template_data = generator._prepare_template_data(consolidated_data)

        # Assert
        assert template_data["execution_status"]["stock_crew"] == "completed"
        assert template_data["execution_status"]["etf_crew"] == "failed"
        assert template_data["execution_status"]["crypto_crew"] == "completed"


class TestFinalReportGeneratorValidation:
    """Test template validation methods."""

    @pytest.fixture
    def generator(self):
        """Create FinalReportGenerator instance."""
        return FinalReportGenerator()

    def test_should_validate_template_exists(self, generator, mocker):
        """Test template existence validation."""
        # Arrange
        mock_path = mocker.Mock()
        mock_path.exists.return_value = True
        mocker.patch.object(generator, "get_template_path", return_value=mock_path)

        # Act
        result = generator.validate_template_exists()

        # Assert
        assert result is True

    def test_should_return_false_when_template_missing(self, generator):
        """Test validation returns False when template is missing."""
        # Arrange
        # Override template_dir to point to non-existent location
        generator.template_dir = Path("/nonexistent/templates")

        # Act
        result = generator.validate_template_exists()

        # Assert
        assert result is False

    def test_should_return_correct_template_path(self, generator):
        """Test that correct template path is returned."""
        # Act
        template_path = generator.get_template_path()

        # Assert
        assert isinstance(template_path, Path)
        assert str(template_path).endswith("crew_reports/final_report.html")
        assert "templates" in str(template_path)


class TestFinalReportGeneratorFrenchLanguage:
    """Test French language rendering."""

    @pytest.fixture
    def generator(self):
        """Create FinalReportGenerator instance."""
        return FinalReportGenerator()

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "reports"
        output_dir.mkdir()
        return output_dir

    def test_should_render_french_sections(self, generator, temp_output_dir, mocker):
        """Test that French sections are rendered correctly."""
        # Arrange
        consolidated_data = ConsolidatedReportExport(
            session_id="test",
            total_execution_time=1.0,
        )
        output_path = temp_output_dir / "final_report.html"

        # Mock template with French content
        french_html = """
        <html>
        <body>
            <h1>📊 Rapport Final</h1>
            <h2>Résumé Exécutif</h2>
            <h2>Analyses d'Actions</h2>
            <h2>Analyses d'ETFs</h2>
            <h2>Analyses de Cryptomonnaies</h2>
        </body>
        </html>
        """
        mock_template = mocker.Mock()
        mock_template.render.return_value = french_html
        mock_env = mocker.patch.object(generator, "env")
        mock_env.get_template.return_value = mock_template

        # Act
        generator.generate_final_report(consolidated_data=consolidated_data, output_path=output_path)

        # Assert
        content = output_path.read_text(encoding="utf-8")
        assert "Résumé Exécutif" in content
        assert "Analyses d'Actions" in content
        assert "Analyses d'ETFs" in content
        assert "Analyses de Cryptomonnaies" in content
