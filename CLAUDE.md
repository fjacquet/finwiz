# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinWiz is a sophisticated AI-powered financial analysis platform built with CrewAI. It uses autonomous AI agents to perform comprehensive analysis of stocks, ETFs, cryptocurrencies, and portfolios. The platform emphasizes **AI Minimalism** - using Python for deterministic tasks and AI only where reasoning is required.

**Key Capabilities:**
- Multi-asset financial analysis (stocks, ETFs, crypto)
- Portfolio review with keep/sell recommendations
- Portfolio rebalancing with optimization
- A+ investment discovery across markets
- Quantitative analysis with professional-grade libraries (Backtrader, TA-Lib, QuantLib)
- Batch processing for high-performance portfolio analysis (10-20x speedup)
- Python-based scoring engine (100% cost reduction vs AI)

## Commands

### Development & Testing

```bash
# Run the main application
crewai flow kickoff

# Install dependencies
uv sync

# Testing
make test                  # Unit tests only (< 3 minutes)
make test-all              # All tests including integration
make coverage              # Test coverage report

# Code Quality
make lint                  # Ruff linting
make format                # Auto-format with ruff
make mypy                  # Type checking
make check                 # All quality checks

# Cleanup
make clean                 # Clean cache directories
make cleanup               # Full codebase cleanup
```

### Documentation

```bash
make docs-serve            # Preview docs locally (Jekyll or simple HTTP server)
make docs-lint             # Lint markdown files
make docs-validate         # Validate documentation structure
make docs-clean            # Clean documentation artifacts
```

### HTML Report Generation

```bash
make html-reports          # Generate all HTML reports
make html-convert          # Convert JSON to HTML
```

## Architecture

### Core Design Principles

1. **AI Minimalism**: Use Python for deterministic calculations, AI only for analysis requiring reasoning
2. **Pydantic-First**: All outputs validated with strict schemas
3. **File-Based Data Passing**: Pass file paths (not data) between crews to avoid context limits
4. **Concurrent Execution**: SME crews run in parallel for maximum performance
5. **Clean Separation**: Analysis (AI) vs presentation (Python templates)

### Directory Structure

```
src/finwiz/
├── crews/                      # CrewAI agent crews
│   ├── stock_crew/            # Stock analysis
│   ├── etf_crew/              # ETF analysis
│   ├── crypto_crew/           # Cryptocurrency analysis
│   ├── portfolio_rebalancing_crew/
│   ├── investment_discovery_crew/
│   ├── report_crew/           # Final consolidation (NO tools)
│   └── deep_analysis/         # Per-holding deep analysis
│
├── flows/                      # CrewAI Flow orchestration
│   └── flow_orchestrator.py   # Main workflow coordination
│
├── orchestrators/              # Business logic coordination
│   ├── portfolio_review.py
│   ├── rebalancing_*.py
│   └── review_decisions.py
│
├── quantitative/               # Quant analysis (modernized)
│   ├── technical/             # Technical analysis (split from monolith)
│   ├── backtesting.py         # Backtrader integration
│   ├── optimization.py        # Portfolio optimization
│   ├── derivatives.py         # QuantLib derivatives
│   ├── screening.py           # Stock screening
│   └── portfolio_*.py         # Portfolio management
│
├── integration/                # Data integration (modernized)
│   ├── data_accessor.py       # Core data access
│   ├── data_validation.py     # Validation logic
│   └── data_cache.py          # Caching logic
│
├── tools/                      # Custom financial tools
│   ├── tool_factories.py      # Centralized tool initialization
│   ├── quantitative_analysis_tool.py
│   ├── enhanced_sentiment_tool.py
│   └── scoring/               # Python scoring engines
│
├── schemas/                    # Pydantic data models
│   └── crew_exports.py        # Export schemas per crew
│
├── scoring/                    # Deterministic scoring
│   └── deep_analysis_scorer.py
│
├── reporting/                  # Report generation
│   └── deep_analysis_report_generator.py
│
├── templates/                  # Jinja2 templates
│   └── crew_reports/
│
├── utils/                      # Utilities
│   ├── agent_validators.py    # @final_reporter decorator
│   ├── task_decorators.py     # @async_task, @sync_task
│   └── logging_helpers.py     # CrewLogger
│
└── validation/                 # Validation infrastructure
```

### Flow Architecture

FinWiz uses CrewAI Flow for orchestration with structured Pydantic state management:

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class FinwizState(BaseModel):
    """Type-safe flow state."""
    portfolio_review: dict = {}
    deep_analysis_results: dict = {}

