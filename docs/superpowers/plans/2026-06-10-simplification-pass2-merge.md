# Simplification Pass 2 — Merge (DRY) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse duplicate/stub/orphaned tools into single canonical implementations and close out the Pass-2 leads, per the approved spec (`docs/superpowers/specs/2026-06-09-codebase-simplification-design.md`).

**Architecture:** Same verify-then-act discipline as Pass 1, but this pass ALLOWS targeted behavior-affecting merges where evidence is strong (each gets a justification and test coverage). One canonical sentiment tool; stub tools deleted and dewired; a small shared JSON-error helper for `_run` methods applied to the worst offenders only (mixed return conventions across 39 tools make a universal wrapper wrong — YAGNI).

**Tech Stack:** Python 3.12, uv, pytest (pytest-mock ONLY — unittest.mock is banned and enforced), ruff, mkdocs. `make check` after every task. Prefix shell commands with `rtk`; use `rtk proxy <cmd>` for unfiltered output. New files must be ≤300 lines (pre-commit hook).

**Research facts this plan relies on (re-verify in each task):**

- `StandardizedSentimentAnalysisTool` (tools/standardized_sentiment_tool.py, 612 lines, returns dict) is wired into ALL crew toolsets via finance_tools.py lines ~69/100/127/151/179. `EnhancedSentimentAnalysisTool` (tools/enhanced_sentiment_tool.py, returns JSON string) is used in exactly ONE place: `orchestrators/deep_analysis_data_collector.py` `_collect_sentiment_data()` (~line 321), which parses the JSON and extracts numeric fields only.
- Stub tools that return "use the other tool" placeholder dicts: `CryptoThesisGeneratorTool` + `CryptoRiskScoringTool` (enhanced_crypto_tool.py:504–545) and `ETFTrackingAnalysisTool` (enhanced_etf_tool.py:179–199). All three are instantiated in finance_tools.py (crypto: ~88–96; etf: ~118–134).
- Orphans (zero crew/factory wiring): `tools/sentiment_analyzer.py` (501 lines, utility class), `tools/enhanced_technical_analyzer_tool.py` (270) + its only dependency `tools/technical_analyzer.py` (75).
- NOT duplicates (keep all): `EnhancedSECAnalysisTool` vs `StandardizedRiskScoringTool` (separate concerns); `EnhancedETFAnalysisTool` (fetching+Perplexity) vs `ETFAnalysisTool` (metrics on pre-fetched data).
- `GradeInfo.css_class` (scoring/grading_system.py:24, populated at 8 sites in `score_to_grade`) is write-only; HTML rendering uses `reporting/sections/common.py::grade_css_class()` which recomputes independently.
- `is_feature_enabled("batch_prefetch")` exists ONLY as an example in `src/finwiz/config/CLAUDE.md:63` — no code call site. Unknown flags return False with a logged warning (flags.py `is_enabled`).
- Self-validating flag loop: flags `chart_analysis`, `enhanced_sentiment_analysis`, `twelve_data_integration` are queried ONLY by `config/manager.py:332–349 _validate_feature_flag_consistency()`, whose entire effect is a startup `logger.warning` when a flag is on but its API key is missing. The flags gate no functionality.
- `FeatureFlagStrategy.USER_LIST` and `TIME_WINDOW` enum members are used by no flag definition; evaluators.py has handling branches (~lines 52/55) with tests.
- 15 pre-existing broken doc link targets: fictional example links in `docs/maintenance/{content-creation-guide,content-governance,troubleshooting-guide,style-guide}.md` (some in style-guide are INTENTIONAL examples) and never-created pages linked from `docs/reference/index.md` (`api/analysis.md`, `api/scoring.md`, `api/reporting.md`, `schemas/crew_exports.md`, …). Also `docs/development/DEVELOPER_GUIDE.md:1809` references nonexistent `.github/workflows/ci.yml` (real workflows: docs.yml, quality.yml, osv-scanner.yml, supply-chain.yml).

---

### Task 0: Branch setup

**Files:** none

