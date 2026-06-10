# Lean Dependencies + Official SBOM & CVE Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 5 heavy/high-churn dependencies (fastapi, langchain-community, unstructured, langchain-text-splitters, sec-api) and add an official CycloneDX SBOM + osv-scanner CVE gate in CI.

**Architecture:** Replace the only live consumers of the doomed deps with stdlib/`beautifulsoup4`/a tiny local chunker; delete dead modules (`sec_tool.py`, the `api/` package); drop the deps and re-lock; add a `supply-chain.yml` workflow that emits a CycloneDX SBOM and gates on `osv-scanner` (with `chromadb` allowlisted). Target release 5.5.0.

**Tech Stack:** Python 3.12, uv (lockfile), pytest + pytest-mock, beautifulsoup4, cyclonedx-bom (`cyclonedx-py`), osv-scanner (CI), GitHub Actions.

**Working branch:** `chore/lean-deps-sbom` (already created).

**Spec:** `docs/superpowers/specs/2026-06-07-lean-deps-and-sbom-design.md`

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `src/finwiz/tools/_text_chunking.py` | Fixed-window text chunker with `.page_content`-compatible chunks | Create |
| `tests/unit/tools/test_text_chunking.py` | Tests for the chunker | Create |
| `src/finwiz/tools/enhanced_sec_tool.py` | Live SEC tool — swap unstructured→bs4, splitter→chunker, drop sec_api | Modify |
| `src/finwiz/tools/sec_tool.py` | Dead RAG SEC tool (langchain-community) | Delete |
| `tests/unit/tools/test_sec_tool.py` | Tests for the dead tool | Delete |
| `src/finwiz/tools/finance_tools.py` | Unwire `SECFilingSearchTool` | Modify |
| `src/finwiz/schemas/tools/inputs.py`, `.../__init__.py` | Drop orphan `SECFilingSearchInput` | Modify |
| `src/finwiz/api/` | Unused FastAPI module | Delete |
| `src/finwiz/schemas/api/` | Schemas used only by `api/` | Delete |
| `tests/unit/api/`, `tests/unit/schemas/api/` | Tests for removed code | Delete |
| `pyproject.toml` | Drop 5 deps + starlette constraint; add cyclonedx-bom/pip-audit dev deps; bump 5.5.0 | Modify |
| `osv-scanner.toml` | Allowlist chromadb advisory | Create |
| `.github/workflows/supply-chain.yml` | SBOM + CVE gate | Create |
| `Makefile` | `sbom` + `audit` targets | Modify |
| `docs/development/dependencies.md` | Dependency policy | Create |
| `CHANGELOG.md` | 5.5.0 entry | Modify |

---

## Task 1: Local text chunker (replaces CharacterTextSplitter)

**Files:**

- Create: `src/finwiz/tools/_text_chunking.py`
- Test: `tests/unit/tools/test_text_chunking.py`

- [ ] **Step 1: Write the failing test**

Create `tests/unit/tools/test_text_chunking.py`:

```python
"""Tests for the local fixed-window text chunker."""

import pytest

from finwiz.tools._text_chunking import TextChunk, chunk_text


def test_splits_into_overlapping_windows():
    text = "x" * 5000
    chunks = chunk_text(text, chunk_size=2000, overlap=200)
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(len(c.page_content) <= 2000 for c in chunks)
    assert len(chunks) >= 3
    # consecutive windows overlap by `overlap` characters
    assert chunks[0].page_content[-200:] == chunks[1].page_content[:200]


def test_short_text_single_chunk():
    out = chunk_text("hello world", chunk_size=2000)
    assert len(out) == 1
    assert out[0].page_content == "hello world"


def test_empty_or_whitespace_returns_empty():
    assert chunk_text("   ") == []
    assert chunk_text("") == []


def test_invalid_params_raise():
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=0)
    with pytest.raises(ValueError):
        chunk_text("x", chunk_size=100, overlap=100)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/tools/test_text_chunking.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'finwiz.tools._text_chunking'`

- [ ] **Step 3: Write the implementation**

Create `src/finwiz/tools/_text_chunking.py`:

```python
"""Lightweight fixed-window text chunking.

Replaces ``langchain_text_splitters.CharacterTextSplitter`` for the SEC tool:
the only behaviour needed is splitting a long string into overlapping
fixed-size character windows. Chunks expose ``page_content`` so existing
consumers that read ``doc.page_content`` keep working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    """A chunk of text with a langchain-Document-compatible ``page_content``."""

    page_content: str


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[TextChunk]:
    """Split *text* into fixed-size character windows with overlap.

    Args:
        text: Source text.
        chunk_size: Max characters per chunk (must be > 0).
        overlap: Overlap between consecutive chunks (0 <= overlap < chunk_size).

    Returns:
        List of ``TextChunk``; empty for empty/whitespace-only input.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
    cleaned = text.strip()
    if not cleaned:
        return []
    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    for start in range(0, len(cleaned), step):
        window = cleaned[start : start + chunk_size]
        if window.strip():
            chunks.append(TextChunk(page_content=window))
        if start + chunk_size >= len(cleaned):
            break
    return chunks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/tools/test_text_chunking.py -v --no-cov`
Expected: PASS (4 tests)

- [ ] **Step 5: Lint + typecheck**

Run: `uv run ruff check --fix src/finwiz/tools/_text_chunking.py tests/unit/tools/test_text_chunking.py && uv run ruff format src/finwiz/tools/_text_chunking.py && uv run mypy src/finwiz/tools/_text_chunking.py`
Expected: all clean

- [ ] **Step 6: Commit**

```bash
git add src/finwiz/tools/_text_chunking.py tests/unit/tools/test_text_chunking.py
git commit -m "feat(tools): add local text chunker to replace CharacterTextSplitter"
```

---

## Task 2: Refactor `enhanced_sec_tool.py` (bs4 + chunker, drop sec_api)

**Files:**

- Modify: `src/finwiz/tools/enhanced_sec_tool.py`
- Test: `tests/unit/tools/test_enhanced_sec_tool.py` (existing — must stay green; it patches `_get_filing_date_from_api` and `_download_html`, not the removed symbols)

- [ ] **Step 1: Swap the import (top of file)**

In `src/finwiz/tools/enhanced_sec_tool.py`, replace line 16:

```python
from langchain_text_splitters import CharacterTextSplitter
```

with:

```python
from finwiz.tools._text_chunking import chunk_text
```

- [ ] **Step 2: Rewrite `_split_into_documents` (around lines 258-263)**

Replace:

```python
    def _split_into_documents(self, html_text: str) -> list[Any]:
        """Split HTML content into manageable document chunks."""
        elements = partition_html(text=html_text)
        content = "\n".join([str(el) for el in elements])
        splitter = CharacterTextSplitter(separator="\n", chunk_size=2000, chunk_overlap=200, length_function=len)
        return splitter.create_documents([content])
```

with:

```python
    def _split_into_documents(self, html_text: str) -> list[Any]:
        """Extract readable text from filing HTML and split into chunks."""
        content = _html_to_text(html_text)
        return chunk_text(content, chunk_size=2000, overlap=200)
```

- [ ] **Step 3: Simplify `_get_filing_date_from_api` (lines 200-239)**

Replace the whole method body with a no-op that keeps the method as a patch point:

```python
    def _get_filing_date_from_api(self, ticker: str, form_type: str) -> str | None:
        """Filing-date lookup hook.

        The optional ``sec_api`` integration was removed (dependency trim); this
        now always returns ``None`` so the caller falls back to the current
        timestamp. Kept as a method so it stays a patch point for tests and any
        future provider.
        """
        return None
```

- [ ] **Step 4: Remove the unstructured fallback block and QueryApi global (bottom of file, lines 571-585)**

Delete this entire block:

```python
try:
    from unstructured.partition.html import partition_html
except ImportError as e:
    logger.debug(f"unstructured package not available, using fallback HTML partitioner: {e}")

    def _partition_html_fallback(text: str) -> list[Any]:
        """Fallback partitioner: return the raw HTML as a single chunk."""
        return [text]

    partition_html = _partition_html_fallback  # type: ignore[assignment]


# Defer importing QueryApi to runtime
QueryApi = None
```

