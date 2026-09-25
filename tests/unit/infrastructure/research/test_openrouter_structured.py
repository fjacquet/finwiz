"""One web-grounded structured call to OpenRouter, no network.

``_build_client`` is the seam: tests hand back an ``httpx.AsyncClient`` on an
``httpx.MockTransport`` so the request body and the response handling are both
exercised for real.
"""

from __future__ import annotations

import json

import httpx
import pytest
from pydantic import BaseModel

from finwiz.infrastructure.research import openrouter_structured as module
from finwiz.infrastructure.research.openrouter_structured import (
    Citation,
    ResearchResult,
    SearchOptions,
    openrouter_structured,
)


class _Payload(BaseModel):
    value: str


def _annotation(url: str, title: str = "t", content: str = "c") -> dict:
    return {"type": "url_citation", "url_citation": {"url": url, "title": title, "content": content}}


def _ok_body(content: str, annotations: list[dict] | None = None, usage: dict | None = None) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content, "annotations": annotations or []}}],
        "usage": usage if usage is not None else {"prompt_tokens": 3282, "completion_tokens": 1985, "cost": 0.0169},
    }


def _install(mocker, handler) -> list[httpx.Request]:
    """Route the client through a MockTransport and collect the requests it sends."""
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    mocker.patch.object(module, "_build_client", side_effect=lambda timeout: httpx.AsyncClient(transport=httpx.MockTransport(recording), timeout=timeout))
    return seen


async def test_valid_response_yields_data_citations_and_cost(mocker):
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}', [_annotation("https://a"), _annotation("https://b"), _annotation("https://a")])))

    result = await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="test-openrouter-key")

    assert result == ResearchResult(
        data=_Payload(value="ok"),
        citations=(Citation(url="https://a", title="t", content="c"), Citation(url="https://b", title="t", content="c")),
        cost_usd=0.0169,
        prompt_tokens=3282,
        completion_tokens=1985,
    )
    body = json.loads(seen[0].content)
    assert body["model"] == "google/gemini-3.8-flash"
    assert body["plugins"] == [{"id": "web", "engine": "exa", "max_results": 8}]
    assert body["response_format"]["type"] == "json_schema"
    assert body["response_format"]["json_schema"]["name"] == "_Payload"
    assert body["response_format"]["json_schema"]["strict"] is True
    assert body["max_tokens"] == 4000
    assert [m["role"] for m in body["messages"]] == ["system", "user"]
    assert seen[0].headers["authorization"] == "Bearer test-openrouter-key"
    assert str(seen[0].url) == module.OPENROUTER_CHAT


async def test_recency_hint_is_appended_to_the_user_prompt(mocker):
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}')))

    await openrouter_structured(prompt="p", schema=_Payload, system="s", search=SearchOptions(recency_hint="month"), api_key="k")

    user = json.loads(seen[0].content)["messages"][1]["content"]
    assert user.startswith("p")
    assert "dernier mois" in user


async def test_search_none_omits_the_plugin(mocker):
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}')))

    await openrouter_structured(prompt="p", schema=_Payload, system="s", search=None, api_key="k")

    assert "plugins" not in json.loads(seen[0].content)


async def test_model_and_max_results_come_from_env(mocker, monkeypatch):
    monkeypatch.setenv("RESEARCH_MODEL", "google/gemini-3.8-pro")
    monkeypatch.setenv("RESEARCH_WEB_MAX_RESULTS", "5")
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}')))

    await openrouter_structured(prompt="p", schema=_Payload, system="s", search=SearchOptions(), api_key="k")

    body = json.loads(seen[0].content)
    assert body["model"] == "google/gemini-3.8-pro"
    assert body["plugins"][0]["max_results"] == 5


async def test_schema_invalid_content_returns_none(mocker):
    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"nope": 1}')))

    assert await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k") is None


async def test_fenced_valid_json_is_recovered(mocker):
    """A reply wrapped in a ```json fence still validates, mirroring the vendored
    Perplexity client's tolerant two-step parse."""
    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('Voici le résultat:\n```json\n{"value": "ok"}\n```\nMerci.')))

    result = await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k")

    assert result is not None
    assert result.data == _Payload(value="ok")


async def test_validation_error_logs_field_paths_not_values(mocker, caplog):
    """A schema constraint violation (not a parse failure) logs loc+type, never the value."""

    class _Scored(BaseModel):
        strategic_score: float

    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"strategic_score": "top-secret-value-should-not-leak"}')))

    with caplog.at_level("WARNING", logger="finwiz.infrastructure.research.openrouter_structured"):
        result = await openrouter_structured(prompt="p", schema=_Scored, system="s", api_key="k")

    assert result is None
    # Scoped to this module's own logger: a process-wide pydantic patch some
    # other test may have installed (crewai_json_patch) logs on its own
    # logger and is not this module's concern.
    our_text = "\n".join(r.getMessage() for r in caplog.records if r.name == "finwiz.infrastructure.research.openrouter_structured")
    assert "strategic_score" in our_text
    assert "top-secret-value-should-not-leak" not in our_text


async def test_non_200_returns_none(mocker):
    _install(mocker, lambda r: httpx.Response(429, json={"error": {"message": "rate limited"}}))

    assert await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k") is None


async def test_transport_error_returns_none(mocker):
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    _install(mocker, boom)

    assert await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k") is None


async def test_missing_usage_cost_is_none_not_zero(mocker):
    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}', usage={"prompt_tokens": 10, "completion_tokens": 5})))

    result = await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k")

    assert result is not None
    assert result.cost_usd is None
    assert (result.prompt_tokens, result.completion_tokens) == (10, 5)


async def test_cached_prompt_tokens_are_read_from_usage_details(mocker):
    usage = {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.001, "prompt_tokens_details": {"cached_tokens": 7}}
    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}', usage=usage)))

    result = await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k")

    assert result is not None
    assert result.cached_prompt_tokens == 7


async def test_no_usage_details_means_zero_cached_tokens(mocker):
    _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}', usage={"prompt_tokens": 10, "completion_tokens": 5})))

    result = await openrouter_structured(prompt="p", schema=_Payload, system="s", api_key="k")

    assert result is not None
    assert result.cached_prompt_tokens == 0


async def test_missing_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        await openrouter_structured(prompt="p", schema=_Payload, system="s")


async def test_env_key_is_used_when_no_explicit_key(mocker, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-test-key")
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}')))

    await openrouter_structured(prompt="p", schema=_Payload, system="s")

    assert seen[0].headers["authorization"] == "Bearer env-test-key"


def test_json_schema_for_is_cached_per_class():
    first = module._json_schema_for(_Payload)
    second = module._json_schema_for(_Payload)

    assert first is second


def test_web_max_results_falls_back_to_default_on_a_bad_env_value(monkeypatch):
    monkeypatch.setenv("RESEARCH_WEB_MAX_RESULTS", "eight")

    assert SearchOptions().max_results == 8
