# Simplification Pass 3 — Decompose + Guardrails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the worst hotspot functions (functional core / imperative shell), move pure CSS/JS out of Python into asset files, wire complexity + dead-code + duplication guardrails into the build so complexity cannot regrow, and finish the systemic doc drift — per the approved spec (`docs/superpowers/specs/2026-06-09-codebase-simplification-design.md`) and the Pass-2 Out-of-Scope leads.

**Architecture:** Behavior-preserving refactors only (existing tests are the oracle and are NOT rewritten — only patch targets may move). Decomposition before guardrails, so the grandfathered ignore list is smaller. Pure-asset extraction keeps the Python function APIs intact (functions read the file), so zero caller churn.

**Tech Stack:** Python 3.12, uv, pytest (pytest-mock ONLY — unittest.mock banned+enforced), ruff (`>=0.4.8`, select currently `E,F,W,I,UP,TID,D,S,B,RUF`), vulture (via uvx), pylint duplicate-code (via uvx), mkdocs. pytest-socket network guard active in unit suite. New .py files ≤300 lines (pre-commit; the hook only matches `\.py$`, so new .css/.js assets are exempt). Prefix shell commands with `rtk`; `rtk proxy <cmd>` for unfiltered output.

**Research facts this plan relies on (re-verify per task):**

