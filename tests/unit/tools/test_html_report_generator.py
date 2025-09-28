"""
Unit tests for HTML report generator.

Tests ensure HTML-first output standards with UTF-8 encoding,
emoji support, and French report section requirements.
"""

import pytest

from finwiz.tools.html_report_generator import HTMLReportGenerator, ReportSection


class TestReportSection:
    """Test ReportSection model."""

    def test_should_create_section_with_required_fields(self):
        """Test creating a report section with required fields."""
        # Arrange & Act
        section = ReportSection(title="Test Section", content="<p>Test content</p>")

        # Assert
        assert section.title == "Test Section"
        assert section.content == "<p>Test content</p>"
        assert section.emoji is None
        assert section.order == 0

    def test_should_create_section_with_all_fields(self):
        """Test creating a report section with all fields."""
        # Arrange & Act
        section = ReportSection(title="Analysis Section", content="<p>Analysis content</p>", emoji="📊", order=5)

        # Assert
        assert section.title == "Analysis Section"
        assert section.content == "<p>Analysis content</p>"
        assert section.emoji == "📊"
        assert section.order == 5


class TestHTMLReportGenerator:
    """Test HTML report generator functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = HTMLReportGenerator()

    def test_should_initialize_with_default_template_path(self):
        """Test generator initialization with default template path."""
        # Act
        generator = HTMLReportGenerator()

        # Assert
        assert generator.template_path == "src/finwiz/templates/html_template.html"
        assert generator.sections == []

    def test_should_initialize_with_custom_template_path(self):
        """Test generator initialization with custom template path."""
        # Arrange
        custom_path = "/custom/template.html"

        # Act
        generator = HTMLReportGenerator(template_path=custom_path)

        # Assert
        assert generator.template_path == custom_path

    def test_should_add_section_without_emoji(self):
        """Test adding a section without emoji."""
        # Act
        self.generator.add_section("Test Section", "<p>Content</p>")

        # Assert
        assert len(self.generator.sections) == 1
        section = self.generator.sections[0]
        assert section.title == "Test Section"
        assert section.content == "<p>Content</p>"
        assert section.emoji == ""
        assert section.order == 0

    def test_should_add_section_with_emoji(self):
        """Test adding a section with emoji."""
        # Act
        self.generator.add_section("Growth Analysis", "<p>Growth content</p>", "growth", 1)

        # Assert
        assert len(self.generator.sections) == 1
        section = self.generator.sections[0]
        assert section.title == "Growth Analysis"
        assert section.emoji == "📈"
        assert section.order == 1

    def test_should_add_french_section_synthese_10k(self):
        """Test adding French Synthèse 10-K section."""
        # Act
        self.generator.add_french_section("synthese_10k", "<p>Synthèse content</p>")

        # Assert
        assert len(self.generator.sections) == 1
        section = self.generator.sections[0]
        assert section.title == "Synthèse 10-K"
        assert section.content == "<p>Synthèse content</p>"
        assert section.order == 100

    def test_should_add_french_section_sentiment_marche(self):
        """Test adding French Sentiment du Marché section."""
        # Act
        self.generator.add_french_section("sentiment_marche", "<p>Sentiment content</p>")

        # Assert
        assert len(self.generator.sections) == 1
        section = self.generator.sections[0]
        assert section.title == "Sentiment du Marché"
        assert section.content == "<p>Sentiment content</p>"
        assert section.order == 100

    def test_should_raise_error_for_invalid_french_section(self):
        """Test error handling for invalid French section key."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.generator.add_french_section("invalid_key", "<p>Content</p>")

        assert "Invalid French section key: invalid_key" in str(exc_info.value)

    def test_should_generate_html_with_utf8_encoding(self):
        """Test HTML generation includes UTF-8 encoding."""
        # Arrange
        self.generator.add_section("Test", "<p>Test content</p>")

        # Act
        html = self.generator.generate_html()

        # Assert
        assert 'charset="UTF-8"' in html
        assert "<!DOCTYPE html>" in html
        assert "Test content" in html

    def test_should_generate_html_with_emojis(self):
        """Test HTML generation includes emojis."""
        # Arrange
        self.generator.add_section("Analysis", "<p>Content</p>", "analysis")

        # Act
        html = self.generator.generate_html()

        # Assert
        assert "🔍" in html  # Analysis emoji
        assert "📊" in html  # Report emoji in title

    def test_should_generate_html_with_french_sections(self):
        """Test HTML generation includes French sections."""
        # Arrange
        self.generator.add_french_section("synthese_10k", "<p>10-K analysis</p>")
        self.generator.add_french_section("sentiment_marche", "<p>Market sentiment</p>")

        # Act
        html = self.generator.generate_html()

        # Assert
        assert "Synthèse 10-K" in html
        assert "Sentiment du Marché" in html
        assert "french-section" in html

    def test_should_generate_html_with_custom_title_and_language(self):
        """Test HTML generation with custom title and language."""
        # Arrange
        self.generator.add_section("Test", "<p>Content</p>")

        # Act
        html = self.generator.generate_html(title="Custom Report", language="fr")

        # Assert
        assert "<title>Custom Report</title>" in html
        assert 'lang="fr"' in html
        assert "Custom Report" in html

    def test_should_sort_sections_by_order(self):
        """Test that sections are sorted by order in generated HTML."""
        # Arrange
        self.generator.add_section("Third", "<p>Third</p>", order=3)
        self.generator.add_section("First", "<p>First</p>", order=1)
        self.generator.add_section("Second", "<p>Second</p>", order=2)

        # Act
        html = self.generator.generate_html()

        # Assert
        first_pos = html.find("First")
        second_pos = html.find("Second")
        third_pos = html.find("Third")

        assert first_pos < second_pos < third_pos

    def test_should_load_custom_template(self, mocker):
        """Test loading custom template file."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_read_text = mocker.patch("pathlib.Path.read_text")
        mock_exists.return_value = True
        mock_read_text.return_value = "<html><body>Custom template</body></html>"

        # Act
        html = self.generator.generate_html()

        # Assert
        mock_read_text.assert_called_once_with(encoding="utf-8")
        assert "Custom template" in html

    def test_should_use_default_template_when_file_not_found(self, mocker):
        """Test fallback to default template when file not found."""
        # Arrange
        mock_exists = mocker.patch("pathlib.Path.exists")
        mock_exists.return_value = False

        # Act
        html = self.generator.generate_html()

        # Assert
        assert "<!DOCTYPE html>" in html
        assert 'charset="UTF-8"' in html

    def test_should_validate_compliant_html(self):
        """Test validation of compliant HTML output."""
        # Arrange
        self.generator.add_french_section("synthese_10k", "<p>Content</p>")
        html = self.generator.generate_html()

        # Act
        result = self.generator.validate_html_output(html)

        # Assert
        assert result["is_valid"] is True
        assert result["has_utf8"] is True
        assert result["has_french_sections"] is True
        assert result["has_emojis"] is True
        assert result["issues"] == []

    def test_should_detect_missing_utf8_encoding(self):
        """Test validation detects missing UTF-8 encoding."""
        # Arrange
        html = "<html><head><title>Test</title></head><body></body></html>"

        # Act
        result = self.generator.validate_html_output(html)

        # Assert
        assert result["is_valid"] is False
        assert "Missing UTF-8 encoding declaration" in result["issues"]
        assert result["has_utf8"] is False

    def test_should_detect_missing_doctype(self):
        """Test validation detects missing DOCTYPE."""
        # Arrange
        html = '<html><head><meta charset="UTF-8"></head><body></body></html>'

        # Act
        result = self.generator.validate_html_output(html)

        # Assert
        assert result["is_valid"] is False
        assert "Missing or incorrect DOCTYPE declaration" in result["issues"]

    def test_should_detect_missing_french_sections(self):
        """Test validation detects missing French sections."""
        # Arrange
        html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Test</title></head><body>📊</body></html>'

        # Act
        result = self.generator.validate_html_output(html)

        # Assert
        assert result["is_valid"] is False
        assert any("Missing required French sections" in issue for issue in result["issues"])
        assert result["has_french_sections"] is False

    def test_should_detect_missing_emojis(self):
        """Test validation detects missing emojis."""
        # Arrange
        html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Test</title></head><body>Synthèse 10-K</body></html>'

        # Act
        result = self.generator.validate_html_output(html)

        # Assert
        assert result["is_valid"] is False
        assert any("No emojis found" in issue for issue in result["issues"])
        assert result["has_emojis"] is False

    def test_should_save_report_with_utf8_encoding(self, mocker):
        """Test saving report with UTF-8 encoding."""
        # Arrange
        mock_mkdir = mocker.patch("pathlib.Path.mkdir")
        mock_write_text = mocker.patch("pathlib.Path.write_text")
        html_content = "<html>Test content</html>"
        file_path = "output/test_report.html"

        # Act
        self.generator.save_report(html_content, file_path)

        # Assert
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_write_text.assert_called_once_with(html_content, encoding="utf-8")

    def test_should_clear_all_sections(self):
        """Test clearing all sections from the generator."""
        # Arrange
        self.generator.add_section("Test 1", "<p>Content 1</p>")
        self.generator.add_section("Test 2", "<p>Content 2</p>")
        assert len(self.generator.sections) == 2

        # Act
        self.generator.clear_sections()

        # Assert
        assert len(self.generator.sections) == 0

    def test_should_include_disclaimer_in_english(self):
        """Test that English disclaimer is included."""
        # Act
        html = self.generator.generate_html(language="en")

        # Assert
        assert "Disclaimer" in html
        assert "informational purposes only" in html

    def test_should_include_disclaimer_in_french(self):
        """Test that French disclaimer is included."""
        # Act
        html = self.generator.generate_html(language="fr")

        # Assert
        assert "Avertissement" in html
        assert "à des fins d'information uniquement" in html
