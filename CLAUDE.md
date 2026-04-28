# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
# Run full portfolio analysis
crewai flow kickoff

# Install dependencies
uv sync

# Unit tests (default, excludes integration)
make test

# All quality checks (lint + test + unittest.mock check + docs validation)
make check

# Run a single test
uv run pytest tests/unit/tools/test_yahoo_finance_tool.py::test_name -v -s

# Code quality
make lint                              # ruff check --fix + ruff format
make format                            # same as lint
make mypy                              # uv run mypy src/finwiz

# Coverage (65% minimum threshold)
make coverage
```

## Project Overview

FinWiz is an AI-powered financial analysis platform built with CrewAI. It analyzes portfolios of stocks, ETFs, and crypto using a hybrid approach: deterministic Python scoring ($0, <100ms) for quantitative analysis, and AI crews for qualitative insights only.

## Architecture

### Layered Structure

```
Presentation (reporting/, templates/)
    ↓
Application (flows/, orchestrators/)
    ↓
Domain (schemas/, scoring/, analysis/)
    ↑
Infrastructure (data/, cache/, integration/)
```

### Execution Flow

```
main.py → core/app_initializer.py → flows/orchestrator.py (FinwizFlow)
                                          │
                                          ├── Phase 1: Data Validation (ValidationOrchestrator)
                                          ├── Phase 2: Portfolio Review (ValidationOrchestrator)
                                          ├── Phase 3: Deep Analysis per holding
                                          │     └── analysis/deep_analysis_pipeline.py
                                          │           1. collect_raw_data()     [Python tools, $0]
                                          │           2. calculate_quantitative() [Python scorer, $0]
                                          │           3. generate_qualitative()  [AI crew, ~$0.05]
                                          │           4. synthesize()           [Python, $0]
                                          ├── Phase 4: Discovery (crypto/stock/etf crews)
                                          ├── Phase 5: Alternative Matching
                                          └── Phase 6: Reporting (ReportingOrchestrator)