and replace it with the bs4 helper:

```python
def _html_to_text(html: str) -> str:
    """Extract visible text from filing HTML using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)
```

- [ ] **Step 5: Drop now-unused imports**

Run: `uv run ruff check --fix src/finwiz/tools/enhanced_sec_tool.py`
Expected: removes any now-unused imports (e.g. `import os` if no longer used). If ruff reports remaining errors, read the file and remove the offending unused names by hand.

- [ ] **Step 6: Run the existing SEC tool tests + chunker test**

Run: `uv run pytest tests/unit/tools/test_enhanced_sec_tool.py tests/unit/tools/test_text_chunking.py -v --no-cov`
Expected: PASS (13 + 4). If a test referenced `partition_html`/`CharacterTextSplitter`/`QueryApi` (it should not), update it to drive `_download_html` + `_split_into_documents` instead.

- [ ] **Step 7: Add a focused test for bs4 extraction**

Append to `tests/unit/tools/test_enhanced_sec_tool.py`:

```python
def test_split_into_documents_extracts_text_via_bs4():
    from finwiz.tools.enhanced_sec_tool import EnhancedSECAnalysisTool

    tool = EnhancedSECAnalysisTool()
    html = "<html><body><p>" + ("Risk factors. " * 300) + "</p></body></html>"
    docs = tool._split_into_documents(html)
    assert docs, "expected at least one chunk"
    assert all(hasattr(d, "page_content") for d in docs)
    assert "Risk factors." in docs[0].page_content
    assert "<p>" not in docs[0].page_content  # tags stripped
```

- [ ] **Step 8: Run it**

Run: `uv run pytest tests/unit/tools/test_enhanced_sec_tool.py::test_split_into_documents_extracts_text_via_bs4 -v --no-cov`
Expected: PASS

- [ ] **Step 9: Typecheck + commit**

Run: `uv run mypy src/finwiz/tools/enhanced_sec_tool.py`
Expected: clean (or pre-existing-only notes)

```bash
git add src/finwiz/tools/enhanced_sec_tool.py tests/unit/tools/test_enhanced_sec_tool.py
git commit -m "refactor(sec): replace unstructured/text-splitter/sec_api with bs4 + local chunker"
```

---

## Task 3: Delete dead `sec_tool.py` → unblock langchain-community removal

**Files:**

- Delete: `src/finwiz/tools/sec_tool.py`, `tests/unit/tools/test_sec_tool.py`
- Modify: `src/finwiz/tools/finance_tools.py`, `src/finwiz/schemas/tools/inputs.py`, `src/finwiz/schemas/tools/__init__.py`

- [ ] **Step 1: Unwire `SECFilingSearchTool` from finance_tools.py**

In `src/finwiz/tools/finance_tools.py`, delete the import line (line 28):

```python
from finwiz.tools.sec_tool import SECFilingSearchTool
```

and remove `SECFilingSearchTool` from the key-gated tuple (line 74), changing:

```python
    for cls in (AlphaVantageCompanyOverviewTool, AlphaVantageNewsSentimentTool, TwelveDataIndicatorTool, ChartImgTool, SECFilingSearchTool):
```

to:

```python
    for cls in (AlphaVantageCompanyOverviewTool, AlphaVantageNewsSentimentTool, TwelveDataIndicatorTool, ChartImgTool):
```

- [ ] **Step 2: Delete the dead module and its test**

```bash
git rm src/finwiz/tools/sec_tool.py tests/unit/tools/test_sec_tool.py
```

- [ ] **Step 3: Remove the orphan `SECFilingSearchInput` schema**

Confirm it is now unused outside schemas:

Run: `grep -rn "SECFilingSearchInput" src/finwiz | grep -v __pycache__`
Expected: only `schemas/tools/inputs.py` and `schemas/tools/__init__.py`

Read `src/finwiz/schemas/tools/inputs.py` and delete the `class SECFilingSearchInput(...)` definition; read `src/finwiz/schemas/tools/__init__.py` and remove `SECFilingSearchInput` from the imports and `__all__`.

- [ ] **Step 4: Verify nothing imports the removed names**

