# ADR-012: OpenRouter Web-Grounded Research Provider

- **Status:** Accepted
- **Date:** 2026-09-20
- **Deciders:** FinWiz Core Team
- **Supersedes:** the provider choice in ADR-002 (Perplexity Research Integration)

## Context

Four call sites asked Perplexity Sonar Pro for web-grounded structured answers:
SWOT and Porter per holding, the portfolio posture, the equity fact-pack gap-fill,
and the sentiment news search. At 67 holdings that is about 135 structured calls
plus up to 67 news searches per run, priced at $3 / $15 per million tokens plus
$5 per thousand searches, roughly $3.5 per run. None of it appeared in
`output/run_summary.json`: the cost tracker only sees CrewAI kickoffs.

Everything else in FinWiz already runs on `openrouter/google/gemini-3.8-flash`.
OpenRouter exposes web search for that model through its `web` plugin and returns
the exact cost of each request in `usage.cost`. A live spike on 2026-09-20
confirmed that the plugin and a strict `json_schema` response format work in the
same request, that the reply validates against `SwotAnalysis` unchanged, that
`url_citation` annotations are returned, and that a SWOT-size call costs about
$0.017.

## Decision

- `infrastructure/research/openrouter_structured.py` makes one `httpx` POST to
  OpenRouter with `plugins: [{"id": "web", "engine": "exa", "max_results": 8}]`
  and `response_format: json_schema` (strict), returning the validated model,
  the deduplicated citations and `usage.cost`.
- `infrastructure/resilience/research_retry.py` wraps it with the same retry,
  backoff and process-wide throttle shape as `perplexity_retry.py`, records the
  exact cost under `research_<kind>` in the run cost summary, and falls back to
  one Perplexity attempt when a `PPLX_API_KEY` / `PERPLEXITY_API_KEY` is set.
- All four call sites use `research_with_retry`. The Perplexity client stays as
  the fallback; there is no provider switch.
- Engine: Exa. Native Google grounding ($0.014 per search, no domain filter) and
  the Perplexity engine were rejected on cost.
- CrewAI `LLM` routing was rejected: it hides `usage.cost` and the citations and
  adds an agent stack to a single API call.

## Consequences

### Positive

- Research cost drops from about $3.5 to about $2.3 per run and becomes visible
  in `run_summary.json` and the report's cost section.
- One provider and one key for every LLM call in a default setup; Perplexity
  becomes optional.
- Citations are available to callers for future rendering.

### Negative

- Exa injects about 3 000 prompt tokens per call; `RESEARCH_WEB_MAX_RESULTS`
  trades grounding breadth for cost.
- The Exa engine has no recency parameter on OpenRouter; the window is expressed
  in the prompt, which is weaker than Perplexity's `search_recency_filter`.

### Risks

- OpenRouter plugin or annotation contract changes break the client; the unit
  tests pin the request body and the response parsing, and one integration test
  (skipped without a key) exercises the live contract.
- Strict mode was verified accepted on `google/gemini-3.8-flash` for
  `SwotAnalysis` and `_FactPackRaw`, but OpenRouter does not reject
  non-conformant schemas for this model, so the reply is validated by
  Pydantic and the score floats are clamped before validation; other
  providers may reject the schema outright (`RESEARCH_MODEL` overrides are
  unverified).

## References

- `src/finwiz/infrastructure/research/openrouter_structured.py`
- `src/finwiz/infrastructure/resilience/research_retry.py`
- `docs/superpowers/specs/2026-09-20-openrouter-research-provider-design.md`
- ADR-002 (superseded for the provider choice), ADR-001 (OpenRouter as LLM provider)
