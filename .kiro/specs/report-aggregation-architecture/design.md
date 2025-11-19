# Report Aggregation Architecture Design

## Overview

**🚨 CRITICAL DESIGN UPDATE BASED ON IMPLEMENTATION FAILURE ANALYSIS 🚨**

This design implements a **PURE PYTHON FIRST** architecture to fix the fundamental failures identified in the implementation analysis. The current AI-based approach has failed to deliver promised performance improvements and cost reductions.

**Key Failures Identified (Requirements 0.x):**

1. AI-based deep analysis still being used (no speed improvement) - **Requirement 0.1-0.7**
2. JSON exports only in cache, not output directory (broken integration) - **Requirement 0.8-0.12**
3. A+ discovery showing 0 opportunities (broken data flow) - **Requirement 0.13-0.17**
4. Backtesting not executing (disconnected pipeline) - **Requirement 0.18-0.21**
5. AI-generated reports instead of Python templates (inconsistent quality) - **Requirement 0.22-0.26**

The new architecture follows **PURE PYTHON FIRST** principle (Requirements 18-21): eliminate AI for all deterministic tasks and achieve 10-20x speed improvement with 100% cost reduction for calculations.

### Core Design Principles

1. **Pydantic-First**: All crew outputs validated with strict Pydantic schemas (Requirements 1, 10)
2. **Python for Determinism**: HTML generation and data consolidation use Jinja2 templates and Python functions (NO AI) (Requirements 2, 3, 18-21)
3. **File-Based Data Passing**: Pass file paths (not data) between crews to avoid context limits (Requirement 6)
4. **Concurrent Execution**: All SME crews run in parallel for maximum performance (Requirement 7, 17)
5. **Clean Break**: No backward compatibility with legacy broken patterns (Requirement 11)
6. **AI Minimalism Compliance**: Use Python for deterministic tasks, AI only for reasoning (Requirements 18.41-18.44)
7. **Performance Optimization**: Configurable modes for speed/cost/quality balance (Requirement 21)

## Architecture

### High-Level Flow (PURE PYTHON ARCHITECTURE)

```mermaid
Portfolio Input (CSV files)
    ↓
[Portfolio Review Generation] - Python function
    ↓ (portfolio_review.json)
┌─────────────────────────────────────────────────────┐
│  PURE PYTHON DEEP ANALYSIS                          │
│  ⚡ 10-20x faster, $0 cost, deterministic           │
│                                                      │
│  ┌─────────────────────────────────────────────────┐│
│  │  PortfolioDeepAnalyzer.analyze_portfolio()     ││
│  │                                                 ││
│  │  For each holding:                              ││
│  │  1. Extract data (Python)                      ││
│  │  2. DeepAnalysisScorer.calculate_score()       ││
│  │  3. Generate JSON export                       ││
│  │  4. Update holding with results                 ││
│  │                                                 ││
│  │  Concurrent processing: 5-10 holdings/batch    ││
│  │  Time: 10-30 seconds total (vs 3-6 hours AI)   ││
│  │  Cost: $0 (vs $3.30-6.60 AI)                  ││
│  └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
                      ↓
              JSON Exports Created:
              • output/stock/*.json
              • output/etf/*.json
              • output/crypto/*.json
              • output/deep_analysis_consolidated.json
                      ↓
┌─────────────────────────────────────────────────────┐
│  A+ DISCOVERY INTEGRATION                            │
│  📊 Reads JSON exports from output directory        │
│                                                      │
│  1. Scan deep analysis results                      │
│  2. Identify A+ and A grade holdings                │
│  3. Set has_a_plus_analysis = true                  │
│  4. Set total_opportunities_found = count           │
│  5. Generate discovery export                       │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  BACKTESTING PIPELINE                               │
│  🔬 Executes when A+ candidates available           │
│                                                      │
│  1. Read A+ opportunities from discovery            │
│  2. Run backtesting analysis                        │
│  3. Generate backtesting results                    │
│  4. Include in final report                         │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│  PYTHON REPORT GENERATION                           │
│  📋 Jinja2 templates, millisecond generation        │
│                                                      │
│  PythonReportGenerator.generate_report():           │
│  1. Load portfolio review                           │
│  2. Load deep analysis results                      │
│  3. Load A+ discovery results                       │
│  4. Load backtesting results                        │
│  5. Render Jinja2 template                         │
│  6. Generate final HTML report                      │
│                                                      │
│  Time: <100ms (vs 30-60 seconds AI)                │
│  Cost: $0 (vs $0.01-0.02 AI)                      │
└─────────────────────────────────────────────────────┘
                      ↓
           final_report.html (French)
           ✅ Actual data, not placeholders
           ✅ A+ opportunities shown
           ✅ Backtesting results included
           ✅ Performance metrics displayed
```

### Data Flow Architecture

```
PHASE 1: Concurrent Analysis
┌─────────────────────────────────────────────────────────────┐
│ Analysis Crews (Stock/ETF/Crypto/DeepAnalysis/Discovery)   │
│                                                             │
│  AI Analysis Tasks → Final Reporter Task                   │
│                           ↓                                 │
│                  Pydantic Export Object                     │
│                           ↓                                 │
│              {crew_name}_export.json                        │
│                           ↓                                 │
│         Python Template Function (Jinja2)                   │
│                           ↓                                 │
│              {crew_name}_report.html                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
PHASE 2: Rebalancing (Sees ALL Options)
┌─────────────────────────────────────────────────────────────┐
│ Portfolio Rebalancing Crew                                  │
│                                                             │
│  Input: File paths to ALL analysis exports                 │
│  - stock_crew exports (current holdings)                   │
│  - etf_crew exports (current holdings)                     │
│  - crypto_crew exports (current holdings)                  │
│  - deep_analysis exports (detailed grades)                 │
│  - discovery_crew export (A+ opportunities)                │
│                           ↓                                 │
│  AI Rebalancing Analysis (sees complete picture)           │
│                           ↓                                 │
│              rebalancing_export.json                        │
│                           ↓                                 │
│         Python Template Function (Jinja2)                   │
│                           ↓                                 │
│              rebalancing_report.html                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
PHASE 3: Consolidation
┌─────────────────────────────────────────────────────────────┐
│ Python Consolidation Function (NO AI)                      │
│                                                             │
│  Read all {crew_name}_export.json files                    │
│  (including rebalancing_export.json)                        │
│           ↓                                                 │
│  Validate against Pydantic schemas                          │
│           ↓                                                 │
│  Create ConsolidatedReportExport                            │
│           ↓                                                 │
│  Save consolidated_report.json                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
PHASE 4: Final Report
┌─────────────────────────────────────────────────────────────┐
│ Python Final Report Generator (NO AI)                      │
│                                                             │
│  Read consolidated_report.json                              │
│           ↓                                                 │
│  Render Jinja2 template (French)                            │
│           ↓                                                 │
│  Save final_report.html                                     │
└─────────────────────────────────────────────────────────────┘
```

## Design Rationale

### Why Rebalancing Must Run After All Analysis

**Critical Design Decision**: The rebalancing crew MUST execute AFTER all analysis crews complete (Phase 2), not concurrently with them (Phase 1).

**Rationale**:

1. **Complete Information Required**: Rebalancing decisions require seeing ALL available options:

   - **Current holdings** (Stock/ETF/Crypto crew exports) - What do we own today?
   - **Deep analysis results** (DeepAnalysisCrew exports) - Detailed grades for underperforming holdings
   - **Discovery opportunities** (DiscoveryCrew export) - What A+ alternatives exist?

2. **Optimization Problem**: Portfolio rebalancing is an optimization problem that requires:

   - Current allocation (from holdings analysis)
   - Quality assessment of each holding (from deep analysis)
   - Available alternatives (from discovery)
   - Risk/return tradeoffs across ALL options

3. **Sequential Dependency**: Rebalancing cannot make informed decisions without:

   - Knowing which holdings are underperforming (requires analysis completion)
   - Knowing what A+ opportunities exist (requires discovery completion)
   - Having detailed grades for problematic holdings (requires deep analysis completion)

4. **Example Scenario**:

   ```
   Current Portfolio:
   - AAPL (Stock) - Grade B (from StockCrew)
   - IBM (Stock) - Grade D (from StockCrew)

   Deep Analysis:
   - IBM detailed analysis (from DeepAnalysisCrew) - Grade D confirmed, sell recommended

   Discovery:
   - MSFT (Stock) - Grade A+ opportunity (from DiscoveryCrew)
   - NVDA (Stock) - Grade A+ opportunity (from DiscoveryCrew)

   Rebalancing Decision (requires ALL above):
   - Keep AAPL (Grade B is acceptable)
   - Sell IBM (Grade D confirmed by deep analysis)
   - Buy MSFT or NVDA (A+ alternatives from discovery)
   - Optimize allocation across AAPL + new A+ holding
   ```

5. **Flow Architecture**:

   ```
   Phase 1 (Parallel):
   - Stock/ETF/Crypto crews analyze current holdings
   - DeepAnalysis crew analyzes underperformers
   - Discovery crew finds A+ opportunities

   Phase 2 (Sequential - AFTER Phase 1):
   - Rebalancing crew receives ALL Phase 1 results
   - Makes informed optimization decisions
   - Proposes trades and target allocation
   ```

**Implementation**: The Flow uses `@listen(and_(...))` to ensure rebalancing waits for ALL Phase 1 crews to complete before executing.

### Phase 1 Dependencies Explained

**Phase 1a: Holdings Analysis (Parallel, No Dependencies)**

- Stock/ETF/Crypto crews run concurrently
- Each analyzes current holdings independently
- No dependencies on each other

**Phase 1b: Context-Dependent Analysis (Parallel, Depends on Phase 1a)**

- **DeepAnalysis Crew**: Depends on holdings analysis to identify which assets need deep analysis (grade < B)
  - Reads stock/etf/crypto exports to find underperformers
  - Then performs detailed analysis on those specific tickers
- **Discovery Crew**: Depends on holdings analysis to understand portfolio context
  - Reads current holdings to understand what you already own
  - Finds A+ opportunities that complement (not duplicate) current holdings
  - Considers sector/asset class diversification

**Why These Dependencies Matter**:

1. DeepAnalysis shouldn't analyze everything - only underperformers identified by holdings analysis
2. Discovery should find complementary opportunities, not duplicates of what you already own
3. Both crews run in parallel once holdings analysis completes (Phase 1b)

**Flow Execution**:

```python
# Phase 1a: Parallel
@listen("initialize_flow")
def execute_stock_crew(...)

@listen("initialize_flow")
def execute_etf_crew(...)

@listen("initialize_flow")
def execute_crypto_crew(...)

# Phase 1b: Parallel (waits for Phase 1a)
@listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew"))
def execute_deep_analysis_crew(...)

@listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew"))
def execute_discovery_crew(...)

# Phase 2: Sequential (waits for ALL Phase 1)
@listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew",
             "execute_deep_analysis_crew", "execute_discovery_crew"))
def execute_rebalancing_crew(...)
```

### CrewAI Best Practices Compliance

**Critical Design Decision**: All crews must follow CrewAI best practices for reasoning, planning, delegation, and state management to ensure optimal performance and maintainability.

#### Reasoning Configuration

**Enable `reasoning=True` for:**

- ✅ investment_discovery_crew (complex multi-asset discovery)
- ✅ portfolio_rebalancing_crew (complex portfolio optimization)
- ✅ crypto_crew, stock_crew, etf_crew (complex market analysis)

**Disable `reasoning=False` for:**

- ❌ deep_analysis_crew (high-volume execution: 66+ runs per portfolio)
- ❌ Final reporters (consolidation only, no new analysis)

**Configuration Pattern**:

```python
analyst = Agent(
    reasoning=True,
    max_reasoning_attempts=3  # Prevent infinite loops
)
```

**Rationale**: Reasoning adds 5-15 seconds and 1-3 LLM calls per cycle. For high-volume crews (66+ executions), this overhead is prohibitive. Deep analysis crew runs once per underperforming holding, which can be 66+ times per portfolio.

#### Planning Configuration

**Enable `planning=True` ONLY when ALL conditions met:**

- Crew has 4+ agents AND
- Crew has 6+ tasks AND
- Execution volume ≤ 3 runs

**Enabled for:**

- ✅ portfolio_rebalancing_crew (3+ agents, 4+ tasks, single execution)
- ✅ investment_discovery_crew (4 agents, 7 tasks, single execution)

**Disabled for:**

- ❌ deep_analysis_crew (runs 66+ times - overhead × 66 is too costly)
- ❌ crypto_crew, stock_crew, etf_crew (simpler workflows)

**Configuration Pattern**:

```python
@crew
def crew(self) -> Crew:
    return Crew(
        agents=self.agents,
        tasks=self.tasks,
        planning=True,
        planning_llm="gpt-4o-mini"  # Optimal planning quality
    )
```

**Rationale**: Planning overhead multiplied by execution count. For deep_analysis_crew running 66+ times, planning overhead would be excessive.

#### Delegation Configuration

**Enable `allow_delegation=True` for:**

- ✅ Coordinator/lead agents managing workflow
- ✅ Agents needing to ask questions

**Disable `allow_delegation=False` for:**

- ❌ Focused specialist agents (single responsibility)
- ❌ Final reporters (consolidation only)

**Configuration Pattern**:

```python
@agent
def lead_analyst(self) -> Agent:
    return Agent(
        allow_delegation=True  # Can delegate to specialists
    )

@final_reporter
@agent
def reporter(self) -> Agent:
    return Agent(
        tools=[],  # Enforced empty
        allow_delegation=False  # No delegation
    )
```

#### Flow State Management

**Structured State with Pydantic** (REQUIRED):

```python
from pydantic import BaseModel
from crewai.flow import Flow

class ReportAggregationState(BaseModel):
    crew_export_paths: Dict[str, List[str]] = {}
    consolidated_json_path: Optional[str] = None

class ReportAggregationFlow(Flow[ReportAggregationState]):
    # Use self.state (structured), NOT self.inputs (unstructured)
    pass
```

**Flow Method Signatures** (REQUIRED):

```python
@listen("upstream_method")
def process_data(self) -> dict[str, Any]:
    # Update structured state
    self.state.processing_complete = True

    # Return data for downstream listeners
    return {"results": data}

@listen("process_data")
def next_step(self, upstream_data: dict[str, Any]) -> dict[str, Any]:
    # Receive data from upstream as parameter
    results = upstream_data.get("results")
    return {"processed": results}
```

**Rationale**: Structured state with Pydantic provides type safety, prevents data corruption, and follows CrewAI Flow documentation patterns exactly.

#### Configuration Matrix

| Crew                  | Reasoning  | Planning   | Delegation | Execution Volume | Rationale                               |
| --------------------- | ---------- | ---------- | ---------- | ---------------- | --------------------------------------- |
| investment_discovery  | ✅ Enable  | ✅ Enable  | ✅ Enable  | 1                | 4 agents, 7 tasks, complex coordination |
| portfolio_rebalancing | ✅ Enable  | ✅ Enable  | ✅ Enable  | 1                | 3+ agents, 4+ tasks, optimization       |
| deep_analysis         | ❌ Disable | ❌ Disable | ❌ Disable | 66+              | High volume - avoid overhead            |
| crypto_crew           | ✅ Enable  | ❌ Disable | Mixed      | 1-10             | Complex analysis, simpler workflow      |
| stock_crew            | ✅ Enable  | ❌ Disable | Mixed      | 1-10             | Complex analysis, simpler workflow      |
| etf_crew              | ✅ Enable  | ❌ Disable | Mixed      | 1-10             | Complex analysis, simpler workflow      |

### Crew Evaluation Results

**Critical Design Decision**: All existing crews have been evaluated to identify tasks that should be Python instead of AI, following the AI Minimalism principle.

**Evaluation Criteria Applied**:

- **AI Required**: Tasks requiring reasoning, synthesis, or natural language understanding
- **Python Preferred**: Data fetching, calculations, validations, HTML generation, data transformation

#### Evaluation Summary

| Crew                       | AI Tasks | Python Tasks | Cost Savings     | Time Savings | Priority     |
| -------------------------- | -------- | ------------ | ---------------- | ------------ | ------------ |
| report_crew                | 3        | 1            | \$2.00-3.00      | 30-60s       | **CRITICAL** |
| investment_discovery_crew  | 6        | 1            | \$1.00-2.00      | 20-40s       | HIGH         |
| portfolio_rebalancing_crew | 3        | 2            | \$1.00-1.50      | 15-30s       | HIGH         |
| deep_analysis              | 3        | 1            | \$0.40-0.80      | 10-20s       | HIGH         |
| crypto_crew                | 4        | 1            | \$0.50-1.00      | 10-20s       | MEDIUM       |
| stock_crew                 | 4        | 1            | \$0.50-1.00      | 10-20s       | MEDIUM       |
| etf_crew                   | 4        | 1            | \$0.60-1.00      | 10-20s       | MEDIUM       |
| **TOTAL**                  | **27**   | **8**        | **\$6.00-10.30** | **106-200s** | -            |

