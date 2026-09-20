# OpenRouter Research Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route the four Perplexity Sonar call sites (SWOT/Porter, portfolio posture, fact-pack gap-fill, sentiment news) through an OpenRouter web-grounded structured client on `google/gemini-3.8-flash`, with exact per-call cost recorded in the run summary and Perplexity kept as a one-shot fallback.

**Architecture:** A new `infrastructure/research/openrouter_structured.py` client makes one `httpx` POST with the `web` plugin (Exa) and a strict `json_schema` response format, returning data + citations + `usage.cost`. A new `infrastructure/resilience/research_retry.py` wraps it with the same retry/throttle shape as `perplexity_retry.py`, records cost into the existing `TokenMonitorCallback`, and falls back to one `perplexity_with_retry` attempt when a PPLX key is set. The three structured call sites swap the wrapper and unwrap `.data`; the sentiment wrapper asks for a small `NewsDigest` schema and feeds headlines + citations through its existing `_create_sonar_article` path.

**Tech Stack:** httpx ≥ 0.28 (already a dependency, `httpx.MockTransport` for tests), Pydantic v2 `model_json_schema()` / `model_validate_json()`, threading `BoundedSemaphore`, pytest-mock, `pytest-asyncio` in auto mode.

**Spec:** `docs/superpowers/specs/2026-09-20-openrouter-research-provider-design.md`

**One deliberate deviation from the spec:** `ResearchResult.citations` is `tuple[Citation, ...]` with `Citation(url, title, content)` rather than `tuple[str, ...]`. The sentiment task (spec §4) needs title and snippet from the annotations to build a `SonarArticle`; a URL-only tuple would force a second parse of the raw response. Deduplication by URL, order preserved, is unchanged.

## Global Constraints

- Model id `google/gemini-3.8-flash` (raw OpenRouter API, no `openrouter/` prefix). Env `RESEARCH_MODEL` overrides it. Endpoint `https://openrouter.ai/api/v1/chat/completions`, `RESEARCH_BASE_URL` overrides the base.
- Web plugin body: `"plugins": [{"id": "web", "engine": "exa", "max_results": N}]`, N from `RESEARCH_WEB_MAX_RESULTS` (default `8`). Response format: `{"type": "json_schema", "json_schema": {"name": <schema class name>, "strict": true, "schema": <model_json_schema()>}}`. `max_tokens` 4000.
- `RESEARCH_CONCURRENCY` default `6`, floored at 1, process-wide `threading.BoundedSemaphore` (same reasoning as `perplexity_retry.get_perplexity_semaphore`).
- The client returns `None` on any HTTP / transport / JSON / Pydantic failure and raises `ValueError` only when no API key is available. It never logs the prompt body or the key.
- Cost attribution key is `research_{kind}` with `kind` in `swot`, `porter`, `posture`, `factpack`, `news`.
- Provenance literal `"perplexity.gap_fill"` becomes `"research.gap_fill"` everywhere it is written or read.
- `unittest.mock` is banned; `pytest-mock` (`mocker`) only. No network in unit tests: patch `_build_client` on the client module or `research_with_retry` at the call site.
- Never print or assert on a real key. Tests use placeholder strings like `"test-openrouter-key"`.
- `json.dumps` always with `default=str`.
- Pydantic models live under `schemas/`; `NewsDigest` goes in `schemas/perplexity.py`.
- Docs ship in the same branch (ADR-012, ADR-002 status line, CHANGELOG, root `CLAUDE.md`, `.env.example`, `docs/how-to/setup_environment.md`, `docs/development/dependencies.md`, `src/finwiz/analysis/CLAUDE.md`).
- Branch: `feat/openrouter-research-provider` off `main` **after** the cache-prompt PR is merged. Merge with `gh pr merge --merge`.
- Commits end with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB`.
- Shell commands are prefixed with `rtk`.
- Before pushing: `rtk make check`, `rtk uv run mypy src/finwiz`, `uvx vulture src/finwiz --min-confidence 80` (renaming a module can unmask a vulture warning in an untouched file).

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `src/finwiz/infrastructure/monitoring/litellm_callback.py:97-155` | Modify | `record_usage` accepts an exact `cost_usd` |
| `src/finwiz/config/endpoints.py` | Modify | `OPENROUTER_CHAT` endpoint constant |
| `src/finwiz/infrastructure/research/__init__.py` | Create | Package marker |
| `src/finwiz/infrastructure/research/openrouter_structured.py` | Create | One structured, web-grounded OpenRouter call |
| `src/finwiz/infrastructure/resilience/research_retry.py` | Create | Retry, throttle, cost recording, Perplexity fallback |
| `src/finwiz/infrastructure/resilience/perplexity_retry.py:1-19` | Modify | Docstring: now the fallback provider |
| `src/finwiz/analysis/strategic_research.py` | Modify | SWOT / Porter / posture call the new wrapper |
| `src/finwiz/analysis/fact_pack/sources/research_source.py` | Rename from `perplexity_source.py` | Gap-fill via the new wrapper |
| `src/finwiz/analysis/fact_pack/composer.py:11,92,99` | Modify | Import rename, provenance literal |
| `src/finwiz/analysis/fact_pack_research.py:7,13,138-143,150` | Modify | Docstrings and system prompt wording |
| `src/finwiz/reporting/sections/factpack.py:98` | Modify | Provenance label |
| `src/finwiz/schemas/perplexity.py` | Modify | `NewsHeadline`, `NewsDigest` |
| `src/finwiz/tools/perplexity_analysis_integration.py` | Modify | Availability + `search_financial_news` via research |
| `src/finwiz/config/features/definitions.py:141-149` | Modify | Flag description |
| `tests/conftest.py:96-100` | Modify | Clear `OPENROUTER_API_KEY` per test |
| `tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py` | Modify | `cost_usd` tests |
| `tests/unit/infrastructure/research/test_openrouter_structured.py` | Create | Client tests |
| `tests/unit/infrastructure/resilience/test_research_retry.py` | Create | Wrapper tests |
| `tests/unit/analysis/test_strategic_research_retry.py` | Modify | Seam renamed |
| `tests/unit/analysis/fact_pack/test_gap_fill.py` | Modify | Module renamed |
| `tests/unit/tools/test_perplexity_integration_wrapper.py` | Modify | Four HTTP-seam tests re-pointed |
| `tests/integration/test_openrouter_research_live.py` | Create | One live SWOT call, skipped without key |
| `docs/adr/ADR-012-openrouter-research-provider.md` | Create | Decision record |
| `docs/adr/ADR-002-perplexity-research-integration.md:3` | Modify | Superseded note |
| `.env.example`, `CHANGELOG.md`, `CLAUDE.md`, `docs/how-to/setup_environment.md`, `docs/development/dependencies.md`, `src/finwiz/analysis/CLAUDE.md` | Modify | Config and docs |

---

### Task 1: Cost tracker accepts an exact provider cost

**Files:**
- Modify: `src/finwiz/infrastructure/monitoring/litellm_callback.py:97-155`
- Test: `tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py`

**Interfaces:**
- Produces: `TokenMonitorCallback.record_usage(crew_name: str, token_usage: Any, model: str | None = None, *, cost_usd: float | None = None) -> None`. When `cost_usd` is given it is used verbatim and the crew is marked priced; when it is `None` the existing litellm lookup runs (and with `model=None` the crew is marked `cost_known=False`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py` (the module already defines `_usage(prompt, completion, requests)`):

```python
class TestExactProviderCost:
    """OpenRouter returns ``usage.cost``; record it instead of estimating."""

    def test_exact_cost_is_accumulated_and_marks_the_crew_priced(self):
        cb = TokenMonitorCallback()

        cb.record_usage("research_swot", _usage(3282, 1985), cost_usd=0.0169)
        cb.record_usage("research_swot", _usage(3000, 1500), cost_usd=0.0150)

        summary = cb.get_cost_summary()
        assert summary["per_crew"]["research_swot"]["cost"] == pytest.approx(0.0319)
        assert summary["per_crew"]["research_swot"]["calls"] == 2
        assert summary["per_crew"]["research_swot"]["cost_known"] is True
        assert summary["total_cost"] == pytest.approx(0.0319)

    def test_exact_cost_wins_over_the_model_estimate(self, mocker):
        priced = mocker.patch("litellm.cost_per_token", return_value=(1.0, 1.0))
        cb = TokenMonitorCallback()

        cb.record_usage("research_swot", _usage(), model="openrouter/google/gemini-3.8-flash", cost_usd=0.01)

        priced.assert_not_called()
        assert cb.get_cost_summary()["per_crew"]["research_swot"]["cost"] == pytest.approx(0.01)

    def test_none_cost_with_no_model_counts_tokens_but_stays_unknown(self):
        """The Perplexity fallback path: tokens unknown, cost unknown, call counted."""
        cb = TokenMonitorCallback()

        cb.record_usage("research_swot", _usage(0, 0, requests=1), cost_usd=None)

        crew = cb.get_cost_summary()["per_crew"]["research_swot"]
        assert crew["calls"] == 1
        assert crew["cost_known"] is False
        assert crew["cost"] == 0.0
```

- [ ] **Step 2: Run to verify they fail**

Run: `rtk uv run pytest tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py::TestExactProviderCost -v`
Expected: 3 FAIL with `TypeError: ... got an unexpected keyword argument 'cost_usd'`.

- [ ] **Step 3: Implement**

In `record_usage`, change the signature and the cost block:

```python
    def record_usage(self, crew_name: str, token_usage: Any, model: str | None = None, *, cost_usd: float | None = None) -> None:
        """Record authoritative usage metrics for one crew kickoff or research call.

        This is the source of truth for the cost summary. CrewAI populates
        ``CrewOutput.token_usage`` directly, which survives thread boundaries and
        CrewAI's own clobbering of ``litellm.callbacks`` (the reason
        ``log_success_event`` never fires for crews). Cost is an ESTIMATE derived
        from token counts and the crew's model via litellm pricing, unless the
        caller passes ``cost_usd`` -- the exact figure OpenRouter returns in
        ``usage.cost`` for direct research calls -- in which case that figure is
        recorded as is. When neither is available we count tokens but mark cost
        unknown rather than recording a misleading $0.

        Args:
            crew_name: Crew attribution key (e.g. ``deep_analysis_stock``,
                ``research_swot``).
            token_usage: CrewAI ``UsageMetrics``-shaped object (``prompt_tokens``,
                ``completion_tokens``, ``successful_requests``).
            model: litellm model id for price lookup (e.g. ``openai/gpt-4o-mini``).
                Ignored when ``cost_usd`` is given.
            cost_usd: Exact cost reported by the provider, when known.
        """
        prompt_tokens = int(getattr(token_usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(token_usage, "completion_tokens", 0) or 0)
        requests = int(getattr(token_usage, "successful_requests", 0) or 0)
        if prompt_tokens == 0 and completion_tokens == 0 and requests == 0:
            return  # nothing measurable (empty/cached-only result) — don't fabricate a call

        calls = requests if requests > 0 else 1

        cost: float | None = None
        if cost_usd is not None:
            cost = float(cost_usd)
        elif model:
            for candidate in _price_candidates(model):
```

