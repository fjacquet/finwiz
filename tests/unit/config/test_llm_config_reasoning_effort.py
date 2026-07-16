"""Tests for explicit reasoning-effort pinning in get_configured_llm (LLM_REASONING_EFFORT).

finwiz never set a reasoning/thinking level, so hybrid-reasoning models (e.g.
glm-5.2, qwen3.7-plus) ran at whatever effort the provider defaulted to. That
inflates qualify-stage latency/output-token cost and eats into the generation
budget, contributing to truncated/malformed JSON. LLM_REASONING_EFFORT (default
"low") is now pinned explicitly via extra_body, but only on the one route
verified (against the installed crewai/litellm) to accept it: OpenRouter's
chat-completions passthrough. crewai routes openrouter/* models through its
native provider class (bypassing litellm entirely), so litellm's own
reasoning_effort/supports_reasoning gate never applies to this codebase.
"""

from __future__ import annotations

import finwiz.config.llm.llm_config as llm_config
from finwiz.config.llm.llm_config import _get_reasoning_params, _resolve_reasoning_effort


def _capture_llm_kwargs(mocker):
    """Patch the LLM ctor + API-key validation; return a Mock capturing LLM() kwargs."""
    mock_llm = mocker.patch.object(llm_config, "LLM")
    mocker.patch.object(llm_config, "_validate_api_key_for_model")
    llm_config._llm_cache.clear()
    return mock_llm


class TestResolveReasoningEffort:
    """Unit tests for _resolve_reasoning_effort()."""

    def test_should_default_to_low_when_unset(self, monkeypatch):
        monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)

        assert _resolve_reasoning_effort() == "low"

    def test_should_default_to_low_when_empty(self, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "   ")

        assert _resolve_reasoning_effort() == "low"

    def test_should_accept_medium(self, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "medium")

        assert _resolve_reasoning_effort() == "medium"

    def test_should_accept_high(self, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "HIGH")

        assert _resolve_reasoning_effort() == "high"

    def test_should_accept_none(self, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "none")

        assert _resolve_reasoning_effort() == "none"

    def test_should_fall_back_to_low_on_invalid_value(self, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "ultra-max")

        assert _resolve_reasoning_effort() == "low"


class TestGetReasoningParams:
    """Unit tests for _get_reasoning_params() per model family."""

    def test_should_send_reasoning_object_for_openrouter_low(self):
        assert _get_reasoning_params("openrouter/z-ai/glm-5.2", "low") == {"reasoning": {"effort": "low"}}

    def test_should_send_reasoning_object_for_openrouter_medium(self):
        assert _get_reasoning_params("openrouter/qwen/qwen3.7-plus", "medium") == {"reasoning": {"effort": "medium"}}

    def test_should_send_reasoning_object_for_openrouter_high(self):
        assert _get_reasoning_params("openrouter/anthropic/claude-opus-4.5", "high") == {"reasoning": {"effort": "high"}}

    def test_should_send_nothing_when_effort_is_none(self):
        assert _get_reasoning_params("openrouter/z-ai/glm-5.2", "none") == {}

    def test_should_send_nothing_for_unverified_native_openai_route(self):
        assert _get_reasoning_params("openai/gpt-4o-mini", "low") == {}

    def test_should_send_nothing_for_unverified_anthropic_route(self):
        assert _get_reasoning_params("anthropic/claude-opus-4.5", "high") == {}

    def test_should_send_nothing_for_bare_model_name(self):
        assert _get_reasoning_params("gpt-4o-mini", "low") == {}


class TestGetConfiguredLlmReasoningEffort:
    """Construction-level tests: LLM() kwargs reflect the resolved reasoning effort."""

    def test_should_pin_low_effort_by_default_for_openrouter_model(self, mocker, monkeypatch):
        monkeypatch.delenv("LLM_REASONING_EFFORT", raising=False)
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openrouter/z-ai/glm-5.2")

        kwargs = mock_llm.call_args.kwargs
        assert kwargs["extra_body"]["reasoning"] == {"effort": "low"}

    def test_should_pin_medium_effort_when_configured(self, mocker, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "medium")
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openrouter/qwen/qwen3.7-plus")

        kwargs = mock_llm.call_args.kwargs
        assert kwargs["extra_body"]["reasoning"] == {"effort": "medium"}

    def test_should_send_no_reasoning_params_when_effort_is_none(self, mocker, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "none")
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openrouter/z-ai/glm-5.2")

        extra_body = mock_llm.call_args.kwargs.get("extra_body") or {}
        assert "reasoning" not in extra_body

    def test_should_send_no_reasoning_params_for_unverified_native_provider(self, mocker, monkeypatch):
        """Non-openrouter routes are unverified, so "none" is the safe fallback regardless of effort."""
        monkeypatch.setenv("LLM_REASONING_EFFORT", "high")
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openai/gpt-4o-mini")

        extra_body = mock_llm.call_args.kwargs.get("extra_body")
        if extra_body is not None:
            assert "reasoning" not in extra_body

    def test_should_fall_back_to_low_for_invalid_env_value(self, mocker, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "not-a-real-level")
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openrouter/z-ai/glm-5.2")

        kwargs = mock_llm.call_args.kwargs
        assert kwargs["extra_body"]["reasoning"] == {"effort": "low"}

    def test_should_combine_with_force_json_object_in_same_extra_body(self, mocker, monkeypatch):
        monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
        mock_llm = _capture_llm_kwargs(mocker)

        llm_config.get_configured_llm(model_override="openrouter/z-ai/glm-5.2", force_json_object=True)

        extra_body = mock_llm.call_args.kwargs["extra_body"]
        assert extra_body["reasoning"] == {"effort": "low"}
        assert extra_body["response_format"] == {"type": "json_object"}

    def test_should_cache_distinct_instances_per_reasoning_effort(self, mocker, monkeypatch):
        mock_llm = _capture_llm_kwargs(mocker)
        mock_llm.side_effect = lambda **kw: mocker.Mock(name="llm")
        model = "openrouter/z-ai/glm-5.2"

        monkeypatch.setenv("LLM_REASONING_EFFORT", "low")
        low_instance = llm_config.get_configured_llm(model_override=model)

        monkeypatch.setenv("LLM_REASONING_EFFORT", "high")
        high_instance = llm_config.get_configured_llm(model_override=model)

        assert low_instance is not high_instance
        assert mock_llm.call_count == 2
