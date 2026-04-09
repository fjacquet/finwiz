"""
JSON Repair Utility for FinWiz.

Repairs common JSON syntax errors from LLM outputs using a pipeline pattern.
Each repair step is a separate function that can be tested independently.

Handles:
- Trailing commas in arrays and objects
- Missing quotes around keys
- Single quotes instead of double quotes
- Comments in JSON (// and /* */)
- Extra text before/after JSON
- Markdown code blocks
- Python-style output mixed with JSON
- Missing commas between elements
- Truncated JSON (unclosed strings, brackets, braces)
- Incomplete key-value pairs
"""

import json
import re
from collections.abc import Callable
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Pipeline Step Functions
# =============================================================================


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON object or array from text that may contain extra content.

    Finds the first '{' or '[' and matching closing bracket to extract JSON.
    """
    obj_start = text.find("{")
    arr_start = text.find("[")

    # Determine which comes first (object or array)
    if obj_start == -1 and arr_start == -1:
        return text
    elif obj_start == -1:
        start, open_char, close_char = arr_start, "[", "]"
    elif arr_start == -1:
        start, open_char, close_char = obj_start, "{", "}"
    elif obj_start < arr_start:
        start, open_char, close_char = obj_start, "{", "}"
    else:
        start, open_char, close_char = arr_start, "[", "]"

    # Find the matching closing bracket by counting depth
    depth = 0
    end = start
    for i, char in enumerate(text[start:], start):
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                end = i
                break

    if depth != 0:
        return text  # Unbalanced brackets

    return text[start : end + 1]


def _remove_trailing_commas(text: str) -> str:
    """Remove trailing commas before closing brackets/braces."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _remove_comments(text: str) -> str:
    """Remove JavaScript-style comments (// and /* */)."""
    # Remove single-line comments
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    # Remove multi-line comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _replace_single_quotes(text: str) -> str:
    """
    Replace single quotes used as string delimiters with double quotes.

    Only replaces single quotes that appear to be string delimiters,
    not single quotes inside strings (like apostrophes in "don't").
    """
    # Only replace single quotes that are string delimiters:
    # - At start/end of keys: 'key':
    # - At start/end of string values: : 'value'
    # Pattern: 'text' where text doesn't contain unescaped single quotes
    import re

    # Replace 'key': with "key":
    text = re.sub(r"'([\w_]+)'(\s*:)", r'"\1"\2', text)

    # Replace :'value' with :"value" (simple values without quotes inside)
    # This is conservative - only replaces if there are no quotes inside
    text = re.sub(r":\s*'([^']*)'(\s*[,}\]])", r': "\1"\2', text)

    return text


