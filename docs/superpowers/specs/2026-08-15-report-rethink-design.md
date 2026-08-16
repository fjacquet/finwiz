# Report Rethink — Design

**Date:** 2026-08-15
**Status:** Approved design, ready for implementation planning
**Scope:** `src/finwiz/reporting/`, `src/finwiz/analysis/stages/`, `src/finwiz/schemas/hybrid_analysis/strategic.py`, `src/finwiz/analysis/strategic_research.py`, `src/finwiz/discovery/`, `src/finwiz/infrastructure/monitoring/litellm_callback.py`

## Problem

The run of 2026-08-15 09:34 produced `output/finwiz_family_financial_plan.html` (435 KB). It presents partial data with full authority, mixes two languages, and contradicts itself inside a single page.

### Observed defects

| # | Location | Symptom |
|---|---|---|
| 1 | `reporting/sections/portfolio_summary.py:127` | 700-word AI essay with raw markdown (`**bold**`, `-` bullets) and unresolved citation markers (`[3]`, `[8]`, `[VAHN JSON]`) rendered via `escape()` into one `<p>` |
| 2 | `reporting/sections/portfolio_summary.py:117` | Section titled "Posture Stratégique **du Portefeuille**" synthesized from 3 holdings (ORCL, VAHN, TSLA) |
| 3 | `reporting/sections/analysis.py:41-55` | "45 Successful Analyses / 0 Failed / 100.0% Success Rate" on the same page as "Couverture: 39/64 (25 échoués)" |
| 4 | `reporting/sections/analysis.py:84-102` | "0 LLM Calls / 0.0s Total Time / $0.00" — `metrics` dict never populated |
| 5 | `reporting/sections/insights.py:197-206` | `cost_total_and_calls()` discards the monitor's `cost_known` flag, so `$0.00 sur 781 appels LLM` prints as fact over 11.4M unpriced tokens |
| 6 | `reporting/sections/discovery.py:220` | "0 New Opportunities Identified" presented as a finding |
| 7 | `tools/alternative_finder_tool.py:179`, `orchestrators/extraction/engine.py:169,192` | All three read `output/discovery/discovery_latest.json`, which nothing writes |
| 8 | `analysis/stages/fact_pack.py:74` | `RuntimeError` kills 22 of 64 holdings on Perplexity 429 / transport timeout |
| 9 | `config/critical_fields_config.py:18,24,32` | `CriticalFieldError: Missing critical fields: volatility` kills 3 more holdings |
| 10 | `discovery/universe_provider.py:89` | ETF universe = 11 tickers after excluding 71 holdings |
| 11 | Report structure | 15 sections, 7 English headings / 8 French |

### Evidence

Run ledger `output/run_ledger/4ac8188848aa.jsonl`, 306 rows, 64 tickers:

```
collect    ok 64
quantify   ok 61   failed 3    (CriticalFieldError: volatility)
fact_pack  ok 39   failed 22   (RuntimeError: Perplexity fetch failed)
qualify    ok 39
synthesize ok 39
emit       ok 39
```

Perplexity failures, `logs/finwiz.log`:

```
20  Perplexity transport error for _FactPackRaw:
 3  Perplexity HTTP 429 for SwotAnalysis
 2  Perplexity HTTP 429 for PestelAnalysis
 2  Perplexity HTTP 429 for _FactPackRaw
 1  Perplexity transport error for SwotAnalysis:
 1  Perplexity HTTP 429 for FiveForcesAnalysis
```

Cost, `logs/finwiz.log:6352`:

```
LLM Cost Summary (estimated from CrewAI usage metrics):
  deep_analysis_stock:  cost n/a (unpriced model) (138 calls, 1946467 tokens)
  deep_analysis_crypto: cost n/a (unpriced model) (39 calls, 564654 tokens)
  deep_analysis_etf:    cost n/a (unpriced model) (604 calls, 8916020 tokens)
  TOTAL: ~$0.0000 estimated across 781 calls
```

Discovery, `logs/finwiz.log:5944-5956`:

```
Universe for etf: 11 tickers (source=dynamic, excluded=71)
Portfolio-aware scoring produced 10 scored etf candidates
filter_actionable_candidates: 10 scored -> 0 actionable (dropped 10 grade<C)
```

