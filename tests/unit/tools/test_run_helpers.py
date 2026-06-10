"""Tests for the shared _run JSON envelope helpers."""

import json

from finwiz.tools.run_helpers import json_error, json_ok


class TestJsonOk:
    def test_serializes_dict_with_default_str(self):
        from datetime import UTC, datetime

        payload = {"when": datetime(2026, 1, 1, tzinfo=UTC), "value": 1.5}
        out = json_ok(payload)
        parsed = json.loads(out)
        assert parsed["value"] == 1.5
        assert "2026-01-01" in parsed["when"]

    def test_output_is_indented(self):
        assert "\n" in json_ok({"a": 1})


class TestJsonError:
    def test_wraps_exception_with_type_and_context(self):
        out = json_error(ValueError("bad ticker"), ticker="AAPL")
        parsed = json.loads(out)
        assert parsed["success"] is False
        assert parsed["error"] == "bad ticker"
        assert parsed["error_type"] == "ValueError"
        assert parsed["ticker"] == "AAPL"

    def test_context_cannot_clobber_envelope_keys(self):
        out = json_error(ValueError("x"), error="hacked", success=True, error_type="Spoofed")
        parsed = json.loads(out)
        assert parsed["error"] == "x"
        assert parsed["success"] is False
        assert parsed["error_type"] == "ValueError"
