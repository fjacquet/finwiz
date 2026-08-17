# Changelog

All notable changes to the FinWiz project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [5.13.0] - 2026-08-17

Strategic posture coverage (PR #138). 13 tasks plus a whole-branch review and a
CodeRabbit pass. **Validated against a live `crewai flow kickoff` run of 64
holdings** — the defects below were found by that run, not only by review.

The headline: the portfolio's strategic posture was synthesized from **1 of 64
holdings** while reporting itself as complete. It now covers 64/64.

### Added

- Dedicated strategic posture page (`reporting/sections/posture_page.py`):
  coverage banner first, verdicts in the open, analyst-length synthesis behind
  `<details>`, per-holding PESTEL/SWOT/Porter score table with a plain-language
  legend, and a sources list.
- Escape-first markdown render boundary (`reporting/markdown_fragment.py`), so
  model-authored text reaches HTML as rendered markup instead of literal `**`
  and `[1]` markers. `_is_safe_url` gates every citation URL on both surfaces.
- ETF- and crypto-specific strategic framings, instead of applying the equity
  framing to every asset class.
- `LLM_MAX_TOKENS_DEEP_ANALYSIS` (default 8192), sized from measured output:
  ~800 tokens median, 4.5k p90, 5.1k max. Was 40960/61440.

### Fixed

- Strategic synthesis digested every holding instead of truncating to one. The
  family artifact's posture section dropped from 17,818 to 869 characters, with
  zero raw `**` and zero unresolved `[n]` markers.
- Strategic framework research now routes through `perplexity_with_retry`
  (bounded retries, exponential backoff, concurrency throttle) instead of
  calling `perplexity_structured` directly. The live run lost all three
  frameworks for two holdings to 429s; the wrapper already existed and was
  simply not called. Attempts capped at 3 to stay inside the holding budget.
- The deep-analysis crew can no longer author `strategic_analysis` it was never
  asked for — the field is gone from the crew's output schema. Citation density
  (0 markers vs 38–82) proved the LLM was filling it from the schema whenever
  Perplexity failed.
- Value-weighted coverage is computed from real holdings and duplicate tickers
  are summed rather than collapsed; an all-`None` `StrategicAnalysis` counts as
  no evidence, not as full coverage. Coverage identity is enforced in the
  schema, not trusted from callers.
- A failed posture synthesis is now visible to the reader instead of silently
  rendering as a confident empty result.
- Crew circuit breaker reworked: timeouts no longer open it, queued holdings
  wait out the cooldown instead of failing immediately, and the recovery
  timeout is configurable via `FINWIZ_CIRCUIT_BREAKER_RECOVERY`.
- `_coerce_str_list` no longer silently discards non-list data.
- Trust-banner states now have distinct CSS rules; `.verdict` is styled.

### Changed

- `FINWIZ_PARALLEL_LIMIT` default 10 → 4, to keep per-holding retry budgets
  inside their timeout headroom.
- Strategic fields are capped in the schema, so an over-long model response is
  clamped rather than lost.
- `vulture` added as a pre-commit hook; `tests/conftest.py` now isolates
  `PERPLEXITY_API_KEY` and friends so a developer `.env` cannot make a test
  pass that would fail in CI.

## [5.12.0] - 2026-08-16

Pipeline coverage pass (PR #130) + repository hygiene. 16 tasks, 39 commits,
whole-branch review and five rounds of CodeRabbit triage. Test suite 4802 →
4924 passing.

**Not yet validated against a live run.** The coverage claim below is backed by
unit tests and code review, not by a `crewai flow kickoff` against real market
data.

### Added

- Perplexity retry wrapper with exponential backoff and a concurrency cap. The
  throttle is a `threading.BoundedSemaphore`, not an `asyncio.Semaphore`:
  production gives each holding its own event loop (one holding per
  `ThreadPoolExecutor` worker) and an asyncio primitive binds to the first loop
  that contends on it — which silently dropped 5 of 10 holdings and deadlocked a
  worker, with no rate limit involved.
- Volatility is derived from real price history in the technical fallback,
  before the critical-field gate, so a recoverable holding is no longer refused
  for a field the pipeline already had the inputs to compute.
- `output/discovery/scored_*.json` persists the full scored candidate list
  *before* filtering, so a zero-opportunity run is auditable rather than opaque.
- Minimum universe size (50) with an explicit shortfall log.

### Fixed

- Fact-pack unavailability is classified transient, so the declared retry
  actually runs; the stale-cache window widened to 90 days so an older fact pack
  can rescue a rate-limited run.
- A successful discovery run no longer renders as "No A+ opportunities
  identified". Three layered extraction seams, each only visible once the
  previous was fixed: the `opportunities` key was not accepted as a candidate
  container, `ticker` was not accepted as a `symbol` fallback, and absent
  `cost_metrics.ter` / `market_cap_usd` were read as zeros.
- A malformed candidate no longer zeroes its whole asset class — the `try` moved
  from the extraction loop to the individual candidate.
- Percent-scaled volatility is normalized rather than rejected as absurd;
  non-finite values (`NaN`, `inf`) are refused. A fabricated `0.0` previously
  defeated three defenses in sequence and scored an unanalysable holding as the
  safest in the portfolio.
- Percent-scaled `max_drawdown` no longer leaks into the risk scorer.
- Technical, backtest, and performance analysis are isolated, so one failure no
  longer drops the entire payload.
- Cache metadata is snapshotted before serialization (`default=str`): the
  C-accelerated JSON encoder does not raise on mid-serialize mutation, it
  silently writes inconsistent output.
- Seed-ETF override is honored for ETFs; ticker hygiene applied to the mined
  universe.
- A refused holding is no longer persisted as `C` / `0.5` / `HOLD`. When an
  upstream stage failed, the pipeline returned a bare
  `EnrichedAnalysis.model_construct()`, which took the schema defaults and wrote
  them to `{TICKER}_enriched.json` — the artifact the report and every
  downstream consumer read. A holding the pipeline had explicitly refused was
  therefore recorded as a confident middling hold, with `ticker: ""` and both
  analysis sections `null`, while the `DeepAnalysisResult` beside it correctly
  said `N/A` / `0.0` / `WAIT`. The refusal is now built explicitly and carries
  the upstream failure reason, and the schema's own defaults are a refusal
  (`N/A` / `0.0` / `WAIT`) so a forgotten field can never again read as a
  recommendation. Found by inspecting the 2026-08-16 run, where 24 holdings
  were each written out as C/HOLD.
- README badges: the CI badge pointed at a `quality.yml` workflow that does not
  exist, Python was listed as 3.12 against a `>=3.13,<3.14` floor, coverage was
  a stale hand-written 72%, and the MIT badge linked to a `LICENSE` file that
  was never committed.

### Removed

- Hardcoded A+ fabrication in the ETF, stock, and crypto analyzers. A failed
  newcomer discovery now returns `method: "newcomer_discovery_failed"` with an
  `error` key instead of inventing opportunities.
- `discovery_latest.json` dead template mapping.
- 31 obsolete documentation files, including the `investment_discovery/` and
  `portfolio_rebalancing/` trees, with mkdocs nav and inbound links repaired.

### Added (packaging)

- `LICENSE` (MIT) and the corresponding `license` / `license-files` metadata in
  `pyproject.toml`. Both were missing despite the README advertising MIT since
  the first release.

### Known limitations

Three of these were found by inspecting a live `crewai flow kickoff` on
2026-08-16. That run executed a pre-merge build, so it did not exercise the
fixes above — but the defects below were confirmed against the merged source
and are live in this release.

- **A Perplexity failure discards completed Python work.** When `fact_pack`
  fails, `stages/__init__.py` short-circuits the whole holding to pending, even
  though `collect` and `quantify` had already succeeded. In the observed run 24
  of 61 holdings were lost this way while their deterministic scoring was
  already done. This inverts AI Minimalism: the $0 deterministic half is held
  hostage by the flaky AI half. The fix is to emit a partial verdict carrying
  the quantitative scores with the qualitative section marked unavailable.
- **The orchestrator counts placeholders as analyses**, logging
  `Deep analysis complete: 64/64 holdings analyzed` when 27 were pending
  placeholders.
- **Perplexity transport errors log an empty message**
  (`Perplexity transport error for _FactPackRaw:`), so a failing run gives no
  indication of why.
- Discovery still surfaces few or no opportunities. `composite_score =
  standalone_factor × portfolio_fit` uses fit as a full-range multiplier, but
  fit's practical ceiling is ~0.75 (its diversification term is `1 − max_corr`,
  and cross-asset correlation is rarely below 0.3). Every candidate is therefore
  deflated ~25% before any gate: a +30% six-month performer in an unheld sector
  at 0.70 correlation scores 0.579 and is dropped as grade D. Task 13 recalibrated
  `factor`; the composition itself is an open `portfolio_fit_scorer` design
  question.

## [5.11.0] - 2026-08-10

Dependency and supply-chain maintenance. Released without a changelog entry or
a `pyproject.toml` version bump; recorded here retroactively.

### Fixed

- 10 Dependabot alerts cleared across two passes (GitPython 3.1.58,
  cryptography, lxml) plus a full `uv.lock` upgrade.
- Dockerfile installs `git` so the `crewai-custom-tools` git dependency
  resolves; base image names fully qualified for Podman.

### Changed

- Dependency floors raised: crewai >=1.15.12, pandas >=3.0.5, numpy >=2.5.1,
  scipy >=1.18.0, litellm >=1.94.1, aiohttp >=3.14.3, ta-lib >=0.7.1,
  quantlib >=1.43, gnews >=0.8.2, pymdown-extensions >=11.0.1, and the
  langchain-core / pyportfolioopt / mypy / faker / types-requests /
  scipy-stubs / cyclonedx-bom dev floors.
- Dependabot auto-merge uses rebase instead of squash.

## [5.10.0] - 2026-07-16

Deep-analysis latency pass (PR #100) + post-migration documentation cleanup (PR #101).

### Added

- `LLM_REASONING_EFFORT` (default `low`, values `low|medium|high|none`): reasoning
  effort is now explicitly pinned on every LLM construction instead of inherited
  from provider defaults — hybrid-reasoning models (glm-5.2, qwen3.7) no longer
  spend uncontrolled thinking tokens on qualitative-synthesis calls. Sent via
  OpenRouter's `reasoning` passthrough; `none` sends nothing; non-OpenRouter
  routes untouched.
- JSON repair now fixes the duplicated-leading-brace pattern some LLMs emit
  (`{` newline `{…`), turning previously unrepairable full-call retries into
  instant repairs.
- `docs/development/dependencies.md` documents the centralized-tools package:
  git-tag pin, wave→release mapping, and the local `[tool.uv.sources]`
  co-development override.

### Fixed

- mkdocs nav pointed the three Investment Discovery entries at placeholder
  stubs while the real guides sat outside the nav — repointed, stubs deleted,
  dangling cross-links fixed.
- 60 stale documentation references from the tool-centralization migration
  (dead feature-flag names, deleted module paths, tools misattributed to
  finwiz that now live in crewai-custom-tools).

### Removed

- Dead `_get_thinking_params()`/`THINKING_CAPABLE_MODELS` subsystem
  (superseded by `LLM_REASONING_EFFORT`).

## [5.9.0] - 2026-07-15

Tool centralization: all reusable tools now come from
[crewai-custom-tools](https://github.com/fjacquet/crewai-custom-tools) v0.6.0
(git-tag pin). Delivered as four waves (PRs #97, #98, #99); full acceptance
`crewai flow kickoff` compared against the 5.8.0 baseline — structural parity,
zero tool-related failures.

### Changed

- Yahoo Finance ×5, Perplexity ×2, AlphaVantage, TwelveData ×2, Kraken,
  ChartImg, ticker validation, Enhanced ETF/Crypto/SEC, DeFi (now real
  DeFiLlama), sentiment, risk scoring, file tools, valuation, ETF analysis,
  compliance, position sizing, price targets, and the A+ grading/screening
  cluster now delegate to the central package (thin wrappers where finwiz
  enrichment is preserved).
- Rate limiting now uses the central bounded token-bucket registry
  (`asyncio.to_thread` at async call sites); API-key fail-fast uses central
  `require_api_key`.
- Crew task prose updated to real tool names and 0-5 risk scale notes.

### Removed

- Local rate-limiter stack, `api_decorators`, `api_key_validation`, the no-op
  LLM retry chain (`crewai_retry_patch`, `llm_retry`), np.random placeholder
  tools (Optimization, RiskAssessment), dead `chart_analyzer`/`charts/`,
  `twelve_data/` chain, `freshness_validated_tool`, orphaned schemas/endpoints,
  the dead `alpha_vantage_rate_limit` config chain, and `aiolimiter` —
  roughly 7,000 lines net deleted across the waves.

### Fixed

- `composite_score` no longer collapses to 0.5 on the detailed scoring path
  (fixed upstream in central with regression tests).
- Perplexity `search_recency` filter is now actually applied upstream.
- ETF holdings retrieval no longer calls nonexistent yfinance APIs.
- `enable_rate_limiting=False` now genuinely disables batch throttling.
- Crypto/AlphaVantage enrichment no longer renders literal "None" for
  present-but-null fields.

### Security

- Dependency floors bumped (mypy 2.2.0, ruff 0.15.20, litellm 1.92.0,
  grpcio, filelock and others) with lockfile refresh; harden-runner added to CI.

## [5.8.0] - 2026-06-30

### Added

- **Python 3.13 support** — migrated runtime, CI, and the Docker image
  (`python:3.12-slim` → `python:3.13-slim`; all GitHub Actions workflows;
  `pyproject.toml` `requires-python`/ruff/mypy targets). Python 3.12 is no
  longer supported.
- **A 7-day dependency cooldown** (`exclude-newer` in `[tool.uv]`) for
  transitive packages, so a newly published — and potentially compromised or
  unstable — release has time to be caught before it silently lands in the
  lockfile. Direct dependencies are exempted, since their floors are already
  bumped explicitly in reviewed commits.

### Fixed

- **crewai LLM calls crashing with `TypeError: Completions.parse() got an
  unexpected keyword argument 'drop_params'`** on natively-routed models,
  including `openrouter/*` (via `OpenAICompatibleCompletion`, which subclasses
  crewai's native OpenAI provider without overriding its param-prep logic).
  `drop_params=True` was forwarded straight into the OpenAI SDK call; removed
  it from `get_configured_llm()` — it was also redundant on the litellm-routed
  path, where crewai already forces `litellm.drop_params = True` globally.
- **`FinwizFlow.__init__` silently discarding state** assigned before
  `super().__init__()` — pydantic's `BaseModel.__init__` replaces
  `self.__dict__` wholesale during validation, so the parent constructor must
  run first.
- **`RateLimiter` tests patching the wrong target** — `AsyncLimiter` uses
  `__slots__`, so `acquire()` must be patched on the class, not a per-instance
  attribute.
- **mypy error in `data_validators.py`** (`numpy.signedinteger` vs `int`),
  surfaced now that mypy resolves cleanly under the 3.13 interpreter.

### Removed

- **Unused `safety` dev dependency.** Never wired into any Makefile target or
  CI workflow — CVE scanning is already covered by `pip-audit` (`make audit`)
  and `osv-scanner` (`make vuln`, CI-gated), SAST by `semgrep`
  (`make security`). Dropped 10 packages total (`nltk`, `safety`,
  `safety-schemas`, `authlib`, `dparse`, `joserfc`, `marshmallow`,
  `ruamel-yaml`, `tomlkit`, `truststore`) — this also closes the only
  still-open Dependabot advisory with no upstream fix (path traversal in
  `nltk.data.load()`).

### Security

- Routine dependency floor bumps via Dependabot (openai, hypothesis,
  mkdocs-material, pre-commit, types-pyyaml, pytest-xdist, scipy-stubs,
  actions/checkout, pandas-stubs, cyclonedx-bom, pytest-cov, beautifulsoup4)
  plus two bulk lockfile re-resolutions.

## [5.7.0] - 2026-06-11

The three-pass codebase simplification (Delete → Merge → Decompose), ~42,000
lines removed across PRs #64, #65, and #66 with permanent guardrails so
complexity cannot silently regrow. Every commit passed spec-compliance plus
adversarial quality review; each pass was validated by a production flow run.

### Removed

- **Pass 1 (Delete, −32.7k lines):** dead notification service, unused
  `examples/` demos, the orphaned `portfolio_review_enhanced`/
  `portfolio_review_html` report chain, ~45 orphaned `scripts/` (54 → 13,
  keep-list verified against Makefile/CI/pre-commit), 61 doc pages
  (meta-docs, historical fix logs, auto-generated placeholder stubs that were
  live in the published nav), 8 never-queried feature flags, and
  vulture-confirmed dead functions.
- **Pass 2 (Merge, −7.2k lines):** three stub tools whose `_run` only returned
  "use the other tool" messages, the orphaned analyzer cluster
  (`sentiment_analyzer`, `technical_analyzer` + algorithms/patterns/models),
  the enhanced sentiment tool and its private helpers (sentiment unified on
  `StandardizedSentimentAnalysisTool` — one methodology for crews and deep
  analysis), the self-validating feature-flag loop, and the write-only
  `GradeInfo.css_class` field.

### Added

- **Build guardrails (Pass 3):** cyclomatic-complexity (C901, max 10) and
  statement-count (PLR0915) gates with a shrink-only grandfather list;
  vulture dead-code gate; pylint duplicate-code gate (37-line clean baseline)
  — all real failing gates in `make check`/`make all` AND CI.
- **Network isolation for unit tests:** a pytest-socket guard blocks all
  remote access in `make test` (integration tests exempt); 16 silently
  leaking tests were caught and mocked at the seam, roughly halving suite
  wall-clock. Remote access must be mocked — the guard enforces it.
- Shared `json_ok`/`json_error` tool-response envelopes (`tools/run_helpers`),
  a `create_report_jinja_env` factory, and `BaseReportGenerator`
  `_apply_common_defaults()` deduplicating five report generators.

### Changed

- **Pass 3 decomposition (functional core / imperative shell):** ~870 lines of
  pure CSS/JS moved from Python strings to `reporting/assets/` files
  (byte-identical, APIs unchanged); `get_integrated_data_context` (236 lines,
  the repo's worst complexity offender) decomposed to a thin orchestrator over
  module-level loaders; `run_deep_analysis_concurrent`'s nested closures
  hoisted to typed module-level helpers.
- Deep-analysis sentiment now uses the standardized rule-based scorer (same
  −1..1 scale; values shift; collector output contract unchanged).
- Docs ground-truthed: the phantom `finwiz.utils.*` namespace retired
  (14 modules repointed with execution-verified imports), fictional API
  reference pages removed, feature-flag docs rewritten to the surviving API.

### Fixed

- **Layered-timeout collision that discarded computed analyses.** The inner
  crew timeout and outer per-holding timeout both read
  `FINWIZ_HOLDING_TIMEOUT`, so when an LLM call hung, the qualify retry could
  never complete before the holding was discarded — quantitative scores
  included. Crew attempts now have their own budget (`FINWIZ_CREW_TIMEOUT`,
  default 600 s) and the holding timeout auto-raises to crew + 300 s headroom.
- `backtesting_summary` was unconditionally `None` (a flag never set since
  inception) — report-crew context now receives real aggregate summaries.
- `AttributeError` crash path when a portfolio review is marked available but
  empty is now guarded.
- GitHub Actions context-injection vector in `quality.yml` (interpolations in
  `run:` blocks) fixed via quoted `env:` indirection.
- `make html-reports`/`html-convert` had been crashing on a stale import.

## [5.6.0] - 2026-06-09

### Added

- **EUR-weighted portfolio allocation from a CSV `Quantity` column.** Each holding
  can now carry a position `Quantity`; FinWiz values it in its native currency via
  the price API, converts to a EUR base via a live yfinance FX provider (per-run
  cache; `GBp`/`GBX` pence handled with a single ÷100), and stamps
  `quantity / native_currency / native_value / eur_value / weight` plus a
  portfolio-level `total_value_eur` onto the review. 100% deterministic Python
  (`scoring/portfolio_valuation.py`, injected `price_fn`/`fx_fn`); graceful
  degradation — missing quantity/price/FX leaves a `None` weight and never crashes,
  and the EUR total is computed over priced holdings only. New `make fix-currencies`
  rewrites the CSV `Currency` column from the authoritative price API (explicit,
  atomic, idempotent; never on a normal run).
- **Allocation surfaced in the portfolio review report** — a total-value hero,
  weight-sorted breakdown with weight bars, and `Poids` / `Valeur (€)` columns in
  the holdings table. Degrades to a guidance note when no quantities are set.

### Changed

- **Modern-fintech redesign of the portfolio review report.** Replaced the
  purple-gradient / blue-table look with a restrained white-card system on a cool
  off-white background, a single emerald accent, light small-caps table headers,
  tabular numerics, and refined badges. Light + dark mode; existing section classes
  restyled coherently.

## [5.5.1] - 2026-06-08

### Changed

- **Faster default test runs (~7min → ~3min, 2.4x).** Coverage instrumentation
  was moved out of pytest `addopts` (it added a ~7-11x tax to every run); the
  fast default `make test` runs without it (`-q`), while coverage + the 65% gate
  run via `make coverage` / `make coverage-check` (CI now uses the latter).
  Four discovery "import-error" unit tests that hit the live yfinance network
  (~135s) now mock the universe provider. Added a `make test-verbose` target.
  (pytest-xdist parallelization is a deferred follow-up — the suite has latent
  test-isolation issues, e.g. a `ConfigurationManager` singleton reading the
  real environment, that must be fixed first.)
- **Parallel test runs (pytest-xdist).** Added an autouse isolation fixture
  (`tests/conftest.py`) that clears config-driving env vars and resets cached
  config singletons (configuration manager, settings, resilience, feature flags,
  token monitor) before every test — making the suite reorder-safe. This also
  fixes a latent order-dependent leak where a config test could read — and print
  on failure — the developer's real `.env` API keys. The fixture's own overhead
  is negligible. `make test` and the CI coverage gate now run with
  `-n auto --dist=loadscope`.
- **Default unit run is now network-free and deterministic (~3 min → ~1m53s).**
  Profiling showed the default suite was dominated — and made wildly
  time-variable — by ~18 deep-analysis orchestrator "unit" tests that made real
  network calls (Alpha Vantage / yfinance via the macro-snapshot and
  batch-prefetch paths) wrapped in retry/backoff. These are now marked
  `@pytest.mark.integration`, so `make test` (`-m "not integration"`) excludes
  them and runs CPU-bound at ~1m53s on a 10-core machine (was ~3 min and
  network-variable); they still run in the integration job. Pure-logic tests in
  those files stay in the fast unit run. Fully mocking the orchestrator data
  layer to return them to the unit suite is a possible future refinement.

## [5.5.0] - 2026-06-07

### Changed

- **Leaner dependency tree.** Removed `fastapi` (unused REST module deleted),
  `langchain-community` (dead `sec_tool.py` deleted), `unstructured` (replaced
  with `beautifulsoup4`), `langchain-text-splitters` (replaced with a local
  chunker), and `sec-api` (optional, EDGAR-direct path covers it). Drops their
  large transitive trees (faiss, nltk, lxml, starlette-via-fastapi, …).

### Security

- **Official SBOM + CVE gate.** New `supply-chain` CI workflow emits a
  CycloneDX SBOM (attached to releases); a dedicated `osv-scanner` PR workflow
  gates merges on newly-introduced advisories. Accepted advisories are recorded
  in `osv-scanner.toml` (currently chromadb `GHSA-f4j7-r4q5-qw2c`, server-only,
  no fix). Local parity via `make sbom` / `make audit`.
- **Cleared transitive CVEs in `pyjwt`** — bumped to `>=2.13.0`
  (PYSEC-2026-175/177/178/179), surfaced by the new CVE gate.
- **Restored shadowed dev security tooling** — `bandit`, `safety`, and
  `pip-audit` were declared in a shadowed `dependency-groups.dev` block and
  never installed; consolidated so they are active again.

## [5.4.1] - 2026-06-07

### Security

- **Patched 15 Dependabot advisories** by raising dependency floors: litellm
  `>=1.83.10`, langchain-core `>=1.3.3`, aiohttp `>=3.14.0`, plus transitive
  security floors via `[tool.uv] constraint-dependencies` (urllib3 `>=2.7.0`,
  idna `>=3.15`, GitPython `>=3.1.50`, langchain-classic `>=1.0.7`, starlette
  `>=1.0.1`, uv `>=0.11.15`) and pymdown-extensions `>=10.21.3` (docs).
- **chromadb (GHSA-f4j7-r4q5-qw2c)** has no patched release and is a transitive
  dependency of crewai core; the vulnerability is in ChromaDB's server, which
  FinWiz never runs (in-process memory only). Tracked as not-affected.

### Changed

- **Leaner dependency tree (-18 packages).** Dropped the `crewai[google-genai]`
  extra (Gemini is used via OpenRouter/litellm, which doesn't need Google's
  native SDK) and the `crewai[tools]` extra. The only tools FinWiz used from
  `crewai-tools` were `FileReadTool`/`DirectoryReadTool`; these are now
  self-contained in `finwiz.tools.file_tools` (behaviour-faithful, incl. runtime
  path override). Removed pyarrow, lancedb, pymupdf, docker, python-docx, pytube,
  youtube-transcript-api, google-genai, and more. `chromadb` remains (crewai core).

## [5.4.0] - 2026-06-07

### Fixed

- **Discovery no longer emits weak (D/F) opportunities** -- the
  portfolio-aware discovery path skipped the actionable-grade filter, so the
  `a_plus_*`/`consolidated_discovery` outputs filled with F/D candidates (and
  zero A+). `NewcomerDiscoveryPipeline.discover()` now applies
  `_filter_actionable()` on both the portfolio-aware and legacy paths; wide
  recall still happens inside scoring, but the surfaced list excludes noise.
  See `src/finwiz/scoring/discovery/pipeline.py`.
- **AI qualitative analysis no longer silently falls back to Python-only** --
  `validate_ai_output_with_retry` was called with no `retry_callback`, so any
  crew output that failed structured parsing logged a misleading double-ERROR
  and dropped to Python-only (32 holdings last run). A real `retry_callback`
  now re-runs the deep-analysis crew once with explicit JSON format
  instructions (`{retry_guidance}`) before falling back. The no-callback path
  logs a single WARNING instead of two ERRORs.
- **Stale/renamed crypto tickers no longer spam yfinance errors** -- new
  `discovery/ticker_hygiene.py` centralizes renames (`MATIC`->`POL`,
  `FTM`->`S`) and non-tradable exclusions (`XTSLA`), applied at
  `to_yfinance_symbol` and the `get_returns`/`get_sectors` fetch boundaries.

### Changed

- **Honest LLM cost summary** -- the end-of-run summary reported "No LLM calls
  made" even when the deep-analysis crew ran (CrewAI clobbers
  `litellm.callbacks`, so our callback never fired). Cost/tokens are now
  recorded from CrewAI's authoritative `CrewOutput.token_usage` at the
  `execute_crew_with_timeout` chokepoint via `record_usage()`. An unmeasured
  run says so plainly; dollar amounts are labelled estimates; unpriced models
  show "cost n/a" instead of a false $0.
- **Reduced log noise** -- downgraded ~500 by-design fallback WARNINGs to
  DEBUG (fact-pack truncation, defaulted-field metrics, news-source waterfall,
  SEC CIK misses for non-US tickers).

## [5.3.0] - 2026-05-03

### Added

- **Tactical price targets and sell-level floors per holding (ADR-011)** --
  Per-holding `PriceTargets` (buy/sell primary + secondary) computed from
  price history, support/resistance, ATR floors, and asset-class-specific
  caps (25% stocks/ETFs, 40% crypto). Surfaced in HTML report rationale.
  See `src/finwiz/quantitative/tactical_pricing.py` and PR #38.

### Fixed

- **Deep analysis cascade for 2026-04-28 across 3 workstreams** -- repaired
  cascade failure that propagated through the analysis pipeline. See PR #28.
- **Test suite robust to weekend run dates** -- `pd.bdate_range(end=Sunday,
  periods=N)` returns `N-1` business days because pandas drops a period
  when end is non-business. Affected `test_quantify_price_targets.py` (3
  tests) and `test_tactical_pricing.py` (15 tests). Snap end to the most
  recent business day via `BDay(0).rollback` before calling `bdate_range`.

### Changed

- **Dependabot enabled** for weekly dependency updates (PR #29).
- **Dependency bumps:** fastapi, beautifulsoup4, pytest-mock, pandas-stubs,
  scipy-stubs, plus CI actions (checkout, setup-uv, upload-pages-artifact).
- **Task Master AI integration removed** -- never used in practice; deleted
  `AGENTS.md`, `docs/setup/CLAUDE_007_TASKMASTER_SETUP.md`, and local-only
  `.vscode/mcp.json` / `amp.mcpServers` settings.
- **AGENTS.md/CLAUDE.md deduplication** -- removed duplicated grepai and
  code-review-graph sections (CLAUDE.md is single source of truth).

## [5.2.0] - 2026-04-28

### Added

- **Grounded qualitative analysis (v5.2 trust spine extension)** -- New
  `fact_pack` pipeline stage runs between quantify and qualify, fetches
  verified corporate facts from Perplexity (one structured call per holding),
  caches them for 7 days, and injects them into every qualitative prompt as
  the authoritative source. The qualify task template treats the fact pack as
  ground truth -- anti-hallucination is now structural, not advisory. The
  DELL/VMware class is fixed at the root: a fact pack carrying "Divested
  VMware November 2021" overrides the AI's stale training data.
- **`FactPack` schema** at `src/finwiz/schemas/hybrid_analysis/fact_pack.py`
  with Python-derived `freshness` field (AI cannot lie about staleness --
  cross-checked by `model_validator`). Carries `corporate_structure`,
  `recent_events` (last 12 months), `leadership`, `confidence` (AI-rated),
  and `source_citations` (Perplexity URLs).
- **Provenance footer in HTML reports** -- Pill (green/neutral/amber by
  freshness) + numbered citation links rendered next to the rationale cell.
  Stale (>7 days) entries show amber pill with confidence rating, prompting
  the operator to refresh.
- **`scripts/invalidate_fact_pack.py` CLI** for forced cache refresh on
  real-world events (M&A, leadership change). Usage:
  `uv run python -m scripts.invalidate_fact_pack DELL` or `--all`.
- **Hardened DELL/VMware regression test** with 10-phrase forbidden library --
  catches wishy-washy hallucination ("Dell's VMware unit", "owns VMware",
  "VMware integration", etc.), not just literal matches.

### Changed

- **Version naming aligned with milestone codename.** This release jumps from
  `0.4.0` to `5.2.0` so the SemVer tag matches the internal milestone
  ("v5.2 -- Grounded Qualitative"). The `0.X` series ends with `0.4.0`. From
  this release forward, every artifact (pyproject, git tags, GitHub releases,
  ADRs, specs, plans) references `5.2.0`. The major jump is the deliberate
  signal that the trust-spine + fact-pack lineage is the new generation.
- **Per-task Perplexity verification budget reduced** in the qualitative
  crew prompt (`tasks.yaml`) from "max 2" to "max 1" -- the fact pack
  pre-loads the common verifications, so the per-task budget can shrink.
- **`_build_crew_inputs` accepts an optional `fact_pack` parameter** and
  injects 5 new keys into the prompt template (`corporate_structure`,
  `recent_events`, `leadership`, `fact_pack_freshness`,
  `fact_pack_confidence`).
- **Trust-spine invariant preserved.** The DEGRADED outcome whitelist stays
  `{"qualify"}` only -- the `fact_pack` stage emits OK or FAILED. Staleness
  is a payload field on `FactPack`, not a stage outcome state. Same
  user-visible signal (amber pill) without weakening the v5.1 structural
  invariant.

### Fixed

- **DELL/VMware hallucination class fixed at root.** v0.3.0 patched the
  symptom (date-anchored prompts + bounded Perplexity access). v5.2 fixes
  the cause: every qualitative call now grounds against a Perplexity-verified
  fact pack. Pinned by `tests/regression/test_dell_vmware.py` with a
  10-phrase forbidden library.

### Cost / latency note

First-run cost: 60 holdings x ~5 s Perplexity p95 = ~300 s wall-time worst case.
With existing parallelism (`FINWIZ_DEEP_ANALYSIS_PARALLEL_LIMIT=2`) net add is
~2.5 minutes to the first kickoff. Subsequent kickoffs hit the 7-day cache and
pay 0 s.

## [0.4.0] - 2026-04-28

### Added

- **Trust spine (v5.1, PR #24)** -- Typed `StageResult[T]` contract (OK / DEGRADED / FAILED discriminated union) on every pipeline stage. Silent failure is now structurally impossible: the type system forces every caller to handle all three variants. A holding with any FAILED stage is marked `AnalysePending` — no partial result is ever presented as complete.
- **`@stage` decorator** -- Wraps each stage function with per-unit timeout, configurable retry policy, and automatic `RunLedger` recording. Sync and async variants supported. Replaces the removed aggregate `asyncio.wait_for` pattern (which was the root cause of the v0.3.1 bug).
- **`RunLedger` JSONL artifact** -- Written to `output/run_ledger/<run_id>.jsonl` with one entry per stage execution (ticker, stage name, status, duration_ms, error). Survives the process for replayable post-mortem analysis without re-running the flow.
- **`TrustBanner`** -- Four-state (green / amber / red / blocked) banner derived deterministically from `RunLedger` coverage at report time. `blocked` state carries the explicit warning "NE PAS prendre de décisions sur ce rapport" when coverage falls below threshold. No AI involved in banner computation.
- **AST static check** (`scripts/check_stage_contract.py`, `make check-stage-contract`) -- Parses source AST to forbid aggregate `asyncio.wait_for` patterns and flag stages returning bare values instead of `StageResult`. Wired into `make check`.
- **v0.3.0 trust-crisis regression test** -- `tests/regression/test_v030_silent_success.py` pins the silent-success class (0 analyses, fake "completed successfully" banner). Guards against reintroduction.
- **Hypothesis property tests** -- Invariant tests covering `StageResult` variance, `TrustBanner` derivation monotonicity, and `RunLedger` append-only semantics.

### Changed

- **`deep_analysis_pipeline.py` refactored from 1,209 → 99 lines** -- Stage logic extracted into 10 focused modules under `src/finwiz/analysis/stages/` (`collect`, `quantify`, `qualify`, `synthesize`, `emit`, plus private helpers `_ledger`, `_resilience`, `_qualify_fallbacks`, `_synthesize_helpers`, `_synthesize_options`). The pipeline file is now a thin orchestrator.
- **`qualify` emits DEGRADED on Python fallback** -- Previously, when the AI crew returned `None`, qualify silently substituted Python-derived values and emitted status `OK`. Now it emits `StageResult.DEGRADED`. This fixes the "Python fallback masquerading as AI insight" class from v0.3.0. Confidence propagates as `'low'` through synthesize → emit → HTML amber badge.
- **Orchestrator uses `RunLedger` view** -- The `DeepAnalysisOrchestrator` derives coverage counts and failure tracking from `RunLedger` data, replacing the manual `_failed_holdings` list. Single source of truth for what ran.
- **Phase 4 Investment Discovery runs unconditionally (PR #23)** -- The `INVESTMENT_DISCOVERY_ENABLED` kill switch has been removed. Discovery always runs because it is a core deliverable; opt-out via kill switch created the same class of silent-omission trust bug as the v0.3.0 `DEEP_PORTFOLIO_ANALYSIS` switch.

### Fixed

- **Any-stage FAILED short-circuits to AnalysePending** -- Previously a holding could pass through a FAILED stage and continue to emit a synthetic result. Now the first FAILED stage aborts the holding's pipeline and marks it `AnalysePending` in the report (amber, not a fabricated grade).
- **Per-unit timeouts only; aggregate `wait_for` banned** -- The `@stage` decorator applies timeouts at individual stage scope. The AST static check enforces this at CI time. Total runtime now scales naturally with N holdings (same fix as v0.3.1, now enforced structurally rather than just by removal).
- **`confidence='low'` propagates end-to-end** -- When qualify emits DEGRADED, `confidence='low'` flows through synthesize, through emit, and into the HTML renderer which shows the amber "Insight IA indisponible" badge. No code path was passing `None`-qualified data through as full-confidence output.

### Removed

- **`INVESTMENT_DISCOVERY_ENABLED` env var kill switch** -- Setting this variable is now a no-op. Discovery runs as part of every standard flow execution. `app_initializer.py` no longer reads or forwards this variable.

## [0.3.1] - 2026-04-27

### Fixed

- **Phase 3 lost successfully-completed work** -- The 1800s aggregate timeout
  (`GLOBAL_PHASE_TIMEOUT` / `FINWIZ_PHASE_TIMEOUT` env var) was wrapping the
  per-holding `asyncio.gather` and discarding every already-completed future
  when it fired. A run on 2026-04-27 had XRP-USD finish cleanly at 09:00:12
  (grade=D, rec=SELL, 92.3s) but its result was thrown away when the
  aggregate timeout fired 4½ minutes later. With 60+ holdings, an outer cap
  is the wrong abstraction — it punishes work that already succeeded when
  one slow ticker pushes total runtime over. **The aggregate timeout has
  been removed entirely.** `PER_HOLDING_TIMEOUT` (600s default,
  `FINWIZ_HOLDING_TIMEOUT`) remains the only safety cap; total runtime now
  scales naturally with N. The gather now uses `return_exceptions=True` so
  one holding's exception doesn't poison siblings.
- **Phase 3 runner crashes were silent** -- Codex P1 catch on PR #22:
  `run_deep_analysis_concurrent` exceptions (executor init, asyncio loop,
  config errors) used to be caught, logged, and the orchestrator returned
  `{"error": ...}` — letting the flow continue and report success. Now the
  orchestrator updates state then re-raises so the failure can never go
  silent. The `flows/orchestrator.py` try/except wrapper still ensures
  cost/cache summaries fire on the failure path.
- **Single source of truth for Phase 3 fail-loud** -- Removed the duplicate
  fail-loud check in `flows/orchestrator.py:run_sequential_workflow` (the
  v0.3.0 location wasn't on every flow code path). The orchestrator now
  raises `RuntimeError` directly on 0 results — independent of which flow
  path called it.

## [0.3.0] - 2026-04-27

### Fixed

- **Deep analysis silent-failure → trust crisis (DELL B+ → D panic)** -- A portfolio kickoff produced 0 deep analyses for 62 of 63 holdings yet reported `"✅ FinWiz analysis workflow completed successfully"`. The hidden `DEEP_PORTFOLIO_ANALYSIS` env-var kill switch defaulted to `"false"` and silently no-op'd Phase 3, then the placeholder `grade="D"` / `composite_score=0.6` from `decisions.py` rendered as a real verdict in the report. Three layers of fixes: (1) DELETED the kill switch — deep analysis ALWAYS runs because financial trust requires it; (2) honest success accounting via `_failed_holdings` tracker + `deep_analysis_coverage` tuple on `FinwizState`, plus flow-level `RuntimeError` when 0 analyses produced for N>0 holdings; (3) reporting layer truthfully renders unanalyzed holdings as `⏳ Analyse en attente` (new `Grade="N/A"` literal) with `composite_score` reset to 0.0 so downstream consumers don't see fabricated 0.6.
- **Coverage banner on the executive summary** -- New green/amber/red banner showing actual `analyzed/total` ratio. Red includes the explicit warning **"NE PAS prendre de décisions sur ce rapport"** when 0 holdings analyzed. Average portfolio score now ignores N/A holdings so a 1/63 kickoff can't fabricate a portfolio-wide score from placeholder noise.
- **Date-anchored AI prompts** -- Every AI prompt (CrewAI deep_qualitative_analysis_task + the four Perplexity strategic prompts in `analysis/strategic_research.py`) now opens with the current date in long French form (e.g. `26 avril 2026`). The model is explicitly told that its training data may be outdated for corporate structure (acquisitions, divestitures, partnerships) and that "récent" means the 12 months preceding `{current_date}`. Resolves the DELL-still-owns-VMware class of hallucination (Dell sold VMware in November 2021).
- **OpenRouter mid-stream drops** -- Set `litellm.num_retries=3` at module import time in `config/llm/llm_config.py`. CrewAI's `LLM(...)` constructor doesn't expose num_retries (verified), so the litellm module-level global is the only working hook. Catches `httpcore.RemoteProtocolError` / "incomplete chunked read" / `APIError` 502/503/504 with built-in exponential backoff. Tunable via `LLM_NUM_RETRIES` env var (default: 3, with defensive parse for empty/garbage values).

### Changed

- **Qualitative crew now has bounded Perplexity access** -- `asset_analyst` in `crews/deep_analysis/` was running in zero-tool mode, which left it relying on training memory for corporate facts (cause of the DELL/VMware hallucination). Added `PerplexitySearchTool` with strict in-prompt caps: max 2 calls per holding, reserved for material facts (current corporate structure, recent leadership changes, major events in last 12 months), forbidden for already-provided Python data (scores/metrics). Web search wins over model memory whenever they conflict. Token-overflow risk mitigated by the call cap.

### Removed

- **Dependency cleanup** -- Dropped 16 unused runtime packages and 2 redundant wrappers from `pyproject.toml`. Removed: `firecrawl-py`, `serpapi`, `tavily-python` (no tool actually imported them), `supabase`, `asyncpg` (no persistence layer wired), `qdrant-client`, `faiss-cpu`, `sec-edgar-downloader`, `eod`, `perplexityai`, `quandl`, `statsmodels`, `trio`, `rumdl`. Redundant wrappers: `dotenv` (duplicate of `python-dotenv`), `bs4` (duplicate of `beautifulsoup4`). `uv.lock` shrank by ~250 lines / 35 packages including transitive trees.
- **`FIRECRAWL_API_KEY` env var** -- The `Firecrawl` `APIKeyConfig` entry, validation rule, and sanitizer entry were removed alongside the `firecrawl-py` package. Setting the env var is now a no-op. Documentation updated in `USER_GUIDE.md`, `setup_environment.md`, `tutorials/USER_GUIDE.md`, and `tutorials/getting_started.md`.

### Changed

- **Dev/docs dependency reorganization** -- Moved `ruff`, `pytest-asyncio`, and the five `mkdocs*` packages out of `[project.dependencies]` into the `[dependency-groups]` `dev` and `docs` blocks where they belong. Runtime `uv sync` no longer installs lint/test/docs tooling.

### Added

- **Options-implied scenario probabilities** -- Scenario probability bars (bull/base/bear) are now derived from market-implied data via Black-Scholes N(d₂) applied to yfinance options chains. Picks the expiry closest to 90 days, interpolates IV at +20% (bull) and -15% (bear) strikes. Fallback chain: options-implied → AI-provided → Python composite-score formula. Crypto and niche ETFs without liquid options use the Python fallback. Configurable via `RISK_FREE_RATE` env var (default: 0.045).
- **Recommendation conflict notice** -- When Python quantitative score and AI qualitative recommendation disagree, an amber warning box is shown in the HTML report (Python still wins; conflict is surfaced for transparency).
- **Python-computed scenario probabilities fallback** -- When AI omits `scenario_probabilities`, Python derives them from `composite_score` and `risk_score` (deterministic, $0), preventing "non disponible" display in scenario cards.

### Changed

- **Token optimization (ADR-007)** -- Pruned ~10K tokens of YAML boilerplate across all 7 crews: removed 33 redundant JSON OUTPUT blocks, 11 ANTI-HALLUCINATION blocks, 8 "Read schema" instructions, and compressed 25+ agent backstories to ~15 words each
- **LLM max_tokens caps** -- Added response length limits per model type (standard: 2048, mini: 1024, manager: 1024, planning: 2048, baseline: 4096) to prevent unbounded output; configurable via `LLM_MAX_TOKENS` env var
- **Deep analysis max_tokens** -- Increased to 4096 to accommodate structured JSON output requiring 1500-2000 words; further raised to 6144 to reduce token-pressure truncation of `investment_synthesis` prose
- **QualitativeInsights field ordering** -- `investment_synthesis` moved to first position in schema so LLM fills the most user-visible section before token budget runs out (zero-cost change, transparent to all callers)

### Fixed

- **risk_factors schema** -- Added field_validator to `SecAnalysisInsights` to coerce LLM dict responses (`{'risk': '...', 'severity': '...'}`) to plain strings, preventing Pydantic validation failures
- **LLM cache key** -- Include `max_tokens` in cache key to prevent callers with different token limits from receiving the wrong cached instance

### Added

- **Pre-call token guard** -- LiteLLM callback now logs error when estimated prompt tokens exceed configurable `MAX_PROMPT_TOKENS` threshold (default: 100K)
- **CrewAI usage_metrics logging** -- Token consumption per crew logged after each execution for cost visibility
- **ADR-007** -- Token Consumption Optimization architecture decision record

## [0.2.0] - 2026-03-29

### Added

- **MacroScorer**: New component scorer wiring macro-economic data into the composite scoring pipeline (40% fundamental, 30% technical, 30% risk)
- **Sentiment & Macro report sections**: Wire sentiment summary, macro dashboard, and economic calendar sections into the per-holding enriched analysis report
- **EconomicCalendar schemas**: New `EconomicCalendar` Pydantic models and adapter with feature-flag guard
- **Report enrichment pipeline**: Persist `sentiment_summary` in enriched JSON; add macro overlay and calendar section generators
- **Per-holding sentiment rendering**: Dedicated sentiment section in deep analysis HTML report
- Comprehensive CLAUDE.md documentation for all 12 major subfolders (crews, flows, tools, schemas, quantitative, orchestrators, reporting, utils, data, integration, scoring, validation)

### Changed

- **Major Refactoring** — Split 13 large files (600–1682 lines) into 40+ focused modules
  - `deep_analysis_orchestrator.py` (1,682 → 4 modules): data_collector, executor, processor
  - `deep_analysis_scorer.py` (1,178 → 3 modules): score_result_builder, crew_export_generator
  - `hybrid_analysis_flow.py` (1,042 → 3 modules): data_collector, synthesizer
  - `quantitative_analysis_tool.py` (649 → 5 modules): technical, backtesting, performance analyzers
  - `report_consolidator.py` (646 → 3 modules): export_loaders, html_collector
  - `schemas/quantitative/models.py` (643 → 7 domain files): backtesting, data, enums, portfolio, risk, screening, technical
  - `supabase/client.py` (641 → 6 modules): config, health, metrics, operations, pool
  - `registry_manager.py` (624 → 5 modules): models, data_retrieval, execution, storage
  - `flow_state.py` (620 → 4 modules): models, analysis, utils
- Applied functional programming patterns (list comprehensions, itertools, operator module)
- Centralized exception hierarchy in `exceptions/` module
- Circuit breaker now configurable via `ResilienceConfig`
- Holding analysis timeout increased to 600 s to accommodate deep analysis workloads
- Upgraded all dependencies (`uv.lock`)

### Fixed

- **CI: memory constraint test** — Mock `peak_memory` so `test_should_validate_memory_constraints_when_within_limit` is deterministic and no longer fails on loaded CI runners (#11)
- **CI: notification quiet-hours test** — Mock quiet-hours logic to prevent timezone-dependent failures in CI (#10)
- Force-exit after flow completion to prevent thread-pool hang on process exit
- ROE validation relaxed; `beta=1.0` accepted; NaN guarded in backtesting calculations
- `data_extractor.py`: Fallback to `final_grade`/`final_score` when AI crews emit those keys instead of `grade`/`composite_score`
- `python_report_generator.py`: Handle `None` grade to prevent `'NoneType' has no attribute 'lower'` error
- Dead code: Prefixed 8 unused parameters with underscore (vulture 100% confidence)
- Security: `MD5` hash flagged with `usedforsecurity=False` (bandit high-severity)
- Lint: 10 ruff issues resolved (unused imports, unsorted imports)

## [0.1.0] - 2025-12-07

### Added

- Initial FinWiz platform release
- CrewAI-based multi-agent financial analysis system
- Stock, ETF, and cryptocurrency analysis crews
- Portfolio review and rebalancing functionality
- A+ investment discovery system
- Deep per-holding analysis with Python scoring
- Hybrid Python/AI analysis architecture
- Quantitative analysis with Backtrader, TA-Lib, QuantLib, PyPortfolioOpt
- Batch processing for high-performance portfolio analysis (10-20x speedup)
- HTML report generation with Jinja2 templates
- RAG (Retrieval-Augmented Generation) integration
- Multi-source data fetching with fallback strategies

### Core Crews

- `StockCrew` - Stock fundamental and technical analysis
- `EtfCrew` - ETF factsheet and holdings analysis
- `CryptoCrew` - Cryptocurrency on-chain metrics
- `DeepAnalysisCrew` - Per-holding comprehensive analysis
- `InvestmentDiscoveryCrew` - A+ opportunity discovery
- `PortfolioRebalancingCrew` - Portfolio optimization
- `ReportCrew` - Final consolidated report generation

### AI Minimalism Implementation

- Python-based scoring engine (100% cost reduction vs AI)
- Jinja2 template-based report generation
- Deterministic calculations for reproducibility
- AI reserved for analysis requiring reasoning

### Testing

- pytest with pytest-mock (no unittest.mock)
- Faker for test data generation
- 65% minimum coverage requirement
- Type checking with mypy

---

## Changelog Maintenance

Claude should maintain this changelog by:

1. **Adding entries** when implementing new features or fixing bugs
2. **Categorizing changes** under appropriate headers:
   - `Added` - New features
   - `Changed` - Changes in existing functionality
   - `Deprecated` - Soon-to-be removed features
   - `Removed` - Removed features
   - `Fixed` - Bug fixes
   - `Security` - Security-related changes
3. **Including context** - Brief description of what changed and why
4. **Referencing issues/PRs** when applicable

### Example Entry

```markdown
### Fixed
- Resolved JSON serialization error in crew exports by adding `default=str` to all `json.dumps()` calls
- Fixed mock path errors in tests by patching at import location rather than definition
```