#### Key Findings by Crew

**1. report_crew (HIGHEST PRIORITY)**

- **AI Tasks (3)**: Financial integration, portfolio allocation, risk assessment
- **Python Tasks (1)**: Comprehensive report generation (796-line task description!)
- **Cost Savings**: \$2.00-3.00 per execution (HIGHEST)
- **Time Savings**: 30-60 seconds (BIGGEST)
- **Critical Issue**: Most expensive report generation in entire codebase
- **Implementation**: Jinja2 template with French localization, SEC citation handling, anti-hallucination logic
- **Complexity**: HIGH (1-2 days) - extensive French report with many sections

**2. investment_discovery_crew**

- **AI Tasks (6)**: ETF/stock/crypto discovery, validation, optimization, feedback learning
- **Python Tasks (1)**: Report generation
- **Cost Savings**: \$1.00-2.00 per execution
- **Time Savings**: 20-40 seconds
- **Implementation**: Jinja2 template with French localization
- **Complexity**: MEDIUM (4-8 hours)

**3. portfolio_rebalancing_crew**

- **AI Tasks (3)**: Holding analysis, alternatives finding, rebalancing strategy
- **Python Tasks (2)**: Price target calculations, report generation
- **Cost Savings**: \$1.00-1.50 per execution
- **Time Savings**: 15-30 seconds
- **Implementation**: Python calculator + Jinja2 template
- **Complexity**: MEDIUM (1-2 days)

**4. deep_analysis**

- **AI Tasks (3)**: Deep analysis, technical analysis, risk assessment
- **Python Tasks (1)**: Final report generation
- **Cost Savings**: \$0.40-0.80 per execution
- **Time Savings**: 10-20 seconds
- **Volume Impact**: Runs 66+ times per portfolio (high-volume crew)
- **Implementation**: Jinja2 template
- **Complexity**: LOW (2-4 hours)

**5. crypto_crew, stock_crew, etf_crew (Discovery Crews)**

- **AI Tasks (4 each)**: Market analysis, screening, technical detail, risk assessment
- **Python Tasks (1 each)**: Final report generation
- **Cost Savings**: \$0.50-1.00 per execution each
- **Time Savings**: 10-20 seconds each
- **Implementation**: Jinja2 templates
- **Complexity**: LOW (2-4 hours each)

#### Common Patterns Identified

**Tasks That REQUIRE AI** (27 total):

- ✅ Market trend interpretation and synthesis
- ✅ Multi-factor screening and decision-making
- ✅ SEC filing analysis and interpretation
- ✅ Risk scenario analysis and mitigation strategies
- ✅ Portfolio optimization and allocation
- ✅ Investment thesis generation
- ✅ Pattern recognition in technical analysis
- ✅ Sentiment analysis interpretation
- ✅ Strategic synthesis and recommendations

**Tasks That SHOULD BE Python** (8 total):

- ❌ HTML report generation (ALL crews)
- ❌ Price target calculations (portfolio_rebalancing_crew)
- ❌ Technical indicator calculations (can be extracted as helpers)
- ❌ Risk metric calculations (can be extracted as helpers)
- ❌ Backtesting calculations (can be extracted as helpers)

#### Implementation Roadmap

**Phase 1: Convert Report Generation to Python Templates**

**Priority Order**:

1. **report_crew** (CRITICAL) - \$2.00-3.00 savings, 30-60s faster

   - Highest cost savings opportunity
   - Most complex implementation (1-2 days)
   - French localization with extensive sections

2. **investment_discovery_crew** (HIGH) - \$1.00-2.00 savings, 20-40s faster

   - Second highest savings
   - Medium complexity (4-8 hours)
   - French localization required

3. **portfolio_rebalancing_crew** (HIGH) - \$1.00-1.50 savings, 15-30s faster

   - Includes price target calculator
   - Medium complexity (1-2 days)

4. **deep_analysis** (HIGH) - \$0.40-0.80 savings, 10-20s faster

   - High-volume crew (66+ executions)
   - Low complexity (2-4 hours)
   - Cumulative savings significant

5. **crypto_crew, stock_crew, etf_crew** (MEDIUM) - \$0.50-1.00 each
   - Similar implementations
   - Low complexity (2-4 hours each)
   - Can be done in parallel

**Expected Phase 1 Results**:

- **Total Cost Savings**: \$6.00-10.30 per full portfolio analysis
- **Total Time Savings**: 106-200 seconds per execution
- **At Scale (100 portfolios)**: \$600-1,030 savings, 2.9-5.5 hours faster
- **Consistency**: 100% consistent formatting across all reports
- **Testability**: Full unit test coverage for all report generation

**Phase 2: Extract Python Calculation Helpers**

**Implementation Requirements** (Part of this spec):

- Technical indicator calculations (RSI, MACD, Bollinger Bands)
- Risk metric calculations (VaR, CVaR, volatility, max drawdown)
- Backtesting engine (strategy execution, performance metrics)
- Price target calculations (DCF, P/E, support/resistance)
- ETF-specific metrics (tracking error, correlation, concentration risk)

**Python Modules to Create**:

- `src/finwiz/utils/technical_indicators.py` - Technical analysis calculations
- `src/finwiz/utils/risk_metrics.py` - Risk metric calculations
- `src/finwiz/utils/backtesting.py` - Backtesting engine
- `src/finwiz/utils/price_targets.py` - Valuation calculations
- `src/finwiz/utils/etf_metrics.py` - ETF-specific calculations

**Expected Phase 2 Results**:

- Additional \$1.00-3.00 cost savings per execution
- Additional 30-90 seconds time savings
- Testable calculation logic with full unit test coverage
- Easier maintenance and debugging
- AI agents focus on interpretation, not calculation

#### Cost-Benefit Analysis

**Investment Required**:

- Phase 1: 5-8 days development time (report templates)
- Phase 2: 5-10 days development time (calculation helpers)
- **Total**: 10-18 days development time

**Returns (Both Phases)**:

- Per execution: \$7.00-13.30 savings, 136-290s faster
- Per 100 executions: \$700-1,330 savings, 3.8-8.1 hours faster
- Per 1000 executions: \$7,000-13,300 savings, 38-81 hours faster

**Break-even Point**: ~50-100 portfolio analyses

**Long-term Benefits**:

- ✅ Testable calculation logic with full unit test coverage
- ✅ Consistent, maintainable codebase
- ✅ AI agents focus on reasoning, not calculations
- ✅ Faster debugging and issue resolution
- ✅ Easier onboarding for new developers
- ✅ Professional French localization in templates

**Rationale**: Following AI Minimalism principle - use Python for deterministic tasks (free, fast, testable) and reserve AI exclusively for analysis requiring reasoning. Both phases are essential for a production-ready, cost-efficient architecture.

## Components and Interfaces

### 0. Critical Fixes Implementation (Requirements 0.x)

**IMMEDIATE PRIORITY**: These components address the fundamental failures identified in the implementation analysis.

#### 0.1 Pure Python Deep Analysis Replacement

**Problem**: AI-based `DeepAnalysisCrew` still being used instead of pure Python scoring.

**Solution**: `PortfolioDeepAnalyzer` class that completely replaces AI crews:

```python
# src/finwiz/scoring/portfolio_deep_analyzer.py
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

class PortfolioDeepAnalyzer:
    """Pure Python portfolio analysis - NO AI crews."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.scorer = DeepAnalysisScorer()

    def analyze_portfolio_holdings(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze multiple holdings concurrently using Python threading.

        Requirements: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7
        """
        start_time = time.time()
        results = {}

        # Process holdings concurrently (5-10 at a time)
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ticker = {
                executor.submit(self._analyze_single_holding, holding): holding['ticker']
                for holding in holdings
            }

            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    result = future.result()
                    results[ticker] = result

                    # Save JSON export to proper output directory
                    self._save_json_export(ticker, result)

                except Exception as e:
                    logger.error(f"Analysis failed for {ticker}: {e}")
                    results[ticker] = self._create_error_result(ticker, str(e))

        # Generate consolidated export
        consolidated_path = self._save_consolidated_export(results)

        execution_time = time.time() - start_time
        logger.info(f"Portfolio analysis completed in {execution_time:.1f}s")
        logger.info(f"Performance: {len(holdings)/execution_time:.1f} holdings/second")
        logger.info(f"Cost: $0.00 (100% Python calculations)")

        return {
            "results": results,
            "consolidated_path": consolidated_path,
            "execution_time": execution_time,
            "holdings_per_second": len(holdings)/execution_time,
            "cost": 0.0
        }

    def _analyze_single_holding(self, holding: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze single holding using DeepAnalysisScorer."""
        ticker = holding['ticker']

        # Extract data (this would normally come from tools)
        fundamental_metrics = self._extract_fundamental_data(holding)
        technical_metrics = self._extract_technical_data(holding)
        risk_metrics = self._extract_risk_data(holding)

        # Use Python scorer (NO AI)
        result = self.scorer.score_ticker(
            ticker=ticker,
            fundamental_metrics=fundamental_metrics,
            technical_metrics=technical_metrics,
            risk_metrics=risk_metrics
        )

        return result

    def _save_json_export(self, ticker: str, result: Dict[str, Any]) -> None:
        """Save JSON export to output directory (NOT just cache).

        Requirements: 0.8, 0.9, 0.10, 0.11
        """
        asset_class = result.get('asset_class', 'stock')
        output_dir = Path(f"output/{asset_class}")
        output_dir.mkdir(parents=True, exist_ok=True)

        export_path = output_dir / f"{ticker}_{self.session_id}.json"
        export_path.write_text(json.dumps(result, indent=2))

        logger.info(f"JSON export saved: {export_path}")
```

#### 0.2 Fixed JSON Export Directory Structure

**Problem**: JSON exports only saved to cache, not accessible to downstream systems.

**Solution**: Proper output directory structure (Requirements 0.8-0.12):

```
output/
├── stock/
│   ├── AAPL_{session_id}.json
│   ├── MSFT_{session_id}.json
│   └── ...
├── etf/
│   ├── SPY_{session_id}.json
│   └── ...
├── crypto/
│   ├── BTC_{session_id}.json
│   └── ...
└── deep_analysis_consolidated_{session_id}.json
```

#### 0.3 A+ Discovery Integration Fix

**Problem**: A+ discovery shows 0 opportunities because it's not reading deep analysis results.

**Solution**: Updated discovery integration (Requirements 0.13-0.17):

```python
class APlusDiscoveryIntegrator:
    """Integrate A+ discovery with deep analysis results."""

    def integrate_with_deep_analysis(self, session_id: str) -> Dict[str, Any]:
        """Read deep analysis results and identify A+ opportunities.

        Requirements: 0.13, 0.14, 0.15, 0.16, 0.17
        """
        # Read deep analysis JSON exports from output directory
        deep_analysis_results = self._read_deep_analysis_exports(session_id)

        # Identify A+ and A grade holdings
        aplus_opportunities = []
        for ticker, result in deep_analysis_results.items():
            if result.get('grade') in ['A+', 'A']:
                aplus_opportunities.append({
                    'ticker': ticker,
                    'grade': result['grade'],
                    'composite_score': result['composite_score'],
                    'recommendation': result['recommendation']
                })

        # Update discovery export
        discovery_export = {
            'has_a_plus_analysis': len(aplus_opportunities) > 0,
            'total_opportunities_found': len(aplus_opportunities),
            'opportunities': aplus_opportunities,
            'session_id': session_id
        }

        # Save discovery export
        discovery_path = Path(f"output/discovery_{session_id}.json")
        discovery_path.write_text(json.dumps(discovery_export, indent=2))

        return discovery_export
```

#### 0.4 Backtesting Pipeline Connection

**Problem**: Backtesting shows "Non exécuté" because it's not connected to discovery results.

**Solution**: Backtesting integration (Requirements 0.18-0.21):

```python
class BacktestingPipelineConnector:
    """Connect backtesting to discovery results."""

    def execute_backtesting_if_candidates_available(self, session_id: str) -> Dict[str, Any]:
        """Execute backtesting when A+ candidates are found.

        Requirements: 0.18, 0.19, 0.20, 0.21
        """
        # Read A+ opportunities from discovery export
        discovery_path = Path(f"output/discovery_{session_id}.json")
        if not discovery_path.exists():
            return {"status": "no_discovery_data", "executed": False}

        discovery_data = json.loads(discovery_path.read_text())

        if not discovery_data.get('has_a_plus_analysis', False):
            return {"status": "no_aplus_candidates", "executed": False}

        # Execute backtesting for A+ candidates
        candidates = discovery_data.get('opportunities', [])
        backtesting_results = []

        for candidate in candidates:
            ticker = candidate['ticker']
            try:
                # Run backtesting analysis
                result = self._run_backtesting_for_ticker(ticker)
                backtesting_results.append(result)
            except Exception as e:
                logger.error(f"Backtesting failed for {ticker}: {e}")

        # Save backtesting results
        backtesting_export = {
            'executed': True,
            'candidates_analyzed': len(candidates),
            'results': backtesting_results,
            'session_id': session_id
        }

        backtesting_path = Path(f"output/backtesting_{session_id}.json")
        backtesting_path.write_text(json.dumps(backtesting_export, indent=2))

        return backtesting_export
```

#### 0.5 Python Report Generator

**Problem**: Final reports generated by AI instead of Python templates.

**Solution**: Pure Python report generation (Requirements 0.22-0.26):

```python
# src/finwiz/reporting/python_report_generator.py
from jinja2 import Environment, FileSystemLoader

class PythonReportGenerator:
    """Generate reports using Jinja2 templates (NO AI).

    Requirements: 0.22, 0.23, 0.24, 0.25, 0.26
    """

    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('src/finwiz/templates'),
            autoescape=True
        )

    def generate_family_financial_plan(
        self,
        portfolio_data: Dict[str, Any],
        session_id: str
    ) -> str:
        """Generate final French report using templates."""

        # Load all analysis results
        analysis_data = self._load_all_analysis_results(session_id)

        # Prepare template data
        template_data = {
            'portfolio': portfolio_data,
            'stock_analyses': analysis_data.get('stocks', []),
            'etf_analyses': analysis_data.get('etfs', []),
            'crypto_analyses': analysis_data.get('cryptos', []),
            'aplus_opportunities': analysis_data.get('aplus_opportunities', []),
            'backtesting_results': analysis_data.get('backtesting', {}),
            'session_id': session_id,
            'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Render template
        template = self.env.get_template('family_financial_plan.html.j2')
        html_content = template.render(**template_data)

        # Save final report
        output_path = Path(f"output/finwiz_family_financial_plan_{session_id}.html")
        output_path.write_text(html_content, encoding='utf-8')

        logger.info(f"Final report generated: {output_path}")
        return str(output_path)
```

#### 0.6 Integration Demonstration Script

**Solution**: Validation script (Requirements 0.31-0.34):

```python
# scripts/run_python_analysis.py
"""Demonstration script for pure Python analysis approach."""

def main():
    """Demonstrate complete Python-based analysis pipeline."""

    # Load portfolio data
    portfolio_data = load_portfolio_from_csv('data/portfolio.csv')

    # Run pure Python analysis
    analyzer = PortfolioDeepAnalyzer(session_id="demo")
    analysis_results = analyzer.analyze_portfolio_holdings(portfolio_data)

    # Integrate A+ discovery
    discovery_integrator = APlusDiscoveryIntegrator()
    discovery_results = discovery_integrator.integrate_with_deep_analysis("demo")

    # Connect backtesting
    backtesting_connector = BacktestingPipelineConnector()
    backtesting_results = backtesting_connector.execute_backtesting_if_candidates_available("demo")

    # Generate final report
    report_generator = PythonReportGenerator()
    final_report_path = report_generator.generate_family_financial_plan(portfolio_data, "demo")

    # Log performance metrics
    logger.info("=== PYTHON ANALYSIS PERFORMANCE ===")
    logger.info(f"Total time: {analysis_results['execution_time']:.1f}s")
    logger.info(f"Holdings/second: {analysis_results['holdings_per_second']:.1f}")
    logger.info(f"Total cost: ${analysis_results['cost']:.2f}")
    logger.info(f"A+ opportunities found: {discovery_results['total_opportunities_found']}")
    logger.info(f"Backtesting executed: {backtesting_results['executed']}")
    logger.info(f"Final report: {final_report_path}")

    # Prove 10-20x speed improvement
    estimated_ai_time = len(portfolio_data) * 300  # 5 minutes per holding
    speedup_factor = estimated_ai_time / analysis_results['execution_time']
    logger.info(f"Speedup factor: {speedup_factor:.1f}x faster than AI approach")

if __name__ == "__main__":
    main()
```

### 1. Pydantic Export Schemas

