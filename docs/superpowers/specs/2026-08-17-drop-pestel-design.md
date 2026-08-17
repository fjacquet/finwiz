# Drop PESTEL from the FinWiz pipeline

**Date:** 2026-08-17
**Status:** Approved for planning

## Goal

Remove PESTEL analysis from FinWiz entirely. Per-holding strategic research
keeps SWOT and Porter's Five Forces; macro analysis moves outside this system.

## Why

PESTEL is a macro-environmental framework — political, economic, social,
technological, environmental, legal. Those forces act on markets and sectors,
not on individual companies. Running it once per holding asks a
portfolio-level question 64 times and attaches the answer to the wrong unit of
analysis.

SWOT and Five Forces are firm-level by construction. Strengths, weaknesses,
moat, buyer power, rivalry genuinely differ per holding and are correctly
scoped to it. PESTEL is the odd one out.

The decision is a judgement about the right level of analysis, not a
redundancy finding. An earlier claim in the discussion — that 64 PESTEL runs
produce near-duplicate output — was measured and **found false**: pairwise
vocabulary overlap across 20 holdings was 0.164 median for PESTEL against
0.138 for SWOT. The model does contextualise the macro picture per company.
That contextualisation is simply not what this system should be spending a
Perplexity call on, and it is not what a per-holding page should assert.

## What gets removed

| Area | File | Change |
|---|---|---|
| Research | `analysis/strategic_research.py` | `_pestel_prompt`, the PESTEL `perplexity_with_retry` call, PESTEL rungs in `_SERIALIZE_RUNGS`, `include_pestel_summary` / `include_pestel_dimensions` in `_digest_one` |
| Schema | `schemas/hybrid_analysis/strategic.py` | `PestelAnalysis`; `StrategicAnalysis.pestel`; `macro_environment_summary` and `macro_verdict` on `PortfolioPostureNarrative` |
| Schema | `schemas/hybrid_analysis/qualitative.py` | PESTEL references |
| Pipeline | `analysis/stages/__init__.py`, `analysis/stages/qualify.py` | PESTEL references |
| Scoring | `scoring/thresholds.py` | PESTEL references |
| Validation | `validation/ai_output.py` | PESTEL references |
| Reporting | `reporting/sections/posture_page.py` | "🌍 Environnement Macro" theme block; the PESTEL column in the per-holding table |
| Reporting | `reporting/sections/portfolio_summary.py` | `macro_verdict` bullet in the family artifact |
| Reporting | `reporting/deep_analysis_report_generator.py` | PESTEL references |
| Template | `templates/crew_reports/deep_analysis_report.html.j2` | PESTEL references |

Tests across 7 directories: `tests/unit/analysis` (6 files),
`tests/unit/reporting` (2), `tests/unit/orchestrators` (2),
`tests/unit/schemas` (1).

## Consequences, measured

### Scoring changes, and the change is user-visible

`StrategicAnalysis.composite_strategic_score` averages the non-`None`
framework scores. With PESTEL gone it averages two instead of three.

Measured across the 26 researched holdings of the 2026-08-16 run:

| | value |
|---|---|
| mean composite, with PESTEL | 0.651 |
| mean composite, without | 0.638 |
| median delta | −0.012 |
| range | −0.090 to +0.057 |
| holdings moving more than 0.05 | 4 of 26 |

This flows through `DeepAnalysisScorer.recompute_with_strategic` into displayed
grades and BUY/HOLD/SELL. **The next run's grades will differ from the last
one's for reasons unrelated to the market**, and a few holdings may cross a
grade boundary. That is acceptable and expected; it should be stated in the
changelog rather than discovered by a reader.

### The degradation ladder stays load-bearing

PESTEL is 39% of the strategic payload: 235,286 of 610,786 chars across the
run. After removal the payload is **375,500 chars against a 240,000-char
budget** — still over, so `_SERIALIZE_RUNGS` continues to do real work rather
than becoming dead code. It degrades by roughly one rung instead of falling
through to the coarsest, so the portfolio synthesis sees *more* evidence per
holding than it does today.

Do not delete the ladder as part of this work. Remove only the PESTEL-specific
rung dimensions; the remaining rungs still fire.

### Backward compatibility is free

The strategic schemas set `model_config = {"str_strip_whitespace": True}` with
no `extra=` key, so Pydantic defaults to `extra="ignore"`. Existing
`*_enriched.json` files carrying a `pestel` key validate cleanly and drop it.

This matters more than it appears: stale enriched files are reused for holdings
that fail re-analysis, so a strict schema here would fail those holdings on the
first post-change run. **Add a test pinning that a legacy payload containing
`pestel` still validates**, so a future `extra="forbid"` cannot silently break
re-analysis fallback.

### Time and cost

64 fewer Perplexity calls per run — one third of strategic research. Strategic
work drops from roughly 25s to roughly 17s per holding.

## The macro section is removed, not replaced

`macro_environment_summary` and `macro_verdict` are deleted from the posture
schema rather than kept and left empty. The posture page becomes competitive
landscape plus aggregated SWOT.

Rejected alternatives, recorded so they are not relitigated:

- **Feed the block from FRED.** The snapshot already collects `fed_rate`,
  `cpi_yoy`, `unemployment_rate`, `gdp_growth`, treasury spreads, VIX and
  fear/greed. Deterministic and free, but it is a data strip, not analysis —
  and macro is moving out of this system entirely, so a half-replacement here
  would compete with the real one.
- **Keep the field as an external paste-in.** Adds an optional input path and a
  conditional render for content that has no producer inside FinWiz.
- **Have the portfolio synthesis infer macro from SWOT/Porter.** Macro inferred
  from firm-level evidence is the weakest provenance available, and this branch
  has spent its length removing exactly that kind of ungrounded assertion.

Because both fields are currently **required** on `PortfolioStrategicPosture`
(made so deliberately, to stop a missing posture rendering as a confident
blank), removing them is a schema-narrowing change: update the model, the
synthesis prompt that fills them, and every fixture that constructs a posture.

## Testing

- Tests that assert a three-framework composite move to two.
- Tests constructing `StrategicAnalysis(pestel=...)` are **rewritten, not
  deleted**. Several pin the all-`None` and partial-coverage behaviour that the
  C1 coverage fix depends on (`13e053c9`); that behaviour must survive with two
  frameworks. Specifically: an all-`None` `StrategicAnalysis` must still yield
  `composite_strategic_score is None` and be excluded from coverage, and a
  partial analysis (one framework of two) must still count as covered.
- Add the legacy-payload test described above.
- The full suite must stay green: 5114 passed / 31 skipped at
  `3f154734`.

## Out of scope

- Where and how PESTEL is run outside FinWiz.
- The synthesis payload budget itself (`SYNTHESIS_PAYLOAD_BUDGET_CHARS`), which
  stays at 240,000.
- The remaining raw-markdown leakage in "Quintessence par position".
