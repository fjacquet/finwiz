# Test Isolation + pytest-xdist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the test suite reorder-safe (reset cached singletons + isolate config env per test, killing an API-key leak), then enable `pytest-xdist` so `make test` runs in parallel (~3min → target <30s).

**Architecture:** Add one autouse, function-scoped fixture in `tests/conftest.py` that (a) clears the env vars that feed the config singletons and (b) nulls the cached singletons before every test. With state no longer leaking across tests, `-n auto --dist=loadscope` becomes safe; wire it into `make test` / `make coverage-check` (CI).

**Tech Stack:** Python 3.12, uv, pytest + pytest-mock (`monkeypatch`), pytest-xdist.

**Working branch:** `perf/test-isolation-xdist` (create before Task 1: `git checkout -b perf/test-isolation-xdist`).

**Constraints:** pytest-mock only (NO `unittest.mock`). Line length ≤180. Do not weaken the 65% coverage gate. Keep the existing discovery network mocks.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `tests/conftest.py` | Global autouse isolation (singletons + env) | Modify |
| `tests/unit/test_global_isolation.py` | Meta-tests proving the isolation fixture works | Create |
| `tests/unit/utils/test_configuration_manager.py` | Drop the destructive `setup_method`; rely on autouse isolation | Modify |
| `pyproject.toml` | Add `pytest-xdist` dev dep | Modify |
| `Makefile` | `test` + `coverage-check` run `-n auto --dist=loadscope` | Modify |
| `CHANGELOG.md` | `[Unreleased]` note | Modify |

Singletons/globals involved (read-only references):
- `src/finwiz/config/manager.py:379` — `_config_manager` (no reset fn; null it directly).
- `src/finwiz/config/resilience_config.py` — `_resilience_config` + `reset_resilience_config()` (line 179).
- `src/finwiz/infrastructure/monitoring/litellm_callback.py:179` — `_token_monitor`.

---

## Task 1: Autouse isolation fixture (singletons + env)

**Files:**
- Modify: `tests/conftest.py`
- Test: `tests/unit/test_global_isolation.py`

- [ ] **Step 1: Write the failing meta-tests**

Create `tests/unit/test_global_isolation.py`:

```python
"""Meta-tests verifying the autouse isolation fixture in tests/conftest.py.

These guard the reorder-safety guarantees that let the suite run under
pytest-xdist: config-driving env vars are cleared and cached singletons are
reset before every test.
"""

import os


def test_api_key_env_vars_are_isolated():
    # The developer's real .env keys must never be visible inside tests
    # (prevents real-secret leakage into assertions/output).
    for var in ("OPENAI_API_KEY", "CHART_IMG_API_KEY", "KRAKEN_API_KEY"):
        assert os.getenv(var) is None, f"{var} leaked into the test environment"


def test_resilience_env_vars_are_isolated():
    assert os.getenv("FINWIZ_MAX_RETRIES") is None


def test_config_manager_singleton_is_reset():
    import finwiz.config.manager as cfg

    assert cfg._config_manager is None


def test_resilience_singleton_is_reset():
    import finwiz.config.resilience_config as res

    assert res._resilience_config is None


def test_token_monitor_singleton_is_reset():
    import finwiz.infrastructure.monitoring.litellm_callback as llm

    assert llm._token_monitor is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/test_global_isolation.py -v --no-cov`
Expected: FAIL (env vars present from `.env` and/or singletons not guaranteed None) — at least `test_api_key_env_vars_are_isolated` fails if a key is set in the environment.

- [ ] **Step 3: Add the autouse isolation fixture to `tests/conftest.py`**

In `tests/conftest.py`, after the existing imports/`os.environ.setdefault(...)` block and before the data fixtures (after line ~31, the `from tests.fixtures import (...)` block), add:

