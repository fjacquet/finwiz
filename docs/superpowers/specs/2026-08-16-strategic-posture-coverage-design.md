# Strategic Posture: Correct Coverage, Dedicated Page, Safe Rendering — Design

**Date:** 2026-08-16
**Status:** Approved
**Supersedes nothing.** Extends `2026-08-15-report-rethink-design.md` (Plan B), which
established the two-artifact split and the verdict/detail contract. This spec applies
that contract to the strategic posture specifically, and fixes the data feeding it.

## Problem

The family report shows **“Score Stratégique Global 71 % · Confiance 83 %”** above a wall
of raw markdown. Every part of that line is wrong, and the prose is unreadable. Measured
against the 2026-08-16 run (`output/run_ledger/8a2ae9b9187f.jsonl`):

| Symptom | Measurement |
|---|---|
| Holdings carrying a strategic analysis | 26 of 64 |
| Serialized synthesis payload | 626,286 chars |
| Truncation applied (`_serialize_holdings`) | `[:30000]` — **4.8 % survives** |
| Tickers surviving the cut | **`['AAPL']`**, and cut mid-object |
| Raw `**markdown**` markers rendered as text | 42 |
| Dangling `[n]` citation markers | 470 |

So the portfolio-wide score is synthesized from roughly one holding's worth of malformed
JSON, and the narrative it produced discusses Disney and HPE — neither of whose data
reached the model. Those came from Perplexity's own live web search. **The section reads
as a portfolio synthesis and is actually a web search wearing the portfolio's name.**

### Why coverage was only 26 of 64

Three independent causes, none of them “the API was flaky”:

1. **Output bloat overruns our own token ceiling.** Each `strategic_analysis` is 33,505
   chars (AAPL): every one of the 18 PESTEL/SWOT/Porter sub-dimensions is a
   paragraph-length essay (`political` 1,353 chars, `swot.strategic_assessment` 2,727).
   The deep-analysis crew hits `max_tokens=40960` exactly — six times in one run — and
   fails with `Could not parse response content as the length limit was reached`, i.e.
   cut off mid-JSON. One such call cost **$0.63** and returned nothing usable.
2. **The breaker cascade.** Five consecutive crew failures open the circuit breaker
   (`crew_execution.py:166`). Because holdings run concurrently, 31 more holdings then hit
   the open breaker and fail **instantly, never attempted** — after they had already
   completed `collect`, `quantify` and `fact_pack` successfully. Ledger: 20
   `CircuitBreakerOpenError` on `deep_analysis_etf`, 11 on `deep_analysis_stock`.
3. **Structural exclusion.** `stages/__init__.py:100` — `do_strategic = ctx.asset_class ==
   "stock"`. ETFs and crypto never get strategic analysis at all: 38 of 64 holdings.

Also: 12 holdings hit the 900 s per-holding wall, a consequence of (1) — one crew run took
224 s generating prose nobody reads.

### Two defects that made the lie unreportable

- **`PortfolioStrategicPosture` has no coverage field.** The schema cannot express “this
  covers N of M holdings”, so no honest renderer could have existed.
- **`strategic_score` and `confidence` default to `0.5`.** A posture built from nothing
  reports 50 % favorability at 50 % confidence — the same fail-plausible default class as
  the `EnrichedAnalysis` `C`/`0.5`/`HOLD` bug fixed in `c2a17d1a`.

### Why the rendering is broken

`_portfolio_prompt` (`strategic_research.py:100`) contains **no output-format instruction
at all**. It asks for French narrative and never mentions markdown or HTML, so the model
emits markdown, which is interpolated into HTML unconverted.

The five crew `tasks.yaml` files *do* carry HTML instructions, and an `output-standards`
skill covers exactly this — but the strategic posture is a **direct Perplexity call, not a
crew**, so none of those conventions ever applied to it. The worst-rendering section is
the one path outside the convention.

The `[n]` markers are worse than ugly. `crewai_custom_tools.tools.web.perplexity_structured`
already returns `{"structured": ..., "citations": [...]}` — a list of URLs we request,
pay for, and discard. The markers are a credibility signal pointing at nothing.

## Non-goals

- Changing the composite scoring weights, grade bands, or `portfolio_fit_scorer`.
- Rewriting the family artifact beyond removing the posture section and linking out.
- Retrofitting the two-artifact split to sections other than posture.

---

## §1 Coverage guarantee