The grade filter behaved correctly — weak signals are excluded rather than emitted as D/F. The defect is upstream: a universe of 11 candidates is not a search.

### Root cause

Two roots, not eleven:

1. **No section knows its own evidence base.** Each section reads raw dicts independently and renders at full confidence regardless of what it received. Defects 1-6 are all instances of this.
2. **A rate-limited dependency fails closed.** One Perplexity 429 destroys an entire holding rather than degrading it. Defects 8 and 10 share this.

## Decisions

| Decision | Choice |
|---|---|
| Audience | Family, non-technical. Plain French. |
| Partial data | Pipeline's job to reach full coverage; document refuses only what it genuinely lacks |
| Qualitative rendering | Two layers — one-sentence verdict, detail behind `<details>` |
| Machinery content | Relocated to a second artifact, not deleted |
| Architecture | Section contract + view models (rejected: patch-in-place; rejected: Jinja2 swap) |

Rejected approaches and why:

- **Patch each site.** Fastest, but the defect class recurs — nothing prevents the next section from printing an unbacked number.
- **Jinja2 template swap.** Better long-term ergonomics, but lands a second large change alongside the semantic one. The f-string path in `python_report_generator.py` is the one production renders; churning it while changing semantics doubles blast radius.

## Design

### 1. Two artifacts, one run

`FinwizFlow` Phase 6 emits both from the same view models.

| | `finwiz_family_financial_plan.html` | `finwiz_run_report.html` |
|---|---|---|
| Reader | family | maintainer |
| Language | French only | French, technical terms kept |
| Positions | verdict + short reason | full detail, all fields |
| Qualitative | verdict; `<details>` for reasoning | full PESTEL/SWOT/Porter + sources |
| Numbers | grades as words ("solide", "fragile") | scores, components, weights |
| Coverage | one line: "39 des 64 positions analysées" | per-stage ledger, failures named with reason |
| Cost | absent | tokens, calls, per-crew, "non chiffrable" where true |
| Machinery | absent | success rate, timings, retries, fallbacks |

Split rule: **family answers "what do we do"; run report answers "can we trust it and what did it cost"**. Every existing section lands in exactly one. Nothing is dropped.

Because both render from the same view models, the defect-3 contradiction becomes structurally impossible.

### 2. Section contract + view models

```
enrichment.py (raw dicts, crew exports, ledger)
        │
        ▼  builders/     pure Python, no AI, no HTML
   view_models/          typed, carry their own evidence
        │
        ├──▶ renderers/family/     → finwiz_family_financial_plan.html
        └──▶ renderers/technical/  → finwiz_run_report.html
```

Every view model embeds evidence as a mandatory field:

```python
class Evidence(BaseModel):
    covered: int              # items this section actually used
    total: int                # items it claims to describe
    basis: list[str] = []     # tickers or sources behind it
    known: bool = True        # False = measured but not trustworthy
    missing: list[str] = []   # named gaps
```

Renderers enforce it; sections cannot opt out:

- `covered < total` → scope line printed before the content (fixes defects 2, 3)
- `known is False` → renders "non chiffrable", never `$0.00` (fixes defect 5)
- `covered == 0` → renders a refusal, not an empty table under a confident heading (fixes defect 6)

**New modules**

| Path | Role |
|---|---|
| `reporting/view_models/*.py` | one Pydantic model per section, plus `Evidence` |
| `reporting/builders/*.py` | raw → view model; deterministic, testable without HTML |
| `reporting/renderers/family/*.py` | word-grades, verdict-only, French |
| `reporting/renderers/technical/*.py` | full numbers, ledger, cost |

**Changed modules**

| Path | Change |
|---|---|
| `reporting/python_report_generator.py` | stays production entry; orchestrates builders + two renderers instead of holding f-strings |
| `reporting/sections/*.py` (9 files) | logic moves to builders, markup to renderers; thin re-export shims remain |
| `reporting/css_styles.py` | shared; family gets a reduced sheet |
| `reporting/section_generators.py` | re-export shim, kept so imports outside `reporting/` keep working |

### 3. Qualitative contract