- [ ] **Step 1: Branch from up-to-date main**

```bash
rtk git checkout main && rtk git pull && rtk git checkout -b chore/simplify-pass2-merge
```

- [ ] **Step 2: Confirm baseline**

Run: `make check`
Expected: exit 0 (Pass 1 left it fully green, including docs-lint).

---

### Task 1: Delete the three stub tools and dewire them

**Files:**

- Modify: `src/finwiz/tools/enhanced_crypto_tool.py` (delete `CryptoThesisGeneratorTool`, `CryptoRiskScoringTool` classes, ~lines 504–545)
- Modify: `src/finwiz/tools/enhanced_etf_tool.py` (delete `ETFTrackingAnalysisTool` class, ~lines 179–199)
- Modify: `src/finwiz/tools/finance_tools.py` (remove imports + instantiations)
- Modify: any crew YAML/test that names the stubs

These stubs do nothing: their `_run` returns a placeholder dict telling the agent to use the Enhanced tool instead. Registering them in crews wastes agent tool-choice attention.

- [ ] **Step 1: Verify the stubs are stubs and enumerate references**

```bash
rtk proxy sed -n '504,545p' src/finwiz/tools/enhanced_crypto_tool.py
rtk proxy sed -n '179,199p' src/finwiz/tools/enhanced_etf_tool.py
rtk proxy grep -rn "CryptoThesisGeneratorTool\|CryptoRiskScoringTool\|ETFTrackingAnalysisTool\|Crypto Thesis Generator Tool\|Crypto Risk Scoring Tool\|ETF Tracking Analysis Tool" src/finwiz tests docs --include='*' | grep -v superpowers
```

Expected: the class bodies are placeholder returns; references only in the defining files, finance_tools.py, possibly tests and crew YAML task descriptions. If a stub's `_run` contains REAL logic, STOP and report.

- [ ] **Step 2: Delete the classes and dewire**

Remove the three class definitions. In `finance_tools.py`: remove their imports and the instantiation lines from `get_crypto_research_tools()` and `get_etf_research_tools()` (keep `EnhancedCryptoAnalysisTool` and `EnhancedETFAnalysisTool`). Remove any input-schema classes used ONLY by the stubs from `schemas/tools/inputs.py` + its `__init__.py` exports (verify each schema has no other consumer first).

- [ ] **Step 3: Clean tests and YAML mentions**

For each test that exercises a stub: delete that test method (not the file). For crew YAML task descriptions mentioning the stub tool names: rewrite the sentence to reference the surviving Enhanced tool.

- [ ] **Step 4: Validate**

Run: `make test` then `make check`
Expected: green. A failure naming a stub class means a missed reference — fix it.

- [ ] **Step 5: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: delete placeholder stub tools (CryptoThesisGenerator, CryptoRiskScoring, ETFTracking) and dewire from crews"
```

---

### Task 2: Delete orphaned analyzer modules

**Files:**

- Delete: `src/finwiz/tools/sentiment_analyzer.py` (501 lines)
- Delete: `src/finwiz/tools/enhanced_technical_analyzer_tool.py` (270 lines)
- Delete: `src/finwiz/tools/technical_analyzer.py` (75 lines — only consumer is the file above)
- Delete: their dedicated test files (locate in Step 1)

- [ ] **Step 1: Verify zero production wiring**

```bash
for m in sentiment_analyzer enhanced_technical_analyzer_tool technical_analyzer; do
  echo "== $m"
  rtk proxy grep -rn "$m\|$(echo $m | sed 's/_//g')" src/finwiz --include='*.py' | grep -v "tools/$m.py" | grep -v "tools/enhanced_technical_analyzer_tool.py"
