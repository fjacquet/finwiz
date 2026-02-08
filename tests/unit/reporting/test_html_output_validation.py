"""Tests for HTML output validation of enriched analysis reports.

Validates well-formedness, XSS prevention, character encoding, Jinja2 autoescape
configuration, and key content sections in generated HTML reports.
"""

from typing import Any

import pytest
from bs4 import BeautifulSoup

from finwiz.reporting.enriched_analysis_report_generator import (
    EnrichedAnalysisReportGenerator,
)


class TestHtmlOutputValidation:
    """Test HTML output validation for enriched analysis reports."""

    @pytest.fixture
    def generator(self):
        """Create EnrichedAnalysisReportGenerator instance."""
        return EnrichedAnalysisReportGenerator()

    @pytest.fixture
    def sample_data(self, generator) -> dict[str, Any]:
        """Create sample enriched analysis data."""
        return generator._create_sample_enriched_analysis()

    @pytest.fixture
    def sample_html(self, generator, sample_data) -> str:
        """Generate HTML from sample data."""
        return generator.generate_report(sample_data)

    def test_html_has_doctype_and_root_elements(self, sample_html):
        """HTML has DOCTYPE declaration and html/head/body elements."""
        assert sample_html.lower().startswith("<!doctype html>")

        soup = BeautifulSoup(sample_html, "html.parser")
        assert soup.find("html") is not None
        assert soup.find("head") is not None
        assert soup.find("body") is not None

    def test_html_has_utf8_charset(self, sample_html):
        """HTML declares UTF-8 charset via meta tag."""
        soup = BeautifulSoup(sample_html, "html.parser")

        # Check <meta charset="UTF-8">
        meta_charset = soup.find("meta", attrs={"charset": True})
        has_charset_tag = (
            meta_charset is not None
            and meta_charset["charset"].upper() == "UTF-8"
        )

        # Alternative: <meta http-equiv="Content-Type" content="...charset=UTF-8">
        meta_http = soup.find("meta", attrs={"http-equiv": "Content-Type"})
        has_http_equiv = (
            meta_http is not None
            and "UTF-8" in meta_http.get("content", "").upper()
        )

        assert has_charset_tag or has_http_equiv, (
            "No UTF-8 charset declaration found in meta tags"
        )

    def test_html_has_style_block(self, sample_html):
        """HTML contains inline CSS style block with expected classes."""
        soup = BeautifulSoup(sample_html, "html.parser")
        style = soup.find("style")
        assert style is not None, "No <style> block found"

        style_text = style.get_text()
        assert "primary-color" in style_text or "card-background" in style_text

    def test_html_xss_prevention_script_tag_escaped(self, generator, sample_data):
        """Injected <script> in ticker is escaped, not rendered as executable."""
        sample_data["ticker"] = '<script>alert("xss")</script>'
        html = generator.generate_report(sample_data)

        # Raw <script> should NOT appear
        assert '<script>alert' not in html

        # Escaped version should appear
        assert "&lt;script&gt;" in html or "&#60;script&#62;" in html

        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script")
        for s in scripts:
            assert "alert" not in (s.string or ""), (
                "Executable script tag with alert found in output"
            )

    def test_html_xss_prevention_event_handler_escaped(self, generator, sample_data):
        """Injected onmouseover event handler is escaped in output."""
        sample_data["company_name"] = 'Evil Corp" onmouseover="alert(1)'
        html = generator.generate_report(sample_data)

        soup = BeautifulSoup(html, "html.parser")
        assert not soup.find(attrs={"onmouseover": True}), (
            "onmouseover attribute found in generated HTML"
        )

    def test_html_contains_key_content_sections(self, sample_html):
        """HTML contains expected content: ticker, grade, recommendation, summary."""
        soup = BeautifulSoup(sample_html, "html.parser")
        text = soup.get_text()

        assert "TEST" in text
        assert "BUY" in text
        # Grade A appears in recommendation box as "Grade A"
        assert "Grade A" in text or "grade A" in text.lower()
        # Executive summary section header (French in this template)
        assert "Résumé Exécutif" in text or "Executive Summary" in text

    def test_jinja2_autoescape_enabled(self, generator):
        """Jinja2 environment has autoescape=True for XSS prevention."""
        assert generator.env.autoescape is True

    def test_html_is_parseable_without_errors(self, sample_html):
        """HTML is parseable by BeautifulSoup with substantial structure."""
        soup = BeautifulSoup(sample_html, "html.parser")
        assert soup is not None

        all_tags = soup.find_all()
        assert len(all_tags) > 10, (
            f"Only {len(all_tags)} tags found; expected substantial HTML"
        )

        # No CDATA or broken tag artifacts
        assert "<![CDATA[" not in sample_html

    def test_html_special_characters_in_rationale(self, generator, sample_data):
        """Special characters in investment_rationale are properly escaped."""
        # Build a rationale with special chars, repeated to meet 500-word threshold
        special_segment = (
            "Revenue grew 25% YoY. P/E ratio < 30. Risk: 'moderate'. "
            "Debt/Equity & leverage acceptable. Growth > expectations. "
        )
        # Repeat to reach 500+ words
        sample_data["investment_rationale"] = (special_segment * 50).strip()

        html = generator.generate_report(sample_data)

        # & should be escaped as &amp; in HTML output
        assert "&amp;" in html

        # < not part of an HTML tag should be escaped
        # Check that "< 30" appears escaped (not as a tag opener)
        assert "&lt;" in html

        # Parseable without errors
        soup = BeautifulSoup(html, "html.parser")
        assert soup is not None