**Requirement: every holding gets real strategic data. No silent loss.**

### 1.1 Cap what we ask for

Change the prompts and schema so each dimension returns a rating plus short bullets, not
an essay:

| Field | Today | Target |
|---|---|---|
| `PestelAnalysis.political` … `.legal` (6) | free prose, ~1,300 chars each | `list[str]`, max 3 bullets, each ≤ 200 chars |
| `SwotAnalysis.strengths` … `.threats` (4) | unbounded lists, ~2,400 chars each | max 4 bullets, each ≤ 200 chars |
| `SwotAnalysis.strategic_assessment` | 2,727 chars | ≤ 400 chars |
| `ForceRating.rationale` (×5) | ~1,500 chars each | ≤ 250 chars |
| `FiveForcesAnalysis.competitive_position_summary` | 2,191 chars | ≤ 400 chars |

Enforced two ways, because prompts are requests and schemas are guarantees:

- the prompt states the limits explicitly;
- Pydantic validators truncate at the limit on ingest, so an over-long model response is
  clamped rather than rejected — never a parse failure, never an oversized payload.

Expected payload: ~3,000 chars per holding, **~10× smaller**. 64 holdings ≈ 190 K chars,
which fits the synthesis budget whole.

### 1.2 Timeouts must not open the breaker

In `crew_execution.py`, `TimeoutError` stops incrementing `_crew_failures`. A timeout is a
per-holding event; the breaker exists for upstream *service* failure. Parse errors and
connection errors still count.

When the breaker **is** open, a holding waits out the remaining cooldown and retries once
rather than failing immediately. Failing 31 unattempted holdings in the same instant is
the behaviour being removed.

`FINWIZ_HOLDING_TIMEOUT` (900 s) remains the outer bound, so waiting cannot run away.

### 1.3 Extend strategic analysis to every asset class

Delete the `asset_class == "stock"` gate. PESTEL/SWOT/Porter are firm-level frameworks, so
ETFs and crypto get framings that fit — same schema, different prompt:

- **ETF** — regulatory/tax regime, sector and geographic concentration, cost and tracking
  posture, liquidity. `five_forces` maps to provider competition and fee pressure.
- **Crypto** — protocol economics and issuance, regulatory posture by jurisdiction,
  network effects and developer activity, custody/counterparty risk.

Prompt selection is keyed on `asset_class`; the returned schema is unchanged, so the
synthesis and rendering paths need no per-class branching.

### 1.4 Synthesis digests, never truncates

Replace `_serialize_holdings`’s `[:30000]` slice with a digest builder:

- every covered holding contributes an entry — the holding list is never shortened;
- if the payload would exceed the budget, **per-holding detail** shrinks (bullets drop from
  3 → 2 → 1, then prose fields drop, then scores only);
- dropping a holding is not an operation the function can perform.

**Budget:** `SYNTHESIS_PAYLOAD_BUDGET_CHARS = 240_000` (≈ 60 K tokens), leaving headroom
under the synthesis model's context alongside the prompt and its response. With the §1.1
caps a 64-holding portfolio lands near 190 K chars, so the degradation ladder is a
guard-rail rather than the normal path. The constant is module-level and asserted in tests
against the caps, so raising a cap without revisiting the budget fails CI.

### 1.5 Coverage is data, and a tripwire

Add to `PortfolioStrategicPosture`:

```python
holdings_covered: int = Field(..., description="Holdings with a real strategic analysis")
holdings_total: int = Field(..., description="Holdings in the portfolio")
value_covered_pct: float = Field(..., ge=0.0, le=100.0, description="Share of portfolio value covered")
uncovered_tickers: list[str] = Field(default_factory=list, description="Named, never silently omitted")
```

All four are **required** (`Field(...)`), so a posture cannot be constructed without
stating its own coverage.

Change `strategic_score` and `confidence` from `default=0.5` to **required**. A synthesis
that produced no score must fail construction rather than assert a confident midpoint —
the `c2a17d1a` lesson.

At the end of the deep-analysis phase, if `holdings_covered < holdings_total` the run
**logs an error naming every missing ticker**. Not an excuse path: the point is that a gap
becomes impossible to ship silently, which is exactly what happened here.

---

## §2 Dedicated posture page

### 2.1 Family artifact

The posture section shrinks to three lines: one-sentence verdict, the score with its
coverage, and a link. Everything else leaves.