class FinwizFlow(Flow[FinwizState]):
    @start()
    def initialize(self) -> dict[str, Any]:
        # Update structured state
        self.state.portfolio_review = {}
        # Return for downstream listeners
        return {"status": "initialized"}

    @listen(initialize)
    def analyze_portfolio(self, data: dict[str, Any]) -> dict[str, Any]:
        # Direct crew execution (CrewAI standard)
        crew = StockCrew()
        result = crew.crew().kickoff(inputs={"ticker": "AAPL"})

        # Update state and return
        self.state.deep_analysis_results = result.raw
        return {"results": result.raw}
```

**CRITICAL Flow Rules:**
- ✅ Use `Flow[PydanticModel]` for type safety
- ✅ All Flow methods return `dict[str, Any]`
- ✅ Access state via `self.state.field_name`
- ✅ Direct crew instantiation (not factory patterns)
- ❌ NEVER use `self.inputs` (deprecated)

### Crew Structure

Every crew follows this exact structure:

```
crews/{crew_name}/
├── {crew_name}.py          # @agent, @task, @crew decorators
└── config/
    ├── agents.yaml         # Agent configurations
    └── tasks.yaml          # Task definitions
```

**Agent Configuration Standards:**

```python
from crewai import Agent, agent
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.agent_validators import final_reporter

@agent
def analyst(self) -> Agent:
    return Agent(
        config=self.agents_config["analyst"],
        tools=get_stock_crew_tools(include_rag=True),
        reasoning=True,              # For complex analysis
        max_reasoning_attempts=3,    # Prevent infinite loops
        allow_delegation=False,      # Only for coordinators
        max_rpm=20,                  # Rate limiting
        verbose=True
    )

@final_reporter  # Enforces empty tools
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # MUST be empty
        reasoning=False,
        verbose=True
    )
```

**Task Configuration Standards:**

```yaml
# config/tasks.yaml
analysis_task:
  description: "Analyze {ticker} with quantitative metrics"
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "TenKInsight"
  output_json: true
  agent: analyst
  async_execution: true  # Except final task
```

### Tool Factories Pattern

Centralized tool initialization eliminates code duplication:

```python
from finwiz.tools.tool_factories import (
    get_stock_crew_tools,
    get_etf_crew_tools,
    get_crypto_crew_tools
)

# Get standardized tool set
tools = get_stock_crew_tools(
    include_rag=True,
    include_quantitative=True,
    collection_suffix="stock"
)
```

### Performance Optimization Rules

**Reasoning (`reasoning=True`)**:
- Enable: Complex analysis, multi-step workflows
- Disable: Validators, reporters, high-volume (66+ executions)
- Cost: 5-15s, 1-3 LLM calls

**Planning (`planning=True`)**:
- Enable: 4+ agents AND 6+ tasks AND ≤3 runs
- Disable: High-volume, single-agent crews
- Example: Portfolio rebalancing (single run) ✅, Deep analysis (66 runs) ❌

**Delegation (`allow_delegation=True`)**:
- Enable: Coordinators managing workflow
- Disable: Specialists, reporters
- Cost: 5-15s per delegation

### Batch Processing System

For portfolio analysis with 10+ holdings, batch processing provides 10-20x speedup:

**Configuration** (`.env`):
```bash
BATCH_PREFETCH_ENABLED=true           # Enable batch mode
DEEP_ANALYSIS_BATCH_SIZE=5            # Concurrent crews
BATCH_PREFETCH_MIN_HOLDINGS=10        # Trigger threshold
ENABLE_ALPHA_VANTAGE=false            # Yahoo Finance sufficient
```

**Performance**:
- 66 holdings: 5.5-11 hours → 20-40 minutes
- Data pre-fetch: 2-5 seconds (Yahoo Finance)
- Concurrent execution: 5 crews in parallel (configurable)

### Python Scoring Engine

Replace AI-based calculations with deterministic Python for 10-20x speedup and 100% cost reduction:

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()
result = scorer.calculate_composite_score(
    ticker="AAPL",
    asset_class="stock",
    data={
        "roe": 0.25,
        "debt_to_equity": 0.3,
        "revenue_growth": 0.15,
        # ... metrics
    }
)
# Grade: A, Score: 0.78, Recommendation: BUY
```

**When to Use**:
- Deep analysis scoring
- Portfolio screening
- Risk assessment calculations
- Performance metrics

## Important Patterns

