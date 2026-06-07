# Lean Dependencies + Official SBOM & Vulnerability Scanning

**Date:** 2026-06-07
**Status:** Approved (design)
**Target version:** 5.5.0

## Context

FinWiz carries a large dependency tree (~274 locked packages even after the 5.4.1
trim). Routine Dependabot churn — minor/patch PRs to review and merge every week —
is a recurring chore disproportionate to the value, and the surface area is a
standing supply-chain risk. There is currently **no SBOM and no vulnerability
scanning**; the only signal is Dependabot alerts on `uv.lock`.

The goal is two-fold and complementary:

1. **Shrink the dependency surface** so there are simply fewer packages to ever
   upgrade (the user's chosen primary mechanism over "security-only Dependabot"
   or "slower cadence").
2. **Stand up an official SBOM + a CVE gate** so security advisories — not every
   minor release — drive upgrade action. The gate makes "upgrade when there's a
   real CVE" a safe operating mode.

An audit (with file:line evidence) confirmed five heavy, high-churn direct
dependencies whose code paths are dead or trivially replaceable, plus the
load-bearing ones to keep.

## Part A — Remove 5 heavy/churny direct dependencies

All five are confirmed removable against the production entry point
(`crewai flow kickoff` → `main.py` → `core/app_initializer.py` →
`flows/orchestrator.py`). The existing test suite (5260 passing) is the safety net.

### A1. Remove the FastAPI module → drop `fastapi`

- `src/finwiz/api/` (`app.py`, `rebalancing.py`, `__init__.py`) is imported only by
  `tests/unit/api/` — never by the flow, orchestrators, crews, scripts, or docs.
- **Action:** delete `src/finwiz/api/` and `tests/unit/api/`; remove `fastapi` from
  `pyproject.toml` dependencies; remove the now-moot `starlette>=1.0.1` entry from
  `[tool.uv] constraint-dependencies` (starlette was pulled by fastapi — verify
  nothing else requires it before removing the pin). Retires the starlette CVE
  surface entirely.

### A2. Delete dead `sec_tool.py` → drop `langchain-community`

- Production SEC analysis runs through `EnhancedSECAnalysisTool`
  (`tools/enhanced_sec_tool.py`, EDGAR-direct via `sec_filing_url_generator.py`).
- `tools/sec_tool.py`'s `SECFilingSearchTool` is the only consumer of
  `langchain_community` (FAISS + OpenAIEmbeddings) and is wired as "optional" in
  `tools/finance_tools.py` (~line 74).
- **Action:** confirm `SECFilingSearchTool` is not on any production crew's tool
  list (remove the optional wiring in `finance_tools.py` and any tool-routing
  references); delete `sec_tool.py` and its tests; drop `langchain-community`.
  Verify no other module imports `langchain_community`.

### A3. Replace `unstructured` with `beautifulsoup4`

- `enhanced_sec_tool.py` (~line 572) uses `unstructured.partition.html.partition_html`
  with a raw-HTML fallback already in place; `beautifulsoup4` is already a direct
  dependency.
- **Action:** replace the `partition_html` call with a small bs4 text extraction
  (`BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)`);
  drop `unstructured`.

### A4. Replace `langchain-text-splitters` with a tiny chunker

- `enhanced_sec_tool.py` (line 16) uses `CharacterTextSplitter` for length-based
  chunking only.
- **Action:** add a small local chunking helper (fixed-size character windows with
  optional overlap) — co-locate in the sec tool or a `tools/_text_chunking.py`;
  drop `langchain-text-splitters`.

### A5. Drop `sec-api`

- `enhanced_sec_tool.py` (~line 216) uses `sec_api.QueryApi` only as an optional
  filing-date lookup that already returns `None` on any failure
  (`_get_filing_date_from_api`).
- **Action:** remove the optional `sec_api` branch (keep the graceful `None`
  behavior without the import); drop `sec-api`.

### A — Keep (load-bearing, verified)

`plotly` + `pypfopt` (active quant path via `quantitative_analysis_tool` →
`performance.py`), `langchain-core` (direct **and** a hard transitive of crewai),
`ta-lib`, `QuantLib`, `backtrader`, `empyrical-reloaded`, and the small
single-purpose libs (`feedparser`, `gnews`, `fredapi`, `vaderSentiment`).

