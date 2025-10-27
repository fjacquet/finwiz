---
title: "Api Reference"
description: "Complete reference documentation for Api Reference"
category: "reference"
tags:
  - "api"
  - "reference"
date: "2025-10-26"
source: "reference/API_REFERENCE.md"
---

# FinWiz API Reference

Complete API reference for FinWiz tools, schemas, and utilities.

## Table of Contents

1. [Crews](#crews)
2. [Tools](#tools)
3. [Schemas](#schemas)
4. [Utilities](#utilities)
5. [Configuration](#configuration)

## Crews

### Stock Crew

Analyzes publicly traded stocks with fundamental and technical analysis.

**Location**: `src/finwiz/crews/stock_crew/`

**Agents**:

- `stock_analyst`: Performs fundamental analysis
- `technical_analyst`: Performs technical analysis
- `risk_assessor`: Evaluates risk factors

**Output Schema**: `TenKInsight`, `MarketSentiment`, `RiskAssessmentStandardized`

### ETF Crew

Analyzes Exchange-Traded Funds with expense ratio and holdings analysis.

**Location**: `src/finwiz/crews/etf_crew/`

**Agents**:

- `etf_analyst`: Analyzes ETF structure and holdings
- `cost_analyst`: Evaluates expense ratios and tracking error
- `risk_assessor`: Evaluates risk factors

**Output Schema**: `ETFFactsheet`, `ETFTopHolding`, `RiskAssessmentStandardized`

### Crypto Crew

Analyzes cryptocurrencies with technical and market structure analysis.

**Location**: `src/finwiz/crews/crypto_crew/`

**Agents**:

- `crypto_analyst`: Analyzes crypto fundamentals
- `technical_analyst`: Performs technical analysis
- `risk_assessor`: Evaluates risk factors

**Output Schema**: `CryptoThesis`, `RiskAssessmentStandardized`

### Portfolio Rebalancing Crew

Provides intelligent portfolio rebalancing analysis and optimization.

**Location**: `src/finwiz/crews/portfolio_rebalancing_crew/`

**Agents**:

- `portfolio_analyst`: Analyzes current portfolio composition
- `rebalancing_strategist`: Generates trade recommendations
- `risk_manager`: Validates against risk constraints
- `cost_analyzer`: Calculates transaction costs

**Output Schema**: `PortfolioRebalancingResult`

**See**: [Portfolio Rebalancing Documentation](portfolio_rebalancing/)

### Investment Discovery Crew

Proactively discovers A+ investment opportunities.

**Location**: `src/finwiz/crews/investment_discovery_crew/`

**Agents**:

- `etf_discovery_agent`: Discovers A+ ETFs
- `stock_discovery_agent`: Discovers A+ stocks
- `crypto_discovery_agent`: Discovers A+ crypto
- `validation_agent`: Validates discoveries
- `portfolio_optimizer_agent`: Optimizes portfolio integration

**Output Schema**: `APlusDiscoveryResult`

**See**: [Investment Discovery Documentation](investment_discovery/)

## Tools

### Portfolio Holdings Analysis Tools

#### AlternativeFinder

Find better alternatives for underperforming holdings.

**Location**: `src/finwiz/tools/alternative_finder_tool.py`

**Usage**:

```pythonthon
from finwiz.tools.alternative_finder_tool import AlternativeFinder, HoldingProfile

finder = AlternativeFinder()

holding = HoldingProfile(
    ticker="IBM",
    name="IBM Corporation",
    asset_class="stock",
    grade="D",
    composite_score=0.55
)

alternatives = finder.find_alternatives(holding, max_alternatives=3)
```text
**Features**:

- A+ candidate prioritization from discovery crew
- Transition strategies (immediate/gradual/tax-optimized)
- Asset-specific comparison metrics
- French language output

#### PriceTargetCalculator

Calculate actionable buy/sell price targets.

**Location**: `src/finwiz/tools/price_target_calculator.py`

**Usage**:

```pythonthon
from finwiz.tools.price_target_calculator import PriceTargetCalculator

calculator = PriceTargetCalculator()

targets = calculator.calculate_targets(
    ticker="AAPL",
    asset_class="stock",
    current_price=150.0,
    currency="USD",
    decision="KEEP"
)
```text
**Features**:

- Fair value calculations (DCF, P/E, NAV)
- Technical support/resistance levels
- Multi-currency support
- Asset-specific stop-loss levels

#### HoldingAnalyzerOrchestrator

Coordinate deep analysis across stock/ETF/crypto crews.

**Location**: `src/finwiz/tools/holding_analyzer_orchestrator.py`

**Usage**:

```pythonthon
from finwiz.tools.holding_analyzer_orchestrator import HoldingAnalyzerOrchestrator

orchestrator = HoldingAnalyzerOrchestrator()

analysis = orchestrator.analyze_holding(
    ticker="AAPL",
    asset_class="stock",
    currency="USD"
)
```text
**Features**:

- Crew integration with 7-day caching
- Schema mapping to portfolio review
- Graceful fallback on crew failure

### Quantitative Analysis Tools

#### QuantitativeAnalysisTool

Comprehensive quantitative analysis framework.

**Location**: `src/finwiz/tools/quantitative_analysis_tool.py`

**Usage**:

```pythonthon
from finwiz.tools.quantitative_analysis_tool import QuantitativeAnalysisTool

tool = QuantitativeAnalysisTool(asset_class="stock")

result = tool._run(
    ticker="AAPL",
    analysis_type="technical",
    timeframe="1y"
)
```text
**Analysis Types**:

- `technical`: Multi-indicator technical analysis
- `backtesting`: Strategy backtesting
- `performance`: Risk-adjusted performance metrics
- `comprehensive`: Combined analysis

**See**: [Quantitative Analysis Documentation](quantitative_analysis.md)

### Portfolio Rebalancing Tools

#### PortfolioRebalancingTool

Comprehensive portfolio rebalancing analysis.

**Location**: `src/finwiz/tools/portfolio_rebalancing_tool.py`

**Usage**:

```pythonthon
from finwiz.tools.portfolio_rebalancing_tool import PortfolioRebalancingTool

tool = PortfolioRebalancingTool()

result = tool._run(
    portfolio_config=config,
    method="MINIMIZE_COSTS"
)
```text
**Methods**:

- `MINIMIZE_TRADES`: Reduce transaction count
- `MINIMIZE_COSTS`: Optimize for lowest costs
- `RISK_AWARE`: Consider risk metrics

**See**: [Portfolio Rebalancing Documentation](portfolio_rebalancing/)

### Validation Tools

#### TickerValidationTool

Validate ticker existence across multiple exchanges.

**Location**: `src/finwiz/tools/ticker_validation_tool.py`

**Usage**:

```pythonthon
from finwiz.tools.ticker_validation_tool import TickerValidationTool

tool = TickerValidationTool()

result = tool._run(ticker="AAPL", asset_class="stock")
```text
### Sentiment Analysis Tools

#### StandardizedSentimentTool

Comprehensive sentiment analysis with multi-source aggregation.

**Location**: `src/finwiz/tools/standardized_sentiment_tool.py`

**Usage**:

```pythonthon
from finwiz.tools.enhanced_sentiment_tool import StandardizedSentimentTool

tool = StandardizedSentimentTool()

result = tool._run(
    ticker="AAPL",
    asset_class="stock",
    days_back=7
)
```text
**Features**:

- Multi-source news aggregation
- Weighted sentiment scoring
- Trending topics extraction
- Article deduplication
- Optional Perplexity Sonar integration

## Schemas

### Portfolio Review Schemas

#### HoldingDecision

Individual holding analysis with recommendations.

**Location**: `src/finwiz/schemas/portfolio_review.py`

```pythonthon
class HoldingDecision(BaseModel):
    ticker: str
    name: str
    asset_class: AssetClass
    decision: Decision  # KEEP, SELL, BUY
    composite_score: float
    grade: Grade  # A+, A, B+, B, C+, C, D, F
    price_targets: Optional[PriceTargets]
    alternatives: list[Alternative]
    position_sizing: Optional[PositionSizeRecommendation]
```text
#### PriceTargets

Buy/sell price targets with rationale.

```pythonthon
class PriceTargets(BaseModel):
    current_price: float
    currency: str
    fair_value_estimate: Optional[float]
    buy_target_primary: Optional[float]
    buy_target_secondary: Optional[float]
    sell_target_primary: Optional[float]
    stop_loss_level: Optional[float]
    buy_rationale: str
    sell_rationale: str
```text
#### Alternative

Alternative investment suggestion.

```pythonthon
class Alternative(BaseModel):
    ticker: str
    name: str
    asset_class: AssetClass
    composite_score: float
    grade: Grade
    is_a_plus_candidate: bool
    transition_strategy: str
    swap_timing: Literal["immediate", "gradual", "tax_optimized"]
    tax_implications: str
```text
### Risk Assessment Schema

#### RiskAssessmentStandardized

Standardized 0-5 risk scoring.

**Location**: `src/finwiz/schemas/common.py`

```pythonthon
class RiskAssessmentStandardized(BaseModel):
    risk_score: float = Field(ge=0.0, le=5.0)
    risk_level: RiskLevel  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH
    systematic_risk: float
    idiosyncratic_risk: float
    risk_factors: list[str]
```text
## Utilities

### Enhanced Data Extraction

#### CrewDataAccessor

Unified interface for accessing crew data with enhanced extraction capabilities.

**Location**: `src/finwiz/integration/data_accessor.py`

**Usage**:

```pythonthon
from finwiz.integration.data_accessor import CrewDataAccessor

accessor = CrewDataAccessor(integration_manager)

# Get enhanced data
backtesting = accessor.get_backtesting_metrics()
market_context = accessor.get_market_context()
methodology = accessor.get_discovery_methodology()
performance = accessor.get_performance_report()

# Get consolidated reporter input with all enhanced data
consolidated = accessor.get_consolidated_reporter_input(
    max_age_hours=24,
    current_portfolio_grade=0.70
)
```text
**Features**:

- Backtesting metrics extraction from validation results
- Market context indicators (VIX, inflation, rates, regime)
- Discovery methodology details (criteria, statistics, scores)
- Performance aggregation by asset type and regime
- Graceful degradation when data unavailable

#### BacktestingDataExtractor

Extracts backtesting performance metrics from validation results.

**Location**: `src/finwiz/integration/backtesting_extractor.py`

**Usage**:

```pythonthon
from finwiz.integration.backtesting_extractor import BacktestingDataExtractor

extractor = BacktestingDataExtractor(logger=logger)

# Extract metrics for specific symbol
metrics = extractor.extract_backtesting_metrics(validation_result, "AAPL")

# Extract regime performance
regime_perf = extractor.extract_regime_performance(validation_result)

# Get performance summary
summary = extractor.get_performance_summary(validation_results)
```text
**Extracted Metrics**:

- Annualized return, Sharpe ratio, max drawdown, win rate
- Regime-specific performance (bull/bear/sideways)
- Risk-adjusted metrics (Sortino, Calmar ratios)
- Consistency scores across regimes

#### MarketContextExtractor

Extracts market context indicators from discovery results.

**Location**: `src/finwiz/integration/market_context_extractor.py`

**Usage**:

```pythonthon
from finwiz.integration.market_context_extractor import MarketContextExtractor

extractor = MarketContextExtractor(logger=logger)

# Extract market regime
regime = extractor.extract_market_regime(discovery_result)

# Extract VIX indicators
vix = extractor.extract_vix_indicators(discovery_result)

# Get complete context summary
summary = extractor.get_market_context_summary(discovery_result)
```text
**Extracted Indicators**:

- Market regime type (bull/bear/sideways/volatile)
- VIX levels and percentiles
- Inflation rate and interest rate trends
- Market stress level assessment
- Allocation implications

#### DiscoveryMethodologyExtractor

Extracts discovery methodology details from discovery results.

**Location**: `src/finwiz/integration/discovery_methodology_extractor.py`

**Usage**:

```pythonthon
from finwiz.integration.discovery_methodology_extractor import DiscoveryMethodologyExtractor

extractor = DiscoveryMethodologyExtractor(logger=logger)

# Extract screening criteria
criteria = extractor.extract_screening_criteria(discovery_result)

# Extract validation statistics
stats = extractor.extract_validation_statistics(discovery_result)

# Get methodology summary
summary = extractor.get_methodology_summary(discovery_result)
```text
**Extracted Details**:

- Screening criteria and thresholds
- Validation statistics (screened, found, passed)
- Fundamental and technical score breakdowns
- Data sources used

#### PerformanceMetricsAggregator

Aggregates performance metrics across asset types and regimes.

**Location**: `src/finwiz/integration/performance_metrics_aggregator.py`

**Usage**:

```pythonthon
from finwiz.integration.performance_metrics_aggregator import PerformanceMetricsAggregator

aggregator = PerformanceMetricsAggregator(backtesting_extractor, logger=logger)

# Aggregate by asset type
by_asset = aggregator.aggregate_by_asset_type(validation_results, asset_type_map)

# Aggregate by regime
by_regime = aggregator.aggregate_by_regime(validation_results)

# Calculate portfolio impact
impact = aggregator.calculate_portfolio_impact(validation_results, current_grade=0.70)

# Generate comprehensive report
report = aggregator.generate_performance_report(
    validation_results,
    asset_type_map,
    current_portfolio_grade=0.70
)
```text
**Aggregation Features**:

- Metrics by asset type (ETF/stock/crypto)
- Metrics by market regime
- Portfolio impact calculations
- Top opportunities identification

### Data Quality Components

#### SECFilingURLGenerator

Generate valid, working SEC filing URLs.

**Location**: `src/finwiz/tools/sec_filing_url_generator.py`

**Usage**:

```pythonthon
from finwiz.tools.sec_filing_url_generator import SECFilingURLGenerator

generator = SECFilingURLGenerator()

# Get filing URL
url = generator.get_filing_url(ticker="AAPL", filing_type="10-K")

# Get company browse URL
browse_url = generator.get_company_browse_url(cik="0000320193")

# Verify URL accessibility
is_valid = generator.verify_url(url)
```text
**Features**:

- SEC EDGAR API integration
- CIK lookup functionality
- URL verification
- Fallback to company browse page
- Returns None when no filings available

#### PortfolioHoldingsProcessor

Process all portfolio holdings from CSV files.

**Location**: `src/finwiz/orchestrators/portfolio_holdings_processor.py`

**Usage**:

```pythonthon
from finwiz.orchestrators.portfolio_holdings_processor import PortfolioHoldingsProcessor

processor = PortfolioHoldingsProcessor()

# Load all holdings
holdings = processor.load_all_holdings()

# Process all holdings (including failed validations)
processed = processor.process_holdings(holdings)

# Get processing summary
summary = processor.get_processing_summary()
```text
**Features**:

- Reads from stock.csv, etf.csv, crypto.csv
- Processes ALL holdings regardless of validation status
- Tracks excluded holdings with reasons
- Provides processing summary
- Comprehensive logging

#### APlusDiscoveryAccessor

Access A+ discovery results reliably.

**Location**: `src/finwiz/integration/aplus_discovery_accessor.py`

**Usage**:

```pythonthon
from finwiz.integration.aplus_discovery_accessor import APlusDiscoveryAccessor

accessor = APlusDiscoveryAccessor()

# Check if discovery results exist
has_results = accessor.has_discovery_results()

# Load discovery results
results = accessor.load_discovery_results()

# Get human-readable summary
summary = accessor.get_opportunities_summary()
```text
**Features**:

- Checks for output/discovery/ files
- Parses discovery JSON
- Returns None with clear message when unavailable
- Provides human-readable summaries
- Comprehensive logging

#### DataAvailabilityTracker

Track and report data availability and freshness.

**Location**: `src/finwiz/integration/data_availability_tracker.py`

**Usage**:

```pythonthon
from finwiz.integration.data_availability_tracker import DataAvailabilityTracker

tracker = DataAvailabilityTracker()

# Track data source
tracker.track_data_source(
    source="sentiment",
    status="available",
    age_hours=2
)

# Get availability summary
summary = tracker.get_availability_summary()

# Get freshness warnings
warnings = tracker.get_freshness_warnings()
```text
**Features**:

- Tracks all data sources (sentiment, SEC, portfolio, discovery, backtesting)
- Records status and timestamp
- Calculates data age
- Generates warnings for stale data (>7 days)
- Provides comprehensive availability summary

## Flows

### Flow Orchestrator

Orchestrates the execution of the main financial analysis flow.

**Location**: `src/finwiz/flows/flow_orchestrator.py`

**Usage**:

```pythonthon
from finwiz.flows.flow_orchestrator import FlowOrchestrator

orchestrator = FlowOrchestrator()

result = orchestrator.run_flow()
```text
## Monitoring

### Investment Discovery Monitor

Monitors the investment discovery process and sends alerts on A+ opportunities.

**Location**: `src/finwiz/monitoring/investment_discovery_monitor.py`

### Alerting

Provides alerting functionality for key events.

**Location**: `src/finwiz/monitoring/alerting.py`

### Validation Manager

Centralized validation system.

**Location**: `src/finwiz/validation/manager.py`

**Usage**:

```pythonthon
from finwiz.validation import get_validation_manager

manager = get_validation_manager()

result = manager.validate_crew_output(data, "stock", "analysis")

if result.is_valid:
    processed_data = result.sanitized_data
```text
### Cache Manager

Intelligent caching system.

**Location**: `src/finwiz/cache/manager.py`

**Usage**:

```pythonthon
from finwiz.cache import get_cache_manager

cache = get_cache_manager()

cache.set("key", value, ttl=3600)
value = cache.get("key")
```text
### Feature Flags

Feature flag and circuit breaker system.

**Location**: `src/finwiz/utils/feature_flags.py`

**Usage**:

```pythonthon
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()

if flags.is_enabled("perplexity_research"):
    # Use feature
    pass
```text
## Configuration

### Environment Variables

#### Required

- `OPENAI_API_KEY`: OpenAI API key
- `SERPER_API_KEY`: Serper API key
- `FIRECRAWL_API_KEY`: Firecrawl API key

#### Optional

- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `TWELVE_DATA_API_KEY`: Twelve Data API key
- `CHART_IMG_API_KEY`: Chart-img API key
- `COINMARKETCAP_API_KEY`: CoinMarketCap API key
- `PPLX_API_KEY`: Perplexity API key

#### Configuration

- `VALIDATION_STRICTNESS`: off/warn/error (default: warn)
- `CACHE_BACKEND`: memory/file/hybrid (default: hybrid)
- `CACHE_TTL`: Cache TTL in seconds (default: 2700)
- `FF_PERPLEXITY_RESEARCH`: Enable Perplexity integration (default: false)

### Configuration Files

#### Crew Configuration

**agents.yaml**:

```yaml
stock_analyst:
  role: "Stock Analyst"
  goal: "Analyze stock fundamentals and provide investment recommendations"
  backstory: "Expert financial analyst with deep knowledge of equity markets"
```text
**tasks.yaml**:

```yaml
stock_analysis_task:
  description: "Analyze stock with quantitative metrics"
  expected_output: "Structured analysis with risk assessment"
  output_pydantic: "TenKInsight"
  agent: stock_analyst
  async_execution: true
```text
## See Also

- [Developer Guide](DEVELOPER_GUIDE.md) - Development standards
- [Architecture Guide](ARCHITECTURE.md) - System architecture
- [Agent Handbook](agent_handbook.md) - Agent guidelines
- [Portfolio Holdings Analysis](portfolio_holdings_analysis_user_guide.md) - User guide
- [Enhanced Data Extraction](ENHANCED_DATA_EXTRACTION.md) - Backtesting, market context, and methodology extraction
- [Report Crew Examples](REPORT_CREW_ENHANCED_EXAMPLES.md) - Practical examples for enhanced data usage
- [Crew Data Integration Index](CREW_DATA_INTEGRATION_INDEX.md) - Complete data integration guide

---

**Version**: 2.1
**Last Updated**: 2025-10-25
