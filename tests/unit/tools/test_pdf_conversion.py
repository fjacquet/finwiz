"""Tests for HtmlToPdfTool (WeasyPrint-based HTML to PDF conversion)."""

from pathlib import Path

import pytest

from finwiz.tools.file_conversion_tools import HtmlToPdfTool


def test_nonexistent_file_returns_error() -> None:
    tool = HtmlToPdfTool()
    out = tool._run(html_file_path="/non/existent/file.html")
    assert isinstance(out, str)
    assert out.startswith("Error: HTML file not found")


def test_rejects_non_html_extension(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("not html")
    tool = HtmlToPdfTool()
    out = tool._run(html_file_path=str(sample))
    assert out.startswith("Error: Input file")


def test_success_converts_and_writes_pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    html_file = tmp_path / "doc.html"
    html_file.write_text("<html><body>ok</body></html>")
    expected_pdf = tmp_path / "doc.pdf"

    # Dummy HTML class to avoid real WeasyPrint dependency during unit test
    class DummyHTML:
        def __init__(self, filename: str) -> None:
            self.filename = filename

        def write_pdf(self, output_path: str) -> None:
            Path(output_path).write_bytes(b"%PDF-1.4\n% dummy\n")

    # Patch the HTML symbol used inside the module under test
    import finwiz.tools.file_conversion_tools as mod

    monkeypatch.setattr(mod, "HTML", DummyHTML)

    tool = HtmlToPdfTool()
    out = tool._run(html_file_path=str(html_file))
    assert "Successfully converted" in out
    assert expected_pdf.exists()
