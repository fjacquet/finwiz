"""Tests for fail-fast API key validation."""

import pytest

from finwiz.tools.api_key_validation import validate_api_key


class TestValidateApiKey:
    """Test the validate_api_key helper."""

    def test_returns_key_when_set(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "my-secret-key")
        result = validate_api_key("TEST_API_KEY", "TestTool")
        assert result == "my-secret-key"

    def test_raises_when_unset(self, monkeypatch):
        monkeypatch.delenv("TEST_API_KEY", raising=False)
        with pytest.raises(ValueError, match="TestTool requires TEST_API_KEY"):
            validate_api_key("TEST_API_KEY", "TestTool")

    def test_raises_when_empty(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "")
        with pytest.raises(ValueError, match="TEST_API_KEY"):
            validate_api_key("TEST_API_KEY", "TestTool")

    def test_error_message_includes_tool_name(self, monkeypatch):
        monkeypatch.delenv("MY_KEY", raising=False)
        with pytest.raises(ValueError, match="MyCustomTool"):
            validate_api_key("MY_KEY", "MyCustomTool")

    def test_error_message_includes_env_var(self, monkeypatch):
        monkeypatch.delenv("SPECIAL_KEY", raising=False)
        with pytest.raises(ValueError, match="SPECIAL_KEY"):
            validate_api_key("SPECIAL_KEY", "SomeTool")