```python
class QualitativeBlock(BaseModel):
    verdict: str              # 1 sentence, plain French, <=30 words
    detail: str               # reasoning, plain French prose, <=200 words
    sources: list[str] = []   # resolved URLs/titles, not [3] markers
```

Validators make the essay structurally impossible rather than cleaned up after the fact:

- `verdict`: reject `**`, `-`, `#`, newlines; enforce the 30-word cap
- both fields: reject unresolved `[n]` and `[TICKER JSON]` markers — they move to `sources` or are stripped
- `detail`: enforce the 200-word cap; markdown bullets convert to a real list at build time

`PortfolioStrategicPosture` (`schemas/hybrid_analysis/strategic.py:158`) changes:

| Field | Now | After |
|---|---|---|
| `macro_environment_summary` | `str` | `QualitativeBlock` |
| `competitive_landscape_summary` | `str` | `QualitativeBlock` |
| `overall_assessment` | `str` | `QualitativeBlock` |
| `portfolio_strengths` / `_weaknesses` / `_opportunities` / `_threats` | `list[str]` | unchanged |
| `dominant_themes` | `list[str]` | unchanged |
| `strategic_score`, `confidence` | AI-rated | unchanged — the AI rates its own analysis |
| — | — | **new** `basis: list[str]` — tickers the synthesis actually used |

`basis` feeds `Evidence.basis`, so the posture section self-labels its real scope instead of claiming the whole portfolio.

Prompt changes at `analysis/strategic_research.py:100`: request `verdict` and `detail` as separate fields, ban markdown explicitly, forbid citing the input payload (source of `[VAHN JSON]`), state the word caps. Structured output already uses Perplexity's native schema path, so the model is constrained rather than merely asked.

Rendering: family shows `verdict` plain with `detail` inside `<details><summary>Pourquoi</summary>`; the run report shows both open plus `sources` and `basis`.

**Migration:** a `mode="before"` validator promotes a bare `str` to `QualitativeBlock(verdict=<first sentence>, detail=<rest>)`, so cached exports under `output/` still load.

### 4. Coverage fixes

**4.1 fact_pack — 22 failures.** `analysis/stages/fact_pack.py:74`. The stale-cache fallback at line 68 is correct but never fired: these tickers had no cache at all, and live fetch died on 20 transport timeouts plus 8 HTTP 429s.

- Exponential backoff with jitter on 429, honoring `Retry-After`
- Concurrency throttle on Perplexity so a run stops inflicting 429s on itself. Per-item caps only — no aggregate `wait_for` around a gather, which discards completed work
- Cache warm survives across runs, so a rate-limited run degrades to stale rather than to nothing
- `@stage(retries=1)` at line 76 retries after backoff, not immediately

**4.2 volatility — 3 failures.** `config/critical_fields_config.py` lists `volatility` in `CRITICAL_FIELDS` for all three asset classes (:18, :24, :32); `deep_analysis_scorer.py` only calls `validate_critical_fields` and re-raises. (`deep_analysis_scorer.py:468` is `_get_expected_fields()`, the data-quality list — a different thing.) The collect stage already pulls price history, from which volatility is derivable. Compute it in collect rather than failing in quantify. Where history genuinely does not exist (`XTSLA`, `UNI-USD`, `POL-USD`, `S-USD`, `IMX-USD`, `GRT-USD`, `COMP-USD` — all confirmed delisted in the log), the position is legitimately unanalyzable and is refused by name.

**4.3 Discovery universe.** `discovery/universe_provider.py:89` returned 11 ETF tickers after excluding 71 holdings. Widen the dynamic universe so that **at least 50 candidates per asset class survive exclusion**; a universe that cannot meet that floor logs the shortfall rather than silently scanning a handful. The grade-C actionability threshold stays unchanged — noise stays out, and a genuinely empty result after a real search is a valid finding.

**4.4 `discovery_latest.json`.** Written by nothing; read by `tools/alternative_finder_tool.py:179` and `orchestrators/extraction/engine.py:169,192`. Discovery writes `consolidated_discovery.json` instead. Consequence: "No discovery crew output found" on every holding and empty alternatives portfolio-wide. **Resolution: point the three readers at `consolidated_discovery.json` and retire the `discovery_latest.json` name**, rather than adding a fourth writer. `infrastructure/json/to_html_converter.py:38-39` maps both names and needs the dead entry removed.