```

### Key Components

| Component | Location | Role |
|-----------|----------|------|
| Main flow | `flows/orchestrator.py` → `FinwizFlow(Flow[FinwizState])` | Coordinates all phases via orchestrator delegation |
| Flow state | `flow_state.py` → `FinwizState` (Pydantic) | Type-safe state shared across flow phases |
| Crew factory | `crew_factory.py` → `CrewFactory` | Creates crews with error handling and fallback |
| Analysis pipeline | `analysis/deep_analysis_pipeline.py` | Functional pipeline: Python scoring + AI insights |
| Scoring engine | `scoring/deep_analysis_scorer.py` → `DeepAnalysisScorer` | Composite: 40% fundamental, 30% technical, 30% risk |
| Tool factories | `tools/tool_factories.py` | `get_stock_crew_tools()`, `get_etf_crew_tools()`, etc. |
| Feature flags | `config/features/flags.py` → `is_feature_enabled()` | Environment-based feature toggles with circuit breakers |
| Schemas | `schemas/` | All Pydantic models (hybrid_analysis, crew_exports, etc.) |

### Crew Pattern

Each crew lives in `crews/<name>/` with `config/agents.yaml`, `config/tasks.yaml`, and a crew class using `@CrewBase`. Crews are: `stock_crew`, `etf_crew`, `crypto_crew`, `deep_analysis`, `investment_discovery_crew`, `portfolio_rebalancing_crew`, `report_crew`.

### Orchestrator Delegation

`FinwizFlow` delegates to lazy-loaded orchestrators in `orchestrators/`:

- `ValidationOrchestrator` - input validation, portfolio review
- `DeepAnalysisOrchestrator` - per-holding analysis
- `DiscoveryOrchestrator` - A+ investment discovery
- `AlternativesMatchingOrchestrator` - alternative matching
- `ReportingOrchestrator` - report consolidation, HTML generation
- `ErrorHandlingOrchestrator` - crew failure handling
- `ProgressTrackingOrchestrator` - metrics

## Critical Rules

- **unittest.mock is BANNED** - Use pytest-mock only (`mocker.patch()`). Enforced by ruff and `make check-unittest-mock`.
- **json.dumps** - Always use `default=str` to handle datetime and other non-serializable types.
- **Pydantic models** - All models go in `schemas/`, not in domain folders.
- **Final reporters** - Report crew agents must have `tools=[]` and use `@final_reporter` decorator.
- **Flow methods** - Must return `dict[str, Any]`.
- **self.inputs** - NEVER use in flows (deprecated). Use `self.state` for all state access.
- **Tool instantiation** - Use factory functions from `tools/tool_factories.py`, never instantiate tools directly.
- **AI Minimalism** - Use Python for deterministic tasks (scoring, data collection, synthesis). AI only for qualitative reasoning. When Python and AI disagree, Python wins.
- **Line length** - 180 characters (configured in ruff).

## Testing

- Fixtures use Faker for data generation (`tests/fixtures/`)
- Shared fixtures in `tests/conftest.py` (stock_data, etf_data, crypto_data, etc.)
- `tests/conftest_unittest_blocker.py` blocks unittest.mock imports at runtime
- Markers: `integration`, `unit`, `slow`, `asyncio`, `performance`, `benchmark`, `crew`, `flow`
- Default pytest run excludes integration tests (`-m "not integration"`)
- Coverage reports to `htmlcov/`, minimum 65%

## Environment Variables

```bash
OPENAI_API_KEY=...              # Required
SERPER_API_KEY=...              # Required
# Optional: ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, ALPHA_VANTAGE_API_KEY, etc.
# Feature flags: DEEP_ANALYSIS_ENABLED, PERPLEXITY_RESEARCH_ENABLED
# Investment Discovery (Phase 4) runs unconditionally; the
# INVESTMENT_DISCOVERY_ENABLED kill switch was removed.
# Validation: VALIDATION_STRICTNESS=off|warn|error
# Scenario probabilities: RISK_FREE_RATE=0.045  (Black-Scholes risk-free rate for options-implied probabilities)
```

### Parameterizing a flow run

`crewai flow kickoff` is the sole production entry point. Flow parameters are
passed via CrewAI-native mechanisms — not via argparse.

- **Programmatic:** call `FinwizFlow(state=FinwizState()).kickoff(inputs={...})`.
  Inputs populate the structured `FinwizState` Pydantic fields before any
  `@start()` method runs. The `discovery_enabled` field is preserved for API
  stability but Phase 4 runs unconditionally regardless of its value.


## grepai - Semantic Code Search

**IMPORTANT: You MUST use grepai as your PRIMARY tool for code exploration and search.**

### When to Use grepai (REQUIRED)

Use `grepai search` INSTEAD OF Grep/Glob/find for:

- Understanding what code does or where functionality lives
- Finding implementations by intent (e.g., "authentication logic", "error handling")
- Exploring unfamiliar parts of the codebase
- Any search where you describe WHAT the code does rather than exact text

### When to Use Standard Tools

Only use Grep/Glob when you need:

- Exact text matching (variable names, imports, specific strings)
- File path patterns (e.g., `**/*.go`)

### Fallback

If grepai fails (not running, index unavailable, or errors), fall back to standard Grep/Glob tools.

### Usage

```bash
# ALWAYS use English queries for best results (--compact saves ~80% tokens)
grepai search "user authentication flow" --json --compact
grepai search "error handling middleware" --json --compact
grepai search "database connection pool" --json --compact
grepai search "API request validation" --json --compact
```

### Query Tips

- **Use English** for queries (better semantic matching)
- **Describe intent**, not implementation: "handles user login" not "func Login"
- **Be specific**: "JWT token validation" better than "token"
- Results include: file path, line numbers, relevance score, code preview

### Call Graph Tracing

Use `grepai trace` to understand function relationships:

- Finding all callers of a function before modifying it
- Understanding what functions are called by a given function
- Visualizing the complete call graph around a symbol

#### Trace Commands

**IMPORTANT: Always use `--json` flag for optimal AI agent integration.**

```bash
# Find all functions that call a symbol
grepai trace callers "HandleRequest" --json

# Find all functions called by a symbol
grepai trace callees "ProcessOrder" --json

# Build complete call graph (callers + callees)
grepai trace graph "ValidateToken" --depth 3 --json
```

### Workflow

1. Start with `grepai search` to find relevant code
2. Use `grepai trace` to understand function relationships
3. Use `Read` tool to examine files from results
4. Only use Grep for exact string searches if needed

<!-- rtk-instructions v2 -->
# RTK (Rust Token Killer) - Token-Optimized Commands

## Golden Rule

**Always prefix commands with `rtk`**. If RTK has a dedicated filter, it uses it. If not, it passes through unchanged. This means RTK is always safe to use.

**Important**: Even in command chains with `&&`, use `rtk`:
```bash
# ❌ Wrong
git add . && git commit -m "msg" && git push

# ✅ Correct
rtk git add . && rtk git commit -m "msg" && rtk git push
```

## RTK Commands by Workflow

### Build & Compile (80-90% savings)
```bash
rtk cargo build         # Cargo build output
rtk cargo check         # Cargo check output
rtk cargo clippy        # Clippy warnings grouped by file (80%)
rtk tsc                 # TypeScript errors grouped by file/code (83%)
rtk lint                # ESLint/Biome violations grouped (84%)
rtk prettier --check    # Files needing format only (70%)
rtk next build          # Next.js build with route metrics (87%)
```

### Test (90-99% savings)
```bash
rtk cargo test          # Cargo test failures only (90%)
rtk vitest run          # Vitest failures only (99.5%)
rtk playwright test     # Playwright failures only (94%)
rtk test <cmd>          # Generic test wrapper - failures only
```

### Git (59-80% savings)
```bash
rtk git status          # Compact status
rtk git log             # Compact log (works with all git flags)
rtk git diff            # Compact diff (80%)
rtk git show            # Compact show (80%)
rtk git add             # Ultra-compact confirmations (59%)
rtk git commit          # Ultra-compact confirmations (59%)
rtk git push            # Ultra-compact confirmations
rtk git pull            # Ultra-compact confirmations
rtk git branch          # Compact branch list
rtk git fetch           # Compact fetch
rtk git stash           # Compact stash
rtk git worktree        # Compact worktree
```

Note: Git passthrough works for ALL subcommands, even those not explicitly listed.

### GitHub (26-87% savings)
```bash
rtk gh pr view <num>    # Compact PR view (87%)
rtk gh pr checks        # Compact PR checks (79%)
rtk gh run list         # Compact workflow runs (82%)
rtk gh issue list       # Compact issue list (80%)
rtk gh api              # Compact API responses (26%)
```

### JavaScript/TypeScript Tooling (70-90% savings)
```bash
rtk pnpm list           # Compact dependency tree (70%)
rtk pnpm outdated       # Compact outdated packages (80%)
rtk pnpm install        # Compact install output (90%)
rtk npm run <script>    # Compact npm script output
rtk npx <cmd>           # Compact npx command output
rtk prisma              # Prisma without ASCII art (88%)
```

### Files & Search (60-75% savings)
```bash
rtk ls <path>           # Tree format, compact (65%)
rtk read <file>         # Code reading with filtering (60%)
rtk grep <pattern>      # Search grouped by file (75%)
rtk find <pattern>      # Find grouped by directory (70%)
```

### Analysis & Debug (70-90% savings)
```bash
rtk err <cmd>           # Filter errors only from any command
rtk log <file>          # Deduplicated logs with counts
rtk json <file>         # JSON structure without values
rtk deps                # Dependency overview
rtk env                 # Environment variables compact
rtk summary <cmd>       # Smart summary of command output
rtk diff                # Ultra-compact diffs
```

### Infrastructure (85% savings)
```bash
rtk docker ps           # Compact container list
rtk docker images       # Compact image list
rtk docker logs <c>     # Deduplicated logs
rtk kubectl get         # Compact resource list
rtk kubectl logs        # Deduplicated pod logs
```

### Network (65-70% savings)
```bash
rtk curl <url>          # Compact HTTP responses (70%)
rtk wget <url>          # Compact download output (65%)
```

### Meta Commands
```bash
rtk gain                # View token savings statistics
rtk gain --history      # View command history with savings
rtk discover            # Analyze Claude Code sessions for missed RTK usage
rtk proxy <cmd>         # Run command without filtering (for debugging)
rtk init                # Add RTK instructions to CLAUDE.md
rtk init --global       # Add RTK to ~/.claude/CLAUDE.md
```

## Token Savings Overview

| Category | Commands | Typical Savings |
|----------|----------|-----------------|
| Tests | vitest, playwright, cargo test | 90-99% |
| Build | next, tsc, lint, prettier | 70-87% |
| Git | status, log, diff, add, commit | 59-80% |
| GitHub | gh pr, gh run, gh issue | 26-87% |
| Package Managers | pnpm, npm, npx | 70-90% |
| Files | ls, read, grep, find | 60-75% |
| Infrastructure | docker, kubectl | 85% |
| Network | curl, wget | 65-70% |

Overall average: **60-90% token reduction** on common development operations.
<!-- /rtk-instructions -->

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