### 1. Final Reporter Pattern

Final reporters MUST have empty tools and only consume upstream context:

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter  # Enforces NO tools
@agent
def investment_reporter(self) -> Agent:
    return Agent(
        config=self.agents_config['investment_reporter'],
        tools=[],  # Required
        reasoning=False,  # No complex reasoning needed
        verbose=True
    )
```

### 2. Task Execution Pattern

Use decorators to make async/sync execution explicit:

```python
from finwiz.utils.task_decorators import async_task, sync_task

@async_task
@task
def research_task(self) -> Task:
    return Task(
        config=self.tasks_config['research'],
        agent=self.researcher()
    )

@sync_task  # Final task MUST be sync
@task
def final_report_task(self) -> Task:
    return Task(
        config=self.tasks_config['final_report'],
        agent=self.reporter()
    )
```

### 3. Structured Logging

Use `CrewLogger` for consistent logging across crews:

```python
from finwiz.utils.logging_helpers import CrewLogger

class StockCrew:
    def __init__(self):
        super().__init__()
        self.logger = CrewLogger("StockCrew")

    def kickoff(self, inputs: dict) -> Any:
        self.logger.log_start(inputs)
        start_time = time.time()

        try:
            result = super().kickoff(inputs)
            duration = time.time() - start_time
            self.logger.log_complete(duration)
            return result
        except Exception as e:
            self.logger.log_error(e)
            raise
```

### 4. Pydantic Schema Validation

All crew outputs must use Pydantic schemas:

```python
from finwiz.schemas.crew_exports import StockCrewExport

# Crew generates validated export
export = StockCrewExport(
    ticker="AAPL",
    asset_class="stock",
    composite_score=0.85,
    grade="A",
    recommendation="BUY"
)

# Save to JSON
export_path = f"output/reports/{session_id}/stock_crew/AAPL_export.json"
with open(export_path, 'w') as f:
    f.write(export.model_dump_json(indent=2))
```

### 5. HTML Report Generation

Use Jinja2 templates (NO AI) for report generation:

```python
from finwiz.tools.html_report_generator import HTMLReportGenerator

generator = HTMLReportGenerator()
html_path = generator.generate_crew_report(
    crew_name="stock_crew",
    export_data=export.model_dump(),
    output_path=f"output/reports/{session_id}/stock_crew/AAPL_report.html"
)
```

## Testing Standards

### Test Infrastructure

- **Framework**: pytest with pytest-mock (NEVER unittest.mock)
- **Mocking**: All external dependencies (APIs, file system, LLM calls)
- **Test Data**: Faker library for realistic data generation
- **Coverage**: Minimum 65% (configured in pyproject.toml)

### Test Markers

```bash
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests (requires API keys)
pytest -m slow              # Slow-running tests
pytest -m performance       # Performance benchmarks
```

### unittest.mock Ban

NEVER use `unittest.mock`. Use pytest-mock instead:

```python
# ❌ WRONG
from unittest.mock import Mock, patch

# ✅ CORRECT
def test_example(mocker):
    mock_obj = mocker.Mock()
    mocker.patch('module.function', return_value="result")