Each crew generates a validated export object saved to JSON.

#### Base Export Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CrewExportBase(BaseModel):
    """Base schema for all crew exports."""
    crew_name: str = Field(..., description="Name of the crew")
    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: str = Field(..., pattern="^(stock|etf|crypto)$")
    analysis_date: datetime = Field(default_factory=datetime.now)
    session_id: str = Field(..., description="Flow session identifier")

    model_config = {
        "extra": "forbid",
        "str_strip_whitespace": True
    }
```

#### Stock Crew Export

```python
from finwiz.schemas.stock import TenKInsight, RiskAssessmentStandardized

class StockCrewExport(CrewExportBase):
    """Export schema for Stock Crew analysis."""
    crew_name: str = Field(default="stock_crew")

    # Analysis Results
    fundamental_analysis: TenKInsight
    risk_assessment: RiskAssessmentStandardized
    technical_indicators: Dict[str, Any]

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0)
    grade: str = Field(..., pattern="^(A\\+|A|B|C|D|F)$")

    # Recommendations
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=50)

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### ETF Crew Export

```python
from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding

class ETFCrewExport(CrewExportBase):
    """Export schema for ETF Crew analysis."""
    crew_name: str = Field(default="etf_crew")

    # Analysis Results
    factsheet: ETFFactsheet
    top_holdings: List[ETFTopHolding]
    risk_assessment: RiskAssessmentStandardized

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0)
    grade: str = Field(..., pattern="^(A\\+|A|B|C|D|F)$")

    # Cost Analysis
    expense_ratio: float
    tracking_error: Optional[float]

    # Recommendations
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### Crypto Crew Export

```python
from finwiz.schemas.crypto import CryptoThesis

class CryptoCrewExport(CrewExportBase):
    """Export schema for Crypto Crew analysis."""
    crew_name: str = Field(default="crypto_crew")

    # Analysis Results
    thesis: CryptoThesis
    risk_assessment: RiskAssessmentStandardized
    technical_analysis: Dict[str, Any]

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0)
    grade: str = Field(..., pattern="^(A\\+|A|B|C|D|F)$")

    # Volatility Metrics
    volatility_30d: float
    max_drawdown: float

    # Recommendations
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### Deep Analysis Crew Export

```python
class DeepAnalysisCrewExport(CrewExportBase):
    """Export schema for Deep Analysis Crew."""
    crew_name: str = Field(default="deep_analysis_crew")

    # Comprehensive Analysis
    detailed_analysis: Dict[str, Any]
    risk_assessment: RiskAssessmentStandardized

    # Scores and Grades
    composite_score: float = Field(..., ge=0.0, le=1.0)
    grade: str = Field(..., pattern="^(A\\+|A|B|C|D|F)$")

    # Recommendations
    recommendation: str = Field(..., pattern="^(BUY|HOLD|SELL)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### Discovery Crew Export

```python
class DiscoveryOpportunity(BaseModel):
    """Single A+ investment opportunity."""
    ticker: str
    name: str
    asset_class: str
    composite_score: float = Field(..., ge=0.7, le=1.0)  # A+ threshold
    grade: str = Field(default="A+")
    rationale: str

class DiscoveryCrewExport(CrewExportBase):
    """Export schema for Investment Discovery Crew."""
    crew_name: str = Field(default="discovery_crew")
    ticker: str = Field(default="N/A")  # Discovery doesn't analyze single ticker

    # Discovery Results
    opportunities: List[DiscoveryOpportunity] = Field(..., max_items=10)
    screening_criteria: Dict[str, Any]
    market_context: str

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### Rebalancing Crew Export

```python
class TradeRecommendation(BaseModel):
    """Single trade recommendation."""
    action: str = Field(..., pattern="^(BUY|SELL|HOLD)$")
    ticker: str
    asset_class: str
    quantity: Optional[float] = None
    rationale: str

class RebalancingCrewExport(CrewExportBase):
    """Export schema for Portfolio Rebalancing Crew.

    This crew receives ALL analysis results as inputs:
    - Current holdings (stock/etf/crypto exports)
    - Deep analysis results (detailed grades)
    - Discovery opportunities (A+ alternatives)
    """
    crew_name: str = Field(default="rebalancing_crew")
    ticker: str = Field(default="N/A")  # Portfolio-level analysis

    # Input Summary (what the crew saw)
    holdings_analyzed: int = Field(..., description="Number of current holdings analyzed")
    deep_analyses_reviewed: int = Field(..., description="Number of deep analyses reviewed")
    opportunities_discovered: int = Field(..., description="Number of A+ opportunities found")

    # Current State
    current_allocation: Dict[str, float] = Field(..., description="Current portfolio allocation by ticker")
    current_total_value: float

    # Optimization Results
    target_allocation: Dict[str, float] = Field(..., description="Recommended allocation by ticker")
    trades_required: List[TradeRecommendation]

    # Performance Metrics
    expected_return: float = Field(..., description="Expected annual return")
    expected_risk: float = Field(..., description="Expected volatility")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return metric")

    # Improvement Analysis
    improvement_summary: str = Field(..., description="How rebalancing improves portfolio")
    risk_reduction: float = Field(..., description="Expected risk reduction")
    return_improvement: float = Field(..., description="Expected return improvement")

    # Metadata
    data_sources: List[str]
    report_html_path: str
    report_json_path: str
```

#### Consolidated Report Export

```python
class ConsolidatedReportExport(BaseModel):
    """Consolidated export from all SME crews."""
    session_id: str
    consolidation_date: datetime = Field(default_factory=datetime.now)

    # SME Crew Results
    stock_analyses: List[StockCrewExport] = []
    etf_analyses: List[ETFCrewExport] = []
    crypto_analyses: List[CryptoCrewExport] = []
    deep_analyses: List[DeepAnalysisCrewExport] = []
    discovery_results: Optional[DiscoveryCrewExport] = None
    rebalancing_results: Optional[RebalancingCrewExport] = None

    # Execution Metadata
    crew_execution_status: Dict[str, str]  # crew_name -> "completed" | "failed"
    total_execution_time: float

    model_config = {"extra": "forbid"}
```

### 2. Crew Reporter Task Pattern

Each crew has a final reporter task that creates the Pydantic export object.

#### Implementation Pattern

```python
from crewai import Agent, Task, agent, task
from finwiz.utils.agent_validators import final_reporter

class StockCrew:

    @final_reporter
    @agent
    def investment_reporter(self) -> Agent:
        """Final reporter with empty tools (enforced by decorator)."""
        return Agent(
            config=self.agents_config["investment_reporter"],
            tools=[],  # MUST be empty
            verbose=True
        )

    @task
    def generate_export_task(self) -> Task:
        """Final task to create Pydantic export object."""
        return Task(
            description="""
            Consolidate all analysis findings from context into a StockCrewExport object.

            Steps:
            1. Extract fundamental_analysis from context
            2. Extract risk_assessment from context
            3. Extract technical_indicators from context
            4. Calculate composite_score and grade
            5. Generate recommendation with rationale
            6. Create StockCrewExport object
            7. Validate against Pydantic schema
            8. Save to JSON file

            Output file: output/reports/{session_id}/stock_crew/stock_crew_export.json
            """,
            expected_output="StockCrewExport object saved to JSON",
            output_pydantic=StockCrewExport,
            output_json=True,
            agent=self.investment_reporter(),
            async_execution=False  # Final task must be synchronous
        )
```

### 3. Python HTML Generation (NO AI)

HTML reports are generated using Jinja2 templates from JSON exports.

#### Template Structure

```
src/finwiz/templates/
├── base.html                    # Base template with CSS
├── stock_report.html            # Stock crew template
├── etf_report.html              # ETF crew template
├── crypto_report.html           # Crypto crew template
├── deep_analysis_report.html    # Deep analysis template
├── discovery_report.html        # Discovery template
├── rebalancing_report.html      # Rebalancing template
└── final_report.html            # Consolidated final report
```

#### HTML Generator Function

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any

class HTMLReportGenerator:
    """Generate HTML reports from JSON exports using Jinja2."""

    def __init__(self, template_dir: str = "src/finwiz/templates"):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def generate_crew_report(
        self,
        crew_name: str,
        export_data: Dict[str, Any],
        output_path: Path
    ) -> str:
        """Generate HTML report for a crew.

        Args:
            crew_name: Name of crew (stock_crew, etf_crew, etc.)
            export_data: Validated JSON export data
            output_path: Path to save HTML file

        Returns:
            Path to generated HTML file
        """
        # Load appropriate template
        template_name = f"{crew_name}_report.html"
        template = self.env.get_template(template_name)

        # Render template with data
        html_content = template.render(
            data=export_data,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        return str(output_path)
```

#### Template Design Notes

**Inspiration from Existing Output**:

- Review existing crew HTML outputs in `output/` directory
- Reuse successful styling patterns and section structures
- Maintain consistent visual language across all reports
- Preserve emoji usage patterns for visual clarity
- Keep professional French terminology that works well

**Template Reusability**:

- Base template provides consistent styling and structure
- Crew-specific templates extend base and add specialized sections
- CSS supports both light and dark modes automatically
- Responsive design works on desktop and mobile

#### Base Template (base.html)

```html
<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{% block title %}Rapport FinWiz{% endblock %}</title>
    <style>
      /* Professional CSS with light/dark mode support */
      :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f5f5f5;
        --text-primary: #2c3e50;
        --text-secondary: #34495e;
        --accent: #3498db;
        --success: #27ae60;
        --warning: #f39c12;
        --danger: #e74c3c;
      }

      @media (prefers-color-scheme: dark) {
        :root {
          --bg-primary: #1a1a1a;
          --bg-secondary: #2d2d2d;
          --text-primary: #ecf0f1;
          --text-secondary: #bdc3c7;
          --accent: #3498db;
        }
      }

      body {
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: var(--bg-secondary);
        color: var(--text-primary);
      }

      h1 {
        color: var(--text-primary);
        border-bottom: 3px solid var(--accent);
      }
      h2 {
        color: var(--text-secondary);
        margin-top: 30px;
      }

      .grade-a-plus {
        color: var(--success);
        font-weight: bold;
      }
      .grade-a {
        color: #2ecc71;
      }
      .grade-b {
        color: var(--warning);
      }
      .grade-c {
        color: #e67e22;
      }
      .grade-d {
        color: var(--danger);
      }
      .grade-f {
        color: #c0392b;
        font-weight: bold;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        background-color: var(--bg-primary);
      }

      th {
        background-color: var(--accent);
        color: white;
        padding: 12px;
        text-align: left;
      }

      td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
      }
    </style>
  </head>
  <body>
    {% block content %}{% endblock %}
  </body>
</html>
```

#### Stock Report Template Example

```html
{% extends "base.html" %} {% block title %}Analyse {{ data.ticker }} - FinWiz{%
endblock %} {% block content %}
<h1>📊 Analyse {{ data.ticker }} ({{ data.asset_class|upper }})</h1>
<p><strong>Date:</strong> {{ data.analysis_date }}</p>
<p><strong>Session:</strong> {{ data.session_id }}</p>

<section>
  <h2>Recommandation</h2>
  <p class="grade-{{ data.grade|lower|replace('+', '-plus') }}">
    {% if data.recommendation == 'BUY' %}✅{% elif data.recommendation == 'SELL'
    %}❌{% else %}⏸️{% endif %}
    <strong>{{ data.recommendation }}</strong> - Grade {{ data.grade }}
  </p>
  <p>
    <strong>Score Composite:</strong> {{ "%.2f"|format(data.composite_score *
    100) }}%
  </p>
  <p><strong>Confiance:</strong> {{ "%.0f"|format(data.confidence * 100) }}%</p>
  <p><strong>Rationale:</strong> {{ data.rationale }}</p>
</section>

<section>
  <h2>Analyse Fondamentale</h2>
  <table>
    <tr>
      <th>Métrique</th>
      <th>Valeur</th>
    </tr>
    {% for key, value in data.fundamental_analysis.items() %}
    <tr>
      <td>{{ key }}</td>
      <td>{{ value }}</td>
    </tr>
    {% endfor %}
  </table>
</section>

<section>
  <h2>Évaluation des Risques</h2>
  <p>
    <strong>Score de Risque:</strong> {{ data.risk_assessment.risk_score }}/10
  </p>
  <p><strong>Facteurs de Risque:</strong></p>
  <ul>
    {% for factor in data.risk_assessment.risk_factors %}
    <li>{{ factor }}</li>
    {% endfor %}
  </ul>
</section>

<section>
  <h2>Sources de Données</h2>
  <ul>
    {% for source in data.data_sources %}
    <li>{{ source }}</li>
    {% endfor %}
  </ul>
</section>

<footer>
  <p><em>Généré le {{ generation_date }}</em></p>
</footer>
{% endblock %}
```

### 4. Python Data Consolidation (NO AI)

Pure Python function consolidates all crew JSON exports.

#### Consolidation Function

```python
from pathlib import Path
from typing import List, Dict, Any
import json
from pydantic import ValidationError

class ReportConsolidator:
    """Consolidate crew reports using pure Python (NO AI)."""

    def __init__(self, session_id: str, output_dir: Path):
        self.session_id = session_id
        self.output_dir = output_dir

    def consolidate_reports(
        self,
        crew_export_paths: Dict[str, List[str]]
    ) -> ConsolidatedReportExport:
        """Consolidate all crew JSON exports.

        Args:
            crew_export_paths: Dict mapping crew names to list of export file paths
                {
                    "stock_crew": ["path/to/AAPL_export.json", ...],
                    "etf_crew": ["path/to/SPY_export.json", ...],
                    ...
                }

        Returns:
            ConsolidatedReportExport object
        """
        import time
        start_time = time.time()

        consolidated = ConsolidatedReportExport(
            session_id=self.session_id,
            crew_execution_status={}
        )

        # Consolidate stock analyses
        if "stock_crew" in crew_export_paths:
            consolidated.stock_analyses = self._load_exports(
                crew_export_paths["stock_crew"],
                StockCrewExport
            )
            consolidated.crew_execution_status["stock_crew"] = (
                "completed" if consolidated.stock_analyses else "failed"
            )

        # Consolidate ETF analyses
        if "etf_crew" in crew_export_paths:
            consolidated.etf_analyses = self._load_exports(
                crew_export_paths["etf_crew"],
                ETFCrewExport
            )
            consolidated.crew_execution_status["etf_crew"] = (
                "completed" if consolidated.etf_analyses else "failed"
            )

        # Consolidate crypto analyses
        if "crypto_crew" in crew_export_paths:
            consolidated.crypto_analyses = self._load_exports(
                crew_export_paths["crypto_crew"],
                CryptoCrewExport
            )
            consolidated.crew_execution_status["crypto_crew"] = (
                "completed" if consolidated.crypto_analyses else "failed"
            )

        # Consolidate deep analyses
        if "deep_analysis_crew" in crew_export_paths:
            consolidated.deep_analyses = self._load_exports(
                crew_export_paths["deep_analysis_crew"],
                DeepAnalysisCrewExport
            )
            consolidated.crew_execution_status["deep_analysis_crew"] = (
                "completed" if consolidated.deep_analyses else "failed"
            )

        # Consolidate discovery results (single file)
        if "discovery_crew" in crew_export_paths:
            discovery_exports = self._load_exports(
                crew_export_paths["discovery_crew"],
                DiscoveryCrewExport
            )
            consolidated.discovery_results = discovery_exports[0] if discovery_exports else None
            consolidated.crew_execution_status["discovery_crew"] = (
                "completed" if consolidated.discovery_results else "failed"
            )

        # Consolidate rebalancing results (single file)
        if "rebalancing_crew" in crew_export_paths:
            rebalancing_exports = self._load_exports(
                crew_export_paths["rebalancing_crew"],
                RebalancingCrewExport
            )
            consolidated.rebalancing_results = rebalancing_exports[0] if rebalancing_exports else None
            consolidated.crew_execution_status["rebalancing_crew"] = (
                "completed" if consolidated.rebalancing_results else "failed"
            )

        consolidated.total_execution_time = time.time() - start_time

        # Save consolidated export
        output_path = self.output_dir / "consolidated_report.json"
        output_path.write_text(
            consolidated.model_dump_json(indent=2),
            encoding="utf-8"
        )

        return consolidated

    def _load_exports(
        self,
        file_paths: List[str],
        schema_class: type[BaseModel]
    ) -> List[BaseModel]:
        """Load and validate JSON exports."""
        exports = []

        for path_str in file_paths:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Export file not found: {path}")
                continue

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                export = schema_class.model_validate(data)
                exports.append(export)
            except ValidationError as e:
                logger.error(f"Validation failed for {path}: {e}")
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")

        return exports
