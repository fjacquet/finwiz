"""
Unit tests for the JSON repair pipeline.

Covers the duplicated-leading-brace repair strategy (production evidence from
glm-5.2: a lone "{" line followed by the real JSON object) as well as
regression coverage for the pre-existing repair steps (trailing commas,
truncation repair, and the "truly broken" failure path).
"""

from __future__ import annotations

import json

import pytest

from finwiz.infrastructure.json.repair import (
    _fix_duplicated_leading_brace,
    repair_json,
    safe_json_loads,
)


class TestFixDuplicatedLeadingBrace:
    """Unit tests for the `_fix_duplicated_leading_brace` step in isolation."""

    def test_should_strip_lone_leading_brace_when_duplicated(self):
        text = '{\n{"a": 1, "b": 2}'

        result = _fix_duplicated_leading_brace(text)

        assert result == '{"a": 1, "b": 2}'
        assert json.loads(result) == {"a": 1, "b": 2}

    def test_should_not_touch_pretty_printed_nested_close(self):
        """Regression: '}' newline '}' is the NORMAL closing sequence of a
        pretty-printed nested object — stripping it corrupts valid JSON."""
        text = '{"a": {"b": 1}\n}'

        result = _fix_duplicated_leading_brace(text)

        assert result == text
        assert json.loads(result) == {"a": {"b": 1}}

    def test_should_not_downgrade_repairable_document_with_nested_close(self):
        """Regression: a trailing-comma document ending in '}' newline '}' must be
        fixed by the cheap comma repair, not corrupted into the truncation path."""
        text = '{"a": {"b": 1,}\n}'

        repaired = repair_json(text)

        assert json.loads(repaired) == {"a": {"b": 1}}

    def test_should_leave_normal_object_untouched(self):
        text = '{"a": 1, "b": 2}'

        result = _fix_duplicated_leading_brace(text)

        assert result == text

    def test_should_leave_nested_object_untouched(self):
        """A single leading brace followed by a nested key's brace must not be stripped."""
        text = '{"outer": {"inner": 1}}'

        result = _fix_duplicated_leading_brace(text)

        assert result == text


class TestRepairJsonDuplicatedBrace:
    """Repair pipeline coverage for the duplicated-leading-brace pattern."""

    def test_should_repair_exact_observed_glm_pattern(self):
        """Verbatim-shaped payload from production glm-5.2 output."""
        payload = '{\n{"sec_insights":{"business_model":"L\'iShares MSCI World test fund","risk_factors":["market risk","currency risk"]},"summary":"Overall solid holding."}'

        repaired = repair_json(payload)
        parsed = json.loads(repaired)

        assert parsed["sec_insights"]["business_model"] == "L'iShares MSCI World test fund"
        assert parsed["sec_insights"]["risk_factors"] == ["market risk", "currency risk"]
        assert parsed["summary"] == "Overall solid holding."

    def test_should_repair_via_safe_json_loads_too(self):
        payload = '{\n{"ticker": "AAPL", "score": 0.85}'

        result = safe_json_loads(payload)

        assert result == {"ticker": "AAPL", "score": 0.85}

    def test_should_repair_duplicated_leading_brace_with_nested_objects(self):
        payload = '{\n{"a": {"b": {"c": 1}}, "d": [1, 2, 3]}'

        repaired = repair_json(payload)
        parsed = json.loads(repaired)

        assert parsed == {"a": {"b": {"c": 1}}, "d": [1, 2, 3]}


class TestRepairJsonPassthrough:
    """A normal, valid payload must pass through untouched."""

    def test_should_pass_through_valid_json_unchanged(self):
        payload = '{"ticker": "AAPL", "composite_score": 0.85, "nested": {"x": 1}}'

        result = repair_json(payload)

        assert result == payload
        assert json.loads(result) == {
            "ticker": "AAPL",
            "composite_score": 0.85,
            "nested": {"x": 1},
        }

    def test_should_pass_through_valid_array_unchanged(self):
        payload = '[{"a": 1}, {"b": 2}]'

        result = repair_json(payload)

        assert result == payload


class TestRepairJsonTrulyBroken:
    """Payloads that cannot be repaired must fail cleanly with ValueError."""

    def test_should_raise_value_error_for_unrepairable_garbage(self):
        payload = "not json at all { this is just : broken ; ; ;"

        with pytest.raises(ValueError, match="Could not repair JSON"):
            repair_json(payload)

    def test_should_raise_value_error_for_empty_object_soup(self):
        payload = "{{{{{{{"

        with pytest.raises(ValueError, match="Could not repair JSON"):
            repair_json(payload)

    def test_should_raise_value_error_for_non_string_input(self):
        with pytest.raises(ValueError, match="non-empty string"):
            repair_json("")


class TestRepairJsonTruncation:
    """Regression coverage for the pre-existing truncation-repair steps."""

    def test_should_close_truncated_object_missing_closing_brace(self):
        payload = '{"ticker": "AAPL", "score": 0.85'

        repaired = repair_json(payload)
        parsed = json.loads(repaired)

        assert parsed["ticker"] == "AAPL"
        assert parsed["score"] == 0.85

    def test_should_close_unclosed_string_value(self):
        payload = '{"ticker": "AAPL", "note": "cut off mid-sentence'

        repaired = repair_json(payload)
        parsed = json.loads(repaired)

        assert parsed["ticker"] == "AAPL"
        assert "note" in parsed

    def test_should_close_truncated_nested_array(self):
        payload = '{"ticker": "AAPL", "tags": ["growth", "tech"'

        repaired = repair_json(payload)
        parsed = json.loads(repaired)

        assert parsed["ticker"] == "AAPL"
        assert parsed["tags"][0] == "growth"

    def test_should_remove_trailing_comma_before_closing_brace(self):
        payload = '{"a": 1, "b": 2,}'

        repaired = repair_json(payload)

        assert json.loads(repaired) == {"a": 1, "b": 2}

    def test_should_remove_trailing_comma_before_closing_bracket(self):
        payload = '{"items": [1, 2, 3,]}'

        repaired = repair_json(payload)

        assert json.loads(repaired) == {"items": [1, 2, 3]}
