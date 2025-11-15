"""Tests for verify_html_reports script."""

import re
import pytest
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from verify_html_reports import (
    TICKER_PATTERN,
    TICKER_TITLE_PATTERN,
    NUMERIC_PATTERN,
    GRADE_PATTERN,
    SCORE_PATTERN,
    RECOMMENDATION_PATTERN,
    TABLE_ROW_PATTERN,
    verify_html_file,
)


class TestRegexPatterns:
    """Test suite for regex pattern constants."""

    def test_ticker_pattern_should_match_valid_tickers(self):
        """Test TICKER_PATTERN matches valid ticker symbols in table cells."""
        # Valid tickers
        assert re.search(TICKER_PATTERN, "<td>AAPL</td>")
        assert re.search(TICKER_PATTERN, "<td>GOOGL</td>")
        assert re.search(TICKER_PATTERN, "<td>BRK.B</td>")
        assert re.search(TICKER_PATTERN, '<td class="ticker">MSFT</td>')

        # Should not match invalid formats
        assert not re.search(TICKER_PATTERN, "<td>A</td>")  # Too short
        assert not re.search(TICKER_PATTERN, "<td>apple</td>")  # Lowercase
        assert not re.search(TICKER_PATTERN, "<td>123</td>")  # Numbers only

    def test_ticker_title_pattern_should_match_tickers_in_headings(self):
        """Test TICKER_TITLE_PATTERN matches ticker symbols in h1 tags."""
        assert re.search(TICKER_TITLE_PATTERN, "<h1>AAPL Analysis</h1>")
        assert re.search(TICKER_TITLE_PATTERN, "<h1>Stock Report: GOOGL</h1>")
        assert re.search(TICKER_TITLE_PATTERN, "<h1>BRK.B Portfolio</h1>")

        # Should not match without ticker
        assert not re.search(TICKER_TITLE_PATTERN, "<h1>Portfolio Analysis</h1>")

    def test_numeric_pattern_should_match_metric_values(self):
        """Test NUMERIC_PATTERN matches numeric values in metric divs."""
        assert re.search(NUMERIC_PATTERN, '<div class="metric-value">150</div>')
        assert re.search(NUMERIC_PATTERN, '<div class="metric-value">1234567</div>')

        # Should not match without metric-value class
        assert not re.search(NUMERIC_PATTERN, '<div class="other">150</div>')

    def test_grade_pattern_should_match_grade_indicators(self):
        """Test GRADE_PATTERN matches grade CSS classes and text."""
        # CSS classes
        assert re.search(GRADE_PATTERN, '<span class="grade-a">A+</span>')
        assert re.search(GRADE_PATTERN, '<div class="grade-b">B</div>')
        assert re.search(GRADE_PATTERN, '<td class="grade-f">F</td>')

        # Grade text
        assert re.search(GRADE_PATTERN, "Grade A")
        assert re.search(GRADE_PATTERN, "Grade F")

        # Should not match invalid grades
        assert not re.search(GRADE_PATTERN, "grade-1")
        assert not re.search(GRADE_PATTERN, "Grade X")

    def test_score_pattern_should_match_decimal_scores(self):
        """Test SCORE_PATTERN matches decimal scores with 2-3 places."""
        assert re.search(SCORE_PATTERN, "0.85")
        assert re.search(SCORE_PATTERN, "1.234")
        assert re.search(SCORE_PATTERN, "99.99")
        assert re.search(SCORE_PATTERN, "0.123")

        # Should not match single decimal
        assert not re.search(SCORE_PATTERN, "1.5")
        # Should not match integers
        assert not re.search(SCORE_PATTERN, "100")

    def test_recommendation_pattern_should_match_recommendations(self):
        """Test RECOMMENDATION_PATTERN matches investment recommendations."""
        assert re.search(RECOMMENDATION_PATTERN, "BUY")
        assert re.search(RECOMMENDATION_PATTERN, "SELL")
        assert re.search(RECOMMENDATION_PATTERN, "HOLD")
        assert re.search(RECOMMENDATION_PATTERN, "Recommendation: BUY")

        # Should not match partial matches
        assert not re.search(RECOMMENDATION_PATTERN, "BUYER")
        assert not re.search(RECOMMENDATION_PATTERN, "HOLDER")

    def test_table_row_pattern_should_match_data_rows(self):
        """Test TABLE_ROW_PATTERN matches table rows excluding headers."""
        # Should match data rows
        assert re.search(TABLE_ROW_PATTERN, "<tr><td>Data</td></tr>")
        assert re.search(TABLE_ROW_PATTERN, '<tr class="data-row"><td>Value</td></tr>')

        # Should not match header rows
        assert not re.search(TABLE_ROW_PATTERN, "<tr><th>Header</th></tr>")


class TestVerifyHtmlFile:
    """Test suite for verify_html_file function."""

    def test_should_detect_html_with_ticker_data(self, tmp_path):
        """Test detection of HTML files with ticker data."""
        # Create test HTML file
        html_file = tmp_path / "test.html"
        html_file.write_text("""
        <html>
            <body>
                <h1>AAPL Analysis</h1>
                <table>
                    <tr><td>AAPL</td><td>150.00</td></tr>
                </table>
            </body>
        </html>
        """)

        # Verify
        result = verify_html_file(html_file)

        assert result["has_data"] is True
        assert result["has_ticker_data"] is True
        assert result["status"] == "✅ PASS"

    def test_should_detect_html_with_grade_data(self, tmp_path):
        """Test detection of HTML files with grade data."""
        html_file = tmp_path / "test.html"
        html_file.write_text("""
        <html>
            <body>
                <div class="grade-a">Grade A</div>
                <div>Score: 0.85</div>
            </body>
        </html>
        """)

        result = verify_html_file(html_file)

        assert result["has_data"] is True
        assert result["has_grade_data"] is True
        assert result["has_score_data"] is True

    def test_should_detect_html_with_recommendation(self, tmp_path):
        """Test detection of HTML files with recommendations."""
        html_file = tmp_path / "test.html"
        html_file.write_text("""
        <html>
            <body>
                <div>Recommendation: BUY</div>
            </body>
        </html>
        """)

        result = verify_html_file(html_file)

        assert result["has_data"] is True
        assert result["has_recommendation"] is True

    def test_should_detect_empty_html(self, tmp_path):
        """Test detection of empty HTML files."""
        html_file = tmp_path / "test.html"
        html_file.write_text("""
        <html>
            <body>
                <h1>Empty Report</h1>
                <p>No data available</p>
            </body>
        </html>
        """)

        result = verify_html_file(html_file)

        assert result["has_data"] is False
        assert result["status"] == "❌ FAIL"

    def test_should_handle_file_read_errors(self, tmp_path):
        """Test handling of file read errors."""
        # Non-existent file
        html_file = tmp_path / "nonexistent.html"

        result = verify_html_file(html_file)

        assert result["has_data"] is False
        assert "ERROR" in result["status"]