def _escape_newlines_in_strings(text: str) -> str:
    """
    Escape literal newlines inside JSON string values.

    JSON strings cannot contain literal newlines - they must be escaped as \\n.
    Only processes strings that actually contain newlines.
    """
    import re

    def escape_string_content(match: re.Match[str]) -> str:
        """Escape newlines within a single matched string."""
        full_match: str = match.group(0)
        # Only modify if there are actual newlines in the string
        if "\n" not in full_match and "\r" not in full_match:
            return full_match

        # Extract content between quotes and escape newlines
        content = match.group(1)
        content = content.replace("\n", "\\n")
        content = content.replace("\r", "\\r")
        return f'"{content}"'

    # Match complete JSON strings: "content"
    # This regex matches a quoted string that may span multiple lines
    # Pattern: " followed by (non-quote chars or escaped chars)* followed by "
    # Only process strings that contain newlines
    result = []
    pos = 0
    in_string = False
    string_start = 0

    for i, char in enumerate(text):
        if char == '"' and (i == 0 or text[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_start = i
            else:
                # End of string - check if it has newlines
                string_content = text[string_start + 1 : i]
                if "\n" in string_content or "\r" in string_content:
                    escaped = string_content.replace("\n", "\\n").replace("\r", "\\r")
                    result.append(text[pos:string_start])
                    result.append(f'"{escaped}"')
                    pos = i + 1
                in_string = False

    result.append(text[pos:])
    return "".join(result)


def _remove_markdown_blocks(text: str) -> str:
    """Remove markdown code block markers."""
    text = re.sub(r"^```json\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    return text


def _fix_unquoted_keys(text: str) -> str:
    """Add quotes around unquoted keys."""
    return re.sub(r"(\{|,)\s*(\w+)\s*:", r'\1"\2":', text)


def _fix_python_repr(text: str) -> str:
    """Fix Python-style representations mixed with JSON."""
    text = re.sub(r"=\w+\(", "={", text)
    text = re.sub(r"\)([,}\]])", r"}\1", text)
    return text


def _fix_unescaped_inner_quotes(text: str) -> str:
    """
    Fix unescaped double quotes inside JSON string values.

    LLMs sometimes produce strings like:
        "risque de "feature creep" et pression"
    which should be:
        "risque de \\"feature creep\\" et pression"

    Uses a state machine: when inside a string, a '"' is structural (closing)
    only if followed by a JSON structural token (:, ,, }, ]) or EOF.
    Otherwise it's an interior quote that needs escaping.
    """
    result: list[str] = []
    i = 0
    in_string = False

    while i < len(text):
        char = text[i]

        # Handle escape sequences inside strings
        if char == "\\" and in_string and i + 1 < len(text):
            result.append(text[i : i + 2])
            i += 2
            continue

        if char == '"':
            if not in_string:
                in_string = True
                result.append(char)
                i += 1
            else:
                # Determine if this quote is structural (closing) or interior
                rest = text[i + 1 :].lstrip()
                if not rest or rest[0] in ":,}]":
                    # Structural closing quote
                    in_string = False
                    result.append(char)
                    i += 1
                else:
                    # Interior quote — escape it
                    result.append('\\"')
                    i += 1
        else:
            result.append(char)
            i += 1

    return "".join(result)


def _add_missing_commas(text: str) -> str:
    """
    Add missing commas between JSON elements.

    Handles cases where LLM forgets comma between:
    - "value" "key":  (single or multi-line)
    - "value""key":   (no whitespace)
    - } "key":
    - ] "key":
    - number "key":
    - true/false/null "key":
    """
    # Strategy: Look for patterns where a value ends and a key begins without comma
    # Key pattern: "something": (quote, word chars, quote, colon)

    # Pattern 1a: After closing quote with whitespace: "value" "key":
    text = re.sub(r'(?<=[^,]")\s+("[\w_]+"\s*:)', r", \1", text)

    # Pattern 1b: After closing quote WITHOUT whitespace: "value""key":
    # This handles cases where LLM produces "Test""nextField": directly
    text = re.sub(r'(?<=[^,]")("[\w_]+"\s*:)', r", \1", text)

    # Pattern 2: After closing brace: } "key": or }"key":
    text = re.sub(r'(?<=[^,]})(\s*)("[\w_]+"\s*:)', r",\1\2", text)

    # Pattern 3: After closing bracket: ] "key": or ]"key":
    text = re.sub(r'(?<=[^,]])(\s*)("[\w_]+"\s*:)', r",\1\2", text)

    # Pattern 4: After number (digit at end): 123 "key": or 123"key":
    text = re.sub(r'(\d)(\s*)("[\w_]+"\s*:)', r"\1,\2\3", text)

    # Pattern 5: After boolean/null: true "key": or true"key":
    text = re.sub(r'(true|false|null)(\s*)("[\w_]+"\s*:)', r"\1,\2\3", text)

    return text


def _fix_double_commas(text: str) -> str:
    """Remove double commas that might be introduced by other repairs."""
    return re.sub(r",\s*,", ",", text)


def _close_truncated_json(text: str) -> str:
    """
    Close truncated JSON by adding missing closing brackets/braces.

    Handles cases where LLM output is cut off mid-way, leaving
    unclosed strings, arrays, or objects. This is a last-resort
    repair that attempts to make the JSON syntactically valid.
    """
    # First, handle unclosed strings (string cut off mid-way)
    # Count quotes (excluding escaped quotes)
    quote_count = 0
    i = 0
    while i < len(text):
        if text[i] == '"' and (i == 0 or text[i - 1] != "\\"):
            quote_count += 1
        i += 1

    # If odd number of quotes, we have an unclosed string
    if quote_count % 2 == 1:
        # Find the last opening quote and close the string
        # Also remove any incomplete content after last complete value
        text = text.rstrip()
        # Try to find a safe truncation point (end of a complete value)
        # Look for patterns like: ..." or ...] or ...} or a number/bool/null

        # First close the string
        text = text + '"'
        logger.debug("Closed unclosed string in truncated JSON")

    # Track bracket depth
    stack = []
    i = 0
    in_string = False

    while i < len(text):
        char = text[i]

        # Track string state (skip escaped quotes)
        if char == '"' and (i == 0 or text[i - 1] != "\\"):
            in_string = not in_string

        if not in_string:
            if char == "{":
                stack.append("}")
            elif char == "[":
                stack.append("]")
            elif char in "}]":
                if stack and stack[-1] == char:
                    stack.pop()

        i += 1

    # If we have unclosed brackets, we need to close them
    if stack:
        # Remove any trailing partial content that might cause issues
        text = text.rstrip()

        # Remove trailing comma if present (would be invalid before closing)
        text = re.sub(r",\s*$", "", text)

        # Close all unclosed brackets in reverse order
        closing = "".join(reversed(stack))
        text = text + closing
        logger.debug(f"Closed {len(stack)} unclosed brackets in truncated JSON: {closing}")

    return text


def _fix_truncated_values(text: str) -> str:
    """
    Fix truncated values at the end of JSON.

    Handles cases like:
    - "key": "value that was cut  -> "key": "value that was cut"
    - "key": [item1, item2,  -> "key": [item1, item2]
    - "key": {nested:  -> "key": {}
    """
    text = text.rstrip()

    # Pattern: ends with incomplete key-value (key with colon but no value)
    # e.g., ..."some_key": or ..."some_key":
    if re.search(r'"[\w_]+"\s*:\s*$', text):
        # Add a placeholder empty string
        text = text + '""'
        logger.debug("Added placeholder for truncated value")

    # Pattern: ends with comma (invalid JSON)
    text = re.sub(r",\s*$", "", text)

    return text


# =============================================================================
# Pipeline Configuration
# =============================================================================

# Basic repair steps (fast, safe)
BASIC_REPAIR_STEPS: list[Callable[[str], str]] = [
    _extract_json_from_text,
    _remove_markdown_blocks,  # Moved earlier - markdown blocks are common
    _remove_comments,
    _escape_newlines_in_strings,  # Must escape before other processing
    _replace_single_quotes,
    _fix_unescaped_inner_quotes,  # Escape interior quotes before comma fixes
    _add_missing_commas,  # Add missing commas BEFORE removing trailing
    _remove_trailing_commas,
    _fix_double_commas,  # Cleanup any double commas
]

# Aggressive repair steps (slower, may alter content)
AGGRESSIVE_REPAIR_STEPS: list[Callable[[str], str]] = [
    _fix_unquoted_keys,
    _fix_python_repr,
]

# Truncation repair steps (last resort - may lose data)
TRUNCATION_REPAIR_STEPS: list[Callable[[str], str]] = [
    _fix_truncated_values,
    _close_truncated_json,
    _remove_trailing_commas,  # Run again after closing
]


# =============================================================================
# Main Repair Functions
# =============================================================================


def repair_json(json_str: str) -> str:
    """
    Repair common JSON syntax errors from LLM outputs.

    Uses a pipeline pattern where each repair step is tried in sequence.
    Returns as soon as valid JSON is produced.

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

    # Try direct parse first
    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        pass

    # Apply basic repair steps
    for step in BASIC_REPAIR_STEPS:
        repaired = step(repaired)
        try:
            json.loads(repaired)
            if repaired != original:
                logger.info(f"JSON repaired by: {step.__name__}")
            return repaired
        except json.JSONDecodeError:
            continue

    # Apply aggressive repair steps
    for step in AGGRESSIVE_REPAIR_STEPS:
        repaired = step(repaired)
        try:
            json.loads(repaired)
            if repaired != original:
                logger.info(f"JSON repaired by: {step.__name__} (aggressive)")
            return repaired
        except json.JSONDecodeError:
            continue

    # Apply truncation repair steps (last resort - may lose data)
    logger.warning("Attempting truncation repair (JSON may be incomplete)")
    for step in TRUNCATION_REPAIR_STEPS:
        repaired = step(repaired)
        try:
            json.loads(repaired)
            if repaired != original:
                logger.warning(f"JSON repaired by: {step.__name__} (truncation repair - data may be incomplete)")
            return repaired
        except json.JSONDecodeError:
            continue

    # Final attempt: apply ALL repair steps in sequence (handles interaction effects)
    for step in BASIC_REPAIR_STEPS + AGGRESSIVE_REPAIR_STEPS + TRUNCATION_REPAIR_STEPS:
        repaired = step(repaired)

    try:
        json.loads(repaired)
        logger.info("JSON repaired after full pipeline re-run")
        return repaired
    except json.JSONDecodeError as e:
        # Log detailed error info for debugging
        logger.error(f"JSON repair failed: {e}")
        logger.error(f"Error position: line {e.lineno}, column {e.colno}")
        logger.debug(f"Original (first 500): {original[:500]}...")
        logger.debug(f"Repaired (first 500): {repaired[:500]}...")

        # Try to show context around the error
        if hasattr(e, "pos") and e.pos:
            start = max(0, e.pos - 50)
            end = min(len(repaired), e.pos + 50)
            logger.error(f"Context around error: ...{repaired[start:end]}...")

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
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("JSON parse failed, attempting repair...")
        repaired = repair_json(json_str)
        return json.loads(repaired)


def validate_and_repair_json(
    json_str: str,
    expected_keys: list[str] | None = None,
) -> dict[str, Any]:
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
    data = safe_json_loads(json_str)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object (dict), got {type(data)}")

    if expected_keys:
        missing = set(expected_keys) - set(data.keys())
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

    return data
