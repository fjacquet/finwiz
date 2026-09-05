"""Tests for provider-enforced JSON mode in get_configured_llm (force_json_object).

The deep-analysis qualitative crew emits the pipeline's largest strict-schema JSON;
provider JSON mode (response_format=json_object, injected via extra_body to bypass
CrewAI's response_format guard for OpenRouter) eliminates markdown-fenced / malformed
output at the source. Validated live against openrouter/mistralai/mistral-small-2603.
"""

from __future__ import annotations

import finwiz.config.llm.llm_config as llm_config


def _capture_llm_kwargs(mocker):
    """Patch the LLM ctor + API-key validation; return a Mock capturing LLM() kwargs."""
    mock_llm = mocker.patch.object(llm_config, "LLM")
    mocker.patch.object(llm_config, "_validate_api_key_for_model")
    return mock_llm


def test_force_json_object_injects_response_format(mocker):
    mock_llm = _capture_llm_kwargs(mocker)

    llm_config.get_configured_llm(model_override="openrouter/mistralai/mistral-small-2603", force_json_object=True)

    kwargs = mock_llm.call_args.kwargs
    assert kwargs["extra_body"]["response_format"] == {"type": "json_object"}


def test_default_does_not_force_json(mocker):
    mock_llm = _capture_llm_kwargs(mocker)

    llm_config.get_configured_llm(model_override="openrouter/mistralai/mistral-small-2603")

    extra_body = mock_llm.call_args.kwargs.get("extra_body") or {}
    assert "response_format" not in extra_body


def test_json_mode_is_cache_distinct(mocker):
    mock_llm = _capture_llm_kwargs(mocker)
    mock_llm.side_effect = lambda **kw: mocker.Mock(name="llm")  # distinct instance per build
    model = "openrouter/mistralai/mistral-small-2603"

    plain = llm_config.get_configured_llm(model_override=model)
    forced = llm_config.get_configured_llm(model_override=model, force_json_object=True)

    # Different cache entries -> two distinct LLM constructions, not a shared instance.
    assert plain is not forced
    assert mock_llm.call_count == 2