```python
# ---------------------------------------------------------------------------
# Global reorder-safe isolation (enables pytest-xdist parallelism).
#
# Cached config singletons + the developer's real .env would otherwise leak
# across tests, making results order-dependent (and leaking real API keys into
# assertion output). This autouse fixture resets that state before every test.
# ---------------------------------------------------------------------------

# Env vars that feed config singletons. Cleared per-test so unit tests never
# read the real .env and cannot pollute each other.
_ISOLATED_ENV_VARS = (
    # API keys — REQUIRED_API_KEYS in finwiz.config.manager
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "CHART_IMG_API_KEY",
    "TWELVE_DATA_API_KEY",
    "X-CMC_PRO_API_KEY",
    "KRAKEN_API_KEY",
    # Resilience config — finwiz.config.resilience_config
    "FINWIZ_MAX_RETRIES",
    "FINWIZ_RETRY_BASE_DELAY",
    "FINWIZ_RETRY_MAX_DELAY",
    "FINWIZ_HOLDING_TIMEOUT",
    "FINWIZ_FLOW_TIMEOUT",
    "FINWIZ_CIRCUIT_BREAKER_THRESHOLD",
    "FINWIZ_CIRCUIT_BREAKER_RECOVERY",
    "FINWIZ_AUTO_RESUME",
    "FINWIZ_STATE_MAX_AGE_HOURS",
    "FINWIZ_PARALLEL_LIMIT",
    "FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT",
    "FINWIZ_CLEANUP_STATE_ON_SUCCESS",
    "FINWIZ_STATE_CLEANUP_MAX_AGE_DAYS",
    "PORTFOLIO_PARALLEL_LIMIT",
    "DEEP_ANALYSIS_PARALLEL_LIMIT",
)


@pytest.fixture(autouse=True)
def _isolate_global_state(monkeypatch):
    """Reset cached config singletons and clear config-driving env vars per test.

    Makes the suite safe to run in parallel (pytest-xdist) and prevents unit
    tests from reading the real ``.env`` (which also stops real secrets reaching
    assertion output). ``monkeypatch`` auto-restores on teardown.

    A test that needs a specific value sets it AFTER this fixture runs (e.g.
    ``monkeypatch.setenv("OPENAI_API_KEY", "test-key")``), which wins.
    """
    import finwiz.config.manager as _cfg
    import finwiz.config.resilience_config as _res
    import finwiz.infrastructure.monitoring.litellm_callback as _llm

    for var in _ISOLATED_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    monkeypatch.setattr(_cfg, "_config_manager", None, raising=False)
    monkeypatch.setattr(_res, "_resilience_config", None, raising=False)
    monkeypatch.setattr(_llm, "_token_monitor", None, raising=False)
```

(`pytest` is already imported in conftest.py.)

- [ ] **Step 4: Run the meta-tests — verify they pass**

Run: `uv run pytest tests/unit/test_global_isolation.py -v --no-cov`
Expected: PASS (5 tests).

- [ ] **Step 5: Lint**

Run: `uv run ruff check --fix tests/conftest.py tests/unit/test_global_isolation.py && uv run ruff format tests/conftest.py tests/unit/test_global_isolation.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/unit/test_global_isolation.py
git commit -m "test: autouse fixture to isolate config singletons + env (reorder-safe)"
```

---

## Task 2: Remove the destructive env-clearing from the config-manager tests

**Files:**
- Modify: `tests/unit/utils/test_configuration_manager.py`

The class `TestConfigurationManager` (line 25) has a `setup_method` (lines 28-42) that does `del os.environ[var]` for 7 vars — destructive (never restored), incomplete, and the source of order-dependence. The autouse fixture from Task 1 now provides clean, restored env isolation for ALL classes (including `TestConfigurationManagerIntegration` at line 429, which had none). Remove the manual `setup_method`.

- [ ] **Step 1: Delete the `setup_method`**

In `tests/unit/utils/test_configuration_manager.py`, delete these lines (28-42) entirely:

```python
    def setup_method(self):
        """Set up test environment."""
        # Clear environment variables
        env_vars_to_clear = [
            "OPENAI_API_KEY",
            "SERPER_API_KEY",
            "ALPHA_VANTAGE_API_KEY",
            "CHART_IMG_API_KEY",
            "TWELVE_DATA_API_KEY",
            "X-CMC_PRO_API_KEY",
            "KRAKEN_API_KEY",
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]
```

Leave the rest of `TestConfigurationManager` and its tests intact. If `os` becomes unused after this deletion, the next step's ruff `--fix` removes the import; if other tests in the file still use `os` (e.g. `mocker.patch.dict("os.environ", ...)` references), leave it.

