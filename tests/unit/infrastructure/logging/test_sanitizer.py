"""Tests for the sensitive data log sanitizer."""

import logging

from finwiz.infrastructure.logging.sanitizer import SensitiveDataFilter


class TestSensitiveDataFilter:
    """Test handler-level log sanitization."""

    def test_redacts_known_env_var_value(self, monkeypatch):
        monkeypatch.setenv("PPLX_API_KEY", "pplx-secret-abc123")
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Calling API with key pplx-secret-abc123 now",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert "pplx-secret-abc123" not in record.msg
        assert "***REDACTED***" in record.msg

    def test_redacts_sk_pattern(self):
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Using key sk-abcdefghij1234567890abcdefghij1234567890abcd",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert "sk-abcdefghij" not in record.msg

    def test_redacts_bearer_token(self):
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert "eyJhbGciOiJIUzI1NiJ9" not in record.msg

    def test_passes_clean_message_through(self):
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Processing ticker AAPL for portfolio analysis",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert record.msg == "Processing ticker AAPL for portfolio analysis"

    def test_always_returns_true(self):
        """Filter should always return True (never drop records)."""
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="secret key sk-abc123abc123abc123abc123abc123abc123abc123ab",
            args=(),
            exc_info=None,
        )
        result = filt.filter(record)
        assert result is True

    def test_redacts_string_args(self, monkeypatch):
        monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "av-key-12345")
        filt = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Key is %s",
            args=("av-key-12345",),
            exc_info=None,
        )
        filt.filter(record)
        assert "av-key-12345" not in str(record.args)

    def test_refresh_patterns(self, monkeypatch):
        """Test that refresh_patterns picks up changed env var values."""
        monkeypatch.setenv("OPENAI_API_KEY", "old-key-12345678")
        filt = SensitiveDataFilter()
        # Change the key value after filter creation
        monkeypatch.setenv("OPENAI_API_KEY", "new-key-87654321")
        filt.refresh_patterns()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Value is new-key-87654321",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert "new-key-87654321" not in record.msg