The rest of the method (the `for candidate` loop body and everything after it) is unchanged.

- [ ] **Step 4: Run the whole cost test module**

Run: `rtk uv run pytest tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
rtk git checkout -b feat/openrouter-research-provider main
rtk git add src/finwiz/infrastructure/monitoring/litellm_callback.py tests/unit/infrastructure/monitoring/test_litellm_callback_cost.py
rtk git commit -m "feat(monitoring): let record_usage take an exact provider cost

OpenRouter returns usage.cost on every response. A caller that has it
passes cost_usd and the crew is priced exactly instead of through the
litellm estimate.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 2: OpenRouter structured client

**Files:**
- Modify: `src/finwiz/config/endpoints.py` (add after `PERPLEXITY_SEARCH`)
- Create: `src/finwiz/infrastructure/research/__init__.py`
- Create: `src/finwiz/infrastructure/research/openrouter_structured.py`
- Modify: `tests/conftest.py:96-100`
- Create: `tests/unit/infrastructure/research/` (no `__init__.py`: the sibling `resilience/` and `monitoring/` test directories have none)
- Create: `tests/unit/infrastructure/research/test_openrouter_structured.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class Citation:
    url: str
    title: str = ""
    content: str = ""

@dataclass(frozen=True)
class SearchOptions:
    engine: str = "exa"
    max_results: int = <RESEARCH_WEB_MAX_RESULTS, default 8>
    recency_hint: str | None = None   # "month" | "week" | None

@dataclass(frozen=True)
class ResearchResult[T: BaseModel]:
    data: T
    citations: tuple[Citation, ...]
    cost_usd: float | None
    prompt_tokens: int
    completion_tokens: int

async def openrouter_structured[T: BaseModel](
    *, prompt: str, schema: type[T], system: str,
    search: SearchOptions | None = SearchOptions(),
    timeout: float = 60.0, api_key: str | None = None,
) -> ResearchResult[T] | None