done
rtk proxy grep -rn "SentimentAnalyzer\b\|TechnicalAnalyzer\b\|EnhancedTechnicalAnalyzerTool" src/finwiz tests --include='*.py' | grep -v "tools/sentiment_analyzer.py\|tools/technical_analyzer.py\|tools/enhanced_technical_analyzer_tool.py"
```

Expected: hits only in dedicated test files (delete those too) and possibly `tools/__init__.py` lazy exports (remove those lines). CAUTION: `TechnicalAlgorithms` and `TechnicalPatterns` (technical_algorithms.py / technical_patterns.py) are SEPARATE modules — if the deep-analysis quantitative path imports them directly, they are ALIVE; only `technical_analyzer.py` (the thin `TechnicalAnalyzer` wrapper) is the orphan. Verify `technical_algorithms.py` has consumers outside the deleted files before assuming anything. Any production import of the three target modules = STOP and report.

- [ ] **Step 2: Delete modules + dedicated tests + **init** exports**

```bash
rtk git rm src/finwiz/tools/sentiment_analyzer.py src/finwiz/tools/enhanced_technical_analyzer_tool.py src/finwiz/tools/technical_analyzer.py
rtk proxy grep -rln "sentiment_analyzer\|enhanced_technical_analyzer\|technical_analyzer" tests --include='*.py' | xargs -r rtk git rm
```

Then remove their entries from `src/finwiz/tools/__init__.py` and `tools/CLAUDE.md` if present.

- [ ] **Step 3: Validate + straggler grep**

Run: `make test && make check`
Then: `rtk proxy grep -rn "sentiment_analyzer\|technical_analyzer" src docs mkdocs.yml | grep -v superpowers | grep -v technical_algorithms` → expected empty.

- [ ] **Step 4: Commit**

```bash
rtk git add -A && rtk git commit -m "chore: delete orphaned analyzer modules (sentiment_analyzer, technical_analyzer wrapper, enhanced_technical_analyzer_tool)"
```

---

### Task 3: Unify sentiment on StandardizedSentimentAnalysisTool

**Files:**

- Modify: `src/finwiz/orchestrators/deep_analysis_data_collector.py` `_collect_sentiment_data()` (~line 321)
- Delete: `src/finwiz/tools/enhanced_sentiment_tool.py` + `tests/unit/tools/test_enhanced_sentiment_tool.py`
- Modify: `src/finwiz/schemas/tools/inputs.py` (delete `EnhancedSentimentInput`, ~lines 117–123) + `schemas/tools/__init__.py` exports
- Possibly delete: `tools/sentiment_formatting.py` (+ parts of `sentiment_calculations.py`/`sentiment_sources.py`) if orphaned afterward — verified in Step 6
- Test: `tests/unit/orchestrators/test_deep_analysis_data_collection.py` (existing collector tests — update mocks)

**DOCUMENTED BEHAVIOR CHANGE:** deep-analysis sentiment scores will come from the standardized rule-based scorer instead of the enhanced weighted scorer. Same −1..1 scale (verify in Step 1); values will shift. Justification: one sentiment methodology across crews and deep analysis (the spec's DRY goal); the standardized tool has stricter no-hallucination guarantees. Goes in the commit body and PR description.

- [ ] **Step 1: Read both sides of the seam**

Read `deep_analysis_data_collector.py::_collect_sentiment_data` in full: what keys does it put into the collected-data dict (e.g. `sentiment_score`, `overall_sentiment`, `sentiment_confidence`, `sentiment_analysis`) and who consumes them downstream (grep each key in `scoring/deep_analysis_scorer.py`, `analysis/`). Read `StandardizedSentimentAnalysisTool._run` output dict keys (`mean_score`, `weighted_score`, `confidence_interval`, `counts`, …) and CONFIRM the score scale is −1..1 (read `_calculate_article_sentiment` and `_calculate_sentiment_metrics`). If scales differ, STOP and report.

- [ ] **Step 2: Write the failing test for the new collector behavior**

In `tests/unit/orchestrators/test_deep_analysis_data_collection.py`, add (adjust names to the file's existing conventions and fixtures):

```python
def test_collect_sentiment_uses_standardized_tool(mocker):
    """Sentiment collection delegates to StandardizedSentimentAnalysisTool and maps its dict output."""
    fake_result = {
        "symbol": "AAPL",
        "asset_class": "stock",
        "weighted_score": 0.42,
        "mean_score": 0.40,
        "confidence_interval": [0.30, 0.54],
        "counts": {"pos": 6, "neu": 3, "neg": 1},
        "articles_analyzed": 10,
        "trending_topics": [],
        "top_pos": [],
        "top_neg": [],
    }
    mock_tool = mocker.patch(
        "finwiz.orchestrators.deep_analysis_data_collector.StandardizedSentimentAnalysisTool"
    )
    mock_tool.return_value._run.return_value = fake_result

    collector = DeepAnalysisDataCollector()
    data = collector._collect_sentiment_data("AAPL", "stock")

    mock_tool.return_value._run.assert_called_once_with(
        symbol="AAPL", asset_class="stock", max_articles=20, days_back=30
    )
    assert data["sentiment_score"] == 0.42
    assert data["overall_sentiment"] in {"positive", "bullish"}  # match the file's existing label convention
    assert 0.0 <= data["sentiment_confidence"] <= 1.0
