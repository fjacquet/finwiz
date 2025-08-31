"""
HTML Report Generator for FinWiz financial analysis reports.

This module provides HTML-first output standards with UTF-8 encoding,
emoji support, and French report section requirements.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ReportSection(BaseModel):
    """Represents a section in the HTML report."""

    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in HTML format")
    emoji: str | None = Field(None, description="Optional emoji for the section")
    order: int = Field(default=0, description="Display order of the section")


class HTMLReportGenerator:
    """
    Generates HTML reports with UTF-8 encoding and emoji support.

    Implements FinWiz HTML-first output standards including French report
    section requirements (Synthèse 10-K, Sentiment du Marché).
    """

    # Standard emoji mappings for financial content
    EMOJI_MAP = {
        "growth": "📈",
        "decline": "📉",
        "analysis": "🔍",
        "global": "🌐",
        "opportunity": "🚀",
        "risk": "⚠️",
        "financial": "💰",
        "time": "⏱️",
        "data": "📊",
        "defensive": "🛡️",
        "management": "👨‍💼",
        "innovation": "💡",
        "report": "📋",
        "summary": "📝",
        "portfolio": "💼",
        "market": "🏪",
    }

    # Required French sections
    FRENCH_SECTIONS = {"synthese_10k": "Synthèse 10-K", "sentiment_marche": "Sentiment du Marché"}

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize the HTML report generator.

        Args:
            template_path: Optional path to custom HTML template

        """
        self.template_path = template_path or "src/finwiz/templates/html_template.html"
        self.sections: list[ReportSection] = []

    def add_section(self, title: str, content: str, emoji_key: str | None = None, order: int = 0) -> None:
        """
        Add a section to the report.

        Args:
            title: Section title
            content: Section content in HTML format
            emoji_key: Key for emoji from EMOJI_MAP
            order: Display order (lower numbers appear first)

        """
        emoji = self.EMOJI_MAP.get(emoji_key, "") if emoji_key else ""
        section = ReportSection(title=title, content=content, emoji=emoji, order=order)
        self.sections.append(section)
        logger.debug(f"Added section: {title}")

    def add_french_section(self, section_key: str, content: str) -> None:
        """
        Add a required French section to the report.

        Args:
            section_key: Key from FRENCH_SECTIONS
            content: Section content in HTML format

        Raises:
            ValueError: If section_key is not a valid French section

        """
        if section_key not in self.FRENCH_SECTIONS:
            raise ValueError(f"Invalid French section key: {section_key}")

        title = self.FRENCH_SECTIONS[section_key]

        self.add_section(title, content, order=100)  # French sections appear later
        logger.info(f"Added French section: {title}")

    def generate_html(self, title: str = "FinWiz Financial Report", language: str = "en") -> str:
        """
        Generate the complete HTML report.

        Args:
            title: Report title
            language: Report language (en/fr)

        Returns:
            Complete HTML report as string

        """
        # Load template
        template_content = self._load_template()

        # Generate report content
        report_content = self._generate_report_content(title, language)

        # Insert content into template
        html_report = template_content.replace("<!-- Content will be inserted here -->", report_content)

        # Update title and language
        html_report = html_report.replace("<title>Financial Report</title>", f"<title>{title}</title>")
        html_report = html_report.replace('lang="en"', f'lang="{language}"')

        logger.info(f"Generated HTML report with {len(self.sections)} sections")
        return html_report

    def _load_template(self) -> str:
        """Load the HTML template."""
        try:
            template_path = Path(self.template_path)
            if not template_path.exists():
                logger.warning(f"Template not found at {self.template_path}, using default")
                return self._get_default_template()

            return template_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get the default HTML template with UTF-8 encoding and emoji support."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Report</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            margin: 20px; 
            background-color: #f9f9f9; 
        }
        .container { 
            max-width: 1000px; 
            margin: auto; 
            background: #fff; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.08); 
        }
        h1, h2, h3 { 
            color: #2c3e50; 
            border-bottom: 2px solid #e7e7e7; 
            padding-bottom: 10px; 
            margin-top: 30px; 
        }
        h1 { 
            text-align: center; 
            color: #1a2a3a; 
        }
        h2 { 
            color: #34495e; 
        }
        .section { 
            background-color: #fdfdfd; 
            border: 1px solid #eee; 
            border-radius: 6px; 
            padding: 20px; 
            margin-bottom: 25px; 
            box-shadow: 0 1px 5px rgba(0,0,0,0.05); 
        }
        .section h3 { 
            margin-top: 0; 
            color: #2980b9; 
            border-bottom: 1px dashed #e0e0e0; 
            padding-bottom: 8px; 
        }
        ul { 
            list-style: none; 
            padding: 0; 
        }
        ul li { 
            margin-bottom: 10px; 
            padding-left: 25px; 
            position: relative; 
        }
        ul li::before { 
            content: '•'; 
            color: #2980b9; 
            font-weight: bold; 
            display: inline-block; 
            width: 1em; 
            margin-left: -1em; 
        }
        .risk-category { 
            font-weight: bold; 
            color: #e74c3c; 
        }
        .strategy-category { 
            font-weight: bold; 
            color: #27ae60; 
        }
        .note { 
            font-style: italic; 
            color: #7f8c8d; 
            margin-top: 20px; 
            padding: 15px; 
            background-color: #ecf0f1; 
            border-left: 5px solid #bdc3c7; 
            border-radius: 4px; 
        }
        .disclaimer { 
            font-size: 0.9em; 
            color: #95a5a6; 
            margin-top: 40px; 
            border-top: 1px solid #eee; 
            padding-top: 20px; 
        }
        .emoji { 
            margin-right: 8px; 
            font-size: 1.2em; 
            vertical-align: middle; 
        }
        .french-section {
            border-left: 4px solid #3498db;
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Content will be inserted here -->
    </div>
</body>
</html>"""

    def _generate_report_content(self, title: str, language: str) -> str:
        """Generate the main report content."""
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sort sections by order
        sorted_sections = sorted(self.sections, key=lambda x: x.order)

        # Generate header
        content = f"""
        <h1>📊 {title}</h1>
        <p><strong>{"Date" if language == "en" else "Date"}:</strong> {current_date}</p>
        <p><strong>{"Language" if language == "en" else "Langue"}:</strong> {language.upper()}</p>
        """

        # Generate sections
        for section in sorted_sections:
            emoji_prefix = f'<span class="emoji">{section.emoji}</span>' if section.emoji else ""
            section_class = "section"

            # Add special styling for French sections
            if section.title in self.FRENCH_SECTIONS.values():
                section_class += " french-section"

            content += f"""
            <div class="{section_class}">
                <h2>{emoji_prefix}{section.title}</h2>
                <div>{section.content}</div>
            </div>
            """

        # Add disclaimer
        disclaimer_text = (
            "This report is generated by FinWiz AI and is for informational purposes only. "
            "Please consult with a qualified financial advisor before making investment decisions."
            if language == "en"
            else "Ce rapport est généré par FinWiz AI et est à des fins d'information uniquement. "
            "Veuillez consulter un conseiller financier qualifié avant de prendre des décisions d'investissement."
        )

        content += f"""
        <div class="disclaimer">
            <p><strong>{"Disclaimer" if language == "en" else "Avertissement"}:</strong> {disclaimer_text}</p>
        </div>
        """

        return content

    def validate_html_output(self, html_content: str) -> dict[str, Any]:
        """
        Validate HTML output for compliance with FinWiz standards.

        Args:
            html_content: HTML content to validate

        Returns:
            Validation result with compliance status and issues

        """
        issues = []

        # Check for UTF-8 encoding declaration
        if 'charset="UTF-8"' not in html_content and "charset=UTF-8" not in html_content:
            issues.append("Missing UTF-8 encoding declaration")

        # Check for proper DOCTYPE
        if not html_content.strip().startswith("<!DOCTYPE html>"):
            issues.append("Missing or incorrect DOCTYPE declaration")

        # Check for required French sections
        french_section_found = any(section_title in html_content for section_title in self.FRENCH_SECTIONS.values())

        if not french_section_found:
            issues.append("Missing required French sections (Synthèse 10-K, Sentiment du Marché)")

        # Check for emoji support (basic check)
        if "📊" not in html_content and "📈" not in html_content:
            issues.append("No emojis found - may indicate encoding issues")

        # Check for basic HTML structure
        required_tags = ["<html", "<head", "<body", "<title"]
        for tag in required_tags:
            if tag not in html_content:
                issues.append(f"Missing required HTML tag: {tag}")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "has_utf8": 'charset="UTF-8"' in html_content,
            "has_french_sections": french_section_found,
            "has_emojis": any(emoji in html_content for emoji in self.EMOJI_MAP.values()),
        }

    def save_report(self, html_content: str, file_path: str) -> None:
        """
        Save HTML report to file with proper UTF-8 encoding.

        Args:
            html_content: HTML content to save
            file_path: Path where to save the file

        """
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Ensure UTF-8 encoding when saving
            output_path.write_text(html_content, encoding="utf-8")

            logger.info(f"HTML report saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            raise

    def clear_sections(self) -> None:
        """Clear all sections from the report."""
        self.sections.clear()
        logger.debug("Cleared all report sections")
