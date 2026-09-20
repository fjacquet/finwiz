# Design: OpenRouter web-grounded research replaces Perplexity Sonar

**Date:** 2026-09-20
**Status:** approved
**Path:** architectural (new provider client behind an existing seam; Perplexity
kept as fallback)

## Problem

Perplexity Sonar Pro is called directly (`api.perplexity.ai`, `PPLX_API_KEY`) from
four places:

| Call site | Calls per run (67 holdings) | Seam |
|---|---|---|
| SWOT + Porter, `analysis/strategic_research.py` | 134 | `perplexity_with_retry` |
| Portfolio posture, same file | 1 | `perplexity_with_retry` |
| Fact-pack gap-fill, `analysis/fact_pack/sources/perplexity_source.py` | ~6 | `perplexity_with_retry` |
| Sentiment news, `tools/perplexity_analysis_integration.py` | up to 67, gated by `FF_PERPLEXITY_RESEARCH` | `PerplexitySearchTool` (vendored) |

Sonar Pro is priced at $3 / $15 per million tokens plus $5 per thousand searches,
roughly $0.026 per SWOT-size call, about **$3.5 per run**, and none of it appears
in `output/run_summary.json`: the cost tracker only sees CrewAI kickoffs.

Everything else already runs on `openrouter/google/gemini-3.8-flash`. OpenRouter
exposes web search for that model through the `web` plugin and returns exact cost
on every response. A live spike on 2026-09-20 confirmed, on three calls:

- `plugins: [{"id": "web", "engine": "exa", "max_results": 5}]` and
  `response_format: {"type": "json_schema", ...strict}` work in the same request.
- The response validates against `SwotAnalysis` unchanged.
- `choices[0].message.annotations` carries 5 `url_citation` entries.
- `usage.cost` is present; SWOT-size call $0.017 (Exa injects ~3k prompt tokens and
  bills $0.007). Estimated **$2.3 per run** for the 135 structured calls, visible in
  the cost summary.

## Decisions taken in the brainstorm

- Scope: all four call sites.
- Engine: Exa, 8 results. Native Google grounding ($0.014 per search, no domain
  filter) and the Perplexity engine were considered and rejected on cost.
- Fallback: after OpenRouter retries are exhausted, one Perplexity attempt when a
  PPLX key is configured. No `RESEARCH_PROVIDER` switch.
- CrewAI `LLM` routing was rejected: it hides `usage.cost` and citations and adds
  the agent stack to a single API call (see memory: CrewAI only for reasoning).

## Design

### 1. Client — `infrastructure/research/openrouter_structured.py`

```text
@dataclass(frozen=True)
class SearchOptions:
    engine: str = "exa"
    max_results: int = RESEARCH_WEB_MAX_RESULTS  (env, default 8)
    recency_hint: str | None = None   # "month" | "week" | None

@dataclass(frozen=True)
class ResearchResult[T: BaseModel]:
    data: T
    citations: tuple[str, ...]        # url_citation.url, order preserved, deduplicated
    cost_usd: float | None            # usage.cost
    prompt_tokens: int
    completion_tokens: int

async def openrouter_structured[T: BaseModel](
    *, prompt: str, schema: type[T], system: str,
    search: SearchOptions | None = SearchOptions(),
    timeout: float = 60.0, api_key: str | None = None,
) -> ResearchResult[T] | None
```

- One `httpx.AsyncClient.post` to `https://openrouter.ai/api/v1/chat/completions`
  (`RESEARCH_BASE_URL` overridable for tests). Headers: bearer key,
  `HTTP-Referer`/`X-Title` set to the project, as OpenRouter recommends.
- Body: `model` from `RESEARCH_MODEL` (default `google/gemini-3.8-flash`, no
  `openrouter/` prefix: this is the raw API, not litellm), `messages`
  system+user, `response_format` json_schema strict with
  `schema.model_json_schema()`, `max_tokens` 4 000, `plugins` when `search` is set.
