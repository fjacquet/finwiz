# Report File Structure Documentation

This document describes the `output/` directory tree FinWiz actually writes, as observed
from a live 3-holding kickoff run on 2026-09-07 (branch `refactor/remove-crew-subsystem`).
An earlier version of this document described an `output/reports/{session_id}/{crew}/`
tree — that layout never existed in production; it described infrastructure
(`crew_export_generator.py`'s path strings, per-crew report generators) that no live
code path ever called. This rewrite replaces it with the tree the run actually produced.

## Table of Contents

1. [Directory Structure](#directory-structure)
2. [File Naming Conventions](#file-naming-conventions)
3. [Accumulation, Not Sessions](#accumulation-not-sessions)
4. [What Doesn't Exist](#what-doesnt-exist)

## Directory Structure

`output/` is flat — there is no per-session subdirectory. A run writes into the same
tree every time, adding to what previous runs left behind:

```
output/
├── stock/
│   ├── AAPL_enriched.json          # deep-analysis result (written once, at analysis time)
│   ├── AAPL_report.html            # HTML for this holding (written once, same time as the .json)
│   └── discovery_output_20260907_170625.json   # per-run backup snapshot (accumulates)
├── etf/
│   ├── 2B7K.DE_enriched.json
│   ├── 2B7K.DE_report.html
│   └── discovery_output_20260907_170625.json
├── crypto/
│   ├── BTC-USD_enriched.json
│   ├── BTC-USD_report.html
│   └── discovery_output_20260907_170625.json
├── discovery/
│   ├── a_plus_stocks.json          # per-asset-class A+ opportunity list
│   ├── a_plus_etfs.json
│   ├── a_plus_crypto.json
│   ├── consolidated_discovery.json # merged A+ list — the one file alternative_finder_tool.py reads
│   └── discovery_output_20260907_170625.json   # same backup pattern, one per asset class per run
├── portfolio/
│   ├── portfolio_review.json
│   └── portfolio_processing_summary.json
├── cache/
│   ├── fred_snapshot.json
│   ├── returns_2026-09-07.json
│   └── sectors_2026-09-07.json
├── run_ledger/
│   └── <run_id>.jsonl              # one file per per-holding analysis run — see below
├── finwiz_family_financial_plan.html   # the one report every run always produces
├── finwiz_posture_strategique.html     # companion strategic-posture report
└── run_summary.json                # the run gate's verdict and eight checks (see the Quick Reference in root CLAUDE.md)
```

### Where each file comes from

- **`{ticker}_enriched.json`** and **`{ticker}_report.html`** are written together, once
  per holding, by `DeepAnalysisOrchestrator` during Phase 3 (`src/finwiz/orchestrators/
  deep_analysis_orchestrator.py`), via `EnrichedAnalysisReportGenerator`
  (`src/finwiz/reporting/enriched_analysis_report_generator.py`). `_report.html` is a
  snapshot of the report as it looked at analysis time, and it is the only per-holding
  HTML render — a second, reporting-phase pass
  (`ReportingOrchestrator.generate_enriched_html_reports()`) used to re-render every
  `*_enriched.json` a second time into a byte-identical `{ticker}_enriched.html`; it was
  deleted as redundant (#195).
- **`discovery_output_{timestamp}.json`** (one per asset class, written into
  `output/stock/`, `output/etf/`, `output/crypto/`, and `output/discovery/`) is a backup
  snapshot written by `DiscoveryOrchestrator` (`src/finwiz/orchestrators/
  discovery_orchestrator.py:420`) on every run. Nothing prunes these — the observed
  `output/discovery/` directory held 200+ of them going back to 2026-09-05.
- **`a_plus_stocks.json`** / **`a_plus_etfs.json`** / **`a_plus_crypto.json`** and
  **`consolidated_discovery.json`** are written by `DiscoveryOrchestrator`.
  `consolidated_discovery.json` is the only one of the four that
  `alternative_finder_tool.py` reads back.
- **`portfolio_review.json`** and **`portfolio_processing_summary.json`** are written by
  `PortfolioReviewOrchestrator` (`src/finwiz/orchestrators/portfolio_review_orchestrator.py`).
- **`run_ledger/<run_id>.jsonl`** is appended to by `RunLedger`
  (`src/finwiz/schemas/run_ledger.py`, `src/finwiz/analysis/stages/_ledger.py`) — one JSONL
  line per pipeline stage (`collect`, `quantitative`, `qualitative`, `synthesize`) per
  holding, each recording outcome, retries, fallback use, and cost. `run_id` here is the
  per-holding analysis run's own id, not the top-level `run_summary.json` `run_id`. The
  run gate's `coverage` check is computed from these files.
- **`finwiz_family_financial_plan.html`** is written by `PythonReportGenerator`
  (`src/finwiz/reporting/python_report_generator.py:123`), whose `output_dir` defaults to
  `"output"`. This is the one file every successful run always produces, regardless of
  how many holdings were analyzed.
- **`finwiz_posture_strategique.html`** is written alongside it, from
  `src/finwiz/orchestrators/reporting/enrichment.py:147`.
- **`run_summary.json`** is written by the run gate orchestrator
  (`src/finwiz/orchestrators/run_gate_orchestrator.py`) and holds the `verdict` and the
  eight named checks; see root `CLAUDE.md`'s "Parameterizing a flow run" section for how
  to read it.

## File Naming Conventions

- Tickers appear as given by the data source (e.g. `AAPL`, `2B7K.DE`, `BTC-USD`) — not
  normalized to a single case or suffix convention.
- `_enriched.json` / `_report.html` are fixed suffixes; there is no timestamp embedded in
  a per-ticker filename.
- `discovery_output_{YYYYMMDD_HHMMSS}.json` is the one filename pattern that does embed a
  timestamp, because it's a backup snapshot rather than a per-holding artifact.

## Accumulation, Not Sessions

There is no session concept and no cleanup. Every run adds to `output/stock/`,
`output/etf/`, `output/crypto/`, and `output/discovery/` rather than writing into an
isolated directory; `{ticker}_enriched.json`/`{ticker}_report.html`
are overwritten in place for a holding that gets re-analyzed, but nothing removes files for
holdings that drop out of the portfolio, and the `discovery_output_*.json` backups are
never pruned. A directory that has been run against repeatedly over multiple days (as
observed here) accumulates hundreds of files.

## What Doesn't Exist

None of the following are written by anything in `src/`, and none appeared in the
observed run's output:

- **`output/reports/{session_id}/`** — no per-session directory tree of any kind exists.
- **`{crew}_export.json`** (e.g. `AAPL_export.json`) — the export-schema/crew-report
  infrastructure that would have written these was deleted; see root `CLAUDE.md`'s "Crew
  Pattern" section.
- **`consolidated_report.json`**, **`final_report.html`** — these were never real output
  paths; they were, respectively, `ReportConsolidator`'s output (no caller ever existed)
  and a Jinja2 template *name* inside code that was itself deleted along with the rest of
  the crew subsystem.
- **`manifest.json`** — no manifest of any kind exists or ever existed; `manifest` does
  not appear anywhere in `src/` or `tests/`.
- **`{ticker}_enriched.html`** — this document's version 2.0 observed 93 of these per run,
  written by a reporting-phase pass that re-rendered every `*_enriched.json` a second
  time. That pass produced files byte-identical to `{ticker}_report.html` (save the
  footer timestamp) and was deleted as redundant (#195).

---

**Version**: 2.1 — removed `{ticker}_enriched.html` and the reporting-phase render pass
that produced it (#195).
**Last Updated**: 2026-09-08