```

Match the patch target to how the collector imports the tool (module-level import recommended — patch where it's looked up). Reuse the file's existing collector fixture if one exists.

- [ ] **Step 3: Run it — must fail**

Run: `uv run pytest tests/unit/orchestrators/test_deep_analysis_data_collection.py -k standardized -v`
Expected: FAIL (collector still uses the enhanced tool).

- [ ] **Step 4: Rewire the collector**

In `_collect_sentiment_data`, replace the enhanced-tool call:

```python
from finwiz.tools.standardized_sentiment_tool import StandardizedSentimentAnalysisTool  # move to module-level imports

result = StandardizedSentimentAnalysisTool()._run(
    symbol=ticker, asset_class=asset_class, max_articles=20, days_back=30
)
score = float(result.get("weighted_score") or result.get("mean_score") or 0.0)
counts = result.get("counts") or {}
total = max(1, sum(counts.values()))
data["sentiment_score"] = score
data["overall_sentiment"] = "positive" if score > 0.1 else "negative" if score < -0.1 else "neutral"  # keep the file's existing label set
data["sentiment_confidence"] = round(max(counts.values(), default=0) / total, 2)
data["sentiment_analysis"] = result
```

Adapt key names/labels to what Step 1 found downstream consumers expect — preserve the collector's OUTPUT contract exactly; only the upstream tool changes. No JSON parsing needed (dict in, dict out). Keep the existing try/except shape of the method.

- [ ] **Step 5: Run the test + the full collector/scorer suites**

Run: `uv run pytest tests/unit/orchestrators/test_deep_analysis_data_collection.py tests/unit/orchestrators/test_beta_extraction.py tests/unit/tools/test_perplexity_feature_flag_integration.py tests/unit/tools/test_perplexity_multi_tool_integration.py -v 2>&1 | tail -15`
Expected: PASS. These four files referenced the enhanced tool at planning time — update their mocks/imports to the standardized tool where they patched the enhanced one.

- [ ] **Step 6: Delete the enhanced tool and check the helper-module fallout**

```bash
rtk git rm src/finwiz/tools/enhanced_sentiment_tool.py tests/unit/tools/test_enhanced_sentiment_tool.py
```

Remove `EnhancedSentimentInput` from `schemas/tools/inputs.py` and `schemas/tools/__init__.py`. Then check the recursive-orphan pattern:

```bash
for m in sentiment_formatting sentiment_calculations sentiment_sources; do
  echo "== $m"; rtk proxy grep -rln "$m" src/finwiz tests --include='*.py' | grep -v "tools/$m.py"
done
```

Any of the three with hits ONLY in its own test file → delete module + test (list in commit body). Any with live consumers → keep.

- [ ] **Step 7: Validate**

Run: `make test && make check`
Then straggler grep: `rtk proxy grep -rn "EnhancedSentimentAnalysisTool\|enhanced_sentiment_tool\|EnhancedSentimentInput" src tests docs mkdocs.yml .env.example | grep -v superpowers` → expected empty (clean up doc mentions found, e.g. in tools/CLAUDE.md).

- [ ] **Step 8: Commit**

```bash
rtk git add -A && rtk git commit -m "refactor: unify sentiment analysis on StandardizedSentimentAnalysisTool

