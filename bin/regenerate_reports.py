#!/usr/bin/env python
"""
Script to regenerate HTML reports with the improved HTMLOutputTool template.
This will fix emoji rendering and improve the visual appearance of reports.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the HTMLOutputTool
from src.finwiz.tools.html_output_tool import HTMLOutputTool


def regenerate_html_reports():
    """Regenerate all HTML reports in the report directory with the improved template."""
    report_dir = Path("report")
    html_tool = HTMLOutputTool()

    # Get all HTML files in the report directory
    html_files = list(report_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML reports to regenerate")

    for html_file in html_files:
        try:
            # Read the current HTML content
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract the title from the content
            title = extract_title(content)
            if not title:
                title = html_file.stem.replace("_", " ").title()

            # Extract the main content (everything between <body> and </body>)
            main_content = extract_content(content)
            if not main_content:
                print(f"Warning: Could not extract content from {html_file}")
                continue

            # Generate new HTML with the improved template
            output_path = str(html_file)
            result = html_tool._run(output_path, title, main_content)
            print(f"Regenerated {html_file}: {result}")

        except Exception as e:
            print(f"Error regenerating {html_file}: {e}")


def extract_title(html_content):
    """Extract the title from HTML content."""
    import re

    # Try to find the title in <title> tags
    title_match = re.search(
        r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
    )
    if title_match:
        return title_match.group(1).strip()

    # Try to find the title in <h1> tags
    h1_match = re.search(r"<h1>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL)
    if h1_match:
        return h1_match.group(1).strip()

    return None


def extract_content(html_content):
    """Extract the main content from HTML content."""
    import re

    # Try to find content between <body> and </body>
    body_match = re.search(
        r"<body>(.*?)</body>", html_content, re.IGNORECASE | re.DOTALL
    )
    if body_match:
        body_content = body_match.group(1).strip()

        # If there's a container div, extract just the content
        container_match = re.search(
            r'<div class="container">(.*?)<div class="footer">',
            body_content,
            re.IGNORECASE | re.DOTALL,
        )
        if container_match:
            return container_match.group(1).strip()

        return body_content

    # If no body tags, return the content as is (it might be just the main content)
    if "<html" not in html_content.lower():
        return html_content

    return None


if __name__ == "__main__":
    regenerate_html_reports()
