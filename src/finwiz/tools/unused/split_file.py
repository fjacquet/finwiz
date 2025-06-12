#!/usr/bin/env python3
"""Script to split incorrectly merged HTML/JSON files into separate files."""

import json
import os
import re
import sys


def split_file(input_file: str) -> tuple[str, str] | None:
    """
    Split a file containing both HTML and JSON into separate files.

    Args:
        input_file: Path to the file to be split

    Returns:
        Tuple containing paths to the HTML and JSON output files,
        or None if splitting failed

    """
    print(f"Processing file: {input_file}")

    # Read the input file
    with open(input_file) as f:
        content = f.read()

    # Extract HTML content
    html_match = re.search(r"```html\s*(.*?)```", content, re.DOTALL)
    if not html_match:
        print("No HTML content found")
        return None

    html_content = html_match.group(1)

    # Extract JSON content
    json_match = re.search(r"```json\s*(.*?)```", content, re.DOTALL)
    if not json_match:
        print("No JSON content found")
        return None

    json_content = json_match.group(1)

    # Validate JSON
    try:
        json_obj = json.loads(json_content)
        json_content = json.dumps(json_obj, indent=2)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON content: {e}")
        return None

    # Create output file paths
    base_name = os.path.splitext(input_file)[0]
    html_file = f"{base_name}.html"
    json_file = f"{base_name}.json"

    # Write the HTML file
    with open(html_file, "w") as f:
        f.write(html_content)
    print(f"HTML content written to: {html_file}")

    # Write the JSON file
    with open(json_file, "w") as f:
        f.write(json_content)
    print(f"JSON content written to: {json_file}")

    return html_file, json_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_file.py <path_to_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        sys.exit(1)

    result = split_file(input_file)
    if result:
        print("File splitting completed successfully!")
    else:
        print("File splitting failed!")
        sys.exit(1)