Deep-analysis sentiment now uses the same rule-based scorer as the crews
(one methodology, stricter no-hallucination guarantees). Scores shift
within the same -1..1 scale; collector output contract unchanged."
```

---

### Task 4: Shared JSON error/serialization helper for `_run` methods

**Files:**

- Create: `src/finwiz/tools/run_helpers.py` (small — well under the 300-line new-file limit)
- Test: `tests/unit/tools/test_run_helpers.py`
- Modify (migration, top payoff only): `tools/risk_assessment_tool.py`, `tools/backtesting_tool.py`, `tools/portfolio_analysis_tool.py`, `tools/quantitative_analysis_tool.py`, `tools/valuation_tool.py`

Scope discipline: 39 tools have THREE return conventions (plain str, JSON str, dict). A universal wrapper would force churn for no benefit (YAGNI). This task standardizes only the JSON-STRING-returning tools' duplicated success/error envelopes.

- [ ] **Step 1: Write failing tests for the helpers**

```python
# tests/unit/tools/test_run_helpers.py
"""Tests for the shared _run JSON envelope helpers."""

import json

from finwiz.tools.run_helpers import json_error, json_ok


class TestJsonOk:
    def test_serializes_dict_with_default_str(self):
        from datetime import UTC, datetime

        payload = {"when": datetime(2026, 1, 1, tzinfo=UTC), "value": 1.5}
        out = json_ok(payload)
        parsed = json.loads(out)
        assert parsed["value"] == 1.5
        assert "2026-01-01" in parsed["when"]

    def test_output_is_indented(self):
        assert "\n" in json_ok({"a": 1})


class TestJsonError:
    def test_wraps_exception_with_type_and_context(self):
        out = json_error(ValueError("bad ticker"), ticker="AAPL")
        parsed = json.loads(out)
        assert parsed["success"] is False
        assert parsed["error"] == "bad ticker"
        assert parsed["error_type"] == "ValueError"
        assert parsed["ticker"] == "AAPL"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/unit/tools/test_run_helpers.py -v`
Expected: FAIL with ModuleNotFoundError.

- [ ] **Step 3: Implement the helpers**

```python
# src/finwiz/tools/run_helpers.py
"""Shared JSON envelope helpers for tool _run methods that return JSON strings."""

import json
from typing import Any


def json_ok(payload: dict[str, Any]) -> str:
    """Serialize a tool success payload (handles datetimes and other non-JSON types)."""
    return json.dumps(payload, indent=2, default=str)


def json_error(exc: Exception, **context: Any) -> str:
    """Serialize a tool failure envelope with the exception type and optional context fields."""
    payload: dict[str, Any] = {"success": False, "error": str(exc), "error_type": type(exc).__name__, **context}
    return json.dumps(payload, indent=2, default=str)
