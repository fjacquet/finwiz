# FinWiz Developer Guide

Comprehensive guide for developers contributing to or extending FinWiz.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Code Organization](#code-organization)
4. [Core Patterns](#core-patterns)
5. [Creating Custom Crews](#creating-custom-crews)
6. [Testing](#testing)
7. [Performance Optimization](#performance-optimization)
8. [Contributing](#contributing)
9. [Deployment](#deployment)

## Architecture Overview

### System Design

FinWiz follows a modular, microservices-inspired architecture built on CrewAI's agent framework.

```
┌─────────────────────────────────────────────────────────────┐
│                     Flow Orchestrator                        │
│                  (CrewAI Flow - Pydantic State)             │
└────────┬────────────────────────────────────────────┬────────┘
         │                                            │
         ▼                                            ▼
┌──────────────────┐                        ┌──────────────────┐
│   Orchestrators  │                        │   Crews (AI)     │
│  (Business Logic)│                        │  (Analysis)      │
├──────────────────┤                        ├──────────────────┤
│ • Portfolio Review│                       │ • Stock Crew     │
│ • Rebalancing    │                        │ • ETF Crew       │
│ • Decisions      │                        │ • Crypto Crew    │
└────────┬─────────┘                        │ • Deep Analysis  │
         │                                  │ • Discovery      │
         ▼                                  └─────────┬────────┘
┌──────────────────┐                                 │
│  Scoring Engine  │                                 ▼
│   (Python)       │                        ┌──────────────────┐
├──────────────────┤                        │      Tools       │
│ • Deep Analysis  │                        ├──────────────────┤
│ • Portfolio      │                        │ • Quantitative   │
│ • Risk           │                        │ • Sentiment      │
└────────┬─────────┘                        │ • Technical      │
         │                                  │ • Data Access    │
         ▼                                  └─────────┬────────┘
┌──────────────────┐                                 │
│  Reporting       │                                 ▼
│  (Jinja2)        │                        ┌──────────────────┐
├──────────────────┤                        │   Integration    │
│ • HTML Reports   │                        ├──────────────────┤
│ • Templates      │                        │ • Data Accessor  │
│ • Formatters     │                        │ • Validation     │
└──────────────────┘                        │ • Caching        │
                                            └──────────────────┘
```

### Core Design Principles

#### 1. AI Minimalism

**Principle**: Use Python for deterministic tasks, AI only where reasoning is required.

**Implementation**:

```python
# ❌ WRONG: Using AI for deterministic calculation
@task
def calculate_score(self) -> Task:
    return Task(
        description="Calculate composite score using AI",
        agent=self.analyst()
    )

# ✅ CORRECT: Use Python for calculations
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()
score = scorer.calculate_composite_score(ticker, asset_class, data)
```

**Benefits**:

- 10-20x speedup
- 100% cost reduction
- Deterministic results
- Easier testing

#### 2. Pydantic-First

**Principle**: All outputs validated with strict Pydantic schemas.

**Implementation**:

```python
from pydantic import BaseModel, Field, field_validator

class StockAnalysis(BaseModel):
    """Stock analysis output schema."""

    ticker: str = Field(..., description="Stock ticker symbol")
    grade: str = Field(..., pattern="^[A-F][+-]?$")
    composite_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or len(v) > 10:
            raise ValueError("Invalid ticker symbol")
        return v.upper()

# Use in crew output
@task
def analysis_task(self) -> Task:
    return Task(
        description="Analyze stock",
        expected_output="Structured analysis",
        output_pydantic=StockAnalysis,  # Enforces schema
        agent=self.analyst()
    )
```

#### 3. File-Based Data Passing

**Principle**: Pass file paths between crews, not large data objects.

**Why**: Avoids context window limits, enables caching, improves performance.

**Implementation**:

```python
# ✅ CORRECT: Pass file paths
@listen("analyze_holdings")
def generate_report(self, data: dict[str, Any]) -> dict[str, Any]:
    # Write analysis to file
    export_path = f"output/reports/{session_id}/analysis.json"
    with open(export_path, 'w') as f:
        f.write(json.dumps(data, indent=2))

    # Pass path to next crew
    report_crew = ReportCrew()
    result = report_crew.crew().kickoff(inputs={
        "analysis_file": export_path  # Path, not data
    })

    return {"report_path": result.report_path}

# ❌ WRONG: Pass large data directly
def generate_report(self, data: dict[str, Any]) -> dict[str, Any]:
    report_crew = ReportCrew()
    result = report_crew.crew().kickoff(inputs={
        "analysis_data": data  # May exceed context limits
    })
```

#### 4. Concurrent Execution

**Principle**: Run independent tasks in parallel for maximum performance.

**Implementation**:

```python
import concurrent.futures

def analyze_portfolio_concurrent(holdings: list[str]) -> dict[str, Any]:
    """Analyze multiple holdings concurrently."""

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        future_to_ticker = {
            executor.submit(analyze_holding, ticker): ticker
            for ticker in holdings
        }

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                results[ticker] = future.result()
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
                results[ticker] = None

    return results
```

#### 5. Clean Separation

**Principle**: Separate analysis (AI) from presentation (templates).

**Implementation**:

```python
# Analysis (AI)
class DeepAnalysisCrew:
    @task
    def analyze_task(self) -> Task:
        return Task(
            description="Analyze {ticker}",
            output_pydantic=DeepAnalysisExport,
            agent=self.analyst()
        )

# Presentation (Python/Jinja2)
from finwiz.reporting.deep_analysis_report_generator import HTMLReportGenerator

generator = HTMLReportGenerator()
html_path = generator.generate_crew_report(
    crew_name="deep_analysis",
    export_data=analysis_result.model_dump(),
    output_path="output/reports/AAPL_report.html"
)
```

### Directory Structure Deep-Dive

```
src/finwiz/
├── crews/                          # AI Agent Crews
│   ├── stock_crew/
│   │   ├── stock_crew.py          # @agent, @task, @crew decorators
│   │   └── config/
│   │       ├── agents.yaml        # Agent definitions
│   │       └── tasks.yaml         # Task definitions
│   ├── etf_crew/
│   ├── crypto_crew/
│   ├── deep_analysis/             # Per-holding deep analysis
│   ├── investment_discovery_crew/ # A+ opportunity discovery
│   └── portfolio_rebalancing_crew/
│
├── flows/                          # CrewAI Flow Orchestration
│   └── flow_orchestrator.py       # Main workflow coordination
│
├── orchestrators/                  # Business Logic Coordination
│   ├── portfolio_review.py        # Portfolio analysis orchestration
│   ├── rebalancing_*.py           # Rebalancing logic components
│   └── review_decisions.py        # Decision aggregation
│
├── quantitative/                   # Quantitative Analysis
│   ├── technical/                 # Technical analysis (modular)
│   │   ├── technical_indicators.py
│   │   ├── technical_models.py
│   │   ├── basic_indicators.py
│   │   ├── advanced_indicators.py
│   │   └── engine.py
│   ├── backtesting.py             # Backtrader integration
│   ├── optimization.py            # Portfolio optimization
│   ├── derivatives.py             # QuantLib derivatives
│   ├── screening.py               # Stock screening
│   └── portfolio_*.py             # Portfolio management
│
├── integration/                    # Data Integration
│   ├── data_accessor.py           # Core data access (Yahoo, Alpha Vantage)
│   ├── data_validation.py         # Validation logic
│   ├── data_cache.py              # Caching layer
│   └── data_transformation.py     # Data transformation
│
├── tools/                          # Custom Financial Tools
│   ├── tool_factories.py          # Centralized tool initialization
│   ├── quantitative_analysis_tool.py
│   ├── enhanced_sentiment_tool.py
│   └── scoring/                   # Python scoring engines
│
├── schemas/                        # Pydantic Data Models
│   ├── crew_exports.py            # Export schemas per crew
│   ├── quantitative/              # Quantitative models
│   │   ├── config_models.py
│   │   └── analysis_models.py
│   └── portfolio/                 # Portfolio models
│
├── scoring/                        # Deterministic Scoring
│   ├── deep_analysis_scorer.py    # Deep analysis scoring
│   └── portfolio_scorer.py        # Portfolio-level scoring
│
├── reporting/                      # Report Generation
│   ├── deep_analysis_report_generator.py
│   └── portfolio_report_generator.py
│
├── templates/                      # Jinja2 Templates
│   ├── crew_reports/              # Crew-specific templates
│   │   ├── base.html
│   │   └── deep_analysis_report.html.j2
│   └── static/                    # CSS, JavaScript
│
├── utils/                          # Utilities
│   ├── agent_validators.py        # @final_reporter decorator
│   ├── task_decorators.py         # @async_task, @sync_task
│   ├── logging_helpers.py         # CrewLogger
│   └── feature_flags.py           # Feature flag management
│
└── validation/                     # Validation Infrastructure
    ├── schema_registry.py         # Central schema registry
    └── validation_manager.py      # Validation orchestration
```

## Development Setup

### Prerequisites

- **Python 3.12** (3.13 not supported)
- **uv** package manager (recommended) or **pip**
- **Git** for version control
- **Make** for build automation

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/finwiz.git
cd finwiz

# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Install development dependencies
uv sync --all-groups

# Set up pre-commit hooks
uv run pre-commit install
```

### Configuration

Create `.env` file:

```bash
# Copy example
cp .env.example .env

# Add your API keys
OPENAI_API_KEY=sk-your-key
SERPER_API_KEY=your-key

# Development settings
LOG_LEVEL=DEBUG
VALIDATION_STRICTNESS=warn
CACHE_BACKEND=hybrid
```

### Verify Setup

```bash
# Run tests
make test

# Type checking
make mypy

# Linting
make lint

# Full quality check
make check
```

## Code Organization

### Crew Structure

Every crew follows this standardized structure:

```
crews/{crew_name}/
├── {crew_name}.py              # Main crew implementation
└── config/
    ├── agents.yaml             # Agent configurations
    └── tasks.yaml              # Task definitions
```

#### Example: Stock Crew

**File**: `src/finwiz/crews/stock_crew/stock_crew.py`

```python
from crewai import Agent, Crew, Task, agent, crew, task
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.task_decorators import async_task, sync_task
from finwiz.utils.logging_helpers import CrewLogger

class StockCrew:
    """Stock analysis crew."""

    def __init__(self):
        self.logger = CrewLogger("StockCrew")

    @agent
    def analyst(self) -> Agent:
        """Financial analyst with quantitative tools."""
        return Agent(
            config=self.agents_config["analyst"],
            tools=get_stock_crew_tools(
                include_rag=True,
                include_quantitative=True
            ),
            reasoning=True,
            max_reasoning_attempts=3,
            allow_delegation=False,
            max_rpm=20,
            verbose=True
        )

    @final_reporter  # Enforces empty tools
    @agent
    def reporter(self) -> Agent:
        """Final report generator."""
        return Agent(
            config=self.agents_config["reporter"],
            tools=[],  # MUST be empty
            reasoning=False,
            verbose=True
        )

    @async_task
    @task
    def research_task(self) -> Task:
        """Research task with async execution."""
        return Task(
            config=self.tasks_config["research"],
            agent=self.analyst()
        )

    @sync_task  # Final task MUST be sync
    @task
    def report_task(self) -> Task:
        """Generate final report."""
        return Task(
            config=self.tasks_config["report"],
            output_pydantic=StockAnalysisExport,
            output_json=True,
            agent=self.reporter()
        )

    @crew
    def crew(self) -> Crew:
        """Create crew with configured agents and tasks."""
        return Crew(
            agents=[self.analyst(), self.reporter()],
            tasks=[self.research_task(), self.report_task()],
            process=Process.sequential,
            verbose=True
        )
```

**File**: `src/finwiz/crews/stock_crew/config/agents.yaml`

```yaml
analyst:
  role: "Stock Market Research Analyst"
  goal: "Conduct comprehensive analysis of {ticker} to provide investment recommendations"
  backstory: |
    You are a senior equity research analyst with 20+ years of experience analyzing
    publicly traded companies. You excel at fundamental analysis, technical analysis,
    and synthesizing multiple data sources into actionable insights.

reporter:
  role: "Investment Report Writer"
  goal: "Create clear, structured investment reports from analysis"
  backstory: |
    You are an expert at distilling complex financial analysis into clear,
    actionable investment reports. You ensure consistency and completeness
    while maintaining professional standards.
```

**File**: `src/finwiz/crews/stock_crew/config/tasks.yaml`

```yaml
research:
  description: |
    Perform comprehensive analysis of {ticker} ({asset_class}).

    Required Analysis:
    1. Fundamental Analysis:
       - Financial metrics (P/E, ROE, debt ratios)
       - Revenue and earnings trends
       - Competitive positioning

    2. Technical Analysis:
       - Price trends and patterns
       - Key technical indicators
       - Support/resistance levels

    3. Risk Assessment:
       - Volatility analysis
       - Sector and market risks
       - Company-specific risks

  expected_output: |
    Comprehensive analysis with:
    - Fundamental metrics and interpretation
    - Technical analysis findings
    - Risk assessment (1-10 scale)
    - Investment thesis

  agent: analyst
  async_execution: true

report:
  description: |
    Generate final investment report for {ticker}.

    Consolidate all analysis into structured output:
    - Grade (A+ to F)
    - Composite score (0.0-1.0)
    - Clear recommendation (BUY/HOLD/SELL)
    - Supporting rationale

  expected_output: |
    Structured report with:
    - Executive summary
    - Detailed findings
    - Clear recommendation
    - Risk disclosure

  output_pydantic: "StockAnalysisExport"
  output_json: true
  agent: reporter
  async_execution: false  # Final task must be sync
```

### Flow Architecture

FinWiz uses CrewAI Flow for orchestration with Pydantic state management.

#### Flow Implementation

**File**: `src/finwiz/flows/flow_orchestrator.py`

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field
from typing import Any

class FinwizState(BaseModel):
    """Type-safe flow state."""

    session_id: str = Field(default="")
    portfolio_review: dict[str, Any] = Field(default_factory=dict)
    deep_analysis_results: dict[str, Any] = Field(default_factory=dict)
    rebalancing_recommendations: dict[str, Any] = Field(default_factory=dict)

class FinwizFlow(Flow[FinwizState]):
    """Main FinWiz orchestration flow."""

    @start()
    def initialize(self) -> dict[str, Any]:
        """Initialize flow with session setup."""
        import uuid

        session_id = str(uuid.uuid4())
        self.state.session_id = session_id

        logger.info(f"Flow initialized: {session_id}")

        return {"session_id": session_id, "status": "initialized"}

    @listen(initialize)
    def analyze_portfolio(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze portfolio holdings."""
        from finwiz.orchestrators.portfolio_review import PortfolioReviewOrchestrator

        orchestrator = PortfolioReviewOrchestrator()

        # Run portfolio analysis
        results = orchestrator.run_portfolio_review(
            stock_csv="data/stock.csv",
            etf_csv="data/etf.csv",
            session_id=self.state.session_id
        )

        # Update state
        self.state.portfolio_review = results.model_dump()

        return {
            "holdings_analyzed": len(results.holdings),
            "recommendations": results.summary
        }

    @listen(analyze_portfolio)
    def generate_alternatives(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate alternatives for SELL recommendations."""
        from finwiz.orchestrators.portfolio_review import generate_alternatives

        sell_holdings = [
            h for h in self.state.portfolio_review["holdings"]
            if h["recommendation"] == "SELL"
        ]

        alternatives = generate_alternatives(
            sell_holdings,
            session_id=self.state.session_id
        )

        return {"alternatives": alternatives}

    @listen(generate_alternatives)
    def create_final_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive final report."""
        from finwiz.reporting.portfolio_report_generator import PortfolioReportGenerator

        generator = PortfolioReportGenerator()

        report_path = generator.generate_report(
            portfolio_data=self.state.portfolio_review,
            alternatives=data["alternatives"],
            session_id=self.state.session_id
        )

        return {
            "report_path": report_path,
            "status": "complete"
        }
```

**CRITICAL Flow Rules**:

1. ✅ Use `Flow[PydanticModel]` for type safety
2. ✅ All Flow methods return `dict[str, Any]`
3. ✅ Access state via `self.state.field_name`
4. ✅ Direct crew instantiation (not factory patterns)
5. ❌ NEVER use `self.inputs` (deprecated)

### Tool Factories Pattern

Centralized tool initialization eliminates code duplication.

**File**: `src/finwiz/tools/tool_factories.py`

```python
from typing import List
from crewai_tools import Tool

def get_stock_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = True,
    collection_suffix: str = "stock"
) -> List[Tool]:
    """Get standardized tool set for stock analysis."""

    tools = []

    # Core tools (always included)
    from finwiz.tools.data_fetcher import DataFetcherTool

    tools.extend([
        DataFetcherTool(),
    ])

    # Optional RAG integration
    if include_rag:
        from finwiz.tools.rag_search import RAGSearchTool
        tools.append(RAGSearchTool(collection_name=f"finwiz_{collection_suffix}"))

    # Optional quantitative analysis
    if include_quantitative:
        from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool
        tools.append(QuantitativeAnalysisTool())

    return tools

def get_etf_crew_tools(
    include_rag: bool = True,
    include_quantitative: bool = False
) -> List[Tool]:
    """Get standardized tool set for ETF analysis."""

    tools = []

    from finwiz.tools.data_fetcher import DataFetcherTool
    from finwiz.tools.etf_analyzer import ETFAnalyzerTool

    tools.extend([
        DataFetcherTool(),
        ETFAnalyzerTool()
    ])

    if include_rag:
        from finwiz.tools.rag_search import RAGSearchTool
        tools.append(RAGSearchTool(collection_name="finwiz_etf"))

    return tools
```

## Core Patterns

### 1. Final Reporter Pattern

Final reporters MUST have empty tools and only consume upstream context.

```python
from finwiz.utils.agent_validators import final_reporter

@final_reporter  # Enforces NO tools
@agent
def reporter(self) -> Agent:
    return Agent(
        config=self.agents_config["reporter"],
        tools=[],  # Required
        reasoning=False,
        verbose=True
    )

# The decorator will raise an error if tools are provided:
# ValidationError: Final reporter must have empty tools list
```

### 2. Task Execution Pattern

Use decorators to make async/sync execution explicit.

```python
from finwiz.utils.task_decorators import async_task, sync_task

@async_task
@task
def research_task(self) -> Task:
    """Research can run asynchronously."""
    return Task(
        config=self.tasks_config["research"],
        agent=self.researcher()
    )

@sync_task  # Final task MUST be sync
@task
def final_report_task(self) -> Task:
    """Final task must be synchronous."""
    return Task(
        config=self.tasks_config["final_report"],
        agent=self.reporter()
    )
```

### 3. Structured Logging

Use `CrewLogger` for consistent logging across crews.

```python
from finwiz.utils.logging_helpers import CrewLogger
import time

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

All crew outputs use Pydantic schemas for validation.

**File**: `src/finwiz/schemas/crew_exports.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class DeepAnalysisExport(BaseModel):
    """Deep analysis export schema."""

    ticker: str = Field(..., description="Ticker symbol")
    asset_class: Literal["stock", "etf", "crypto"] = Field(...)
    grade: str = Field(..., pattern="^[A-F][+-]?$")
    composite_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: Literal["BUY", "HOLD", "SELL"] = Field(...)

    fundamental_score: float = Field(..., ge=0.0, le=1.0)
    technical_score: float = Field(..., ge=0.0, le=1.0)
    sentiment_score: float = Field(..., ge=0.0, le=1.0)

    risk_level: int = Field(..., ge=1, le=10)
    confidence: float = Field(..., ge=0.0, le=1.0)

    reasoning: str = Field(..., min_length=50)

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or len(v) > 10:
            raise ValueError("Invalid ticker symbol")
        return v.upper()

# Use in crew
@task
def analysis_task(self) -> Task:
    return Task(
        description="Analyze ticker",
        output_pydantic=DeepAnalysisExport,
        agent=self.analyst()
    )

# Save to file
export = DeepAnalysisExport(...)
export_path = f"output/reports/{session_id}/analysis.json"
with open(export_path, 'w') as f:
    f.write(export.model_dump_json(indent=2))
```

### 5. HTML Report Generation

Use Jinja2 templates (NO AI) for report generation.

**File**: `src/finwiz/reporting/deep_analysis_report_generator.py`

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class HTMLReportGenerator:
    """Generate HTML reports from analysis data."""

    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates" / "crew_reports"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def generate_crew_report(
        self,
        crew_name: str,
        export_data: dict,
        output_path: str
    ) -> str:
        """Generate HTML report for crew analysis."""

        # Load template
        template = self.env.get_template(f"{crew_name}_report.html.j2")

        # Render with data
        html_content = template.render(
            ticker=export_data["ticker"],
            grade=export_data["grade"],
            score=export_data["composite_score"],
            recommendation=export_data["recommendation"],
            **export_data
        )

        # Write to file
        with open(output_path, 'w') as f:
            f.write(html_content)

        return output_path
```

**Template**: `src/finwiz/templates/crew_reports/deep_analysis_report.html.j2`

{% raw %}

```html
{% extends "base.html" %}

{% block title %}{{ ticker }} - Deep Analysis Report{% endblock %}

{% block content %}
<div class="report-header">
    <h1>{{ ticker }} Analysis</h1>
    <div class="grade-badge grade-{{ grade[0] }}">
        {{ grade }}
    </div>
</div>

<div class="metrics">
    <div class="metric">
        <span class="label">Composite Score:</span>
        <span class="value">{{ "%.2f"|format(score) }}</span>
    </div>
    <div class="metric">
        <span class="label">Recommendation:</span>
        <span class="value rec-{{ recommendation|lower }}">
            {{ recommendation }}
        </span>
    </div>
    <div class="metric">
        <span class="label">Risk Level:</span>
        <span class="value">{{ risk_level }}/10</span>
    </div>
</div>

<div class="analysis-section">
    <h2>Investment Thesis</h2>
    <p>{{ reasoning }}</p>
</div>

<div class="scores">
    <div class="score-card">
        <h3>Fundamental</h3>
        <div class="score">{{ "%.2f"|format(fundamental_score) }}</div>
    </div>
    <div class="score-card">
        <h3>Technical</h3>
        <div class="score">{{ "%.2f"|format(technical_score) }}</div>
    </div>
    <div class="score-card">
        <h3>Sentiment</h3>
        <div class="score">{{ "%.2f"|format(sentiment_score) }}</div>
    </div>
</div>
{% endblock %}
```

{% endraw %}

## Creating Custom Crews

### Step-by-Step Guide

#### 1. Create Crew Directory

```bash
mkdir -p src/finwiz/crews/my_custom_crew/config
```

#### 2. Create Crew Implementation

**File**: `src/finwiz/crews/my_custom_crew/my_custom_crew.py`

```python
from crewai import Agent, Crew, Task, agent, crew, task
from finwiz.tools.tool_factories import get_stock_crew_tools
from finwiz.utils.agent_validators import final_reporter
from finwiz.utils.task_decorators import async_task, sync_task
from finwiz.utils.logging_helpers import CrewLogger

class MyCustomCrew:
    """Custom crew for specific analysis."""

    def __init__(self):
        self.logger = CrewLogger("MyCustomCrew")
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()

    def _load_agents_config(self) -> dict:
        """Load agents configuration from YAML."""
        import yaml
        from pathlib import Path

        config_path = Path(__file__).parent / "config" / "agents.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_tasks_config(self) -> dict:
        """Load tasks configuration from YAML."""
        import yaml
        from pathlib import Path

        config_path = Path(__file__).parent / "config" / "tasks.yaml"
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @agent
    def analyst(self) -> Agent:
        """Primary analyst agent."""
        return Agent(
            config=self.agents_config["analyst"],
            tools=get_stock_crew_tools(include_rag=True),
            reasoning=True,
            max_reasoning_attempts=3,
            allow_delegation=False,
            max_rpm=20,
            verbose=True
        )

    @final_reporter
    @agent
    def reporter(self) -> Agent:
        """Final report generator."""
        return Agent(
            config=self.agents_config["reporter"],
            tools=[],
            reasoning=False,
            verbose=True
        )

    @async_task
    @task
    def analysis_task(self) -> Task:
        """Main analysis task."""
        return Task(
            config=self.tasks_config["analysis"],
            agent=self.analyst()
        )

    @sync_task
    @task
    def report_task(self) -> Task:
        """Generate final report."""
        return Task(
            config=self.tasks_config["report"],
            output_pydantic=MyCustomExport,
            output_json=True,
            agent=self.reporter()
        )

    @crew
    def crew(self) -> Crew:
        """Create crew with configured agents and tasks."""
        return Crew(
            agents=[self.analyst(), self.reporter()],
            tasks=[self.analysis_task(), self.report_task()],
            process=Process.sequential,
            verbose=True
        )
```

#### 3. Create Agent Configuration

**File**: `src/finwiz/crews/my_custom_crew/config/agents.yaml`

```yaml
analyst:
  role: "Custom Analysis Specialist"
  goal: "Perform specialized analysis of {ticker}"
  backstory: |
    You are an expert in custom financial analysis with deep domain knowledge.

reporter:
  role: "Report Generator"
  goal: "Create structured reports from analysis"
  backstory: |
    You excel at creating clear, actionable reports from complex analysis.
```

#### 4. Create Task Configuration

**File**: `src/finwiz/crews/my_custom_crew/config/tasks.yaml`

```yaml
analysis:
  description: |
    Perform custom analysis of {ticker}.

    Analysis Requirements:
    1. Custom metric calculation
    2. Specialized data collection
    3. Domain-specific evaluation

  expected_output: |
    Comprehensive analysis with:
    - Custom metrics
    - Specialized findings
    - Actionable insights

  agent: analyst
  async_execution: true

report:
  description: |
    Generate final report for {ticker}.

    Create structured output with all findings.

  expected_output: "Structured report with recommendations"
  output_pydantic: "MyCustomExport"
  output_json: true
  agent: reporter
  async_execution: false
```

#### 5. Create Export Schema

**File**: `src/finwiz/schemas/crew_exports.py` (add to existing)

```python
class MyCustomExport(BaseModel):
    """Custom crew export schema."""

    ticker: str = Field(..., description="Ticker symbol")
    custom_metric: float = Field(..., ge=0.0, le=1.0)
    recommendation: str = Field(...)
    reasoning: str = Field(..., min_length=50)
```

#### 6. Add Tests

**File**: `tests/unit/crews/test_my_custom_crew.py`

```python
import pytest
from finwiz.crews.my_custom_crew.my_custom_crew import MyCustomCrew
from finwiz.schemas.crew_exports import MyCustomExport

def test_crew_initialization():
    """Test crew initializes correctly."""
    crew = MyCustomCrew()
    assert crew is not None
    assert crew.logger is not None

def test_agents_configuration(mocker):
    """Test agents are configured correctly."""
    crew = MyCustomCrew()

    analyst = crew.analyst()
    assert analyst is not None
    assert len(analyst.tools) > 0
    assert analyst.reasoning is True

    reporter = crew.reporter()
    assert reporter is not None
    assert len(reporter.tools) == 0  # Final reporter has no tools

@pytest.mark.integration
def test_crew_execution(mocker):
    """Test crew executes successfully."""
    # Mock expensive operations
    mocker.patch('finwiz.tools.data_fetcher.DataFetcherTool._run')

    crew = MyCustomCrew()

    result = crew.crew().kickoff(inputs={
        "ticker": "TEST",
        "asset_class": "stock"
    })

    # Validate result
    assert result is not None
    export = MyCustomExport(**result.model_dump())
    assert export.ticker == "TEST"
```

#### 7. Integrate with Flow

**File**: `src/finwiz/flows/flow_orchestrator.py` (modify)

```python
@listen(some_trigger)
def run_custom_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
    """Run custom analysis crew."""
    from finwiz.crews.my_custom_crew.my_custom_crew import MyCustomCrew

    crew = MyCustomCrew()
    result = crew.crew().kickoff(inputs={
        "ticker": data["ticker"],
        "asset_class": "stock"
    })

    return {"custom_analysis": result.model_dump()}
```

## Testing

### Test Infrastructure

FinWiz uses **pytest** with **pytest-mock** for all testing.

**CRITICAL**: NEVER use `unittest.mock`. Always use `pytest-mock`.

```python
# ❌ WRONG: unittest.mock
from unittest.mock import Mock, patch

def test_example():
    with patch('module.function') as mock_fn:
        ...

# ✅ CORRECT: pytest-mock
def test_example(mocker):
    mock_fn = mocker.patch('module.function')
    ...
```

### Test Organization

```
tests/
├── unit/                          # Unit tests (< 3 minutes)
│   ├── crews/                     # Crew tests
│   │   ├── test_stock_crew.py
│   │   └── test_deep_analysis.py
│   ├── tools/                     # Tool tests
│   │   ├── test_quantitative_analysis_tool.py
│   │   └── test_sentiment_tool.py
│   ├── scoring/                   # Scoring engine tests
│   │   └── test_deep_analysis_scorer.py
│   └── utils/                     # Utility tests
│       └── test_logging_helpers.py
│
├── integration/                   # Integration tests (requires API keys)
│   ├── test_portfolio_review.py
│   └── test_data_integration.py
│
├── performance/                   # Performance tests
│   └── test_batch_processing.py
│
└── conftest.py                    # Shared fixtures
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    """Fast unit test."""
    pass

@pytest.mark.integration
def test_integration_example():
    """Integration test requiring API keys."""
    pass

@pytest.mark.slow
def test_slow_example():
    """Slow-running test."""
    pass

@pytest.mark.performance
def test_performance_example():
    """Performance benchmark."""
    pass
```

Run specific test categories:

```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

@pytest.fixture
def scorer():
    """Provide scorer instance."""
    return DeepAnalysisScorer()

@pytest.fixture
def stock_data():
    """Provide sample stock data."""
    return {
        "roe": 0.25,
        "debt_to_equity": 0.3,
        "revenue_growth": 0.15,
        "profit_margin": 0.22,
        "pe_ratio": 28.5,
        "current_ratio": 1.1
    }

def test_calculate_composite_score(scorer, stock_data):
    """Test composite score calculation."""
    result = scorer.calculate_composite_score(
        ticker="AAPL",
        asset_class="stock",
        data=stock_data
    )

    assert result.grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]
    assert 0.0 <= result.composite_score <= 1.0
    assert result.recommendation in ["BUY", "HOLD", "SELL"]

def test_invalid_asset_class(scorer, stock_data):
    """Test handling of invalid asset class."""
    with pytest.raises(ValueError, match="Invalid asset_class"):
        scorer.calculate_composite_score(
            ticker="AAPL",
            asset_class="invalid",
            data=stock_data
        )

@pytest.mark.parametrize("score,expected_grade", [
    (0.98, "A+"),
    (0.88, "A"),
    (0.78, "B+"),
    (0.68, "B"),
    (0.58, "C+"),
    (0.48, "C"),
    (0.38, "D"),
    (0.28, "F"),
])
def test_grade_mapping(scorer, score, expected_grade):
    """Test score to grade conversion."""
    grade = scorer._score_to_grade(score)
    assert grade == expected_grade
```

#### Mocking External Dependencies

```python
import pytest
from finwiz.integration.data_accessor import DataAccessor

def test_fetch_stock_data(mocker):
    """Test stock data fetching with mocked API."""
    # Mock yfinance
    mock_ticker = mocker.Mock()
    mock_ticker.info = {
        "symbol": "AAPL",
        "currentPrice": 175.50,
        "marketCap": 2_800_000_000_000
    }

    mocker.patch('yfinance.Ticker', return_value=mock_ticker)

    # Test data accessor
    accessor = DataAccessor()
    data = accessor.fetch_stock_data("AAPL")

    assert data["symbol"] == "AAPL"
    assert data["currentPrice"] == 175.50

def test_api_error_handling(mocker):
    """Test handling of API errors."""
    # Mock API failure
    mocker.patch(
        'yfinance.Ticker',
        side_effect=Exception("API Error")
    )

    accessor = DataAccessor()

    with pytest.raises(Exception, match="API Error"):
        accessor.fetch_stock_data("INVALID")
```

#### Testing Crews

```python
import pytest
from finwiz.crews.stock_crew.stock_crew import StockCrew
from finwiz.schemas.crew_exports import StockAnalysisExport

def test_stock_crew_initialization():
    """Test stock crew initializes correctly."""
    crew = StockCrew()

    assert crew is not None
    assert crew.logger is not None
    assert crew.agents_config is not None
    assert crew.tasks_config is not None

def test_agents_have_correct_tools(mocker):
    """Test agents are configured with correct tools."""
    crew = StockCrew()

    analyst = crew.analyst()
    assert len(analyst.tools) > 0
    assert analyst.reasoning is True

    reporter = crew.reporter()
    assert len(reporter.tools) == 0  # Final reporter has no tools

@pytest.mark.integration
def test_crew_execution_full(mocker):
    """Test full crew execution (integration test)."""
    # Mock expensive API calls
    mocker.patch('finwiz.tools.data_fetcher.DataFetcherTool._run')
    mocker.patch('finwiz.tools.quantitative_analysis_tool.QuantitativeAnalysisTool._run')

    crew = StockCrew()

    result = crew.crew().kickoff(inputs={
        "ticker": "AAPL",
        "asset_class": "stock"
    })

    # Validate result structure
    assert result is not None

    # Validate export schema
    export = StockAnalysisExport(**result.model_dump())
    assert export.ticker == "AAPL"
    assert export.asset_class == "stock"
    assert 0.0 <= export.composite_score <= 1.0
```

### Test Coverage

```bash
# Run tests with coverage
make coverage

# Generate HTML coverage report
pytest --cov=src/finwiz --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Coverage Standards**:

- Minimum: 65% (enforced)
- Target: 80%
- Critical paths: 90%+

## Performance Optimization

### Performance Optimization Rules

#### Reasoning (`reasoning=True`)

**When to Enable**:

- Complex analysis requiring multi-step thinking
- Decision-making with multiple factors
- Creative synthesis of information

**When to Disable**:

- Validators and reporters
- High-volume executions (66+ runs)
- Simple data transformation

**Cost**: 5-15 seconds, 1-3 LLM calls per execution

```python
# ✅ GOOD: Complex analysis
@agent
def analyst(self) -> Agent:
    return Agent(
        reasoning=True,  # Complex multi-step analysis
        max_reasoning_attempts=3
    )

# ❌ BAD: High-volume execution
@agent
def validator(self) -> Agent:
    return Agent(
        reasoning=True,  # Will execute 66+ times - too slow
        max_reasoning_attempts=3
    )
```

#### Planning (`planning=True`)

**When to Enable**:

- 4+ agents AND 6+ tasks AND ≤3 runs
- Complex workflows with dependencies
- Strategic planning required

**When to Disable**:

- High-volume executions
- Single-agent crews
- Simple sequential workflows

**Example**:

```python
# ✅ GOOD: Complex workflow, single run
@crew
def crew(self) -> Crew:
    return Crew(
        agents=[self.analyst(), self.researcher(), self.validator(), self.reporter()],
        tasks=[...],  # 6+ tasks
        planning=True,  # Complex, runs once
        process=Process.sequential
    )

# ❌ BAD: High-volume execution
@crew
def crew(self) -> Crew:
    return Crew(
        agents=[self.analyst()],
        tasks=[self.analyze()],
        planning=True,  # Will run 66 times - unnecessary overhead
        process=Process.sequential
    )
```

#### Delegation (`allow_delegation=True`)

**When to Enable**:

- Coordinator agents managing workflow
- Dynamic task distribution needed

**When to Disable**:

- Specialist agents (focused role)
- Reporter agents
- High-volume executions

**Cost**: 5-15 seconds per delegation

```python
# ✅ GOOD: Coordinator agent
@agent
def coordinator(self) -> Agent:
    return Agent(
        allow_delegation=True,  # Manages other agents
        max_rpm=10
    )

# ❌ BAD: Specialist agent
@agent
def analyst(self) -> Agent:
    return Agent(
        allow_delegation=True,  # Specialist shouldn't delegate
        max_rpm=20
    )
```

### Batch Processing Optimization

For portfolios with 10+ holdings, use batch processing:

**Configuration**:

```bash
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5  # Adjust based on CPU/memory
BATCH_PREFETCH_MIN_HOLDINGS=10
ENABLE_ALPHA_VANTAGE=false  # Yahoo Finance faster for batch
```

**Performance Gains**:

- 66 holdings: 5.5-11 hours → 20-40 minutes (10-20x speedup)
- Data pre-fetch: 2-5 seconds (Yahoo Finance)
- Concurrent execution: 5 crews in parallel

### Caching Strategy

```bash
# Optimal caching configuration
CACHE_BACKEND=hybrid        # Memory + file
CACHE_TTL=2700             # 45 minutes
CACHE_STRATEGY=adaptive    # Adapts to usage patterns
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100
```

### Python Scoring Engine

Replace AI-based calculations with deterministic Python:

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()
result = scorer.calculate_composite_score(ticker, asset_class, data)

# Performance: 10-20x faster than AI
# Cost: 100% reduction (zero LLM calls)
# Consistency: Same input = same output
```

## Contributing

### Code Style

FinWiz uses **Ruff** for linting and formatting:

```bash
# Format code
make format

# Check linting
make lint

# Fix linting issues
ruff check --fix src/
```

### Type Hints

All public functions must have type hints (Python 3.12+ syntax):

```python
# ✅ CORRECT: Python 3.12+ syntax
def analyze_stock(ticker: str, data: dict[str, Any]) -> dict[str, Any]:
    """Analyze stock with type hints."""
    return {"ticker": ticker}

# ❌ WRONG: Old syntax
from typing import Dict, Any, Optional

def analyze_stock(ticker: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return {"ticker": ticker}
```

### Documentation

All public modules, classes, and functions require docstrings:

```python
def calculate_composite_score(
    ticker: str,
    asset_class: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    """Calculate composite score for asset.

    Args:
        ticker: Asset ticker symbol (e.g., "AAPL")
        asset_class: Type of asset ("stock", "etf", "crypto")
        data: Financial metrics dictionary

    Returns:
        Dictionary containing:
            - grade: Letter grade (A+ to F)
            - composite_score: Numeric score (0.0-1.0)
            - recommendation: Investment action (BUY/HOLD/SELL)
            - reasoning: Explanation of score

    Raises:
        ValueError: If asset_class is invalid
        KeyError: If required metrics missing from data

    Example:
        >>> scorer = DeepAnalysisScorer()
        >>> result = scorer.calculate_composite_score(
        ...     "AAPL", "stock", {"roe": 0.25, "debt_to_equity": 0.3}
        ... )
        >>> print(result["grade"])
        A
    """
    ...
```

### Pull Request Process

1. **Create Feature Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Write code following style guide
   - Add tests for new functionality
   - Update documentation

3. **Run Quality Checks**:

   ```bash
   make check  # Runs lint, mypy, tests
   ```

4. **Commit Changes**:

   ```bash
   git add .
   git commit -m "feat: add new feature - @documentation-specialist"
   ```

5. **Push and Create PR**:

   ```bash
   git push origin feature/your-feature-name
   gh pr create --title "Add new feature" --body "Description"
   ```

6. **Code Review**:
   - Address reviewer comments
   - Ensure CI passes
   - Update documentation if needed

### Commit Attribution

**CRITICAL**: All commits MUST include contributing agents:

```bash
# Format
type(scope): description - @agent1 @agent2

# Examples
feat(auth): implement authentication - @documentation-specialist @security-specialist
docs(api): update API documentation - @documentation-specialist
config(setup): configure project settings - @documentation-specialist @infrastructure-expert
```

## Deployment

### Production Deployment

#### Docker Deployment

**Dockerfile**:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY . /app

# Install dependencies
RUN uv sync

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Run application
CMD ["uv", "run", "crewai", "flow", "kickoff"]
```

**Build and Run**:

```bash
# Build image
docker build -t finwiz:latest .

# Run container
docker run -d \
  --name finwiz \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e SERPER_API_KEY=$SERPER_API_KEY \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/output:/app/output \
  finwiz:latest
```

#### Environment Configuration

**Production `.env`**:

```bash
# API Keys
OPENAI_API_KEY=sk-prod-key
SERPER_API_KEY=prod-key

# Validation (strict in production)
VALIDATION_STRICTNESS=error

# Performance
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
RISK_ASSESSMENT_USE_MINI=true

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Security
ENABLE_ENCRYPTION=true
SUPABASE_ENCRYPTION_KEY=your-32-char-key
```

#### Health Checks

```python
from finwiz.utils import run_health_check

# Run health check
results = run_health_check(
    check_apis=True,
    check_cache=True,
    check_data=True,
    check_validation=True
)

if not results.healthy:
    logger.error(f"Health check failed: {results.errors}")
    sys.exit(1)
```

#### Monitoring

```bash
# Monitor logs
tail -f logs/finwiz.log

# Check errors
grep -i "error" logs/finwiz_error.log

# Monitor performance
grep "duration" logs/finwiz.log | tail -n 20
```

### Continuous Integration

**GitHub Actions** (`.github/workflows/ci.yml`):

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run linting
        run: make lint

      - name: Run type checking
        run: make mypy

      - name: Run tests
        run: make test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## Additional Resources

- [Operations Guide](../how-to/OPERATIONS_GUIDE.md) - Deployment, operations, and migration
- [API Reference](../reference/API_REFERENCE.md) - API documentation
- [Architecture Overview](../explanations/ARCHITECTURE.md) - System design
- [Testing Guide](#testing) - Testing best practices

## Support

- **Documentation**: [https://fjacquet.github.io/finwiz](https://fjacquet.github.io/finwiz)
- **Issues**: [GitHub Issues](https://github.com/fjacquet/finwiz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fjacquet/finwiz/discussions)

---

*Last updated: 2025-01-18*
