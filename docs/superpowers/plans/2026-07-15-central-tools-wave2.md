# Central Tools Migration — Wave 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship crewai-custom-tools v0.5.0 (bounded rate-limiter waits, provider fixes, company-info fallback fix), swap finwiz's seven "clean" Wave-2 tools to central, and convert four Perplexity-entangled tools into thin finwiz wrappers over central deterministic cores.

**Architecture:** Same three-repo order as Wave 1: central release first (tag v0.5.0), epic_news gate (additive-only — expect zero changes beyond the pin), then finwiz swaps/wrappers. finwiz keeps every tool whose value is domain enrichment (Perplexity, feature flags) as a wrapper that delegates its deterministic fetch to the central tool and parses the envelope. Spec: `docs/superpowers/specs/2026-07-14-centralized-tools-design.md`.

**Tech Stack:** Python (3.11+ central, 3.13 finwiz), uv, pytest + pytest-mock (unittest.mock BANNED both repos), CrewAI BaseTool, requests/httpx.

## Spec deltas (approved scope corrections from reconnaissance)

1. **`market_screening_tool` deferred to Wave 3** — it imports `screening_criteria`/`screening_utils`/`screening_ranking` and transitively invokes `APlusScoringTool._run` (all Wave-3 grading cluster). Migrating it alone breaks the closure.
2. **`enhanced_sec_tool` (EnhancedSECAnalysisTool) and `standardized_sentiment_tool` (StandardizedSentimentAnalysisTool) stay in finwiz unchanged this wave** — central's same-named classes are different tools (companyfacts metrics vs filing-section analysis; text-VADER vs symbol-news pipeline). No meaningful deterministic core to deduplicate. Revisit in Wave 3+ only if central grows matching cores.
3. **`twelve_data/` subdir + `twelve_data_transformers.py` + `twelve_data_client.py` are an orphaned dead-code chain** (imported by nobody) — deleted, not migrated. **`sentiment/` is an empty directory** — deleted.
4. **Enrichment strategy (user decision): thin finwiz wrappers.** TwelveData ×2, AlphaVantage overview, EnhancedCrypto, EnhancedETF keep their finwiz class names, signatures, and output shapes; only their internal data fetch is replaced by a central-tool call + `parse_tool_result`.
5. **Placeholder removals:** finwiz's `StandardizedRiskScoringTool` (in enhanced_sec_tool.py) and `CrossAssetSentimentComparatorTool` (in standardized_sentiment_tool.py) are stubs returning static methodology text. Risk scoring swaps to central's real implementation (same symbol-based mental model). CrossAsset comparator is REMOVED from factories entirely — central's version is text-corpus-based (wrong shape for finwiz crews), and a placeholder tool in an agent's kit is noise, not signal.

## Global Constraints

- **Envelope contract:** central tools return `ok(data)`/`err(msg)` JSON strings; finwiz programmatic callers and wrappers parse via `crewai_custom_tools.core.results.parse_tool_result` (raises `ToolResultError`).
- **Additive-first for epic_news:** v0.5.0 must not change any tool epic_news uses (`KrakenTickerInfoTool`, `KrakenAssetListTool`, `AlphaVantageOverviewTool`, `ExchangeRateTool` — all agent-facing). No signature or envelope-shape changes to those.
- **Wrapper rule:** wrappers preserve current finwiz `_run` signatures and return types EXACTLY (dicts stay dicts, markdown stays markdown). Only the fetch internals change.
- **pytest-mock only; tests offline; output pristine.** finwiz: `make check` green before every commit; new files ≤300 lines; line length 180. Central: `uv run --extra dev pytest tests/ -q` green.
- **Commit trailer** on every commit:
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`
- Central work on branch `wave2-finwiz-parity` (from main/v0.4.0), merged + tagged v0.5.0 before any consumer bumps. finwiz work continues on `spec/centralized-tools`.
- finwiz environment note: after any plain `uv sync`, re-run `uv sync --group docs` (mkdocs pre-commit hook needs it).

---

## Part A — crewai_custom_tools (Tasks 1–3)

Working directory: `/Users/fjacquet/Projects/crewai_custom_tools`. Before Task 1: `git checkout main && git pull && git checkout -b wave2-finwiz-parity`.

### Task 1: Bounded rate-limiter waits + provider registry fixes

**Files:**

- Modify: `src/crewai_custom_tools/core/rate_limiter.py`
- Modify: `src/crewai_custom_tools/core/decorators.py`
- Modify: `src/crewai_custom_tools/tools/finance/sec.py` (provider string only)
- Test: `tests/test_rate_limiter.py` (append), `tests/test_decorators.py` (append)

**Interfaces:**

- Consumes: existing `RateLimit`, `_TokenBucket`, `RateLimiterRegistry`, `get_rate_limiter()`.
- Produces: `RateLimitExceeded(RuntimeError)`; `RateLimiterRegistry.acquire(provider, max_wait: float | None = None)` — waits up to `max_wait` seconds (default from env `CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT`, fallback 120.0), raises `RateLimitExceeded` beyond it, and logs a WARNING whenever a wait exceeds 5s. `@api_tool` converts `RateLimitExceeded` into the standard `err(...)` envelope. Registry gains entries: `"SECEdgar"` also matched by `"SEC-EDGAR"` (sec.py normalized instead — see Step 4), `"TickerValidation"` RateLimit(120, 10), `"CoinGecko"` RateLimit(30, 5), `"DeFiLlama"` RateLimit(60, 10).

- [ ] **Step 1: Write the failing tests** (append to `tests/test_rate_limiter.py`)

```python
import logging