- `recency_hint` becomes one sentence appended to the user prompt ("Ne retiens que
  des sources publiées au cours du dernier mois.") because the Exa engine has no
  recency parameter on OpenRouter.
- Returns `None` on any HTTP, transport, JSON or Pydantic failure, logged at
  WARNING with schema name and status code. Raises `ValueError` only when
  `OPENROUTER_API_KEY` is missing, mirroring the Perplexity client, so the retry
  wrapper can fail fast.
- Never logs the prompt body or the key; the sanitizer already redacts
  `OPENROUTER_API_KEY`.

### 2. Retry and fallback — `infrastructure/resilience/research_retry.py`

```text
RESEARCH_CONCURRENCY = max(1, int(os.getenv("RESEARCH_CONCURRENCY", "6")))

async def research_with_retry[T: BaseModel](
    *, prompt, schema, system, search_recency_filter="month",
    timeout=15.0, max_attempts=4, base_delay=1.0, kind: str = "research",
) -> ResearchResult[T] | None
```

- Same keyword surface as `perplexity_with_retry`, plus `kind` for cost
  attribution.
- Throttle: a process-wide `threading.BoundedSemaphore(RESEARCH_CONCURRENCY)`
  built the same way as `get_perplexity_semaphore` (thread-per-holding event
  loops make `asyncio.Semaphore` unusable; that docstring is reused).
- Loop `max_attempts` over `openrouter_structured` with the existing
  `PerplexityFallbackManager.calculate_backoff_delay` (renamed import only if the
  helper moves; otherwise reuse as is).
- On exhaustion, if `PERPLEXITY_API_KEY`/`PPLX_API_KEY` is set, one call to
  `perplexity_with_retry(max_attempts=1)` and wrap its result in a
  `ResearchResult` with `citations=()` and `cost_usd=None`. Log which provider
  answered.
- Each successful OpenRouter call records cost (section 5).
- `perplexity_retry.py` stays, docstring rewritten: "fallback provider; primary
  is `research_retry`".

### 3. Structured call sites

- `analysis/strategic_research.py`: three `perplexity_with_retry(...)` calls become
  `research_with_retry(..., kind="swot" | "porter" | "posture")` and unwrap
  `.data`. `SYSTEM_FR` unchanged. Citations ignored for SWOT/Porter for now (the
  schemas have no field for them; adding one is a report change, out of scope).
- `analysis/fact_pack/sources/perplexity_source.py` renamed
  `research_source.py`; `fetch_missing_events` unchanged in signature, uses
  `kind="factpack"`. `analysis/fact_pack/composer.py` consumes only the event
  strings and tags provenance with the literal `"perplexity.gap_fill"`; that tag
  becomes `"research.gap_fill"` (the report renders it, grep
  `reporting/sections/factpack.py` and its tests for the old literal). Citations
  stay unused here.
- `analysis/fact_pack_research.py` docstring and the `_SYSTEM_FR` reference
  updated; `_FactPackRaw` reused as the schema.

### 4. Sentiment news — `tools/perplexity_analysis_integration.py`

- `__init__`: availability = OpenRouter key present, else Perplexity tool
  constructible. Keep the class and file names to avoid touching four tool
  modules that import it; update the module docstring.
- `search_financial_news`: call `research_with_retry` with a minimal
  `NewsDigest` schema (`headlines: list[{title, url, one_line_summary}]`,
  ≤ `max_results`) and `kind="news"`. Build citation dicts
  `{"title", "url", "snippet"}` from `ResearchResult.citations` merged with the
  digest, then feed them through the existing `_create_sonar_article` so
  `SonarArticle` / `SonarSearchResult` and `standardized_sentiment_tool.py` are
  untouched.
- `sonar-small-chat` model string disappears with the `PerplexitySearchTool`
  call path; the tool object is kept only for the fallback branch inside
  `research_with_retry`, not called here directly.
- `FF_PERPLEXITY_RESEARCH` keeps gating this path (flag name unchanged; the
  definition's description says "web research", root CLAUDE.md note updated).

### 5. Cost tracking

- `infrastructure/monitoring/litellm_callback.py`: `record_usage(crew_name,
  token_usage, model=None, *, cost_usd: float | None = None)`. When `cost_usd`
  is given, use it instead of the litellm price lookup and mark the crew priced.
- `research_with_retry` calls it with `crew_name=f"research_{kind}"` and a small
  usage object (`prompt_tokens`, `completion_tokens`, `successful_requests=1`).
- Perplexity fallback calls record tokens with `cost_usd=None` so the summary
  shows `cost n/a` for them, as today's honesty rule requires.
- `run_summary.json` and the report's "Coût réel" section pick this up with no
  change: they iterate the tracker's crew map.

### 6. Config and docs

- `.env.example`: `RESEARCH_MODEL=google/gemini-3.8-flash`,
  `RESEARCH_CONCURRENCY=6`, `RESEARCH_WEB_MAX_RESULTS=8`; `PPLX_API_KEY` comment
  becomes "optional, fallback only".
- `docs/adr/ADR-012-openrouter-research-provider.md`: supersedes the provider
  choice in ADR-002 (Perplexity research integration); ADR-002 gets a
  "Superseded by ADR-012 for the provider" status line.
- `CHANGELOG.md` Unreleased; root `CLAUDE.md` env block (the
  `FF_PERPLEXITY_RESEARCH` paragraph now describes OpenRouter web research with
  Perplexity fallback); `docs/how-to/setup_environment.md`,
  `docs/development/dependencies.md` where they list the Perplexity key as
  required.
- Memory rule "never show API keys" applies to every log line and test fixture.

### 7. Testing

Unit (pytest-mock only, `httpx.MockTransport` or `mocker.patch` at the client
seam, no network):

- Client: 200 valid → `ResearchResult` with citations deduplicated and cost;
  200 with schema-invalid content → `None`; 429 → `None`; transport error →
  `None`; missing key → `ValueError`; `search=None` omits `plugins`.
- Retry: three failures then success; exhaustion with PPLX key → Perplexity
  called once and result wrapped; exhaustion without key → `None`; semaphore
  honoured (`RESEARCH_CONCURRENCY=1` serialises two concurrent calls).
- Call sites: `strategic_research` tests keep passing with the seam patched to
  `research_with_retry`; `test_strategic_research_retry.py` adapted; fact-pack
  gap-fill test renamed.
- Sentiment: annotations → `SonarArticle` mapping, URL validation still applied,
  empty digest → `success=False`.
- Cost: `record_usage(cost_usd=...)` accumulates and marks priced.

Integration (marker `integration`, skipped without `OPENROUTER_API_KEY`): one
live SWOT call for a fixed ticker asserting schema validity and `cost_usd > 0`.

## Verification

1. `make check`, `uv run mypy src/finwiz`, `uvx vulture src/finwiz
   --min-confidence 80`.
2. Three-CSV `$0.04` pipeline run: posture page renders, SWOT/Porter present for
   the three holdings, `run_summary.json` lists `research_swot`, `research_porter`,
   `research_posture` with non-zero cost.
3. One run with `OPENROUTER_API_KEY` unset and PPLX set: fallback path produces the
   same sections, cost shows `n/a` for research crews.

## Out of scope

- Adding citation fields to `SwotAnalysis` / `FiveForcesAnalysis` and rendering
  them.
- Removing the Perplexity client and key entirely (user chose fallback).
- Reading exact `usage.cost` for CrewAI kickoffs (see the cache spec).
