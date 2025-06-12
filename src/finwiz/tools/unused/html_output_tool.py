"""
Tool for saving HTML output with proper emoji handling.

This module provides a tool for generating HTML reports with proper emoji support
by using a template with UTF-8 encoding.
"""

import logging
import os
import re
from pathlib import Path
from typing import Tuple

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, validator


class HTMLOutputToolInput(BaseModel):
    """Input schema for HTMLOutputTool."""

    output_path: str = Field(
        ...,
        description="Path where the HTML file will be saved.",
    )
    title: str = Field(
        ...,
        description="Title for the HTML document.",
    )
    content: str = Field(
        ...,
        description="HTML content to be saved.",
    )

    @validator("output_path")
    def validate_output_path(cls, v: str) -> str:
        """Validate that the output path has a .html extension."""
        if not v.endswith(".html"):
            raise ValueError("Output path must have a .html extension")
        return v


# Set up logging
logger = logging.getLogger(__name__)


class HTMLOutputError(Exception):
    """Exception raised for errors in the HTML output."""


class HTMLOutputTool(BaseTool):
    """Tool for saving HTML output with proper emoji handling and content validation.

    This tool loads an HTML template, inserts the provided content and title,
    validates the content to ensure it doesn't contain raw JSON or API data,
    and saves the result with UTF-8 encoding to ensure proper emoji rendering.
    It creates any necessary directories in the output path if they don't exist.
    """

    name: str = "HTMLOutputTool"
    description: str = (
        "Use this tool to save HTML output with properly formatted emojis. "
        "The output will be saved to the specified path with UTF-8 encoding "
        "to ensure proper emoji rendering. Content is validated to prevent "
        "accidental inclusion of JSON or raw API data."
    )
    args_schema: type[BaseModel] = HTMLOutputToolInput

    def _validate_content(self, content: str) -> Tuple[bool, str]:
        """Validate that content is proper HTML and doesn't contain raw JSON or API data.

        Args:
            content: HTML content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if content looks like JSON
        json_indicators = [
            # Check for common JSON patterns
            lambda c: c.strip().startswith('{') and c.strip().endswith('}'),
            lambda c: c.strip().startswith('[') and c.strip().endswith(']'),
            # Look for JSON key-value patterns
            lambda c: bool(re.search(r'"\w+"\s*:\s*[{\[]', c)),
            # Check for API response patterns
            lambda c: '"searchParameters"' in c,
            lambda c: '"results"' in c and ('"items"' in c or '"data"' in c),
            # Check for raw API responses
            lambda c: bool(re.search(r'\{\s*"[^"]+"\s*:\s*\{', c))
        ]

        # Check if content has minimum HTML structure
        has_html_structure = (
            ('<html' in content.lower() or '<!doctype html' in content.lower()) and
            '</html>' in content.lower() and
            ('<body' in content.lower() or '<div' in content.lower())
        )

        # If content doesn't have HTML structure but has JSON indicators, it's likely invalid
        if not has_html_structure:
            for check in json_indicators:
                if check(content):
                    return False, "Content appears to be JSON or raw API data, not HTML"

        # If content contains both HTML and JSON blocks, try to detect mixed content
        json_blocks_in_html = re.search(r'\{\s*"[^"]+"\s*:\s*[{\[].*[\]\}]\s*\}', content)
        if json_blocks_in_html and len(json_blocks_in_html.group(0)) > 50:  # Arbitrary size threshold
            return False, "Content contains large JSON blocks that should be in separate JSON output"

        return True, ""

    def _run(self, output_path: str, title: str, content: str) -> str:
        """Save HTML content with proper emoji handling to the specified path.

        Includes validation to prevent JSON data in HTML output and uses a shared template
        for consistent styling across all reports.

        Args:
            output_path: Path where the HTML file will be saved
            title: Title for the HTML document
            content: HTML content to be saved

        Returns:
            A confirmation message indicating where the file was saved.

        Raises:
            HTMLOutputError: If content validation fails
        """
        # Validate content
        is_valid, error_message = self._validate_content(content)
        if not is_valid:
            logger.error("HTML content validation failed: %s", error_message)
            # Try to fix the content if possible
            if content.strip().startswith('{'):
                # This appears to be pure JSON
                content = (
                    "<h1>{}</h1><p>Error: Agent provided JSON instead of HTML. "
                    "Please see the JSON output file for data.</p>"
                ).format(title)
                logger.warning("Replaced invalid JSON content with error message HTML")
            elif not ('<html' in content.lower() or '<!doctype' in content.lower()):
                # Try to wrap non-HTML content in HTML tags
                content = f"<h1>{title}</h1>{content}"
                logger.warning("Wrapped non-HTML content in HTML tags")

        # Ensure directory exists
        output_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(output_dir, exist_ok=True)

        # Get the directory containing the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Build the path to the template file
        template_path = os.path.join(current_dir, '..', 'templates', 'html_template.html')

        try:
            # Load the template
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()

            logger.info("Successfully loaded HTML template from %s", template_path)

            # Insert title and content into the template
            template = template.replace(
                '<title>Financial Report</title>',
                f'<title>{title}</title>'
            )

            # Insert content into the container div
            template = template.replace(
                '<!-- Content will be inserted here -->',
                f'<h1>{title}</h1>\n{content}'
            )

            # Save the final HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(template)

            return f"Successfully saved HTML report to {output_path}"

        except FileNotFoundError:
            logger.error("Template file not found at %s", template_path)
            # Fallback to minimal HTML
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            margin: 20px;
            color: #333;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { 
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 0;
        }
        h2 {{
            color: #3498db;
            margin-top: 1.5em;
        }}
        p, li {{
            margin-bottom: 1em;
        }}
        a {{
            color: #2980b9;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {content}
    </div>
</body>
</html>""".format(title=title, content=content)  # noqa: F524

            # Save the fallback HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return f"Template not found. Saved basic HTML report to {output_path}"

        # Load the template file
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Replace title in both the <title> tag and the header
        template = template.replace(
            "<title>Financial Report</title>",
            f"<title>{title}</title>"
        )
        template = template.replace(
            "<h1>FinWiz Financial Analysis</h1>",
            f"<h1>{title}</h1>"
        )

        # Insert content
        template = template.replace(
            "<!-- Content will be inserted here -->",
            content
        )

        # Write the final HTML with proper UTF-8 encoding for emoji support
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)

        return f"HTML content with properly formatted emojis saved to {output_path}"

    async def _arun(self, output_path: str, title: str, content: str) -> str:
        """Async implementation of _run."""
        return self._run(output_path, title, content)