- [ ] **Step 2: Run the whole file (and the previously-failing test) in isolation**

Run: `uv run pytest tests/unit/utils/test_configuration_manager.py -v --no-cov`
Expected: ALL pass, including `TestConfigurationManagerIntegration::test_should_handle_mixed_required_and_optional_keys` — and the test now operates on a clean env (no real `.env` keys present).

- [ ] **Step 3: Prove the secret leak is gone**

Run a deliberately-isolated single test and confirm its output contains no real key material. Run:
`uv run pytest "tests/unit/utils/test_configuration_manager.py::TestConfigurationManagerIntegration::test_should_handle_mixed_required_and_optional_keys" -q --no-cov 2>&1 | tail -5`
Expected: `1 passed`. (Because the autouse fixture cleared all API-key env vars, `ConfigurationManager.api_keys` can only contain values the test sets itself — never the developer's real keys — so even a future failure cannot print real secrets.)

- [ ] **Step 4: Lint + commit**

Run: `uv run ruff check --fix tests/unit/utils/test_configuration_manager.py && uv run ruff format tests/unit/utils/test_configuration_manager.py`

```bash
git add tests/unit/utils/test_configuration_manager.py
git commit -m "test(config): drop destructive env-clearing; rely on autouse isolation (no secret leak)"
```

---

## Task 3: Confirm the resilience reset test is reorder-safe

**Files:**
- Verify only: `tests/unit/config/test_resilience_config.py` (no change expected)

`TestResetResilienceConfig::test_should_reset_singleton` (line ~533) assumes the singleton starts unset (`get_resilience_config()` reads `FINWIZ_MAX_RETRIES=5`). It failed under xdist when a prior test had already cached `_resilience_config`. Task 1's autouse fixture now nulls `_resilience_config` before every test, so the assumption holds regardless of order.

- [ ] **Step 1: Run the resilience test file**

Run: `uv run pytest tests/unit/config/test_resilience_config.py -v --no-cov`
Expected: ALL pass.

- [ ] **Step 2: Run it inside the broader config suite (cross-test contamination check)**

Run: `uv run pytest tests/unit/config -q --no-cov`
Expected: ALL pass — the autouse reset makes the singleton's starting state independent of any earlier test in the run.

- [ ] **Step 3: No code change → no commit for this task.** (If a change WAS needed, the fix is the same pattern as Task 1 — reset the offending singleton in `_isolate_global_state`.)

---

## Task 4: Enable pytest-xdist

**Files:**
- Modify: `pyproject.toml`, `Makefile`

- [ ] **Step 1: Add the dev dependency**

In `pyproject.toml`, in `[dependency-groups]` `dev = [ ... ]`, add after `"pytest-timeout>=2.4.0",`:

```python
    "pytest-xdist>=3.6.0",
```

- [ ] **Step 2: Lock + sync**

Run: `uv lock && uv sync --all-groups`
Expected: adds `pytest-xdist` and `execnet`.

- [ ] **Step 3: Parallelize `make test` and `make coverage-check`**

In `Makefile`, change the `test` recipe from:

```makefile
test:
	uv run pytest -m "not integration" -q
```

to:

```makefile
test:
	uv run pytest -m "not integration" -q -n auto --dist=loadscope
```

And change the `coverage-check` recipe from:

```makefile
	uv run pytest --cov=src/finwiz --cov-report=term-missing --cov-fail-under=65 --quiet
```

to:

```makefile
	uv run pytest --cov=src/finwiz --cov-report=term-missing --cov-fail-under=65 --quiet -n auto --dist=loadscope
```

(Recipe lines use TAB indentation. Leave `test-verbose` and `coverage` serial.)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock Makefile
git commit -m "test: enable pytest-xdist (-n auto) for make test + coverage-check"
```

---

## Task 5: Verify reorder-safety and flakiness

**Files:** none (verification). Capture only PASS/FAIL summaries and test IDs — never dump full assertion output (secret-safety).

- [ ] **Step 1: Run the full suite under xdist (loadscope) — run 1**

Run: `uv run pytest -m "not integration" --no-cov -n auto --dist=loadscope -q -rf 2>&1 | tail -8`
Expected: `N passed` (≈5164 incl. the 5 new meta-tests), `0 failed`.

- [ ] **Step 2: Run it again — run 2 (flakiness check)**

Run: `uv run pytest -m "not integration" --no-cov -n auto --dist=loadscope -q -rf 2>&1 | tail -8`
Expected: identical `0 failed`. If any test fails in run 1 or 2, note its ID, find the shared state it depends on (singleton/env/file), and reset/isolate it in `tests/conftest.py::_isolate_global_state` (or that test's own `monkeypatch`). Re-run until two consecutive clean runs.

- [ ] **Step 3: Stress with `--dist=load` (max reordering)**

Run: `uv run pytest -m "not integration" --no-cov -n auto --dist=load -q -rf 2>&1 | tail -10`
Expected: ideally `0 failed`. `load` distributes individual tests (more aggressive than `loadscope`) and may surface class-fixture-shared tests that are NOT true global-state bugs. If failures appear ONLY under `load` and are due to legitimate same-class fixture sharing (not global singletons/env), that's acceptable — `loadscope` (our chosen mode) keeps classes together. Record any such cases in the commit message; only fix true global-state leaks.

- [ ] **Step 4: Confirm the coverage gate passes under xdist**

Run: `make coverage-check 2>&1 | tail -6`
Expected: `Coverage meets minimum threshold (65%)` and `0 failed`. If a test that previously relied on a real `.env` key now fails (env isolation), fix that test to set the value it needs via `monkeypatch.setenv(...)` or to mock the dependency — do NOT relax the autouse isolation.

- [ ] **Step 5: Commit any straggler fixes**

```bash
git add -A
git commit -m "test: isolate remaining order-dependent state for xdist"
```
(Skip if Steps 1-4 were clean with no changes.)

---

## Task 6: CHANGELOG + final gate

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update the changelog**

In `CHANGELOG.md`, under the existing `## [Unreleased]` `### Changed` section (created by the previous test-speedup PR), append:

```markdown
- **Parallel test runs (pytest-xdist).** Added an autouse isolation fixture
  (`tests/conftest.py`) that resets cached config singletons and clears
  config-driving env vars before every test, making the suite reorder-safe;
  this also fixes a latent leak where config tests could read — and print on
  failure — the developer's real `.env` API keys. `make test` and the CI
  coverage gate now run with `-n auto --dist=loadscope` (~3min → <1min).
```

- [ ] **Step 2: Final gates**

Run: `uv run ruff check . 2>&1 | tail -3`
Expected: `All checks passed!`

Run: `make coverage-check 2>&1 | tail -4`
Expected: passes, coverage ≥65%.

Run: `uv run mypy src/finwiz 2>&1 | tail -2`
Expected: `Success` (no src changes, but confirm nothing regressed).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note parallel test runs + test-isolation fix"
```

---

## Final verification (before PR)

- [ ] Two consecutive `-n auto --dist=loadscope` full runs: `0 failed`.
- [ ] `make coverage-check`: passes, coverage ≥65%, under xdist.
- [ ] `grep -rn "OPENAI_API_KEY\|CHART_IMG_API_KEY" $(git ls-files 'tests/**') | grep -v conftest.py | grep -v _ISOLATED` — no test asserts on a real key value.
- [ ] `make test` wall-clock noticeably reduced (record before/after).
- [ ] ruff clean; mypy clean; no `unittest.mock` introduced.

## Spec-coverage check

- Reorder-safe singleton reset → Task 1. ✅
- Env isolation (no real `.env` in tests) → Task 1. ✅
- Secret-leak fixed + verified → Task 1 + Task 2 (Step 3). ✅
- Remove destructive setup_method → Task 2. ✅
- Resilience reset test reorder-safe → Task 3. ✅
- Enable xdist (dep + make test + coverage-check/CI) → Task 4. ✅
- Verify reorder-safety + flakiness + gate → Task 5. ✅
- CHANGELOG, no version bump → Task 6. ✅
- CI uses `make coverage-check` (already wired in the prior PR), so xdist + the 65% gate run in CI automatically. ✅
