# Central Tools Migration — Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship crewai-custom-tools v0.4.0 (rate limiter, envelope parser, batch mode, reconciled Perplexity + Yahoo tools), bump epic_news to it, and swap finwiz's five Yahoo tools + two Perplexity modules to the central package.

**Architecture:** Three repos, strict order: (1) upstream all features into `/Users/fjacquet/Projects/crewai_custom_tools`, tag v0.4.0, push; (2) bump `/Users/fjacquet/Projects/crews/epic_news` pin and fix its tests; (3) add the git dependency to `/Users/fjacquet/Projects/finwiz`, rewrite import sites, adapt programmatic callers to the `ToolResult` envelope, delete the local tool files. Spec: `docs/superpowers/specs/2026-07-14-centralized-tools-design.md`.

**Tech Stack:** Python (3.11+ central, 3.13 finwiz), uv, pytest + pytest-mock (unittest.mock is BANNED in both repos), CrewAI BaseTool, requests/httpx, yfinance.

## Global Constraints

- **Envelope contract:** every central tool `_run` returns the JSON string from `ok(data)` / `err(msg)` (`crewai_custom_tools.core.results`). Programmatic callers parse with `parse_tool_result()`. Never return bare dicts from central tools.
- **Additive-first:** epic_news at v0.3.1 semantics must not silently change. The ONLY sanctioned Wave-1 breaks: `PerplexitySearchTool` signature and its fail-fast construction. Everything else is additive (new optional params, new exports).
- **Central supports Python >=3.11:** no PEP 695 syntax (`def f[T](...)`), use `typing.TypeVar`.
- **crewai floor in central:** bump `crewai>=0.100.0` → `crewai>=1.15.1` (both consumers already require >=1.15.1).
- **finwiz rules:** `make check` green before every finwiz commit; ruff line length 180; new files ≤300 lines (pre-commit hook); no `unittest.mock` anywhere.
- **Central test conventions:** offline, mocked, seconds-fast. New tests must not hit the network.
- **Rate limiting must not slow tests:** both repos' test setup sets `CREWAI_TOOLS_RATE_LIMIT_DISABLED=1` (Tasks 3, 13).
- **Every commit** ends its message with:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Central repo work happens on branch `wave1-finwiz-parity`, merged to `main` before tagging (Task 10). finwiz work happens on branch `spec/centralized-tools` (already checked out).

---

## Part A — crewai_custom_tools (Tasks 1–10)

Working directory for all Part A tasks: `/Users/fjacquet/Projects/crewai_custom_tools`

Before Task 1: `git checkout -b wave1-finwiz-parity`

### Task 1: `parse_tool_result()` + `ToolResultError`

**Files:**

- Modify: `src/crewai_custom_tools/core/results.py` (append after `err()`)
- Test: `tests/test_results.py` (append)

**Interfaces:**

