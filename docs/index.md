---
layout: default
title: Home
nav_order: 1
---

# FinWiz Documentation

Welcome to the FinWiz documentation! FinWiz is a sophisticated AI-powered financial analysis platform built with CrewAI, leveraging autonomous AI agents to perform comprehensive analysis of stocks, ETFs, cryptocurrencies, and portfolios.

## What is FinWiz?

FinWiz emphasizes **AI Minimalism** - using Python for deterministic tasks and AI only where reasoning is required:

- **Comprehensive Asset Analysis**: Deep analysis of stocks, ETFs, and cryptocurrencies
- **AI-Powered Insights**: Autonomous agents for research requiring reasoning
- **Python Scoring Engine**: 100% deterministic calculations with 10-20x speedup
- **Portfolio Management**: Review, rebalancing, and optimization
- **A+ Investment Discovery**: Proactive opportunity discovery
- **Quantitative Analysis**: Professional-grade libraries (Backtrader, TA-Lib, QuantLib)

## Quick Start

New to FinWiz? Start here:

1. **[User Guide](USER_GUIDE.md)** - Complete guide for using FinWiz
   - Installation and setup
   - Core features and capabilities
   - Portfolio analysis workflows
   - Configuration and troubleshooting

2. **[Developer Guide](DEVELOPER_GUIDE.md)** - Architecture and development
   - System architecture overview
   - Code organization and patterns
   - Creating custom crews
   - Testing and deployment

3. **[Getting Started Tutorial](tutorials/getting_started.md)** - Step-by-step walkthrough
   - First-time setup
   - Running your first analysis
   - Understanding outputs

## Documentation Structure