```

### 5. Final Report Generation (Python Template)

Final French report generated using Jinja2 template from consolidated JSON.

#### Final Report Generator

```python
class FinalReportGenerator:
    """Generate final French report from consolidated JSON."""

    def __init__(self, template_dir: str = "src/finwiz/templates"):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def generate_final_report(
        self,
        consolidated_data: ConsolidatedReportExport,
        output_path: Path
    ) -> str:
        """Generate final HTML report in French.

        Args:
            consolidated_data: Consolidated export object
            output_path: Path to save final report

        Returns:
            Path to generated HTML file
        """
        template = self.env.get_template("final_report.html")

        # Prepare data for template
        template_data = {
            "session_id": consolidated_data.session_id,
            "consolidation_date": consolidated_data.consolidation_date,
            "stock_analyses": consolidated_data.stock_analyses,
            "etf_analyses": consolidated_data.etf_analyses,
            "crypto_analyses": consolidated_data.crypto_analyses,
            "deep_analyses": consolidated_data.deep_analyses,
            "discovery_results": consolidated_data.discovery_results,
            "rebalancing_results": consolidated_data.rebalancing_results,
            "execution_status": consolidated_data.crew_execution_status,
            "total_time": consolidated_data.total_execution_time
        }

        # Render template
        html_content = template.render(**template_data)

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        return str(output_path)
```

#### Final Report Template Structure

```html
{% extends "base.html" %} {% block title %}Rapport FinWiz Consolidé{% endblock
%} {% block content %}
<h1>📊 Rapport d'Analyse FinWiz</h1>
<p><strong>Session:</strong> {{ session_id }}</p>
<p><strong>Date de Consolidation:</strong> {{ consolidation_date }}</p>
<p><strong>Temps d'Exécution:</strong> {{ "%.2f"|format(total_time) }}s</p>

<!-- Executive Summary -->
<section>
  <h2>Résumé Exécutif</h2>
  <p>
    Analyse complète de {{ stock_analyses|length + etf_analyses|length +
    crypto_analyses|length }} actifs.
  </p>

  <h3>Statut d'Exécution</h3>
  <table>
    <tr>
      <th>Crew</th>
      <th>Statut</th>
    </tr>
    {% for crew_name, status in execution_status.items() %}
    <tr>
      <td>{{ crew_name }}</td>
      <td>{{ "✅" if status == "completed" else "❌" }} {{ status }}</td>
    </tr>
    {% endfor %}
  </table>
</section>

<!-- Stock Analyses -->
{% if stock_analyses %}
<section>
  <h2>📈 Analyses d'Actions</h2>
  {% for analysis in stock_analyses %}
  <div class="analysis-card">
    <h3>
      {{ analysis.ticker }} - {{ analysis.fundamental_analysis.company_name }}
    </h3>
    <p class="grade-{{ analysis.grade|lower|replace('+', '-plus') }}">
      <strong>Grade:</strong> {{ analysis.grade }} | <strong>Score:</strong> {{
      "%.0f"|format(analysis.composite_score * 100) }}%
    </p>
    <p><strong>Recommandation:</strong> {{ analysis.recommendation }}</p>
    <p>{{ analysis.rationale }}</p>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- ETF Analyses -->
{% if etf_analyses %}
<section>
  <h2>📊 Analyses d'ETFs</h2>
  {% for analysis in etf_analyses %}
  <div class="analysis-card">
    <h3>{{ analysis.ticker }}</h3>
    <p class="grade-{{ analysis.grade|lower|replace('+', '-plus') }}">
      <strong>Grade:</strong> {{ analysis.grade }} | <strong>Score:</strong> {{
      "%.0f"|format(analysis.composite_score * 100) }}%
    </p>
    <p>
      <strong>Ratio de Frais:</strong> {{ "%.2f"|format(analysis.expense_ratio *
      100) }}%
    </p>
    <p><strong>Recommandation:</strong> {{ analysis.recommendation }}</p>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- Crypto Analyses -->
{% if crypto_analyses %}
<section>
  <h2>🪙 Analyses de Cryptomonnaies</h2>
  {% for analysis in crypto_analyses %}
  <div class="analysis-card">
    <h3>{{ analysis.ticker }}</h3>
    <p class="grade-{{ analysis.grade|lower|replace('+', '-plus') }}">
      <strong>Grade:</strong> {{ analysis.grade }} | <strong>Score:</strong> {{
      "%.0f"|format(analysis.composite_score * 100) }}%
    </p>
    <p>
      <strong>Volatilité 30j:</strong> {{ "%.2f"|format(analysis.volatility_30d
      * 100) }}%
    </p>
    <p><strong>Recommandation:</strong> {{ analysis.recommendation }}</p>
  </div>
  {% endfor %}
</section>
{% endif %}

<!-- Discovery Results -->
{% if discovery_results %}
<section>
  <h2>💎 Opportunités A+ Découvertes</h2>
  <table>
    <tr>
      <th>Ticker</th>
      <th>Nom</th>
      <th>Classe</th>
      <th>Score</th>
      <th>Rationale</th>
    </tr>
    {% for opp in discovery_results.opportunities %}
    <tr>
      <td>{{ opp.ticker }}</td>
      <td>{{ opp.name }}</td>
      <td>{{ opp.asset_class }}</td>
      <td class="grade-a-plus">
        {{ "%.0f"|format(opp.composite_score * 100) }}%
      </td>
      <td>{{ opp.rationale }}</td>
    </tr>
    {% endfor %}
  </table>
</section>
{% endif %}

<!-- Rebalancing Results -->
{% if rebalancing_results %}
<section>
  <h2>⚖️ Recommandations de Rééquilibrage</h2>
  <p>
    <strong>Rendement Attendu:</strong> {{
    "%.2f"|format(rebalancing_results.expected_return * 100) }}%
  </p>
  <p>
    <strong>Risque Attendu:</strong> {{
    "%.2f"|format(rebalancing_results.expected_risk * 100) }}%
  </p>
  <p>
    <strong>Ratio de Sharpe:</strong> {{
    "%.2f"|format(rebalancing_results.sharpe_ratio) }}
  </p>

  <h3>Transactions Requises</h3>
  <table>
    <tr>
      <th>Action</th>
      <th>Ticker</th>
      <th>Quantité</th>
    </tr>
    {% for trade in rebalancing_results.trades_required %}
    <tr>
      <td>{{ trade.action }}</td>
      <td>{{ trade.ticker }}</td>
      <td>{{ trade.quantity }}</td>
    </tr>
    {% endfor %}
  </table>
</section>
{% endif %}

<footer>
  <p><em>Rapport généré par FinWiz - {{ consolidation_date }}</em></p>
</footer>
{% endblock %}
```

### 6. CrewAI Flow Integration

Flow orchestrates concurrent crew execution and calls Python consolidation.

#### Flow State Model

```python
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

class ReportAggregationState(BaseModel):
    """Structured state for report aggregation flow."""
    session_id: str

    # Crew execution tracking
    crew_export_paths: Dict[str, List[str]] = {}
    crew_html_paths: Dict[str, List[str]] = {}
    crew_execution_status: Dict[str, str] = {}

    # Consolidation results
    consolidated_json_path: Optional[str] = None
    final_report_path: Optional[str] = None

    # Error tracking
    errors: List[str] = []
```

#### Flow Implementation

```python
from crewai.flow import Flow, listen, start, and_
from pathlib import Path
import os

