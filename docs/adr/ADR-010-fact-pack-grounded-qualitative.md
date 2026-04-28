# ADR-010: Fact Pack Grounded Qualitative Analysis

- **Status:** Accepted
- **Date:** 2026-04-28
- **Deciders:** FinWiz Core Team

## Context

The v0.3.0 release patched the symptom of the DELL/VMware hallucination
class: the qualitative AI claimed Dell still owned VMware (divested
November 2021) because its training data was stale and there was no
authoritative override. v0.3.0 added (a) date-anchored prompts and
(b) bounded Perplexity access for the qualitative crew. This worked
operationally but was advisory: the AI could still ignore both signals
under token pressure or with imprecise prompts.

The deeper issue: every qualitative call relied on the AI's discretion
to verify material facts about the company (current parent, subsidiaries,
recent M&A, leadership, recent events). When the AI declined to call
Perplexity (which it sometimes did to save tokens) or interpreted
ambiguous prompts loosely, hallucinations leaked through.

## Decision

Introduce a `fact_pack` pipeline stage between `quantify` and `qualify`.
Each per-holding pipeline run fetches a structured fact pack from
Perplexity (one call), caches it for 7 days, and injects the verified
facts into the qualitative prompt as the authoritative source.

The qualitative prompt template is updated to declare the fact pack
AUTORITAIRE: AI may not contradict it. Anti-hallucination becomes
structural, not advisory.

### Implementation

**Schema** (`src/finwiz/schemas/hybrid_analysis/fact_pack.py`):
- `FactPack` Pydantic model with `corporate_structure`, `recent_events`,
  `leadership`, `fetched_at`, `freshness`, `confidence`, `source_citations`
- `freshness` is Python-derived from `fetched_at` -- AI cannot lie about
  staleness (cross-checked by `model_validator`)

**Fetcher** (`src/finwiz/analysis/fact_pack_research.py`):
- `fetch_fact_pack()` async via `perplexity_structured()` (mirrors
  `strategic_research.py`'s pattern -- direct httpx + json_schema, no
  CrewAI subagent)
- Sync wrapper for non-async callers

**Cache** (`src/finwiz/cache/fact_pack_cache.py`):
- Schema-version-tagged JSON envelopes (entries with mismatched version
  trigger silent re-fetch)
- TTL via `CacheDataType.FACT_PACK = 604800` (7 days)
- `invalidate(ticker)` and `invalidate_all()` methods

**Stage** (`src/finwiz/analysis/stages/fact_pack.py`):
- `@stage(name="fact_pack", timeout_s=60, retries=1)` -- NOT
  `allow_degrade`. The trust-spine invariant from ADR-009 stays intact:
  only `qualify` may DEGRADE.
- Behavior:
  - cache fresh (<7d) -> OK with cached payload
  - cache stale (7-14d) + Perplexity OK -> OK with new payload
  - cache stale (7-14d) + Perplexity fails -> OK with cached payload,
    `freshness="stale"` (renderer maps to amber pill)
  - no cache + Perplexity fails -> raise -> @stage records FAILED ->
    `run_pipeline` short-circuits to `AnalysePending`

**Prompt template** (`src/finwiz/crews/deep_analysis/config/tasks.yaml`):
- New FACT PACK section before CONTEXT block declaring the fact pack
  AUTORITAIRE for corporate structure, recent events (12 months),
  leadership
- Existing anti-hallucination block updated to reference the fact pack
  as primary source ahead of `Description`
- Per-task Perplexity verification budget reduced from "max 2" to
  "max 1" (fact pack pre-loads common verifications)

**Report** (`src/finwiz/reporting/section_generators.py`):
- Provenance footer rendered next to rationale cell:
  - fresh -> green pill "Faits actuels"
  - recent -> neutral pill
  - stale -> amber pill + confidence rating
  - None -> muted "Faits non vérifiés" note (legacy callers only)
- Citations rendered as numbered footnote links with `rel="noopener"`
- All user-derived strings escaped via `escape()` (XSS hardening
  preserved per ADR-009 / v0.4.1)

## Consequences

### Positive

- DELL/VMware hallucination class fixed at root, pinned by
  `tests/regression/test_dell_vmware.py` (10-phrase forbidden library
  catches wishy-washy hallucination, not just literal matches).
- Cost amortized via 7-day cache: cold kickoff = 60 Perplexity calls,
  warm kickoff = 0 calls. Single $0.50-$1 cost per cold run.
- Trust-spine invariant from ADR-009 preserved: DEGRADED whitelist
  stays `{"qualify"}`. Staleness is a payload field, not an outcome
  state. The "DEGRADED is rare and intentional" structural property
  remains a load-bearing schema invariant.
- AI Minimalism aligned: fact pack collection is one Perplexity call
  with structured output (per `feedback_crewai_only_for_reasoning.md`:
  "go direct via httpx with native structured-output").

### Negative

- Cold-kickoff latency: ~2.5 minutes added on first run for 60 holdings
  (with `FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=2`). Acceptable given the
  trust value; subsequent runs amortize to 0.
- Schema migration: v0.4.0 cached `enriched.json` files won't deserialize
  with the new `fact_pack` field. Resolution: caches are ephemeral;
  `FactPackCache` version-tags entries; v5.2 silently re-fetches.
- Strategic_analysis ↔ fact_pack overlap. Both are Perplexity-fetched
  with confidence ratings. Kept separate in v5.2 (different lifecycles:
  per-run vs cached 7d, different consumers: report-only vs every
  qualitative prompt). Unification candidate for v5.3+.

### Risks

- Perplexity outages on first run for a ticker block that holding
  (AnalysePending). With 60 holdings and a 0.1% per-call failure rate,
  expected halt rate ~5-10% per kickoff. The trust-spine policy is
  deliberate: silent failure is forbidden.
- 14-day stale cap means even degraded answers stop being available
  after two weeks; force-refresh via the CLI script when needed.
- Fact pack is text-only (`recent_events: list[str]`); numeric facts
  (revenue, headcount) belong in fundamentals, not here.

## References

- Spec: `~/.claude/plans/ok-let-s-start-planning-eager-quiche.md`
- Schema: `src/finwiz/schemas/hybrid_analysis/fact_pack.py`
- Stage: `src/finwiz/analysis/stages/fact_pack.py`
- Renderer: `src/finwiz/reporting/section_generators.py:_fact_pack_provenance_footer`
- [ADR-009: Trust Spine](ADR-009-trust-spine.md) -- v5.1 stage contract
- [ADR-003: AI Minimalism](ADR-003-ai-minimalism.md) -- Python wins over AI for deterministic data
- [ADR-002: Perplexity Research Integration](ADR-002-perplexity-research-integration.md) -- baseline Perplexity pattern
