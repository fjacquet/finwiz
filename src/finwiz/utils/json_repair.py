"""
JSON Repair Utility for FinWiz.

Repairs common JSON syntax errors from LLM outputs, particularly:
- Trailing commas in arrays and objects
- Missing quotes around keys
- Single quotes instead of double quotes
- Comments in JSON
- Extra text before/after JSON
- Python-style output mixed with JSON

This is needed because LLMs sometimes generate
invalid JSON despite explicit instructions.
"""

import json
import re
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON object from text that may contain extra content.

    Finds the first '{' and matching last '}' to extract the JSON object.
    """
    # Find the first opening brace
    start = text.find('{')
    if start == -1:
        return text

    # Find the matching closing brace by counting braces
    depth = 0
    end = start
    for i, char in enumerate(text[start:], start):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                end = i
                break

    if depth != 0:
        # Unbalanced braces, return original
        return text

    return text[start:end + 1]


def repair_json(json_str: str) -> str:
    """
    Repair common JSON syntax errors from LLM outputs.

    Args:
        json_str: Potentially invalid JSON string

    Returns:
        Repaired JSON string that should be valid

    Raises:
        ValueError: If JSON cannot be repaired

    """
    if not json_str or not isinstance(json_str, str):
        raise ValueError("Input must be a non-empty string")

    original = json_str
    repaired = json_str

    try:
        # Step 0: Try direct parse first
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass

        # Step 1: Extract JSON from surrounding text
        repaired = _extract_json_from_text(repaired)

        # Step 2: Remove trailing commas before closing brackets/braces
        repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)

        # Step 3: Remove comments (// and /* */)
        repaired = re.sub(r'//.*?$', '', repaired, flags=re.MULTILINE)
        repaired = re.sub(r'/\*.*?\*/', '', repaired, flags=re.DOTALL)

        # Step 4: Replace single quotes with double quotes
        repaired = repaired.replace("'", '"')

        # Step 5: Try to parse
        try:
            json.loads(repaired)
            if repaired != original:
                logger.info("Successfully repaired JSON (extracted/cleaned)")
            return repaired
        except json.JSONDecodeError:
            pass

        # Step 6: More aggressive repairs
        # Remove markdown code blocks
        repaired = re.sub(r'^```json\s*', '', repaired)
        repaired = re.sub(r'^```\s*', '', repaired)
        repaired = re.sub(r'\s*```$', '', repaired)

        # Remove Python-style representations
        repaired = re.sub(r'=\w+\(', '={', repaired)
        repaired = re.sub(r'\)([,}\]])', r'}\1', repaired)

        # Fix unquoted keys
        repaired = re.sub(r'(\{|,)\s*(\w+)\s*:', r'\1"\2":', repaired)

        # Try to parse again
        json.loads(repaired)

        if repaired != original:
            logger.info("Successfully repaired JSON (aggressive cleanup)")

        return repaired

    except json.JSONDecodeError as e:
        logger.error(f"JSON repair failed: {e}")
        logger.debug(f"Original (first 500): {original[:500]}...")
        logger.debug(f"Repaired (first 500): {repaired[:500]}...")
        raise ValueError(f"Could not repair JSON: {e}") from e


def safe_json_loads(json_str: str) -> Any:
    """
    Safely load JSON with automatic repair attempts.

    Args:
        json_str: JSON string to parse

    Returns:
        Parsed JSON object

    Raises:
        ValueError: If JSON cannot be parsed even after repair

    """
    try:
        # Try direct parse first
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Try repair
        logger.warning("JSON parse failed, attempting repair...")
        repaired = repair_json(json_str)
        return json.loads(repaired)


def validate_and_repair_json(json_str: str, expected_keys: list[str] | None = None) -> dict[str, Any]:
    """
    Validate and repair JSON, optionally checking for expected keys.

    Args:
        json_str: JSON string to validate
        expected_keys: Optional list of keys that must be present

    Returns:
        Parsed and validated JSON object

    Raises:
        ValueError: If JSON is invalid or missing expected keys

    """
    # Parse with repair
    data = safe_json_loads(json_str)

    # Validate it's a dict
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(data)}")

    # Check expected keys
    if expected_keys:
        missing = set(expected_keys) - set(data.keys())
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

    return data