class ReportAggregationFlow(Flow[ReportAggregationState]):
    """Flow for concurrent crew execution and report aggregation."""

    @start()
    def initialize_flow(self) -> dict[str, Any]:
        """Initialize flow with session ID and output directories."""
        import uuid

        session_id = str(uuid.uuid4())
        self.state.session_id = session_id

        # Create output directory structure
        output_dir = Path(f"output/reports/{session_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        return {"session_id": session_id, "output_dir": str(output_dir)}

    # PHASE 1: Concurrent Analysis Crews
    @listen("initialize_flow")
    def execute_stock_crew(self, init_data: dict) -> dict[str, Any]:
        """Execute stock crew for each stock ticker."""
        from finwiz.crews.stock_crew.stock_crew import StockCrew

        tickers = self._get_stock_tickers()
        export_paths = []
        html_paths = []

        for ticker in tickers:
            try:
                # Execute crew
                crew = StockCrew()
                result = crew.crew().kickoff(inputs={"ticker": ticker})

                # Generate HTML from JSON export
                export_path = self._get_export_path("stock_crew", ticker)
                html_path = self._generate_html_report("stock_crew", export_path)

                export_paths.append(str(export_path))
                html_paths.append(html_path)

            except Exception as e:
                logger.error(f"Stock crew failed for {ticker}: {e}")
                self.state.errors.append(f"stock_crew:{ticker}:{str(e)}")

        self.state.crew_export_paths["stock_crew"] = export_paths
        self.state.crew_html_paths["stock_crew"] = html_paths
        self.state.crew_execution_status["stock_crew"] = (
            "completed" if export_paths else "failed"
        )

        return {"crew": "stock_crew", "exports": export_paths}
```

    @listen("initialize_flow")
    def execute_etf_crew(self, init_data: dict) -> dict[str, Any]:
        """Execute ETF crew for each ETF ticker."""
        from finwiz.crews.etf_crew.etf_crew import EtfCrew

        tickers = self._get_etf_tickers()
        export_paths = []
        html_paths = []

        for ticker in tickers:
            try:
                crew = EtfCrew()
                result = crew.crew().kickoff(inputs={"ticker": ticker})

                export_path = self._get_export_path("etf_crew", ticker)
                html_path = self._generate_html_report("etf_crew", export_path)

                export_paths.append(str(export_path))
                html_paths.append(html_path)

            except Exception as e:
                logger.error(f"ETF crew failed for {ticker}: {e}")
                self.state.errors.append(f"etf_crew:{ticker}:{str(e)}")

        self.state.crew_export_paths["etf_crew"] = export_paths
        self.state.crew_html_paths["etf_crew"] = html_paths
        self.state.crew_execution_status["etf_crew"] = (
            "completed" if export_paths else "failed"
        )

        return {"crew": "etf_crew", "exports": export_paths}

    @listen("initialize_flow")
    def execute_crypto_crew(self, init_data: dict) -> dict[str, Any]:
        """Execute crypto crew for each crypto ticker."""
        from finwiz.crews.crypto_crew.crypto_crew import CryptoCrew

        tickers = self._get_crypto_tickers()
        export_paths = []
        html_paths = []

        for ticker in tickers:
            try:
                crew = CryptoCrew()
                result = crew.crew().kickoff(inputs={"ticker": ticker})

                export_path = self._get_export_path("crypto_crew", ticker)
                html_path = self._generate_html_report("crypto_crew", export_path)

                export_paths.append(str(export_path))
                html_paths.append(html_path)

            except Exception as e:
                logger.error(f"Crypto crew failed for {ticker}: {e}")
                self.state.errors.append(f"crypto_crew:{ticker}:{str(e)}")

        self.state.crew_export_paths["crypto_crew"] = export_paths
        self.state.crew_html_paths["crypto_crew"] = html_paths
        self.state.crew_execution_status["crypto_crew"] = (
            "completed" if export_paths else "failed"
        )

        return {"crew": "crypto_crew", "exports": export_paths}

    @listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew"))
    def execute_deep_analysis_crew(self, *holdings_results) -> dict[str, Any]:
        """Execute deep analysis crew for underperforming holdings.

        Depends on holdings analysis to identify which assets need deep analysis.
        """
        from finwiz.crews.deep_analysis.deep_analysis import DeepAnalysisCrew

        # Read holdings analysis results to find underperformers (grade < B)
        underperforming_tickers = self._identify_underperforming_holdings()
        export_paths = []
        html_paths = []

        for ticker, asset_class in underperforming_tickers:
            try:
                crew = DeepAnalysisCrew()
                result = crew.crew().kickoff(inputs={
                    "ticker": ticker,
                    "asset_class": asset_class
                })

                export_path = self._get_export_path("deep_analysis_crew", ticker)
                html_path = self._generate_html_report("deep_analysis_crew", export_path)

                export_paths.append(str(export_path))
                html_paths.append(html_path)

            except Exception as e:
                logger.error(f"Deep analysis crew failed for {ticker}: {e}")
                self.state.errors.append(f"deep_analysis_crew:{ticker}:{str(e)}")

        self.state.crew_export_paths["deep_analysis_crew"] = export_paths
        self.state.crew_html_paths["deep_analysis_crew"] = html_paths
        self.state.crew_execution_status["deep_analysis_crew"] = (
            "completed" if export_paths else "failed"
        )

        return {"crew": "deep_analysis_crew", "exports": export_paths}

    @listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew"))
    def execute_discovery_crew(self, *holdings_results) -> dict[str, Any]:
        """Execute discovery crew to find A+ opportunities.

        Depends on holdings analysis to understand current portfolio context
        and find complementary opportunities.
        """
        from finwiz.crews.investment_discovery_crew.investment_discovery_crew import InvestmentDiscoveryCrew

        try:
            crew = InvestmentDiscoveryCrew()
            result = crew.crew().kickoff(inputs={
                "session_id": self.state.session_id
            })

            export_path = self._get_export_path("discovery_crew", "discovery")
            html_path = self._generate_html_report("discovery_crew", export_path)

            self.state.crew_export_paths["discovery_crew"] = [str(export_path)]
            self.state.crew_html_paths["discovery_crew"] = [html_path]
            self.state.crew_execution_status["discovery_crew"] = "completed"

            return {"crew": "discovery_crew", "exports": [str(export_path)]}

        except Exception as e:
            logger.error(f"Discovery crew failed: {e}")
            self.state.errors.append(f"discovery_crew:{str(e)}")
            self.state.crew_execution_status["discovery_crew"] = "failed"
            return {"crew": "discovery_crew", "exports": []}

    # PHASE 2: Rebalancing (Waits for ALL analysis to complete)
    @listen(and_(
        "execute_stock_crew",
        "execute_etf_crew",
        "execute_crypto_crew",
        "execute_deep_analysis_crew",
        "execute_discovery_crew"
    ))
    def execute_rebalancing_crew(self, *analysis_results) -> dict[str, Any]:
        """Execute rebalancing crew with ALL analysis results.

        This crew sees:
        - Current holdings (stock/etf/crypto exports)
        - Deep analysis results (detailed grades)
        - Discovery opportunities (A+ alternatives)
        """
        from finwiz.crews.portfolio_rebalancing_crew.portfolio_rebalancing_crew import PortfolioRebalancingCrew

        try:
            # Prepare inputs with ALL analysis file paths
            rebalancing_inputs = {
                "session_id": self.state.session_id,
                "stock_exports": self.state.crew_export_paths.get("stock_crew", []),
                "etf_exports": self.state.crew_export_paths.get("etf_crew", []),
                "crypto_exports": self.state.crew_export_paths.get("crypto_crew", []),
                "deep_analysis_exports": self.state.crew_export_paths.get("deep_analysis_crew", []),
                "discovery_export": self.state.crew_export_paths.get("discovery_crew", [None])[0]
            }

            crew = PortfolioRebalancingCrew()
            result = crew.crew().kickoff(inputs=rebalancing_inputs)

            export_path = self._get_export_path("rebalancing_crew", "rebalancing")
            html_path = self._generate_html_report("rebalancing_crew", export_path)

            self.state.crew_export_paths["rebalancing_crew"] = [str(export_path)]
            self.state.crew_html_paths["rebalancing_crew"] = [html_path]
            self.state.crew_execution_status["rebalancing_crew"] = "completed"

            return {"crew": "rebalancing_crew", "exports": [str(export_path)]}

        except Exception as e:
            logger.error(f"Rebalancing crew failed: {e}")
            self.state.errors.append(f"rebalancing_crew:{str(e)}")
            self.state.crew_execution_status["rebalancing_crew"] = "failed"
            return {"crew": "rebalancing_crew", "exports": []}

    # PHASE 3: Python Consolidation (NO AI)
    @listen("execute_rebalancing_crew")
    def consolidate_reports(self, rebalancing_result: dict) -> dict[str, Any]:
        """Consolidate all crew reports using Python (NO AI)."""

        consolidator = ReportConsolidator(
            session_id=self.state.session_id,
            output_dir=Path(f"output/reports/{self.state.session_id}")
        )

        # Consolidate all crew exports
        consolidated = consolidator.consolidate_reports(
            crew_export_paths=self.state.crew_export_paths
        )

        # Save consolidated JSON path
        consolidated_path = f"output/reports/{self.state.session_id}/consolidated_report.json"
        self.state.consolidated_json_path = consolidated_path

        return {
            "consolidated_path": consolidated_path,
            "consolidated_data": consolidated.model_dump()
        }

    # PHASE 4: Final Report Generation (Python Template)
    @listen("consolidate_reports")
    def generate_final_report(self, consolidation_data: dict) -> dict[str, Any]:
        """Generate final French report using Python template (NO AI)."""

        # Load consolidated data
        consolidated_path = Path(consolidation_data["consolidated_path"])
        consolidated_json = json.loads(consolidated_path.read_text(encoding="utf-8"))
        consolidated = ConsolidatedReportExport.model_validate(consolidated_json)

        # Generate final HTML report
        generator = FinalReportGenerator()
        final_report_path = Path(f"output/reports/{self.state.session_id}/final_report.html")

        report_path = generator.generate_final_report(
            consolidated_data=consolidated,
            output_path=final_report_path
        )

        self.state.final_report_path = report_path

        return {
            "final_report_path": report_path,
            "session_id": self.state.session_id
        }

    # Helper methods
    def _get_export_path(self, crew_name: str, ticker: str) -> Path:
        """Get export file path for crew and ticker."""
        return Path(
            f"output/reports/{self.state.session_id}/{crew_name}/{ticker}_export.json"
        )

    def _generate_html_report(self, crew_name: str, export_path: Path) -> str:
        """Generate HTML report from JSON export."""
        generator = HTMLReportGenerator()

        # Load export data
        export_data = json.loads(export_path.read_text(encoding="utf-8"))

        # Generate HTML
        html_path = export_path.with_suffix(".html")
        return generator.generate_crew_report(
            crew_name=crew_name,
            export_data=export_data,
            output_path=html_path
        )

```


## Data Models

### File Structure

```

output/reports/{session_id}/
├── stock_crew/
│ ├── AAPL_export.json
│ ├── AAPL_report.html
│ ├── MSFT_export.json
│ └── MSFT_report.html
├── etf_crew/
│ ├── SPY_export.json
│ ├── SPY_report.html
│ ├── QQQ_export.json
│ └── QQQ_report.html
├── crypto_crew/
│ ├── BTC_export.json
│ ├── BTC_report.html
│ ├── ETH_export.json
│ └── ETH_report.html
├── deep_analysis_crew/
│ ├── AAPL_deep_export.json
│ └── AAPL_deep_report.html
├── discovery_crew/
│ ├── discovery_export.json
│ └── discovery_report.html
├── rebalancing_crew/
│ ├── rebalancing_export.json
│ └── rebalancing_report.html
├── consolidated_report.json
└── final_report.html

````

### Report Manifest

```python
class ReportManifest(BaseModel):
    """Manifest tracking all generated reports."""
    session_id: str
    generation_date: datetime

    reports: List[ReportEntry] = []

    class ReportEntry(BaseModel):
        crew_name: str
        ticker: str
        asset_class: str
        status: str  # "completed" | "failed"
        json_path: str
        html_path: str
        error_message: Optional[str] = None

# Save manifest
manifest_path = Path(f"output/reports/{session_id}/manifest.json")
manifest = ReportManifest(session_id=session_id, reports=report_entries)
manifest_path.write_text(manifest.model_dump_json(indent=2))
````

## Error Handling

### Graceful Degradation Strategy

```python
class ErrorHandler:
    """Handle crew failures gracefully."""

    def handle_crew_failure(
        self,
        crew_name: str,
        ticker: str,
        error: Exception
    ) -> None:
        """Log error and continue with other crews."""
        logger.error(
            f"Crew {crew_name} failed for {ticker}: {error}",
            exc_info=True
        )

        # Track error in state
        self.state.errors.append({
            "crew": crew_name,
            "ticker": ticker,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        })

        # Mark crew as failed
        self.state.crew_execution_status[crew_name] = "failed"

    def generate_error_placeholder(
        self,
        crew_name: str,
        ticker: str
    ) -> dict:
        """Generate placeholder data for failed crew."""
        return {
            "crew_name": crew_name,
            "ticker": ticker,
            "status": "failed",
            "error_message": "Analysis failed - see logs for details",
            "recommendation": "HOLD",
            "grade": "N/A",
            "composite_score": 0.0
        }
```

### Validation Error Recovery

```python
def validate_and_recover(
    data: dict,
    schema_class: type[BaseModel]
) -> Optional[BaseModel]:
    """Validate data and attempt recovery on failure."""
    try:
        return schema_class.model_validate(data)
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")

        # Attempt to fix common issues
        if "grade" in str(e):
            data["grade"] = "N/A"
        if "composite_score" in str(e):
            data["composite_score"] = 0.0

        # Retry validation
        try:
            return schema_class.model_validate(data)
        except ValidationError:
            logger.error("Recovery failed - returning None")
            return None
```

### Missing Report Handling

```python
def handle_missing_report(crew_name: str) -> str:
    """Generate placeholder section for missing crew report."""
    return f"""
    <section class="missing-report">
        <h2>⚠️ {crew_name} - Analyse Non Disponible</h2>
        <p>L'analyse de {crew_name} n'a pas pu être complétée.</p>
        <p>Consultez les logs pour plus de détails.</p>
    </section>
    """
```

## Batch Processing Architecture

### Overview

The batch processing architecture dramatically improves Deep Analysis performance by **pre-fetching all data in batch API calls** before crew execution. This eliminates API latency during crew execution and reduces total time from 3-6 hours to 30-60 minutes for 66 holdings (80%+ improvement).

### Design Principles

1. **Batch Data Pre-Fetching**: Fetch ALL ticker data upfront in single batch API calls
2. **Pre-Fetched Data Injection**: Pass pre-fetched data to crews to eliminate API latency
3. **Sequential Crew Execution**: Crews run sequentially but with zero API wait time
4. **Intelligent Rate Limiting**: Respect API limits during batch data fetching
5. **Graceful Degradation**: Handle partial data fetch failures without breaking analysis
6. **Backward Compatibility**: Maintain single-ticker mode for non-portfolio analysis

### Batch Execution Flow

```
Portfolio Holdings (66 tickers)
         ↓
┌─────────────────────────────────────────────────────┐
│  PHASE 1: Batch Data Pre-Fetching                  │
│  (ONE-TIME UPFRONT)                                 │
│                                                      │
│  Fetch ALL data for ALL 66 tickers:                │
│  ┌────────────────────────────────────┐            │
│  │ Yahoo Finance Batch Download       │            │
│  │ yf.download(all_tickers, period)   │            │
│  │ → ONE API call for 66 tickers!     │            │
│  └────────────────────────────────────┘            │
│                                                      │
│  ┌────────────────────────────────────┐            │
│  │ Alpha Vantage Batch Queue          │            │
│  │ Queue 66 requests with rate limit  │            │
│  │ → 66 calls in ~13 minutes          │            │
│  └────────────────────────────────────┘            │
│                                                      │
│  ┌────────────────────────────────────┐            │
│  │ Store in DataCache                 │            │
│  │ {ticker: {yf_data, av_data, ...}}  │            │
│  └────────────────────────────────────┘            │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│  PHASE 2: Sequential Crew Execution                │
│  (NO API CALLS - READ FROM CACHE)                  │
│                                                      │
│  For each ticker in 66 tickers:                    │
│    ┌──────────────────────────────┐                │
│    │ DeepAnalysisCrew(ticker)     │                │
│    │ - Read from DataCache        │                │
│    │ - No API latency!            │                │
│    │ - Fast analysis (10-20s)     │                │
│    └──────────────────────────────┘                │
│                                                      │
│  Total: 66 × 15s = 16.5 minutes                    │
│  (vs 66 × 60s = 66 minutes sequential)             │
└─────────────────────────────────────────────────────┘
         ↓
[Aggregate all results]
         ↓
[Generate consolidated report]
```

### Batch Data Pre-Fetcher

The Data Pre-Fetcher fetches ALL data for ALL tickers upfront in batch API calls:

```python
from typing import List, Dict, Any
import yfinance as yf
import asyncio
import aiohttp
from pathlib import Path
import json

class BatchDataPreFetcher:
    """Pre-fetch all data for all tickers in batch API calls."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cache_dir = Path(f"cache/batch_data/{session_id}")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    def prefetch_all_data(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Pre-fetch all data for all tickers.

        Args:
            tickers: List of all ticker symbols to analyze

        Returns:
            Dict mapping ticker to all pre-fetched data
        """
        logger.info(f"Starting batch data pre-fetch for {len(tickers)} tickers")
        start_time = time.time()

        # Step 1: Batch fetch Yahoo Finance data (ONE API call!)
        logger.info("Fetching Yahoo Finance data in batch...")
        yf_data = self._fetch_yahoo_finance_batch(tickers)
        logger.info(f"Yahoo Finance batch fetch completed in {time.time() - start_time:.1f}s")

        # Step 2: Batch fetch Alpha Vantage data (with rate limiting)
        logger.info("Fetching Alpha Vantage data with rate limiting...")
        av_start = time.time()
        av_data = asyncio.run(self._fetch_alpha_vantage_batch(tickers))
        logger.info(f"Alpha Vantage batch fetch completed in {time.time() - av_start:.1f}s")

        # Step 3: Combine all data
        combined_data = {}
        for ticker in tickers:
            combined_data[ticker] = {
                "ticker": ticker,
                "yahoo_finance": yf_data.get(ticker, {}),
                "alpha_vantage": av_data.get(ticker, {}),
                "fetch_timestamp": datetime.now().isoformat()
            }

        # Step 4: Save to cache
        self._save_to_cache(combined_data)

        total_time = time.time() - start_time
        logger.info(f"Batch data pre-fetch completed in {total_time:.1f}s ({total_time/len(tickers):.1f}s per ticker)")

        return combined_data

    def _fetch_yahoo_finance_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """Fetch Yahoo Finance data for all tickers in ONE API call."""
        try:
            logger.info(f"Downloading data for {len(tickers)} tickers from Yahoo Finance...")

            # Single batch API call for ALL tickers
            data = yf.download(
                tickers=' '.join(tickers),
                period="1y",
                group_by='ticker',
                auto_adjust=True,
                threads=True,  # Parallel download
                progress=False
            )

            # Also fetch ticker info
            tickers_obj = yf.Tickers(' '.join(tickers))

            results = {}
            for ticker in tickers:
                try:
                    # Historical data
                    if len(tickers) == 1:
                        ticker_data = data
                    else:
                        ticker_data = data[ticker]

                    # Ticker info
                    ticker_info = tickers_obj.tickers[ticker].info

                    results[ticker] = {
                        "symbol": ticker,
                        "name": ticker_info.get("shortName", "N/A"),
                        "sector": ticker_info.get("sector", "N/A"),
                        "industry": ticker_info.get("industry", "N/A"),
                        "current_price": ticker_info.get("currentPrice", ticker_info.get("regularMarketPrice", "N/A")),
                        "market_cap": ticker_info.get("marketCap", "N/A"),
                        "pe_ratio": ticker_info.get("trailingPE", "N/A"),
                        "dividend_yield": ticker_info.get("dividendYield", "N/A"),
                        "52wk_high": float(ticker_data['High'].max()) if not ticker_data.empty else "N/A",
                        "52wk_low": float(ticker_data['Low'].min()) if not ticker_data.empty else "N/A",
                        "avg_volume": float(ticker_data['Volume'].mean()) if not ticker_data.empty else "N/A",
                        "historical_data_points": len(ticker_data) if not ticker_data.empty else 0,
                    }

                    logger.debug(f"Successfully fetched Yahoo Finance data for {ticker}")

                except Exception as e:
                    logger.warning(f"Failed to process Yahoo Finance data for {ticker}: {e}")
                    results[ticker] = {"error": str(e)}

            return results

        except Exception as e:
            logger.error(f"Yahoo Finance batch download failed: {e}")
            return {ticker: {"error": str(e)} for ticker in tickers}

    async def _fetch_alpha_vantage_batch(self, tickers: List[str]) -> Dict[str, Any]:
        """Fetch Alpha Vantage data with intelligent rate limiting."""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not set, skipping")
            return {ticker: {"error": "API key not set"} for ticker in tickers}

        # Rate limit: 5 calls/minute (free tier)
        rate_limit = 5
        delay_between_calls = 60 / rate_limit  # 12 seconds

        results = {}

        async with aiohttp.ClientSession() as session:
            for i, ticker in enumerate(tickers, 1):
                try:
                    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={self.alpha_vantage_key}"

                    async with session.get(url, timeout=15) as response:
                        data = await response.json()

                        if "Symbol" in data:
                            results[ticker] = {
                                "symbol": ticker,
                                "name": data.get("Name", "N/A"),
                                "sector": data.get("Sector", "N/A"),
                                "industry": data.get("Industry", "N/A"),
                                "market_cap": data.get("MarketCapitalization", "N/A"),
                                "pe_ratio": data.get("PERatio", "N/A"),
                                "eps": data.get("EPS", "N/A"),
                                "revenue_ttm": data.get("RevenueTTM", "N/A"),
                                "profit_margin": data.get("ProfitMargin", "N/A"),
                            }
                            logger.debug(f"Successfully fetched Alpha Vantage data for {ticker} ({i}/{len(tickers)})")
                        else:
                            results[ticker] = {"error": "No data available"}

                    # Rate limiting delay (except for last ticker)
                    if i < len(tickers):
                        logger.debug(f"Rate limit delay: {delay_between_calls:.1f}s before next request")
                        await asyncio.sleep(delay_between_calls)

                except Exception as e:
                    logger.warning(f"Failed to fetch Alpha Vantage data for {ticker}: {e}")
                    results[ticker] = {"error": str(e)}

        return results

    def _save_to_cache(self, data: Dict[str, Dict[str, Any]]) -> None:
        """Save pre-fetched data to cache."""
        cache_file = self.cache_dir / "batch_data.json"
        cache_file.write_text(json.dumps(data, indent=2, default=str))
        logger.info(f"Batch data saved to cache: {cache_file}")

    def load_from_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-fetched data from cache."""
        cache_file = self.cache_dir / "batch_data.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            logger.info(f"Loaded batch data from cache: {cache_file}")
            return data
        return {}
```

### Modified Tools for Pre-Fetched Data

Tools are modified to accept pre-fetched data instead of making API calls:

```python
class YahooFinanceTickerInfoTool(BaseTool):
    """Get ticker info - supports pre-fetched data."""

    name: str = "Yahoo Finance Ticker Info Tool"
    description: str = "Get ticker information (uses pre-fetched data if available)"

    def _run(self, ticker: str, prefetched_data: Optional[Dict] = None) -> dict:
        """Execute ticker info lookup.

        Args:
            ticker: Ticker symbol
            prefetched_data: Pre-fetched data from batch API call (optional)

        Returns:
            Ticker information
        """
        # Use pre-fetched data if available
        if prefetched_data and "yahoo_finance" in prefetched_data:
            logger.debug(f"Using pre-fetched Yahoo Finance data for {ticker}")
            return prefetched_data["yahoo_finance"]

        # Fallback to live API call (single-ticker mode)
        logger.debug(f"Fetching live Yahoo Finance data for {ticker}")
        ticker_data = yf.Ticker(ticker)
        info = ticker_data.info

        return {
            "symbol": ticker,
            "name": info.get("shortName", "N/A"),
            "current_price": info.get("currentPrice", "N/A"),
            # ... rest of fields
        }

class AlphaVantageCompanyOverviewTool(BaseTool):
    """Get company overview - supports pre-fetched data."""

    name: str = "Alpha Vantage Company Overview"
    description: str = "Get company overview (uses pre-fetched data if available)"

    def _run(self, ticker: str, prefetched_data: Optional[Dict] = None) -> str:
        """Execute company overview lookup.

        Args:
            ticker: Ticker symbol
            prefetched_data: Pre-fetched data from batch API call (optional)

        Returns:
            Company overview data
        """
        # Use pre-fetched data if available
        if prefetched_data and "alpha_vantage" in prefetched_data:
            logger.debug(f"Using pre-fetched Alpha Vantage data for {ticker}")
            return json.dumps(prefetched_data["alpha_vantage"], indent=2)

        # Fallback to live API call (single-ticker mode)
        logger.debug(f"Fetching live Alpha Vantage data for {ticker}")
        # ... existing API call logic
```

### Deep Analysis Crew with Pre-Fetched Data

The Deep Analysis crew accepts pre-fetched data to eliminate API latency:

```python
from typing import Optional, Dict, Any
from crewai import Agent, Task, Crew, agent, task, crew

class DeepAnalysisCrew:
    """Deep analysis crew with pre-fetched data support."""

    def __init__(self):
        self.agents_config = self._load_agents_config()
        self.tasks_config = self._load_tasks_config()
        self.prefetched_data = None

    def set_prefetched_data(self, data: Dict[str, Any]) -> None:
        """Set pre-fetched data for this crew execution."""
        self.prefetched_data = data
        logger.debug(f"Pre-fetched data set for crew")

    def get_tools_with_prefetched_data(self, asset_class: str) -> list:
        """Get tools configured to use pre-fetched data."""
        # Create tool instances with pre-fetched data injected
        tools = [
            YahooFinanceTickerInfoTool(),  # Modified to accept prefetched_data
            AlphaVantageCompanyOverviewTool(),  # Modified to accept prefetched_data
            TickerValidationTool(),
            # ... other tools
        ]

        # Inject pre-fetched data into tool context
        for tool in tools:
            if hasattr(tool, 'set_prefetched_data'):
                tool.set_prefetched_data(self.prefetched_data)

        return tools

    @agent
    def analyst(self) -> Agent:
        """Analyst configured to use pre-fetched data."""
        return Agent(
            config=self.agents_config["analyst"],
            tools=self.get_tools_with_prefetched_data("stock"),
            reasoning=False,  # Disabled for performance
            allow_delegation=False,
            verbose=True
        )

    @task
    def analysis_task(self) -> Task:
        """Analysis task using pre-fetched data."""
        return Task(
            description="""
            Perform deep analysis on the provided ticker using PRE-FETCHED DATA.

            IMPORTANT: All data has been pre-fetched. Tools will return cached data instantly.
            No API calls will be made during this analysis.

            Steps:
            1. Validate ticker symbol
            2. Analyze fundamental data (from pre-fetched cache)
            3. Calculate risk metrics
            4. Generate grade and recommendation
            5. Create DeepAnalysisCrewExport object

            Expected execution time: 10-20 seconds (no API latency)
            """,
            expected_output="DeepAnalysisCrewExport object",
            agent=self.analyst(),
            async_execution=False
        )
```

### Flow with Batch Data Pre-Fetching

The Flow pre-fetches all data upfront, then executes crews sequentially with zero API latency:

```python
from typing import List, Tuple, Dict, Any
import time

class ReportAggregationFlow(Flow[ReportAggregationState]):
    """Flow with batch data pre-fetching."""

    def __init__(self):
        super().__init__()
        self.batch_prefetch_enabled = os.getenv("BATCH_PREFETCH_ENABLED", "true").lower() == "true"
        self.prefetched_data = {}

    @listen(and_("execute_stock_crew", "execute_etf_crew", "execute_crypto_crew"))
    def execute_deep_analysis_with_prefetch(self, *holdings_results) -> dict[str, Any]:
        """Execute deep analysis with batch data pre-fetching."""
        # Identify underperforming holdings
        underperformers = self._identify_underperforming_holdings()

        if not underperformers:
            logger.info("No underperforming holdings found")
            return {"crew": "deep_analysis_crew", "exports": []}

        tickers = [ticker for ticker, _ in underperformers]
        logger.info(f"Starting deep analysis for {len(tickers)} underperforming holdings")

        # PHASE 1: Batch Data Pre-Fetching
        if self.batch_prefetch_enabled:
            logger.info("=" * 80)
            logger.info("PHASE 1: BATCH DATA PRE-FETCHING")
            logger.info("=" * 80)

            prefetcher = BatchDataPreFetcher(self.state.session_id)
            self.prefetched_data = prefetcher.prefetch_all_data(tickers)

            logger.info(f"Pre-fetched data for {len(self.prefetched_data)} tickers")
            logger.info("=" * 80)

        # PHASE 2: Sequential Crew Execution (with zero API latency)
        logger.info("=" * 80)
        logger.info("PHASE 2: SEQUENTIAL CREW EXECUTION (NO API CALLS)")
        logger.info("=" * 80)

        start_time = time.time()
        all_exports = []
        successful = 0
        failed = 0

        for i, (ticker, asset_class) in enumerate(underperformers, 1):
            ticker_start = time.time()

            try:
                logger.info(f"Analyzing {ticker} ({i}/{len(underperformers)})...")

                # Create crew with pre-fetched data
                crew = DeepAnalysisCrew()
                if ticker in self.prefetched_data:
                    crew.set_prefetched_data(self.prefetched_data[ticker])

                # Execute crew (no API calls - reads from pre-fetched data)
                result = crew.crew().kickoff(inputs={
                    "ticker": ticker,
                    "asset_class": asset_class,
                    "session_id": self.state.session_id
                })

                # Collect export path
                export_path = self._get_export_path("deep_analysis_crew", ticker)
                if export_path.exists():
                    all_exports.append(str(export_path))
                    successful += 1

                    ticker_duration = time.time() - ticker_start
                    logger.info(f"✅ {ticker} completed in {ticker_duration:.1f}s")
                else:
                    failed += 1
                    logger.warning(f"❌ {ticker} failed - export not found")

            except Exception as e:
                failed += 1
                logger.error(f"❌ {ticker} failed: {e}")
                self.state.errors.append(f"deep_analysis:{ticker}:{str(e)}")

        # Log performance metrics
        total_duration = time.time() - start_time
        self._log_prefetch_performance(
            total_tickers=len(underperformers),
            successful=successful,
            failed=failed,
            total_duration=total_duration
        )

        # Update state
        self.state.crew_export_paths["deep_analysis_crew"] = all_exports
        self.state.crew_execution_status["deep_analysis_crew"] = (
            "completed" if all_exports else "failed"
        )

        return {"crew": "deep_analysis_crew", "exports": all_exports}

    def _log_prefetch_performance(
        self,
        total_tickers: int,
        successful: int,
        failed: int,
        total_duration: float
    ) -> None:
        """Log batch pre-fetch performance metrics."""
        avg_time_per_ticker = total_duration / total_tickers if total_tickers > 0 else 0

        # Estimate sequential execution time WITHOUT pre-fetching (assume 60s per ticker)
        estimated_sequential_time = total_tickers * 60
        time_savings = estimated_sequential_time - total_duration
        time_savings_pct = (time_savings / estimated_sequential_time) * 100 if estimated_sequential_time > 0 else 0

        logger.info("=" * 80)
        logger.info("BATCH PRE-FETCH PERFORMANCE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tickers analyzed: {total_tickers}")
        logger.info(f"Successful: {successful} ({successful/total_tickers*100:.1f}%)")
        logger.info(f"Failed: {failed} ({failed/total_tickers*100:.1f}%)")
        logger.info(f"Total execution time: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        logger.info(f"Average time per ticker: {avg_time_per_ticker:.1f}s")
        logger.info(f"Estimated time WITHOUT pre-fetching: {estimated_sequential_time:.1f}s ({estimated_sequential_time/60:.1f} minutes)")
        logger.info(f"Time savings: {time_savings:.1f}s ({time_savings/60:.1f} minutes, {time_savings_pct:.1f}%)")
        logger.info("=" * 80)

        # Save metrics to file
        metrics_path = Path(f"output/reports/{self.state.session_id}/batch_prefetch_metrics.json")
        metrics_data = {
            "approach": "batch_data_prefetching",
            "total_tickers": total_tickers,
            "successful": successful,
            "failed": failed,
            "total_duration_seconds": total_duration,
            "avg_time_per_ticker_seconds": avg_time_per_ticker,
            "estimated_sequential_time_seconds": estimated_sequential_time,
            "time_savings_seconds": time_savings,
            "time_savings_percentage": time_savings_pct,
            "prefetch_enabled": self.batch_prefetch_enabled
        }
        metrics_path.write_text(json.dumps(metrics_data, indent=2))
        logger.info(f"Performance metrics saved to: {metrics_path}")
```

### Rate Limiting Strategy

```python
class RateLimiter:
    """Intelligent rate limiter for batch API calls."""

    def __init__(self, provider: str):
        self.provider = provider
        self.limits = {
            "yahoo_finance": {"rpm": None, "rps": 10},  # 10 requests/second
            "alpha_vantage_free": {"rpm": 5, "rps": None},  # 5 calls/minute
            "alpha_vantage_premium": {"rpm": 75, "rps": None},  # 75 calls/minute
            "twelve_data_free": {"rpm": 8, "rps": None},  # 8 calls/minute
            "twelve_data_premium": {"rpm": 800, "rps": None},  # 800 calls/minute
        }

        self.last_call_time = 0
        self.call_count = 0
        self.minute_start = time.time()

    async def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        limits = self.limits.get(self.provider, {})

        # Check requests per second limit
        if limits.get("rps"):
            min_delay = 1.0 / limits["rps"]
            elapsed = time.time() - self.last_call_time
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)

        # Check requests per minute limit
        if limits.get("rpm"):
            # Reset counter if minute has passed
            if time.time() - self.minute_start >= 60:
                self.call_count = 0
                self.minute_start = time.time()

            # Wait if limit reached
            if self.call_count >= limits["rpm"]:
                wait_time = 60 - (time.time() - self.minute_start)
                if wait_time > 0:
                    logger.info(f"Rate limit reached for {self.provider}, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self.call_count = 0
                    self.minute_start = time.time()

        self.last_call_time = time.time()
        self.call_count += 1
```

### Performance Targets

**Expected Performance Improvements:**

| Metric                  | Sequential (No Pre-Fetch) | With Batch Pre-Fetch     | Improvement    |
| ----------------------- | ------------------------- | ------------------------ | -------------- |
| API calls per ticker    | 5-10 individual calls     | 0 (pre-fetched)          | 100% reduction |
| Time per ticker         | 60s (with API latency)    | 15s (no API latency)     | 75% faster     |
| Total time (66 tickers) | 66 minutes                | 30 minutes               | 55% faster     |
| Batch pre-fetch time    | N/A                       | 13-15 minutes (one-time) | Amortized      |
| Memory usage            | Low                       | Low                      | Same           |
| Success rate            | 95%                       | 95%                      | Maintained     |

**Breakdown for 66 Tickers:**

1. **Batch Pre-Fetch Phase** (one-time upfront):

   - Yahoo Finance batch download: ~30 seconds (ONE API call for all 66 tickers)
   - Alpha Vantage queue (5 calls/min): ~13 minutes (66 calls with rate limiting)
   - **Total pre-fetch time**: ~13-15 minutes

2. **Crew Execution Phase** (sequential, no API calls):

   - Per ticker: ~15 seconds (no API latency)
   - **Total execution time**: 66 × 15s = 16.5 minutes

3. **Total Time**: 13-15 min (pre-fetch) + 16.5 min (execution) = **30 minutes**
   - vs 66 minutes without pre-fetching
   - **Time savings**: 36 minutes (55% faster)

**Configuration:**

```bash
# Enable batch pre-fetching (default: true)
BATCH_PREFETCH_ENABLED=true

# Alpha Vantage rate limit (calls per minute)
ALPHA_VANTAGE_RATE_LIMIT=5  # Free tier
# ALPHA_VANTAGE_RATE_LIMIT=75  # Premium tier (much faster pre-fetch)
```

**Memory Considerations:**

- Pre-fetched data cache: ~10-50 MB for 66 tickers
- Single crew instance: ~200-500 MB
- Total memory usage: ~500 MB (very low)
- Recommended system RAM: 4 GB minimum, 8 GB optimal

**Scalability:**

- **Premium Alpha Vantage** (75 calls/min): Pre-fetch time reduces to ~1 minute

  - Total time: 1 min (pre-fetch) + 16.5 min (execution) = **17.5 minutes**
  - **Time savings**: 48.5 minutes (73% faster)

- **Large portfolios** (200+ tickers): Linear scaling
  - Pre-fetch: ~40 minutes (free tier) or ~3 minutes (premium)
  - Execution: 200 × 15s = 50 minutes
  - Still much faster than 200 × 60s = 200 minutes sequential

## Pure Python Architecture (Requirements 18-21)

### Overview

**Critical Design Decision**: Implement complete pure Python architecture that replaces AI crews with deterministic Python functions for 10-20x performance improvement.

**Requirements Coverage**:

- **Requirement 18**: Python-Based Scoring Engine for Deep Analysis
- **Requirement 19**: Jinja2 Templates for Deep Analysis Reports
- **Requirement 20**: Pure Python Architecture Implementation
- **Requirement 21**: Performance Optimization Configuration

**Rationale**: Current deep analysis uses 5 AI tasks with extensive LLM reasoning for calculations that are fundamentally deterministic (composite scores, grades, risk scores). Analysis shows AI provides minimal unique value beyond reformatting tool outputs into prose, while consuming 5-10 minutes and \$0.05-0.10 per ticker.

### Python-Based Scoring Engine for Deep Analysis (Requirement 18)

#### DeepAnalysisScorer Class

Pure Python class that performs all scoring calculations (Requirements 18.1-18.10): all scoring calculations deterministically:

```python
from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ScoringWeights:
    """Configurable weights for composite score calculation."""
    fundamental: float = 0.40
    technical: float = 0.30
    risk: float = 0.30

class DeepAnalysisScorer:
    """Deterministic scoring engine for deep analysis."""

    def __init__(self, weights: ScoringWeights = ScoringWeights()):
        self.weights = weights

        # Grade thresholds
        self.grade_thresholds = {
            0.90: "A+", 0.85: "A", 0.80: "A-",
            0.75: "B+", 0.70: "B", 0.65: "B-",
            0.60: "C+", 0.55: "C", 0.50: "C-",
            0.45: "D+", 0.40: "D", 0.35: "D-"
        }

    def calculate_composite_score(
        self,
        fundamental_metrics: Dict[str, Any],
        technical_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> float:
        """Calculate composite score using weighted formula.

        Formula: 40% fundamental + 30% technical + 30% risk (Requirement 18.2)

        Returns:
            Composite score (0.0-1.0)
        """
        fundamental_score = self._calculate_fundamental_score(fundamental_metrics)
        technical_score = self._calculate_technical_score(technical_metrics)
        risk_score = self._calculate_risk_score(risk_metrics)

        composite = (
            fundamental_score * self.weights.fundamental +
            technical_score * self.weights.technical +
            (1.0 - risk_score / 5.0) * self.weights.risk  # Invert risk (lower is better)
        )

        return max(0.0, min(1.0, composite))  # Clamp to [0.0, 1.0]

    def _calculate_fundamental_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate fundamental score from metrics.

        Scoring rules (Requirement 18.3):
        - ROE bonus: +0.2 if >20%, +0.1 if >15%
        - Debt penalty: -0.1 if debt/equity >0.5, -0.2 if >1.0
        - Growth bonus: +0.2 if revenue growth >15%, +0.1 if >10%

        Returns:
            Fundamental score (0.0-1.0)
        """
        base_score = 0.5

        # ROE bonus
        roe = metrics.get("roe", 0)
        if roe > 0.20:
            base_score += 0.2
        elif roe > 0.15:
            base_score += 0.1

        # Debt penalty
        debt_equity = metrics.get("debt_equity", 0)
        if debt_equity > 1.0:
            base_score -= 0.2
        elif debt_equity > 0.5:
            base_score -= 0.1

        # Growth bonus
        revenue_growth = metrics.get("revenue_growth", 0)
        if revenue_growth > 0.15:
            base_score += 0.2
        elif revenue_growth > 0.10:
            base_score += 0.1

        return max(0.0, min(1.0, base_score))

    def _calculate_technical_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate technical score from metrics.

        Scoring rules:
        - RSI analysis: +0.1 if 40-60 (neutral), -0.2 if <30 or >70
        - Trend analysis: +0.3 if strong uptrend (SMA crossover), -0.3 if downtrend

        Returns:
            Technical score (0.0-1.0)
        """
        base_score = 0.5

        # RSI analysis
        rsi = metrics.get("rsi", 50)
        if 40 <= rsi <= 60:
            base_score += 0.1
        elif rsi < 30 or rsi > 70:
            base_score -= 0.2

        # Trend analysis (SMA crossover)
        sma_50 = metrics.get("sma_50", 0)
        sma_200 = metrics.get("sma_200", 0)
        current_price = metrics.get("current_price", 0)

        if sma_50 > 0 and sma_200 > 0 and current_price > 0:
            if sma_50 > sma_200 and current_price > sma_50:
                base_score += 0.3  # Strong uptrend
            elif sma_50 < sma_200 and current_price < sma_50:
                base_score -= 0.3  # Downtrend

        return max(0.0, min(1.0, base_score))

    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate risk score (0-5 scale, higher = riskier).

        Scoring rules:
        - Base score: (volatility / 35) * 2.0
        - Drawdown penalty: (abs(max_drawdown) / 50) * 1.5
        - Beta adjustment: +0.5 if >1.5, -0.3 if <0.5

        Returns:
            Risk score (0.0-5.0)
        """
        # Base score from volatility
        volatility = metrics.get("volatility", 0.20)
        base_score = (volatility / 0.35) * 2.0

        # Drawdown penalty
        max_drawdown = abs(metrics.get("max_drawdown", 0))
        base_score += (max_drawdown / 0.50) * 1.5

        # Beta adjustment
        beta = metrics.get("beta", 1.0)
        if beta > 1.5:
            base_score += 0.5
        elif beta < 0.5:
            base_score -= 0.3

        return max(0.0, min(5.0, base_score))

    def assign_grade(self, composite_score: float) -> str:
        """Assign letter grade based on composite score.

        Thresholds (Requirement 18.6):
        - A+: ≥0.90, A: ≥0.85, A-: ≥0.80
        - B+: ≥0.75, B: ≥0.70, B-: ≥0.65
        - C+: ≥0.60, C: ≥0.55, C-: ≥0.50
        - D+: ≥0.45, D: ≥0.40, D-: ≥0.35, F: <0.35

        Returns:
            Letter grade (A+ to F)
        """
        for threshold, grade in sorted(self.grade_thresholds.items(), reverse=True):
            if composite_score >= threshold:
                return grade
        return "F"

    def generate_recommendation(
        self,
        grade: str,
        risk_score: float
    ) -> Tuple[str, str]:
        """Generate investment recommendation and rationale.

        Rules (Requirement 18.7):
        - BUY: grade in [A+, A, A-] AND risk_score ≤ 3.0
        - HOLD: grade in [B+, B] AND risk_score ≤ 3.5, OR grade in [B-, C+, C]
        - SELL: grade in [D+, D, D-, F] OR risk_score > 4.0

        Returns:
            Tuple of (recommendation, rationale)
        """
        if grade in ["A+", "A", "A-"] and risk_score <= 3.0:
            recommendation = "BUY"
            rationale = f"Strong fundamentals and technicals (Grade {grade}) with acceptable risk ({risk_score:.1f}/5.0)"
        elif grade in ["B+", "B"] and risk_score <= 3.5:
            recommendation = "HOLD"
            rationale = f"Good fundamentals (Grade {grade}) but monitor risk level ({risk_score:.1f}/5.0)"
        elif grade in ["B-", "C+", "C"]:
            recommendation = "HOLD"
            rationale = f"Average performance (Grade {grade}), hold for diversification"
        elif risk_score > 4.0:
            recommendation = "SELL"
            rationale = f"High risk level ({risk_score:.1f}/5.0) exceeds acceptable threshold"
        else:
            recommendation = "SELL"
            rationale = f"Weak fundamentals and technicals (Grade {grade})"

        return recommendation, rationale

    def score_ticker(
        self,
        ticker: str,
        fundamental_metrics: Dict[str, Any],
        technical_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete scoring for a ticker.

        Returns:
            Dict with composite_score, grade, recommendation, rationale, risk_score
        """
        composite_score = self.calculate_composite_score(
            fundamental_metrics,
            technical_metrics,
            risk_metrics
        )

        grade = self.assign_grade(composite_score)
        risk_score = self._calculate_risk_score(risk_metrics)
        recommendation, rationale = self.generate_recommendation(grade, risk_score)

        return {
            "ticker": ticker,
            "composite_score": composite_score,
            "grade": grade,
            "recommendation": recommendation,
            "rationale": rationale,
            "risk_score": risk_score,
            "fundamental_score": self._calculate_fundamental_score(fundamental_metrics),
            "technical_score": self._calculate_technical_score(technical_metrics)
        }
```

### Jinja2 Templates for Deep Analysis Reports (Requirement 19)

**Critical Design Decision**: Replace AI-generated HTML reports with Jinja2 templates for instant, deterministic, and maintainable report generation.

#### Template Implementation (Requirements 19.1-19.8)

```html
<!-- src/finwiz/templates/deep_analysis_report.html.j2 -->
<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Analyse {{ data.ticker }} - FinWiz</title>
    <style>
      /* Professional CSS with light/dark mode support */
      :root {
        --bg-primary: #ffffff;
        --text-primary: #2c3e50;
        --accent: #3498db;
        --success: #27ae60;
        --danger: #e74c3c;
      }

      @media (prefers-color-scheme: dark) {
        :root {
          --bg-primary: #1a1a1a;
          --text-primary: #ecf0f1;
        }
      }

      .grade-a-plus {
        color: var(--success);
        font-weight: bold;
      }
      .grade-f {
        color: var(--danger);
        font-weight: bold;
      }
      /* ... responsive design styles ... */
    </style>
  </head>
  <body>
    <h1>📊 Analyse {{ data.ticker }} ({{ data.asset_class|upper }})</h1>

    <!-- Executive Summary (Résumé Exécutif) -->
    <section>
      <h2>Résumé Exécutif</h2>
      <p class="grade-{{ data.grade|lower|replace('+', '-plus') }}">
        {% if data.recommendation == 'BUY' %}✅{% elif data.recommendation ==
        'SELL' %}❌{% else %}⏸️{% endif %}
        <strong>{{ data.recommendation }}</strong> - Grade {{ data.grade }}
      </p>
      <p>
        <strong>Score Composite:</strong> {{ "%.0f"|format(data.composite_score
        * 100) }}%
      </p>
    </section>

    <!-- Key Metrics (Métriques Clés) -->
    <section>
      <h2>💰 Métriques Clés</h2>
      <table>
        <tr>
          <th>Score Fondamental</th>
          <td>{{ "%.0f"|format(data.fundamental_score * 100) }}%</td>
        </tr>
        <tr>
          <th>Score Technique</th>
          <td>{{ "%.0f"|format(data.technical_score * 100) }}%</td>
        </tr>
        <tr>
          <th>Score de Risque</th>
          <td>{{ data.risk_score }}/5</td>
        </tr>
      </table>
    </section>

    <!-- Rationale (Justification) -->
    <section>
      <h2>Justification</h2>
      <p>{{ data.rationale }}</p>
    </section>

    <!-- Risk Assessment (Évaluation des Risques) -->
    <section>
      <h2>⚠️ Évaluation des Risques</h2>
      <p><strong>Niveau de Risque:</strong> {{ data.risk_score }}/5</p>
      <!-- Risk factors would be listed here -->
    </section>

    <!-- Data Sources (Sources de Données) -->
    <section>
      <h2>📋 Sources de Données</h2>
      <ul>
        {% for source in data.data_sources %}
        <li>{{ source }}</li>
        {% endfor %}
      </ul>
    </section>

    <footer>
      <p><em>Généré le {{ generation_date }} par FinWiz</em></p>
    </footer>
  </body>
</html>
```

#### Deep Analysis Report Generator (Requirements 19.9-19.18)

```python
# src/finwiz/reporting/deep_analysis_report_generator.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class DeepAnalysisReportGenerator:
    """Generate deep analysis HTML reports using Jinja2 templates.

    Requirements: 19.9-19.18
    """

    def __init__(self, template_dir: str = "src/finwiz/templates"):
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def generate_report(
        self,
        analysis_result: Dict[str, Any],
        output_path: Path
    ) -> str:
        """Generate HTML report from analysis result.

        Requirements: 19.12, 19.13, 19.14, 19.15, 19.16
        """
        # Load template
        template = self.env.get_template('deep_analysis_report.html.j2')

        # Render with data
        html_content = template.render(
            data=analysis_result,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

        return str(output_path)
```

#### Performance Comparison (Requirements 19.25-19.28)

| Approach             | Time per Report     | Cost per Report         | Quality           | Testability        |
| -------------------- | ------------------- | ----------------------- | ----------------- | ------------------ |
| **AI Generation**    | 30-60 seconds       | \$0.01-0.02             | Variable          | Difficult          |
| **Jinja2 Templates** | <100ms              | \$0.00                  | Consistent        | Full unit tests    |
| **Improvement**      | **300-600x faster** | **100% cost reduction** | **Deterministic** | **Fully testable** |

### Simplified Deep Analysis Crew (Requirements 18.11-18.20)

Deep Analysis crew simplified from 5 AI tasks to 2 tasks:

```python
class DeepAnalysisCrew:
    """Simplified deep analysis crew using Python scoring."""

    @task
    def data_collection_task(self) -> Task:
        """Task 1: Collect all data using tools (async)."""
        return Task(
            description="""
            Collect all required data for deep analysis of {ticker}.

            Steps:
            1. Validate ticker using TickerValidationTool
            2. Fetch fundamental data using asset-specific tool
            3. Fetch technical indicators using QuantitativeAnalysisTool
            4. Fetch sentiment data using StandardizedSentimentTool
            5. Store all data in structured context dict

            DO NOT perform any analysis or calculations.
            ONLY fetch and store data.
            """,
            expected_output="Structured dict with all fetched data",
            agent=self.data_collector(),
            async_execution=True  # Parallel data fetching
        )

    @task
    def python_scoring_task(self) -> Task:
        """Task 2: Calculate scores using Python (sync)."""
        return Task(
            description="""
            Calculate scores and generate recommendation using Python scoring engine.

            Steps:
            1. Extract fetched data from context
            2. Call DeepAnalysisScorer.score_ticker() with data
            3. Create DeepAnalysisCrewExport object with results
            4. Save export to JSON file

            NO AI reasoning or LLM calls required.
            Pure Python calculation.
            """,
            expected_output="DeepAnalysisCrewExport object",
            output_pydantic=DeepAnalysisCrewExport,
            output_json=True,
            agent=self.scorer(),
            async_execution=False,  # Final task must be sync
            depends_on=[self.data_collection_task()]
        )
```

### Performance Optimization Configuration (Requirement 21)

#### Configuration Options (Requirements 21.1-21.4)

Environment variables for performance tuning:

```bash
# Core optimizations
RISK_ASSESSMENT_USE_MINI=true          # Use gpt-4o-mini for risk assessment
USE_MINIMAL_RISK_TOOLS=true            # Use minimal tool set for risk assessor
DEEP_ANALYSIS_AI_SUMMARY=false         # Disable optional AI summary (default)
DEEP_ANALYSIS_BATCH_SIZE=5             # Batch size for concurrent execution

# Validation
PYTHON_SCORING_VALIDATION=true         # Validate Python vs AI scoring consistency
PERFORMANCE_REGRESSION_TESTS=true      # Enable performance regression testing
```

#### Optimization Modes (Requirements 21.5-21.8)

```python
class OptimizationMode(Enum):
    """Performance optimization modes."""
    MAXIMUM_SPEED = "maximum_speed"     # Python scoring + no AI + gpt-4o-mini + minimal tools
    BALANCED = "balanced"               # Python scoring + optional AI + gpt-4o-mini + minimal tools
    BASELINE = "baseline"               # AI scoring (for comparison/debugging)

class PerformanceConfig:
    """Performance optimization configuration."""

    def __init__(self, mode: OptimizationMode = OptimizationMode.MAXIMUM_SPEED):
        self.mode = mode
        self._configure_mode()

    def get_expected_performance(self) -> Dict[str, Any]:
        """Get expected performance characteristics by mode."""
        performance_specs = {
            OptimizationMode.MAXIMUM_SPEED: {
                "time_per_ticker": "10-30 seconds",
                "cost_per_ticker": "$0.00",
                "portfolio_66_time": "10-30 minutes",
                "portfolio_66_cost": "$0.00",
                "speedup_factor": "10-20x"
            },
            OptimizationMode.BALANCED: {
                "time_per_ticker": "15-40 seconds",
                "cost_per_ticker": "$0.01",
                "portfolio_66_time": "15-40 minutes",
                "portfolio_66_cost": "$0.66",
                "speedup_factor": "8-15x"
            },
            OptimizationMode.BASELINE: {
                "time_per_ticker": "5-10 minutes",
                "cost_per_ticker": "$0.05-0.10",
                "portfolio_66_time": "5.5-11 hours",
                "portfolio_66_cost": "$3.30-6.60",
                "speedup_factor": "1x (baseline)"
            }
        }
        return performance_specs[self.mode]
```

#### Performance Monitoring (Requirements 21.9-21.11)

```python
class PerformanceMonitor:
    """Monitor and validate performance metrics."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics = {
            "execution_times": [],
            "llm_calls": [],
            "api_calls": [],
            "cost_estimates": []
        }

    def validate_performance_targets(self, mode: OptimizationMode) -> Dict[str, bool]:
        """Validate that performance targets are met.

        Requirements: 21.12, 21.13, 21.14
        """
        expected = PerformanceConfig(mode).get_expected_performance()
        actual = self.get_actual_performance()

        validation_results = {
            "time_target_met": actual["avg_time_per_ticker"] <= self._parse_time_target(expected["time_per_ticker"]),
            "cost_target_met": actual["avg_cost_per_ticker"] <= self._parse_cost_target(expected["cost_per_ticker"]),
            "speedup_achieved": actual["speedup_factor"] >= self._parse_speedup_target(expected["speedup_factor"])
        }

        # Alert if performance degrades >10%
        if not all(validation_results.values()):
            logger.warning("Performance targets not met!")
            for metric, passed in validation_results.items():
                if not passed:
                    logger.warning(f"Failed: {metric}")

        return validation_results
```

### Performance Comparison

| Approach              | Tasks         | AI Reasoning | Time per Ticker | Cost per Ticker       | Deterministic |
| --------------------- | ------------- | ------------ | --------------- | --------------------- | ------------- |
| **Current (AI)**      | 5 tasks       | Yes          | 5-10 minutes    | \$0.05-0.10           | No            |
| **Python Scoring**    | 2 tasks       | No           | 10-30 seconds   | \$0.00 (calculations) | Yes           |
| **Hybrid (Optional)** | 2 + 1 summary | Optional     | 15-40 seconds   | \$0.01 (summary only) | Yes           |

**Benefits of Python Scoring:**

- ✅ **10-20x faster**: 30 seconds vs 5-10 minutes per ticker
- ✅ **100% cost reduction**: $0 vs $0.05-0.10 for calculations
- ✅ **Deterministic**: Same input = same output
- ✅ **Fully testable**: Unit tests for all scoring logic
- ✅ **Consistent quality**: No AI variability
- ✅ **Maintainable**: Python code vs prompt engineering

**What We Lose (Acceptable):**

- ❌ Natural language prose (replaced with Jinja2 templates)
- ❌ Generic AI statements (no unique insight)
- ❌ Arbitrary confidence levels (not statistically grounded)
- ❌ Inconsistent quality (sometimes good, often generic)
- ❌ Rare creative insights (not worth 10-20x performance penalty)

**What We Preserve:**

- ✅ ALL quantitative data from tool outputs
- ✅ ALL calculation results (scores, grades, recommendations)
- ✅ Template-based rationale text (professional, consistent)
- ✅ Risk assessments and metrics
- ✅ Data quality and validation

### Hybrid Approach (Optional)

Optional AI summary generation for natural language polish:

```python
class DeepAnalysisCrew:
    """Deep analysis with optional AI summary."""

    def __init__(self):
        self.ai_summary_enabled = os.getenv("DEEP_ANALYSIS_AI_SUMMARY", "false").lower() == "true"

    @task
    def optional_ai_summary_task(self) -> Task:
        """Optional Task 3: Generate AI prose summary (if enabled)."""
        if not self.ai_summary_enabled:
            return None  # Skip this task

        return Task(
            description="""
            Generate natural language summary of analysis results.

            Input: Python scoring results from context
            Output: Professional prose summary (2-3 paragraphs)

            This is OPTIONAL polish only. All calculations are already complete.
            """,
            expected_output="Natural language summary",
            agent=self.summarizer(),
            async_execution=False,
            depends_on=[self.python_scoring_task()]
        )
```

**Hybrid Performance:**

- Total time: 15-40 seconds (vs 5-10 minutes)
- Cost: $0.01 per ticker (vs $0.05-0.10)
- Time savings: 80-90%
- Cost savings: 80-90%

## Performance Optimization Configuration

### Configuration Options

Environment variables for performance tuning:

```python
# Deep Analysis Optimizations
DEEP_ANALYSIS_AI_SUMMARY=false  # Disable optional AI summary (default)
DEEP_ANALYSIS_BATCH_SIZE=5  # Batch size for concurrent execution
BATCH_PREFETCH_ENABLED=true  # Enable batch data pre-fetching

# Risk Assessment Optimizations (from PERFORMANCE_OPTIMIZATION_GUIDE.md)
RISK_ASSESSMENT_USE_MINI=true  # Use gpt-4o-mini for risk assessment
USE_MINIMAL_RISK_TOOLS=true  # Use minimal tool set for risk assessor
```

### Optimization Modes

Three optimization modes for different use cases:

```python
class OptimizationMode(Enum):
    """Performance optimization modes."""
    MAXIMUM_SPEED = "maximum_speed"  # Python scoring + no AI summary + gpt-4o-mini + minimal tools
    BALANCED = "balanced"  # Python scoring + optional AI summary + gpt-4o-mini + minimal tools
    BASELINE = "baseline"  # AI scoring (for comparison/debugging)

class PerformanceConfig:
    """Performance optimization configuration."""

    def __init__(self, mode: OptimizationMode = OptimizationMode.MAXIMUM_SPEED):
        self.mode = mode
        self._configure_mode()

    def _configure_mode(self):
        """Configure settings based on optimization mode."""
        if self.mode == OptimizationMode.MAXIMUM_SPEED:
            os.environ["DEEP_ANALYSIS_AI_SUMMARY"] = "false"
            os.environ["RISK_ASSESSMENT_USE_MINI"] = "true"
            os.environ["USE_MINIMAL_RISK_TOOLS"] = "true"
            os.environ["BATCH_PREFETCH_ENABLED"] = "true"

        elif self.mode == OptimizationMode.BALANCED:
            os.environ["DEEP_ANALYSIS_AI_SUMMARY"] = "true"
            os.environ["RISK_ASSESSMENT_USE_MINI"] = "true"
            os.environ["USE_MINIMAL_RISK_TOOLS"] = "true"
            os.environ["BATCH_PREFETCH_ENABLED"] = "true"

        elif self.mode == OptimizationMode.BASELINE:
            os.environ["DEEP_ANALYSIS_AI_SUMMARY"] = "false"
            os.environ["RISK_ASSESSMENT_USE_MINI"] = "false"
            os.environ["USE_MINIMAL_RISK_TOOLS"] = "false"
            os.environ["BATCH_PREFETCH_ENABLED"] = "false"
```

### Performance Monitoring

Track and log performance metrics:

```python
class PerformanceMonitor:
    """Monitor and log performance metrics."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics = {
            "execution_times": [],
            "llm_calls": [],
            "api_calls": [],
            "cost_estimates": []
        }

    def log_ticker_analysis(
        self,
        ticker: str,
        execution_time: float,
        llm_calls: int,
        api_calls: int,
        cost_estimate: float
    ):
        """Log metrics for single ticker analysis."""
        self.metrics["execution_times"].append(execution_time)
        self.metrics["llm_calls"].append(llm_calls)
        self.metrics["api_calls"].append(api_calls)
        self.metrics["cost_estimates"].append(cost_estimate)

        logger.info(f"{ticker}: {execution_time:.1f}s, {llm_calls} LLM calls, ${cost_estimate:.4f}")

    def generate_summary(self) -> Dict[str, Any]:
        """Generate performance summary."""
        total_tickers = len(self.metrics["execution_times"])

        return {
            "total_tickers": total_tickers,
            "total_time": sum(self.metrics["execution_times"]),
            "avg_time_per_ticker": sum(self.metrics["execution_times"]) / total_tickers if total_tickers > 0 else 0,
            "total_llm_calls": sum(self.metrics["llm_calls"]),
            "total_api_calls": sum(self.metrics["api_calls"]),
            "total_cost": sum(self.metrics["cost_estimates"]),
            "avg_cost_per_ticker": sum(self.metrics["cost_estimates"]) / total_tickers if total_tickers > 0 else 0
        }

    def compare_to_baseline(self, baseline_time: float, baseline_cost: float) -> Dict[str, Any]:
        """Compare actual performance to baseline."""
        summary = self.generate_summary()

        time_savings = baseline_time - summary["total_time"]
        time_savings_pct = (time_savings / baseline_time) * 100 if baseline_time > 0 else 0

        cost_savings = baseline_cost - summary["total_cost"]
        cost_savings_pct = (cost_savings / baseline_cost) * 100 if baseline_cost > 0 else 0

        return {
            **summary,
            "baseline_time": baseline_time,
            "baseline_cost": baseline_cost,
            "time_savings": time_savings,
            "time_savings_percentage": time_savings_pct,
            "cost_savings": cost_savings,
            "cost_savings_percentage": cost_savings_pct,
            "speedup_factor": baseline_time / summary["total_time"] if summary["total_time"] > 0 else 0
        }
```

### Expected Performance by Mode

| Mode              | Time per Ticker | Cost per Ticker | 66-Ticker Portfolio Time | 66-Ticker Portfolio Cost |
| ----------------- | --------------- | --------------- | ------------------------ | ------------------------ |
| **Maximum Speed** | 10-30s          | \$0.00          | 10-30 min                | \$0.00 (calculations)    |
| **Balanced**      | 15-40s          | \$0.01          | 15-40 min                | \$0.66                   |
| **Baseline (AI)** | 5-10 min        | \$0.05-0.10     | 5.5-11 hours             | \$3.30-6.60              |

**Speedup Factors:**

- Maximum Speed: **10-20x faster** than baseline
- Balanced: **8-15x faster** than baseline
- Cost Reduction: **90-100%** for calculations

## Testing Strategy

### Unit Tests (Python Functions)

All Python functions are fully testable with mocks.

```python
# Test Python scoring engine
def test_should_calculate_composite_score():
    """Test composite score calculation."""
    # Arrange
    scorer = DeepAnalysisScorer()
    fundamental_metrics = {"roe": 0.22, "debt_equity": 0.3, "revenue_growth": 0.18}
    technical_metrics = {"rsi": 55, "sma_50": 150, "sma_200": 140, "current_price": 155}
    risk_metrics = {"volatility": 0.25, "max_drawdown": -0.15, "beta": 1.2}

    # Act
    score = scorer.calculate_composite_score(
        fundamental_metrics,
        technical_metrics,
        risk_metrics
    )

    # Assert
    assert 0.0 <= score <= 1.0
    assert score > 0.7  # Should be high given strong metrics

def test_should_assign_correct_grade():
    """Test grade assignment."""
    # Arrange
    scorer = DeepAnalysisScorer()

    # Act & Assert
    assert scorer.assign_grade(0.92) == "A+"
    assert scorer.assign_grade(0.87) == "A"
    assert scorer.assign_grade(0.72) == "B"
    assert scorer.assign_grade(0.42) == "D"
    assert scorer.assign_grade(0.30) == "F"

def test_should_generate_buy_recommendation_for_strong_metrics():
    """Test recommendation generation."""
    # Arrange
    scorer = DeepAnalysisScorer()

    # Act
    recommendation, rationale = scorer.generate_recommendation("A+", 2.5)

    # Assert
    assert recommendation == "BUY"
    assert "Strong fundamentals" in rationale
    assert "A+" in rationale

# Test HTML generation
def test_should_generate_html_from_json_export(tmp_path):
    """Test HTML generation from JSON export."""
    # Arrange
    generator = HTMLReportGenerator()
    export_data = {
        "ticker": "AAPL",
        "grade": "A+",
        "composite_score": 0.85,
        "recommendation": "BUY"
    }
    output_path = tmp_path / "report.html"

    # Act
    result_path = generator.generate_crew_report(
        crew_name="stock_crew",
        export_data=export_data,
        output_path=output_path
    )

    # Assert
    assert output_path.exists()
    html_content = output_path.read_text()
    assert "AAPL" in html_content
    assert "A+" in html_content
    assert "BUY" in html_content

# Test consolidation
def test_should_consolidate_multiple_crew_exports(tmp_path):
    """Test consolidation of crew exports."""
    # Arrange
    consolidator = ReportConsolidator(
        session_id="test-session",
        output_dir=tmp_path
    )

    # Create mock export files
    stock_export = tmp_path / "stock_export.json"
    stock_export.write_text(json.dumps({
        "crew_name": "stock_crew",
        "ticker": "AAPL",
        "grade": "A+",
        "composite_score": 0.85
    }))

    crew_export_paths = {
        "stock_crew": [str(stock_export)]
    }

    # Act
    consolidated = consolidator.consolidate_reports(crew_export_paths)

    # Assert
    assert len(consolidated.stock_analyses) == 1
    assert consolidated.stock_analyses[0].ticker == "AAPL"
    assert consolidated.crew_execution_status["stock_crew"] == "completed"

# Test validation
def test_should_reject_invalid_export_data():
    """Test Pydantic validation rejects invalid data."""
    # Arrange
    invalid_data = {
        "ticker": "AAPL",
        "grade": "INVALID",  # Invalid grade
        "composite_score": 1.5  # Out of range
    }

    # Act & Assert
    with pytest.raises(ValidationError):
        StockCrewExport.model_validate(invalid_data)
```

ame="stock_crew",
export_data=export_data,
output_path=output_path
)

    # Assert
    assert output_path.exists()
    html_content = output_path.read_text()
    assert "AAPL" in html_content
    assert "A+" in html_content
    assert "BUY" in html_content