from crewai_custom_tools.core.rate_limiter import RateLimitExceeded


def test_acquire_raises_when_max_wait_exceeded():
    registry = RateLimiterRegistry({"Slow": RateLimit(requests_per_minute=1, burst=1)})
    registry.acquire("Slow")  # consumes the only burst token
    with pytest.raises(RateLimitExceeded, match="Slow"):
        registry.acquire("Slow", max_wait=0.05)


def test_acquire_env_default_max_wait(monkeypatch):
    monkeypatch.setenv("CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT", "0.05")
    registry = RateLimiterRegistry({"Slow": RateLimit(requests_per_minute=1, burst=1)})
    registry.acquire("Slow")
    with pytest.raises(RateLimitExceeded):
        registry.acquire("Slow")


def test_long_wait_logs_warning(monkeypatch, caplog):
    monkeypatch.setattr("crewai_custom_tools.core.rate_limiter._WARN_WAIT_SECONDS", 0.01)
    registry = RateLimiterRegistry({"Chatty": RateLimit(requests_per_minute=600, burst=1)})
    registry.acquire("Chatty")
    with caplog.at_level(logging.WARNING, logger="crewai_custom_tools.rate_limiter"):
        registry.acquire("Chatty")  # ~0.1s refill wait > 0.01 threshold
    assert any("Chatty" in rec.message for rec in caplog.records)


def test_new_providers_registered():
    for provider in ("TickerValidation", "CoinGecko", "DeFiLlama"):
        assert provider in DEFAULT_RATE_LIMITS
```

(these tests live in the same file as the existing `_enable_rate_limiting` autouse fixture — they inherit it; add the needed imports at the top of the file.)

- [ ] **Step 2: Write the failing decorator test** (append to `tests/test_decorators.py`)

```python
def test_api_tool_converts_rate_limit_exceeded_to_err(mocker):
    import json

    from crewai_custom_tools.core import decorators
    from crewai_custom_tools.core.rate_limiter import RateLimitExceeded

    registry = mocker.Mock()
    registry.acquire.side_effect = RateLimitExceeded("DemoProvider: rate-limit wait exceeded 0.0s")
    mocker.patch.object(decorators, "get_rate_limiter", return_value=registry)

    @decorators.api_tool(provider="DemoProvider", endpoint="DemoEndpoint")
    def sample() -> str:
        return "never reached"

    payload = json.loads(sample())
    assert payload["success"] is False
    assert "rate-limit" in payload["error"]
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_rate_limiter.py tests/test_decorators.py -v`
Expected: FAIL — `ImportError: cannot import name 'RateLimitExceeded'`

- [ ] **Step 4: Implement.** In `src/crewai_custom_tools/core/rate_limiter.py`:

Add after the imports (module already imports `os`, `threading`, `time`; add `import logging` and a module logger):

```python
logger = logging.getLogger("crewai_custom_tools.rate_limiter")

_WARN_WAIT_SECONDS = 5.0
_DEFAULT_MAX_WAIT = 120.0


class RateLimitExceeded(RuntimeError):
    """Raised when acquiring a token would exceed the caller's max_wait budget."""
