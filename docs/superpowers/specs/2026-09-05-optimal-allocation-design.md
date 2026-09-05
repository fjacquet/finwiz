# Optimal Allocation — Design

**Date:** 2026-09-05
**Status:** Approved design, ready for implementation planning
**Scope:** `src/finwiz/schemas/portfolio_optimization.py` (new), `src/finwiz/quantitative/allocation_optimizer.py` (new), `src/finwiz/orchestrators/allocation_orchestrator.py` (new), `src/finwiz/reporting/sections/optimal_allocation.py` (new), `src/finwiz/flows/orchestrator.py`, `src/finwiz/flow_state_models.py`, `src/finwiz/reporting/python_report_generator.py`

## Problem

FinWiz grades 64 holdings and recommends buy, hold or sell on each one. It never says what the portfolio as a whole should look like. There is no target allocation anywhere in the system.

This is not an oversight in the reporting layer — the capability is absent from the domain. `target_allocations` reaches the rebalancing path as `base_inputs.get("target_allocations", {})`, and nothing in the codebase ever populates that key. The live `optimization_algorithms.py` is a trade *sequencer*: given target weights it produces orders minimising count, cost or risk. It consumes weights it is never given.

Two mean-variance implementations existed, both unreachable from production:

- `optimization.py` — hand-rolled over scipy. Deleted 2026-09-05 (PR #159, 1147 source lines with its two orphaned helpers).
- `performance_benchmarks.py` → `BenchmarkAnalyzer.optimize_portfolio` — built on **pypfopt**. Retained, and the basis of this work.

The pypfopt path is the one worth keeping: a maintained library rather than a bespoke solver, per the project's own financial-libraries guidance. It has never been called from production, and no report has ever displayed its output.

## Decisions

Four decisions were settled before design and constrain everything below.

1. **Delivered in two stages.** Stage 1 (this spec) is advisory only: the report shows current allocation against an optimal one. Stage 2 turns on Phase 6 and converts the target weights into orders through the existing sequencer. Stage 1 must be independently useful and independently verifiable on a live run.

2. **Constrained weights, not raw mean-variance.** Long-only, capped per position and per asset class. Unconstrained max-Sharpe on 64 holdings collapses onto four to six names and moves violently between runs; it is a mathematically honest signal and useless advice.

3. **Minimum variance — no expected returns at all.** Estimation error in expected returns dominates every other error in mean-variance optimisation. The design removes that term rather than modelling it. `pypfopt` accepts `expected_returns=None` for `min_volatility`, so the refusal to forecast is expressed through the API rather than worked around.

4. **Approach A — a flow phase, not a rendering-time computation.** The result lands in flow state as a typed object. Rendering-time computation would put a convex solve and 64 price series inside a report function, break the project's layering, and leave Stage 2 nothing to consume.

## Design

### 1. Placement

**Phase 3.7**, immediately after the gap profile (3.6) and before discovery (4). It requires deep analysis to have run — that is what warms the price cache — and nothing else.

Phase 3.5 (stress testing) is the exact structural precedent: compute from state, store for the report, fail soft. Phase 3.7 follows it line for line, including the `if self.state.deep_analysis_success` guard and the local import.

### 2. Components

Six pieces, each with one reason to exist.

| Component | Role | Depends on |
|---|---|---|
| `schemas/portfolio_optimization.py` — `OptimalAllocation`, `HoldingTarget`, `ExcludedHolding` | output types | nothing. Models live in `schemas/`, per project rule |
| `quantitative/allocation_optimizer.py` — `AllocationOptimizer` | pure domain: price matrix + constraints → weights | pypfopt, numpy, pandas |
| `orchestrators/allocation_orchestrator.py` — `AllocationOrchestrator` | assembles the matrix from state, calls the optimiser | `HistoricalDataManager`, `AllocationOptimizer` |
| `reporting/sections/optimal_allocation.py` | renders current vs target | the schema alone |
| `flows/orchestrator.py` | Phase 3.7 | the orchestrator |
| `flow_state_models.py` | `optimal_allocation`, `optimal_allocation_error` | — |

The optimiser never touches flow state and never fetches data. It takes a DataFrame and returns weights. That is what makes it testable without a network or a flow.

### 3. The numerical core

```python
S = CovarianceShrinkage(prices).ledoit_wolf()
ef = EfficientFrontier(None, S, weight_bounds=(0.0, per_position_cap))
for asset_class, cap in class_caps.items():
    ef.add_constraint(lambda w, idx=index_of[asset_class], c=cap: cvxpy.sum(w[idx]) <= c)
ef.min_volatility()
weights = ef.clean_weights()
```

Verified against the installed versions (pypfopt 1.6.0, cvxpy 1.9.2) on 2026-09-05: `min_volatility()` accepts `expected_returns=None`, weights sum to 1, and both the per-position and per-class caps bind correctly. Note that `clean_weights()` takes no argument — it reads the weights the objective call already produced.

Shrinkage is not a refinement here, it is a requirement. Sixty-four assets estimated from roughly 252 daily observations puts the sample covariance matrix at n ≈ p, where it is ill-conditioned and its inverse — which the optimiser needs — is unstable. Ledoit-Wolf shrinkage toward a structured target is the standard remedy and is applied unconditionally.

### 4. Constraints

Both are defaults, both configurable.

- **Per position: 8%.** At 64 holdings equal weight is 1.6%, so 8% permits conviction up to five times neutral without allowing a dominant position.
- **Per asset class: current class weight + 10 percentage points.** Today's split is roughly stocks 62 / ETF 31 / crypto 7, so crypto cannot exceed 17%. This prevents a wholesale class rotation nobody asked for while leaving the optimiser room to move.

"Current class weight" means the weight over **priced** holdings, computed from the same set that feeds the allocation hero — not over all 64 CSV entries. Deriving it from a different denominator than the one displayed beside it is the exact defect 5.14.1 fixed, and it must not be reintroduced here.

### 5. Calendar alignment

**This decides the result more than the optimiser does.** The portfolio spans seven European venues (`.SW`, `.PA`, `.DE`, `.L`, `.AS`, `.F`, `.DU`), US listings, and four cryptocurrencies that trade every day of the year. Swiss, French and German market holidays do not coincide; crypto weekends exist for no equity. A strict inner join on common dates would collapse the observation count far below what the covariance estimate needs.

The rule:

1. Reindex every series onto the union of business days in the window.
2. Forward-fill each series by at most 3 days, absorbing single-market holidays without inventing a week of prices.
3. Drop any date still incomplete after that fill.
4. Restrict crypto to business days, so it aligns with equities rather than dragging weekend moves into a matrix nothing else observes.

The surviving observation count is recorded in `OptimalAllocation` metadata. It is a diagnostic, not an implementation detail: a low count is the first thing to look at when a result looks wrong.

### 6. Eligibility and exclusion

A holding needs **at least 120 aligned daily observations** (roughly six months) to enter the optimisation. Below that its covariance row is noise.

Excluded holdings are **listed in the report with their reason**. This follows the pattern established by the 5.14.1 allocation fix: what the system cannot process, it declares. A reader who cannot see an omission cannot question it.

### 7. Failure modes

Three levels, none silent.

**Phase.** `try/except` sets `state.optimal_allocation_error`, logs a warning, and the flow continues. Phase 3.5's template exactly.

**Report.** No optimal allocation, or one carrying an error, renders the current allocation section alone plus one line giving the reason. The section never simply disappears.

**Optimiser.** Two named failures, neither returning partial weights:

- *Infeasible caps.* An 8% per-position cap needs at least 13 eligible holdings to reach 100%. If the history filter leaves 10, no solution exists. pypfopt does raise here — `OptimizationError: Please check your objectives/constraints or use a different solver` — but that message names neither the cap nor the count. Check feasibility before calling the solver and raise with the arithmetic: "10 eligible holdings, minimum 13 under an 8% cap."
- *Solver non-convergence.* Reported as itself, never as an approximate answer.

### 8. Testing

Everything below runs without a network, under the pytest-socket guard, with pytest-mock only.

| Test | Asserts |
|---|---|
| `AllocationOptimizer` on synthetic covariance | caps respected, weights sum to 1, variance strictly below equal-weight |
| Infeasibility | caps × eligible < 1 raises the named error with its arithmetic, before the solver is called |
| Calendar alignment | a crypto series and two venue series with disjoint holidays produce the expected observation count |
| Orchestrator, `HistoricalDataManager` mocked | short-history ticker excluded, with its reason |
| Section, both paths | nominal render; degraded render carries the reason |

This is deterministic Python end to end. It falls fully inside the coverage gate — there is no AI path here to exempt.

**The synthetic fixture must use heterogeneous volatilities.** Measured on 2026-09-05 across four setups: with identical volatilities across assets, equal weight *is* the minimum-variance portfolio, so a binding class cap can only push the solution away from it and the "beats equal-weight" assertion fails against a perfectly correct implementation. With heterogeneous volatilities — as any real portfolio has — minimum variance wins comfortably whether or not the class cap binds (0.0035 vs 0.0047 in the measured case). Draw per-asset volatilities from a range such as 0.005–0.03 and the assertion is sound.

## Risks

**The advice may be unwelcome rather than wrong.** Minimum variance systematically favours low-volatility holdings. It will propose trimming exactly the positions that performed best, because past return plays no part in the objective. That is the intended behaviour of the chosen estimator, and the report must say so plainly next to the table, or the number will be read as a forecast.

**Nothing consumes the weights yet.** Stage 1 is advisory by construction. If Stage 2 never follows, this is a section in a report and no more.

**pypfopt is currently reachable only from dead code.** `BenchmarkAnalyzer` has never run in production. Its dependency is declared and installed, and plotly 7.0 / pypfopt were exercised directly on 2026-09-05, but the first live run of this path is the first real exercise of the library in this codebase.

## Implementation order

1. `schemas/portfolio_optimization.py` — types first, so everything downstream is typed against a fixed contract.
2. `quantitative/allocation_optimizer.py` + tests — pure, offline, no dependency on the rest.
3. `orchestrators/allocation_orchestrator.py` + tests — alignment and exclusion logic, `HistoricalDataManager` mocked.
4. `flow_state_models.py` + `flows/orchestrator.py` — Phase 3.7 wiring.
5. `reporting/sections/optimal_allocation.py` + tests, and its call site in `python_report_generator.py`.
6. Live `crewai flow kickoff` to verify against the real 64-holding portfolio.

Each step leaves the suite green. Steps 1-3 change no production behaviour at all.

## Done when

- A live run renders an optimal allocation section listing target weight and delta per holding, with excluded holdings and their reasons.
- No holding exceeds 8%; no asset class exceeds its current weight plus 10 points.
- The surviving observation count is visible in the run log and in the section metadata.
- Killing the optimiser (forced exception) degrades the report to the current allocation alone, with the reason shown, and the run still completes.
- `make check` green.