# Test data consolidation

def test_should_consolidate_multiple_crew_exports(tmp_path):
"""Test consolidation of crew exports.""" # Arrange
consolidator = ReportConsolidator("test-session", tmp_path)

    # Create mock export files
    stock_export = tmp_path / "stock_crew" / "AAPL_export.json"
    stock_export.parent.mkdir(parents=True)
    stock_export.write_text(json.dumps({
        "ticker": "AAPL",
        "grade": "A+",
        "composite_score": 0.85
    }))

    crew_export_paths = {
        "stock_crew": [str(stock_export)]
    }

    # Act
    consolidated = consolidator.consolidate_reports(crew_export_paths)

    # Assert
    assert len(consolidated.stock_analyses) == 1
    assert consolidated.stock_analyses[0].ticker == "AAPL"
    assert consolidated.crew_execution_status["stock_crew"] == "completed"

# Test batch data pre-fetcher

def test_should_prefetch_data_for_multiple_tickers(mocker):
"""Test batch data pre-fetching.""" # Arrange
prefetcher = BatchDataPreFetcher("test-session")
tickers = ["AAPL", "MSFT", "GOOGL"]

    # Mock Yahoo Finance batch download
    mock_yf_download = mocker.patch('yfinance.download')
    mock_yf_download.return_value = mocker.Mock()

    # Act
    data = prefetcher.prefetch_all_data(tickers)

    # Assert
    assert len(data) == 3
    assert "AAPL" in data
    assert "yahoo_finance" in data["AAPL"]
    mock_yf_download.assert_called_once()