```

- [ ] **Step 4: Run tests — pass**

Run: `uv run pytest tests/unit/tools/test_run_helpers.py -v`
Expected: PASS.

- [ ] **Step 5: Migrate the five tools, one at a time**

For each of risk_assessment_tool, backtesting_tool, portfolio_analysis_tool, quantitative_analysis_tool, valuation_tool: replace hand-rolled `json.dumps(result, indent=2, default=str)` success returns with `json_ok(result)` and the except-block error dicts with `json_error(e, ticker=...)` (preserve each tool's existing error-payload KEYS — if a tool's error payload has extra fields like `"analysis_type"`, pass them as context kwargs so the emitted JSON is unchanged). After EACH tool: run its test file (`uv run pytest tests/unit/tools/test_<tool>.py -v`). If a tool's existing tests assert on exact error JSON shape and the helper changes it, adapt the call (context kwargs), NOT the test.

- [ ] **Step 6: Validate + commit**

Run: `make test && make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "refactor(tools): shared json_ok/json_error envelope helpers, applied to the 5 highest-boilerplate tools"
```

---

### Task 5: Remove dead GradeInfo.css_class and fix the batch_prefetch doc example

**Files:**

- Modify: `src/finwiz/scoring/grading_system.py` (drop `css_class` field, ~line 24, + its 8 populate sites in `score_to_grade`)
- Modify: `tests/unit/utils/test_grading_system.py` (only if any test reads css_class)
- Modify: `src/finwiz/config/CLAUDE.md:63` (example uses nonexistent `batch_prefetch` flag)

- [ ] **Step 1: Verify css_class is still write-only**

```bash
rtk proxy grep -rn "css_class" src/finwiz tests --include='*.py' | grep -v "reporting/sections/common.py" | grep -v "grade_css_class"
```

Expected: hits only inside grading_system.py (definition + 8 populates) and possibly its tests. The live `grade_css_class()` helper in reporting/sections/common.py is a DIFFERENT thing — untouched.

- [ ] **Step 2: Remove the field**

Delete `css_class: str` from the `GradeInfo` dataclass and the `css_class="grade-..."` kwarg from all 8 `GradeInfo(...)` constructions in `score_to_grade`. Fix any test asserting on it.

- [ ] **Step 3: Fix the doc example**

In `src/finwiz/config/CLAUDE.md` (~line 63), replace the `is_feature_enabled("batch_prefetch")` usage example with a real flag, e.g. `is_feature_enabled("newcomer_discovery")`.

- [ ] **Step 4: Validate + commit**

Run: `uv run pytest tests/unit/utils/test_grading_system.py tests/unit/scoring -q` then `make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "chore: drop write-only GradeInfo.css_class; fix batch_prefetch doc example to a real flag"
```

---

### Task 6: Delete the self-validating feature-flag loop and unused strategy enums

**Files:**

- Modify: `src/finwiz/config/features/definitions.py` (remove `chart_analysis`, `enhanced_sentiment_analysis`, `twelve_data_integration` entries)
- Modify: `src/finwiz/config/manager.py` (`_validate_feature_flag_consistency`, lines ~332–349)
- Modify: `src/finwiz/config/features/` flags/evaluators (remove `FeatureFlagStrategy.USER_LIST` + `TIME_WINDOW` members and their evaluator branches)
- Modify: `.env.example` (FF_CHART_ANALYSIS, FF_ENHANCED_SENTIMENT*, FF_TWELVE_DATA* lines), related tests

Rationale (goes in commit body): these three flags gate no functionality anywhere — their only consumer is a startup validator that warns when a flag is enabled without its API key. Toggling them changes nothing else. Removing flag + validator kills the closed loop (spec: remove the switch). The API-key presence warnings, if valuable, already exist where the keys are read.

- [ ] **Step 1: Re-verify the closed loop**

```bash
for f in chart_analysis enhanced_sentiment_analysis twelve_data_integration; do
  echo "== $f"; rtk proxy grep -rn "\"$f\"\|'$f'" src/finwiz --include='*.py' | grep -v "features/definitions.py"