```

Replace `_TokenBucket.acquire` with a bounded variant:

```python
    def acquire(self, provider: str, max_wait: float | None = None) -> None:
        deadline = None if max_wait is None else time.monotonic() + max_wait
        waited = 0.0
        warned = False
        while True:
            with self._lock:
                now = time.monotonic()
                self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._refill_per_sec)
                self._updated = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._refill_per_sec
            if deadline is not None and time.monotonic() + wait > deadline:
                raise RateLimitExceeded(f"{provider}: rate-limit wait would exceed {max_wait:.1f}s (waited {waited:.1f}s)")
            if not warned and waited + wait > _WARN_WAIT_SECONDS:
                logger.warning(f"{provider}: rate-limited, waiting {wait:.1f}s for a token (total wait so far {waited:.1f}s)")
                warned = True
            time.sleep(wait)
            waited += wait
```

(note: `_TokenBucket.acquire` gains the `provider` parameter for messages/logs.)

Replace `RateLimiterRegistry.acquire` with:

```python
    def acquire(self, provider: str, max_wait: float | None = None) -> None:
        if os.getenv("CREWAI_TOOLS_RATE_LIMIT_DISABLED", "").lower() in ("1", "true"):
            return
        bucket = self._buckets.get(provider)
        if bucket is None:
            return
        if max_wait is None:
            max_wait = float(os.getenv("CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT", str(_DEFAULT_MAX_WAIT)))
        bucket.acquire(provider, max_wait)
```

Add to `DEFAULT_RATE_LIMITS`:

```python
    "TickerValidation": RateLimit(requests_per_minute=120, burst=10),
    "CoinGecko": RateLimit(requests_per_minute=30, burst=5),
    "DeFiLlama": RateLimit(requests_per_minute=60, burst=10),
```

- [ ] **Step 5: Convert the exception in `@api_tool`.** In `src/crewai_custom_tools/core/decorators.py`, import `RateLimitExceeded` alongside `get_rate_limiter`, and add a dedicated except branch BEFORE the generic `except Exception` in the wrapper:

```python
            except RateLimitExceeded as e:
                logger.warning(f"{provider} {endpoint} rate-limit budget exhausted: {e}")
                return err(f"{provider} {endpoint}: {e}")
```

- [ ] **Step 6: Fix the SEC provider mismatch.** In `src/crewai_custom_tools/tools/finance/sec.py`, change `@api_tool(provider="SEC-EDGAR", ...)` to `@api_tool(provider="SECEdgar", ...)` (registry key match; SEC calls were running unthrottled).

- [ ] **Step 7: Run the full suite**

Run: `uv run --extra dev pytest tests/ -q`
Expected: all PASS (the suite-wide kill switch keeps everything else fast)

- [ ] **Step 8: Commit**

```bash
git add src/crewai_custom_tools/core/rate_limiter.py src/crewai_custom_tools/core/decorators.py src/crewai_custom_tools/tools/finance/sec.py tests/test_rate_limiter.py tests/test_decorators.py
git commit -m "feat(core): bounded rate-limiter waits with warn logging; register missing providers

Waits now respect CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT (default 120s) and
surface as err() envelopes instead of blocking forever. Fixes SEC-EDGAR
vs SECEdgar registry mismatch (SEC calls ran unthrottled); adds
TickerValidation/CoinGecko/DeFiLlama limits.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 2: CompanyInfo — financials fetch falls back on ANY failure

**Files:**

- Modify: `src/crewai_custom_tools/tools/finance/company_info.py`
- Test: `tests/test_finance_tools.py` (append)

**Interfaces:**

- Consumes/produces: unchanged `_run(self, ticker: str) -> str`. The Wave-1 deferral: the revenue-growth calculation's `except (KeyError, ValueError, TypeError, AttributeError, IndexError)` doesn't cover network errors from the independent `ticker_data.financials` fetch, so a `RequestException` errs the whole call even though `info` succeeded and the fallback exists.

- [ ] **Step 1: Write the failing test** (append to `tests/test_finance_tools.py`)