````

### Integration Tests

Test complete workflows with real crew execution:

```python
@pytest.mark.integration
def test_should_execute_deep_analysis_with_python_scoring():
    """Test deep analysis crew with Python scoring."""
    # Arrange
    crew = DeepAnalysisCrew()
    ticker = "AAPL"

    # Act
    result = crew.crew().kickoff(inputs={"ticker": ticker, "asset_class": "stock"})

    # Assert
    assert result is not None
    # Verify export file exists
    export_path = Path(f"output/reports/test-session/deep_analysis_crew/{ticker}_export.json")
    assert export_path.exists()

    # Verify export contains required fields
    export_data = json.loads(export_path.read_text())
    assert export_data["ticker"] == ticker
    assert "composite_score" in export_data
    assert "grade" in export_data
    assert "recommendation" in export_data

@pytest.mark.integration
def test_should_complete_full_flow_with_consolidation():
    """Test complete flow from analysis to final report."""
    # Arrange
    flow = ReportAggregationFlow()

    # Act
    result = flow.kickoff()

    # Assert
    assert flow.state.final_report_path is not None
    final_report = Path(flow.state.final_report_path)
    assert final_report.exists()

    # Verify consolidated JSON exists
    consolidated_path = Path(flow.state.consolidated_json_path)
    assert consolidated_path.exists()
````

### Performance Tests

Validate performance improvements:

```python
@pytest.mark.slow
def test_should_achieve_target_performance_with_python_scoring():
    """Test that Python scoring achieves 10-20x speedup."""
    # Arrange
    ticker = "AAPL"

    # Measure Python scoring time
    start_time = time.time()
    crew = DeepAnalysisCrew()  # With Python scoring
    result = crew.crew().kickoff(inputs={"ticker": ticker, "asset_class": "stock"})
    python_time = time.time() - start_time

    # Assert
    assert python_time < 60  # Should complete in under 60 seconds

    # Compare to baseline (assume 5 minutes for AI scoring)
    baseline_time = 300
    speedup_factor = baseline_time / python_time
    assert speedup_factor >= 5  # At least 5x faster

