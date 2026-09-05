# FinWiz Reevaluation — Roadmap

**Date:** 2026-09-05
**Status:** Findings recorded; workstream order to be decided
**Basis:** one live `crewai flow kickoff` (09:04–09:28, 64 holdings, `logs/finwiz.log`), the code reached by that run, and what was fixed or deleted the same day

## Purpose

A step back from feature work to ask what the system actually does for its reader, what it silently fails at, and what it wastes. Every finding below is backed by a number from the run or a line in the code. Where the first reading turned out to be wrong, the correction is kept in place rather than erased — the wrong reading is itself evidence about what the system makes hard to see.

This document indexes workstreams. It does not design them. Each row of the table at the end gets its own spec → plan → implementation cycle.

## What the run delivered

- 64/64 holdings analysed, 0 failures, 63/64 priced (98 %), average composite score 0.746.
- 2 080 LLM calls, 15.9 M tokens, 23 minutes wall time.
- Report: 64 grades with buy/hold/sell, allocation hero (49 734 € over 63 positions, 1 unpriced and declared), strategic posture page, stress tests.
- Verified correct on live data: the 5.14.1 allocation-count fix, yfinance 1.7.0 (no new failures versus the August runs), plotly 7.0 (both visualisation paths).

## Findings

### F1. Perplexity fails on 28 % of fact packs, and the errors say nothing

18 of 64 fact packs failed their live fetch and were served from cache — **17 dated 2026-08-17, one 2026-08-23**. The cause is in the retry layer: 128 lines reading `Perplexity transport error for _FactPackRaw:` followed by **nothing** — an empty message, 115 empty responses, 5 HTTP 429, 18 holdings exhausting all 4 attempts.

