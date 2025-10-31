# Pure Python Pipeline

Welcome to the Pure Python Pipeline documentation. This pipeline provides a high-performance, deterministic alternative to AI-based portfolio analysis.

## Quick Links

- **[Overview](python_pipeline/overview.md)** - Introduction and key benefits
- **[Components](python_pipeline/components.md)** - Detailed component documentation
- **[Data Flow](python_pipeline/data-flow.md)** - Complete data flow architecture
- **[JSON Exports](python_pipeline/json-exports.md)** - Export structure specifications
- **[Best Practices](python_pipeline/best-practices.md)** - Implementation guidelines
- **[Troubleshooting](python_pipeline/troubleshooting.md)** - Common issues and solutions

## What is the Pure Python Pipeline?

The Pure Python Pipeline is a high-performance, deterministic alternative to AI-based portfolio analysis that delivers:

- **10-20x faster** execution
- **100% cost reduction** (zero LLM calls)
- **Deterministic results** (same inputs = same outputs)
- **Full integration** with deep analysis, A+ discovery, backtesting, and reporting

## Components

The pipeline consists of four main components:

1. **[Portfolio Deep Analyzer](python_pipeline/components.md#portfolio-deep-analyzer)** - Pure Python scoring engine
2. **[A+ Discovery Integrator](python_pipeline/components.md#aplus-discovery-integrator)** - Opportunity identification
3. **[Backtesting Pipeline Connector](python_pipeline/components.md#backtesting-pipeline-connector)** - Performance validation
4. **[Python Report Generator](python_pipeline/components.md#python-report-generator)** - Template-based reporting

[View detailed component documentation →](python_pipeline/components.md)

## Performance

### Speed Comparison

| Component | AI-Based | Python-Based | Improvement |
|-----------|----------|--------------|-------------|
| Deep Analysis (per holding) | 30-60s | <1s | 30-60x faster |
| Total (5 holdings) | 5-10 min | 10-20s | 15-30x faster |

### Cost Comparison

| Component | AI-Based | Python-Based | Savings |
|-----------|----------|--------------|---------|
| Deep Analysis (per holding) | $0.05-0.10 | $0.00 | 100% |
| Total (5 holdings) | $0.65-1.35 | $0.00 | 100% |

[View detailed performance metrics →](python_pipeline/overview.md#performance-comparison)

## Quick Start

```python
from finwiz.scoring.portfolio_deep_analyzer import analyze_portfolio_with_python
from finwiz.integration.aplus_discovery_integrator import integrate_aplus_discovery_with_deep_analysis
from finwiz.integration.backtesting_pipeline_connector import connect_backtesting_to_discovery_results
from finwiz.reporting.python_report_generator import generate_python_report

# Run complete pipeline
analysis_results = analyze_portfolio_with_python(holdings, session_id)
discovery_results = integrate_aplus_discovery_with_deep_analysis(session_id)
backtesting_results = connect_backtesting_to_discovery_results(session_id)
report_path = generate_python_report(portfolio_review, analysis_results, session_id)
```

[View complete usage guide →](../how-to/use_python_pipeline.md)

## Documentation Structure

### Explanations (Understanding)

- **[Overview](python_pipeline/overview.md)** - Introduction and key benefits
- **[Components](python_pipeline/components.md)** - Detailed component documentation
- **[Data Flow](python_pipeline/data-flow.md)** - Complete data flow architecture
- **[JSON Exports](python_pipeline/json-exports.md)** - Export structure specifications
- **[Best Practices](python_pipeline/best-practices.md)** - Implementation guidelines
- **[Troubleshooting](python_pipeline/troubleshooting.md)** - Common issues and solutions

### How-to Guides (Problem-solving)

- **[Use Python Pipeline](../how-to/use_python_pipeline.md)** - Step-by-step usage instructions

### Reference (Information)

- **[API Reference](../reference/integration/python_pipeline_integration.md)** - Complete API documentation

## Getting Started

1. **[Read the overview](python_pipeline/overview.md)** to understand the pipeline
2. **[Learn about components](python_pipeline/components.md)** to see how it works
3. **[Follow the how-to guide](../how-to/use_python_pipeline.md)** to implement it
4. **[Review best practices](python_pipeline/best-practices.md)** to optimize your implementation

## Related Documentation

- **[How-to Guide](../how-to/use_python_pipeline.md)** - Step-by-step usage instructions
- **[API Reference](../reference/integration/python_pipeline_integration.md)** - Complete API documentation