```

Enforcement is in `pyproject.toml` and `make check-unittest-mock`.

### Type Checking

```bash
make mypy                   # Type check entire codebase
uv run mypy src/finwiz/     # Type check source
```

**Type Hint Standards** (Python 3.12+):
- Use `str | None` instead of `Optional[str]`
- Use `list[Type]` instead of `List[Type]`
- All public functions must have type hints
- Return types must be explicit

## AI Minimalism Principles

**Core Principle**: AI agents are tools, not the alpha and omega. Use Python for deterministic tasks.

### Use AI ONLY For:
✅ Analysis requiring reasoning (interpreting complex financial data)
✅ Synthesis of complex information (combining multiple data sources)
✅ Generating insights from unstructured data (news, sentiment)
✅ Natural language understanding (parsing text)
✅ Creative content generation (writing analysis narratives)

### Use Python (NOT AI) For:
❌ HTML generation (use Jinja2 templates)
❌ Data consolidation (use Python functions)
❌ File I/O operations (use standard Python)
❌ Calculations and formulas (use Python/numpy)
❌ Data validation (use Pydantic)
❌ Template rendering (use Jinja2)
❌ Deterministic logic (use if/else, loops)

### Cost Comparison Example

Generating 100 HTML reports:

| Approach | Cost | Time | Reliability |
|----------|------|------|-------------|
| AI Agent | $5-10 | 500-1000s | 95% |
| Python Template | $0 | 1-2s | 100% |

**Savings: $5-10, 500x faster, 100% reliable**

### Evaluation Checklist

Before creating an AI task, ask:
- Is this deterministic? (same input = same output)
- Can this be expressed as a template?
- Is this data transformation or calculation?
- Can a junior developer implement this in Python?

If YES to any → **Use Python, not AI**

## Data Quality Principles

1. **Fail Fast**: Reject invalid data at source
2. **Transparency**: Communicate when data unavailable
3. **No Hallucinations**: Never generate fake URLs or metrics
4. **Completeness**: Process all available data
5. **Traceability**: Log all data decisions

## Code Modernization

The codebase has undergone significant modernization:

- **File Decomposition**: Large files (1000+ lines) split into focused modules
- **Target**: Keep files under 200 lines for maintainability
- **Scientific Package Optimization**: Use pandas/numpy for calculations
- **Modular Architecture**: Clear separation of concerns

**Current Status**:
- Files >600 lines: 17 remaining (started with 27)
- Test Pass Rate: 82.2% (target: >95%)
- Phase 0 (Fix Test Suite) is **CRITICAL PRIORITY** blocking all refactoring

## Refactoring Standards

### File Organization Rules

**Schema Models**:
- ✅ All Pydantic models go in `src/finwiz/schemas/`
- ✅ Domain-specific subfolders: `schemas/quantitative/`, `schemas/rebalancing/`
- ✅ Business logic stays in domain folders: `quantitative/`, `tools/`, `orchestrators/`

**File Size Limits**:
- **Hard limit**: 300 lines per file
- **Ideal target**: 150-200 lines
- **Minimum**: 50 lines (avoid tiny files)

**When to Split**:
- File >300 lines → MUST split
- File >250 lines → Should split
- File >200 lines → Consider splitting

### Refactoring Checklist

Before splitting any large file:
- [ ] Check existing patterns (especially schema location)
- [ ] Plan structure (sketch new file organization)
- [ ] Ensure no file will exceed 300 lines
- [ ] Plan test updates (imports and mock paths)
- [ ] Create re-export layer for backward compatibility
- [ ] Execute split and update all tests
- [ ] Verify ALL tests pass (not just new ones)

**CRITICAL**: Never leave failing tests after refactoring. Tests are the contract.

### JSON Serialization Rule

When using `json.dumps()`, always include `default=str` to handle datetime, numpy types:

```python
# ❌ WRONG
result = json.dumps(data)

# ✅ CORRECT
result = json.dumps(data, default=str)

# ✅ BEST (with Pydantic)
result = model.model_dump_json(indent=2)
```

### Strategy Pattern (ABC)

For asset-specific logic (stock/ETF/crypto), use Python ABC pattern instead of conditional logic:

```python
from abc import ABC, abstractmethod

class AssetAnalyzer(ABC):
    @abstractmethod
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        pass

class StockAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        # Stock-specific logic only
        return score, details

class AnalyzerFactory:
    _ANALYZERS = {
        "stock": StockAnalyzer,
        "etf": ETFAnalyzer,
        "crypto": CryptoAnalyzer,
    }

    @classmethod
    def get_analyzer(cls, asset_class: str) -> AssetAnalyzer:
        return cls._ANALYZERS[asset_class.lower()]()
```

**Benefits**: Each strategy 50-150 lines, easy to test, follows Open/Closed Principle.

## Flow Architecture Lessons

### 1. Flow Sequence Must Match Business Logic

Design flow sequences to match logical business process:

```python
# ✅ CORRECT: Portfolio analysis → Discovery → Rebalancing
@listen("validate_data_integration")
def check_portfolio(self):  # Analyze what you have FIRST
    pass

@listen("analyze_and_update_portfolio")
def check_crypto(self):  # Discover new opportunities AFTER
    pass
```

### 2. Consolidate Related Operations

When operations are sequential and related, consolidate into ONE atomic method:

```python
# ✅ CORRECT: Atomic operation
@listen("check_portfolio")
def analyze_and_update_portfolio(self) -> dict[str, Any]:
    """Atomic: deep analysis + alternatives + portfolio update."""
    deep_results = self._run_deep_analysis()
    alternatives = self._match_alternatives(deep_results)
    portfolio = self._update_portfolio()  # Only once!
    return {"results": portfolio}