### 2.2 New artifact

`output/finwiz_posture_strategique.html` — self-contained, French, same CSS as the family
report (`css_styles.get_report_css()`), generated by a new
`reporting/sections/posture_page.py` and written alongside the family report.

```
Posture Stratégique — 16 août 2026
Couverture : 64 / 64 holdings · 100 % de la valeur      ← leads the page
──────────────────────────────────────────────────
🌍 Macro          « Une phrase de verdict. »
                  ▸ Détail (replié)
⚔️ Concurrence    « Une phrase de verdict. »
                  ▸ Détail (replié)
📐 SWOT           « Une phrase de verdict. »
                  ▸ Détail (replié)
──────────────────────────────────────────────────
Par ligne : une carte par holding (score + puces)
Sources : [1] url … [15] url
```

Rules:

- **Coverage leads.** It is the first thing on the page, not a footnote.
- **Two layers.** Each theme is one sentence; depth lives in `<details>`, closed by
  default — the contract from the Plan B spec.
- **Per-holding cards** give the per-line strategic detail a home, which it currently
  lacks entirely.
- **Sources resolve.** A numbered list at the foot, populated from the `citations` array.

### 2.3 Verdict sentences

The one-sentence verdict per theme is requested explicitly from the synthesis
(`macro_verdict`, `competitive_verdict`, `swot_verdict`, each ≤ 200 chars, required), not
extracted from prose by Python. Extracting a first sentence from a markdown essay is how
you get “À la date du 16 août 2026, les thèmes PESTEL transversaux affectant le
portefeuille se structurent ainsi : - **Politique / Régulation**” as a headline.

---

## §3 Markdown render boundary

### 3.1 The function

`src/finwiz/reporting/markdown_fragment.py`:

```python
def render_markdown_fragment(text: str, *, citations: list[str] | None = None) -> str:
    """Convert model markdown to safe HTML. Escape first, then allow a fixed subset."""
```

- **Escape everything first**, then apply the allowlist. Injection-safe by construction: a
  `<script>` in model output renders as visible text, never as markup. No raw-HTML
  passthrough, no model-supplied links.
- **Allowlist:** `**bold**`, `*italic*`, dash-prefixed lists, paragraph breaks. Nothing else.
- **Citations:** `[n]` becomes a superscript anchor into the page's source list when
  `citations[n-1]` exists; when it does not, the marker is **removed**, not left dangling.

### 3.2 Where it applies

At the section generators (`reporting/sections/`), not in the schema. Model output stays
clean markdown so the technical artifact and JSON exports keep reusable source text.

### 3.3 Why not ask the model for HTML

Rejected deliberately:

- it is an injection vector — Perplexity quotes live web pages into that output, and
  accepting HTML means disabling autoescape and trusting it as markup;
- it couples content to presentation, making the same text unusable in the JSON exports
  and the technical artifact;
- models are unreliable at balanced HTML and reliable at markdown; malformed HTML breaks
  the page silently, malformed markdown is merely ugly.

---

## Testing

- **Schema caps:** an over-long model response is clamped, not rejected. Property test over
  generated oversized payloads.
- **Digest never drops a holding:** given N holdings and a budget too small for full
  detail, assert all N appear in the output and only detail shrank.
- **Coverage is required:** constructing `PortfolioStrategicPosture` without coverage
  fields raises. Constructing without `strategic_score` raises.
- **Breaker:** a `TimeoutError` does not increment the failure count; a parse error does.
  An open breaker makes a holding wait rather than fail instantly.
- **Render boundary:** `<script>alert(1)</script>` in model output appears as visible text;
  unbalanced `**` does not leak; `[7]` with no `citations[6]` is removed, not rendered.
- **Regression on the real defect:** a posture built from 1 of 64 holdings must not render
  a bare “71 %” — the page states 1/64 or the run fails the tripwire.

## Risks

- **Shorter output may read as less insightful.** Mitigated by keeping per-holding detail
  on the posture page; the essays were never visible to the family anyway.
- **Extending to ETF/crypto triples strategic call volume.** Offset by the ~10× payload
  reduction; net token spend should fall. To be measured on the first full run, not
  assumed.
- **Required fields are a breaking schema change.** Every in-tree construction site must be
  updated in the same change; `model_construct()` call sites need auditing, since that is
  precisely how the `EnrichedAnalysis` default leaked to disk.
