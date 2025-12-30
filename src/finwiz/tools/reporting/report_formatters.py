"""
HTML report formatting and generation.

This module provides HTML formatting, template rendering, and report generation
with UTF-8 encoding and emoji support using BeautifulSoup4.
"""

import logging
from datetime import datetime
from operator import attrgetter
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from finwiz.tools.reporting.report_sections import ReportSection

logger = logging.getLogger(__name__)


class HTMLReportFormatter:
    """Formats and generates HTML reports with UTF-8 encoding and emoji support."""

    # Required French sections
    FRENCH_SECTIONS = {"synthese_10k": "Synthèse 10-K", "sentiment_marche": "Sentiment du Marché"}

    def __init__(self, template_path: str | None = None) -> None:
        """
        Initialize the HTML report formatter.

        Args:
            template_path: Optional path to custom HTML template

        """
        self.template_path = template_path or "src/finwiz/templates/html_template.html"
        self.unified_template_path = "src/finwiz/templates/unified_portfolio_report.html"

    def generate_html(self, title: str, sections: list[ReportSection], language: str = "en") -> str:
        """
        Generate the complete HTML report using BeautifulSoup4.

        Args:
            title: Report title
            sections: List of report sections
            language: Report language (en/fr)

        Returns:
            Complete HTML report as string

        """
        # Load template
        template_content = self._load_template()

        # Generate report content
        report_content = self._generate_report_content(title, sections, language)

        # Use BeautifulSoup to properly insert content and update attributes
        soup = BeautifulSoup(template_content, "html.parser")

        # Update title
        title_tag = soup.find("title")
        if title_tag:
            title_tag.string = title

        # Update language attribute
        html_tag = soup.find("html")
        if html_tag:
            html_tag["lang"] = language

        # Find content insertion point and replace
        content_comment = soup.find(string=lambda text: text and "Content will be inserted here" in text)
        if content_comment:
            # Parse the report content and insert it
            content_soup = BeautifulSoup(report_content, "html.parser")
            # Replace the comment with the parsed content
            content_comment.replace_with(*content_soup.contents)
        else:
            # Fallback: find container div and insert content there
            container = soup.find("div", class_="container")
            if container:
                content_soup = BeautifulSoup(report_content, "html.parser")
                container.clear()
                container.extend(content_soup.contents)

        # Generate final HTML with proper formatting
        html_report = soup.prettify(formatter="html")

        logger.info(f"Generated HTML report with {len(sections)} sections")
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

    def _generate_report_content(self, title: str, sections: list[ReportSection], language: str) -> str:
        """Generate the main report content using BeautifulSoup4."""
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sort sections by order
        sorted_sections = sorted(sections, key=attrgetter("order"))

        # Create HTML using BeautifulSoup4
        soup = BeautifulSoup("", "html.parser")

        # Generate header
        h1 = soup.new_tag("h1")
        h1.string = f"📊 {title}"

        date_p = soup.new_tag("p")
        date_strong = soup.new_tag("strong")
        date_strong.string = "Date" if language == "en" else "Date"
        date_p.append(date_strong)
        date_p.append(f": {current_date}")

        lang_p = soup.new_tag("p")
        lang_strong = soup.new_tag("strong")
        lang_strong.string = "Language" if language == "en" else "Langue"
        lang_p.append(lang_strong)
        lang_p.append(f": {language.upper()}")

        # Create main container
        main_div = soup.new_tag("div")
        main_div.append(h1)
        main_div.append(date_p)
        main_div.append(lang_p)

        # Generate sections
        for section in sorted_sections:
            section_class = "section"

            # Add special styling for French sections
            if section.title in self.FRENCH_SECTIONS.values():
                section_class += " french-section"

            section_div = soup.new_tag("div", **{"class": section_class})

            # Create section header
            h2 = soup.new_tag("h2")
            if section.emoji:
                emoji_span = soup.new_tag("span", **{"class": "emoji"})
                emoji_span.string = section.emoji
                h2.append(emoji_span)
                h2.append(f" {section.title}")  # Add space and title as text
            else:
                h2.string = section.title

            # Create section content div
            content_div = soup.new_tag("div")
            # Parse the existing HTML content and append it
            content_soup = BeautifulSoup(section.content, "html.parser")
            for element in content_soup:
                content_div.append(element)

            section_div.append(h2)
            section_div.append(content_div)
            main_div.append(section_div)

        # Add disclaimer
        disclaimer_text = (
            "This report is generated by FinWiz AI and is for informational purposes only. Please consult with a qualified financial advisor before making investment decisions."
            if language == "en"
            else "Ce rapport est généré par FinWiz AI et est à des fins d'information uniquement. "
            "Veuillez consulter un conseiller financier qualifié avant de prendre des décisions d'investissement."
        )

        disclaimer_div = soup.new_tag("div", **{"class": "disclaimer"})
        disclaimer_p = soup.new_tag("p")
        disclaimer_strong = soup.new_tag("strong")
        disclaimer_strong.string = "Disclaimer" if language == "en" else "Avertissement"
        disclaimer_p.append(disclaimer_strong)
        disclaimer_p.append(f": {disclaimer_text}")
        disclaimer_div.append(disclaimer_p)
        main_div.append(disclaimer_div)

        return str(main_div)

    def validate_html_output(self, html_content: str) -> dict[str, Any]:
        """
        Validate HTML output for compliance with FinWiz standards.

        Args:
            html_content: HTML content to validate

        Returns:
            Validation result with compliance status and issues

        """
        issues = []

        # Check for UTF-8 encoding declaration (case insensitive)
        if 'charset="utf-8"' not in html_content.lower() and "charset=utf-8" not in html_content.lower():
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
            "has_utf8": 'charset="utf-8"' in html_content.lower(),
            "has_french_sections": french_section_found,
            "has_emojis": any(emoji in html_content for emoji in ["📈", "📉", "🔍", "🌐", "🚀", "⚠️", "💰", "⏱️", "📊", "🛡️", "👨‍💼", "💡", "📋", "📝", "💼", "🏪"]),
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

    def generate_unified_html(self, title: str, sections: list[ReportSection], language: str = "en") -> str:
        """
        Generate unified HTML report using the unified template.

        Args:
            title: Report title
            sections: List of report sections
            language: Report language

        Returns:
            Complete HTML report

        """
        try:
            from jinja2 import Template

            # Read unified template
            template_path = Path(self.unified_template_path)
            if not template_path.exists():
                logger.warning(f"Unified template not found at {template_path}, using fallback")
                return self.generate_html(title, sections, language)

            template_content = template_path.read_text(encoding="utf-8")
            template = Template(template_content)

            # Sort sections by order
            sorted_sections = sorted(sections, key=attrgetter("order"))

            # Render template
            html_content = template.render(
                title=title,
                language=language,
                timestamp=datetime.now(),
                sections=sorted_sections,
                french_sections=list(self.FRENCH_SECTIONS.values()),
            )

            logger.info(f"Generated unified HTML report with {len(sections)} sections")
            return html_content

        except Exception as e:
            logger.error(f"Error generating unified HTML report: {e}")
            # Fallback to standard HTML generation
            return self.generate_html_fallback(title, sections, language)

    def generate_html_fallback(self, title: str, sections: list[ReportSection], language: str = "en") -> str:
        """
        Generate HTML report using fallback template with BeautifulSoup4.

        Args:
            title: Report title
            sections: List of report sections
            language: Report language

        Returns:
            Complete HTML report

        """
        try:
            # Sort sections by order
            sorted_sections = sorted(sections, key=attrgetter("order"))

            # Create HTML document using BeautifulSoup4
            soup = BeautifulSoup("", "html.parser")

            # Create DOCTYPE and html structure
            html = soup.new_tag("html", lang=language)

            # Create head
            head = soup.new_tag("head")

            # Meta tags
            charset_meta = soup.new_tag("meta", charset="UTF-8")
            viewport_meta = soup.new_tag("meta", name="viewport", content="width=device-width, initial-scale=1.0")
            title_tag = soup.new_tag("title")
            title_tag.string = title

            # CSS styles
            style_tag = soup.new_tag("style")
            style_tag.string = """
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; }
                .section-title { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
                .keep { color: #27ae60; font-weight: bold; }
                .sell { color: #e74c3c; font-weight: bold; }
                .buy { background-color: #d5f4e6; }
                .metric-card { background: #f8f9fa; padding: 1rem; margin: 0.5rem; border-radius: 5px; }
                .recommendation-banner { padding: 1rem; border-radius: 5px; margin: 1rem 0; text-align: center; }
                .rebalance-now { background-color: #e74c3c; color: white; }
                .rebalance-soon { background-color: #f39c12; color: white; }
                .monitor { background-color: #3498db; color: white; }
                .no-action { background-color: #27ae60; color: white; }
            """

            head.append(charset_meta)
            head.append(viewport_meta)
            head.append(title_tag)
            head.append(style_tag)

            # Create body
            body = soup.new_tag("body")

            # Main title
            h1 = soup.new_tag("h1")
            h1.string = title
            body.append(h1)

            # Generated date
            date_p = soup.new_tag("p")
            date_p.string = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            body.append(date_p)

            # Add sections
            for section in sorted_sections:
                section_div = soup.new_tag("div", **{"class": "section"})

                # Section title
                section_h2 = soup.new_tag("h2", **{"class": "section-title"})
                section_title_text = f"{section.emoji + ' ' if section.emoji else ''}{section.title}"
                section_h2.string = section_title_text

                # Section content
                content_div = soup.new_tag("div", **{"class": "section-content"})
                # Parse existing HTML content and append
                content_soup = BeautifulSoup(section.content, "html.parser")
                for element in content_soup:
                    content_div.append(element)

                section_div.append(section_h2)
                section_div.append(content_div)
                body.append(section_div)

            # Footer
            footer = soup.new_tag("footer", style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #ddd; text-align: center; color: #666;")
            footer_p = soup.new_tag("p")
            footer_p.string = "Generated by FinWiz Portfolio Analysis System"
            footer.append(footer_p)
            body.append(footer)

            # Assemble document
            html.append(head)
            html.append(body)
            soup.append(html)

            # Generate final HTML with proper DOCTYPE
            html_content = "<!DOCTYPE html>\n" + soup.prettify(formatter="html")

            logger.info(f"Generated fallback HTML report with {len(sections)} sections")
            return html_content

        except Exception as e:
            logger.error(f"Error generating fallback HTML report: {e}")
            # Even error handling uses bs4
            error_soup = BeautifulSoup("", "html.parser")
            html = error_soup.new_tag("html")
            body = error_soup.new_tag("body")
            h1 = error_soup.new_tag("h1")
            h1.string = f"Error generating report: {e}"
            body.append(h1)
            html.append(body)
            error_soup.append(html)
            return "<!DOCTYPE html>\n" + error_soup.prettify(formatter="html")