done
```

Expected: hits ONLY in `config/manager.py` `_validate_feature_flag_consistency`. Anything else = that flag is live; drop it from this task and report.

- [ ] **Step 2: Remove flags + validator**

Delete the three `FeatureFlagConfig` entries from `create_default_flags()`. In `manager.py`: if `_validate_feature_flag_consistency` does nothing but iterate that 3-flag dict, delete the whole method AND its call site(s); if it validates other things too, remove only the dict entries. Read the method fully first.

- [ ] **Step 3: Remove the unused strategy enums**

```bash
rtk proxy grep -rn "USER_LIST\|TIME_WINDOW" src/finwiz tests --include='*.py'
```

Confirm no flag definition or config path selects these strategies (only the enum declaration, evaluator branches, and their tests). Then delete: the two enum members, the evaluator handling branches (evaluators.py ~lines 52/55 and any `user_list`/`time_window` evaluator functions), and their dedicated tests. If ANY non-test selector exists, skip the enum removal and report.

- [ ] **Step 4: Clean .env.example + tests**

Remove `FF_CHART_ANALYSIS*`, `FF_ENHANCED_SENTIMENT*`, `FF_TWELVE_DATA*` lines. Update feature-flag tests that assert on the removed names/strategies (same surgical approach as Pass 1 Task 6: remove assertions, don't weaken surviving coverage).

- [ ] **Step 5: Validate + commit**

Run: `make test && make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "chore: remove self-validating feature-flag loop (3 flags + consistency validator) and unused USER_LIST/TIME_WINDOW strategies"
```

---

### Task 7: Clone-detection sweep over reporting/ and orchestrators/extraction/

**Files:** determined by findings (spec mandates the sweep; fixes only for clear clusters)

- [ ] **Step 1: Run the duplicate-code detector**

```bash
uvx pylint --disable=all --enable=duplicate-code --min-similarity-lines=12 src/finwiz/reporting src/finwiz/orchestrators/extraction src/finwiz/tools/reporting 2>&1 | grep -A14 "duplicate-code\|Similar lines" | head -120
```

(If pylint chokes on the codebase, fallback: `npx jscpd --min-tokens 70 --reporters consoleFull src/finwiz/reporting src/finwiz/orchestrators/extraction 2>&1 | head -80`.)

- [ ] **Step 2: Triage each reported cluster**

For each cluster: classify as (a) MECHANICAL — same logic copy-pasted, one caller-visible behavior → extract one helper function next to the more canonical copy and point both call sites at it (one commit per cluster, existing tests must stay green); (b) COINCIDENTAL — similar-looking but semantically different (e.g. two formatters with different output contracts) → record in the report, don't touch; (c) BIG — extraction would require restructuring → record as a Pass 3 lead, don't touch.

- [ ] **Step 3: For each MECHANICAL extraction: tests stay green**

Run the test files covering both call sites after each extraction (`rtk proxy grep -rln "<function>" tests` to find them): `uv run pytest <files> -q`. No test rewrites — behavior-preserving only.

- [ ] **Step 4: Validate + commit**

Run: `make test && make check`
Expected: green.

```bash
rtk git add -A && rtk git commit -m "refactor: extract shared helpers for clone clusters in reporting/extraction (detector-confirmed, behavior-preserving)"
```

(Skip the commit if every cluster triaged to COINCIDENTAL/BIG — then just record findings in the PR body.)

---

### Task 8: Fix pre-existing broken doc links

**Files:**

- Modify: `docs/reference/index.md` (links to never-created pages: `api/analysis.md`, `api/scoring.md`, `api/reporting.md`, `schemas/crew_exports.md`, …)
- Modify: `docs/maintenance/content-creation-guide.md`, `content-governance.md`, `troubleshooting-guide.md` (fictional example links)
- DO NOT touch: `docs/maintenance/style-guide.md` links that are intentional formatting EXAMPLES (read context before editing)
- Modify: `docs/development/DEVELOPER_GUIDE.md:1809` (`ci.yml` → `quality.yml`)

- [ ] **Step 1: Enumerate current broken links**

```bash
uv run python - <<'EOF'
from pathlib import Path
import re
root = Path("docs")
for md in sorted(root.rglob("*.md")):
    if "superpowers" in str(md):
        continue
    for m in re.finditer(r"\]\(([^)#:\s]+\.md)", md.read_text(encoding="utf-8")):
        target = (md.parent / m.group(1)).resolve()
        if not target.exists():
            print(f"{md}: {m.group(1)}")