@pytest.mark.slow
def test_should_achieve_target_performance_with_batch_prefetch():
    """Test that batch pre-fetching achieves 55%+ time savings."""
    # Arrange
    tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # 5 tickers

    # Measure with batch pre-fetch
    start_time = time.time()
    prefetcher = BatchDataPreFetcher("test-session")
    data = prefetcher.prefetch_all_data(tickers)

    # Execute crews with pre-fetched data
    for ticker in tickers:
        crew = DeepAnalysisCrew()
        crew.set_prefetched_data(data[ticker])
        crew.crew().kickoff(inputs={"ticker": ticker, "asset_class": "stock"})

    total_time = time.time() - start_time

    # Assert
    # Baseline: 5 tickers × 60s = 300s
    # Target: <135s (55% savings)
    assert total_time < 135

    time_savings_pct = ((300 - total_time) / 300) * 100
    assert time_savings_pct >= 55
```

## Summary

This design implements a comprehensive reorganization of the FinWiz crew architecture following the **AI Minimalism** principle and addresses all requirements:

### Requirements Coverage

**Critical Fixes (Requirements 0.x):**

- ✅ Pure Python deep analysis replacement (0.1-0.7)
- ✅ Fixed JSON export directory structure (0.8-0.12)
- ✅ A+ discovery integration with deep analysis (0.13-0.17)
- ✅ Backtesting pipeline connection (0.18-0.21)
- ✅ Python report generation (0.22-0.26)
- ✅ Integration demonstration script (0.31-0.34)

**Core Architecture (Requirements 1-17):**

- ✅ Pydantic-validated export objects (Req 1)
- ✅ Python HTML generation with Jinja2 (Req 2)
- ✅ Python data consolidation (Req 3)
- ✅ Comprehensive crew evaluation (Req 4)
- ✅ French language final report (Req 8)
- ✅ Batch processing architecture (Req 17)

**Pure Python Architecture (Requirements 18-21):**

- ✅ Python-based scoring engine (Req 18)
- ✅ Jinja2 templates for reports (Req 19)
- ✅ Complete pure Python implementation (Req 20)
- ✅ Performance optimization configuration (Req 21)

### Key Design Decisions

1. **Pydantic-First Architecture**: All crew outputs validated with strict schemas (Req 1, 10)
2. **Python for Determinism**: HTML generation, data consolidation, and scoring use Python (NO AI) (Req 2, 3, 18-21)
3. **Python-Based Scoring Engine**: Replace AI reasoning with deterministic calculations (10-20x faster) (Req 18)
4. **File-Based Data Passing**: Pass file paths (not data) to avoid context limits (Req 6)
5. **Concurrent Execution**: All SME crews run in parallel for maximum performance (Req 7, 17)
6. **Batch Data Pre-Fetching**: Pre-fetch all data upfront to eliminate API latency (55%+ time savings) (Req 17)
7. **Clean Break**: No backward compatibility with legacy broken patterns (Req 11)

### Performance Improvements

**Deep Analysis Optimization:**

- **Python Scoring**: 10-20x faster (30s vs 5-10 min per ticker)
- **Cost Reduction**: 100% for calculations ($0 vs $0.05-0.10)
- **Batch Pre-Fetching**: 55%+ time savings (30 min vs 66 min for 66 tickers)
- **Combined**: 66-holding portfolio in 30 minutes vs 5.5-11 hours (10-20x overall speedup)

**What We Use AI For:**

- ✅ Complex market analysis requiring reasoning
- ✅ Multi-factor screening and decision-making
- ✅ SEC filing interpretation
- ✅ Risk scenario analysis
- ✅ Investment thesis generation
- ✅ Optional natural language summaries (hybrid mode)

**What We Use Python For:**

- ✅ HTML report generation (Jinja2 templates)
- ✅ Data consolidation (pure Python functions)
- ✅ Scoring calculations (DeepAnalysisScorer)
- ✅ Data validation (Pydantic models)
- ✅ Batch data pre-fetching (BatchDataPreFetcher)
- ✅ Performance monitoring and metrics

### Architecture Benefits

- **Quality**: Deterministic calculations, consistent output, full test coverage
- **Speed**: 10-20x faster execution through Python scoring and batch pre-fetching
- **Cost**: 90-100% cost reduction for calculations and HTML generation
- **Maintainability**: Python code vs prompt engineering, clear separation of concerns
- **Testability**: Full unit test coverage for all Python components
- **Scalability**: Linear scaling with portfolio size, configurable optimization modes

### Implementation Phases

**Phase 1: Critical Fixes (IMMEDIATE PRIORITY)** (Requirements 0.x)

- Pure Python deep analysis replacement
- Fixed JSON export directory structure
- A+ discovery integration
- Backtesting pipeline connection
- Python report generation
- Integration demonstration script

**Phase 2: Pure Python Architecture** (Requirements 18-21)

- Python-based scoring engine (DeepAnalysisScorer)
- Jinja2 templates for all reports
- Complete pure Python implementation
- Performance optimization configuration
- Optional hybrid mode with AI summaries

**Phase 3: Enhanced Architecture** (Requirements 1-17)

- Batch data pre-fetcher
- Modified tools for pre-fetched data
- Flow integration with batch pre-fetching
- Performance metrics tracking
- Comprehensive crew evaluation

**Phase 4: Testing and Validation** (All Requirements)

- Unit tests for all Python components
- Integration tests for complete workflows
- Performance tests validating speedup targets
- Data quality validation (Python vs AI results)
- Requirements compliance validation

This design achieves the project goals of fixing broken data flow, maximizing performance, and following AI Minimalism principles while maintaining data quality and accuracy.

---

**Version**: 2.0
**Last Updated**: 2025-01-25
**Major Updates**: Added Python-based scoring engine, Jinja2 templates for deep analysis, and performance optimization configuration based on Requirements 18-20
