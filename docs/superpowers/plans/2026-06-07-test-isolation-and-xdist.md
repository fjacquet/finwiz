# Test Isolation + pytest-xdist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the test suite reorder-safe (clear config-driving env vars + reset cached singletons before every test, killing an order-dependent API-key leak), then enable `pytest-xdist` so `make test` runs in parallel. Record the real before/after wall-clock; target ≈3 min → ≈1 min (do **not** hard-commit to "<30s" — xdist worker startup + import cost makes that optimistic).

**Architecture:** Add one autouse, function-scoped fixture in `tests/conftest.py` that (a) clears the env vars that feed the config singletons and (b) nulls the cached singletons — before every test, all via `monkeypatch` so teardown restores cleanly. With state no longer leaking across tests, `-n auto --dist=loadscope` becomes safe; wire it into `make test` / `make coverage-check` (CI).

### Root cause (verified)

The order-dependence and the secret leak come from two interacting facts:

1. **Import-time `.env` pollution.** ~9 modules call a no-arg `load_dotenv()` at import (e.g. `core/app_initializer.py:25`, `config/llm/llm_config.py:35`, the crews, `tools/alpha_vantage_tool.py`). `load_dotenv()` walks up from the package to the repo root and loads the real `.env` into `os.environ` — **once per process**, before any test runs. Verified: importing `finwiz.core.app_initializer` alone populates `OPENAI_API_KEY`, `CHART_IMG_API_KEY`, `KRAKEN_API_KEY`, etc. The repo `.env` exists locally (112 assignments) and contains all seven API keys (required + optional).
2. **A destructive, non-restored cleanup in one test class.** `TestConfigurationManager.setup_method` did `del os.environ[var]` for 7 keys with no restore — a permanent global mutation. So once that class ran, those keys were gone for the rest of the session; tests running *before* it still saw them. `TestConfigurationManagerIntegration` (no `setup_method`) asserts `"Chart-img" not in api_keys`, which only holds if an earlier class already deleted `CHART_IMG_API_KEY`. Under `pytest-xdist` reordering, when the integration test runs first the real `CHART_IMG_API_KEY` is still present → assertion fails **and the real key is printed in the failure output**.

The fix: clear the config-driving env vars before *every* test (restored by `monkeypatch`, so no destructive global mutation), and null the cached singletons so env-derived/mutable state can't carry across tests. Deterministic regardless of order.

> **Deliberately NOT done (and why):** We do **not** patch `load_dotenv` or override pydantic's `env_file`. Verified reasons: `ConfigurationManager`'s own "default `.env`" branch computes `parents[2]/.env` = `.../src/.env`, which does not exist, so constructing a manager re-loads nothing (no per-test re-injection). And `FinWizSettings` uses `env_prefix="FINWIZ_"`; `.env` has no `FINWIZ_`-prefixed API keys, so `get_settings()` surfaces no secrets. Per-test env clearing is therefore sufficient and simpler — don't add `.env`-blocking machinery for paths that don't leak.

**Tech Stack:** Python 3.12, uv, pytest + pytest-mock (`monkeypatch`), pytest-xdist.

**Working branch:** `perf/test-isolation-xdist` (already created).

**Constraints:** pytest-mock only (NO `unittest.mock`). Line length ≤180. Do not weaken the 65% coverage gate. Keep the existing discovery network mocks.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `tests/conftest.py` | Global autouse isolation (clear env + reset singletons) | Modify |
| `tests/unit/test_global_isolation.py` | Meta-tests proving the isolation fixture works (incl. constructing a real manager) | Create |
| `tests/unit/utils/test_configuration_manager.py` | Drop the destructive `setup_method`; rely on autouse isolation | Modify |
| `pyproject.toml` | Add `pytest-xdist` dev dep | Modify |
| `Makefile` | `test` + `coverage-check` run `-n auto --dist=loadscope` | Modify |
| `CHANGELOG.md` | `[Unreleased]` note | Modify |

Singletons reset by the fixture, with rationale:

- `src/finwiz/config/manager.py:379` — `_config_manager` (env-derived; no reset fn — null directly).
- `src/finwiz/config/settings.py:216` — `_settings` (env/`.env`-derived cache; `reset_settings()` existed but was unused). **Was missing from the original plan.**
- `src/finwiz/config/resilience_config.py:87` — `_resilience_config` (env-derived; `reset_resilience_config()` at line 179).
- `src/finwiz/config/features/flags.py:251` — `_feature_flags` (holds **mutable circuit-breaker state** mutated by `record_failure`; leaks across tests under any ordering). **Was missing from the original plan.**
- `src/finwiz/infrastructure/monitoring/litellm_callback.py:179` — `_token_monitor` (mutable accumulator).

