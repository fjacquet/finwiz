---
layout: default
title: User Guide
nav_order: 2
---

# FinWiz User Guide

Complete guide for using FinWiz, from installation to advanced portfolio analysis.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Features](#core-features)
4. [Portfolio Analysis](#portfolio-analysis)
5. [Investment Discovery](#investment-discovery)
6. [Portfolio Rebalancing](#portfolio-rebalancing)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Introduction

### What is FinWiz?

FinWiz is a sophisticated AI-powered financial analysis platform that uses autonomous AI agents to perform comprehensive analysis of stocks, ETFs, cryptocurrencies, and portfolios. Built on CrewAI, FinWiz emphasizes **AI Minimalism** - using Python for deterministic calculations and AI only where reasoning is required.

### Key Capabilities

- **Multi-Asset Analysis**: Comprehensive analysis of stocks, ETFs, and cryptocurrencies
- **Portfolio Review**: Automated portfolio evaluation with keep/sell recommendations
- **Portfolio Rebalancing**: Professional-grade optimization with cost analysis
- **A+ Investment Discovery**: Proactive discovery of exceptional opportunities
- **Quantitative Analysis**: Backtrader, TA-Lib, and QuantLib integration
- **Python Scoring Engine**: 10-20x speedup with deterministic calculations
- **Batch Processing**: High-performance portfolio analysis

### Architecture Philosophy

FinWiz follows these core principles:

1. **AI Minimalism**: Use Python for deterministic tasks, AI only for reasoning
2. **Data Quality First**: Fail fast, never hallucinate, ensure transparency
3. **Performance Optimization**: Batch processing, caching, and smart routing
4. **Pydantic-First**: All outputs validated with strict schemas
5. **Clean Separation**: Analysis (AI) vs presentation (Python templates)

## Getting Started

### Prerequisites

**System Requirements**:

- **Python**: 3.12+ (3.13 not supported)
- **Package Manager**: `uv` (recommended) or `pip`
- **Operating System**: Linux, macOS, or Windows with WSL
- **Memory**: Minimum 2GB RAM (4GB+ recommended for batch processing)
- **Storage**: Minimum 1GB free space

**Required API Keys**:

All FinWiz operations require these API keys:

- **OPENAI_API_KEY**: OpenAI API for LLM operations ([Get key](https://platform.openai.com/api-keys))
- **SERPER_API_KEY**: Google search via Serper ([Get key](https://serper.dev/))

**Optional API Keys** (for enhanced features):

- **FIRECRAWL_API_KEY**: Advanced web scraping ([Get key](https://firecrawl.dev/))
- **ALPHA_VANTAGE_API_KEY**: Financial data ([Get key](https://www.alphavantage.co/support/#api-key))
- **CHART_IMG_API_KEY**: Professional chart generation
- **TWELVE_DATA_API_KEY**: Technical indicators and market data
- **COINMARKETCAP_API_KEY**: Cryptocurrency data
- **PPLX_API_KEY**: Perplexity Sonar for enhanced research

### Installation

#### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/finwiz.git
cd finwiz
```

#### Step 2: Install Dependencies

**Using uv (Recommended)**:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync

# Verify installation
uv run python -c "import finwiz; print('✅ Installation successful')"
```

**Using pip**:

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
python -c "import finwiz; print('✅ Installation successful')"
```

#### Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env  # or your preferred editor
```

**Minimum Configuration**:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-key-here

# Optional API Keys
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key-here
TWELVE_DATA_API_KEY=your-twelve-data-key-here
CHART_IMG_API_KEY=your-chart-img-key-here
COINMARKETCAP_API_KEY=your-coinmarketcap-key-here
PPLX_API_KEY=your-perplexity-key-here

# Validation Configuration
VALIDATION_STRICTNESS=warn  # off, warn, error

# Caching Configuration
CACHE_BACKEND=hybrid        # memory, file, hybrid
CACHE_TTL=2700             # 45 minutes (in seconds)
CACHE_MAX_MEMORY_ITEMS=1000
CACHE_MAX_FILE_SIZE_MB=100

# Performance Optimization
BATCH_PREFETCH_ENABLED=true
DEEP_ANALYSIS_BATCH_SIZE=5
BATCH_PREFETCH_MIN_HOLDINGS=10
RISK_ASSESSMENT_USE_MINI=true
```

#### Step 4: Verify Setup

Run the health check to verify everything is configured correctly:

```bash
# Using uv
uv run python -c "from finwiz.utils import verify_setup; verify_setup()"

# Using pip
python -c "from finwiz.utils import verify_setup; verify_setup()"
```

### Quick Start Tutorial

#### Your First Analysis: Analyzing a Single Stock

Let's analyze Apple (AAPL) to understand the basics:

```bash
# Run single stock analysis
crewai flow kickoff
```

When prompted:

1. Choose "Single Asset Analysis"
2. Enter ticker: `AAPL`
3. Select asset class: `stock`

The analysis will:

- Fetch real-time market data
- Perform fundamental analysis
- Calculate technical indicators
- Generate risk assessment
- Provide BUY/HOLD/SELL recommendation
- Create HTML report with charts

**Expected Output**:

```
✓ Data fetched (2.3s)
✓ Fundamental analysis complete (15.4s)
✓ Technical analysis complete (8.7s)
✓ Risk assessment complete (5.2s)
✓ Report generated (1.1s)

Grade: A
Score: 0.85
Recommendation: BUY
Risk Level: 4/10 (Moderate)

Report: output/reports/[session-id]/stock_crew/AAPL_report.html
```

#### Analyzing Your Portfolio

Prepare your portfolio CSV files:

**Stock Portfolio** (`data/stock.csv`):

```csv
ticker,quantity,purchase_price,purchase_date
AAPL,100,150.00,2023-01-15
MSFT,50,320.00,2023-02-20
GOOGL,75,140.00,2023-03-10
```

**ETF Portfolio** (`data/etf.csv`):

```csv
ticker,quantity,purchase_price,purchase_date
VOO,200,380.00,2023-01-05
QQQ,100,350.00,2023-02-15
```

Run portfolio analysis:

```bash
# Full portfolio review
crewai flow kickoff

# Select "Portfolio Review"
# Analysis runs automatically on configured CSV files
```

The system will:

1. Analyze each holding individually
2. Generate keep/sell recommendations
3. Suggest alternatives for sell recommendations
4. Calculate portfolio metrics (diversification, risk, etc.)
5. Create comprehensive HTML report

## Core Features

### 1. Single Asset Analysis

Deep analysis of individual stocks, ETFs, or cryptocurrencies.

#### Stock Analysis

Comprehensive analysis including:

- **Fundamental Analysis**: P/E ratio, EPS, revenue growth, profit margins
- **Technical Analysis**: Moving averages, RSI, MACD, Bollinger Bands
- **Sentiment Analysis**: News sentiment, social media buzz, analyst ratings
- **Risk Assessment**: Volatility, beta, sector risks, market conditions
- **Valuation**: Fair value estimation, price targets, DCF analysis

**Example**:

```python
from finwiz.crews.stock_crew import StockCrew

crew = StockCrew()
result = crew.crew().kickoff(inputs={
    "ticker": "NVDA",
    "asset_class": "stock"
})

print(f"Grade: {result.grade}")
print(f"Score: {result.composite_score}")
print(f"Recommendation: {result.recommendation}")
```

#### ETF Analysis

ETF-specific metrics:

- **Expense Ratio Analysis**: Cost efficiency evaluation
- **Tracking Error**: How well ETF tracks its index
- **Holdings Diversification**: Portfolio composition analysis
- **Liquidity Analysis**: Trading volume and bid-ask spreads
- **Sector Allocation**: Sector exposure breakdown

**Example**:

```python
from finwiz.crews.etf_crew import ETFCrew

crew = ETFCrew()
result = crew.crew().kickoff(inputs={
    "ticker": "SPY",
    "asset_class": "etf"
})
```

#### Cryptocurrency Analysis

Crypto-specific evaluation:

- **Technical Analysis**: Price patterns, volume, momentum indicators
- **Volatility Assessment**: Risk metrics specific to crypto markets
- **Market Sentiment**: Social media trends, community engagement
- **Regulatory Risk**: Legal and compliance considerations
- **Adoption Metrics**: Network activity, developer engagement

**Example**:

```python
from finwiz.crews.crypto_crew import CryptoCrew

crew = CryptoCrew()
result = crew.crew().kickoff(inputs={
    "ticker": "BTC-USD",
    "asset_class": "crypto"
})
```

### 2. Python Scoring Engine

Deterministic scoring engine that replaces AI-based calculations for 10-20x speedup and 100% cost reduction.

#### Why Use Python Scoring?

- **Speed**: 10-20x faster than AI-based scoring
- **Cost**: 100% cost reduction (zero LLM calls)
- **Consistency**: Same input always produces same output
- **Transparency**: Mathematical formulas are auditable

#### Using the Scorer

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()

# Calculate composite score
result = scorer.calculate_composite_score(
    ticker="AAPL",
    asset_class="stock",
    data={
        "roe": 0.25,
        "debt_to_equity": 0.3,
        "revenue_growth": 0.15,
        "profit_margin": 0.22,
        "pe_ratio": 28.5,
        "current_ratio": 1.1,
        # ... other metrics
    }
)

print(f"Grade: {result.grade}")  # A, B+, C, etc.
print(f"Score: {result.composite_score}")  # 0.0 - 1.0
print(f"Recommendation: {result.recommendation}")  # BUY, HOLD, SELL
print(f"Reasoning: {result.reasoning}")
```

#### Scoring Breakdown

Scores are calculated based on:

**Stock Scoring (40/30/30 weighting)**:

- **Fundamental Score (40%)**: ROE, debt ratios, growth metrics
- **Technical Score (30%)**: Price trends, momentum indicators
- **Sentiment Score (30%)**: News sentiment, analyst ratings

**ETF Scoring (45/30/25 weighting)**:

- **Expense & Tracking (45%)**: Cost efficiency, tracking accuracy
- **Holdings Quality (30%)**: Diversification, concentration risk
- **Performance (25%)**: Returns, Sharpe ratio

**Crypto Scoring (30/40/30 weighting)**:

- **Technical (30%)**: Price patterns, volume trends
- **Sentiment (40%)**: Social buzz, community strength
- **Adoption (30%)**: Network metrics, developer activity

#### Grade Scale

| Grade | Score Range | Meaning | Recommendation |
|-------|-------------|---------|----------------|
| A+ | 0.95 - 1.00 | Exceptional | Strong BUY |
| A | 0.85 - 0.94 | Excellent | BUY |
| B+ | 0.75 - 0.84 | Very Good | BUY |
| B | 0.65 - 0.74 | Good | HOLD/BUY |
| C+ | 0.55 - 0.64 | Above Average | HOLD |
| C | 0.45 - 0.54 | Average | HOLD |
| D | 0.35 - 0.44 | Below Average | SELL/HOLD |
| F | 0.00 - 0.34 | Poor | SELL |

### 3. Batch Processing

High-performance portfolio analysis with 10-20x speedup for large portfolios.

#### When to Use Batch Processing

- **Portfolio Size**: 10+ holdings (configured via `BATCH_PREFETCH_MIN_HOLDINGS`)
- **Time Constraints**: Need results faster than sequential processing
- **Resource Availability**: Have adequate CPU/memory for parallel execution

#### How Batch Processing Works

1. **Data Pre-fetch**: All ticker data fetched in parallel (2-5 seconds)
2. **Concurrent Execution**: Multiple crews run simultaneously
3. **Resource Management**: Configurable concurrency limit
4. **Result Aggregation**: Automatic consolidation of results

#### Configuration

Enable batch processing in `.env`:

```bash
# Enable batch processing
BATCH_PREFETCH_ENABLED=true

# Number of concurrent crews (adjust based on CPU/memory)
DEEP_ANALYSIS_BATCH_SIZE=5

# Minimum holdings to trigger batch mode
BATCH_PREFETCH_MIN_HOLDINGS=10

# Data source optimization
ENABLE_ALPHA_VANTAGE=false  # Yahoo Finance is faster for batch
```

#### Performance Comparison

| Portfolio Size | Sequential | Batch (5 concurrent) | Speedup |
|----------------|-----------|----------------------|---------|
| 10 holdings | 50 min | 15 min | 3.3x |
| 25 holdings | 2.1 hours | 18 min | 7.0x |
| 66 holdings | 5.5 hours | 30 min | 11.0x |
| 100 holdings | 8.3 hours | 45 min | 11.1x |

#### Monitoring Batch Jobs

```python
from finwiz.utils.logging_helpers import CrewLogger

logger = CrewLogger("BatchMonitor")

# Check batch status
logger.info("Batch started with 5 concurrent workers")
logger.info(f"Processing {len(holdings)} holdings")

# Progress tracking
logger.info(f"Completed: {completed}/{total} ({progress:.1f}%)")
```

## Portfolio Analysis

### Portfolio Review

Comprehensive evaluation of your entire portfolio with individual holding analysis.

#### Preparing Portfolio Data

Create CSV files with your holdings:

**Stock Portfolio Format** (`data/stock.csv`):

```csv
ticker,quantity,purchase_price,purchase_date
AAPL,100,150.00,2023-01-15
MSFT,50,320.00,2023-02-20
GOOGL,75,140.00,2023-03-10
NVDA,25,450.00,2023-04-05
TSLA,40,200.00,2023-05-12
```

**ETF Portfolio Format** (`data/etf.csv`):

```csv
ticker,quantity,purchase_price,purchase_date
VOO,200,380.00,2023-01-05
QQQ,100,350.00,2023-02-15
VTI,150,220.00,2023-03-20
```

**Field Descriptions**:

- `ticker`: Stock symbol (e.g., AAPL, MSFT)
- `quantity`: Number of shares owned
- `purchase_price`: Price per share at purchase
- `purchase_date`: Date of purchase (YYYY-MM-DD)

#### Running Portfolio Review

```bash
# Interactive mode
crewai flow kickoff

# Select "Portfolio Review" from menu
```

**Programmatic Usage**:

```python
from finwiz.orchestrators.portfolio_review import PortfolioReviewOrchestrator

orchestrator = PortfolioReviewOrchestrator()

# Run full portfolio review
results = orchestrator.run_portfolio_review(
    stock_csv="data/stock.csv",
    etf_csv="data/etf.csv"
)

# Access results
for holding in results.holdings:
    print(f"{holding.ticker}: {holding.recommendation}")
    print(f"  Grade: {holding.grade}")
    print(f"  Score: {holding.composite_score}")
    print(f"  Reasoning: {holding.reasoning}")
```

#### Review Output

The portfolio review generates:

1. **Individual Holding Reports**: HTML report for each ticker
2. **Keep/Sell Recommendations**: Clear actionable decisions
3. **Alternative Suggestions**: For holdings marked "SELL"
4. **Portfolio Metrics**: Overall risk, diversification, performance
5. **Executive Summary**: High-level portfolio health assessment

**Example Output Structure**:

```
output/reports/[session-id]/
├── portfolio_summary.html          # Executive summary
├── stock_crew/
│   ├── AAPL_report.html           # Individual reports
│   ├── MSFT_report.html
│   └── GOOGL_report.html
├── etf_crew/
│   ├── VOO_report.html
│   └── QQQ_report.html
└── alternatives/
    ├── AAPL_alternatives.html     # Alternative suggestions
    └── MSFT_alternatives.html
```

#### Understanding Recommendations

**KEEP Recommendations**:

- Grade: A+ to B+ (score ≥ 0.75)
- Strong fundamentals
- Positive technical outlook
- Acceptable risk level

**SELL Recommendations**:

- Grade: D or F (score < 0.45)
- Weak fundamentals
- Negative technical indicators
- High risk or deteriorating metrics

**HOLD Recommendations**:

- Grade: B to C (score 0.45 - 0.74)
- Mixed signals
- Moderate risk
- May improve or deteriorate

#### Alternative Suggestions

For each SELL recommendation, FinWiz suggests alternatives:

```json
{
  "original_ticker": "XYZ",
  "original_grade": "D",
  "alternatives": [
    {
      "ticker": "ABC",
      "grade": "A",
      "score": 0.88,
      "reasoning": "Similar sector exposure with stronger fundamentals"
    },
    {
      "ticker": "DEF",
      "grade": "A-",
      "score": 0.82,
      "reasoning": "Better risk-adjusted returns with lower volatility"
    }
  ]
}
```

## Investment Discovery

Proactive discovery of exceptional investment opportunities (A+ grade, score ≥ 0.95).

### A+ Discovery System

The A+ Discovery system continuously scans markets for top-tier investment opportunities.

#### How It Works

1. **Market Screening**: Scan entire universes (S&P 500, crypto markets, etc.)
2. **Initial Filtering**: Apply quantitative filters (liquidity, market cap, etc.)
3. **Deep Analysis**: Comprehensive analysis of candidates
4. **Grade Validation**: Only A+ grade (score ≥ 0.95) assets reported
5. **Monitoring**: Track discovered opportunities over time

#### Running A+ Discovery

**Interactive Mode**:

```bash
crewai flow kickoff

# Select "A+ Investment Discovery"
# Choose asset class: Stock, ETF, or Crypto
```

**Programmatic Usage**:

```python
from finwiz.crews.investment_discovery_crew import InvestmentDiscoveryCrew

crew = InvestmentDiscoveryCrew()

# Discover exceptional stocks
results = crew.crew().kickoff(inputs={
    "asset_class": "stock",
    "market_cap_min": 10_000_000_000,  # $10B minimum
    "liquidity_min": 1_000_000         # $1M daily volume
})

# Access discoveries
for opportunity in results.discoveries:
    print(f"{opportunity.ticker}: {opportunity.grade}")
    print(f"  Score: {opportunity.score}")
    print(f"  Why A+: {opportunity.reasoning}")
```

#### Discovery Criteria

**Stock Discovery**:

- Market cap: ≥ $10B (large cap)
- Daily volume: ≥ $1M
- ROE: ≥ 20%
- Debt-to-equity: ≤ 0.5
- Revenue growth: ≥ 15% YoY
- P/E ratio: Reasonable relative to growth

**ETF Discovery**:

- Assets under management: ≥ $1B
- Expense ratio: ≤ 0.20%
- Tracking error: ≤ 0.50%
- Average volume: ≥ 100,000 shares/day
- 3-year return: Top quartile in category

**Crypto Discovery**:

- Market cap: ≥ $1B
- Daily volume: ≥ $100M
- Network activity: High and growing
- Developer activity: Active and consistent
- Regulatory status: Favorable or neutral

#### Discovery Output

```json
{
  "discoveries": [
    {
      "ticker": "NVDA",
      "grade": "A+",
      "composite_score": 0.96,
      "recommendation": "BUY",
      "reasoning": "Exceptional AI/GPU market position with 45% revenue growth",
      "metrics": {
        "fundamental_score": 0.95,
        "technical_score": 0.97,
        "sentiment_score": 0.96
      },
      "discovered_date": "2025-01-18",
      "price_at_discovery": 875.50
    }
  ],
  "total_screened": 500,
  "total_analyzed": 25,
  "total_discovered": 1
}
```

### Continuous Monitoring

Track discovered opportunities over time:

```bash
# Enable monitoring
export A_PLUS_MONITORING=true
export MONITORING_INTERVAL=24  # hours

# Run discovery with monitoring
crewai flow kickoff --monitor
```

Monitoring features:

- Price change alerts
- Grade degradation warnings
- Entry point suggestions
- Performance tracking

## Portfolio Rebalancing

Professional-grade portfolio optimization with intelligent trade recommendations.

### Rebalancing Overview

Portfolio rebalancing optimizes your holdings to:

- Achieve target asset allocation
- Minimize transaction costs
- Manage risk exposure
- Improve risk-adjusted returns

### Rebalancing Strategies

FinWiz supports multiple optimization strategies:

#### 1. Target Allocation

Rebalance to achieve specific allocation targets.

**Example Configuration**:

```json
{
  "strategy": "target_allocation",
  "targets": {
    "stocks": 0.60,
    "etfs": 0.30,
    "crypto": 0.10
  },
  "tolerance": 0.05  # 5% tolerance band
}
```

#### 2. Risk Parity

Equal risk contribution from each asset.

```json
{
  "strategy": "risk_parity",
  "risk_metric": "volatility",
  "constraints": {
    "max_position": 0.25,
    "min_position": 0.05
  }
}
```

#### 3. Mean-Variance Optimization

Maximize Sharpe ratio (risk-adjusted return).

```json
{
  "strategy": "mean_variance",
  "objective": "max_sharpe",
  "risk_free_rate": 0.045,
  "constraints": {
    "max_position": 0.30,
    "min_position": 0.02
  }
}
```

#### 4. Black-Litterman

Incorporate market equilibrium with your views.

```json
{
  "strategy": "black_litterman",
  "market_caps": {
    "AAPL": 2_800_000_000_000,
    "MSFT": 2_500_000_000_000
  },
  "views": {
    "AAPL": {"expected_return": 0.15, "confidence": 0.8},
    "MSFT": {"expected_return": 0.12, "confidence": 0.7}
  }
}
```

### Running Rebalancing

**Interactive Mode**:

```bash
crewai flow kickoff

# Select "Portfolio Rebalancing"
# Choose strategy
# Review recommendations
# Approve trades
```

**Programmatic Usage**:

```python
from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator

orchestrator = PortfolioRebalancingOrchestrator()

# Run rebalancing
result = orchestrator.run_rebalancing(
    portfolio_csv="data/portfolio.csv",
    strategy="mean_variance",
    total_value=100_000,
    optimization_params={
        "objective": "max_sharpe",
        "risk_free_rate": 0.045,
        "max_position": 0.30
    }
)

# Access trade recommendations
for trade in result.trades:
    print(f"{trade.action} {trade.quantity} {trade.ticker}")
    print(f"  Estimated cost: ${trade.estimated_cost:.2f}")
```

### Rebalancing Output

```json
{
  "current_allocation": {
    "AAPL": 0.35,
    "MSFT": 0.25,
    "GOOGL": 0.20,
    "VOO": 0.15,
    "QQQ": 0.05
  },
  "target_allocation": {
    "AAPL": 0.30,
    "MSFT": 0.25,
    "GOOGL": 0.20,
    "VOO": 0.20,
    "QQQ": 0.05
  },
  "trades": [
    {
      "ticker": "AAPL",
      "action": "SELL",
      "quantity": 10,
      "current_price": 175.50,
      "estimated_cost": 14.75,
      "reasoning": "Reduce overweight position"
    },
    {
      "ticker": "VOO",
      "action": "BUY",
      "quantity": 15,
      "current_price": 420.00,
      "estimated_cost": 31.50,
      "reasoning": "Increase to target allocation"
    }
  ],
  "total_cost": 46.25,
  "expected_improvement": {
    "sharpe_ratio": 0.15,
    "volatility_reduction": 0.02
  }
}
```

### Cost Analysis

FinWiz provides detailed transaction cost analysis:

- **Trading Fees**: Brokerage commissions
- **Bid-Ask Spread**: Market impact costs
- **Tax Implications**: Capital gains estimates
- **Opportunity Cost**: Impact of cash drag

**Example**:

```python
from finwiz.quantitative.cost_analyzer import CostAnalyzer

analyzer = CostAnalyzer()

costs = analyzer.analyze_trade_costs(
    trades=result.trades,
    commission_per_trade=0.00,  # Zero-commission broker
    spread_percent=0.001,       # 0.1% spread
    tax_rate=0.20               # 20% capital gains
)

print(f"Total trading costs: ${costs.total_costs:.2f}")
print(f"Estimated tax impact: ${costs.tax_impact:.2f}")
```

## Configuration

### Environment Variables

Complete reference of all configuration options.

#### Required Settings

```bash
# API Keys (Required)
OPENAI_API_KEY=sk-...              # OpenAI API key
SERPER_API_KEY=...                 # Serper API key for web search
```

#### Optional API Keys

```bash
# Enhanced Features
ALPHA_VANTAGE_API_KEY=...          # Financial data
TWELVE_DATA_API_KEY=...            # Technical indicators
CHART_IMG_API_KEY=...              # Chart generation
COINMARKETCAP_API_KEY=...          # Crypto data
PPLX_API_KEY=...                   # Perplexity research
FIRECRAWL_API_KEY=...              # Web scraping
```

#### Validation Settings

```bash
# Validation Strictness
VALIDATION_STRICTNESS=warn         # off | warn | error

# Schema Validation
PYDANTIC_V2_STRICT=true            # Strict Pydantic validation
```

#### Caching Configuration

```bash
# Cache Backend
CACHE_BACKEND=hybrid               # memory | file | hybrid

# Cache TTL
CACHE_TTL=2700                     # 45 minutes (seconds)

# Cache Limits
CACHE_MAX_MEMORY_ITEMS=1000        # Max in-memory items
CACHE_MAX_FILE_SIZE_MB=100         # Max cache file size

# Cache Strategy
CACHE_STRATEGY=ttl                 # ttl | lru | lfu | adaptive
```

#### Performance Settings

```bash
# Batch Processing
BATCH_PREFETCH_ENABLED=true        # Enable batch mode
DEEP_ANALYSIS_BATCH_SIZE=5         # Concurrent crews
BATCH_PREFETCH_MIN_HOLDINGS=10     # Min holdings for batch

# Resource Optimization
RISK_ASSESSMENT_USE_MINI=true      # Use GPT-3.5 for risk
USE_MINIMAL_RISK_TOOLS=true        # Minimal toolset
```

#### Feature Flags

```bash
# Optional Features
FF_PERPLEXITY_RESEARCH=false       # Perplexity integration
PORTFOLIO_REVIEW_ENABLED=true      # Portfolio review
A_PLUS_MONITORING=false            # Continuous monitoring
```

#### Logging Configuration

```bash
# Log Levels
LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR

# Log Destinations
LOG_TO_FILE=true                   # Write to log files
LOG_TO_CONSOLE=true                # Console output
```

#### Data Sources

```bash
# Primary Data Source
ENABLE_ALPHA_VANTAGE=false         # Use Alpha Vantage
DEFAULT_DATA_SOURCE=yahoo          # yahoo | alpha_vantage

# Fallback Sources
ENABLE_FALLBACK_SOURCES=true       # Enable fallbacks
```

### Portfolio Configuration

Configure portfolio CSV file locations:

```bash
# Portfolio Files
PORTFOLIO_STOCK_CSV=data/stock.csv
PORTFOLIO_ETF_CSV=data/etf.csv
PORTFOLIO_CRYPTO_CSV=data/crypto.csv

# Portfolio Settings
PORTFOLIO_BASE_CURRENCY=USD
PORTFOLIO_TAX_RATE=0.20            # 20% capital gains
```

### Advanced Configuration

#### Custom Tool Configuration

Create `config/tools.yaml`:

```yaml
quantitative_analysis:
  enabled: true
  ta_lib_indicators:
    - SMA
    - EMA
    - RSI
    - MACD
  backtest_periods:
    - 1M
    - 3M
    - 1Y
    - 3Y

sentiment_analysis:
  enabled: true
  sources:
    - news
    - social_media
    - analyst_ratings
  confidence_threshold: 0.7
```

#### Custom Agent Configuration

Modify agent behavior in `src/finwiz/crews/*/config/agents.yaml`:

```yaml
analyst:
  role: "Financial Analyst"
  goal: "Perform comprehensive financial analysis"
  backstory: "Expert financial analyst with 20+ years experience"
  max_rpm: 20
  allow_delegation: false
  reasoning: true
  max_reasoning_attempts: 3
```

## Troubleshooting

### Common Issues

#### Issue: "API Key Not Found"

**Symptoms**:

```
Error: OPENAI_API_KEY not found in environment
```

**Solution**:

1. Verify `.env` file exists in project root
2. Check API key is set: `cat .env | grep OPENAI_API_KEY`
3. Reload environment: `source .env` (bash) or restart terminal

#### Issue: "Rate Limit Exceeded"

**Symptoms**:

```
Error: Rate limit exceeded for API key
```

**Solution**:

1. Reduce `DEEP_ANALYSIS_BATCH_SIZE` (e.g., from 5 to 3)
2. Add delays between requests:

   ```bash
   export API_RATE_LIMIT_DELAY=1.0  # 1 second delay
   ```

3. Use API key with higher limits
4. Enable `RISK_ASSESSMENT_USE_MINI=true` to reduce API calls

#### Issue: "Out of Memory"

**Symptoms**:

```
MemoryError: Unable to allocate array
```

**Solution**:

1. Reduce batch size: `DEEP_ANALYSIS_BATCH_SIZE=3`
2. Use file-based cache: `CACHE_BACKEND=file`
3. Limit cache size:

   ```bash
   CACHE_MAX_MEMORY_ITEMS=500
   CACHE_MAX_FILE_SIZE_MB=50
   ```

4. Process portfolio in smaller batches

#### Issue: "Validation Errors"

**Symptoms**:

```
ValidationError: 1 validation error for StockAnalysis
```

**Solution**:

1. Check data quality in CSV files
2. Reduce strictness: `VALIDATION_STRICTNESS=warn`
3. Review error details in logs
4. Update schemas if data format changed

#### Issue: "Slow Performance"

**Symptoms**:

- Analysis takes longer than expected
- High CPU usage

**Solution**:

1. Enable batch processing: `BATCH_PREFETCH_ENABLED=true`
2. Use faster models: `RISK_ASSESSMENT_USE_MINI=true`
3. Optimize caching:

   ```bash
   CACHE_BACKEND=hybrid
   CACHE_STRATEGY=adaptive
   ```

4. Reduce data fetching:

   ```bash
   ENABLE_ALPHA_VANTAGE=false
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export CREW_VERBOSE=true

# Run with debug output
uv run python src/finwiz/main.py 2>&1 | tee debug.log
```

### Log Analysis

Check logs for errors:

```bash
# View recent errors
tail -n 100 logs/finwiz_error.log

# Search for specific issues
grep -i "validation error" logs/finwiz.log
grep -i "api.*failed" logs/finwiz.log
grep -i "timeout" logs/finwiz.log
```

### Health Check

Run system health check:

```python
from finwiz.utils import run_health_check

# Full health check
results = run_health_check(verbose=True)

# Check specific components
results = run_health_check(
    check_apis=True,
    check_cache=True,
    check_data=True,
    check_validation=True
)

print(results.summary())
```

## Best Practices

### Data Quality

1. **Validate Portfolio Data**:
   - Use consistent date format (YYYY-MM-DD)
   - Verify ticker symbols are correct
   - Ensure numeric fields are properly formatted
   - Check for missing or null values

2. **Regular Updates**:
   - Update portfolio CSVs after trades
   - Refresh analysis periodically (weekly/monthly)
   - Monitor for corporate actions (splits, mergers)

3. **Backup Data**:
   - Keep backups of portfolio CSVs
   - Archive historical analysis reports
   - Version control configuration files

### Performance Optimization

1. **Use Batch Processing**:
   - Enable for portfolios with 10+ holdings
   - Adjust `DEEP_ANALYSIS_BATCH_SIZE` based on resources
   - Monitor system resources during batch jobs

2. **Optimize Caching**:
   - Use `hybrid` cache backend for best performance
   - Set appropriate TTL (45 minutes recommended)
   - Clear old cache files regularly

3. **Minimize API Calls**:
   - Use `RISK_ASSESSMENT_USE_MINI=true`
   - Enable `USE_MINIMAL_RISK_TOOLS=true`
   - Disable unused features

### Security

1. **API Key Management**:
   - Never commit `.env` to version control
   - Use environment-specific API keys
   - Rotate keys periodically
   - Use read-only API keys where possible

2. **Data Privacy**:
   - Keep portfolio data private
   - Don't share session IDs or reports
   - Use encrypted backups for sensitive data

3. **Access Control**:
   - Restrict file system permissions
   - Use secure channels for data transfer
   - Monitor access logs

### Cost Management

1. **Optimize LLM Usage**:
   - Use Python scoring engine when possible
   - Enable mini models for simple tasks
   - Batch similar requests
   - Cache results aggressively

2. **Monitor API Costs**:
   - Track OpenAI API usage
   - Set spending limits
   - Review monthly bills
   - Optimize expensive operations

3. **Resource Efficiency**:
   - Use appropriate batch sizes
   - Clean up old reports and logs
   - Optimize cache sizes

### Analysis Workflow

1. **Regular Portfolio Review**:
   - Weekly: Quick health check
   - Monthly: Full portfolio analysis
   - Quarterly: Rebalancing evaluation
   - Annually: Comprehensive strategy review

2. **Decision Making**:
   - Don't blindly follow recommendations
   - Understand the reasoning behind grades
   - Consider your investment goals
   - Account for tax implications

3. **Record Keeping**:
   - Save analysis reports
   - Document trade decisions
   - Track performance over time
   - Review historical recommendations

### Integration with Workflow

1. **CSV Management**:
   - Use spreadsheet for portfolio tracking
   - Export to CSV for FinWiz analysis
   - Update after each trade
   - Validate data before analysis

2. **Report Review**:
   - Read executive summary first
   - Review individual holding details
   - Understand alternatives suggested
   - Compare with previous analyses

3. **Action Items**:
   - Prioritize SELL recommendations
   - Research suggested alternatives
   - Plan trades to minimize costs
   - Monitor market conditions

---

## Next Steps

- [Developer Guide](DEVELOPER_GUIDE.md) - Architecture and development
- [API Reference](reference/API_REFERENCE.md) - Complete API documentation
- [Tutorials](tutorials/index.md) - Step-by-step learning guides
- [How-To Guides](how-to/index.md) - Specific task solutions

## Support

- **Documentation**: [https://fjacquet.github.io/finwiz](https://fjacquet.github.io/finwiz)
- **Issues**: [GitHub Issues](https://github.com/fjacquet/finwiz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fjacquet/finwiz/discussions)

---

*Last updated: 2025-01-18*