```

Benefits: No race conditions, simpler dependencies, atomic semantics.

### 3. Reasoning-Compatible Task Descriptions

For reasoning agents, be EXPLICIT about single-ticker mode:

```yaml
analysis_task:
  description: >
    Perform analysis of the provided {asset_class} ticker: {ticker}

    SINGLE TICKER MODE: Analyze ONE specific {asset_class}.
    The ticker {ticker} is provided. Do NOT request additional tickers.

    Steps for {ticker}:
    1. Validate {ticker}
    2. Fetch data for {ticker}
    3. Analyze {ticker}
```

Repeat `{ticker}` throughout to prevent reasoning loops.

## Anti-Patterns to Avoid

❌ Using `self.inputs` instead of `self.state` in Flows
❌ Flow methods not returning `dict[str, Any]`
❌ Final reporters with tools
❌ Missing `max_reasoning_attempts` when reasoning enabled
❌ Enabling reasoning for high-volume executions (66+ runs)
❌ Enabling planning for single-agent crews
❌ Hardcoded tool lists (use tool factories)
❌ Async final task in sequential workflows
❌ Using `unittest.mock` instead of pytest-mock
❌ Missing type hints on public functions
❌ Generating fake data to fill gaps
❌ Putting Pydantic models in domain folders (use `schemas/`)
❌ Leaving failing tests after refactoring
❌ Using `json.dumps()` without `default=str`
❌ Discovery crews running before portfolio analysis
❌ Creating separate crews when dynamic routing suffices

## Critical Lessons Learned

From `.kiro/LESSONS_LEARNED.md`:

### Always Check Existing Patterns First
- Look at similar components in the codebase
- Follow established conventions (e.g., Pydantic models in `schemas/`)
- Don't create new patterns unless necessary

### Tests Are The Contract
- Never leave failing tests after refactoring
- Update test imports when moving code
- Fix mock paths to point to actual import locations
- Verify ALL tests pass before marking task complete

### Backward Compatibility Matters
- Create re-export layer in original location
- Existing code should work without changes
- Gradual migration path for large codebases

Example re-export pattern:
```python
# Old location: src/finwiz/quantitative/config.py (now thin re-export)
from finwiz.schemas.quantitative.config_models import BacktestConfig
from finwiz.quantitative.config_manager import QuantitativeConfigManager

__all__ = ["BacktestConfig", "QuantitativeConfigManager"]
```

## AI Development Standards

See `.kiro/steering/` for comprehensive AI development guidance:
- `crewai-standards.md`: CrewAI development patterns (CRITICAL)
- `ai-minimalism.md`: When to use Python vs AI
- `flow-architecture-lessons.md`: Flow design patterns
- `python-abc-strategy-pattern.md`: Strategy pattern with ABC
- `codebase-refactoring-patterns.md`: File organization rules
- `testing-standards.md`: Testing best practices

## Key References

- **CrewAI Flow Docs**: https://docs.crewai.com/concepts/flows
- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **pytest-mock**: https://pytest-mock.readthedocs.io/

## Environment Variables

Key configuration in `.env`:

```bash
# Required
OPENAI_API_KEY=your_key
SERPER_API_KEY=your_key

# Performance Optimization
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
RISK_ASSESSMENT_USE_MINI=true

# Validation
VALIDATION_STRICTNESS=warn  # off/warn/error

# Caching
CACHE_BACKEND=hybrid        # memory/file/hybrid
CACHE_TTL=2700             # 45 minutes
```

## Common Workflows

### Creating a New Crew

1. Create crew directory: `src/finwiz/crews/new_crew/`
2. Add `new_crew.py` with `@agent`, `@task`, `@crew` decorators
3. Add `config/agents.yaml` and `config/tasks.yaml`
4. Use tool factories for tool assignment
5. Define Pydantic export schema in `schemas/crew_exports.py`
6. Add tests in `tests/unit/crews/test_new_crew.py`
7. Document in README.md

### Running Analysis

```bash
# Full portfolio analysis
crewai flow kickoff

# Specific crew (for testing)
uv run python src/finwiz/main.py --ticker AAPL

# A+ discovery
uv run python src/finwiz/main.py --discovery

# Portfolio rebalancing
uv run python src/finwiz/main.py --rebalancing
```

### Debugging

```bash
# Enable verbose logging
export CREW_VERBOSE=true

# Run single test with output
pytest tests/path/to/test.py::test_name -v -s

# Type check specific file
uv run mypy src/finwiz/path/to/file.py

# Check for unittest.mock violations
make check-unittest-mock
```

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