> **Scope note on the other ~19 singletons.** A sweep found 24 module-level `_x: T | None = None` singletons. We reset the 5 above because unit tests exercise them and they carry env-derived or mutable state. The rest (cache managers, rate limiter, degradation manager, monitoring collectors, validation managers, etc.) are left alone deliberately — resetting everything risks masking real bugs and adds churn. The two full-suite verification runs in **Task 5** are the safety net: if a flake surfaces, add a targeted reset to `_isolate_global_state` using the same pattern, and note it.

---

## Task 1: Autouse isolation fixture (clear env + reset singletons)

**Files:**

- Modify: `tests/conftest.py`
- Test: `tests/unit/test_global_isolation.py`

- [ ] **Step 1: Write the failing meta-tests**

Create `tests/unit/test_global_isolation.py`:

```python
"""Meta-tests verifying the autouse isolation fixture in tests/conftest.py.

These guard the reorder-safety guarantees that let the suite run under
pytest-xdist: config-driving env vars are cleared and cached singletons are
reset before every test, so the developer's real ``.env`` (loaded into
``os.environ`` by import-time ``load_dotenv()`` calls) never bleeds into a test
or its failure output.
"""

import os

import pytest

from finwiz.config.manager import ConfigurationError, ConfigurationManager


def test_api_key_env_vars_are_isolated():
    # Real .env keys must never be visible inside tests.
    for var in ("SERPER_API_KEY", "CHART_IMG_API_KEY", "KRAKEN_API_KEY"):
        assert os.getenv(var) is None, f"{var} leaked into the test environment"


def test_resilience_env_vars_are_isolated():
    assert os.getenv("FINWIZ_MAX_RETRIES") is None


def test_building_configuration_manager_sees_no_real_keys():
    # Constructing a manager inside a test must find no API keys — proving the
    # import-time .env pollution was cleared and nothing leaks into api_keys
    # (which is what gets printed on failure).
    mgr = ConfigurationManager()
    with pytest.raises(ConfigurationError) as exc:
        mgr.validate_api_keys()
    assert "SERPER_API_KEY" in exc.value.missing_keys
    assert mgr.api_keys == {}, "real .env keys leaked into ConfigurationManager.api_keys"


def test_config_manager_singleton_is_reset():
    import finwiz.config.manager as cfg

    assert cfg._config_manager is None


def test_settings_singleton_is_reset():
    import finwiz.config.settings as settings

    assert settings._settings is None


def test_resilience_singleton_is_reset():
    import finwiz.config.resilience_config as res

    assert res._resilience_config is None


def test_feature_flags_singleton_is_reset():
    import finwiz.config.features.flags as flags

    assert flags._feature_flags is None


def test_token_monitor_singleton_is_reset():
    import finwiz.infrastructure.monitoring.litellm_callback as llm

    assert llm._token_monitor is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/unit/test_global_isolation.py -v --no-cov`
Expected: FAIL. With a real `.env` present (loaded by import-time `load_dotenv()`), `test_api_key_env_vars_are_isolated` and `test_building_configuration_manager_sees_no_real_keys` fail (keys visible), and the singleton-reset tests fail (no fixture yet).

- [ ] **Step 3: Add the autouse isolation fixture to `tests/conftest.py`**

In `tests/conftest.py`, after the existing imports/`os.environ.setdefault(...)` block and the `from tests.fixtures import (...)` block (after line ~31), add:

```python
# ---------------------------------------------------------------------------
# Global reorder-safe isolation (enables pytest-xdist parallelism).
#
# Import-time load_dotenv() calls in ~9 modules load the real .env into
# os.environ once per process. Combined with cached config singletons, that
# state would otherwise leak across tests, making results order-dependent (and
# leaking real API keys into assertion output on failure). This autouse fixture
# resets that state before every test, via monkeypatch (auto-restored).
# ---------------------------------------------------------------------------

# Non-FINWIZ_-prefixed env vars resilience_config still honours (back-compat).
_EXTRA_CONFIG_ENV_VARS = ("PORTFOLIO_PARALLEL_LIMIT", "DEEP_ANALYSIS_PARALLEL_LIMIT")


@pytest.fixture(autouse=True)
def _isolate_global_state(monkeypatch):
    """Clear config-driving env vars and reset cached config singletons per test.

    Makes the suite safe under pytest-xdist and prevents unit tests from seeing
    the developer's real ``.env`` (which also stops real secrets reaching
    assertion output). ``monkeypatch`` auto-restores on teardown, so there is no
    destructive global mutation.

    A test that needs a specific value sets it AFTER this fixture runs (e.g.
    ``monkeypatch.setenv("SERPER_API_KEY", "test-serper-key-32-characters-long")``),
    which wins.
    """
    import finwiz.config.features.flags as _flags
    import finwiz.config.manager as _cfg
    import finwiz.config.resilience_config as _res
    import finwiz.config.settings as _settings
    import finwiz.infrastructure.monitoring.litellm_callback as _llm

    # Clear config-driving env vars. API-key names are sourced from the code (not
    # duplicated); FINWIZ_-prefixed vars are cleared by scanning so new ones are
    # covered automatically (FINWIZ_TEST_LOGS is preserved).
    for kc in _cfg.ConfigurationManager.REQUIRED_API_KEYS:
        monkeypatch.delenv(kc.env_var, raising=False)
    for var in list(os.environ):
        if var.startswith("FINWIZ_") and var != "FINWIZ_TEST_LOGS":
            monkeypatch.delenv(var, raising=False)
    for var in _EXTRA_CONFIG_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    # Reset env-derived / mutable-state singletons.
    monkeypatch.setattr(_settings, "_settings", None, raising=False)
    monkeypatch.setattr(_cfg, "_config_manager", None, raising=False)
    monkeypatch.setattr(_res, "_resilience_config", None, raising=False)
    monkeypatch.setattr(_flags, "_feature_flags", None, raising=False)
    monkeypatch.setattr(_llm, "_token_monitor", None, raising=False)
```

(`pytest` and `os` are already imported in conftest.py.)

- [ ] **Step 4: Run the meta-tests — verify they pass**

Run: `uv run pytest tests/unit/test_global_isolation.py -v --no-cov`
Expected: PASS (8 tests).

- [ ] **Step 5: Lint**

Run: `uv run ruff check --fix tests/conftest.py tests/unit/test_global_isolation.py && uv run ruff format tests/conftest.py tests/unit/test_global_isolation.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/unit/test_global_isolation.py
git commit -m "test: autouse fixture to isolate config env + reset singletons (reorder-safe)"
```

---

## Task 2: Remove the destructive env-clearing from the config-manager tests

**Files:**

- Modify: `tests/unit/utils/test_configuration_manager.py`

The class `TestConfigurationManager` (line 25) has a `setup_method` (lines 28-42) that does `del os.environ[var]` for 7 vars — a **non-restored global mutation** and the source of the order-dependence (see Root cause). The autouse fixture from Task 1 now provides clean, restored isolation for ALL classes (including `TestConfigurationManagerIntegration` at line 429, which had none). Remove the manual `setup_method`.

- [ ] **Step 1: Delete the `setup_method`**

In `tests/unit/utils/test_configuration_manager.py`, delete lines 28-42 entirely:

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

Leave the rest of `TestConfigurationManager` and its tests intact. If `os` becomes unused after this deletion, the next step's ruff `--fix` removes the import; if other tests still use `os` (e.g. `mocker.patch.dict("os.environ", ...)`), leave it.

- [ ] **Step 2: Run the whole file in isolation**

Run: `uv run pytest tests/unit/utils/test_configuration_manager.py -v --no-cov`
Expected: ALL pass, including `TestConfigurationManagerIntegration::test_should_handle_mixed_required_and_optional_keys`. Previously this was order-dependent: it only passed when an earlier class's destructive `del` had already removed `CHART_IMG_API_KEY`. The autouse fixture now clears it before every test regardless of order.

- [ ] **Step 3: Prove the leak is order-independent now**

Run: `uv run pytest "tests/unit/utils/test_configuration_manager.py::TestConfigurationManagerIntegration::test_should_handle_mixed_required_and_optional_keys" -q --no-cov 2>&1 | tail -5`
Expected: `1 passed`. Run in isolation (no earlier class to clear state), this previously could fail and print the real `CHART_IMG_API_KEY`. The autouse fixture clears all API-key env vars first, so `api_keys` can only contain values the test sets itself — no real secret can reach the output.

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

`TestResetResilienceConfig::test_should_reset_singleton` (line ~533) assumes the singleton starts unset. It failed under xdist when a prior test had already cached `_resilience_config`. Task 1's autouse fixture now nulls `_resilience_config` before every test, so the assumption holds regardless of order.

- [ ] **Step 1: Run the resilience test file**

Run: `uv run pytest tests/unit/config/test_resilience_config.py -v --no-cov`
Expected: ALL pass.