def _build_client(timeout: float) -> httpx.AsyncClient   # the test seam
```

- Consumes: `finwiz.config.endpoints.OPENROUTER_CHAT`.

- [ ] **Step 1: Add the endpoint constant**

In `src/finwiz/config/endpoints.py`, after the `PERPLEXITY_SEARCH` line:

```python
# OpenRouter chat completions, used directly (httpx) by
# infrastructure/research/openrouter_structured.py for web-grounded structured
# research. RESEARCH_BASE_URL lets tests and proxies redirect it.
OPENROUTER_CHAT: str = os.getenv("RESEARCH_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions"
```

- [ ] **Step 2: Isolate the key in tests**

In `tests/conftest.py`, extend `_EXTRA_CONFIG_ENV_VARS`:

```python
_EXTRA_CONFIG_ENV_VARS = (
    "PORTFOLIO_PARALLEL_LIMIT",
    "DEEP_ANALYSIS_PARALLEL_LIMIT",
    "PERPLEXITY_API_KEY",
    "PPLX_API_KEY",
    "OPENROUTER_API_KEY",
)
```

And extend the comment above it with one sentence: `OPENROUTER_API_KEY is cleared for the same reason: research_with_retry skips the primary provider without it.`

Then run `rtk uv run pytest tests/unit/crews tests/unit/infrastructure -q` to confirm nothing depended on an ambient OpenRouter key. Expected: green. If a test now fails for want of the key, it was leaking the developer's `.env`; give it `monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")` in that test.

- [ ] **Step 3: Write the failing client tests**

`tests/unit/infrastructure/research/test_openrouter_structured.py`:

```python
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


async def test_missing_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        await openrouter_structured(prompt="p", schema=_Payload, system="s")


async def test_env_key_is_used_when_no_explicit_key(mocker, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "env-test-key")
    seen = _install(mocker, lambda r: httpx.Response(200, json=_ok_body('{"value": "ok"}')))

    await openrouter_structured(prompt="p", schema=_Payload, system="s")

    assert seen[0].headers["authorization"] == "Bearer env-test-key"
```

- [ ] **Step 4: Run to verify they fail**

Run: `rtk uv run pytest tests/unit/infrastructure/research/test_openrouter_structured.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'finwiz.infrastructure.research'`.

- [ ] **Step 5: Implement the client**

`src/finwiz/infrastructure/research/__init__.py`:

```python
"""Direct research providers (one HTTP call, native structured output, no agent layer)."""
```

`src/finwiz/infrastructure/research/openrouter_structured.py`:

```python
"""One web-grounded, schema-constrained call to OpenRouter.

OpenRouter exposes web search for any model through the ``web`` plugin and
returns the exact cost of every request in ``usage.cost``. Combined with a
strict ``json_schema`` response format this is a single HTTP call that does
what a Perplexity Sonar call did, on the model the rest of FinWiz already runs
(``google/gemini-3.8-flash``), for roughly a third of the price. No CrewAI
``LLM`` wrapper: it would hide the citations and the cost (see memory rule
"CrewAI only for reasoning").

Failure policy mirrors the vendored Perplexity client so the retry wrapper can
treat both providers alike: every HTTP, transport, JSON or Pydantic failure is
logged at WARNING and returned as ``None``; only a missing API key raises,
before any request is made, so a misconfiguration fails fast instead of
burning the attempt budget. The prompt body and the key are never logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import httpx
from pydantic import BaseModel

from finwiz.config.endpoints import OPENROUTER_CHAT
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_MODEL = "google/gemini-3.8-flash"
_DEFAULT_WEB_MAX_RESULTS = 8
_MAX_TOKENS = 4000

# The Exa engine has no recency parameter on OpenRouter, so the window is
# expressed in the prompt. Keys match perplexity_with_retry's
# search_recency_filter values so call sites pass the same string to either.
_RECENCY_SENTENCES: dict[str, str] = {
    "month": "Ne retiens que des sources publiées au cours du dernier mois.",
    "week": "Ne retiens que des sources publiées au cours de la dernière semaine.",
}

_HEADERS_STATIC = {
    "Content-Type": "application/json",
    # OpenRouter asks for these so the app shows up in its activity views.
    "HTTP-Referer": "https://github.com/fjacquet/finwiz",
    "X-Title": "FinWiz",
}


def _web_max_results() -> int:
    return max(1, int(os.getenv("RESEARCH_WEB_MAX_RESULTS", str(_DEFAULT_WEB_MAX_RESULTS))))


@dataclass(frozen=True)
class Citation:
    """One ``url_citation`` annotation from the response."""

    url: str
    title: str = ""
    content: str = ""


@dataclass(frozen=True)
class SearchOptions:
    """Web plugin settings. ``None`` in place of an instance disables search."""

    engine: str = "exa"
    max_results: int = field(default_factory=_web_max_results)
    recency_hint: str | None = None


@dataclass(frozen=True)
class ResearchResult[T: BaseModel]:
    """Validated data plus what the provider told us about the call."""

    data: T
    citations: tuple[Citation, ...]
    cost_usd: float | None
    prompt_tokens: int
    completion_tokens: int


def _build_client(timeout: float) -> httpx.AsyncClient:
    """Test seam: unit tests return a client on an ``httpx.MockTransport``."""
    return httpx.AsyncClient(timeout=timeout)


def _extract_citations(annotations: list[dict[str, Any]]) -> tuple[Citation, ...]:
    seen: set[str] = set()
    out: list[Citation] = []
    for annotation in annotations:
        if not isinstance(annotation, dict):
            continue
        cite = annotation.get("url_citation") or {}
        url = str(cite.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(Citation(url=url, title=str(cite.get("title") or ""), content=str(cite.get("content") or "")))
    return tuple(out)


def _build_payload(*, prompt: str, schema: type[BaseModel], system: str, search: SearchOptions | None) -> dict[str, Any]:
    user = prompt
    if search is not None and search.recency_hint in _RECENCY_SENTENCES:
        user = f"{prompt}\n\n{_RECENCY_SENTENCES[search.recency_hint]}"
    payload: dict[str, Any] = {
        "model": os.getenv("RESEARCH_MODEL", _DEFAULT_MODEL),
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema", "json_schema": {"name": schema.__name__, "strict": True, "schema": schema.model_json_schema()}},
        "max_tokens": _MAX_TOKENS,
    }
    if search is not None:
        payload["plugins"] = [{"id": "web", "engine": search.engine, "max_results": search.max_results}]
    return payload


async def openrouter_structured[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search: SearchOptions | None = SearchOptions(),
    timeout: float = 60.0,
    api_key: str | None = None,
) -> ResearchResult[T] | None:
    """POST one chat completion and validate the reply against ``schema``.

    Args:
        prompt: User turn. A recency sentence is appended when ``search`` has a hint.
        schema: Pydantic model the reply must validate against; its class name is
            the ``json_schema.name`` OpenRouter requires.
        system: System turn.
        search: Web plugin options, or ``None`` for a plain completion.
        timeout: httpx timeout in seconds for the whole request.
        api_key: Overrides ``OPENROUTER_API_KEY``.

    Returns:
        A :class:`ResearchResult`, or ``None`` on any failure after the request
        was attempted.

    Raises:
        ValueError: when no API key is available (checked before any request).
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    payload = _build_payload(prompt=prompt, schema=schema, system=system, search=search)
    headers = {**_HEADERS_STATIC, "Authorization": f"Bearer {key}"}

    try:
        async with _build_client(timeout) as client:
            response = await client.post(OPENROUTER_CHAT, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.warning(f"OpenRouter call for {schema.__name__} failed in transport: {type(exc).__name__}")
        return None

    if response.status_code != 200:
        logger.warning(f"OpenRouter call for {schema.__name__} returned HTTP {response.status_code}")
        return None

    try:
        body = response.json()
        message = body["choices"][0]["message"]
        data = schema.model_validate_json(message.get("content") or "")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        # pydantic.ValidationError and json.JSONDecodeError are both ValueError subclasses.
        logger.warning(f"OpenRouter reply for {schema.__name__} did not validate: {type(exc).__name__}")
        return None

    usage = body.get("usage") or {}
    raw_cost = usage.get("cost")
    return ResearchResult(
        data=data,
        citations=_extract_citations(message.get("annotations") or []),
        cost_usd=float(raw_cost) if raw_cost is not None else None,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
    )
```

- [ ] **Step 6: Run the client tests**

Run: `rtk uv run pytest tests/unit/infrastructure/research/test_openrouter_structured.py -v`
Expected: 10 PASS.

If `test_missing_key_raises_value_error` fails because the key is present, the conftest change in Step 2 did not take; check `_EXTRA_CONFIG_ENV_VARS`.

- [ ] **Step 7: Type-check and commit**

Run: `rtk uv run mypy src/finwiz/infrastructure/research src/finwiz/config/endpoints.py`
Expected: no errors.

```bash
rtk git add src/finwiz/config/endpoints.py src/finwiz/infrastructure/research tests/conftest.py tests/unit/infrastructure/research
rtk git commit -m "feat(research): OpenRouter web-grounded structured client

One httpx POST with the web plugin (Exa) and a strict json_schema
response format. Returns the validated model, deduplicated url_citation
annotations and the exact usage.cost; None on any failure after the
request, ValueError only for a missing key.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 3: Retry, throttle, cost recording and Perplexity fallback

**Files:**
- Create: `src/finwiz/infrastructure/resilience/research_retry.py`
- Modify: `src/finwiz/infrastructure/resilience/perplexity_retry.py:1-19` (docstring first paragraph)
- Create: `tests/unit/infrastructure/resilience/test_research_retry.py`

**Interfaces:**
- Consumes: `openrouter_structured`, `SearchOptions`, `ResearchResult`, `Citation` from Task 2; `perplexity_with_retry` from `perplexity_retry`; `PerplexityFallbackManager.calculate_backoff_delay(attempt, base_delay, max_delay)`; `get_token_monitor()` and `record_usage(..., cost_usd=...)` from Task 1.
- Produces:

```python
RESEARCH_CONCURRENCY: int
def get_research_semaphore() -> threading.BoundedSemaphore
async def research_with_retry[T: BaseModel](
    *, prompt: str, schema: type[T], system: str,
    search_recency_filter: str | None = "month",
    timeout: float = 15.0, max_attempts: int = 4, base_delay: float = 1.0,
    kind: str = "research",
) -> ResearchResult[T] | None
```

- [ ] **Step 1: Write the failing tests**

`tests/unit/infrastructure/resilience/test_research_retry.py`:

```python
"""Retry, throttle, cost recording and Perplexity fallback for research calls."""

from __future__ import annotations

import asyncio
import importlib
import threading

import pytest
from pydantic import BaseModel

from finwiz.infrastructure.monitoring.litellm_callback import TokenMonitorCallback
from finwiz.infrastructure.research.openrouter_structured import Citation, ResearchResult
from finwiz.infrastructure.resilience import research_retry
from finwiz.infrastructure.resilience.research_retry import get_research_semaphore, research_with_retry

_CLIENT = "finwiz.infrastructure.resilience.research_retry.openrouter_structured"
_FALLBACK = "finwiz.infrastructure.resilience.research_retry.perplexity_with_retry"
_SLEEP = "finwiz.infrastructure.resilience.research_retry.asyncio.sleep"
_BACKOFF = "finwiz.infrastructure.resilience.research_retry.PerplexityFallbackManager.calculate_backoff_delay"


class _Payload(BaseModel):
    value: str


def _result(value: str = "ok", cost: float | None = 0.01) -> ResearchResult[_Payload]:
    return ResearchResult(data=_Payload(value=value), citations=(Citation(url="https://a"),), cost_usd=cost, prompt_tokens=100, completion_tokens=50)


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    """OpenRouter key present, Perplexity keys absent, unless a test says otherwise."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)


@pytest.fixture
def monitor(mocker) -> TokenMonitorCallback:
    cb = TokenMonitorCallback()
    mocker.patch("finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor", return_value=cb)
    return cb


async def test_first_success_is_returned_and_costed(mocker, monitor):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))
    sleep = mocker.patch(_SLEEP, new=mocker.AsyncMock())

    result = await research_with_retry(prompt="p", schema=_Payload, system="s", kind="swot")

    assert result == _result()
    assert client.await_count == 1
    assert sleep.await_count == 0
    crew = monitor.get_cost_summary()["per_crew"]["research_swot"]
    assert crew == {"cost": pytest.approx(0.01), "calls": 1, "tokens": {"prompt": 100, "completion": 50}, "cost_known": True}


async def test_recency_filter_is_forwarded_as_the_search_hint(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))

    await research_with_retry(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=33.0)

    kwargs = client.await_args.kwargs
    assert kwargs["search"].recency_hint == "week"
    assert kwargs["timeout"] == 33.0
    assert kwargs["prompt"] == "p"
    assert kwargs["system"] == "s"
    assert kwargs["schema"] is _Payload


async def test_three_failures_then_success(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(side_effect=[None, None, None, _result("late")]))
    sleep = mocker.patch(_SLEEP, new=mocker.AsyncMock())
    mocker.patch(_BACKOFF, return_value=0.5)

    result = await research_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is not None and result.data.value == "late"
    assert client.await_count == 4
    assert [c.args[0] for c in sleep.await_args_list] == [0.5, 0.5, 0.5]


async def test_a_raise_counts_as_a_failed_attempt(mocker):
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock(side_effect=RuntimeError("boom")))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock())

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=2) is None
    assert client.await_count == 2
    fallback.assert_not_awaited()


async def test_exhaustion_without_perplexity_key_returns_none(mocker):
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock())

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=2) is None
    fallback.assert_not_awaited()


async def test_exhaustion_with_perplexity_key_falls_back_once(mocker, monkeypatch, monitor):
    monkeypatch.setenv("PPLX_API_KEY", "test-pplx-key")
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=_Payload(value="pplx")))

    result = await research_with_retry(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=20.0, max_attempts=2, kind="porter")

    assert result == ResearchResult(data=_Payload(value="pplx"), citations=(), cost_usd=None, prompt_tokens=0, completion_tokens=0)
    fallback.assert_awaited_once_with(prompt="p", schema=_Payload, system="s", search_recency_filter="week", timeout=20.0, max_attempts=1)
    crew = monitor.get_cost_summary()["per_crew"]["research_porter"]
    assert crew["calls"] == 1
    assert crew["cost_known"] is False


async def test_fallback_none_is_none(mocker, monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-pplx-key")
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=None))
    mocker.patch(_SLEEP, new=mocker.AsyncMock())
    mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=None))

    assert await research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1) is None


async def test_no_openrouter_key_skips_straight_to_fallback(mocker, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("PPLX_API_KEY", "test-pplx-key")
    client = mocker.patch(_CLIENT, new=mocker.AsyncMock())
    fallback = mocker.patch(_FALLBACK, new=mocker.AsyncMock(return_value=_Payload(value="pplx")))

    result = await research_with_retry(prompt="p", schema=_Payload, system="s")

    assert result is not None and result.data.value == "pplx"
    client.assert_not_awaited()
    fallback.assert_awaited_once()


async def test_cost_recording_failure_never_breaks_the_call(mocker):
    mocker.patch(_CLIENT, new=mocker.AsyncMock(return_value=_result()))
    mocker.patch("finwiz.infrastructure.monitoring.litellm_callback.get_token_monitor", side_effect=RuntimeError("monitor down"))

    assert await research_with_retry(prompt="p", schema=_Payload, system="s") == _result()


class TestConcurrencyFloor:
    def _reload(self, monkeypatch, value: str | None) -> None:
        if value is None:
            monkeypatch.delenv("RESEARCH_CONCURRENCY", raising=False)
        else:
            monkeypatch.setenv("RESEARCH_CONCURRENCY", value)
        importlib.reload(research_retry)

    def test_zero_is_floored_to_one(self, monkeypatch):
        try:
            self._reload(monkeypatch, "0")
            assert research_retry.RESEARCH_CONCURRENCY == 1
        finally:
            self._reload(monkeypatch, None)

    def test_default_is_six(self, monkeypatch):
        try:
            self._reload(monkeypatch, None)
            assert research_retry.RESEARCH_CONCURRENCY == 6
        finally:
            self._reload(monkeypatch, None)


def test_throttle_is_a_loop_agnostic_process_singleton():
    assert get_research_semaphore() is get_research_semaphore()
    assert isinstance(get_research_semaphore(), threading.BoundedSemaphore)


def test_a_cap_of_one_serialises_two_threads_on_independent_loops(mocker, monkeypatch):
    """RESEARCH_CONCURRENCY=1: two holdings on two loops never overlap."""
    monkeypatch.setattr(research_retry, "RESEARCH_CONCURRENCY", 1)
    monkeypatch.setattr(research_retry, "_throttle", None)

    lock = threading.Lock()
    state = {"in_flight": 0, "max_in_flight": 0}

    async def fake_call(**_kwargs):
        with lock:
            state["in_flight"] += 1
            state["max_in_flight"] = max(state["max_in_flight"], state["in_flight"])
        try:
            await asyncio.sleep(0.05)
            return _result()
        finally:
            with lock:
                state["in_flight"] -= 1

    mocker.patch.object(research_retry, "openrouter_structured", new=fake_call)
    results: list[object] = []

    def worker() -> None:
        results.append(asyncio.run(research_with_retry(prompt="p", schema=_Payload, system="s", max_attempts=1)))

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10.0)

    assert [t.name for t in threads if t.is_alive()] == []
    assert len(results) == 2 and all(r is not None for r in results)
    assert state["max_in_flight"] == 1
```

- [ ] **Step 2: Run to verify they fail**

Run: `rtk uv run pytest tests/unit/infrastructure/resilience/test_research_retry.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'finwiz.infrastructure.resilience.research_retry'`.

- [ ] **Step 3: Implement the wrapper**

`src/finwiz/infrastructure/resilience/research_retry.py`:

```python
"""Retry, throttle, cost recording and fallback for web-grounded research calls.

Primary provider is :func:`openrouter_structured`; :func:`perplexity_with_retry`
is the fallback, tried once when every OpenRouter attempt failed and a
Perplexity key is configured. Both providers return ``None`` for any failure
after the request was made and raise only for a missing key, so the loop
retries **by outcome** and treats a raise like a ``None``. Backoff is delegated
to ``PerplexityFallbackManager.calculate_backoff_delay`` -- the same
exponential-with-jitter helper ``perplexity_retry`` uses.

Each successful OpenRouter call records its exact ``usage.cost`` under
``research_{kind}`` in the run's cost summary; a fallback answer is recorded
as one call with unknown cost, so the summary shows ``cost n/a`` rather than a
false zero.
"""

from __future__ import annotations

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from finwiz.infrastructure.research.openrouter_structured import ResearchResult, SearchOptions, openrouter_structured
from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry
from finwiz.tools.logger import get_logger
from finwiz.tools.perplexity_errors import PerplexityFallbackManager

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = get_logger(__name__)

# Process-wide cap on in-flight OpenRouter research calls. Floored at 1 for the
# same reason as PERPLEXITY_CONCURRENCY: a 0 would spin _throttle_slot() forever
# and a negative value would raise out of BoundedSemaphore's constructor.
RESEARCH_CONCURRENCY = max(1, int(os.getenv("RESEARCH_CONCURRENCY", "6")))

_MAX_BACKOFF_DELAY = 60.0
_SLOT_POLL_INTERVAL = 0.01

_throttle: threading.BoundedSemaphore | None = None
_throttle_init_lock = threading.Lock()


def get_research_semaphore() -> threading.BoundedSemaphore:
    """Return the process-wide research throttle.

    A ``threading`` primitive, not an ``asyncio`` one: production runs one
    holding per ThreadPoolExecutor worker, each on its own fresh event loop
    (``asyncio.run`` inside ``_run_coroutine_sync``), and an ``asyncio.Semaphore``
    binds to the first loop that contends on it and raises on every other one.
    See ``perplexity_retry.get_perplexity_semaphore`` for the full account,
    including why the lazy init is double-checked-locked.
    """
    global _throttle
    if _throttle is None:
        with _throttle_init_lock:
            if _throttle is None:
                _throttle = threading.BoundedSemaphore(RESEARCH_CONCURRENCY)
    return _throttle


@asynccontextmanager
async def _throttle_slot() -> AsyncIterator[None]:
    """Hold one slot; poll without blocking so the loop stays free."""
    throttle = get_research_semaphore()
    while not throttle.acquire(blocking=False):
        await asyncio.sleep(_SLOT_POLL_INTERVAL)
    try:
        yield
    finally:
        throttle.release()


def _has_openrouter_key() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _has_perplexity_key() -> bool:
    return bool(os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY"))


def _record_cost(kind: str, result: ResearchResult[Any]) -> None:
    """Attribute one research call to ``research_{kind}``; never raises."""
    try:
        from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

        monitor = get_token_monitor()
        if monitor is None:
            return
        usage = SimpleNamespace(prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens, successful_requests=1)
        monitor.record_usage(f"research_{kind}", usage, model=None, cost_usd=result.cost_usd)
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug(f"Cost tracking skipped for research_{kind}: {exc}")


async def _perplexity_fallback[T: BaseModel](
    *, prompt: str, schema: type[T], system: str, search_recency_filter: str | None, timeout: float, kind: str
) -> ResearchResult[T] | None:
    if not _has_perplexity_key():
        return None
    data = await perplexity_with_retry(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, max_attempts=1)
    if data is None:
        return None
    logger.info(f"research_{kind}: {schema.__name__} answered by the Perplexity fallback")
    result: ResearchResult[T] = ResearchResult(data=data, citations=(), cost_usd=None, prompt_tokens=0, completion_tokens=0)
    _record_cost(kind, result)
    return result


async def research_with_retry[T: BaseModel](
    *,
    prompt: str,
    schema: type[T],
    system: str,
    search_recency_filter: str | None = "month",
    timeout: float = 15.0,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    kind: str = "research",
) -> ResearchResult[T] | None:
    """Call OpenRouter with bounded retries, then Perplexity once, then give up.

    Args:
        prompt: User prompt.
        schema: Pydantic model the reply must validate against.
        system: System prompt.
        search_recency_filter: ``"month"``, ``"week"`` or ``None``; becomes the
            OpenRouter recency hint and, on fallback, Perplexity's filter.
        timeout: Per-attempt timeout in seconds.
        max_attempts: OpenRouter attempts including the first. Must be >= 1.
        base_delay: Seconds before the second attempt; doubles each retry with
            jitter, capped at 60 s.
        kind: Cost attribution suffix (``swot``, ``porter``, ``posture``,
            ``factpack``, ``news``).

    Returns:
        A :class:`ResearchResult` from whichever provider answered, or ``None``.
    """
    if not _has_openrouter_key():
        logger.warning(f"research_{kind}: OPENROUTER_API_KEY not configured; trying the Perplexity fallback directly")
        return await _perplexity_fallback(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, kind=kind)

    search = SearchOptions(recency_hint=search_recency_filter)
    for attempt in range(max_attempts):
        try:
            async with _throttle_slot():
                result = await openrouter_structured(prompt=prompt, schema=schema, system=system, search=search, timeout=timeout)
        except Exception as exc:
            logger.warning(f"research_{kind}: {schema.__name__} raised on attempt {attempt + 1}/{max_attempts}: {type(exc).__name__}")
            result = None

        if result is not None:
            if attempt > 0:
                logger.info(f"research_{kind}: {schema.__name__} succeeded on attempt {attempt + 1}/{max_attempts}")
            _record_cost(kind, result)
            return result

        if attempt < max_attempts - 1:
            delay = PerplexityFallbackManager.calculate_backoff_delay(attempt, base_delay, _MAX_BACKOFF_DELAY)
            logger.warning(f"research_{kind}: {schema.__name__} returned no result (attempt {attempt + 1}/{max_attempts}); retrying in {delay:.1f}s")
            await asyncio.sleep(delay)

    logger.warning(f"research_{kind}: {schema.__name__} exhausted {max_attempts} OpenRouter attempts")
    return await _perplexity_fallback(prompt=prompt, schema=schema, system=system, search_recency_filter=search_recency_filter, timeout=timeout, kind=kind)
```

- [ ] **Step 4: Update the Perplexity wrapper docstring**

Replace the first line of `src/finwiz/infrastructure/resilience/perplexity_retry.py` (`"""Retry-with-backoff and concurrency control for Perplexity structured calls.`) with:

```python
"""Retry-with-backoff and concurrency control for Perplexity structured calls.

Fallback provider only: the primary research path is
``infrastructure/resilience/research_retry.py`` (OpenRouter web-grounded
research), which calls this wrapper once, with ``max_attempts=1``, when every
OpenRouter attempt failed and a Perplexity key is configured.
```

Keep the rest of the docstring as it is.

- [ ] **Step 5: Run the wrapper tests and the Perplexity ones**

Run: `rtk uv run pytest tests/unit/infrastructure/resilience/test_research_retry.py tests/unit/infrastructure/resilience/test_perplexity_retry.py -v`
Expected: all PASS.

If `test_first_success_is_returned_and_costed` fails on the `tokens` dict, compare against `get_cost_summary()`'s shape in `litellm_callback.py:157-172`; the assertion mirrors it exactly.

- [ ] **Step 6: Type-check and commit**

Run: `rtk uv run mypy src/finwiz/infrastructure`
Expected: clean.

```bash
rtk git add src/finwiz/infrastructure/resilience/research_retry.py src/finwiz/infrastructure/resilience/perplexity_retry.py tests/unit/infrastructure/resilience/test_research_retry.py
rtk git commit -m "feat(resilience): research_with_retry with cost recording and Perplexity fallback

Same keyword surface as perplexity_with_retry plus kind= for cost
attribution. Process-wide threading throttle (RESEARCH_CONCURRENCY,
default 6), backoff by outcome, exact usage.cost recorded under
research_{kind}; one Perplexity attempt on exhaustion when a PPLX key
is set, recorded with cost n/a.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 4: Strategic research (SWOT, Porter, posture)

**Files:**
- Modify: `src/finwiz/analysis/strategic_research.py:1-15,24,223-238,331-337`
- Modify: `tests/unit/analysis/test_strategic_research_retry.py`

**Interfaces:**
- Consumes: `research_with_retry(..., kind=...) -> ResearchResult[T] | None`.
- Produces: unchanged public signatures of `gather_strategic_analysis`, `gather_strategic_analysis_sync`, `synthesize_portfolio_posture`, `synthesize_portfolio_posture_sync`.

- [ ] **Step 1: Update the tests**

Replace the whole of `tests/unit/analysis/test_strategic_research_retry.py` with:

```python
"""strategic_research must route every research call through research_with_retry.

The 2026-08-16 end-to-end run hit Perplexity 429s eight times against the
strategic frameworks and lost both for two holdings (DIS, ORCL), because
``strategic_research.py`` called the client directly instead of going through
the retry wrapper. The wrapper is now ``research_with_retry`` (OpenRouter
primary, Perplexity fallback); the invariant is the same: no direct client call.
"""

from __future__ import annotations

import pytest

from finwiz.infrastructure.research.openrouter_structured import ResearchResult

_CLIENT = "finwiz.infrastructure.resilience.research_retry.openrouter_structured"
_SEAM = "finwiz.analysis.strategic_research.research_with_retry"


def _wrap(model):
    return ResearchResult(data=model, citations=(), cost_usd=0.01, prompt_tokens=1, completion_tokens=1)


@pytest.mark.asyncio
async def test_a_transient_failure_does_not_lose_a_framework(mocker, monkeypatch):
    """One failed attempt then success must yield the analysis, not None."""
    from finwiz.analysis import strategic_research

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    calls = {"n": 0}

    async def flaky(*, prompt, schema, system, **kw):
        calls["n"] += 1
        if calls["n"] <= 2:  # first attempt of each of the two frameworks
            return None
        return _wrap(schema.model_construct(strategic_score=0.6, confidence=0.7))

    mocker.patch(_CLIENT, side_effect=flaky)
    mocker.patch("finwiz.infrastructure.resilience.research_retry.PerplexityFallbackManager.calculate_backoff_delay", return_value=0.0)

    result = await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert result is not None
    assert calls["n"] > 2


@pytest.mark.asyncio
async def test_strategic_calls_go_through_the_retry_wrapper(mocker):
    """Regression: a direct client import bypassed retry and throttle."""
    from finwiz.analysis import strategic_research

    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=None))

    await strategic_research.gather_strategic_analysis(ticker="ORCL", sector="Tech", industry="Software", description="desc")

    assert wrapper.await_count == 2
    assert sorted(c.kwargs["kind"] for c in wrapper.await_args_list) == ["porter", "swot"]


@pytest.mark.asyncio
async def test_frameworks_are_unwrapped_from_the_research_result(mocker):
    from finwiz.analysis import strategic_research
    from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, SwotAnalysis

    async def answer(*, schema, **kw):
        return _wrap(schema.model_construct(strategic_score=0.6, confidence=0.7))

    mocker.patch(_SEAM, side_effect=answer)

    result = await strategic_research.gather_strategic_analysis(ticker="ORCL")

    assert result is not None
    assert isinstance(result.swot, SwotAnalysis)
    assert isinstance(result.five_forces, FiveForcesAnalysis)


@pytest.mark.asyncio
async def test_portfolio_posture_uses_kind_posture_and_unwraps(mocker):
    from finwiz.analysis import strategic_research
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative, StrategicAnalysis, SwotAnalysis

    narrative = PortfolioPostureNarrative(competitive_verdict="Position concurrentielle solide.", swot_verdict="Forces dominantes.", strategic_score=0.5, confidence=0.5)
    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=_wrap(narrative)))
    holdings = {"ORCL": StrategicAnalysis(swot=SwotAnalysis(strategic_score=0.6, confidence=0.7), five_forces=None)}

    posture = await strategic_research.synthesize_portfolio_posture(holdings, holdings_covered=1, holdings_total=1, value_covered_pct=100.0)

    assert wrapper.await_args.kwargs["kind"] == "posture"
    assert posture is not None
    assert posture.holdings_covered == 1
```

`PortfolioPostureNarrative` requires `competitive_verdict`, `swot_verdict`, `strategic_score` and `confidence`; `SwotAnalysis` and `FiveForcesAnalysis` have defaults for every field.

- [ ] **Step 2: Run to verify the new tests fail**

Run: `rtk uv run pytest tests/unit/analysis/test_strategic_research_retry.py -v`
Expected: `test_a_transient_failure_does_not_lose_a_framework` FAILS (the module still calls `perplexity_with_retry`, which finds no key), the seam tests FAIL with `AttributeError: ... has no attribute 'research_with_retry'`.

- [ ] **Step 3: Swap the wrapper**

In `src/finwiz/analysis/strategic_research.py`:

Line 24, replace:

```python
from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry
```

with:

```python
from finwiz.infrastructure.resilience.research_retry import research_with_retry
```

Module docstring lines 3-11, replace `Two independent Perplexity calls (SWOT/Porter's Five Forces) per` with `Two independent web-grounded research calls (SWOT/Porter's Five Forces) per`, and replace `All run via direct Perplexity Sonar Pro with native\n``response_format: json_schema`` — no CrewAI agent layer (single provider\ncall + native structured output = no reasoning needed).` with `All run via ``research_with_retry`` (OpenRouter web plugin + native\n``response_format: json_schema``, Perplexity as fallback) — no CrewAI agent\nlayer (single provider call + native structured output = no reasoning needed).`

Lines 223-239 in `gather_strategic_analysis`:

```python
    swot_coro = research_with_retry(
        prompt=_swot_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        search_recency_filter="month",
        timeout=timeout,
        max_attempts=_FRAMEWORK_MAX_ATTEMPTS,
        kind="swot",
    )
    porter_coro = research_with_retry(
        prompt=_porter_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=FiveForcesAnalysis,
        system=SYSTEM_FR,
        search_recency_filter="month",
        timeout=timeout,
        max_attempts=_FRAMEWORK_MAX_ATTEMPTS,
        kind="porter",
    )
    swot_result, porter_result = await asyncio.gather(swot_coro, porter_coro)
    # Citations are ignored here for now: SwotAnalysis / FiveForcesAnalysis have
    # no field for them and adding one is a report change (spec: out of scope).
    swot = swot_result.data if swot_result is not None else None
    porter = porter_result.data if porter_result is not None else None
```

Lines 331-339 in `synthesize_portfolio_posture`:

```python
    research = await research_with_retry(
        prompt=_portfolio_prompt(payload, date_anchor),
        schema=PortfolioPostureNarrative,
        system=SYSTEM_FR,
        search_recency_filter="week",
        timeout=timeout,
        kind="posture",
    )
    if research is None:
        return None
    narrative = research.data
```

- [ ] **Step 4: Run strategic tests**

Run: `rtk uv run pytest tests/unit/analysis/ -k "strategic" -v`
Expected: all PASS. Other strategic tests (`test_strategic_research*.py`) that patched `perplexity_with_retry` on the module: grep them and re-point.

```bash
rtk grep -rn "strategic_research.perplexity_with_retry" tests
```

Each hit becomes `finwiz.analysis.strategic_research.research_with_retry`, and its `return_value` must be wrapped: `ResearchResult(data=<model>, citations=(), cost_usd=None, prompt_tokens=0, completion_tokens=0)`.

- [ ] **Step 5: Commit**

```bash
rtk git add src/finwiz/analysis/strategic_research.py tests/unit/analysis/
rtk git commit -m "feat(analysis): SWOT, Porter and posture go through research_with_retry

kind=swot|porter|posture for cost attribution; .data unwrapped, citations
ignored until the schemas grow a field for them.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 5: Fact-pack gap-fill

**Files:**
- Rename: `src/finwiz/analysis/fact_pack/sources/perplexity_source.py` → `research_source.py`
- Modify: `src/finwiz/analysis/fact_pack/composer.py:11,92,99`
- Modify: `src/finwiz/analysis/fact_pack_research.py:1-17,138-143,146-152`
- Modify: `src/finwiz/reporting/sections/factpack.py:98`
- Modify: `src/finwiz/analysis/CLAUDE.md:15,26`
- Modify: `tests/unit/analysis/fact_pack/test_gap_fill.py`
- Test: any test asserting the `"perplexity.gap_fill"` literal or the "Perplexity" label (`rtk grep -rn "gap_fill\|\"Perplexity\"" tests`)

**Interfaces:**
- Produces: `finwiz.analysis.fact_pack.sources.research_source.fetch_missing_events(ticker: str, company_name: str, sector: str | None, industry: str | None, timeout: float = 15.0) -> tuple[str, ...]` (signature unchanged); provenance literal `"research.gap_fill"`; report label `"recherche web"`.

- [ ] **Step 1: Rename and update the tests**

```bash
rtk git mv src/finwiz/analysis/fact_pack/sources/perplexity_source.py src/finwiz/analysis/fact_pack/sources/research_source.py
```

In `tests/unit/analysis/fact_pack/test_gap_fill.py`, replace every `perplexity_source` with `research_source` (import line 5 and the five `mocker.patch.object(...)` calls), and rename `test_an_equity_without_events_asks_perplexity` to `test_an_equity_without_events_asks_for_research`. Add one test to the class:

```python
    def test_gap_filled_events_are_tagged_as_research(self, mocker):
        mocker.patch.object(
            composer.yfinance_source,
            "resolve",
            return_value={"quoteType": "EQUITY", "longBusinessSummary": "Builds planes.", "companyOfficers": [{"name": "G. Faury", "title": "CEO"}]},
        )
        mocker.patch.object(composer.yfinance_source, "filing_events", return_value=FactPackFragment())
        mocker.patch.object(composer.yfinance_source, "news_events", return_value=FactPackFragment())
        mocker.patch.object(composer, "is_feature_enabled", return_value=True)
        mocker.patch.object(research_source, "fetch_missing_events", return_value=("Airbus wins order",))

        pack = composer.compose_fact_pack("AIR.PA", "Airbus SE", None, None, "stock")

        assert "research.gap_fill" in pack.sources_used
        assert "perplexity.gap_fill" not in pack.sources_used
```

If `FactPack` names the field differently from `sources_used`, check `src/finwiz/schemas/hybrid_analysis/fact_pack.py` and use its name.

Add a wrapper-seam test in a new file `tests/unit/analysis/fact_pack/test_research_source.py`:

```python
"""fetch_missing_events asks research_with_retry once and never raises."""

from __future__ import annotations

from finwiz.analysis.fact_pack.sources import research_source
from finwiz.analysis.fact_pack_research import _FactPackRaw
from finwiz.infrastructure.research.openrouter_structured import ResearchResult

_SEAM = "finwiz.infrastructure.resilience.research_retry.research_with_retry"


def test_events_are_unwrapped_capped_and_truncated(mocker):
    raw = _FactPackRaw(recent_events=[f"event {i} " + "x" * 300 for i in range(12)])
    wrapper = mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=ResearchResult(data=raw, citations=(), cost_usd=0.01, prompt_tokens=1, completion_tokens=1)))

    events = research_source.fetch_missing_events("AIR.PA", "Airbus SE", "Industrials", "Aerospace")

    assert wrapper.await_args.kwargs["kind"] == "factpack"
    assert wrapper.await_args.kwargs["schema"] is _FactPackRaw
    assert len(events) == 10
    assert all(len(e) <= 200 for e in events)


def test_none_from_research_is_an_empty_tuple(mocker):
    mocker.patch(_SEAM, new=mocker.AsyncMock(return_value=None))

    assert research_source.fetch_missing_events("AIR.PA", "Airbus SE", None, None) == ()


def test_a_raise_is_an_empty_tuple(mocker):
    mocker.patch(_SEAM, new=mocker.AsyncMock(side_effect=RuntimeError("HTTP 401")))

    assert research_source.fetch_missing_events("AIR.PA", "Airbus SE", None, None) == ()
```

`_FactPackRaw`'s `model_validator` truncates events to 200 chars itself; the source module caps again, so the assertion holds either way.

- [ ] **Step 2: Run to verify failure**

Run: `rtk uv run pytest tests/unit/analysis/fact_pack/test_gap_fill.py tests/unit/analysis/fact_pack/test_research_source.py -v`
Expected: `test_gap_filled_events_are_tagged_as_research` FAILS on the literal; `test_research_source.py` tests FAIL because the source still imports `perplexity_with_retry` (the seam patch has no effect) or error on `ImportError` of `composer` (still importing `perplexity_source`).

- [ ] **Step 3: Rewrite `research_source.py`**

```python
"""Web research, narrowed to the one field structured data cannot supply.

Funds and crypto are complete without it. Equities are too, when the company
files with the SEC or a wire service covered it. What remains is a company with
neither — measured at 6 of 67 holdings. The call goes through
``research_with_retry`` (OpenRouter web plugin, Perplexity as fallback).
"""

from __future__ import annotations

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_EVENT_MAX_CHARS = 200
_MAX_EVENTS = 10


def fetch_missing_events(ticker: str, company_name: str, sector: str | None, industry: str | None, timeout: float = 15.0) -> tuple[str, ...]:
    """Material events for one company. Any failure returns empty; never raises."""
    from finwiz.analysis._helpers import _today_french
    from finwiz.analysis.fact_pack_research import _SYSTEM_FR, _FactPackRaw, _run_coroutine_sync
    from finwiz.infrastructure.resilience.research_retry import research_with_retry

    prompt = (
        f"Date du jour : {_today_french()}.\n\n"
        f"Recherche UNIQUEMENT les événements matériels des 12 derniers mois pour "
        f"{company_name} ({ticker}, {sector or 'secteur inconnu'} / {industry or 'industrie inconnue'}) : "
        "résultats trimestriels notables, fusions-acquisitions, changements de direction, "
        "décisions réglementaires ou judiciaires majeures. Pas de bavardage marketing, "
        "pas de prévisions. Si tu n'as pas de source fiable, renvoie une liste vide."
    )

    try:
        result = _run_coroutine_sync(
            research_with_retry(prompt=prompt, schema=_FactPackRaw, system=_SYSTEM_FR, search_recency_filter="month", timeout=timeout, kind="factpack"),
            timeout=timeout,
        )
    except Exception as e:
        logger.warning(f"fact_pack gap-fill failed for {ticker}: {e}")
        return ()

    if result is None:
        return ()
    return tuple(event[:_EVENT_MAX_CHARS] for event in result.data.recent_events[:_MAX_EVENTS])
```

- [ ] **Step 4: Composer, report label, docstrings**

`src/finwiz/analysis/fact_pack/composer.py`:
- Line 11: `perplexity_source` → `research_source` in the import.
- Lines 73-78 docstring: `Perplexity is consulted only when filings and news both left` → `Web research is consulted only when filings and news both left`.
- Line 92: `perplexity_source.fetch_missing_events(...)` → `research_source.fetch_missing_events(...)`.
- Line 99: `"perplexity.gap_fill"` → `"research.gap_fill"`.

`src/finwiz/reporting/sections/factpack.py:98`: `"perplexity.gap_fill": "Perplexity",` → `"research.gap_fill": "recherche web",`.

`src/finwiz/analysis/fact_pack_research.py`:
- Line 7: `analysis.fact_pack.sources.perplexity_source.fetch_missing_events` → `analysis.fact_pack.sources.research_source.fetch_missing_events`.
- Line 13: `` `perplexity_source` `` → `` `research_source` ``.
- Line 39 (`_FactPackRaw` docstring): `Subset of FactPack returned by Perplexity` → `Subset of FactPack returned by the research provider`.
- Lines 138-143 (`_SYSTEM_FR`): `"au format JSON conforme au schéma fourni. Tu cites tes sources via URLs "\n    "Perplexity. Tu auto-évalues ...` → `"au format JSON conforme au schéma fourni. Tu cites tes sources via les URLs "\n    "des pages web consultées. Tu auto-évalues ...`.
- Line 150: `` `perplexity_source.fetch_missing_events` `` → `` `research_source.fetch_missing_events` ``.

`src/finwiz/analysis/CLAUDE.md`:
- Line 15: `# Perplexity gap-fill support (see analysis/fact_pack/)` → `# Research gap-fill support (see analysis/fact_pack/)`.
- Line 26: `perplexity_source.py  # Equity gap-fill only, behind FF_PERPLEXITY_RESEARCH` → `research_source.py    # Equity gap-fill only (OpenRouter web research, Perplexity fallback), behind FF_PERPLEXITY_RESEARCH`.

- [ ] **Step 5: Sweep for the old names**

```bash
rtk grep -rn "perplexity_source\|perplexity\.gap_fill" src tests docs/*.md CLAUDE.md --include='*.py' --include='*.md' --include='*.yml'
```

Expected: only hits under `docs/superpowers/` (historical plans/specs, leave them) and root `CLAUDE.md:160` (fixed in Task 7). Fix any other hit. Also check report tests:

```bash
rtk grep -rn "\"Perplexity\"" tests/unit/reporting
```

A test asserting the label `Perplexity` for the gap-fill source becomes `recherche web`.

- [ ] **Step 6: Run the fact-pack and reporting tests**

Run: `rtk uv run pytest tests/unit/analysis/fact_pack tests/unit/reporting -q`
Expected: green.

- [ ] **Step 7: Commit**

```bash
rtk git add -A src/finwiz/analysis src/finwiz/reporting/sections/factpack.py tests/unit/analysis/fact_pack tests/unit/reporting
rtk git commit -m "feat(fact-pack): gap-fill via research_with_retry, provenance research.gap_fill

perplexity_source.py renamed research_source.py; the composer tags
gap-filled events research.gap_fill and the report labels it
'recherche web'.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 6: Sentiment news through research

**Files:**
- Modify: `src/finwiz/schemas/perplexity.py` (append two models)
- Modify: `src/finwiz/tools/perplexity_analysis_integration.py:1-7,15-18,51-72,78-120,188-306`
- Modify: `tests/unit/tools/test_perplexity_integration_wrapper.py:81-119,327-392`

**Interfaces:**
- Consumes: `research_with_retry(..., kind="news") -> ResearchResult[NewsDigest] | None`, `Citation`.
- Produces: `NewsHeadline(title: str, url: str, one_line_summary: str = "")`, `NewsDigest(headlines: list[NewsHeadline])` in `finwiz.schemas.perplexity`; `PerplexityAnalysisIntegration.is_available` true when `OPENROUTER_API_KEY` is set or the Perplexity tool constructs; `search_financial_news` signature unchanged.

The schema carries no `Field` constraints on purpose: it is sent as a strict `json_schema`, and a constraint keyword the provider rejects would fail every call. Lengths are clamped in Python (`_create_sonar_article` already truncates the summary to 2 000 chars; `SonarArticle` validates the title).

- [ ] **Step 1: Add the schema**

Append to `src/finwiz/schemas/perplexity.py`:

```python
class NewsHeadline(BaseModel):
    """One headline the research model found on the web."""

    title: str
    url: str
    one_line_summary: str = ""


class NewsDigest(BaseModel):
    """Minimal structured reply for the sentiment news search.

    No Field constraints: this model is sent as a strict ``json_schema`` and a
    rejected keyword would fail every call. Clamping happens in Python.
    """

    headlines: list[NewsHeadline] = []
```

(`BaseModel` is already imported in that module.)

- [ ] **Step 2: Rewrite the four HTTP-seam tests**

In `tests/unit/tools/test_perplexity_integration_wrapper.py`, add near the top (after the existing imports):

```python
from finwiz.infrastructure.research.openrouter_structured import Citation, ResearchResult
from finwiz.schemas.perplexity import NewsDigest, NewsHeadline

_RESEARCH = "finwiz.tools.perplexity_analysis_integration.research_with_retry"


def _digest(*headlines: tuple[str, str, str], citations: tuple[Citation, ...] = ()) -> ResearchResult[NewsDigest]:
    digest = NewsDigest(headlines=[NewsHeadline(title=t, url=u, one_line_summary=s) for t, u, s in headlines])
    return ResearchResult(data=digest, citations=citations, cost_usd=0.01, prompt_tokens=10, completion_tokens=5)
```

Replace `test_should_search_financial_news_successfully` (lines 81-119) with:

```python
    def test_should_search_financial_news_successfully(self, mocker):
        """Headlines from the digest become SonarArticles through the existing parser."""
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        research = mocker.patch(
            _RESEARCH,
            new=mocker.AsyncMock(return_value=_digest(("Apple Reports Strong Q4 Earnings", "https://example.com/apple-earnings", "Apple exceeded expectations with record revenue"))),
        )

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="AAPL earnings analysis", ticker="AAPL", asset_type="stock", analysis_type="sentiment", max_results=10))

        assert isinstance(result, SonarSearchResult)
        assert result.success is True
        assert result.ticker == "AAPL"
        assert result.asset_type == "stock"
        assert result.analysis_type == "sentiment"
        assert len(result.results) == 1
        assert result.results[0].title == "Apple Reports Strong Q4 Earnings"
        assert result.results[0].summary == "Apple exceeded expectations with record revenue"
        assert result.results[0].publisher == "Example"  # Extracted from example.com domain
        assert research.await_args.kwargs["kind"] == "news"
        assert research.await_args.kwargs["schema"] is NewsDigest

    def test_should_merge_citations_not_already_in_the_digest(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(
            _RESEARCH,
            new=mocker.AsyncMock(
                return_value=_digest(
                    ("Headline A", "https://a.example.com/x", "sa"),
                    citations=(Citation(url="https://a.example.com/x", title="dup", content="c"), Citation(url="https://b.example.com/y", title="Cited B", content="snippet b")),
                )
            ),
        )

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="q", ticker="AAPL", asset_type="stock", max_results=10))

        assert [a.url for a in result.results] == ["https://a.example.com/x", "https://b.example.com/y"]
        assert result.results[1].title == "Cited B"
        assert result.results[1].summary == "snippet b"

    def test_should_cap_articles_at_max_results(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(_RESEARCH, new=mocker.AsyncMock(return_value=_digest(*[(f"H{i}", f"https://example.com/{i}", "") for i in range(6)])))

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="q", ticker="AAPL", asset_type="stock", max_results=3))

        assert len(result.results) == 3

    def test_should_report_failure_when_research_returns_nothing(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(_RESEARCH, new=mocker.AsyncMock(return_value=None))

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="q", ticker="AAPL", asset_type="stock"))

        assert result.success is False
        assert result.results == []

    def test_should_report_failure_on_an_empty_digest(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(_RESEARCH, new=mocker.AsyncMock(return_value=_digest()))

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="q", ticker="AAPL", asset_type="stock"))

        assert result.success is False
        assert result.results == []
```

Replace `test_should_retry_on_rate_limit_error`, `test_should_handle_timeout_error`, `test_should_handle_connection_error` (lines 327-392) with:

```python
    def test_should_handle_timeout_error(self, mocker):
        """A raise from the research seam is classified and reported, never propagated."""
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(_RESEARCH, new=mocker.AsyncMock(side_effect=Exception("Request timeout")))

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="test query", ticker="AAPL", asset_type="stock"))

        assert result.success is False
        assert "timeout" in result.error_message.lower()

    def test_should_handle_connection_error(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"})
        mocker.patch(_RESEARCH, new=mocker.AsyncMock(side_effect=Exception("Connection failed")))

        integration = PerplexityAnalysisIntegration(self.config)
        result = asyncio.run(integration.search_financial_news(query="test query", ticker="AAPL", asset_type="stock"))

        assert result.success is False
        assert "connection" in result.error_message.lower()
```

Add to the init tests (after `test_should_initialize_without_api_key`):

```python
    def test_should_be_available_with_only_an_openrouter_key(self, mocker):
        mocker.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-openrouter-key"}, clear=True)

        integration = PerplexityAnalysisIntegration(self.config)

        assert integration.is_available is True
```

- [ ] **Step 3: Run to verify failure**

Run: `rtk uv run pytest tests/unit/tools/test_perplexity_integration_wrapper.py -v`
Expected: the new/rewritten tests FAIL (`AttributeError: ... has no attribute 'research_with_retry'`, `is_available` False with only the OpenRouter key); the parser/article/schema tests still PASS.

- [ ] **Step 4: Rewrite the integration wrapper's search path**

In `src/finwiz/tools/perplexity_analysis_integration.py`:

Module docstring (lines 1-7):

```python
"""
Financial news search for sentiment, technical and fundamental analysis.

Historically a wrapper over ``PerplexitySearchTool``; the class and module
names are kept because four tool modules import them. The search itself now
goes through ``research_with_retry`` (OpenRouter web plugin with a small
``NewsDigest`` schema, Perplexity as fallback) and the reply is fed through
the same citation parser as before, so ``SonarArticle`` / ``SonarSearchResult``
and their consumers are untouched.
"""
```

Imports: delete `from finwiz.config.endpoints import PERPLEXITY_SEARCH` and `cast` from the `typing` import (keep `Any, Literal`). Add:

```python
from finwiz.infrastructure.research.openrouter_structured import ResearchResult
from finwiz.infrastructure.resilience.research_retry import research_with_retry
```

and extend the `finwiz.schemas.perplexity` import with `NewsDigest`.

Module constants (after the `Literal` aliases):

```python
_NEWS_SYSTEM = (
    "Tu es un assistant de veille financière. Tu réponds UNIQUEMENT en JSON conforme au schéma fourni. "
    "Chaque titre doit provenir d'une page web réelle que tu as consultée, avec son URL exacte. "
    "Aucun titre inventé ; si tu ne trouves rien de fiable, renvoie une liste vide."
)
```

`__init__` (lines 51-72): replace the availability block with

```python
        # Available when the primary research provider has a key, or when the
        # Perplexity fallback tool could be constructed.
        self._api_available = bool(os.getenv("OPENROUTER_API_KEY")) or self.perplexity_tool is not None
        if not self._api_available:
            logger.warning("Neither OPENROUTER_API_KEY nor PERPLEXITY_API_KEY/PPLX_API_KEY found; news research will be disabled")
```

`search_financial_news` (lines 78-120): keep the unavailable early-return (its `error_message` string `"Perplexity API key not available"` is asserted by an existing test; leave it). Replace the `try:` body up to and including the `_parse_perplexity_response` line with:

```python
        try:
            enhanced_query = self._create_enhanced_query(query, ticker, asset_type, analysis_type)
            PerplexityOperationLogger.log_search_request(ticker, analysis_type, len(enhanced_query))
            search_filters = self._get_search_filters(analysis_type)

            research = await research_with_retry(
                prompt=self._news_prompt(enhanced_query, max_results, search_filters),
                schema=NewsDigest,
                system=_NEWS_SYSTEM,
                search_recency_filter="week",
                timeout=self.config.timeout_seconds,
                max_attempts=self.config.max_retries + 1,
                kind="news",
            )
            if research is None:
                raise PerplexityAPIError(None, "web research returned no result")

            citations = self._citations_from_research(research, max_results)
            if not citations:
                raise PerplexityAPIError(None, "web research returned no headlines")

            # Same envelope the parser always consumed, so _create_sonar_article
            # and everything downstream stay untouched.
            raw_response = ok({"citations": citations, "results": []})
            retry_count = 0
            articles = self._parse_perplexity_response(raw_response, analysis_type, ticker)
```

The rest of the method (performance metrics, the success `SonarSearchResult`, the `except` branch) is unchanged.

Add two helpers right after `_get_search_filters`:

```python
    def _news_prompt(self, enhanced_query: str, max_results: int, search_filters: dict[str, str]) -> str:
        preferred = search_filters.get("site", "").replace(",", ", ")
        wanted = max(1, min(max_results, 10))
        lines = [
            f"Recherche les actualités récentes pour : {enhanced_query}.",
            f"Retourne au plus {wanted} titres, chacun avec son URL source exacte et un résumé d'une phrase.",
        ]
        if preferred:
            lines.append(f"Privilégie ces sources : {preferred}.")
        return "\n".join(lines)

    @staticmethod
    def _citations_from_research(research: ResearchResult[NewsDigest], max_results: int) -> list[dict[str, Any]]:
        """Digest headlines first, then annotation citations not already named; URL-deduplicated."""
        seen: set[str] = set()
        out: list[dict[str, Any]] = []
        for headline in research.data.headlines:
            url = headline.url.strip()
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({"title": headline.title, "url": url, "snippet": headline.one_line_summary})
        for cite in research.citations:
            if not cite.url or cite.url in seen:
                continue
            seen.add(cite.url)
            out.append({"title": cite.title or cite.url, "url": cite.url, "snippet": cite.content})
        return out[: max(1, max_results)]
```

Delete `_execute_search_with_retry` entirely (lines 188-306, from its `async def` through `raise last_exception or Exception("Max retries exceeded for Perplexity search")`). Keep `_extract_ticker_from_query`, `_classify_error`, `_extract_http_status`, `_parse_perplexity_response`, `_create_sonar_article` and the rest.

- [ ] **Step 5: Run the wrapper tests, then the tools suite**

Run: `rtk uv run pytest tests/unit/tools/test_perplexity_integration_wrapper.py -v`
Expected: all PASS.

Run: `rtk uv run pytest tests/unit/tools tests/tools -q`
Expected: green. `tests/tools/test_perplexity_rate_limiting_validation.py` tests `PerplexityFallbackManager` only and is unaffected.

Run: `rtk uv run ruff check src/finwiz/tools/perplexity_analysis_integration.py`
Expected: clean. If ruff flags the now-unused `PERPLEXITY_SEARCH` per-file ignore in `pyproject.toml:173`, leave the row: it ignores `C901`/`PLR0915` for the module, not the import.

- [ ] **Step 6: Type-check and commit**

Run: `rtk uv run mypy src/finwiz/tools/perplexity_analysis_integration.py src/finwiz/schemas/perplexity.py`

```bash
rtk git add src/finwiz/schemas/perplexity.py src/finwiz/tools/perplexity_analysis_integration.py tests/unit/tools/test_perplexity_integration_wrapper.py
rtk git commit -m "feat(tools): sentiment news search through research_with_retry

NewsDigest (headlines: title/url/one_line_summary) replaces the Perplexity
/search call; digest headlines and url_citation annotations are merged,
URL-deduplicated and fed through the existing SonarArticle parser.
Availability: OpenRouter key or a constructible Perplexity tool.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 7: Config and docs

**Files:**
- Modify: `.env.example:19,51,156,291-292`
- Modify: `src/finwiz/config/features/definitions.py:148`
- Create: `docs/adr/ADR-012-openrouter-research-provider.md`
- Modify: `docs/adr/ADR-002-perplexity-research-integration.md:3`
- Modify: `CHANGELOG.md` (Unreleased)
- Modify: `CLAUDE.md:152-162`
- Modify: `docs/how-to/setup_environment.md:104,361`
- Modify: `docs/development/dependencies.md:33`

- [ ] **Step 1: `.env.example`**

Line 19 becomes:

```text
PPLX_API_KEY=your_perplexity_api_key_here         # Optional: Perplexity fallback when OpenRouter research fails
```

After line 51 (`OPENROUTER_API_KEY=...`), add:

```text
# Web-grounded research (SWOT/Porter, portfolio posture, fact-pack gap-fill,
# sentiment news) runs on OpenRouter with the web plugin; exact cost lands in
# output/run_summary.json under research_<kind>.
RESEARCH_MODEL=google/gemini-3.8-flash            # Raw OpenRouter id, no openrouter/ prefix
RESEARCH_CONCURRENCY=6                            # Max in-flight research calls, process-wide
RESEARCH_WEB_MAX_RESULTS=8                        # Exa results injected per call (~3k prompt tokens)
```

Line 156 becomes:

```text
FF_PERPLEXITY_RESEARCH=true                       # Web research for sentiment/gap-fill (circuit breaker); name kept for stability
```

After line 292 (`# PPLX_SEARCH_URL=...`), add:

```text
# RESEARCH_BASE_URL=https://openrouter.ai/api/v1
```

- [ ] **Step 2: Flag description**

`src/finwiz/config/features/definitions.py:148`:

```python
            description=("Web research (OpenRouter web plugin, Perplexity fallback) for sentiment news and equity fact-pack gap-fill; flag name kept for env stability"),
```

- [ ] **Step 3: ADR-012 and ADR-002**

`docs/adr/ADR-012-openrouter-research-provider.md`:

```markdown
# ADR-012: OpenRouter Web-Grounded Research Provider

- **Status:** Accepted
- **Date:** 2026-09-20
- **Deciders:** FinWiz Core Team
- **Supersedes:** the provider choice in ADR-002 (Perplexity Research Integration)

## Context

Four call sites asked Perplexity Sonar Pro for web-grounded structured answers:
SWOT and Porter per holding, the portfolio posture, the equity fact-pack gap-fill,
and the sentiment news search. At 67 holdings that is about 135 structured calls
plus up to 67 news searches per run, priced at $3 / $15 per million tokens plus
$5 per thousand searches, roughly $3.5 per run. None of it appeared in
`output/run_summary.json`: the cost tracker only sees CrewAI kickoffs.

Everything else in FinWiz already runs on `openrouter/google/gemini-3.8-flash`.
OpenRouter exposes web search for that model through its `web` plugin and returns
the exact cost of each request in `usage.cost`. A live spike on 2026-09-20
confirmed that the plugin and a strict `json_schema` response format work in the
same request, that the reply validates against `SwotAnalysis` unchanged, that
`url_citation` annotations are returned, and that a SWOT-size call costs about
$0.017.

## Decision

- `infrastructure/research/openrouter_structured.py` makes one `httpx` POST to
  OpenRouter with `plugins: [{"id": "web", "engine": "exa", "max_results": 8}]`
  and `response_format: json_schema` (strict), returning the validated model,
  the deduplicated citations and `usage.cost`.
- `infrastructure/resilience/research_retry.py` wraps it with the same retry,
  backoff and process-wide throttle shape as `perplexity_retry.py`, records the
  exact cost under `research_<kind>` in the run cost summary, and falls back to
  one Perplexity attempt when a `PPLX_API_KEY` / `PERPLEXITY_API_KEY` is set.
- All four call sites use `research_with_retry`. The Perplexity client stays as
  the fallback; there is no provider switch.
- Engine: Exa. Native Google grounding ($0.014 per search, no domain filter) and
  the Perplexity engine were rejected on cost.
- CrewAI `LLM` routing was rejected: it hides `usage.cost` and the citations and
  adds an agent stack to a single API call.

## Consequences

### Positive

- Research cost drops from about $3.5 to about $2.3 per run and becomes visible
  in `run_summary.json` and the report's cost section.
- One provider and one key for every LLM call in a default setup; Perplexity
  becomes optional.
- Citations are available to callers for future rendering.

### Negative

- Exa injects about 3 000 prompt tokens per call; `RESEARCH_WEB_MAX_RESULTS`
  trades grounding breadth for cost.
- The Exa engine has no recency parameter on OpenRouter; the window is expressed
  in the prompt, which is weaker than Perplexity's `search_recency_filter`.

### Risks

- OpenRouter plugin or annotation contract changes break the client; the unit
  tests pin the request body and the response parsing, and one integration test
  (skipped without a key) exercises the live contract.
- The strict `json_schema` mode may reject constraint keywords for some models;
  `NewsDigest` carries none for that reason, and the strategic schemas were
  verified live.

## References

- `src/finwiz/infrastructure/research/openrouter_structured.py`
- `src/finwiz/infrastructure/resilience/research_retry.py`
- `docs/superpowers/specs/2026-09-20-openrouter-research-provider-design.md`
- ADR-002 (superseded for the provider choice), ADR-001 (OpenRouter as LLM provider)
```

`docs/adr/ADR-002-perplexity-research-integration.md:3`:

```markdown
- **Status:** Accepted; provider choice superseded by ADR-012 (2026-09-20). Perplexity remains the fallback provider.
```

- [ ] **Step 4: CHANGELOG**

Under `## [Unreleased]`, add a `### Added` section above `### Changed` (or extend it if the cache PR already created one):

```markdown
### Added

- OpenRouter web-grounded research provider. SWOT/Porter, portfolio posture,
  equity fact-pack gap-fill and sentiment news now run on
  `google/gemini-3.8-flash` through OpenRouter's `web` plugin (Exa, 8 results)
  with a strict `json_schema` response, via `research_with_retry`
  (`infrastructure/resilience/research_retry.py`). Each call's exact
  `usage.cost` is recorded under `research_swot`, `research_porter`,
  `research_posture`, `research_factpack` and `research_news` in
  `output/run_summary.json`, where Perplexity spend was invisible before.
  Perplexity is kept as a one-attempt fallback when a PPLX key is set. New env:
  `RESEARCH_MODEL`, `RESEARCH_CONCURRENCY`, `RESEARCH_WEB_MAX_RESULTS`,
  `RESEARCH_BASE_URL`. See ADR-012.

### Changed

- Fact-pack provenance tag `perplexity.gap_fill` is now `research.gap_fill`
  and renders as "recherche web". `PPLX_API_KEY` is optional.
```

- [ ] **Step 5: Root `CLAUDE.md` env block (lines 152-162)**

Replace from `# Optional: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, ...` through `(measured at 6 of 67 holdings), not a dependency.` with:

```text
# Optional: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, ALPHA_VANTAGE_API_KEY, etc.
# Web-grounded research (SWOT/Porter, posture, fact-pack gap-fill, sentiment
#   news) runs on OpenRouter's web plugin via
#   infrastructure/resilience/research_retry.py (RESEARCH_MODEL,
#   RESEARCH_CONCURRENCY, RESEARCH_WEB_MAX_RESULTS). Exact cost is recorded
#   under research_<kind> in output/run_summary.json. PERPLEXITY_API_KEY /
#   PPLX_API_KEY only enable a one-attempt Perplexity fallback (ADR-012).
# Feature flags are all FF_-prefixed, e.g. FF_PERPLEXITY_RESEARCH
#   (full registry: config/features/definitions.py)
# FF_PERPLEXITY_RESEARCH=false makes fact packs fully deterministic: they are
#   built entirely from structured sources (yfinance, curated expense-ratio
#   table), with no research call at all. The flag name predates the provider
#   swap and is kept for env stability. stages/fact_pack.py calls
#   analysis/fact_pack/composer.py's compose_fact_pack(), which consults this
#   flag itself, narrowly, in the equity path only (analysis/fact_pack/
#   sources/research_source.py) — funds and crypto never call research
#   regardless of the flag. Fact packs never fail a holding for want of
#   research either way — it is a gap-filler for equity recent_events when
#   neither SEC filings nor allowlisted wire news covered the company
#   (measured at 6 of 67 holdings), not a dependency.
```

- [ ] **Step 6: How-to and dependencies docs**

`docs/how-to/setup_environment.md:104`: `PPLX_API_KEY=your_perplexity_api_key_here` → `PPLX_API_KEY=your_perplexity_api_key_here   # optional fallback, see ADR-012`.

`docs/how-to/setup_environment.md:361`: `| `PPLX_API_KEY`          | No       | Perplexity search        |` → `| `PPLX_API_KEY`          | No       | Perplexity fallback for web research (primary is OpenRouter, ADR-012) |`.

In the Feature Flags table of the same file, `FF_PERPLEXITY_RESEARCH` description → `Web research for sentiment / gap-fill (circuit breaker)`.

`docs/development/dependencies.md:33`: `Perplexity search` in the tool list → `Perplexity search (fallback only since ADR-012)`.

- [ ] **Step 7: Lint, full check, commit**

Run: `rtk make check`
Expected: green (lint, tests, unittest.mock check, docs validation, complexity, dead code).

```bash
rtk git add .env.example src/finwiz/config/features/definitions.py docs/adr CHANGELOG.md CLAUDE.md docs/how-to/setup_environment.md docs/development/dependencies.md
rtk git commit -m "docs: ADR-012 OpenRouter research provider, env and changelog

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB"
```

---

### Task 8: Integration test, live verification, PR

**Files:**
- Create: `tests/integration/test_openrouter_research_live.py`

- [ ] **Step 1: Integration test (skipped without a key)**

```python
"""One live web-grounded SWOT call. Costs about $0.02; skipped without a key."""

from __future__ import annotations

import os

import pytest

from finwiz.analysis.strategic_research import SYSTEM_FR, _swot_prompt
from finwiz.infrastructure.research.openrouter_structured import openrouter_structured
from finwiz.schemas.hybrid_analysis.strategic import SwotAnalysis

pytestmark = [pytest.mark.integration, pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set")]


async def test_live_swot_validates_and_reports_cost():
    result = await openrouter_structured(
        prompt=_swot_prompt("SAN.PA", "Healthcare", "Pharmaceuticals", "Sanofi", "20 septembre 2026"),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        timeout=90.0,
    )

    assert result is not None
    assert isinstance(result.data, SwotAnalysis)
    assert result.data.strengths
    assert result.cost_usd is not None and result.cost_usd > 0
    assert result.citations
```

Run: `rtk uv run pytest tests/integration/test_openrouter_research_live.py -m integration -v`
Expected: PASS with the key in `.env` (one call, ~$0.02). Without it: SKIPPED. Do not print the key or the response body.

Note: the `tests/conftest.py` isolation fixture clears `OPENROUTER_API_KEY`; check whether `tests/integration/conftest.py` re-enables env for integration tests (it is 7.6 K, read it). If the key is cleared before the skipif is evaluated, the marker still sees the process env at collection time, but the call inside the test will raise `ValueError`. In that case the test must read the key before isolation: add `api_key=os.environ.get("OPENROUTER_API_KEY")` is not enough; instead add a module-level `_KEY = os.getenv("OPENROUTER_API_KEY")` and pass `api_key=_KEY`.

- [ ] **Step 2: Full gates**

```bash
rtk make check
rtk uv run mypy src/finwiz
uvx vulture src/finwiz --min-confidence 80
```

Expected: all clean. Vulture: the rename in Task 5 can unmask a warning elsewhere; fix whatever it names.

- [ ] **Step 3: Three-holding pipeline run, both configurations**

With `OPENROUTER_API_KEY` set (normal `.env`):

```bash
PORTFOLIO_STOCK_CSV=<stock.csv> PORTFOLIO_ETF_CSV=<etf.csv> PORTFOLIO_CRYPTO_CSV=<crypto.csv> rtk uv run kickoff; echo "exit=$?"
rtk uv run python -c "import json;s=json.load(open('output/run_summary.json'));print({k:v for k,v in s.get('cost',s).get('per_crew',{}).items() if k.startswith('research_')})"
```

Expected: exit 0; the posture page renders; SWOT and Porter present for all three holdings; `research_swot`, `research_porter`, `research_posture` listed with non-zero cost and `cost_known: true`. If the summary key path differs, open `output/run_summary.json` and locate `per_crew`.

Fallback path. A full run with `OPENROUTER_API_KEY` empty cannot complete, because the crew LLM is `openrouter/...` too, so exercise the research fallback in isolation with the key hidden for one command only (do **not** edit `.env`):

```bash
OPENROUTER_API_KEY= rtk uv run python -c "
import asyncio
from finwiz.analysis.strategic_research import gather_strategic_analysis_sync
r = gather_strategic_analysis_sync(ticker='SAN.PA', sector='Healthcare', industry='Pharmaceuticals', description='Sanofi')
print('swot' if r and r.swot else 'no swot', 'porter' if r and r.five_forces else 'no porter')
"
```

Expected with a PPLX key in `.env`: `swot porter` and a log line `answered by the Perplexity fallback`. Without a PPLX key: `no swot no porter` and a warning that OpenRouter is not configured. Record which case ran in the PR body.

- [ ] **Step 4: Push and open the PR**

```bash
rtk git push -u origin feat/openrouter-research-provider
rtk gh pr create --title "feat(research): OpenRouter web-grounded research replaces Perplexity Sonar" --body "$(cat <<'EOF'
## Summary

- New `infrastructure/research/openrouter_structured.py`: one httpx POST with the `web` plugin (Exa, 8 results) and strict `json_schema`; returns data, deduplicated citations and exact `usage.cost`.
- New `infrastructure/resilience/research_retry.py`: retry/backoff, process-wide throttle (`RESEARCH_CONCURRENCY`, default 6), cost recorded under `research_<kind>`, one Perplexity attempt as fallback when a PPLX key is set.
- Call sites: SWOT/Porter/posture (`strategic_research.py`), fact-pack gap-fill (`perplexity_source.py` → `research_source.py`, provenance `research.gap_fill`), sentiment news (`NewsDigest` schema, fed through the existing `SonarArticle` parser).
- `record_usage(..., cost_usd=)` records exact provider cost.
- Docs: ADR-012 (supersedes the provider choice in ADR-002), CHANGELOG, root CLAUDE.md, `.env.example`, setup how-to, dependencies.

Spec: `docs/superpowers/specs/2026-09-20-openrouter-research-provider-design.md`.

## Cost

Sonar Pro ≈ $3.5/run, invisible. OpenRouter ≈ $2.3/run for the 135 structured calls, visible in `run_summary.json`.

## Test plan

- [ ] `make check`, `mypy`, `vulture` clean
- [ ] Three-CSV run: posture renders, SWOT/Porter for 3 holdings, `research_*` crews with non-zero cost in `run_summary.json`
- [ ] Fallback path exercised with the OpenRouter key hidden (result recorded above)
- [ ] `tests/integration/test_openrouter_research_live.py` passes with a key

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01VsJfUDq8AC2adLMMWRZuFB
EOF
)"
```

- [ ] **Step 5: CI, merge, sync**

```bash
rtk gh pr checks --watch
rtk gh pr merge --merge --delete-branch
rtk git checkout main && rtk git pull
```

Expected: merge commit on `main`, branch deleted.
