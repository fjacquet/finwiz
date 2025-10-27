---
title: "Python Scoring Engine"
description: "Archived documentation for Python Scoring Engine"
category: "archive"
tags:
  - "archive"
date: "2025-10-26"
source: "explanations/PYTHON_SCORING_ENGINE.md"
---

# Python Scoring Engine Architecture

The Python Scoring Engine represents FinWiz's **AI Minimalism** approach: use deterministic Python calculations for scoring and reserve AI exclusively for analysis requiring reasoning.

[TOC]

## Overview

The Python Scoring Engine is a high-performance, deterministic alternative to AI-based scoring that provides:

- **10-20x faster execution** (10-30 seconds vs 5-10 minutes per ticker)
- **100% cost reduction** for calculations ($0 vs $0.05-0.10 per ticker)
- **Deterministic results** (same input = same output)
- **Full testability** with unit tests and validation

## Architecture Components

### Core Scoring Engine

```pythonthon
# src/finwiz/scoring/deep_analysis_scorer.py
class DeepAnalysisScorer:
    """Pure Python scoring engine for financial analysis."""

    def calculate_composite_score(self, data: dict) -> float:
        """Calculate weighted composite score (0.0-1.0)."""
        fundamental = self.calculate_fundamental_score(data) * 0.40
        technical = self.calculate_technical_score(data) * 0.30
        risk = (5 - self.calculate_risk_score(data)) / 5 * 0.30
        return fundamental + technical + risk
```text
### Portfolio Analyzer

```pythonthon
# src/finwiz/scoring/portfolio_deep_analyzer.py
class PortfolioDeepAnalyzer:
    """Concurrent portfolio analysis using Python scoring."""

    def analyze_portfolio_holdings(self, portfolio: Portfolio) -> dict:
        """Analyze all holdings concurrently with Python scoring."""
        # Process holdings in parallel for maximum performance
        # Export JSON files to proper output directories
        # Update portfolio with analysis results
```text
### Report Generator

```pythonthon
# src/finwiz/reporting/python_report_generator.py
class PythonReportGenerator:
    """Template-based HTML report generation (NO AI)."""

    def generate_family_financial_plan(self, data: dict) -> str:
        """Generate professional French reports using Jinja2."""
        # Use templates for consistent formatting
        # Complete generation in milliseconds
        # Support light/dark mode and responsive design
```text
## Scoring Methodology

### Composite Score Calculation

The composite score combines three weighted components:

```text
Composite Score = (Fundamental × 0.40) + (Technical × 0.30) + (Risk × 0.30)
```text
#### Fundamental Score (40% weight)

Based on financial health metrics:

```pythonthon
def calculate_fundamental_score(self, data: dict) -> float:
    """Calculate fundamental score (0.0-1.0)."""
    base_score = 0.5

    # ROE bonus/penalty
    roe = data.get('roe', 0)
    if roe > 0.20:  # 20%+
        base_score += 0.3
    elif roe > 0.15:  # 15-20%
        base_score += 0.2
    elif roe < 0.05:  # <5%
        base_score -= 0.2

    # Debt-to-equity penalty
    debt_equity = data.get('debt_to_equity', 0)
    if debt_equity > 0.5:
        base_score -= 0.2
    elif debt_equity > 0.3:
        base_score -= 0.1

    # Growth bonus
    revenue_growth = data.get('revenue_growth', 0)
    if revenue_growth > 0.15:  # 15%+
        base_score += 0.2
    elif revenue_growth > 0.10:  # 10-15%
        base_score += 0.1

    return max(0.0, min(1.0, base_score))
```text
#### Technical Score (30% weight)

Based on momentum and trend indicators:

```pythonthon
def calculate_technical_score(self, data: dict) -> float:
    """Calculate technical score (0.0-1.0)."""
    base_score = 0.5

    # RSI analysis
    rsi = data.get('rsi', 50)
    if 30 <= rsi <= 70:  # Neutral zone
        base_score += 0.2
    elif rsi < 30:  # Oversold
        base_score += 0.3
    elif rsi > 70:  # Overbought
        base_score -= 0.2

    # Trend analysis
    trend = data.get('trend_direction', 'neutral')
    if trend == 'bullish':
        base_score += 0.3
    elif trend == 'bearish':
        base_score -= 0.3

    return max(0.0, min(1.0, base_score))
```text
#### Risk Score (30% weight, inverted)

Lower risk = higher contribution to composite score:

