# Drop PESTEL, and stop overfeeding the portfolio synthesis

**Date:** 2026-08-17
**Status:** Approved for planning

## Goal

Two changes to the same code path, done together because they rewrite the same
function:

1. Remove PESTEL analysis from FinWiz entirely. Per-holding strategic research
   keeps SWOT and Porter's Five Forces; macro analysis moves outside this
   system.
2. Cut the portfolio synthesis payload from ~610,000 chars to ~3,000 by sending
   portfolio aggregates and the ten extreme holdings instead of a per-holding
   digest of all 64.

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
| Research | `analysis/strategic_research.py` | `_pestel_prompt` and the PESTEL `perplexity_with_retry` call; `_SERIALIZE_RUNGS`, `_digest_all`, `_digest_one` and the whole degradation ladder deleted; `_serialize_holdings` rewritten to emit aggregates plus extremes |
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

### The synthesis payload becomes aggregates plus extremes

**Two corrections to earlier drafts of this spec, both from bad measurement on
my part. The numbers below come from the real `_digest_one` logic.**

First draft said the ladder stays load-bearing. Second draft said the ladder
turns the wrong dial and quoted 408,817 chars for its coarsest rung, measured
with a homemade digest that serialized every SWOT and Five Forces field. The
real `_digest_one` sends only scores, `strengths[:n]`, `threats[:n]` and prose.
Re-measured, PESTEL removed, scaled to 64 holdings:

| rung | chars/holding | at 64 holdings |
|---|---|---|
| bullets=3, prose | 5,022 | 321,376 |
| bullets=2, prose | 4,495 | 287,665 |
| bullets=1, prose | 3,972 | 254,176 |
| bullets=1, no prose (coarsest) | 609 | **39,001** |

So removing PESTEL alone drops the payload from 610,786 to 39,001 — the ladder
walks down, finds the first three rungs over budget, and lands on the coarsest.
Prose is the dominant term, not bullets: dropping it cuts 85% in one step.

That is still the wrong shape. 39,001 chars (~9,750 tokens) buys ~2,000 chars
of portfolio verdict, of which **869 chars reach the family artifact**. A
700:1 ratio, and it scales linearly with holdings.

**The payload becomes aggregates plus extremes:**

```python
{"n": 64,
 "swot_mean": 0.65, "moat_mean": 0.62,
 "distribution": {"<0.5": 3, "0.5-0.65": 7, "0.65-0.8": 12, ">=0.8": 4},
 "weakest":   [{"t": ticker, "c": composite, "T": threats[0]}   for the 5 lowest],
 "strongest": [{"t": ticker, "c": composite, "S": strengths[0]} for the 5 highest]}
```

Measured on real data: **2,904 chars (~726 tokens) at 26 holdings**, and it
barely grows — aggregates are fixed-size and the extremes stay at 10 entries,
so 64 holdings lands near 3,000–3,500 chars. **200× smaller than today, 13×
smaller than the ladder's floor**, and no longer a function of portfolio size:
a 200-position portfolio sends the same payload.

This is the right level for the call. A portfolio posture is a judgement about
distribution and outliers — concentration of moats, where the weak positions
are, which themes recur. That is what aggregates and extremes carry.

### The trade-off, stated plainly

The synthesis no longer sees the ~54 mid-pack holdings by name. It reasons from
the distribution and the ten extremes.

`dominant_themes` was previously derived from reading all 64 digests. It will
now be built from the extremes, so themes will be **sharper and less
consensual**. That is a real change in character, not just in size, and the
first run after this change should be read against the previous posture before
the result is trusted.

Coverage is unaffected: `holdings_covered`, `value_covered_pct` and
`uncovered_tickers` are computed in Python and merged after the model responds,
so "64 / 64" stays exact regardless of what the payload contains.

No A/B was run on synthesis quality. If the verdicts come back vague, the first
widening step is extremes of 8 instead of 5 — still a fixed-size payload.

### Consequences for the ladder

- `_SERIALIZE_RUNGS`, `_digest_all`'s rung parameter, `_digest_one`, and the
  estimate-then-select logic in `_serialize_holdings` are **deleted**. At ~3,000
  chars against a 240,000-char budget no rung can ever fire. Unlike the second
  draft's claim, this deletion is now justified by measurement rather than
  asserted.
- `SYNTHESIS_PAYLOAD_BUDGET_CHARS` stays as a guard: assert the payload is under
  it, log loudly if a future portfolio approaches it. It should never trigger.

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