### A — Re-lock & verify

`uv lock` → `uv sync` → `deptry src` (zero unused/missing) → full `make test`
(expect 5260 passing, unchanged) → `make mypy`. Confirm `langchain-community`,
`unstructured`, `langchain-text-splitters`, `sec-api`, `fastapi`, and their unique
transitives (faiss, nltk, lxml, dataclasses-json, starlette, uvicorn, …) are gone
from `uv.lock`. Expected net reduction: ~30–60 packages.

## Part B — Official SBOM + CVE gate (generate + scan, no signing)

Posture per decision: **generate + scan + gate, no cryptographic signing/attestation.**

### B1. SBOM generation

- New workflow `.github/workflows/supply-chain.yml`, triggered on `pull_request`,
  `push` to `main`, and `release: published`.
- Steps: checkout → `setup-uv` → `uv sync --all-extras --all-groups` →
  generate **CycloneDX** SBOM via `cyclonedx-py environment` (Python-native,
  reads the synced venv accurately) → upload as a workflow artifact; on a
  published release, also attach the SBOM file to the GitHub Release
  (`gh release upload` or `softprops/action-gh-release`).
- CycloneDX JSON is the official format (security-standard). SPDX is out of scope
  (avoid dual-format maintenance unless later required).

### B2. CVE gate

- Add `osv-scanner` to the same workflow, run against `uv.lock` (native support).
  **Fail CI on new HIGH/CRITICAL** advisories.
- `osv-scanner.toml` at repo root allowlists the accepted **chromadb**
  advisory (`GHSA-f4j7-r4q5-qw2c`) with a documented reason (no patch exists;
  crewai-core transitive; vulnerability is in ChromaDB's server which FinWiz
  never runs) and a review/expiry date.

### B3. Local parity (Makefile)

- `make sbom` — generate the CycloneDX SBOM locally to `dist/finwiz.sbom.cdx.json`.
- `make audit` — run `osv-scanner` (or `uv run pip-audit` fallback) against the lock.
- Wire neither into the default `make check` (keep CI fast); they are explicit,
  plus the CI `supply-chain` job enforces them.

## Part C — Lean practice (lightweight, ongoing)

- A short "Adding a dependency" section in `docs/` (or `CONTRIBUTING`): justify new
  deps, prefer the standard library or an already-present dependency, and note that
  the CVE gate — not routine version drift — is what triggers upgrades.
- Dependabot config is left as-is (already weekly + grouped patch/minor, separate
  majors). The surface cut + CVE gate are the mechanism; no Dependabot retune in
  this spec (explicitly out of scope to respect the chosen "cut surface" strategy).

## Out of scope

- SBOM signing / Sigstore attestation (explicitly declined).
- SPDX format.
- Removing plotly/pypfopt/langchain-core/QuantLib/talib (load-bearing).
- Dependabot strategy change (security-only / cadence).
- Replacing crewai/litellm (the framework core; chromadb stays with it).

## Verification (end-to-end)

1. `deptry src` — no unused/missing dependencies after the cuts.
2. `make test` — 5260 passing (unchanged); `make mypy` clean; `semgrep` clean on
   any new/changed code.
3. `uv.lock` no longer contains fastapi, langchain-community, unstructured,
   langchain-text-splitters, sec-api (or their unique transitives); package count
   dropped.
4. `make sbom` produces a valid CycloneDX JSON; `make audit` / CI `osv-scanner`
   passes with only the allowlisted chromadb advisory.
5. CI `supply-chain` workflow runs green on the PR; SBOM artifact present.
6. SEC analysis still works end-to-end (enhanced tool path) — covered by existing
   SEC tests; add a focused test for the new bs4 extraction and the chunker.

## Suggested phase/commit breakdown

1. `refactor(sec): replace unstructured/text-splitters/sec-api in enhanced_sec_tool`
2. `chore(deps): remove dead sec_tool.py + langchain-community`
3. `chore(api): remove unused FastAPI module + fastapi dep`
4. `chore(deps): re-lock; drop fastapi/langchain-community/unstructured/text-splitters/sec-api`
5. `ci(supply-chain): CycloneDX SBOM + osv-scanner gate + make sbom/audit`
6. `docs: dependency policy; chore(release): 5.5.0`