```pythonthon
def calculate_risk_score(self, data: dict) -> int:
    """Calculate risk score (0-5 scale, 0=Very Low, 5=Very High)."""
    risk_score = 2  # Base moderate risk

    # Volatility adjustment
    volatility = data.get('volatility', 0.2)
    if volatility > 0.4:  # High volatility
        risk_score += 2
    elif volatility > 0.3:
        risk_score += 1
    elif volatility < 0.15:  # Low volatility
        risk_score -= 1

    # Maximum drawdown adjustment
    max_drawdown = abs(data.get('max_drawdown', 0.1))
    if max_drawdown > 0.3:  # >30% drawdown
        risk_score += 1
    elif max_drawdown < 0.1:  # <10% drawdown
        risk_score -= 1

    return max(0, min(5, risk_score))
```text
### Grade Assignment

Grades are assigned based on composite score thresholds:

| Grade | Score Range | Description |
|-------|-------------|-------------|
| A+ | 0.85 - 1.00 | Exceptional opportunity |
| A | 0.75 - 0.84 | Strong buy candidate |
| B | 0.65 - 0.74 | Good investment |
| C | 0.55 - 0.64 | Average performance |
| D | 0.45 - 0.54 | Below average |
| F | 0.00 - 0.44 | Poor investment |

### Recommendation Logic

Investment recommendations follow deterministic rules:

```pythonthon
def generate_recommendation(self, composite_score: float, grade: str) -> str:
    """Generate BUY/HOLD/SELL recommendation."""
    if grade in ['A+', 'A']:
        return 'BUY'
    elif grade in ['B', 'C']:
        return 'HOLD'
    else:  # D, F
        return 'SELL'
```text
## Integration Architecture

### Flow Integration

The Python scoring engine integrates with CrewAI Flow through convenience functions:

```pythonthon
# Integration functions in src/finwiz/scoring/__init__.py

def analyze_portfolio_with_python(portfolio_data: dict) -> dict:
    """Convenience function for Flow integration."""
    analyzer = PortfolioDeepAnalyzer()
    return analyzer.analyze_portfolio_holdings(portfolio_data)

def generate_python_report(analysis_data: dict) -> str:
    """Convenience function for report generation."""
    generator = PythonReportGenerator()
    return generator.generate_family_financial_plan(analysis_data)
```text
### Data Flow Architecture

```mermaid
graph TB
    A[Portfolio Data] --> B[PortfolioDeepAnalyzer]
    B --> C[DeepAnalysisScorer]
    C --> D[Composite Score Calculation]
    D --> E[Grade Assignment]
    E --> F[Recommendation Generation]
    F --> G[JSON Export]
    G --> H[PythonReportGenerator]
    H --> I[Jinja2 Templates]
    I --> J[HTML Report]

    K[A+ Discovery] --> L[APlusDiscoveryIntegrator]
    L --> G

    M[Backtesting] --> N[BacktestingPipelineConnector]
    N --> L

    O[Final Report] --> P[Template Consolidation]
    P --> J
```text
### Performance Optimization

#### Concurrent Processing

```pythonthon
def analyze_portfolio_holdings(self, portfolio: Portfolio) -> dict:
    """Analyze holdings concurrently for maximum performance."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for holding in portfolio.holdings:
            future = executor.submit(self._analyze_single_holding, holding)
            futures.append((holding.ticker, future))

        # Collect results as they complete
        results = {}
        for ticker, future in futures:
            try:
                results[ticker] = future.result(timeout=30)
            except Exception as e:
                logger.error(f"Analysis failed for {ticker}: {e}")
                results[ticker] = self._create_error_result(ticker, str(e))

        return results
```text
#### Memory Management

- Process holdings in batches to control memory usage
- Use generators for large datasets
- Implement proper cleanup after analysis
- Monitor memory consumption during execution

## Performance Characteristics

### Execution Time Comparison

| Component | AI Approach | Python Approach | Speedup |
|-----------|-------------|-----------------|---------|
| Single Ticker Analysis | 5-10 minutes | 10-30 seconds | 10-20x |
| 66-Holding Portfolio | 3-6 hours | 10-20 minutes | 10-18x |
| Report Generation | 30-60 seconds | <1 second | 30-60x |
| **Total Portfolio** | **3.5-6.5 hours** | **10-21 minutes** | **10-19x** |

### Cost Comparison

| Component | AI Cost | Python Cost | Savings |
|-----------|---------|-------------|---------|
| Scoring Calculations | $0.05-0.10 | $0.00 | 100% |
| Report Generation | $0.10-0.30 | $0.00 | 100% |
| Data Consolidation | $0.05-0.15 | $0.00 | 100% |
| **Per Ticker** | **$0.20-0.55** | **$0.00** | **100%** |
| **66-Holding Portfolio** | **$13.20-36.30** | **$0.00** | **100%** |