Run: `grep -rn "from finwiz.tools.sec_tool\|SECFilingSearchTool\|SECFilingSearchInput" src/finwiz tests | grep -v __pycache__`
Expected: no output

- [ ] **Step 5: Lint + import smoke test**

Run: `uv run ruff check --fix src/finwiz/tools/finance_tools.py src/finwiz/schemas/tools/inputs.py src/finwiz/schemas/tools/__init__.py && uv run python -c "from finwiz.tools.finance_tools import get_stock_research_tools; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "chore(deps): remove dead sec_tool.py and unwire SECFilingSearchTool (drops langchain-community)"
```

---

## Task 4: Remove the unused FastAPI module

**Files:**

- Delete: `src/finwiz/api/`, `src/finwiz/schemas/api/`, `tests/unit/api/`, `tests/unit/schemas/api/`

- [ ] **Step 1: Confirm nothing in the flow imports the API**

Run: `grep -rn "finwiz.api\|finwiz.schemas.api" src/finwiz scripts | grep -v __pycache__ | grep -v "src/finwiz/api/" | grep -v "src/finwiz/schemas/api/"`
Expected: no output (only the api package and its schemas reference themselves)

- [ ] **Step 2: Delete the modules and tests**

```bash
git rm -r src/finwiz/api src/finwiz/schemas/api tests/unit/api tests/unit/schemas/api
```

- [ ] **Step 3: Verify no dangling references**

Run: `grep -rn "import fastapi\|from fastapi\|finwiz.api\|finwiz.schemas.api" src/finwiz tests | grep -v __pycache__`
Expected: no output

- [ ] **Step 4: Import smoke test**

Run: `uv run python -c "import finwiz; from finwiz.flows.orchestrator import FinwizFlow; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore(api): remove unused FastAPI module (drops fastapi/starlette surface)"
```

---

## Task 5: Drop the 5 dependencies, re-lock, and verify the whole suite

**Files:**

- Modify: `pyproject.toml`, `uv.lock`

- [ ] **Step 1: Remove the 5 deps from `pyproject.toml` dependencies**

Delete these lines from the `dependencies = [ ... ]` array:

```python
    "unstructured>=0.18.11",
    "langchain-community>=0.3.29",
    "langchain-text-splitters>=0.3.0",
    "sec-api>=1.0.32",
    "fastapi>=0.136.1",
```

- [ ] **Step 2: Remove the now-moot starlette constraint**

In the `[tool.uv] constraint-dependencies` array, delete:

```python
    "starlette>=1.0.1",
```

(Leave urllib3/idna/gitpython/langchain-classic/uv — they are pulled by other deps. Task 5 Step 4 re-checks langchain-classic.)

- [ ] **Step 2b: Add SBOM/audit dev tooling**

In `[dependency-groups] dev = [ ... ]`, add:

```python
    "cyclonedx-bom>=4.0.0",
    "pip-audit>=2.7.0",
```

- [ ] **Step 3: Re-lock and sync**

Run: `uv lock && uv sync --all-extras --all-groups`
Expected: `uv lock` prints "Removed …" lines for unstructured, langchain-community, langchain-text-splitters, sec-api, fastapi and their unique transitives (faiss-cpu, nltk, lxml, dataclasses-json, starlette, uvicorn, …).

- [ ] **Step 4: Verify the deps are gone from the lock; drop langchain-classic constraint if orphaned**

Run: `for p in fastapi langchain-community unstructured langchain-text-splitters sec-api starlette faiss-cpu langchain-classic; do echo "$p: $(grep -c "^name = \"$p\"" uv.lock)"; done`
Expected: all `0` EXCEPT possibly `langchain-classic`. If `langchain-classic: 0`, also delete its line from `[tool.uv] constraint-dependencies` and re-run `uv lock`. If `1`, leave the constraint.

- [ ] **Step 5: deptry — no unused/missing deps**

Run: `uv run --with deptry deptry src --known-first-party finwiz`
Expected: `Success! No dependency issues found.`

- [ ] **Step 6: Full quality gate**

Run: `make test`
Expected: `5260 passed` (minus the deleted sec_tool/api tests; expect ~5260-ish passed, e.g. ~5245+), 0 failed; coverage ≥ 65%.