EOF
```

Expected: ~15 lines matching the research list. This is the work queue.

- [ ] **Step 2: Fix each**

Per link: if an equivalent live page exists (e.g. `schemas/crew_exports.md` → check `docs/schemas/` for the real path), repoint; if the linked page never existed and the sentence is a placeholder promise, delete the line/list-entry; if it's inside a style-guide/content-guide EXAMPLE block demonstrating link syntax, leave it and note it. `DEVELOPER_GUIDE.md:1809`: point at `.github/workflows/quality.yml`.

- [ ] **Step 3: Validate — re-run the Step 1 script**

Expected output: only the intentional style-guide example links remain (list them in the commit body). Then `uv run mkdocs build --strict 2>&1 | tail -3` and `make check` → green.

- [ ] **Step 4: Commit**

```bash
rtk git add -A && rtk git commit -m "docs: fix or remove pre-existing broken links (reference/index, maintenance guides, DEVELOPER_GUIDE workflow ref)"
```

---

### Task 9: Final validation + PR

**Files:** none

- [ ] **Step 1: Full gate**

Run: `make check && make coverage`
Expected: exit 0; coverage ≥ 65% (was 75.27% after Pass 1).

- [ ] **Step 2: Measure**

```bash
rtk proxy git diff --stat main...HEAD | tail -2
```

- [ ] **Step 3: Push + PR**

```bash
rtk git push -u origin chore/simplify-pass2-merge
gh pr create --title "refactor: simplification pass 2 — merge duplicates, delete stubs/orphans (DRY)" --body "<summary per template: stub tools, orphaned analyzers, sentiment unification (BEHAVIOR NOTE: deep-analysis sentiment now uses the standardized rule-based scorer — same scale, values shift), run_helpers, css_class, flag loop, doc links; test plan with make check/coverage/mkdocs results>

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

- [ ] **Step 4: USER GATE — ask the user to run `crewai flow kickoff`**

Required before merge (spec rule), ESPECIALLY because Task 3 changes deep-analysis sentiment values. Ask the user to sanity-check the sentiment sections of the generated report, not just completion.

---

## Out of Scope (Pass 3)

- Function decomposition (get_report_css, get_integrated_data_context, …), CSS/HTML extraction to assets/templates
- ruff C901/PLR0915 + vulture wired into `make check`
- The 45-stub residue docs rewrite (real content for environment_variables etc.)
- Migrating the remaining ~30 tools to run_helpers (opportunistic, as they're touched)
- Clone clusters deferred from the Task 7 sweep (detector hits at 8-line threshold): (1) `analysis_date` normalization prefix duplicated between `deep_analysis_report_generator.py:156-174` and `enriched_analysis_report_generator.py:185-201`; (2) Jinja2 `__init__` setup duplicated between `base_report_generator.py:45-62` and `enriched_analysis_report_generator.py:47-64`. Both resolve the same way: bring `EnrichedAnalysisReportGenerator` (and possibly `DeepAnalysisReportGenerator`/`FinalReportGenerator`) into the `BaseReportGenerator` hierarchy — note their `analysis_date` contract differs (datetime object for template vs formatted string), so this is a restructuring, and the natural moment to flip `_apply_common_defaults` from explicit-call to a template-method pattern.
- The deep-analysis collector's `sentiment_confidence` key is a dead write (kept for output-contract stability; DeepAnalysisScorer derives its own confidence from `news_sentiment`) — candidate for contract cleanup.
- `quantitative/technical/technical_models.py:258` has an `EnhancedTechnicalAnalysisInput` twin not re-exported by its package — pre-existing dead code in the quantitative tree.
- SYSTEMIC doc drift: the nonexistent `finwiz.utils.*` namespace appears in ~56 code snippets across 14 doc files (DATA_QUALITY_AND_FLOW_GUIDE, DEVELOPER_GUIDE, LLM_CONFIGURATION, BATCH_PROCESSING, PERFORMANCE_CONFIGURATION, MEMORY_MANAGEMENT, HTML_INTEGRATION_GUIDE, html_reports, REPORT_AGGREGATION_DEVELOPER_GUIDE, DEEP_ANALYSIS_INTEGRATION, …) — the old utils/ package was reorganized into infrastructure/, config/, reporting/ and the docs never followed. Each snippet needs ground-truthing against the real module (some referenced symbols may no longer exist at all). Pass 2 fixed OPERATIONS_GUIDE + setup_environment only.