- `reporting/css_styles.py::get_report_css()` is 333 lines of pure CSS (no f-string interpolation), single caller `reporting/python_report_generator.py` (~line 327, inlined into a `<style>` block). Same purity holds for `reporting/css/css_elements.py` (217), `reporting/css/css_layouts.py` (136), `reporting/js/javascript_code.py::get_rebalancing_javascript()` (125).
- `crews/helpers/context_preparation.py::ContextPreparationManager.get_integrated_data_context()` (236 lines, 107 statements — the repo's worst C901+PLR0915 offender): stateless orchestration of 6 loading steps over 4 injected accessors; no attribute mutation after `__init__`; covered only via mocks in `tests/unit/crews/test_report_crew_discovery_integration.py`.
- `orchestrators/deep_analysis_orchestrator.py::run_deep_analysis_concurrent()` (~line 316): contains two ~30-line nested function defs (`analyze_single_sync`, `analyze_with_timeout`) that close over injectables and can move to module level.
- Generators: `DeepAnalysisReportGenerator`, `EnrichedAnalysisReportGenerator`, `FinalReportGenerator` each duplicate the base's Jinja2 Environment setup but have genuinely different template contracts (datetime-object vs string `analysis_date`; their templates expect what they currently get) — full hierarchy migration would CHANGE behavior; only the env-setup duplication is safely extractable.
- Guardrail baselines: C901 (threshold 10) = 89 violations; PLR0915 = 27; vulture ≥80% confidence = exactly 5 findings, all trivially fixable unused variables (`integration/middleware.py:206,222` `execution_duration`; `tools/standardized_sentiment_tool.py:322,327,332` `search_term`); pylint duplicate-code at 12 lines = clean, ~30s runtime; `flow_orchestrator.py` is now 387 lines (<400) but its property test is still skipped.
- Doc drift: 13 phantom `finwiz.utils.*` modules map to real paths (table in Task 6); 2 are EXTINCT (`finwiz.utils.html_generator` — 9 function names that exist nowhere, the sole subject of `docs/reference/HTML_INTEGRATION_GUIDE.md` and most of `docs/reference/html_reports.md`; and `finwiz.utils.deep_analysis_merger.DeepAnalysisDataMerger`). `pyproject.toml` has a stale `[[tool.mypy.overrides]] module = "finwiz.utils.*"` section.

---

### Task 0: Branch setup

**Files:** none

- [ ] **Step 1: Branch from up-to-date main**

```bash
rtk git checkout main && rtk git pull && rtk git checkout -b chore/simplify-pass3-decompose
```

- [ ] **Step 2: Confirm baseline**

Run: `make check`
Expected: exit 0 (Pass 2 left it fully green). Record the `make test` summary line as the baseline count.

---

### Task 1: Extract pure CSS/JS from Python into asset files

**Files:**

- Create: `src/finwiz/reporting/assets/report_styles.css` (content of get_report_css)
- Create: `src/finwiz/reporting/assets/rebalancing_elements.css`, `src/finwiz/reporting/assets/rebalancing_layouts.css`, `src/finwiz/reporting/assets/rebalancing.js`
- Modify: `src/finwiz/reporting/css_styles.py`, `src/finwiz/reporting/css/css_elements.py`, `src/finwiz/reporting/css/css_layouts.py`, `src/finwiz/reporting/js/javascript_code.py` — each function keeps its NAME and signature but returns the asset file's content
- Test: `tests/unit/reporting/test_asset_loading.py` (new)

API stability rule: every existing function (`get_report_css`, `get_base_styles`, `get_table_styles`, `get_responsive_styles`, `get_rebalancing_javascript`, …) keeps its exact name and return type; callers are untouched. Read each source file FIRST to enumerate its actual public functions — the per-file function lists above are from research and must be confirmed.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/reporting/test_asset_loading.py
"""CSS/JS asset files load correctly through the legacy function APIs."""

from finwiz.reporting.css_styles import get_report_css


class TestReportCssAsset:
    def test_returns_nonempty_css(self):
        css = get_report_css()
        assert len(css) > 5000  # the stylesheet is ~330 lines
        assert ":root" in css  # design-token variables block
        assert "@media" in css  # responsive queries preserved

    def test_is_cached_across_calls(self):
        assert get_report_css() is get_report_css()  # functools.cache — no re-read per report
```

- [ ] **Step 2: Run to verify the cache test fails**

Run: `uv run pytest tests/unit/reporting/test_asset_loading.py -v`
Expected: `test_returns_nonempty_css` PASSES against the current string implementation; `test_is_cached_across_calls` FAILS (new strings... actually a literal may be interned — if both pass, the test still pins the contract; proceed).

- [ ] **Step 3: Snapshot the current outputs, then extract**

```bash
mkdir -p src/finwiz/reporting/assets
uv run python -c "
from finwiz.reporting.css_styles import get_report_css
from pathlib import Path
Path('src/finwiz/reporting/assets/report_styles.css').write_text(get_report_css(), encoding='utf-8')
print('snapshot written, bytes:', len(get_report_css()))
"
```

Do the same one-liner pattern for each function in `css/css_elements.py`, `css/css_layouts.py`, `js/javascript_code.py` (one asset file per FILE if its functions concatenate naturally, or one per function — match what callers consume; read the callers in `reporting/rebalancing/` first). The snapshot-from-the-running-code approach guarantees byte-identical extraction.

- [ ] **Step 4: Rewrite each Python module as a loader**

```python
# src/finwiz/reporting/css_styles.py (entire new content)
"""CSS for the production HTML report. The stylesheet lives in assets/report_styles.css."""

from functools import cache
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"


@cache
def get_report_css() -> str:
    """Return the report stylesheet (read once from assets/report_styles.css)."""
    return (_ASSETS / "report_styles.css").read_text(encoding="utf-8")
```

Mirror the pattern for the other three modules (adjust `_ASSETS` relative depth for `css/` and `js/` subpackages: `Path(__file__).parent.parent / "assets"`).

- [ ] **Step 5: Byte-identity check + tests**

```bash
uv run python -c "
from finwiz.reporting.css_styles import get_report_css
from pathlib import Path
assert get_report_css() == Path('src/finwiz/reporting/assets/report_styles.css').read_text(encoding='utf-8')
print('byte-identical')
"
uv run pytest tests/unit/reporting/test_asset_loading.py tests/unit/reporting -q | tail -1
```

Expected: byte-identical; all reporting tests pass.

- [ ] **Step 6: Check packaging**

The assets must ship with the package: check `pyproject.toml` for package-data/include configuration (hatchling/setuptools section). If only `.py` files are packaged, add the assets glob (e.g. for hatchling: `[tool.hatch.build] include` or `force-include`; report what the build backend is and what you added). Verify: `uv run python -c "import finwiz.reporting.css_styles as m; print(m.get_report_css()[:40])"` from the repo works regardless, but note the packaging change in the commit body.

- [ ] **Step 7: Validate + commit**

Run: `make test && make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "refactor(reporting): move pure CSS/JS out of Python into assets/ (byte-identical, APIs unchanged)"
```

---

### Task 2: Decompose get_integrated_data_context (functional core / imperative shell)

**Files:**

- Modify: `src/finwiz/crews/helpers/context_preparation.py`
- Test: `tests/unit/crews/test_context_preparation.py` (new — direct unit tests for the extracted loaders)
- Existing oracle: `tests/unit/crews/test_report_crew_discovery_integration.py` must keep passing unmodified

The 236-line method becomes ~6 module-level functions, each taking its dependencies explicitly; `ContextPreparationManager` and its public `get_integrated_data_context(...)` signature SURVIVE (callers untouched) — the method body becomes a thin orchestrator calling the extracted functions. Read the method in full first; the section boundaries below are from research (verify line ranges):

| New module-level function | Extracted from (approx) | Inputs |
|---|---|---|
| `_load_reporter_input(data_accessor, max_age_hours)` | lines ~51–60 | accessor, int |
| `_track_crew_availability(integrated_data, availability_tracker)` | lines ~70–103 (the repetitive stock/etf/crypto block — collapse the 3 copies into one loop over `("stock", "etf", "crypto")`) | dict, tracker |
| `_track_portfolio_stats(integrated_data, availability_tracker)` | lines ~105–142 | dict, tracker |
| `_load_discovery_data(discovery_accessor, inputs, availability_tracker)` | lines ~152–212 | accessor, dict, tracker |
| `_load_backtesting_data(backtesting_extractor, inputs, availability_tracker)` | lines ~215–242 | extractor, dict, tracker |
| `_summarize_availability(availability_tracker)` | lines ~244–278 | tracker |

- [ ] **Step 1: Write failing tests for two extracted loaders (representative pair — one pure-ish, one accessor-driven)**

```python
# tests/unit/crews/test_context_preparation.py
"""Direct unit tests for the decomposed context-preparation loaders."""

from finwiz.crews.helpers.context_preparation import (
    _load_discovery_data,
    _track_crew_availability,
)


class TestTrackCrewAvailability:
    def test_marks_present_crews_available(self, mocker):
        tracker = mocker.MagicMock()
        integrated = {"stock_data": {"x": 1}, "etf_data": None, "crypto_data": {}}

        _track_crew_availability(integrated, tracker)

        # one tracker call per asset class; presence judged by truthiness —
        # ADJUST these assertions to mirror exactly what the original inline
        # block did per crew (read it first; the test pins current behavior)
        assert tracker.method_calls  # placeholder-level assert is NOT acceptable: assert the real calls


class TestLoadDiscoveryData:
    def test_uses_accessor_and_tracks(self, mocker):
        accessor = mocker.MagicMock()
        accessor.get_discovery_data.return_value = {"opportunities": []}
        tracker = mocker.MagicMock()

        result = _load_discovery_data(accessor, inputs={}, availability_tracker=tracker)

        accessor.get_discovery_data.assert_called_once()
        assert result == {"opportunities": []}
```

IMPORTANT: before finalizing these tests, read the original code blocks and make the assertions mirror the ACTUAL accessor method names and tracker calls — the snippets above show the shape, the original code is the source of truth. Tests must pin current behavior, not invented behavior.

- [ ] **Step 2: Run — must fail (functions don't exist)**

Run: `uv run pytest tests/unit/crews/test_context_preparation.py -v 2>&1 | tail -3`
Expected: ImportError.

- [ ] **Step 3: Extract the six functions**

Move each block verbatim into its module-level function (parameterize `self.X` → explicit args). Collapse the stock/etf/crypto triplication into one loop. Then shrink the method to:

```python
def get_integrated_data_context(self, max_age_hours: int = 24, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the consolidated crew-data context (thin orchestrator over module-level loaders)."""
    self.availability_tracker.clear()
    integrated_data = _load_reporter_input(self.data_accessor, max_age_hours)
    _track_crew_availability(integrated_data, self.availability_tracker)
    _track_portfolio_stats(integrated_data, self.availability_tracker)
    integrated_data["discovery"] = _load_discovery_data(self.discovery_accessor, inputs or {}, self.availability_tracker)
    integrated_data["backtesting"] = _load_backtesting_data(self.backtesting_extractor, inputs or {}, self.availability_tracker)
    integrated_data["availability_summary"] = _summarize_availability(self.availability_tracker)
    return integrated_data
```

(Adapt key names/return wiring to EXACTLY what the original produced — the dict shape is the contract. Keep the original try/except placement: if the whole method body was wrapped, wrap the orchestrator body the same way.)

- [ ] **Step 4: All tests green**

Run: `uv run pytest tests/unit/crews -q 2>&1 | tail -1`
Expected: PASS including the untouched `test_report_crew_discovery_integration.py`.

- [ ] **Step 5: Confirm the complexity win**

Run: `uvx ruff check src/finwiz/crews/helpers/context_preparation.py --select C901,PLR0915 2>/dev/null`
Expected: zero violations (was the repo's worst: 3).

- [ ] **Step 6: Validate + commit**

Run: `make test && make check`

```bash
rtk git add -A && rtk git commit -m "refactor(crews): decompose get_integrated_data_context into module-level loaders (236 lines -> thin orchestrator; behavior pinned by new unit tests)"
```

---

### Task 3: Extract nested helpers from run_deep_analysis_concurrent

**Files:**

- Modify: `src/finwiz/orchestrators/deep_analysis_orchestrator.py` (~lines 316–469)
- Existing oracle: `tests/unit/orchestrators/test_deep_analysis_orchestrator.py` (and any other file matching `grep -rln "run_deep_analysis_concurrent" tests`)

- [ ] **Step 1: Read the method in full**

Identify the two nested defs (`analyze_single_sync` ~lines 349–378, `analyze_with_timeout` ~lines 391–423) and EVERY variable they close over (prefetched data, ledger, semaphore, executor, loop, timeout, logger, self.\*). Anything from `self` becomes an explicit parameter.

- [ ] **Step 2: Move them to module level in the same file**

```python
def _analyze_single_sync(holding: ..., prefetched_data: ..., ledger: ..., logger: ...) -> tuple[str, DeepAnalysisResult | None, Any | None]:
    """Synchronous per-holding analysis (runs inside the thread pool)."""
    # body moved verbatim; closures replaced by parameters


async def _analyze_with_timeout(holding, *, executor, semaphore, loop, timeout_seconds, prefetched_data, ledger, logger):
    """Per-holding timeout wrapper around _analyze_single_sync."""
    # body moved verbatim
```

(Exact signatures come from the closure audit in Step 1 — list them in the commit body.) The method keeps its name, signature, and orchestration logic; it now calls the module-level helpers. Per-unit timeout semantics are UNTOUCHED (project memory: per-item timeouts, never aggregate).

- [ ] **Step 3: Tests green**

Run: `uv run pytest tests/unit/orchestrators -q 2>&1 | tail -1` then `uvx ruff check src/finwiz/orchestrators/deep_analysis_orchestrator.py --select C901,PLR0915`
Expected: tests pass; complexity violations for this file reduced (report before/after counts).

- [ ] **Step 4: Validate + commit**

Run: `make test && make check`

```bash
rtk git add -A && rtk git commit -m "refactor(orchestrators): hoist nested analysis helpers out of run_deep_analysis_concurrent (closures -> explicit params)"
```

---

### Task 4: Extract shared Jinja2 environment setup across report generators

**Files:**

- Modify: `src/finwiz/reporting/base_report_generator.py` (extract its env construction into a module-level function)
- Modify: `src/finwiz/reporting/deep_analysis_report_generator.py`, `enriched_analysis_report_generator.py`, `final_report_generator.py` (use it)
- Existing oracles: `tests/unit/reporting/test_deep_analysis_report_generator.py`, `tests/property/test_enriched_analysis_report_properties.py`, the FinalReportGenerator test file, `tests/unit/reporting/test_crew_report_generators.py`

SCOPE FENCE (from research): the three standalones have genuinely different template contracts (their templates expect datetime objects where the base emits strings) — do NOT migrate them into the BaseReportGenerator hierarchy and do NOT touch their `analysis_date` handling. Extract ONLY the duplicated Environment construction.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/unit/reporting/test_asset_loading.py or a new tests/unit/reporting/test_jinja_env_factory.py
"""Shared Jinja2 environment factory used by all report generators."""

from finwiz.reporting.base_report_generator import create_report_jinja_env


class TestCreateReportJinjaEnv:
    def test_env_is_configured_for_reports(self, tmp_path):
        env = create_report_jinja_env(tmp_path)
        assert env.autoescape  # security: HTML auto-escaping stays on
        assert env.trim_blocks and env.lstrip_blocks
```

- [ ] **Step 2: Run — fails (function doesn't exist)**

- [ ] **Step 3: Implement + adopt**

```python
# in base_report_generator.py (module level, above the class)
def create_report_jinja_env(template_dir: Path | str) -> Environment:
    """Jinja2 environment with the report-rendering configuration shared by all generators."""
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,  # Security: auto-escape HTML
        trim_blocks=True,
        lstrip_blocks=True,
    )
```

BaseReportGenerator.**init** uses it; each standalone replaces its inline `Environment(...)` block with `self.env = create_report_jinja_env(<its existing template_dir>)`. CAUTION: first diff each standalone's current Environment kwargs against the base's — if any standalone sets a DIFFERENT kwarg (e.g. no autoescape, extra extensions), it is NOT a drop-in: keep that one inline and report the divergence instead of normalizing it (normalizing autoescape would change rendered output).

- [ ] **Step 4: All generator tests green**

Run: `uv run pytest tests/unit/reporting tests/property/test_enriched_analysis_report_properties.py -q 2>&1 | tail -1`

- [ ] **Step 5: Validate + commit**

Run: `make test && make check`

```bash
rtk git add -A && rtk git commit -m "refactor(reporting): single create_report_jinja_env factory; standalones keep their own template contracts"
```

---

### Task 5: Wire complexity, dead-code, and duplication guardrails into the build

**Files:**

- Modify: `pyproject.toml` (`[tool.ruff.lint]` select + grandfathered per-file-ignores; remove stale mypy `finwiz.utils.*` override while in the file)
- Modify: `src/finwiz/integration/middleware.py` (~lines 206, 222) + `src/finwiz/tools/standardized_sentiment_tool.py` (~lines 322, 327, 332) — fix the 5 vulture-confirmed unused variables instead of whitelisting them
- Modify: `Makefile` (new targets `lint-complexity`, `deadcode`, `check-duplication`; wire into `check` and `all`)
- Test: the make targets themselves are the test

- [ ] **Step 1: Fix the 5 real unused variables**

Read each site: `execution_duration` (middleware 206/222) and `search_term` (sentiment tool 322/327/332). If the value is computed-but-unused, delete the assignment; if the name is needed for tuple unpacking, rename to `_`. Run the two files' covering tests after.

- [ ] **Step 2: Add complexity rules with mechanical grandfathering**

In `pyproject.toml` `[tool.ruff.lint]`: add `"C901", "PLR0915"` to `select`. Then generate the grandfather list mechanically:

```bash
uv run ruff check src/finwiz --select C901,PLR0915 --output-format concise 2>/dev/null | cut -d: -f1 | sort -u
```

For each file in that output, add to `[tool.ruff.lint.per-file-ignores]`:

```toml
# --- Complexity grandfathering (Pass 3): shrink this list, never grow it ---
"src/finwiz/<file>.py" = ["C901", "PLR0915"]
```

(Only the rule the file actually violates — split C901-only vs both using two greps.) After Tasks 2–3, `context_preparation.py` and possibly `deep_analysis_orchestrator.py` must NOT need entries — verify. Then: `uv run ruff check . 2>&1 | tail -2` → "All checks passed!". The headline comment above the block is required — it's the contract that the list only shrinks.

- [ ] **Step 3: Add the Makefile targets**

```makefile
lint-complexity:
 @echo "🧠 Checking cyclomatic complexity (C901) and statement counts (PLR0915)..."
 @uv run ruff check src/finwiz --select C901,PLR0915
 @echo "✅ Complexity within limits (grandfathered files listed in pyproject per-file-ignores)"

deadcode:
 @echo "🦅 Scanning for dead code (vulture, min confidence 80)..."
 @uvx vulture src/finwiz --min-confidence 80
 @echo "✅ No dead code found"

check-duplication:
 @echo "👯 Checking for duplicate code (pylint, min 12 similar lines)..."
 @uvx pylint --disable=all --enable=duplicate-code --min-similarity-lines=12 --score=no src/finwiz
 @echo "✅ No duplication found"
```

(Verify vulture exits non-zero on findings — it does; pylint exits non-zero on messages.) Wire them: `check: lint lint-complexity test check-unittest-mock check-file-size docs-validate check-stage-contract deadcode` (deadcode is ~2s, fine in check; duplication is ~30s, so it goes in `all` ONLY: append `check-duplication` to the `all` chain). Also add all three to `.PHONY`.

- [ ] **Step 4: Unskip the flow_orchestrator size property test**

`tests/property/test_file_size_properties.py`: `flow_orchestrator.py` is now 387 lines (<400) — remove the `@pytest.mark.skip` from `test_flow_orchestrator_file_size_constraint` and run it. If it passes, keep it unskipped; if the OTHER skipped test (`test_orchestrator_module_file_size_constraint`) still fails on grandfathered orchestrators, leave it skipped and note the current line counts in your report.

- [ ] **Step 5: Remove the stale mypy override**

In `pyproject.toml`, delete the `[[tool.mypy.overrides]]` block with `module = "finwiz.utils.*"` (the namespace contains no Python). Run `make mypy` → still green.

- [ ] **Step 6: Validate + commit**

Run: `make lint-complexity && make deadcode && make check-duplication && make test && make check`
Expected: all green.

```bash
rtk git add -A && rtk git commit -m "build: complexity (C901/PLR0915 grandfathered), dead-code, and duplication guardrails in make; fix 5 vulture-confirmed unused vars; drop stale finwiz.utils mypy override"
```

---

### Task 6: Finish the finwiz.utils doc drift (13 repoints, 2 extinct APIs)

**Files:**

- Modify (mechanical repoints): `docs/explanations/DATA_QUALITY_AND_FLOW_GUIDE.md`, `DEEP_ANALYSIS_INTEGRATION.md`, `REPORT_AGGREGATION_DEVELOPER_GUIDE.md`, `docs/development/DEVELOPER_GUIDE.md`, `docs/how-to/BATCH_PROCESSING.md`, `MEMORY_MANAGEMENT.md`, `PERFORMANCE_CONFIGURATION.md`, `PYTHON_SCORING_ENGINE.md`, `template_configuration.md`, `docs/LLM_CONFIGURATION.md`, `docs/setup/LLM_CONFIG_COMPLETE.md`, `docs/setup/REPORT_GENERATION_FIXES.md`, `docs/reference/mypy-configuration-review.md`
- Delete or rewrite (extinct API): `docs/reference/HTML_INTEGRATION_GUIDE.md` (entirely about the extinct `finwiz.utils.html_generator` functions), the extinct portions of `docs/reference/html_reports.md`

**The migration map (ground-truthed at research time — re-verify each import you write by checking the symbol exists at the target):**

| Phantom | Real module |
|---|---|
| `finwiz.utils.data_quality_metrics` | `finwiz.validation.quality_metrics` (or `finwiz.schemas.hybrid_analysis.metadata` — pick whichever exports the symbol used in the snippet) |
| `finwiz.utils.performance_monitor` | `finwiz.infrastructure.monitoring.performance` (verify vs `.core`) |
| `finwiz.utils.memory_manager` | `finwiz.infrastructure.monitoring.memory_manager` |
| `finwiz.utils.batch_data_prefetcher` | `finwiz.integration.batch_data_prefetcher` |
| `finwiz.utils.llm_config` | `finwiz.config.llm.llm_config` |
| `finwiz.utils.performance_config` | `finwiz.config.performance.performance_config` |
| `finwiz.utils.agent_validators` | `finwiz.infrastructure.decorators.agent_validators` |
| `finwiz.utils.task_decorators` | `finwiz.infrastructure.decorators.task_decorators` |
| `finwiz.utils.logging_helpers` | `finwiz.infrastructure.logging.helpers` |
| `finwiz.utils.url_validator` | `finwiz.validation.url` |
| `finwiz.utils.consolidation_validator` / `data_consolidation_validator` | `finwiz.validation.consolidation` |
| `finwiz.utils.report_data_validator` | `finwiz.validation.report_data` |
| `finwiz.utils.report_consolidator` | `finwiz.reporting.consolidator` |
| `finwiz.utils.template_renderer` | `finwiz.reporting.rebalancing.template_renderers` |
| `finwiz.utils.html_generator` (9 symbols) | **EXTINCT** — the real HTML path is `finwiz.reporting.html_auto_generator.auto_generate_html` + `finwiz.reporting.python_report_generator` |
| `finwiz.utils.deep_analysis_merger.DeepAnalysisDataMerger` | **EXTINCT** — nearest live concept: `finwiz.crews.helpers.data_integration_helpers.ContextMerger` (verify before substituting; otherwise delete the snippet) |

- [ ] **Step 1: Mechanical repoints with per-symbol verification**

For each doc file, replace the phantom import lines per the table. For EVERY rewritten import, verify: `uv run python -c "from <real.module> import <Symbol>"` (or grep the symbol at the target if import has side effects). A repoint that doesn't import = treat the snippet as extinct (Step 2 handling).

- [ ] **Step 2: The extinct-API reference pages**

`docs/reference/HTML_INTEGRATION_GUIDE.md`: every documented function is fiction. DELETE the page + any mkdocs nav entry + inbound links (`grep -rn "HTML_INTEGRATION_GUIDE" docs mkdocs.yml`), and ensure `docs/reference/html_reports.md` (after cutting its extinct sections) covers the REAL API: `auto_generate_html(json_path)` and the `make html-reports`/`html-convert` targets. If html_reports.md ends up gutted too, consolidate the surviving real content into one accurate page and delete the other — judgment call, document it in the commit body. `setup/REPORT_GENERATION_FIXES.md`'s `template_renderer` ref: repoint per the table.

- [ ] **Step 3: Acceptance sweep**

```bash
rtk proxy grep -rn "finwiz\.utils\." docs pyproject.toml | grep -v superpowers
```

Expected: EMPTY (the namespace is fully retired from docs and config — the mypy override went in Task 5; if it's still present do it here).

- [ ] **Step 4: Validate + commit**

Run: `uv run mkdocs build --strict 2>&1 | tail -2` then `make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "docs: retire the phantom finwiz.utils namespace (13 modules repointed, extinct html_generator API docs removed)"
```

---

### Task 7: Final validation + PR

**Files:** none

- [ ] **Step 1: Full gate**

Run: `make check && make all && make coverage`
Expected: exit 0 each (note `make all` now includes check-duplication); coverage ≥ 65%.

- [ ] **Step 2: Measure**

```bash
rtk proxy git diff --stat main...HEAD | tail -2
uvx ruff check src/finwiz --select C901,PLR0915 --output-format concise 2>/dev/null | wc -l   # must be 0 (all grandfathered or fixed)
```

- [ ] **Step 3: Push + PR**

```bash
rtk git push -u origin chore/simplify-pass3-decompose
gh pr create --title "refactor: simplification pass 3 — decompose hotspots, extract assets, complexity guardrails" --body "<summary: CSS/JS assets (byte-identical), context_preparation + deep-analysis decomposition, shared Jinja env factory, C901/PLR0915+vulture+duplication guardrails with shrink-only grandfathering, finwiz.utils docs retired; test plan with gate results>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

- [ ] **Step 4: USER GATE — `crewai flow kickoff`**

Required before merge. The report's APPEARANCE is the thing to eyeball this time (CSS/JS now load from asset files): confirm the HTML report renders styled exactly as before.

---

## Out of Scope (recorded, not done)

- Migrating Deep/Enriched/Final generators into the BaseReportGenerator hierarchy (template contracts genuinely differ; revisit only with template changes in scope)
- Converting other stateless `*Manager` classes (ConfigurationManager, AlertManager, …) to module functions — churn outweighs payoff until something else touches them
- Jinja2-templating the f-string HTML builders (`portfolio_holdings_html_generator.py` 617 lines, `rebalancing_html_builders.py` 487) — real interpolation, needs template design, not mechanical
- The other large-function P2/P3 candidates from research (`_deserialize_value` 279, `_is_crypto_symbol` 243, `_read_csv_holdings` 229, …) — grandfathered under the new guardrails; shrink opportunistically
- Writing real content for thin reference docs; the `sentiment_confidence` dead-write contract cleanup; the `EnhancedTechnicalAnalysisInput` quantitative twin