- Consumes: existing `ok()`, `err()` in the same module.
- Produces: `parse_tool_result(raw: str) -> Any` (returns the envelope's `data`; raises `ToolResultError` on `success=False` or malformed input) and `class ToolResultError(RuntimeError)` with `.data` attribute. Tasks 11–15 and all finwiz callers depend on these exact names.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_results.py`)

```python
import pytest

from crewai_custom_tools.core.results import ToolResultError, err, ok, parse_tool_result


def test_parse_tool_result_returns_data_on_success():
    assert parse_tool_result(ok({"x": 1})) == {"x": 1}


def test_parse_tool_result_none_data_on_bare_ok():
    assert parse_tool_result(ok()) is None


def test_parse_tool_result_raises_on_error_envelope():
    with pytest.raises(ToolResultError, match="boom"):
        parse_tool_result(err("boom"))


def test_parse_tool_result_error_carries_partial_data():
    with pytest.raises(ToolResultError) as exc_info:
        parse_tool_result(err("partial", data={"kept": True}))
    assert exc_info.value.data == {"kept": True}


def test_parse_tool_result_raises_on_invalid_json():
    with pytest.raises(ToolResultError, match="envelope"):
        parse_tool_result("not json at all")


def test_parse_tool_result_raises_on_non_envelope_json():
    with pytest.raises(ToolResultError, match="envelope"):
        parse_tool_result('{"answer": 42}')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_results.py -v`
Expected: FAIL — `ImportError: cannot import name 'ToolResultError'`

- [ ] **Step 3: Implement** (append to `src/crewai_custom_tools/core/results.py`)

```python
class ToolResultError(RuntimeError):
    """Raised by :func:`parse_tool_result` when an envelope reports failure."""

    def __init__(self, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.data = data


def parse_tool_result(raw: str) -> Any:
    """Parse a canonical envelope string and return its ``data`` payload.

    Raises:
        ToolResultError: if ``raw`` is not a valid envelope, or the envelope
            has ``success=False`` (the error message and any partial ``data``
            are carried on the exception).
    """
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ToolResultError(f"Not a valid tool envelope: {exc}") from exc
    if not isinstance(payload, dict) or "success" not in payload:
        raise ToolResultError("Not a valid tool envelope: missing 'success' key")
    if not payload["success"]:
        raise ToolResultError(payload.get("error") or "Tool reported failure", data=payload.get("data"))
    return payload.get("data")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_results.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/core/results.py tests/test_results.py
git commit -m "feat(core): add parse_tool_result and ToolResultError for envelope consumers

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 2: `require_api_key()` fail-fast helper

**Files:**

- Create: `src/crewai_custom_tools/core/keys.py`
- Test: `tests/test_keys.py`

**Interfaces:**

- Produces: `require_api_key(*env_vars: str, tool_name: str) -> str` — returns the first non-empty env var value, raises `ValueError` naming the tool and variables otherwise. Task 5 and future waves use it in `model_post_init` so key-less construction raises immediately (finwiz's `_safe_init` skip pattern depends on `ValueError` here).

- [ ] **Step 1: Write the failing tests** (create `tests/test_keys.py`)

```python
import pytest

from crewai_custom_tools.core.keys import require_api_key


def test_returns_first_set_variable(monkeypatch):
    monkeypatch.delenv("PRIMARY_KEY", raising=False)
    monkeypatch.setenv("FALLBACK_KEY", "sk-fallback")
    assert require_api_key("PRIMARY_KEY", "FALLBACK_KEY", tool_name="DemoTool") == "sk-fallback"


def test_primary_wins_when_both_set(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "sk-primary")
    monkeypatch.setenv("FALLBACK_KEY", "sk-fallback")
    assert require_api_key("PRIMARY_KEY", "FALLBACK_KEY", tool_name="DemoTool") == "sk-primary"


def test_raises_value_error_when_all_missing(monkeypatch):
    monkeypatch.delenv("PRIMARY_KEY", raising=False)
    monkeypatch.delenv("FALLBACK_KEY", raising=False)
    with pytest.raises(ValueError, match="DemoTool requires PRIMARY_KEY or FALLBACK_KEY"):
        require_api_key("PRIMARY_KEY", "FALLBACK_KEY", tool_name="DemoTool")


def test_empty_string_counts_as_missing(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "")
    with pytest.raises(ValueError):
        require_api_key("PRIMARY_KEY", tool_name="DemoTool")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_keys.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crewai_custom_tools.core.keys'`

- [ ] **Step 3: Implement** (create `src/crewai_custom_tools/core/keys.py`)

```python
"""Fail-fast API key validation for tool classes.

Tools call :func:`require_api_key` in ``model_post_init`` so a missing key
raises ``ValueError`` at instantiation — not at first API call. Consumers that
want to skip key-less tools gracefully catch ``ValueError`` at construction.
"""

import os


def require_api_key(*env_vars: str, tool_name: str) -> str:
    """Return the first non-empty value among ``env_vars`` or raise ``ValueError``."""
    for var in env_vars:
        value = os.getenv(var)
        if value:
            return value
    names = " or ".join(env_vars)
    raise ValueError(f"{tool_name} requires {names} environment variable")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_keys.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/core/keys.py tests/test_keys.py
git commit -m "feat(core): add require_api_key fail-fast helper

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 3: Provider-keyed synchronous rate limiter

**Files:**

- Create: `src/crewai_custom_tools/core/rate_limiter.py`
- Test: `tests/test_rate_limiter.py`
- Create: `tests/conftest.py` (rate-limit kill switch for the whole central suite)

**Interfaces:**

- Produces: `RateLimit(requests_per_minute: int, burst: int = 5)` frozen dataclass; `DEFAULT_RATE_LIMITS: dict[str, RateLimit]`; `get_rate_limiter() -> RateLimiterRegistry` (process-wide singleton) with `.acquire(provider: str) -> None` (blocks until a token is available; no-op for unknown providers or when `CREWAI_TOOLS_RATE_LIMIT_DISABLED` is `1`/`true`); `reset_rate_limiter() -> None` for tests. Task 4 calls `get_rate_limiter().acquire(provider)` inside `api_tool`.
- Provider keys are the exact strings tools already pass to `@api_tool`: `"YahooFinance"`, `"Perplexity"`, `"AlphaVantage"`, `"TwelveData"`, `"ChartImg"`, `"CoinMarketCap"`, `"Kraken"`, `"SECEdgar"`, `"FRED"`, `"FearGreed"`. Limits ported from finwiz `infrastructure/resilience/rate_limiter_config.py`.

- [ ] **Step 1: Write the failing tests** (create `tests/test_rate_limiter.py`)

```python
import time

import pytest

from crewai_custom_tools.core.rate_limiter import (
    DEFAULT_RATE_LIMITS,
    RateLimit,
    RateLimiterRegistry,
    get_rate_limiter,
    reset_rate_limiter,
)


@pytest.fixture(autouse=True)
def _enable_rate_limiting(monkeypatch):
    # The suite-wide conftest disables limiting; re-enable it for these tests.
    monkeypatch.delenv("CREWAI_TOOLS_RATE_LIMIT_DISABLED", raising=False)
    reset_rate_limiter()
    yield
    reset_rate_limiter()


def test_burst_capacity_is_immediate():
    registry = RateLimiterRegistry({"Demo": RateLimit(requests_per_minute=6000, burst=3)})
    start = time.monotonic()
    for _ in range(3):
        registry.acquire("Demo")
    assert time.monotonic() - start < 0.05


def test_acquire_blocks_after_burst_exhausted():
    # 6000/min = 100 tokens/sec -> 4th call waits ~10ms
    registry = RateLimiterRegistry({"Demo": RateLimit(requests_per_minute=6000, burst=3)})
    for _ in range(3):
        registry.acquire("Demo")
    start = time.monotonic()
    registry.acquire("Demo")
    assert time.monotonic() - start >= 0.005


def test_unknown_provider_is_noop():
    registry = RateLimiterRegistry({})
    start = time.monotonic()
    for _ in range(100):
        registry.acquire("NeverConfigured")
    assert time.monotonic() - start < 0.05


def test_kill_switch_disables_limiting(monkeypatch):
    monkeypatch.setenv("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "1")
    registry = RateLimiterRegistry({"Demo": RateLimit(requests_per_minute=1, burst=1)})
    start = time.monotonic()
    for _ in range(5):
        registry.acquire("Demo")
    assert time.monotonic() - start < 0.05


def test_premium_override_via_env(monkeypatch):
    monkeypatch.setenv("ALPHA_VANTAGE_PREMIUM", "true")
    reset_rate_limiter()
    registry = get_rate_limiter()
    assert registry.limit_for("AlphaVantage") == RateLimit(requests_per_minute=75, burst=10)


def test_default_limits_cover_known_providers():
    for provider in ("YahooFinance", "Perplexity", "AlphaVantage", "TwelveData"):
        assert provider in DEFAULT_RATE_LIMITS


def test_get_rate_limiter_is_singleton():
    assert get_rate_limiter() is get_rate_limiter()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_rate_limiter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crewai_custom_tools.core.rate_limiter'`

- [ ] **Step 3: Implement** (create `src/crewai_custom_tools/core/rate_limiter.py`)

```python
"""Provider-keyed synchronous rate limiting for API-backed tools.

Ported from finwiz's async aiolimiter-based limiter and reduced to what the
sync ``@api_tool`` wrapper needs: a token bucket per provider, blocking
``acquire``. Providers are the same strings tools pass to ``@api_tool``.
Set ``CREWAI_TOOLS_RATE_LIMIT_DISABLED=1`` to bypass entirely (tests, CI).
"""

import os
import threading
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimit:
    """Token-bucket parameters for one provider."""

    requests_per_minute: int
    burst: int = 5


# Values ported from finwiz infrastructure/resilience/rate_limiter_config.py
DEFAULT_RATE_LIMITS: dict[str, RateLimit] = {
    "AlphaVantage": RateLimit(requests_per_minute=5, burst=2),
    "YahooFinance": RateLimit(requests_per_minute=600, burst=20),
    "TwelveData": RateLimit(requests_per_minute=8, burst=3),
    "ChartImg": RateLimit(requests_per_minute=30, burst=5),
    "CoinMarketCap": RateLimit(requests_per_minute=30, burst=5),
    "Kraken": RateLimit(requests_per_minute=60, burst=10),
    "SECEdgar": RateLimit(requests_per_minute=10, burst=3),
    "Perplexity": RateLimit(requests_per_minute=30, burst=5),
    "FRED": RateLimit(requests_per_minute=120, burst=20),
    "FearGreed": RateLimit(requests_per_minute=10, burst=2),
}

# env var -> (provider, premium limit); mirrors finwiz's premium-tier switches
_PREMIUM_OVERRIDES: dict[str, tuple[str, RateLimit]] = {
    "ALPHA_VANTAGE_PREMIUM": ("AlphaVantage", RateLimit(requests_per_minute=75, burst=10)),
    "TWELVE_DATA_PREMIUM": ("TwelveData", RateLimit(requests_per_minute=800, burst=50)),
}


class _TokenBucket:
    def __init__(self, limit: RateLimit) -> None:
        self._capacity = float(limit.burst)
        self._tokens = float(limit.burst)
        self._refill_per_sec = limit.requests_per_minute / 60.0
        self._updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._refill_per_sec)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._refill_per_sec
            time.sleep(wait)


class RateLimiterRegistry:
    """Per-provider token buckets. Unknown providers pass through unthrottled."""

    def __init__(self, limits: dict[str, RateLimit] | None = None) -> None:
        base = dict(DEFAULT_RATE_LIMITS if limits is None else limits)
        for env_var, (provider, premium) in _PREMIUM_OVERRIDES.items():
            if provider in base and os.getenv(env_var, "false").lower() == "true":
                base[provider] = premium
        self._limits = base
        self._buckets = {provider: _TokenBucket(limit) for provider, limit in base.items()}

    def limit_for(self, provider: str) -> RateLimit | None:
        return self._limits.get(provider)

    def acquire(self, provider: str) -> None:
        if os.getenv("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "").lower() in ("1", "true"):
            return
        bucket = self._buckets.get(provider)
        if bucket is not None:
            bucket.acquire()


_registry: RateLimiterRegistry | None = None
_registry_lock = threading.Lock()


def get_rate_limiter() -> RateLimiterRegistry:
    """Return the process-wide registry, creating it on first use."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = RateLimiterRegistry()
    return _registry


def reset_rate_limiter() -> None:
    """Discard the singleton (tests only — premium env vars are read at creation)."""
    global _registry
    _registry = None
```

- [ ] **Step 4: Create the suite-wide kill switch** (create `tests/conftest.py`)

```python
"""Shared test configuration for the central tools suite."""

import os

# Rate limiting is exercised explicitly in test_rate_limiter.py; everywhere
# else it must never slow a test down or make timing flaky.
os.environ.setdefault("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "1")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_rate_limiter.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/crewai_custom_tools/core/rate_limiter.py tests/test_rate_limiter.py tests/conftest.py
git commit -m "feat(core): provider-keyed sync token-bucket rate limiter (ported from finwiz)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 4: Wire the rate limiter into `@api_tool`

**Files:**

- Modify: `src/crewai_custom_tools/core/decorators.py`
- Test: `tests/test_decorators.py` (append)

**Interfaces:**

- Consumes: `get_rate_limiter()` from Task 3.
- Produces: unchanged `api_tool(provider, endpoint, timeout=30.0)` signature; the wrapper now calls `get_rate_limiter().acquire(provider)` before the initial call AND before the 429 retry. All existing tool behavior otherwise unchanged.

- [ ] **Step 1: Write the failing test** (append to `tests/test_decorators.py`)

```python
def test_api_tool_acquires_rate_limit_token(mocker):
    from crewai_custom_tools.core import decorators

    registry = mocker.Mock()
    mocker.patch.object(decorators, "get_rate_limiter", return_value=registry)

    @decorators.api_tool(provider="DemoProvider", endpoint="DemoEndpoint")
    def sample() -> str:
        return "done"

    assert sample() == "done"
    registry.acquire.assert_called_once_with("DemoProvider")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest tests/test_decorators.py::test_api_tool_acquires_rate_limit_token -v`
Expected: FAIL — `AttributeError: module ... has no attribute 'get_rate_limiter'`

- [ ] **Step 3: Implement.** In `src/crewai_custom_tools/core/decorators.py`, add the import after `from crewai_custom_tools.core.results import err`:

```python
from crewai_custom_tools.core.rate_limiter import get_rate_limiter
```

Inside `wrapper`, change the try block's first line and the retry block:

```python
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                get_rate_limiter().acquire(provider)
                return _run_with_timeout(func, args, kwargs, timeout)
```

and in the 429 branch, before the retry call:

```python
                    sleep(2.0)
                    try:
                        get_rate_limiter().acquire(provider)
                        return _run_with_timeout(func, args, kwargs, timeout)
```

- [ ] **Step 4: Run the full central suite** (existing decorator tests must still pass; conftest kill switch keeps everything fast)

Run: `uv run --extra dev pytest tests/ -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/core/decorators.py tests/test_decorators.py
git commit -m "feat(core): api_tool acquires a rate-limit token before each attempt

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 5: Reconcile `PerplexitySearchTool` (sanctioned break)

**Files:**

- Modify: `src/crewai_custom_tools/tools/web/perplexity.py` (replace file content)
- Test: `tests/test_perplexity.py` (replace the `PerplexitySearchTool` tests; keep any `PerplexityStructuredTool` tests untouched)

**Interfaces:**

- Consumes: `api_tool` (Task 4), `ok`/`err`, `require_api_key` (Task 2).
- Produces: `PerplexitySearchTool` with `_run(self, query: str, model: str = "sonar-pro", top_k: int | None = 5, search_recency: str | None = None, search_domain_filter: list[str] | None = None) -> str`. Construction raises `ValueError` when neither `PERPLEXITY_API_KEY` nor `PPLX_API_KEY` is set. Success envelope `data`: `{"answer": str, "citations": list, "source": "perplexity"}` (UNCHANGED from v0.3.1 — downstream consumers keep working). The old `focus`/`recency` params are REMOVED (the spec's sanctioned break). Fixes finwiz's silent bug: recency is sent as `search_recency_filter` (the API ignores `search_recency`).

- [ ] **Step 1: Write the failing tests.** In `tests/test_perplexity.py`, delete existing tests that exercise `focus`/`recency` on `PerplexitySearchTool` and add:

```python
import pytest

from crewai_custom_tools import PerplexitySearchTool
from crewai_custom_tools.core.results import ToolResultError, parse_tool_result


@pytest.fixture()
def pplx_key(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")


def _mock_response(mocker, payload):
    response = mocker.Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_construction_fails_fast_without_key(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    with pytest.raises(ValueError, match="PERPLEXITY_API_KEY or PPLX_API_KEY"):
        PerplexitySearchTool()


def test_legacy_pplx_key_still_works(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setenv("PPLX_API_KEY", "legacy-key")
    assert PerplexitySearchTool() is not None


def test_run_returns_answer_envelope(pplx_key, mocker):
    post = mocker.patch(
        "crewai_custom_tools.tools.web.perplexity.requests.post",
        return_value=_mock_response(
            mocker,
            {
                "choices": [{"message": {"content": "The answer."}}],
                "citations": ["https://example.com"],
            },
        ),
    )
    data = parse_tool_result(PerplexitySearchTool()._run(query="test question"))
    assert data == {"answer": "The answer.", "citations": ["https://example.com"], "source": "perplexity"}
    payload = post.call_args.kwargs["json"]
    assert payload["model"] == "sonar-pro"
    assert payload["top_k"] == 5
    assert "search_recency_filter" not in payload


def test_recency_maps_to_search_recency_filter(pplx_key, mocker):
    post = mocker.patch(
        "crewai_custom_tools.tools.web.perplexity.requests.post",
        return_value=_mock_response(mocker, {"choices": [{"message": {"content": "x"}}], "citations": []}),
    )
    PerplexitySearchTool()._run(query="q", search_recency="week", search_domain_filter=["reddit.com"])
    payload = post.call_args.kwargs["json"]
    assert payload["search_recency_filter"] == "week"
    assert payload["search_domain_filter"] == ["reddit.com"]


def test_missing_answer_yields_error_envelope(pplx_key, mocker):
    mocker.patch(
        "crewai_custom_tools.tools.web.perplexity.requests.post",
        return_value=_mock_response(mocker, {"choices": []}),
    )
    with pytest.raises(ToolResultError, match="no answer"):
        parse_tool_result(PerplexitySearchTool()._run(query="q"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_perplexity.py -v`
Expected: new tests FAIL (`ValueError` not raised; `TypeError: _run() got an unexpected keyword argument 'search_recency'`)

- [ ] **Step 3: Replace `src/crewai_custom_tools/tools/web/perplexity.py`**

```python
"""Perplexity AI-powered search tool."""

import logging
import os
from typing import Any

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_custom_tools.core.decorators import api_tool
from crewai_custom_tools.core.keys import require_api_key
from crewai_custom_tools.core.results import err, ok

logger = logging.getLogger(__name__)

_PERPLEXITY_URL = os.getenv("PPLX_BASE_URL", "https://api.perplexity.ai/chat/completions")


class PerplexitySearchInput(BaseModel):
    """Input schema for Perplexity Search Tool."""

    query: str = Field(..., description="Natural language query to research with Perplexity Sonar.")
    model: str = Field("sonar-pro", description="Perplexity model to use (e.g., sonar-pro).")
    top_k: int | None = Field(5, description="Maximum number of web results to retrieve (1-10 typical).")
    search_recency: str | None = Field(None, description="Recency filter: 'hour', 'day', 'week', 'month', or 'year'. Empty for default.")
    search_domain_filter: list[str] | None = Field(None, description="Restrict the search to these domains, e.g. ['reddit.com'].")


class PerplexitySearchTool(BaseTool):
    """AI-powered web search with synthesis and citations."""

    name: str = "perplexity_search"
    description: str = "AI-powered web search using Perplexity API. Returns synthesized answers with citations. Requires PERPLEXITY_API_KEY (or legacy PPLX_API_KEY)."
    args_schema: type[BaseModel] = PerplexitySearchInput

    def model_post_init(self, __context: Any) -> None:
        """Validate the API key at instantiation (fail-fast)."""
        super().model_post_init(__context)
        self._api_key = require_api_key("PERPLEXITY_API_KEY", "PPLX_API_KEY", tool_name=type(self).__name__)

    @api_tool(provider="Perplexity", endpoint="Search", timeout=45.0)
    def _run(
        self,
        query: str,
        model: str = "sonar-pro",
        top_k: int | None = 5,
        search_recency: str | None = None,
        search_domain_filter: list[str] | None = None,
    ) -> str:
        """Execute a Perplexity search and return a synthesized answer with citations."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": query}],
            "return_citations": True,
        }
        if top_k is not None:
            payload["top_k"] = top_k
        if search_recency:
            payload["search_recency_filter"] = search_recency
        if search_domain_filter:
            payload["search_domain_filter"] = search_domain_filter

        response = requests.post(
            _PERPLEXITY_URL,
            headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()

        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        answer = message.get("content")
        if not answer:
            return err("Perplexity returned no answer content")

        return ok({"answer": answer, "citations": data.get("citations", []), "source": "perplexity"})
```

- [ ] **Step 4: Run the full suite** (other tests may construct `PerplexitySearchTool` without a key — fix any such test by adding the `pplx_key`-style `monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")`)

Run: `uv run --extra dev pytest tests/ -q`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/web/perplexity.py tests/test_perplexity.py
git commit -m "feat(web)!: adopt finwiz PerplexitySearchTool signature, fail-fast key check

BREAKING CHANGE: focus/recency params replaced by model/top_k/search_recency/
search_domain_filter; construction now raises ValueError without an API key.
Fixes silent recency bug (search_recency_filter is now actually sent).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 6: Port the `perplexity_structured()` async function

**Files:**

- Modify: `src/crewai_custom_tools/tools/web/perplexity_structured.py` (append function; keep `PerplexityStructuredTool` untouched)
- Modify: `pyproject.toml` (add `pytest-asyncio` dev dep + asyncio mode)
- Test: `tests/test_perplexity_structured_fn.py`

**Interfaces:**

- Consumes: `require_api_key` (Task 2). Uses `httpx` (already a central dependency).
- Produces: `async def perplexity_structured(*, prompt: str, schema: type[T], system: str = ..., model: str = "sonar-pro", search_recency_filter: str | None = "month", timeout: float = 60.0, api_key: str | None = None) -> T | None` — identical signature and None-on-failure semantics as finwiz's `finwiz/tools/perplexity_structured.py`, so finwiz's `fact_pack_research.py` / `strategic_research.py` swap imports without other changes (Task 14).

- [ ] **Step 1: Add test tooling.** In `pyproject.toml` `[project.optional-dependencies] dev`, add:

```toml
    "pytest-asyncio>=0.25.0",
```

and add (new section at the end of the file):

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

Run: `uv lock && uv sync --extra dev`
Expected: pytest-asyncio installed, lock updated.

- [ ] **Step 2: Write the failing tests** (create `tests/test_perplexity_structured_fn.py`)

```python
import httpx
import pytest
from pydantic import BaseModel

from crewai_custom_tools.tools.web.perplexity_structured import perplexity_structured


class FactPack(BaseModel):
    headline: str
    confidence: float


@pytest.fixture()
def pplx_key(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")


def _client_returning(mocker, payload=None, exc=None):
    """Patch httpx.AsyncClient so post() returns payload or raises exc."""
    response = mocker.Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    client = mocker.AsyncMock()
    client.__aenter__.return_value = client
    if exc is not None:
        client.post.side_effect = exc
    else:
        client.post.return_value = response
    return mocker.patch(
        "crewai_custom_tools.tools.web.perplexity_structured.httpx.AsyncClient",
        return_value=client,
    )


async def test_returns_validated_instance(pplx_key, mocker):
    _client_returning(
        mocker,
        payload={"choices": [{"message": {"content": '{"headline": "Up", "confidence": 0.9}'}}]},
    )
    result = await perplexity_structured(prompt="q", schema=FactPack)
    assert result == FactPack(headline="Up", confidence=0.9)


async def test_returns_none_on_transport_error(pplx_key, mocker):
    _client_returning(mocker, exc=httpx.ConnectError("boom"))
    assert await perplexity_structured(prompt="q", schema=FactPack) is None


async def test_returns_none_on_invalid_payload(pplx_key, mocker):
    _client_returning(mocker, payload={"choices": [{"message": {"content": "not json"}}]})
    assert await perplexity_structured(prompt="q", schema=FactPack) is None


async def test_missing_key_raises_value_error(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    with pytest.raises(ValueError):
        await perplexity_structured(prompt="q", schema=FactPack)
```

Run: `uv run --extra dev pytest tests/test_perplexity_structured_fn.py -v`
Expected: FAIL — `ImportError: cannot import name 'perplexity_structured'`

- [ ] **Step 3: Implement.** Append to `src/crewai_custom_tools/tools/web/perplexity_structured.py` (add these imports at the top of the file: `import logging`, `from typing import TypeVar`, `import httpx`, `from pydantic import ValidationError`, `from crewai_custom_tools.core.keys import require_api_key`; add `logger = logging.getLogger(__name__)` after the imports):

```python
T = TypeVar("T", bound=BaseModel)

_DEFAULT_STRUCTURED_SYSTEM = "You are a research assistant. Provide concise, evidence-grounded answers with citations."


async def perplexity_structured(
    *,
    prompt: str,
    schema: type[T],
    system: str = _DEFAULT_STRUCTURED_SYSTEM,
    model: str = "sonar-pro",
    search_recency_filter: str | None = "month",
    timeout: float = 60.0,
    api_key: str | None = None,
) -> T | None:
    """Call Perplexity Sonar with JSON-schema structured output.

    Returns a validated ``schema`` instance, or ``None`` if the call or parse
    failed (callers treat research as best-effort). Raises ``ValueError`` when
    no API key is configured.
    """
    key = api_key or require_api_key("PERPLEXITY_API_KEY", "PPLX_API_KEY", tool_name="perplexity_structured")
    payload: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"schema": schema.model_json_schema()},
        },
        "return_citations": True,
    }
    if search_recency_filter:
        payload["search_recency_filter"] = search_recency_filter

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(_PERPLEXITY_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Perplexity HTTP {exc.response.status_code} for {schema.__name__}")
        return None
    except (TimeoutError, httpx.HTTPError) as exc:
        logger.warning(f"Perplexity transport error for {schema.__name__}: {exc}")
        return None
    except ValueError as exc:
        logger.warning(f"Perplexity returned non-JSON for {schema.__name__}: {exc}")
        return None

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.warning(f"Perplexity response missing content for {schema.__name__}")
        return None

    try:
        return schema.model_validate_json(content)
    except ValidationError:
        try:
            return schema.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning(f"Perplexity output unrecoverable for {schema.__name__}: {exc}")
            return None
```

Note: the module already defines `_PERPLEXITY_URL` — verify its definition reads `os.getenv("PPLX_BASE_URL", "https://api.perplexity.ai/chat/completions")`; if it is a plain string, change it to that `os.getenv` form (finwiz supports the `PPLX_BASE_URL` override and must not lose it).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_perplexity_structured_fn.py tests/test_perplexity.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/web/perplexity_structured.py tests/test_perplexity_structured_fn.py pyproject.toml uv.lock
git commit -m "feat(web): port perplexity_structured async function from finwiz

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 7: Reconcile `YahooFinanceTickerInfoTool` (batch mode + field parity)

**Files:**

- Modify: `src/crewai_custom_tools/tools/finance/yfinance_ticker.py`
- Test: `tests/test_yfinance_ticker.py` (append; adjust existing assertions if they assert exact key sets)

**Interfaces:**

- Produces: `_run(self, ticker: str, prefetched_data: dict | None = None) -> str`. Envelope `data` gains finwiz's extra fields (`previous_close`, `return_on_equity`, `debt_to_equity`, `revenue_growth`, `profit_margins`, `total_assets`, `nav_price`, `expense_ratio`, `beta` falls back to `beta3Year`) plus `timestamp`, optional `market_time`, and `data_source` (`"prefetched"` or `"live_api"`). Keeps central's cache and err-on-no-data behavior. `prefetched_data` is NOT in the args schema (programmatic-only, agents never pass it).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_yfinance_ticker.py`)

```python
from crewai_custom_tools.core.results import parse_tool_result


def test_prefetched_data_short_circuits_network(mocker):
    from crewai_custom_tools.tools.finance import yfinance_ticker

    ticker_spy = mocker.patch.object(yfinance_ticker.yf, "Ticker")
    tool = yfinance_ticker.YahooFinanceTickerInfoTool()
    raw = tool._run(ticker="AAPL", prefetched_data={"AAPL": {"symbol": "AAPL", "current_price": 123.0}})
    data = parse_tool_result(raw)
    assert data["current_price"] == 123.0
    assert data["data_source"] == "prefetched"
    ticker_spy.assert_not_called()


def test_live_result_includes_extended_fields_and_metadata(mocker):
    from crewai_custom_tools.tools.finance import yfinance_ticker

    mocker.patch.object(
        yfinance_ticker.yf,
        "Ticker",
        return_value=mocker.Mock(
            info={
                "shortName": "Apple",
                "currentPrice": 190.0,
                "returnOnEquity": 1.5,
                "debtToEquity": 152.4,
                "profitMargins": 0.25,
                "beta3Year": 1.1,
                "regularMarketTime": 1750000000,
            }
        ),
    )
    data = parse_tool_result(yfinance_ticker.YahooFinanceTickerInfoTool()._run(ticker="AAPL"))
    assert data["return_on_equity"] == 1.5
    assert data["debt_to_equity"] == 152.4
    assert data["profit_margins"] == 0.25
    assert data["beta"] == 1.1  # falls back to beta3Year
    assert data["data_source"] == "live_api"
    assert "timestamp" in data
    assert "market_time" in data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_yfinance_ticker.py -v`
Expected: new tests FAIL (`TypeError: _run() got an unexpected keyword argument 'prefetched_data'`).
NOTE: the cache manager may serve stale entries between tests — if the second test fails on cached data, check how existing tests in this file isolate the cache (they exercise it already) and reuse that fixture pattern.

- [ ] **Step 3: Implement.** Replace `_run` in `src/crewai_custom_tools/tools/finance/yfinance_ticker.py` (add imports `from datetime import UTC, datetime` and `from typing import Any` at the top):

```python
    @api_tool(provider="YahooFinance", endpoint="TickerInfo")
    def _run(self, ticker: str, prefetched_data: dict | None = None) -> str:
        """Execute the Yahoo Finance ticker info lookup."""
        # Batch mode: pre-fetched data short-circuits cache and network entirely.
        if prefetched_data is not None and ticker in prefetched_data:
            cached_info: dict[str, Any] = dict(prefetched_data[ticker])
            cached_info["data_source"] = "prefetched"
            return ok(cached_info)

        cache = get_cache_manager()
        cache_key = f"yahoo_ticker_info_{ticker}"

        cached_result = cache.get(cache_key, ttl=1800)
        if cached_result is not None:
            return str(cached_result)

        info = yf.Ticker(ticker).info

        fields = {
            "symbol": ticker,
            "name": info.get("shortName", "N/A"),
            "currency": info.get("currency", "N/A"),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
            "previous_close": info.get("previousClose", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "volume": info.get("volume", "N/A"),
            "average_volume": info.get("averageVolume", "N/A"),
            "52wk_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52wk_low": info.get("fiftyTwoWeekLow", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "beta": info.get("beta", info.get("beta3Year", "N/A")),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "total_assets": info.get("totalAssets", "N/A"),
            "nav_price": info.get("navPrice", "N/A"),
            "expense_ratio": info.get("annualReportExpenseRatio", "N/A"),
        }
        result = {k: v for k, v in fields.items() if v != "N/A"}

        # Only "symbol" survived => yfinance returned nothing usable (invalid/delisted).
        # Signal a failure and do NOT cache it, so a transient miss can recover.
        if set(result) <= {"symbol"}:
            return err(f"No data for ticker {ticker}")

        result["timestamp"] = datetime.now(UTC).isoformat()
        if "regularMarketTime" in info:
            try:
                result["market_time"] = datetime.fromtimestamp(info["regularMarketTime"], tz=UTC).isoformat()
            except (ValueError, TypeError, OSError):
                pass
        result["data_source"] = "live_api"

        envelope = ok(result)
        cache.set(cache_key, envelope)
        return envelope
```

- [ ] **Step 4: Run tests; fix any existing assertion that asserted an exact key set** (the data now always contains `timestamp` and `data_source` — change equality assertions to per-key assertions)

Run: `uv run --extra dev pytest tests/test_yfinance_ticker.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/finance/yfinance_ticker.py tests/test_yfinance_ticker.py
git commit -m "feat(finance): ticker info gains prefetched_data batch mode and finwiz field parity

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 8: Reconcile `YahooFinanceHistoryTool` (batch mode + timestamps)

**Files:**

- Modify: `src/crewai_custom_tools/tools/finance/history_holdings.py` (only `YahooFinanceHistoryTool._run`; `YahooFinanceETFHoldingsTool` is already strictly better than finwiz's — finwiz's called nonexistent yfinance APIs — leave it untouched)
- Test: `tests/test_finance_tools.py` (append)

**Interfaces:**

- Produces: `_run(self, ticker: str, period: str = "1y", interval: str = "1d", prefetched_data: dict | None = None) -> str`. Envelope `data` gains `timestamp` (now, UTC ISO), `data_time` (latest bar date as UTC ISO, when parseable) and `data_source`. Central's NaN guards and honest `price_change_percent` math stay.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_finance_tools.py`)

```python
from crewai_custom_tools.core.results import parse_tool_result


def test_history_prefetched_data_short_circuits_network(mocker):
    from crewai_custom_tools.tools.finance import history_holdings

    ticker_spy = mocker.patch.object(history_holdings.yf, "Ticker")
    tool = history_holdings.YahooFinanceHistoryTool()
    raw = tool._run(ticker="AAPL", prefetched_data={"AAPL": {"summary": {"symbol": "AAPL"}}})
    data = parse_tool_result(raw)
    assert data["data_source"] == "prefetched"
    ticker_spy.assert_not_called()


def test_history_live_result_has_timestamps(mocker):
    import pandas as pd

    from crewai_custom_tools.tools.finance import history_holdings

    frame = pd.DataFrame(
        {"Open": [1.0, 2.0], "High": [1.5, 2.5], "Low": [0.5, 1.5], "Close": [1.2, 2.2], "Volume": [100, 200]},
        index=pd.to_datetime(["2026-07-01", "2026-07-02"]),
    )
    mocker.patch.object(history_holdings.yf, "Ticker", return_value=mocker.Mock(history=mocker.Mock(return_value=frame)))
    data = parse_tool_result(history_holdings.YahooFinanceHistoryTool()._run(ticker="AAPL"))
    assert data["data_source"] == "live_api"
    assert "timestamp" in data
    assert data["data_time"].startswith("2026-07-02")
    assert data["summary"]["data_points"] == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -v -k history`
Expected: FAIL (`TypeError: unexpected keyword argument 'prefetched_data'`)

- [ ] **Step 3: Implement.** In `history_holdings.py`, add `from datetime import UTC, datetime` and `from typing import Any` to the imports, then change `YahooFinanceHistoryTool._run`: add the parameter and prefetch branch at the top, and replace the final `return ok(...)` line:

```python
    @api_tool(provider="YahooFinance", endpoint="History")
    def _run(self, ticker: str, period: str = "1y", interval: str = "1d", prefetched_data: dict | None = None) -> str:
        """Execute the Yahoo Finance historical data lookup."""
        if prefetched_data is not None and ticker in prefetched_data:
            cached_history: dict[str, Any] = dict(prefetched_data[ticker])
            cached_history["data_source"] = "prefetched"
            return ok(cached_history)

        ticker_data = yf.Ticker(ticker)
        # ... existing body unchanged through the `summary = {...}` block ...
```

and at the end of the method (replacing `return ok({"summary": summary, "history": history_list[-10:]})`):

```python
payload: dict[str, Any] = {
    "summary": summary,
    "history": history_list[-10:],
    "timestamp": datetime.now(UTC).isoformat(),
    "data_source": "live_api",
}
if history_list:
    try:
        payload["data_time"] = datetime.strptime(history_list[-1]["date"], "%Y-%m-%d").replace(tzinfo=UTC).isoformat()
    except ValueError:
        logger.warning(f"Could not parse latest bar date for {ticker}")
return ok(payload)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/finance/history_holdings.py tests/test_finance_tools.py
git commit -m "feat(finance): history tool gains prefetched_data batch mode and data timestamps

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 9: Reconcile `YahooFinanceCompanyInfoTool` (calculated revenue growth)

**Files:**

- Modify: `src/crewai_custom_tools/tools/finance/company_info.py`
- Test: `tests/test_finance_tools.py` (append)

**Interfaces:**

- Produces: same `_run(self, ticker: str) -> str` signature. Behavior gains finwiz's two fixes: `revenue_growth` is calculated from actual `ticker_data.financials` (falls back to `info["revenueGrowth"]`), and `debt_to_equity` converts yfinance's percentage to a ratio (152.41 → 1.52).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_finance_tools.py`)

```python
def _company_info_mock(mocker, info, financials):
    from crewai_custom_tools.tools.finance import company_info

    ticker = mocker.Mock(info=info)
    ticker.financials = financials
    mocker.patch.object(company_info.yf, "Ticker", return_value=ticker)
    return company_info.YahooFinanceCompanyInfoTool()


def test_company_info_calculates_revenue_growth_from_financials(mocker):
    import pandas as pd

    financials = pd.DataFrame({"2026": [200.0], "2025": [100.0]}, index=["Total Revenue"])
    tool = _company_info_mock(
        mocker,
        info={"longName": "Apple", "debtToEquity": 152.41, "revenueGrowth": 0.99},
        financials=financials,
    )
    data = parse_tool_result(tool._run(ticker="AAPL"))
    assert data["financial_metrics"]["revenue_growth"] == 1.0  # (200-100)/100, NOT info's 0.99
    assert data["financial_metrics"]["debt_to_equity"] == pytest.approx(1.5241)


def test_company_info_falls_back_to_info_field(mocker):
    import pandas as pd

    tool = _company_info_mock(
        mocker,
        info={"longName": "Apple", "revenueGrowth": 0.15},
        financials=pd.DataFrame(),
    )
    data = parse_tool_result(tool._run(ticker="AAPL"))
    assert data["financial_metrics"]["revenue_growth"] == 0.15
```

(add `import pytest` to the file imports if not already present)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -v -k company`
Expected: FAIL — `revenue_growth == 0.99` (raw info field) and `debt_to_equity == 152.41` (no conversion)

- [ ] **Step 3: Implement.** In `company_info.py`, add `from typing import Any` to the imports, and inside `_run` insert before the `company_info = {...}` dict:

```python
        # Calculate revenue growth from actual financials (more reliable than
        # info["revenueGrowth"]); fall back to the info field on any failure.
        revenue_growth: Any = "N/A"
        try:
            financials = ticker_data.financials
            if not financials.empty and "Total Revenue" in financials.index:
                revenues = financials.loc["Total Revenue"].sort_index(ascending=False)
                if len(revenues) >= 2:
                    latest, previous = revenues.iloc[0], revenues.iloc[1]
                    revenue_growth = (latest - previous) / previous if previous != 0 else "N/A"
        except (KeyError, ValueError, TypeError, AttributeError, IndexError) as exc:
            logger.warning(f"Failed to calculate revenue growth for {ticker}: {exc}")
        if revenue_growth == "N/A":
            revenue_growth = info.get("revenueGrowth", "N/A")

        # yfinance returns debtToEquity as a percentage (152.41 = 152.41%);
        # convert to a ratio (1.52) like every other metric here.
        raw_dte = info.get("debtToEquity")
        debt_to_equity = raw_dte / 100 if isinstance(raw_dte, (int, float)) else "N/A"
```

then in the `financial_metrics` dict replace the two lines:

```python
                "debt_to_equity": debt_to_equity,
                "revenue_growth": revenue_growth,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/finance/company_info.py tests/test_finance_tools.py
git commit -m "feat(finance): company info calculates revenue growth, converts debt/equity to ratio

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 10: Exports, version 0.4.0, CHANGELOG, crewai floor, tag, push

**Files:**

- Modify: `src/crewai_custom_tools/__init__.py`, `pyproject.toml`, `CHANGELOG.md`

**Interfaces:**

- Produces: package-root exports `perplexity_structured`, `parse_tool_result`, `ToolResultError`, `require_api_key`, `get_rate_limiter` (Tasks 11–15 import these from `crewai_custom_tools` / `crewai_custom_tools.core.results`); git tag `v0.4.0` on `main`, pushed to GitHub (finwiz's and epic_news's pins resolve against it).

- [ ] **Step 1: Update exports.** In `src/crewai_custom_tools/__init__.py`: change `__version__ = "0.3.1"` to `"0.4.0"`; add imports

```python
from crewai_custom_tools.core.keys import require_api_key
from crewai_custom_tools.core.rate_limiter import get_rate_limiter
from crewai_custom_tools.core.results import ToolResultError, ok, err, parse_tool_result
from crewai_custom_tools.tools.web.perplexity_structured import perplexity_structured
```

and append to `__all__`: `"require_api_key"`, `"get_rate_limiter"`, `"ToolResultError"`, `"ok"`, `"err"`, `"parse_tool_result"`, `"perplexity_structured"`.

- [ ] **Step 2: Bump versions in `pyproject.toml`:** `version = "0.3.1"` → `"0.4.0"`; `"crewai>=0.100.0"` → `"crewai>=1.15.1"`. Run `uv lock`.

- [ ] **Step 3: Add a CHANGELOG entry** (top of `CHANGELOG.md`, match the file's existing entry format):

```markdown
## v0.4.0 (2026-07-14)

### Breaking
- `PerplexitySearchTool`: `focus`/`recency` params replaced by `model`/`top_k`/`search_recency`/`search_domain_filter`; construction now raises `ValueError` without `PERPLEXITY_API_KEY` (or legacy `PPLX_API_KEY`). The recency filter is now actually sent (`search_recency_filter`).
- `crewai` floor raised to `>=1.15.1`.

### Added
- `parse_tool_result()` / `ToolResultError`: canonical envelope parsing for programmatic consumers.
- `require_api_key()`: fail-fast key validation with multi-var fallback.
- Provider-keyed synchronous rate limiter, enforced by `@api_tool` (disable with `CREWAI_TOOLS_RATE_LIMIT_DISABLED=1`).
- `perplexity_structured()` async function (JSON-schema structured research, ported from finwiz).
- `prefetched_data` batch mode on `YahooFinanceTickerInfoTool` and `YahooFinanceHistoryTool`.
- Yahoo ticker/history results now carry `timestamp` / `market_time` / `data_time` / `data_source`; ticker info gains finwiz's extended fundamental fields.
- `YahooFinanceCompanyInfoTool`: revenue growth calculated from actual financials; `debt_to_equity` converted to a ratio.
```

- [ ] **Step 4: Full suite + export smoke test**

Run: `uv run --extra dev pytest tests/ -q && uv run python -c "from crewai_custom_tools import perplexity_structured, parse_tool_result, ToolResultError, require_api_key, get_rate_limiter; print('exports ok')"`
Expected: all PASS, `exports ok`

- [ ] **Step 5: Commit, merge, tag, push**

```bash
git add -A
git commit -m "chore(release): v0.4.0 — finwiz parity wave 1

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git checkout main
git merge --no-ff wave1-finwiz-parity -m "merge: wave1-finwiz-parity for v0.4.0"
git tag v0.4.0
git push origin main --tags
```

Expected: tag `v0.4.0` visible on GitHub (`rtk gh api repos/fjacquet/crewai-custom-tools/tags | head` shows v0.4.0).

---

## Part B — epic_news (Task 11)

Working directory: `/Users/fjacquet/Projects/crews/epic_news`

### Task 11: Bump pin to v0.4.0 and absorb the Perplexity break

**Files:**

- Modify: `pyproject.toml:12`
- Modify: `tests/tools/test_web_tools.py` (and, only if the suite shows the same failure, `tests/tools/test_factory_wiring.py`, `tests/crews/test_composio_gmail_error_surfacing.py`)

**Interfaces:**

- Consumes: central v0.4.0 (`PerplexitySearchTool` now fail-fast; envelope shape unchanged).
- Produces: epic_news green against v0.4.0 — the release gate finwiz needs before consuming the tag.

- [ ] **Step 1: Record the baseline** (pre-existing failures are out of scope; only NEW failures must be fixed)

```bash
git checkout -b chore/crewai-custom-tools-0.4.0
uv run pytest tests -x -q 2>&1 | tail -5 > /tmp/epic_news_baseline.txt; cat /tmp/epic_news_baseline.txt
```

- [ ] **Step 2: Bump the pin.** In `pyproject.toml` line 12:

```toml
    "crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.4.0",
```

Run: `uv lock && uv sync`
Expected: lock resolves v0.4.0.

- [ ] **Step 3: Run the suite and compare against the baseline**

Run: `uv run pytest tests -x -q 2>&1 | tail -5`
Expected NEW failures only in tests that construct `PerplexitySearchTool` without a key (fail-fast `ValueError`). For each such test file, add an autouse fixture at the top:

```python
import pytest


@pytest.fixture(autouse=True)
def _perplexity_key(monkeypatch):
    monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key")
```

Re-run until the failure set matches the baseline.

- [ ] **Step 4: Commit and merge**

```bash
git add pyproject.toml uv.lock tests
git commit -m "chore(deps): bump crewai-custom-tools to v0.4.0

PerplexitySearchTool is now fail-fast at construction; tests provide a
dummy PERPLEXITY_API_KEY. Search tool signature gains model/top_k/
search_recency/search_domain_filter (focus/recency removed).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git checkout main && git merge chore/crewai-custom-tools-0.4.0 && git push
```

---

## Part C — finwiz (Tasks 12–15)

Working directory: `/Users/fjacquet/Projects/finwiz`, branch `spec/centralized-tools` (already exists).

### Task 12: Add the crewai-custom-tools dependency

**Files:**

- Modify: `pyproject.toml` (insert before line 37, the `]` closing `dependencies`)
- Modify: `src/finwiz/tools/CLAUDE.md` (document the co-development override)

**Interfaces:**

- Produces: `import crewai_custom_tools` works in finwiz's venv at v0.4.0. All later tasks depend on it.

- [ ] **Step 1: Add the dependency.** In `pyproject.toml`, before the closing `]` at line 37:

```toml
    "crewai-custom-tools @ git+https://github.com/fjacquet/crewai-custom-tools.git@v0.4.0",
```

Run: `uv lock && uv sync`
Expected: resolves and installs v0.4.0.

- [ ] **Step 2: Smoke-test the import**

Run: `uv run python -c "from crewai_custom_tools import YahooFinanceTickerInfoTool, PerplexitySearchTool, perplexity_structured, parse_tool_result; print('ok')"`
Expected: `ok`

- [ ] **Step 3: Document the local co-development override.** Append to `src/finwiz/tools/CLAUDE.md`:

```markdown
## Centralized tools (crewai-custom-tools)

Generic tools come from the `crewai-custom-tools` package, pinned to a git tag
in `pyproject.toml`. To co-develop against the local checkout, add (do NOT
commit this):

```toml
[tool.uv.sources]
crewai-custom-tools = { path = "../crewai_custom_tools", editable = true }
```

then `uv sync`. Remove the override and re-run `uv lock && uv sync` before
committing. Programmatic callers parse tool output with
`crewai_custom_tools.core.results.parse_tool_result()` — central tools return
the `{"success", "data", "error"}` JSON envelope, never bare dicts.

```

- [ ] **Step 4: Commit**

```bash
rtk git add pyproject.toml uv.lock src/finwiz/tools/CLAUDE.md
rtk git commit -m "feat(deps): add crewai-custom-tools v0.4.0 dependency

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 13: Swap the five Yahoo tools

**Files:**

- Modify: `src/finwiz/tools/finance_tools.py:30-34`
- Modify: `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:34-35`
- Modify: `src/finwiz/tools/portfolio_price_service.py:21` and the `_run` consumption at `:212-222`
- Modify: `src/finwiz/orchestrators/deep_analysis_data_collector.py` (function-local imports at `:121` and `:217` + envelope parsing)
- Modify: `src/finwiz/tools/standardized_sentiment_tool.py:183-197` (dead Yahoo-news branch — fix while adapting)
- Modify: `tests/unit/tools/test_portfolio_price_service.py`, `tests/unit/orchestrators/test_beta_extraction.py`, `tests/unit/orchestrators/test_deep_analysis_data_collection.py`, `tests/conftest.py`
- Delete: `src/finwiz/tools/yahoo_finance_ticker_info_tool.py`, `yahoo_finance_history_tool.py`, `yahoo_finance_company_info_tool.py`, `yahoo_finance_news_tool.py`, `yahoo_finance_etf_holdings_tool.py`, `tests/unit/tools/test_batch_prefetch_tools.py` (its cases now live in central Tasks 7–8)

**Interfaces:**

- Consumes: central classes `YahooFinanceTickerInfoTool`, `YahooFinanceHistoryTool`, `YahooFinanceCompanyInfoTool`, `YahooFinanceNewsTool`, `YahooFinanceETFHoldingsTool` (all return envelope strings) and `parse_tool_result` / `ToolResultError`.
- Produces: no module under `finwiz.tools` named `yahoo_finance_*`; factory bundles unchanged in shape (tool `.name` strings are identical between finwiz and central versions).

- [ ] **Step 1: Disable rate limiting in finwiz tests.** In `tests/conftest.py`, add near the top (after existing imports):

```python
import os

os.environ.setdefault("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "1")
```

- [ ] **Step 2: Swap the agent-facing imports.** In `src/finwiz/tools/finance_tools.py` replace lines 30–34 with:

```python
from crewai_custom_tools import (
    YahooFinanceCompanyInfoTool,
    YahooFinanceETFHoldingsTool,
    YahooFinanceHistoryTool,
    YahooFinanceNewsTool,
    YahooFinanceTickerInfoTool,
)
```

In `portfolio_rebalancing_crew.py` replace lines 34–35 with:

```python
from crewai_custom_tools import YahooFinanceHistoryTool, YahooFinanceTickerInfoTool
```

- [ ] **Step 3: Adapt `portfolio_price_service.py`.** Replace the import at line 21 with:

```python
from crewai_custom_tools import YahooFinanceTickerInfoTool
from crewai_custom_tools.core.results import ToolResultError, parse_tool_result
```

and replace the consumption block at lines 212–222:

```python
                raw = await asyncio.wait_for(asyncio.to_thread(self.yahoo_tool._run, symbol), timeout=self.config.request_timeout)
                try:
                    result = parse_tool_result(raw)
                except ToolResultError as exc:
                    logger.debug(f"Yahoo price fetch failed for {symbol}: {exc}")
                    result = None

                if isinstance(result, dict):
                    current_price = result.get("current_price")
                    if current_price and current_price != "N/A":
                        return PriceData(
                            symbol=symbol,
                            price=float(current_price),
                            timestamp=datetime.now(),
                            source="yahoo_finance",
                            currency=result.get("currency", "USD"),
```

(keep the rest of the function unchanged — the `if isinstance(result, dict) and "error" not in result` guard becomes the `isinstance(result, dict)` check above, since failures now raise).

- [ ] **Step 4: Adapt `deep_analysis_data_collector.py`.** At both function-local import sites (lines ~121 and ~217), replace with the central import plus the parser:

```python
        from crewai_custom_tools import YahooFinanceTickerInfoTool
        from crewai_custom_tools.core.results import parse_tool_result
```

and wrap the `_run` calls, e.g. the ticker-info site:

```python
            ticker_tool = YahooFinanceTickerInfoTool()
            ticker_result = parse_tool_result(ticker_tool._run(ticker=ticker))
```

(the enclosing `except Exception` already handles `ToolResultError`, which keeps the existing fallback `collected_data["ticker_info"] = {}` behavior). Apply the same pattern to the `YahooFinanceCompanyInfoTool` call in `_collect_stock_data`.

- [ ] **Step 5: Fix the dead Yahoo-news branch in `standardized_sentiment_tool.py` (lines 182–197).** The old code checked `isinstance(yahoo_result, list)` against a str return — it never appended anything. Replace with:

```python
            try:
                from crewai_custom_tools import YahooFinanceNewsTool
                from crewai_custom_tools.core.results import ToolResultError, parse_tool_result

                yahoo_tool = YahooFinanceNewsTool()
                try:
                    news_data = parse_tool_result(yahoo_tool._run(ticker=symbol, limit=max_count))
                except ToolResultError:
                    news_data = {}

                for item in (news_data or {}).get("news", [])[:max_count]:
                    articles.append(
                        {
                            "headline": item.get("title", ""),
                            "url": item.get("link", ""),
                            "date": datetime.now() - timedelta(days=1),  # Yahoo item dates are unreliable
                            "source": "Yahoo Finance",
                            "content": "",
                        }
                    )
```

(keep the surrounding try/except structure of the original block).

- [ ] **Step 6: Re-point the test patches.**
  - `tests/unit/tools/test_portfolio_price_service.py`: patch target `finwiz.tools.portfolio_price_service.YahooFinanceTickerInfoTool` is still valid (import-site patching). Update mocked `_run` return values from dicts to envelopes: wrap each mocked dict `D` as `json.dumps({"success": True, "data": D, "error": None})` — or import and use `crewai_custom_tools.core.results.ok(D)`. Error-case mocks (`{"error": ...}` dicts) become `crewai_custom_tools.core.results.err("...")` strings.
  - `tests/unit/orchestrators/test_beta_extraction.py` and `test_deep_analysis_data_collection.py`: replace every patch target `finwiz.tools.yahoo_finance_ticker_info_tool.YahooFinanceTickerInfoTool._run` with `crewai_custom_tools.tools.finance.yfinance_ticker.YahooFinanceTickerInfoTool._run` and `finwiz.tools.yahoo_finance_company_info_tool.YahooFinanceCompanyInfoTool._run` with `crewai_custom_tools.tools.finance.company_info.YahooFinanceCompanyInfoTool._run`; wrap their mocked returns with `ok(...)` the same way. The two function-local test imports (`test_deep_analysis_data_collection.py:423`, `test_beta_extraction.py` if present) switch to `from crewai_custom_tools import ...`.

- [ ] **Step 7: Delete the five tool files and the migrated test file**

```bash
rtk git rm src/finwiz/tools/yahoo_finance_ticker_info_tool.py src/finwiz/tools/yahoo_finance_history_tool.py src/finwiz/tools/yahoo_finance_company_info_tool.py src/finwiz/tools/yahoo_finance_news_tool.py src/finwiz/tools/yahoo_finance_etf_holdings_tool.py tests/unit/tools/test_batch_prefetch_tools.py
```

- [ ] **Step 8: Orphan sweep.** Run:

```bash
rtk grep -rn "yahoo_finance_ticker_info_tool\|yahoo_finance_history_tool\|yahoo_finance_company_info_tool\|yahoo_finance_news_tool\|yahoo_finance_etf_holdings_tool" src tests
rtk grep -rn "GetTickerInfoInput\|GetTickerHistoryInput\|GetCompanyInfoInput\|GetTickerNewsInput\|GetETFHoldingsInput" src tests
```

Expected: first grep returns nothing (fix any stragglers, including `src/finwiz/tools/__init__.py` re-exports). For the second: if the five input schemas in `src/finwiz/schemas/tools/inputs.py` are referenced ONLY by their definitions and `schemas/tools/__init__.py` exports, delete the five classes and their `__init__.py` export lines; if anything else references them, leave them and note it in the commit message.

- [ ] **Step 9: Run the gates**

Run: `make check`
Expected: PASS (lint, tests, unittest.mock check, docs validation, complexity, dead-code)

- [ ] **Step 10: Commit**

```bash
rtk git add -A
rtk git commit -m "refactor(tools): swap five Yahoo Finance tools to crewai-custom-tools

Programmatic callers (price service, deep-analysis collector, sentiment
news branch) now parse the ToolResult envelope via parse_tool_result().
The sentiment Yahoo-news branch was dead code (type check against a str
return) and now actually yields articles.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 14: Swap the Perplexity modules

**Files:**

- Modify: `src/finwiz/tools/perplexity_analysis_integration.py` (import at `:34`, instantiation at `:56`, `_parse_perplexity_response` at `:372-427`)
- Modify: `src/finwiz/analysis/fact_pack_research.py:19`, `src/finwiz/analysis/strategic_research.py:25`
- Delete: `src/finwiz/tools/perplexity_search_tool.py`, `src/finwiz/tools/perplexity_structured.py`
- Test: existing `tests/unit/analysis/test_fact_pack_research.py` (should pass unchanged — it patches at the import site)

**Interfaces:**

- Consumes: central `PerplexitySearchTool` (envelope `data`: `{"answer", "citations", "source"}`), central `perplexity_structured` (same signature as the deleted finwiz function), `parse_tool_result`/`ToolResultError`.
- Produces: no `finwiz.tools.perplexity_search_tool` / `finwiz.tools.perplexity_structured` modules. `PPLX_API_KEY` in `.env` keeps working (central reads it as fallback).

- [ ] **Step 1: Swap the structured-research imports.** In `fact_pack_research.py:19` and `strategic_research.py:25` replace with:

```python
from crewai_custom_tools import perplexity_structured
```

Run: `uv run pytest tests/unit/analysis/test_fact_pack_research.py -v`
Expected: PASS unchanged (the tests patch `finwiz.analysis.fact_pack_research.perplexity_structured`, which still exists as an import-site name).

- [ ] **Step 2: Swap the search tool in `perplexity_analysis_integration.py`.** Replace the import at line 34:

```python
from crewai_custom_tools import PerplexitySearchTool
from crewai_custom_tools.core.results import ToolResultError, parse_tool_result
```

- [ ] **Step 3: Adapt `_parse_perplexity_response` (lines 372–427).** The tool no longer returns the raw Perplexity API JSON; it returns the envelope whose `data` is `{"answer", "citations", "source"}`. Replace the method body's parsing section (keep signature, logging, and `_create_sonar_article` untouched):

```python
        articles = []
        raw_response_size = len(raw_response.encode("utf-8"))

        try:
            data = parse_tool_result(raw_response)

            # Citations come straight from the envelope now.
            citations = (data or {}).get("citations", [])

            for i, citation in enumerate(citations):
                try:
                    article = self._create_sonar_article(citation, analysis_type, i)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse citation {i}: {e!s}")
                    continue

            # If no citations found, try to extract from the answer text via the
            # legacy chat-completions shape the helper still understands.
            if not articles:
                legacy_shaped = {"choices": [{"message": {"content": (data or {}).get("answer", "")}}]}
                articles = self._extract_articles_from_content(legacy_shaped, analysis_type)

            if ticker:
                PerplexityOperationLogger.log_parsing_metrics(ticker, raw_response_size, len(articles))

        except ToolResultError as e:
            logger.error(f"Perplexity tool returned an error envelope: {e!s}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"Tool error: {e!s}")
        except Exception as e:
            logger.error(f"Unexpected error parsing Perplexity response: {e!s}")
            if ticker:
                PerplexityOperationLogger.log_api_failure(ticker, f"Response parsing error: {e!s}")

        return articles
```

Then check any other spot in the file that json-parses the raw tool output: `rtk grep -n "json.loads\|choices" src/finwiz/tools/perplexity_analysis_integration.py` — every remaining `json.loads(raw_response)`-style site must go through `parse_tool_result` the same way (the `_extract_articles_from_content` helper itself keeps its legacy-shape logic and needs no change).

- [ ] **Step 4: Check invocation compatibility.** Run: `rtk grep -n "_run(\|\.run(" src/finwiz/tools/perplexity_analysis_integration.py` — any call passing `model=`, `top_k=`, `search_recency=`, or `search_domain_filter=` is compatible (central adopted finwiz's parameter names). A call passing `focus=` or `recency=` would be a latent finwiz bug — rename to the new params.

- [ ] **Step 5: Delete the two local modules**

```bash
rtk git rm src/finwiz/tools/perplexity_search_tool.py src/finwiz/tools/perplexity_structured.py
```

- [ ] **Step 6: Orphan sweep**

```bash
rtk grep -rn "perplexity_search_tool\|finwiz.tools.perplexity_structured" src tests
rtk grep -rn "PerplexitySearchInput" src tests
rtk grep -rn "PERPLEXITY_CHAT" src tests
```

Expected: first grep empty (fix stragglers). `PerplexitySearchInput` in `schemas/tools/inputs.py`: delete the class + `__init__.py` export if nothing else references it. `PERPLEXITY_CHAT` in `config/endpoints.py`: if only the two deleted modules used it, delete the constant; otherwise leave it.

- [ ] **Step 7: Run the gates**

Run: `make check`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
rtk git add -A
rtk git commit -m "refactor(tools): swap Perplexity search tool and structured client to crewai-custom-tools

The integration layer now parses the ToolResult envelope; citations and
answer text come from the envelope's data instead of the raw API JSON.
PPLX_API_KEY keeps working (central reads it as a fallback).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 15: Contract tests at the factory seam + final verification

**Files:**

- Create: `tests/unit/tools/test_central_tools_contract.py`

**Interfaces:**

- Consumes: everything swapped in Tasks 13–14.
- Produces: the Wave-1 regression net — if a future central release changes tool names, envelope shape, or fail-fast behavior, these tests catch it inside finwiz.

- [ ] **Step 1: Write the contract tests** (create `tests/unit/tools/test_central_tools_contract.py`)

```python
"""Contract tests for the crewai-custom-tools seam (Wave 1).

These pin the parts of the central package finwiz depends on: factory
composition, the ToolResult envelope, and fail-fast key validation.
"""

import pytest
from crewai_custom_tools import PerplexitySearchTool
from crewai_custom_tools.core.results import ToolResultError, err, ok, parse_tool_result

from finwiz.tools.finance_tools import get_etf_research_tools, get_stock_research_tools


def test_stock_bundle_contains_central_yahoo_tools():
    names = {tool.name for tool in get_stock_research_tools()}
    assert {"Yahoo Finance Ticker Info Tool", "Yahoo Finance History Tool", "Yahoo Finance Company Info Tool", "Yahoo Finance News Tool"} <= names


def test_etf_bundle_contains_holdings_tool():
    names = {tool.name for tool in get_etf_research_tools()}
    assert "Yahoo Finance ETF Holdings Tool" in names


def test_envelope_roundtrip():
    assert parse_tool_result(ok({"price": 1.5})) == {"price": 1.5}
    with pytest.raises(ToolResultError, match="boom"):
        parse_tool_result(err("boom"))


def test_perplexity_fails_fast_without_key(monkeypatch):
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    with pytest.raises(ValueError):
        PerplexitySearchTool()


def test_safe_init_skips_keyless_tools(monkeypatch):
    from finwiz.tools.finance_tools import _safe_init

    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.delenv("PPLX_API_KEY", raising=False)
    assert _safe_init(PerplexitySearchTool) is None
```

- [ ] **Step 2: Run the new tests**

Run: `uv run pytest tests/unit/tools/test_central_tools_contract.py -v`
Expected: all PASS

- [ ] **Step 3: Full gates + coverage**

Run: `make check && make coverage`
Expected: PASS; coverage ≥65% (removing the migrated tool files shrinks the denominator — if coverage FELL below 65%, the deleted tests covered shared code paths; find them with the coverage report and extend the contract tests accordingly).

- [ ] **Step 4: Commit**

```bash
rtk git add tests/unit/tools/test_central_tools_contract.py
rtk git commit -m "test: contract tests for the crewai-custom-tools seam

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Wave-1 exit checklist**
  - [ ] central `main` at v0.4.0, tag pushed, CI green
  - [ ] epic_news suite matches its pre-bump baseline
  - [ ] finwiz `make check` green; no `yahoo_finance_*` / `perplexity_search_tool` / local `perplexity_structured` modules remain
  - [ ] `rtk git grep -n "tool.uv.sources" -- pyproject.toml` returns nothing (no committed editable override)