```python
def test_company_info_survives_financials_network_error(mocker):
    from crewai_custom_tools.tools.finance import company_info

    ticker = mocker.Mock(info={"longName": "Apple", "revenueGrowth": 0.15})
    type(ticker).financials = mocker.PropertyMock(side_effect=ConnectionError("edgar down"))
    mocker.patch.object(company_info.yf, "Ticker", return_value=ticker)
    data = parse_tool_result(company_info.YahooFinanceCompanyInfoTool()._run(ticker="AAPL"))
    assert data["financial_metrics"]["revenue_growth"] == 0.15
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -k financials_network -v`
Expected: FAIL — the ConnectionError escapes to `@api_tool` and the call returns an err envelope (`ToolResultError` raised by `parse_tool_result`).

- [ ] **Step 3: Implement.** In `company_info.py`, change the revenue-growth try/except to catch everything (the fallback is the documented intent — "fall back to the info field on any failure"):

```python
        except Exception as exc:  # noqa: BLE001 — any failure here must fall back, not kill the call
            logger.warning(f"Failed to calculate revenue growth for {ticker}: {exc}")
```

(keep the existing `if revenue_growth == "N/A": revenue_growth = info.get("revenueGrowth", "N/A")` fallback line unchanged.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_finance_tools.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/crewai_custom_tools/tools/finance/company_info.py tests/test_finance_tools.py
git commit -m "fix(finance): company info falls back to info field on any financials-fetch failure

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task 3: Subpackage re-exports + release v0.5.0

**Files:**

- Modify: `src/crewai_custom_tools/tools/finance/__init__.py`, `src/crewai_custom_tools/__init__.py` (version only), `pyproject.toml` (version), `CHANGELOG.md`

**Interfaces:**

- Produces: `from crewai_custom_tools.tools.finance import EnhancedCryptoAnalysisTool` (etc.) works for the Wave-2 tool set (currently only top-level imports work); git tag `v0.5.0` pushed. finwiz Tasks 5+ pin this tag.

- [ ] **Step 1: Extend `tools/finance/__init__.py`.** Add imports + `__all__` entries for the classes currently exported only at package root: `TickerExistenceValidationTool`, `EnhancedETFAnalysisTool`, `EnhancedCryptoAnalysisTool`, `DeFiMetricsTool` (from `.enhanced`); `EnhancedSECAnalysisTool` (from `.sec`); `StandardizedRiskScoringTool` (from `.risk`); `StandardizedSentimentAnalysisTool`, `CrossAssetSentimentComparatorTool` (from `.sentiment`); `TwelveDataIndicatorTool`, `TwelveDataMultiIndicatorTool` (from `.indicators`); `AlphaVantageNewsSentimentTool`, `ChartImgTool` (from `.market_extras`); `MarketScreeningTool` (from `.screening`). Follow the file's existing import style exactly.

- [ ] **Step 2: Bump versions.** `pyproject.toml` `version = "0.4.0"` → `"0.5.0"`; `__init__.py` `__version__` likewise. Run `uv lock`.

- [ ] **Step 3: CHANGELOG entry** (top, matching the file's `## [X.Y.Z] - date` convention):

```markdown
## [0.5.0] - 2026-07-15

### Added
- Rate limiter: bounded waits (`CREWAI_TOOLS_RATE_LIMIT_MAX_WAIT`, default 120s) surfacing as `err()` envelopes via `RateLimitExceeded`; WARNING log for waits >5s; new provider limits for `TickerValidation`, `CoinGecko`, `DeFiLlama`.
- `crewai_custom_tools.tools.finance` subpackage now re-exports the full finance tool set (previously top-level only).

### Fixed
- SEC tool's rate-limit provider key (`SEC-EDGAR` → `SECEdgar`) — SEC calls were unthrottled.
- `YahooFinanceCompanyInfoTool` falls back to `info["revenueGrowth"]` on ANY financials-fetch failure (network errors previously errored the whole call).
```

- [ ] **Step 4: Full suite + smoke, then release**

Run: `uv run --extra dev pytest tests/ -q && uv run python -c "from crewai_custom_tools.tools.finance import TwelveDataIndicatorTool, EnhancedCryptoAnalysisTool; print('subpackage ok')"`
Expected: all PASS, `subpackage ok`

```bash
git add -A -- src pyproject.toml uv.lock CHANGELOG.md
git commit -m "chore(release): v0.5.0 — bounded rate limits, finance subpackage exports

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git checkout main
git merge --no-ff wave2-finwiz-parity -m "merge: wave2-finwiz-parity for v0.5.0"
git tag -a v0.5.0 -m "v0.5.0 — bounded rate limits, finance subpackage exports"
git push origin main --tags
```

Expected: `gh api repos/fjacquet/crewai-custom-tools/tags --jq '.[].name' | head -3` includes v0.5.0.

---

## Part B — epic_news (Task 4)

Working directory: `/Users/fjacquet/Projects/crews/epic_news`. NOTE: the checkout may be on a user WIP branch — do all work on a fresh branch from `origin/main` via a temp worktree if the checkout is busy (the Wave-1 fix used `git worktree add`; same pattern), and NEVER touch uncommitted user files.

### Task 4: Bump pin to v0.5.0 (additive gate)

**Files:**

- Modify: `pyproject.toml:12` (pin `@v0.4.0` → `@v0.5.0`), `uv.lock`

**Interfaces:**

- Produces: epic_news green against v0.5.0 — the release gate for finwiz. Wave-2 central changes are strictly additive for epic_news's surface (Kraken ×2, AlphaVantageOverview, ExchangeRate untouched), so ZERO test edits are expected; any new failure means a central regression — STOP and report BLOCKED rather than patching tests.

- [ ] **Step 1: Baseline** — `uv run pytest tests -x -q 2>&1 | tail -3` on the pre-bump checkout; record.
- [ ] **Step 2: Bump** — pin line to `@v0.5.0`; `uv lock && uv sync --all-extras`.
- [ ] **Step 3: Compare** — rerun; failure set must MATCH baseline exactly (no new fixtures allowed this wave).
- [ ] **Step 4: Commit to main, push; watch "CI Tests and Checks" + "Security & SBOM" on the new commit to completion** (poll `gh run list --commit "$(git rev-parse HEAD)"` with sleep 60, up to 15 min). Both must conclude success.

```bash
git commit -m "chore(deps): bump crewai-custom-tools to v0.5.0 (additive: bounded rate limits)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" -- pyproject.toml uv.lock
```

---

## Part C — finwiz (Tasks 5–11)

Working directory: `/Users/fjacquet/Projects/finwiz`, branch `spec/centralized-tools`.

### Task 5: Bump finwiz to v0.5.0

**Files:** `pyproject.toml` (pin line `@v0.4.0` → `@v0.5.0`), `uv.lock`

- [ ] **Step 1:** Edit the pin; `uv lock && uv sync && uv sync --group docs`.
- [ ] **Step 2:** Smoke: `uv run python -c "from crewai_custom_tools import TickerExistenceValidationTool, DeFiMetricsTool, StandardizedRiskScoringTool, KrakenTickerInfoTool, AlphaVantageNewsSentimentTool, ChartImgTool, TwelveDataIndicatorTool, EnhancedCryptoAnalysisTool, AlphaVantageOverviewTool; print('ok')"` → `ok`.
- [ ] **Step 3:** `make test` quick gate, then commit `pyproject.toml uv.lock` with message `chore(deps): bump crewai-custom-tools to v0.5.0` + trailer.

### Task 6: Clean swap A — TickerExistenceValidation + Kraken (+ broken-import bug fix)

**Files:**

- Modify: `src/finwiz/tools/finance_tools.py` (imports at :26 Kraken, :35 TickerValidation), `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:34`, `src/finwiz/crews/deep_analysis/tool_routing.py:138-142`, `src/finwiz/crews/helpers/tool_routing.py:106-110`, `src/finwiz/orchestrators/portfolio_holdings_processor.py:40` (+ its `_run` consumption at ~:400)
- Modify: `tests/unit/orchestrators/test_portfolio_holdings_grading.py`, `tests/unit/orchestrators/test_portfolio_review.py` (patch targets stay import-site — verify), plus any test importing the two modules
- Delete: `src/finwiz/tools/ticker_validation_tool.py`, `src/finwiz/tools/kraken_api_tool.py`

**Interfaces:**

- Consumes: central `TickerExistenceValidationTool._run(symbol, asset_class="auto") -> str` (ENVELOPE — finwiz's returned a dict) and `KrakenTickerInfoTool._run(pair) -> str` (envelope; finwiz's returned raw json.dumps — agent-facing only).
- Produces: no local ticker_validation/kraken modules. `portfolio_holdings_processor` parses the envelope: `data = parse_tool_result(self.validator._run(symbol=..., asset_class=...))` inside a try/except `ToolResultError` that maps to `{"valid": False, "reason": str(exc)}` (preserve the caller's downstream reads of `valid`/`reason`/`meta` — central's data payload carries the same keys; verify against central `enhanced.py` source and adapt key mapping if any differ, noting it in the report).
- **Bug fix (was latent):** `crews/deep_analysis/tool_routing.py:142` imports nonexistent `TickerValidationTool` — becomes `from crewai_custom_tools import TickerExistenceValidationTool` and the instantiation renamed accordingly. Also BOTH tool_routing files pass `prefetched_data=` kwargs to Enhanced* constructors that declare no such field — REMOVE those kwargs (they were silently wrong; enhanced tools get prefetched data via the data-collector path, not construction).

- [ ] Steps: swap imports → adapt `portfolio_holdings_processor` consumption (envelope) → fix both tool_routing files (import name + drop `prefetched_data=` constructor kwargs) → re-point/adjust tests (mock returns become `ok({...})` envelopes where `_run` is patched; import-site class patches keep working) → delete the two files → orphan sweep `rtk grep -rn "ticker_validation_tool\|kraken_api_tool" src tests` (must be empty; also sweep `TickerValidationTool\b`) → `make check` → commit `refactor(tools): swap ticker validation and Kraken to central; fix broken TickerValidationTool import` + trailer.

### Task 7: Clean swap B — AlphaVantage news + ChartImg + DeFi metrics

**Files:**

- Modify: `src/finwiz/tools/finance_tools.py` (:18 AlphaVantageNewsSentimentTool, :21 ChartImgTool, :22 DeFiMetricsTool imports)
- Modify: `tests/unit/tools/test_alpha_vantage_news_tool.py`, `tests/unit/tools/test_chart_img_tool.py` (re-point to central classes and envelope expectations, or delete if central's suite already covers the identical case — central has missing-key/success tests for both; delete finwiz's and note it)
- Delete: `src/finwiz/tools/alpha_vantage_news_tool.py`, `src/finwiz/tools/chart_img_tool.py`, `src/finwiz/tools/defi_metrics_tool.py`

**Interfaces:**

- Consumes: central `AlphaVantageNewsSentimentTool` (parses response into envelope — strictly better than finwiz's raw `resp.text` passthrough), `ChartImgTool` (envelope-wrapped chart payload vs finwiz's bare data-URL string — agent-facing only, no programmatic finwiz consumers: verified in recon), `DeFiMetricsTool` (central hits the REAL DeFiLlama API; finwiz's returned hardcoded mock data — strict upgrade, and the factory's crypto bundle keeps the same tool name).
- Key-gating: central versions check keys lazily in `_run` (no construction ValueError), so `_safe_init` never skips them — they now ALWAYS join the bundle and err politely at runtime without keys. That matches central's hybrid-auth convention; note it in the commit message. `finance_tools.py`: move `AlphaVantageNewsSentimentTool` and `ChartImgTool` out of the `_safe_init` loops into the direct-instantiation lists (they no longer raise).

- [ ] Steps: swap imports + factory-loop adjustments → test re-point/deletion → delete three files → orphan sweep (`alpha_vantage_news_tool\|chart_img_tool\|defi_metrics_tool`) → schema orphan check (`AlphaVantageNewsInput`, `ChartImgInput`, `DeFiMetricsInput` in `schemas/tools/inputs.py` — delete each only if nothing but `test_inputs.py` references it, and drop the corresponding test classes; else leave, note why) → `make check` → commit `refactor(tools): swap AV news, ChartImg, DeFi metrics to central (DeFi now real DeFiLlama data)` + trailer.

### Task 8: Clean swap C — risk scoring placeholder → central; drop comparator placeholder

**Files:**

- Modify: `src/finwiz/tools/enhanced_sec_tool.py` (DELETE the `StandardizedRiskScoringTool` class only; keep `EnhancedSECAnalysisTool` and everything else), `src/finwiz/tools/standardized_sentiment_tool.py` (DELETE the `CrossAssetSentimentComparatorTool` class only)
- Modify: `src/finwiz/tools/finance_tools.py` (:25 import splits — `EnhancedSECAnalysisTool` still from finwiz, `StandardizedRiskScoringTool` from central; remove `CrossAssetSentimentComparatorTool` import at :31-34 and ALL its instantiations at :68, :97, :123, :147), `src/finwiz/crews/portfolio_rebalancing_crew/portfolio_rebalancing_crew.py:26`, `src/finwiz/crews/investment_discovery_crew/investment_discovery_crew.py:194` (import central's risk tool)
- Tests: sweep for both class names; update factory-count assertions (bundles shrink by one tool where the comparator was)

**Interfaces:**

- Consumes: central `StandardizedRiskScoringTool._run(ticker) -> str` (real beta/debt/volatility/size scoring, envelope) replacing finwiz's placeholder `_run(symbol, asset_class, ...) -> dict` — agent-facing only (recon confirmed no programmatic `_run` callers of either placeholder). Args schema changes from (symbol, asset_class) to (ticker); crews adapt via schema automatically.
- Produces: `CrossAssetSentimentComparatorTool` gone from finwiz bundles (placeholder noise removal — logged as a deliberate, user-visible change in the commit message).

- [ ] Steps: class deletions → factory/crew import rewires → test sweep (`rtk grep -rn "StandardizedRiskScoringTool\|CrossAssetSentimentComparatorTool" src tests` — finwiz-src hits must all resolve to central imports; test assertions on bundle contents updated) → schema orphan check (`StandardizedRiskScoringInput`, `CrossAssetSentimentComparatorInput`) → `make check` → commit `refactor(tools): real central risk scoring replaces placeholder; drop comparator stub from bundles` + trailer.

### Task 9: Wrappers — TwelveData ×2 delegate fetch to central

**Files:**

- Modify: `src/finwiz/tools/twelve_data_tool.py`, `src/finwiz/tools/twelve_data_multi_indicator_tool.py`
- Modify: `tests/unit/tools/test_twelve_data_tool.py`, `tests/unit/tools/test_twelve_data_multi_indicator_tool.py`

**Interfaces:**

- Consumes: central `TwelveDataIndicatorTool._run(symbol, indicator="rsi", interval="1day", length=None, fast_period=None, slow_period=None, signal_period=None, outputsize=100) -> str` and `TwelveDataMultiIndicatorTool._run(symbol, interval="1day", indicators=None, rsi_period=..., ...) -> str` — both envelopes. `parse_tool_result`.
- Produces: finwiz classes keep their EXACT current `_run` signatures and markdown-string returns; internally each constructs the central tool once (private attr in `model_post_init`, after the existing `validate_api_key` fail-fast which stays), replaces the direct `requests.get` fetch with `parse_tool_result(self._central._run(...))` (mapping finwiz's param names onto central's — note finwiz's single-indicator signature has `interval` before `indicator`; central the reverse: map by keyword, never positionally), and keeps the markdown formatting + Perplexity enrichment block untouched. The `@api_tool(provider=APIProvider.TWELVE_DATA, ...)` decorator on `_run` is REMOVED (central's decorator now provides timeout + rate limiting + 429 retry inside the delegated call; leaving finwiz's would double-rate-limit).
- Tests: replace `requests.get` mocks with `mocker.patch("crewai_custom_tools.tools.finance.indicators.TwelveDataIndicatorTool._run", return_value=ok({...}))`-style mocks (import `ok` from central); drop the `with_rate_limit` patches (no longer in the path); keep the fail-fast key tests unchanged.

- [ ] Steps per tool: rewrite fetch internals (read the current file first; the change is confined to the fetch helper + decorator removal) → update tests → focused pytest → next tool → `make check` → commit `refactor(tools): TwelveData tools delegate fetch to central package` + trailer.

### Task 10: Wrappers — AlphaVantage overview + EnhancedCrypto delegate fetch to central

**Files:**

- Modify: `src/finwiz/tools/alpha_vantage_tool.py`, `src/finwiz/tools/enhanced_crypto_tool.py`
- Modify: `tests/unit/tools/` tests for both (recon lists `patch.object(tool, "_get_crypto_data")` etc. — those object-level patches keep working; only tests mocking `requests.get` for the fetch path re-point to the central `_run`)
- Modify: `src/finwiz/tools/portfolio_price_service.py:282` consumption ONLY IF the wrapper's return shape changes (it must not — assert unchanged)

**Interfaces:**

- `AlphaVantageCompanyOverviewTool`: keeps `_run(ticker, include_perplexity=True, prefetched_data=None) -> str` (markdown). Internal `_fetch_company_overview` becomes a sync call to central `AlphaVantageOverviewTool._run(ticker)` + `parse_tool_result`, dropping finwiz's `@api_tool` async decorator and the `finwiz.infrastructure.caching` usage for this path (central provides rate limiting; add the fetched dict to the existing markdown renderer). The `load_dotenv()` module side effect stays (other finwiz modules may rely on it loading early — verify with a grep before deciding; if nothing else in the import graph needs it, note and keep anyway this wave).
- `EnhancedCryptoAnalysisTool`: keeps `_run(symbol, include_thesis=True, include_risk_assessment=True, max_thesis_bullets=10, include_perplexity=True) -> dict`. Internal `_get_crypto_data` (CoinGecko fetch) becomes central `EnhancedCryptoAnalysisTool._run(symbol, max_thesis_bullets=...)` + `parse_tool_result`, keeping finwiz's thesis/risk/Perplexity layers reading from the parsed data. IMPORTANT: central's data payload keys differ from CoinGecko's raw shape finwiz parses — read both implementations first and map explicitly (`crypto_data` consumers downstream read `market_cap`, `total_volume`/`volume_24h`, `circulating_supply`, `max_supply`/`total_supply`, `current_price` — the wrapper must guarantee those keys survive; if central's payload lacks any, fetch stays hybrid: use central for what it provides and keep a minimal direct CoinGecko call ONLY for missing keys, documenting which).
- `portfolio_price_service.py:282` and `deep_analysis_data_collector.py:170` consume the wrapper's dict — signatures/keys unchanged means NO edits there; verify with the existing tests.

- [ ] Steps: read both finwiz files + central counterparts → implement AV wrapper → focused tests → implement crypto wrapper (key-mapping table in the report) → focused tests incl. `test_portfolio_price_service.py` and `test_deep_analysis_data_collection.py` untouched-and-green → `make check` → commit `refactor(tools): AlphaVantage overview and EnhancedCrypto delegate fetch to central` + trailer.

### Task 11: EnhancedETF holdings via central + dead-code cleanup + gates

**Files:**

- Modify: `src/finwiz/tools/enhanced_etf_tool.py` (holdings path only), `tests/unit/tools/test_enhanced_etf_tool.py`
- Delete: `src/finwiz/tools/twelve_data/` (whole subdir), `src/finwiz/tools/twelve_data_transformers.py`, `src/finwiz/tools/twelve_data_client.py`, `src/finwiz/tools/sentiment/` (empty dir)
- Modify: `tests/unit/tools/test_central_tools_contract.py` (extend)

**Interfaces:**

- EnhancedETF wrapper: `_extract_top_holdings` (or the equivalent method the file actually has — read it first) delegates to central `EnhancedETFAnalysisTool._run(ticker, max_holdings=...)` + `parse_tool_result`, replacing the yfinance/scraping holdings path; factsheet scraping via `ETFDataFetcher` and risk assessment via `ETFAnalyzer` stay untouched (finwiz domain analysis). Signature and dict return unchanged.
- Dead-code deletions: recon verified `twelve_data_transformers.py`/`twelve_data_client.py`/`tools/twelve_data/` are imported by NOTHING outside themselves; re-verify with `rtk grep -rn "twelve_data_transformers\|twelve_data_client\|tools.twelve_data" src tests` before `git rm` (if a new importer appeared, STOP and report). Delete their test files if any exist (sweep `tests/` for the same names).
- Contract tests extension (append to `test_central_tools_contract.py`):

```python
def test_crypto_bundle_has_real_defi_tool():
    from finwiz.tools.finance_tools import get_crypto_research_tools

    names = {tool.name for tool in get_crypto_research_tools()}
    assert any("DeFi" in name for name in names)


def test_risk_scoring_is_central():
    from crewai_custom_tools import StandardizedRiskScoringTool

    from finwiz.tools.finance_tools import get_stock_research_tools

    assert any(isinstance(tool, StandardizedRiskScoringTool) for tool in get_stock_research_tools())
```

- [ ] Steps: ETF holdings delegation → tests → dead-code sweep + `git rm` → contract tests → `make check && make coverage` (≥65%) → Wave-2 exit checklist: central v0.5.0 tagged + CI green; epic_news green on the v0.5.0 bump; finwiz `rtk git grep -n "tool.uv.sources" -- pyproject.toml` empty; no module named `ticker_validation_tool|kraken_api_tool|alpha_vantage_news_tool|chart_img_tool|defi_metrics_tool|twelve_data_client|twelve_data_transformers` remains → commit `refactor(tools): ETF holdings via central; delete orphaned twelve_data chain` + trailer.
