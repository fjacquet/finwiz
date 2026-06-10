"""
CSS styles for Python report generation.

This module contains all CSS styling for HTML reports, extracted
from the monolithic PythonReportGenerator for maintainability.
The stylesheet lives in assets/report_styles.css.
"""

from functools import cache
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"


@cache
def get_report_css() -> str:
    """Return the report stylesheet (read once from assets/report_styles.css).

    Returns:
        Complete CSS stylesheet as a string for financial reports
        with light mode, dark mode, responsive design, and
        grade/badge styling.
    """
    return (_ASSETS / "report_styles.css").read_text(encoding="utf-8")