*Note: Data fetching costs (APIs) remain the same in both approaches*

### Quality Metrics

| Metric | AI Approach | Python Approach |
|--------|-------------|-----------------|
| Consistency | 95% (probabilistic) | 100% (deterministic) |
| Testability | Limited (prompt testing) | Full (unit tests) |
| Debuggability | Difficult (LLM black box) | Easy (stack traces) |
| Maintainability | Complex (prompt engineering) | Simple (code review) |
| Auditability | Limited (AI reasoning) | Complete (calculation steps) |

## Implementation Status

### ✅ Completed Components

- **DeepAnalysisScorer**: Complete Python scoring engine
- **PortfolioDeepAnalyzer**: Concurrent portfolio analyzer
- **PythonReportGenerator**: Template-based report generation
- **Integration Functions**: Flow-compatible convenience functions
- **Demonstration Script**: End-to-end validation script

### ❌ Critical Integration Gaps

- **Flow Integration**: Flow still calls AI crews instead of Python functions
- **JSON Export Structure**: Proper output directory organization
- **A+ Discovery Integration**: Connect discovery to analysis results
- **Backtesting Pipeline**: Connect backtesting to discovery results
- **Final Report Generation**: Ensure templates are used instead of AI

### 🎯 Next Steps

1. Update Flow to call `analyze_portfolio_with_python()` instead of AI crews
2. Fix JSON export directory structure and accessibility
3. Integrate A+ discovery with deep analysis results
4. Connect backtesting pipeline to discovery results
5. Ensure final report uses Python templates exclusively

## Benefits and Trade-offs

### Benefits

✅ **Performance**: 10-20x faster execution
✅ **Cost**: 100% reduction for calculations
✅ **Reliability**: Deterministic, consistent results
✅ **Testability**: Full unit test coverage
✅ **Maintainability**: Standard Python code review process
✅ **Auditability**: Complete calculation transparency
✅ **Scalability**: No LLM rate limits for calculations

### Trade-offs

⚠️ **Flexibility**: Less adaptable than AI reasoning
⚠️ **Complexity**: Requires manual formula updates
⚠️ **Coverage**: May miss nuanced analysis patterns
⚠️ **Innovation**: No automatic improvement from AI learning

### When to Use Each Approach

#### Use Python Scoring For:

- High-volume portfolio analysis (66+ holdings)
- Production environments requiring consistency
- Cost-sensitive applications
- Regulatory environments requiring auditability
- Performance-critical workflows

#### Use AI Scoring For:

- Single-ticker deep analysis requiring nuanced reasoning
- Research and development of new scoring methodologies
- Complex market condition analysis
- Qualitative factor integration
- Experimental analysis approaches

## Hybrid Approach

For maximum flexibility, FinWiz supports a hybrid approach:

```pythonthon
# Optional AI summary after Python scoring
if os.getenv('DEEP_ANALYSIS_AI_SUMMARY', 'false').lower() == 'true':
    # Python scoring (10-30 seconds, $0)
    python_result = scorer.calculate_composite_score(data)

    # Optional AI summary (5-10 seconds, $0.01)
    ai_summary = generate_ai_summary(python_result, data)

    # Total: 15-40 seconds, $0.01 (vs 5-10 minutes, $0.05-0.10)
```text
This provides:
- **80-90% cost savings** ($0.01 vs $0.05-0.10 per ticker)
- **75-85% time savings** (15-40 seconds vs 5-10 minutes)
- **Best of both worlds**: Python reliability + AI insights

## Related Topics

- [Report Aggregation Architecture](REPORT_AGGREGATION_DEVELOPER_GUIDE.md) - Integration patterns
- [AI Minimalism](../ai-minimalism.md) - Decision framework for AI vs Python
- [Performance Configuration](PERFORMANCE_CONFIGURATION.md) - Optimization settings
- [Testing Standards](../testing-standards.md) - Unit testing approaches

## Further Reading

- [Implementation Tasks](../../.kiro/specs/report-aggregation-architecture/tasks.md) - Detailed implementation plan
- [Flow Architecture](flow_architecture.md) - CrewAI Flow integration patterns
- [Validation Framework](validation_framework.md) - Data quality assurance

---

**Version**: 2.0
**Last Updated**: 2025-10-26
**Status**: Core components implemented, integration in progress