Run: `make mypy`
Expected: `Success`

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): drop fastapi, langchain-community, unstructured, langchain-text-splitters, sec-api; add SBOM tooling"
```

---

## Task 6: SBOM + CVE gate (CycloneDX + osv-scanner)

**Files:**

- Create: `osv-scanner.toml`, `.github/workflows/supply-chain.yml`
- Modify: `Makefile`

- [ ] **Step 1: Create the osv-scanner allowlist**

Create `osv-scanner.toml`:

```toml
# osv-scanner config — allowlisted advisories with documented justification.
# Reviewed on each dependency change.

[[IgnoredVulns]]
id = "GHSA-f4j7-r4q5-qw2c"
# chromadb pre-auth code injection is in ChromaDB's SERVER, which FinWiz never
# runs (crewai uses in-process memory only). No patched release exists and
# chromadb is a hard transitive of crewai core, so it cannot be removed.
reason = "Vulnerable code path (Chroma server) is not used; no fix available; crewai-core transitive."
```

- [ ] **Step 2: Add Makefile targets**

Add to the `.PHONY` line (line 3) the names `sbom audit`, then append at the end of `Makefile`:

```makefile
.PHONY: sbom audit

sbom:  ## Generate a CycloneDX SBOM to dist/finwiz.sbom.cdx.json
 @mkdir -p dist
 uv run cyclonedx-py environment --output-format JSON --output-file dist/finwiz.sbom.cdx.json
 @echo "SBOM written to dist/finwiz.sbom.cdx.json"

audit:  ## Scan installed dependencies for known vulnerabilities (chromadb allowlisted)
 uv run pip-audit --ignore-vuln GHSA-f4j7-r4q5-qw2c
```

- [ ] **Step 3: Verify SBOM + audit locally**

Run: `make sbom`
Expected: `dist/finwiz.sbom.cdx.json` created; valid JSON (check `head -c 200 dist/finwiz.sbom.cdx.json` shows `"bomFormat": "CycloneDX"`).

Run: `make audit`
Expected: completes; either "No known vulnerabilities found" or lists only advisories you then add to the allowlist. (chromadb GHSA-f4j7-r4q5-qw2c is ignored.)

- [ ] **Step 4: Create the CI workflow**

Create `.github/workflows/supply-chain.yml`:

```yaml
name: Supply Chain

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  release:
    types: [published]

permissions:
  contents: write  # attach SBOM to releases

jobs:
  sbom-and-scan:
    name: SBOM + Vulnerability Scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true

      - name: Sync dependencies
        run: uv sync --all-extras --all-groups

      - name: Generate CycloneDX SBOM
        run: |
          mkdir -p dist
          uv run cyclonedx-py environment --output-format JSON --output-file dist/finwiz.sbom.cdx.json

      - name: Upload SBOM artifact
        uses: actions/upload-artifact@v4
        with:
          name: finwiz-sbom-cyclonedx
          path: dist/finwiz.sbom.cdx.json

      - name: Vulnerability scan (osv-scanner)
        uses: google/osv-scanner-action/osv-scanner-action@v2
        with:
          scan-args: |-
            --lockfile=uv.lock
            --config=osv-scanner.toml

      - name: Attach SBOM to release
        if: github.event_name == 'release'
        run: gh release upload "${{ github.event.release.tag_name }}" dist/finwiz.sbom.cdx.json --clobber
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