**4.5 Secondary errors, folded in because they feed coverage:**

- `data_processors.py` — `dictionary changed size during iteration` on cache metadata save; a concurrency bug that silently loses cache writes, which feeds 4.1
- `quantitative_comprehensive_analyzer.py`, `backtesting.py` — `cannot convert float NaN to integer`, `index N is out of bounds for axis 0`
- `_QualitativeInsightsRaw` — 6 OpenAI validation failures, 3 JSON repair failures

Target: coverage 64/64 minus genuinely delisted tickers, which are named.

### 5. Cost truth

`litellm.cost_per_token` cannot price `openrouter/*` models, so `record_usage` (`litellm_callback.py:104-110`) sets `cost = None` for all three crews.

Three layers, first hit wins:

1. `litellm.cost_per_token` — works for `openai/*`
2. OpenRouter's models endpoint, which publishes per-token prompt and completion prices. Cached to disk, refreshed daily. A direct `httpx` call and parse — not a crew, since it is one API call plus parsing
3. Still unknown → `cost_known=False`; renderer prints token counts plus "coût non chiffrable", never `$0.00`

Layer 3 already exists in the monitor and is discarded downstream. `Evidence.known` from §2 is where it is honored, so header, footer and cost section cannot diverge.

`Performance Metrics` (`sections/analysis.py:84-102`) reads a different object than the monitor, hence `0 LLM Calls / 0.0s`. It is fed from the same view model as everything else.

The run report surfaces the per-crew split: `deep_analysis_etf` consumed 604 calls and 8.9M tokens against `deep_analysis_stock`'s 138 calls and 1.9M — visible rather than buried in a total.

### 6. Testing

pytest-mock only; `unittest.mock` is banned and enforced by `make check-unittest-mock`.

- **Builders:** unit tests with no HTML. The 39/64 run becomes a fixture; assert `Evidence(covered=39, total=64, missing=[...])`
- **Renderers:** snapshot tests, one per artifact
- **Regression:** assert `$0.00` never renders when `known is False`; assert no `**` or `[3]` survives into output
- Coverage gates stay off AI and LLM paths — crews and prompts are excluded, never mock-covered

### 7. Risks

- **The §2 refactor touches 9 section files.** Mitigate by moving one section at a time, builders first, with the old path still rendering until its replacement passes snapshot
- **§4.1 and §4.3 contend for the same Perplexity quota.** Widening the discovery universe adds load to the dependency whose rate limit caused the 25 failures. The throttle must account for discovery load, not fact_pack alone
- **Prompt changes (§3) cannot be unit-tested for quality**, only for schema conformance. Verification requires a real `crewai flow kickoff`

## Implementation order

The spec is large. Phases are ordered so each is independently verifiable and none blocks on a later one.

1. **Coverage (§4.1, §4.2, §4.5)** — pipeline only, no report changes. Verifiable by ledger: failures drop from 25 toward 0. Lands first because every later phase wants a full-coverage run to test against.
2. **Cost truth (§5)** — monitor only, narrow blast radius. Verifiable from the log's cost summary alone.
3. **View models + builders (§2, first half)** — new code beside the old path, nothing rendered differently yet. Verifiable by unit tests on the 39/64 fixture.
4. **Renderers + two artifacts (§1, §2 second half)** — one section at a time, old path rendering until each replacement passes snapshot.
5. **Qualitative contract (§3)** — schema, validators, prompt. Last, because it needs a real kickoff to verify and its output feeds renderers built in phase 4.
6. **Discovery universe (§4.3, §4.4)** — after phase 1's throttle exists, since widening the universe adds load to the same quota.

## Done when

A full `crewai flow kickoff` produces both artifacts, with:

- coverage at 64/64 minus named delisted tickers
- no section rendering a number it cannot back
- no `$0.00` where cost is unknown
- no raw markdown or unresolved citation markers in either artifact
- family artifact in French throughout, carrying no numbers beyond the coverage line