- [ ] **Step 2: Run it inside the broader config suite (cross-test contamination check)**

Run: `uv run pytest tests/unit/config -q --no-cov`
Expected: ALL pass — the autouse reset makes the singleton's starting state independent of any earlier test.

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

(Recipe lines use TAB indentation. `loadscope` keeps each module/class on one worker, so class-scoped fixtures stay correct. `pytest-cov` combines per-worker coverage automatically. Leave `test-verbose` and `coverage` serial.)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock Makefile
git commit -m "test: enable pytest-xdist (-n auto) for make test + coverage-check"
```

---

## Task 5: Verify reorder-safety and flakiness

**Files:** none (verification). Capture only PASS/FAIL summaries and test IDs — never dump full assertion output (secret-safety). **Run these locally where `.env` IS present** (that is the environment the order-dependence surfaces in).

- [ ] **Step 1: Full suite under xdist (loadscope) — run 1**

Run: `uv run pytest -m "not integration" --no-cov -n auto --dist=loadscope -q -rf 2>&1 | tail -8`
Expected: `N passed` (≈5167 incl. the 8 new meta-tests), `0 failed`.

- [ ] **Step 2: Run it again — run 2 (flakiness check)**

Run: `uv run pytest -m "not integration" --no-cov -n auto --dist=loadscope -q -rf 2>&1 | tail -8`
Expected: identical `0 failed`. If any test fails in run 1 or 2, note its ID, find the shared state it depends on (singleton/env/file), and reset/isolate it in `tests/conftest.py::_isolate_global_state` (or that test's own `monkeypatch`). Pay special attention to anything touching `_feature_flags` circuit-breaker state. Re-run until two consecutive clean runs.

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

- [ ] **Step 1: Update the changelog** (use the wall-clock numbers actually measured in Task 5)

In `CHANGELOG.md`, under the existing `## [Unreleased]` `### Changed` section, append:

```markdown
- **Parallel test runs (pytest-xdist).** Added an autouse isolation fixture
  (`tests/conftest.py`) that clears config-driving env vars and resets cached
  config singletons (configuration manager, settings, resilience, feature flags,
  token monitor) before every test — making the suite reorder-safe. This also
  fixes a latent order-dependent leak where a config test could read — and print
  on failure — the developer's real `.env` API keys. `make test` and the CI
  coverage gate now run with `-n auto --dist=loadscope` (≈3 min → ≈<MEASURED> min).
```

- [ ] **Step 2: Final gates**

Run: `uv run ruff check . 2>&1 | tail -3`  → Expected: `All checks passed!`
Run: `make coverage-check 2>&1 | tail -4`  → Expected: passes, coverage ≥65%.
Run: `uv run mypy src/finwiz 2>&1 | tail -2`  → Expected: `Success` (no src changes, confirm nothing regressed).

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note parallel test runs + test-isolation fix"
```

---

## Final verification (before PR)

- [ ] Two consecutive `-n auto --dist=loadscope` full runs **with `.env` present**: `0 failed`.
- [ ] `make coverage-check`: passes, coverage ≥65%, under xdist.
- [ ] Meta-tests prove the mechanism: building a `ConfigurationManager()` inside a test sees no real keys; the 5 singletons are reset before each test.
- [ ] `grep -rn "SERPER_API_KEY\|CHART_IMG_API_KEY" $(git ls-files 'tests/**') | grep -v conftest.py | grep -v test_global_isolation` — no test asserts on a real key value.
- [ ] `make test` wall-clock recorded before/after; CHANGELOG number matches the measurement.
- [ ] ruff clean; mypy clean; no `unittest.mock` introduced.

## Spec-coverage check

- Reorder-safe env clearing (sourced from code; restored via monkeypatch) → Task 1. ✅
- Reset cached singletons incl. `_settings` + `_feature_flags` → Task 1. ✅
- Secret-leak fixed (order-independent) + verified by constructing a real manager → Task 1 (meta-tests) + Task 2 (Step 3). ✅
- Remove destructive setup_method → Task 2. ✅
- Resilience reset test reorder-safe → Task 3. ✅
- Enable xdist (dep + make test + coverage-check/CI) → Task 4. ✅
- Verify reorder-safety + flakiness + gate, **locally with `.env` present** → Task 5. ✅
- CHANGELOG with measured numbers, no version bump → Task 6. ✅
- Remaining ~19 singletons: deliberately not reset; Task 5 runs are the safety net. ✅
- CI uses `make coverage-check`, so xdist + the 65% gate run in CI automatically. ✅