*Correction to the first reading.* This was initially filed as a veracity defect — stale facts presented as current. It is not: `reporting/sections/factpack.py` already renders a `fresh / recent / stale` pill with the fetch date in French. The 18 stale packs are declared. The defect is **reliability** (a 28 % failure rate) and **observability** (an exception swallowed to an empty string — the same anti-pattern as the backtest traceback fixed in PR #158).

Evidence: `grep -c 'using stale cache' logs/finwiz.log` → 18; `analysis/stages/fact_pack.py:68-69` (fallback); `infrastructure/resilience/perplexity_retry.py` (133 warnings).

### F2. Three phases run and deliver nothing

| Phase | What happened | What the reader got |
|---|---|---|
| 4 — Discovery | Scanned 70 stock, 58 ETF, 35 crypto tickers; initialised 3 Perplexity Sonar pipelines; `Breakout detection returned 0 candidates from 70 scanned`; `No discovery result found in discovery data` | nothing |
| 4.5 / 5 — Alternatives | 17 underperformers; `No A-band stocks found in discovery output`; both fallbacks are stubs — `Sector matching not yet implemented`, `ETF cost comparison not yet implemented` | 0 alternatives, 68 warnings |
| 6 — Rebalancing | `PORTFOLIO_ENABLE_REBALANCING` absent from `.env`, default `false`; nothing in the codebase computes target weights | not run |

The crypto universe is 35 tickers against a floor of 50, so even a working discovery would be under-covered for that class.

Evidence: `logs/finwiz.log` phase markers; `tools/alternative_finder_tool.py:169`; `orchestrators/validation_orchestrator.py:135-160`.

### F3. The system cannot see what it spends

`openrouter/google/gemini-3.7-flash` is not in the pricing table, so the cost summary reads `TOTAL: ~$0.0000 estimated across 2080 calls` — for 15.9 M tokens. A system whose central claim is "deterministic Python at $0, AI at the margin" cannot measure the margin.

Per-holding call counts by asset class:

| Class | Holdings | LLM calls | Calls / holding | Tokens / holding |
|---|---|---|---|---|
| Stock | 35 | 633 | 18 | 138 K |
| ETF | 25 | 1 198 | 48 | 366 K |
| Crypto | 4 | 249 | **62** | **474 K** |

*Open unknown.* The `deep_analysis` crew has **1 agent, 1 task, `max_iter=2`, `reasoning=False`** (`crews/deep_analysis/deep_analysis.py:294-353`). That configuration cannot account for 62 calls per holding — nor for 18. Either the counter aggregates something else (retries, tool-internal LLM calls, several crews per holding) or there is a loop. This must be measured, not guessed. It is a spike, and it gates any decision about F2's phases, whose real cost is currently unknown.

*Resolved by the workstream B spike, same day.* The counter aggregates. CrewAI keeps token usage on the **LLM object** (`BaseLLM._token_usage`, `+=` per request, never reset by `kickoff`) and `Crew.calculate_usage_metrics` reads it as the crew's own usage. finwiz's `config/llm/llm_config.py` cached LLM instances by `(model, type, max_tokens, json, reasoning)`, so all 64 holdings shared one object and each kickoff reported the running total of every holding before it. The summary then summed running totals. Signature: 35 stocks at one request each, cumulative, is 1+2+…+35 = 630; measured 633.

Consequences: the real deep-analysis spend is ≈ 65–70 requests and ≈ 0.5 M tokens — a **32× overstatement**. The per-class asymmetry above is an artifact of record ordering; **crypto is not more expensive than stocks. Retracted.** The cache saved 13.5 ms per crew (1.1 s per 23-minute run) and had already forced a second bug-class into its own key (`LLM_REASONING_EFFORT` staleness). Deleted rather than bypassed. The pricing half stands: `openrouter/google/gemini-3.7-flash` is unpriced in litellm while `gemini/gemini-3.7-flash` is ($0.75 / $3.75 per M); a fallback lookup now prices through the vendor-native id and says so.

### F4. A requirement that 100 % of outputs violate

128 warnings `Quality validation warnings for <ticker>: Word count N < M (Requirement 9.2); Executive summary N words < M` — exactly 64 × 2. Every holding fails, twice. A requirement violated by every output is either wrong or ignored; either way it hides real signal under constant noise.

Evidence: `reporting/enriched_analysis_report_generator.py` (128 WARNING lines).

### F5. Safety comes from the test suite, not from the product

- **5 134 tests, all network-mocked** under the pytest-socket guard. Strong on logic, blind on integrations: yfinance 1.7.0 shipped in 5.14.1 with zero real API calls exercised. There is no scheduled integration tier.
- **Dead code survives because its tests reference it.** Vulture treats a test import as a use. 1 578 lines were deleted today (PR #159: `optimization.py` and two orphans, imported by nothing in `src/`), and `performance_benchmarks.BenchmarkAnalyzer` (~385 lines) is equally unreachable. A CI check "is this module imported from `src/`?" would have caught both.
- **`make check` green does not mean the product works.** Today's run was green with 28 % stale fact packs, three inert phases and an unknown cost. Nothing after `kickoff` verifies the run.
- **Markdownlint runs only locally.** `make check` was red for weeks on 10 MD032 violations; no workflow ever saw them (fixed in PR #156, the CI gap remains).
- Backtest off-by-one (`index 252 is out of bounds for axis 0 with size 252`, CVLT/GOOGL/HPE) — root cause unknown, does not reproduce outside a run, now instrumented with a traceback (PR #158).
- Six crypto tickers (`POL GRT COMP UNI S IMX`) return no yfinance data on every run since August.

### F6. What the reader does not receive

Grades, decisions, current allocation, posture, stress tests — yes. Not received: **what to buy instead** (alternatives inert), **what to aim for** (no target allocation — spec and plan written today), **what orders to place** (rebalancing off), **what it cost** (unknown).

## Done today, before this document

| PR | Change |
|---|---|
| #155 | CI hardening, `uv.lock` refresh (66 packages), ruff 0.16.5 Markdown reformat |
| #156 | MD032 fixes — `make check` green again |
| #157 | Release 5.14.1 |
| #158 | `BRK.B → BRK-B` at the ticker-hygiene seam; backtest failures keep their traceback |
| #159 | Delete the dead scipy optimiser stack (1 578 lines) |
| — | Spec + plan for optimal allocation, on branch `docs/optimal-allocation-spec` |

## Workstreams

| # | Workstream | Nature | Size | Depends on | Addresses |
|---|---|---|---|---|---|
| A | **Run gate** — after `kickoff`, verify coverage, freshness ratio, active phases, known cost; fail otherwise | new tooling | medium | better with B | F5 |
| B | **Cost** — spike: where do 62 calls per crypto come from with `max_iter=2`? then add `gemini-3.7-flash` to the pricing table | spike → bounded | small | — | F3 |
| C | **Perplexity reliability** — log the full exception; characterise the 128 transport errors; review backoff | infrastructure | small | — | F1 |
| D | **Dead phases** — decide per phase: finish or remove discovery, alternatives, rebalancing | product + flow | **large** | B (real cost of phases) | F2, F6 |
| E | **CI** — nightly `integration` smoke tier; "imported from `src/`" dead-code check; markdownlint in a workflow | CI | medium | — | F5 |
| F | **Requirement 9.2** — recalibrate or remove | bounded | very small | — | F4 |
| G | **Optimal allocation** | spec + plan ready | — | — | F6 |

### Dependencies

- **B before D.** Deciding to keep or kill a phase without knowing what it costs is deciding blind. B is an hour.
- **B improves A.** A run gate that checks "cost is known" needs the pricing table first.
- C, E, F, G are independent of everything else and of each other.

### Suggested order

B → C, F → A → E → D → G at any point.

Small and independent first, the gate before the big decision, the big decision last and informed. This is a suggestion; the order is the open decision this document exists to support.

## Open unknowns

1. What the 62 calls per crypto are (B, spike).
2. What the 128 empty-message Perplexity errors actually were (C — unrecoverable for this run; the fix is to log them next time).
3. Root cause of the backtest off-by-one (instrumented; wait for the next occurrence and read the traceback).

## How to use this document

Pick a row. Brainstorm it into `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, plan it into `docs/superpowers/plans/`, implement it, and strike the row here with the PR number. When every row is struck or explicitly dropped, this roadmap is done.
