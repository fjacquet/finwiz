# CrewAI at FinWiz — Spirit, Inputs, Outputs, and Best Practices

Date: 2025-08-09 22:32 CEST
Audience: FinWiz maintainers and contributors

---

## TL;DR Checklist

- __Spirit__: KISS • YAGNI • Config-first • Minimal tools • Evidence-based • Final reporter has no tools
- __Inputs (“In”)__: YAML agents/tasks • Settings/env • Upstream context • Tool factories • Contracts (Pydantic)
- __Outputs (“Out”)__: Structured context from crews • Strict schemas • Tool-less final HTML per `docs/output_formatting_guide.md`
- __CrewAI Flow__: Async by default; final step synchronous; clear transitions; cache where costly
- __Testing__: Pytest unit by default; integration via markers; contract tests for YAML/schema keys

---

## The Spirit

- __Elegant minimalism (“Light as a haiku”)__: Minimize dependencies, keep flows simple, choose clarity over cleverness.
- __Configuration-driven__: Prefer YAML-configured agents/tasks over hard-coded logic; code is orchestration & validation.
- __Separation of concerns__: Specialized crews research; the report crew synthesizes and formats only.
- __Tool hygiene__: Curate small, focused toolsets via factories; never give tools to the final reporter.
- __Evidence & provenance__: Always include citations and as-of dates where applicable (SEC, factsheets, news).
- __Standards & contracts__: Use strict Pydantic v2 models and stable context keys between crews and reporter.

Reference: `docs/DESIGN_PRINCIPLES.md`

---

## The In (Inputs)

- __Configuration__
  - `agents.yaml` and `tasks.yaml` in each crew directory (e.g., `src/finwiz/crews/stock_crew/config/`)
  - Central `settings.py` for paths, flags, thresholds; env vars override

- __Data & parameters__
  - User-provided lists (e.g., `data/stock.csv`, `data/etf.csv` with `Name,Ticker,Currency`)
  - Feature flags (e.g., `PORTFOLIO_REVIEW_ENABLED`) and thresholds (`KEEP_THRESHOLD`, etc.)

- __Tools__
  - Domain tool factories under `src/finwiz/tools/` (e.g., Yahoo Finance, SEC, web search/scrape)
  - Inject tools into research crews only; final reporter: `tools == []`

- __Contracts & schemas__
  - Pydantic v2 models for cross-crew context; `model_config = {'strict': True}` (rollout with `VALIDATION_STRICTNESS=warn` if needed)
  - Examples: `ten_k_insights[]`, `market_sentiment`, `risk_score_standardized`, ETF factsheet fields

- __Flow orchestration__
  - Orchestrators coordinate crews and aggregate context; keep thin and testable
  - Prefer async I/O tasks; final synchronous reporter (CrewAI sequential constraint)

---

## The Out (Outputs)

- __Specialized crews__
  - Emit structured, validated context (not final HTML)
  - Include provenance: URLs, filed dates, as-of timestamps

- __Final report (report crew)__
  - Tool-less agent consumes upstream context only
  - Produce HTML per `docs/output_formatting_guide.md` (sections, emojis, structure, UTF-8)
  - Examples of required sections: “Synthèse 10-K”, “Sentiment du Marché”, portfolio review (“Conserver ou Vendre”)

- __Artifacts & runtime dirs__
  - Keep Python under `src/`; artifacts at root: `knowledge/`, `logs/`, `output/`, `archive/`, `storage/`

---

## Best of CrewAI (FinWiz Patterns)

- __Config-first crews__: Define agents/tasks in YAML; code wires tools and validation only
- __Thin orchestrators__: Read inputs, run crews, merge context, enforce contracts, hand off to reporter
- __Async where it matters__: Parallelize network-bound steps; keep final sequential step synchronous
- __Strict schemas & contract tests__: Lock cross-crew keys with Pydantic and pytest contract tests
- __Tool factories__: Centralize tool provisioning; avoid ad-hoc tool instantiation inside tasks
- __Caching & cost control__: Short TTL cache for repeated queries (e.g., 30–60 minutes)
- __Determinism & idempotency__: Stable sort keys, seeded randomness where used, predictable outputs for tests
- __Error handling__: Fail fast with clear messages; surface remediation hints (bad ticker, network, schema mismatch)
- __Testing discipline__: `tests/` with unit tests by default; `@pytest.mark.integration` for external I/O; run via `uv run pytest`

---

## Anti‑Patterns

- Reporter performing external research or using tools
- Mixing code and config (hard-coding prompts or tasks in Python when YAML is available)
- Large, monolithic tools that blend scraping, parsing, and analysis without seams
- Hidden global state or inline imports; unpredictable side effects
- Unversioned schema changes that break the reporter

---

## Common Flows (Examples)

- __Stock research flow__
  - Screen → SEC 10‑K excerpts (`ten_k_insights[]`) → Sentiment (`market_sentiment`) → Risk normalization → Reporter

- __ETF research flow__
  - Factsheet parse (expense ratio, replication, top holdings, as_of) → Risk normalization → Reporter

- __Portfolio review flow__
  - Ingest CSV holdings → Validate tickers (Yahoo) → Per‑holding analysis via Stock/ETF crews → Decision policy (KEEP/SELL) → Alternatives (from screeners) → Reporter HTML section

---

## Quick Start (Contributor)

1) Read `docs/DESIGN_PRINCIPLES.md` and `docs/output_formatting_guide.md`
2) Add/modify crew YAML under `src/finwiz/crews/<crew>/config/{agents.yaml,tasks.yaml}`
3) Keep final reporter tools empty; add or adjust reporter sections in YAML
4) Add/adjust schemas under `src/finwiz/schemas/`; prefer strict Pydantic v2
5) Write tests in `tests/`; mark I/O with `@pytest.mark.integration`; run `uv run pytest`
6) For new flows, add a thin orchestrator under `src/finwiz/orchestrators/`

---

## Glossary

- __Crew__: A group of agents and tasks targeting a domain (Stock, ETF, Crypto, Report)
- __Agent__: Role with a backstory, goal, and optional tools
- __Task__: Work unit executed by an agent, often with tools
- __Reporter__: Final, tool‑less agent that assembles HTML output
- __Contract__: Agreed keys/shape of context between crews and reporter

---

References:

- `docs/DESIGN_PRINCIPLES.md`
- `docs/output_formatting_guide.md`
- `src/finwiz/tools/` (tool factories)
- `tests/` (unit/integration structure)