> Note: the gate fails on ANY non-allowlisted advisory osv-scanner finds in `uv.lock` (osv-scanner has no built-in CVSS pass/fail filter). This satisfies the intent — "act on real advisories, not routine version drift" — and low-severity noise is managed by adding entries to `osv-scanner.toml`. Verify `google/osv-scanner-action` has no newer major tag than `v2` (Dependabot's github-actions ecosystem will keep it current).

- [ ] **Step 5: Commit**

```bash
git add osv-scanner.toml .github/workflows/supply-chain.yml Makefile
git commit -m "ci(supply-chain): CycloneDX SBOM + osv-scanner CVE gate; make sbom/audit"
```

---

## Task 7: Dependency policy doc + CHANGELOG + version bump

**Files:**

- Create: `docs/development/dependencies.md`
- Modify: `CHANGELOG.md`, `pyproject.toml`

- [ ] **Step 1: Write the policy doc**

Create `docs/development/dependencies.md`:

```markdown
# Dependency Policy

FinWiz keeps its dependency surface small on purpose: fewer packages means
fewer upgrades to chase and a smaller supply-chain attack surface.

## Adding a dependency

Before adding a package, in order of preference:

1. Use the Python standard library.
2. Use a capability already provided by an existing dependency.
3. Only then add a new dependency — and justify it in the PR description
   (what it does, why nothing we have covers it, rough transitive weight).

Prefer small, single-purpose, actively-maintained libraries over frameworks
that pull large transitive trees.

## Upgrades

Routine minor/patch drift is **not** chased. Upgrades are driven by the CVE
gate: `osv-scanner` runs in CI (`.github/workflows/supply-chain.yml`) against
`uv.lock` and fails on any non-allowlisted advisory. When it fails, raise the
affected floor and re-lock.

Accepted/unfixable advisories live in `osv-scanner.toml` with a written
justification and are reviewed on each dependency change.

## SBOM

A CycloneDX SBOM is generated in CI and attached to every GitHub Release.
Generate it locally with `make sbom`; scan locally with `make audit`.
```

- [ ] **Step 2: Add the CHANGELOG entry**

In `CHANGELOG.md`, replace the `## [Unreleased]` line with:

```markdown
## [Unreleased]

## [5.5.0] - 2026-06-07

### Changed

- **Leaner dependency tree.** Removed `fastapi` (unused REST module deleted),
  `langchain-community` (dead `sec_tool.py` deleted), `unstructured` (replaced
  with `beautifulsoup4`), `langchain-text-splitters` (replaced with a local
  chunker), and `sec-api` (optional, EDGAR-direct path covers it). Drops their
  large transitive trees (faiss, nltk, lxml, starlette, …).

### Security

- **Official SBOM + CVE gate.** New `supply-chain` CI workflow emits a
  CycloneDX SBOM (attached to releases) and gates merges on `osv-scanner`
  against `uv.lock`; accepted advisories are allowlisted in `osv-scanner.toml`
  (currently chromadb `GHSA-f4j7-r4q5-qw2c`, server-only, no fix). Local
  parity via `make sbom` / `make audit`.
```

- [ ] **Step 3: Bump the version**

In `pyproject.toml` change:

```python
version = "5.4.1"
```

to:

```python
version = "5.5.0"
```

Then re-lock so the lock's own version updates:

Run: `uv lock`
Expected: `Updated finwiz v5.4.1 -> v5.5.0`

- [ ] **Step 4: Final full gate**

Run: `make test && make mypy`
Expected: tests pass, mypy clean.

- [ ] **Step 5: Commit**

```bash
git add docs/development/dependencies.md CHANGELOG.md pyproject.toml uv.lock
git commit -m "docs: dependency policy; chore(release): 5.5.0"
```

---

## Final verification (before PR)

- [ ] `make test` green (full suite), `make mypy` clean.
- [ ] `uv run --with deptry deptry src --known-first-party finwiz` → no issues.
- [ ] `grep -rn "fastapi\|langchain_community\|unstructured\|langchain_text_splitters\|sec_api" src/finwiz | grep -v __pycache__` → no output.
- [ ] `make sbom` produces a CycloneDX JSON; `make audit` passes with chromadb allowlisted.
- [ ] Semgrep scan on new/changed Python (`_text_chunking.py`, `enhanced_sec_tool.py`): no findings.
- [ ] Push branch, open PR, confirm both `Lint, Test & Quality Gates` and the new `Supply Chain` workflow pass before merge.

## Spec-coverage check

- Part A (remove 5 deps): Tasks 1–5. ✅
- Part B (SBOM + scan, no signing): Task 6. ✅
- Part C (policy doc; Dependabot untouched): Task 7. ✅
- Keep plotly/pypfopt/langchain-core/talib/QuantLib/backtrader: never touched. ✅
