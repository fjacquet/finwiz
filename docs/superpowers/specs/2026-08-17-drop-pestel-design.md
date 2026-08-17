# Drop PESTEL, and stop overfeeding the portfolio synthesis

**Date:** 2026-08-17
**Status:** Approved for planning

## Goal

Two changes to the same code path, done together because they rewrite the same
function:

1. Remove PESTEL analysis from FinWiz entirely. Per-holding strategic research
   keeps SWOT and Porter's Five Forces; macro analysis moves outside this
   system.
2. Cut the portfolio synthesis payload from ~610,000 chars to ~73,000 by
   sending a lean per-holding digest instead of near-complete framework
   objects.

## Why

PESTEL is macro. It is run once, outside FinWiz. Per-holding strategic
research keeps SWOT and Five Forces, both firm-level by construction.

Decided; not open for relitigation in planning or review.

One factual note, recorded only so it is not revived as an argument in either
direction: the claim that 64 PESTEL runs produce near-duplicate output was
measured and is false (pairwise vocabulary overlap 0.164 median for PESTEL vs
0.138 for SWOT). The removal rests on level of analysis, not redundancy.

## What gets removed

| Area | File | Change |
|---|---|---|
| Research | `analysis/strategic_research.py` | `_pestel_prompt` and the PESTEL `perplexity_with_retry` call; `_SERIALIZE_RUNGS` and the whole degradation ladder; `_digest_one` rewritten to the lean shape |
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

### The degradation ladder is deleted, not trimmed

An earlier draft of this spec said the ladder stays load-bearing and must not
be deleted. **That instruction was wrong**, and the measurement that corrects
it is below.

The ladder's knobs are bullet count and prose inclusion. Measured on the run's
real data, with PESTEL already removed and scaled to 64 holdings:

| rung | chars/holding | at 64 holdings |
|---|---|---|
| bullets=3, prose | 11,868 | 759,569 |
| bullets=1, prose | 9,780 | 625,925 |
| bullets=1, no prose (coarsest) | 6,388 | **408,817** |

Trimming from the finest rung to the coarsest saves only 17%, and even the
coarsest sits at ~102k tokens. The bulk was never the bullets — it is every
field of SWOT and Five Forces, times 64 holdings. The ladder cannot reach a
sane size because it is turning the wrong dial.

### The lean digest

Replace `_digest_one`'s near-complete framework serialization with a fixed
minimal shape, one object per holding:

```python
{"t": ticker,
 "s": swot.strategic_score,          # rounded to 2dp
 "f": five_forces.strategic_score,   # rounded to 2dp
 "S": strengths[0], "W": weaknesses[0],
 "O": opportunities[0], "T": threats[0]}
```

Measured on real data: **1,134 chars per holding, 72,576 chars (~18k tokens)
at 64 holdings** — 5.6× smaller than the ladder's coarsest rung, and 8.4×
smaller than today's payload.

This is the right shape for what the call actually does. The synthesis writes a
portfolio-level verdict: dominant themes, aggregate SWOT, a strategic score.
One sharp point per quadrant per holding is signal; the fourth-ranked weakness
of the twelfth holding is noise it must read past. Cutting it is a quality
argument as much as a cost one.

Consequences:

- `_SERIALIZE_RUNGS`, `_digest_all`'s rung parameter, and the estimate-then-
  select logic in `_serialize_holdings` are **deleted**. At 73k against a 240k
  budget no rung could ever fire, and a degradation mechanism that cannot
  trigger is dead code that rots.
- `SYNTHESIS_PAYLOAD_BUDGET_CHARS` stays, demoted from a live trimming target
  to a guard: assert the payload is under it and log loudly if a future
  portfolio ever approaches it. At 64 holdings the digest uses 30% of budget;
  the budget is not reached until roughly 210 holdings.

### Quality risk, stated rather than hidden

This spec shows the payload shrinks. It does **not** show the synthesis stays
as good — no A/B was run. The proportion argument (94k tokens of input for ~2k
chars of verdict) is strong but it is an argument, not a measurement.

The first run after this change should be read against the last one's posture
output before the result is trusted. If the verdicts get vaguer, the digest is
the first thing to widen — most likely by carrying two bullets per quadrant
instead of one, which roughly doubles the payload to ~145k chars and is still
well inside budget.

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
- The remaining raw-markdown leakage in "Quintessence par position".
- The per-holding qualitative crew output, which is a separate context question
  from the portfolio synthesis payload addressed here.
