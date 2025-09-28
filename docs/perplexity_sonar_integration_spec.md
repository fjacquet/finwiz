# Perplexity Sonar Integration Spike Specification

## 1. Overview

- **Objective**
  Validate Perplexity Sonar Search as a supplementary research capability for FinWiz analyst crews (stocks, ETFs, crypto) while keeping final reporters tool-less.
- **Scope**
  Implement an opt-in prototype that augments one upstream research tool with Sonar-derived insights, measuring content quality, latency, and operational characteristics.
- **Out of Scope**
  Permanent replacement of existing data providers, reporter-agent changes, or production rollout beyond the feature-flagged spike.

## 2. Success Criteria

- **Quality uplift**
  Sonar-sourced evidence increases freshness, breadth, or factual grounding of analyst HTML snippets (measured via manual review across ≥10 ticker runs).
- **Operational viability**
  Average response time ≤2× current provider baseline; rate-limit handling keeps failure rate <5%.
- **Cost predictability**
  Daily projected spend under target budget once usage volume is extrapolated from spike runs.

## 3. Architecture & Integration Plan

- **Entry point**
  Extend `src/finwiz/tools/enhanced_sentiment_tool.py` (or another agreed analyst tool) with a new client that can call Sonar Search.
- **Client implementation**
  - Use Perplexity Python SDK’s OpenAI-compatible client (`perplexity.Client`) configured with `PPLX_API_KEY`.
  - Prefer async request flow for concurrency with existing gatherers.
  - Limit responses to required fields (title, URL, summary) via structured output `response_format`.
  - Apply Sonar filters (e.g., `search_options={"site": "...", "date": ...}`) to match FinWiz needs (financial news, SEC filings).
- **Feature flag**
  - Add `PERPLEXITY_RESEARCH` boolean flag to `src/finwiz/utils/feature_flags.py` and doc updates in `docs/feature_flags_guide.md`.
  - Default `False`; when disabled, tool must behave exactly as today.
- **Configuration**
  - Store API key in `.env` as `PPLX_API_KEY=...`.
  - Document setup in `DOCUMENTATION_UPDATES.md`.
- **Data flow**
  - Upstream analyst agent triggers tool; tool fetches data from existing sources plus Sonar (if flag on).
  - Combine and normalize Sonar results into the tool’s standard output contract (respecting CR-2025-08-09 schemas).
  - Reporter agents consume enriched context without new tools.

## 4. Observability & Safeguards

- **Logging**
  - Log request latency, HTTP status, result count (redact content).
  - Emit warnings on rate-limit (HTTP 429) or quota exhaustion.
- **Error handling**
  - Implement exponential backoff per Perplexity best practices.
  - On persistent failure, fallback to existing provider only; do not degrade reporter flow.
- **Monitoring hooks**
  - Capture usage metrics via FinWiz telemetry (pending integration approval).
  - Track flag adoption in experiment dashboard.

## 5. Validation Plan

1. **Unit tests**
   - Mock Sonar HTTP responses to validate success, error, and timeout paths.
   - Add tests under `tests/tools/test_enhanced_sentiment_tool.py`.
2. **Manual benchmarking**
   - Run 10 manual crew executions (stocks/ETFs/crypto) with flag on/off.
   - Compare freshness of articles, citation coverage, and review latency.
3. **Quality review**
   - Reviewer checks whether reporter HTML cites Sonar sources properly, following `docs/output_formatting_guide.md`.

## 6. Rollout & Timeline

- **Phase 0 (Prep)**
  - Secure Tier access, set up API key, finish documentation updates.
- **Phase 1 (Implementation)**
  - Develop client, flag logic, tests.
- **Phase 2 (Spike evaluation)**
  - Run manual benchmarks, collect qualitative feedback, estimate costs.
- **Phase 3 (Decision)**
  - Present findings to FinWiz leads.
  - If positive, draft follow-up change request for broader rollout across tools/crews.

## 7. Risks & Mitigations

- **Rate limits / tier restrictions**
  Mitigation: Backoff + queueing; pre-check with Perplexity account team.
- **Cost overrun**
  Mitigation: Strict query limits during spike; log request counts for forecasting.
- **API dependency sprawl**
  Mitigation: Confine integration to optional flag; evaluate consolidation with existing providers before expansion.
- **Compliance with FinWiz principles**
  Reporter remains tool-less; translation agent unaffected; HTML structure unchanged.

## 8. Open Questions

- Which specific analyst tool yields the highest ROI for enrichment? (Default chosen: `enhanced_sentiment_tool.py`; confirm with product lead.)
- Required usage tier for structured output? (Check Perplexity plan details.)
- Need for caching to control spend? (Assess after spike metrics.)

---

**Next steps**: Approve specification, set up API credentials, and proceed with Phase 0 tasks.