Our documentation follows the [Diátaxis framework](https://diataxis.fr/) for clear, organized information:

### 📚 [Tutorials](tutorials/index.md)

**Learning-oriented** - Step-by-step lessons to get you started with FinWiz.

- [Getting Started](tutorials/getting_started.md) - Complete setup and configuration
- [First Analysis](tutorials/first_analysis.md) - Your first stock analysis
- [Portfolio Analysis](tutorials/portfolio_analysis.md) - Comprehensive portfolio review

### 🛠️ [How-to Guides](how-to/index.md)

**Problem-solving** - Practical guides for specific tasks and configurations.

- [Setup Environment](how-to/setup_environment.md) - Environment configuration
- [Performance Optimization](how-to/performance_optimization.md) - Speed up analysis
- [Batch Processing](how-to/BATCH_PROCESSING.md) - High-performance portfolio analysis
- [Python Scoring Engine](how-to/PYTHON_SCORING_ENGINE.md) - Deterministic scoring
- [Template Configuration](how-to/template_configuration.md) - Customize reports

### 📖 [Reference](reference/index.md)

**Information-oriented** - Technical reference for APIs, schemas, and commands.

- [API Reference](reference/api/index.md) - Complete API documentation
- [CLI Commands](reference/cli_commands.md) - Command-line interface
- [Schema Documentation](reference/schemas/index.md) - Data models and validation
- [Environment Variables](reference/environment_variables.md) - Configuration reference

### 💡 [Explanations](explanations/index.md)

**Understanding-oriented** - Conceptual guides to understand FinWiz's architecture and design.

- [Architecture](explanations/ARCHITECTURE.md) - System design overview
- [Design Principles](explanations/design_principles.md) - Core philosophy
- [AI Architecture](explanations/ai_architecture.md) - AI agent framework
- [Flow Architecture](explanations/flow_architecture.md) - CrewAI Flow orchestration
- [Testing Strategy](explanations/testing_strategy.md) - Testing approach

## Key Features

### AI Minimalism Philosophy

**Principle**: Use Python for deterministic tasks, AI only where reasoning is required.

**Benefits**:

- **10-20x Faster**: Deterministic Python analysis vs AI-based processing
- **100% Cost Reduction**: Zero LLM calls for calculations
- **Deterministic Results**: Same input always produces same output
- **Easier Testing**: Mathematical formulas are testable and auditable

**When to Use AI**:

- ✅ Analysis requiring reasoning (interpreting complex financial data)
- ✅ Synthesis of complex information (combining multiple data sources)
- ✅ Natural language understanding (parsing text)
- ✅ Creative content generation (writing analysis narratives)

**When to Use Python**:

- ❌ HTML generation (use Jinja2 templates)
- ❌ Data consolidation (use Python functions)
- ❌ Calculations and formulas (use Python/numpy)
- ❌ Data validation (use Pydantic)
- ❌ Template rendering (use Jinja2)

### Multi-Asset Analysis

- **Stocks**: Fundamental analysis using 10-K filings, technical indicators, sector comparisons
- **ETFs**: Expense ratio analysis, tracking error assessment, holdings diversification
- **Cryptocurrencies**: Technical analysis, volatility patterns, regulatory risk assessment

### Python Scoring Engine

Replace AI-based calculations with deterministic Python for maximum performance:

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()
result = scorer.calculate_composite_score(
    ticker="AAPL",
    asset_class="stock",
    data={"roe": 0.25, "debt_to_equity": 0.3, "revenue_growth": 0.15}
)

# Results: Grade: A, Score: 0.78, Recommendation: BUY
```

**Performance Comparison**:

- AI-based scoring: 45-90 seconds per holding
- Python scoring: 2-5 seconds per holding
- **Speedup**: 10-20x faster
- **Cost**: 100% reduction (zero LLM calls)

### Batch Processing

High-performance portfolio analysis with concurrent execution:

**Configuration**:

```bash
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5  # Concurrent crews
BATCH_PREFETCH_MIN_HOLDINGS=10
```

**Performance**:

- 66 holdings: 5.5-11 hours → 20-40 minutes (10-20x speedup)
- Data pre-fetch: 2-5 seconds (Yahoo Finance)
- Concurrent execution: 5 crews in parallel (configurable)

### Portfolio Management

- **Portfolio Review**: Automated evaluation with keep/sell recommendations
- **Deep Analysis**: Comprehensive per-holding analysis with grading (A+ to F)
- **Alternative Suggestions**: For holdings marked "SELL"
- **Rebalancing**: Professional-grade optimization with multiple strategies
- **Cost Analysis**: Transaction costs, tax implications, opportunity cost

### A+ Investment Discovery

Proactive discovery of exceptional investment opportunities:

- **Market Screening**: Scan entire universes (S&P 500, crypto markets, etc.)
- **Deep Analysis**: Comprehensive analysis of candidates
- **Grade Validation**: Only A+ grade (score ≥ 0.95) assets reported
- **Monitoring**: Track discovered opportunities over time

### Quantitative Analysis

Professional-grade quantitative analysis framework:

- **Backtesting**: Backtrader-based strategy testing
- **Technical Analysis**: TA-Lib indicators (50+ indicators)
- **Portfolio Optimization**: PyPortfolioOpt integration
- **Derivatives Pricing**: QuantLib integration
- **Risk Management**: VaR, CVaR, stress testing

## Documentation Features

### Professional Documentation System

- **GitHub Pages**: Clean, fast documentation with Jekyll
- **Mobile Responsive**: Optimized experience across all devices
- **Full-Text Search**: GitHub search integration
- **Professional Navigation**: Clear hierarchical structure
- **Diátaxis Framework**: Organized by documentation type

### Interactive Documentation

- **Code Examples**: Practical, runnable examples throughout
- **API Explorer**: Interactive API reference
- **Schema Browser**: Browse and validate Pydantic schemas
- **Configuration Guide**: Environment variable reference

## Getting Help

### Core Documentation

- **[User Guide](USER_GUIDE.md)** - Complete user documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Architecture and development
- **[API Reference](reference/api/index.md)** - API documentation
- **[Tutorials](tutorials/index.md)** - Learning-oriented guides

### Troubleshooting

- **[Troubleshooting Guide](how-to/troubleshooting.md)** - Common issues and solutions
- **[Performance Guide](how-to/performance_optimization.md)** - Optimization tips
- **[Testing Guide](how-to/testing.md)** - Testing strategies

### Community

- **GitHub Repository**: [finwiz/finwiz](https://github.com/fjacquet/finwiz)
- **Issue Tracker**: [Report bugs and request features](https://github.com/fjacquet/finwiz/issues)
- **Discussions**: [Community Q&A](https://github.com/fjacquet/finwiz/discussions)

## Quick Links

### For Users

- [Installation Guide](USER_GUIDE.md#installation)
- [First Analysis](tutorials/first_analysis.md)
- [Portfolio Analysis](USER_GUIDE.md#portfolio-analysis)
- [Configuration Reference](reference/environment_variables.md)
- [Troubleshooting](how-to/troubleshooting.md)

### For Developers

- [Architecture Overview](DEVELOPER_GUIDE.md#architecture-overview)
- [Development Setup](DEVELOPER_GUIDE.md#development-setup)
- [Creating Custom Crews](DEVELOPER_GUIDE.md#creating-custom-crews)
- [Testing Guide](DEVELOPER_GUIDE.md#testing)
- [Contributing](DEVELOPER_GUIDE.md#contributing)

### Key Features

- [AI Minimalism](explanations/ai_vs_rules.md)
- [Python Scoring Engine](how-to/PYTHON_SCORING_ENGINE.md)
- [Batch Processing](how-to/BATCH_PROCESSING.md)
- [Portfolio Rebalancing](how-to/risk_management.md)
- [A+ Discovery](explanations/deep_analysis.md)

## System Requirements

### Minimum Requirements

- Python 3.12+ (3.13 not supported)
- 2GB RAM (4GB+ recommended)
- 1GB free storage
- Internet connection for API access

### Required API Keys

- **OPENAI_API_KEY**: OpenAI API for LLM operations
- **SERPER_API_KEY**: Google search via Serper

### Optional API Keys

- ALPHA_VANTAGE_API_KEY - Financial data
- TWELVE_DATA_API_KEY - Technical indicators
- CHART_IMG_API_KEY - Chart generation
- COINMARKETCAP_API_KEY - Cryptocurrency data
- PPLX_API_KEY - Perplexity research

## Architecture Overview

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

## Core Design Principles

1. **AI Minimalism**: Use Python for deterministic tasks, AI only for reasoning
2. **Pydantic-First**: All outputs validated with strict schemas
3. **File-Based Data Passing**: Pass file paths (not data) between crews
4. **Concurrent Execution**: SME crews run in parallel for maximum performance
5. **Clean Separation**: Analysis (AI) vs presentation (Python templates)

## Version Information

- **Current Version**: 0.1.0
- **Python Version**: 3.12+
- **CrewAI Version**: 0.120.1+
- **Documentation Updated**: 2025-01-18

## License

FinWiz is released under the MIT License. See the [LICENSE](https://github.com/fjacquet/finwiz/blob/main/LICENSE) file for details.

---

**Ready to get started?** Check out the [User Guide](USER_GUIDE.md) or jump into a [tutorial](tutorials/getting_started.md)!

---

*Documentation built with Jekyll and hosted on GitHub Pages*
