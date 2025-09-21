# FinWiz Technical Reference

This document provides a technical reference for the FinWiz project, covering its architecture, components, and advanced features.

## Project Architecture

FinWiz is built on the [CrewAI](https://github.com/joaomdmoura/crewai) framework and follows a modular architecture designed for extensibility and maintainability.

- **Crews**: The core of the application. Each crew is a specialized team of AI agents designed to perform a specific type of financial analysis (e.g., Crypto, Stocks, ETFs).
- **Agents**: The individual AI workers within a crew. Each agent has a specific role, goal, and set of tools. Agent configurations are defined in `agents.yaml` files.
- **Tasks**: The specific assignments for agents. Tasks define the work to be done, the expected output, and which agent should perform it. Task configurations are defined in `tasks.yaml` files.
- **Tools**: The functions and APIs that agents can use to perform their tasks. This includes web search tools, data scraping tools, and financial data APIs.
- **Flow**: The `crewai.flow` orchestrates the execution of the different crews in a predefined sequence.

## Crews

FinWiz includes the following pre-configured crews:

### 1. Crypto Crew

- **Objective**: To analyze the cryptocurrency market.
- **Tasks**: Performs technical analysis, risk assessment, and develops investment strategies for specified cryptocurrencies.
- **Output**: A detailed report in HTML and PDF formats on the analyzed digital asset.

### 2. Stock Crew

- **Objective**: To research and analyze publicly traded stocks.
- **Tasks**: Conducts market analysis, screens stocks based on predefined criteria, performs technical analysis, and assesses risk.
- **Output**: A report in HTML and PDF formats on promising stock investment opportunities.

### 3. ETF Crew

- **Objective**: To analyze Exchange-Traded Funds (ETFs).
- **Tasks**: Analyzes market trends, screens for suitable ETFs, and assesses risk factors.
- **Output**: A report in HTML and PDF formats with investment strategies for ETFs.

## Customization

You can easily customize FinWiz by modifying the YAML configuration files located in each crew's directory (`src/finwiz/crews/<crew_name>/config/`).

- **To modify an agent**: Edit the `agents.yaml` file. You can change an agent's `role`, `goal`, `backstory`, or assigned `tools`.
- **To modify a task**: Edit the `tasks.yaml` file. You can change a task's `description`, `expected_output`, or the `agent` assigned to it.

## Asynchronous Task Execution

To enhance performance, FinWiz utilizes asynchronous execution for I/O-bound tasks, such as calling external APIs or scraping websites.

### How it Works

Tasks that can run concurrently without waiting for each other are marked with `async_execution=True` in their respective crew definition files (e.g., `src/finwiz/crews/stock_crew/stock_crew.py`). This allows CrewAI to run these tasks in parallel, significantly reducing the total execution time.

### Important Constraint

When using a `Process.sequential` workflow in CrewAI, there is a key limitation:

> **The final task in a sequential crew must be synchronous.**

This means the last task in the sequence cannot have `async_execution=True`. All preceding tasks can be asynchronous. FinWiz's crews are configured to adhere to this rule to ensure the workflow runs correctly. If you modify the task sequence or add new tasks, ensure the final task remains synchronous.

### Final Reporter Tooling Policy

To avoid unintended external calls or research at the reporting stage, the final reporting agent must be configured with an empty tools list. It should only consume upstream context and format the final HTML report according to `docs/output_formatting_guide.md`.

## Available Tools

The agents in FinWiz are equipped with a variety of tools to perform their research, including:

### Web & Search Tools
- `SerperDevTool`: For general web searches.
- `FirecrawlScrapeWebsiteTool`: For scraping content from websites.
- `FirecrawlSearchTool`: For searching within a website's content.
- `YoutubeVideoSearchTool`: For finding relevant videos on YouTube.

### Financial Data Tools
- `YahooFinanceNewsTool`: For fetching financial news.
- `YahooFinanceTickerInfoTool`: Basic ticker information from Yahoo Finance.
- `YahooFinanceHistoryTool`: Historical price data from Yahoo Finance.
- `YahooFinanceCompanyInfoTool`: Detailed company information.
- `YahooFinanceETFHoldingsTool`: ETF holdings information.

### Enhanced Analysis Tools
- `AlphaVantageNewsSentimentTool`: Structured news and sentiment via Alpha Vantage's NEWS_SENTIMENT endpoint with support for multiple tickers, time filtering, topic filtering, and sorting strategies.
- `TwelveDataIndicatorTool`: Technical indicators (RSI, MACD, Bollinger Bands) via Twelve Data.
- `ChartImgTool`: PNG chart images as base64 data URLs via Chart-img.
- `StandardizedSentimentAnalysisTool`: Comprehensive sentiment analysis with consistent methodology across all asset classes. Features weighted scoring, trending topics extraction, confidence intervals, article deduplication, and multi-source news aggregation.
- `CrossAssetSentimentComparatorTool`: Comparative sentiment analysis across different asset classes for relative trend identification.

### Cryptocurrency Tools
- `CoinMarketCapInfoTool`: Detailed cryptocurrency information.
- `CoinMarketCapListTool`: Top cryptocurrencies listing.
- `CoinMarketCapHistoricalTool`: Historical crypto price data.
- `CoinMarketCapNewsTool`: Cryptocurrency news from CoinMarketCap.
- `KrakenTickerInfoTool`: Real-time ticker information from Kraken.

### Validation & Analysis Tools
- `TickerExistenceValidationTool`: Validates ticker existence across multiple exchanges (Yahoo Finance, Coinbase).
- `SECFilingSearchTool`: Searches and extracts SEC filing information.
- `HtmlToPdfTool`: Converts HTML reports to PDF format.
- `AlphaVantageNewsSentimentTool`: Fetches news and sentiment data with filtering capabilities.

### Quantitative Analysis Tools
- `QuantitativeAnalysisTool`: Comprehensive quantitative analysis framework with professional-grade capabilities:
  - **Technical Analysis**: Multi-indicator analysis using TA-Lib (RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, CCI, Williams %R, Fibonacci)
  - **Backtesting**: Strategy backtesting using Backtrader with risk management and performance metrics
  - **Performance Analytics**: Risk-adjusted performance analysis with Sharpe, Sortino, Calmar ratios, VaR, CVaR
  - **Portfolio Optimization**: Modern portfolio theory with efficient frontier calculation (requires PyPortfolioOpt)
  - **Derivatives Pricing**: Options and bond pricing using Black-Scholes and QuantLib models (optional)
  - **Stock Screening**: Multi-criteria screening across major indices with composite scoring
  - Supports stocks, ETFs, and cryptocurrencies with consistent methodologies and unified schemas

### RAG & Knowledge Tools
- `SaveToRagTool`: Persists text for later retrieval via RAG.
- RAG tools for knowledge retrieval and storage.

## Environment Variables

These tools require API keys. Create a `.env` file (see `.env.example`) with the following variables:

### Required API Keys
- `OPENAI_API_KEY`: OpenAI API key for LLM access.
- `SERPER_API_KEY`: Serper API key for web search.
- `FIRECRAWL_API_KEY`: Firecrawl API key for web scraping.

### Optional API Keys (Enhanced Features)
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key for news sentiment analysis via NEWS_SENTIMENT endpoint.
- `TWELVE_DATA_API_KEY`: Twelve Data API key for technical indicators.
- `CHART_IMG_API_KEY`: Chart-img API key for chart generation.
- `CHART_IMG_BASE_URL` (optional): Override base URL for Chart-img; defaults to `https://api.chart-img.com/v1/stock`.
- `COINMARKETCAP_API_KEY`: CoinMarketCap API key for cryptocurrency data.

### Configuration Variables
- `PORTFOLIO_REVIEW_ENABLED` (default: "true"): Enable/disable portfolio review functionality.
- `PORTFOLIO_ETF_CSV` (default: "data/etf.csv"): Path to ETF portfolio CSV file.
- `PORTFOLIO_STOCK_CSV` (default: "data/stock.csv"): Path to stock portfolio CSV file.
- `VALIDATION_STRICTNESS` (default: "warn"): Schema validation mode ("off", "warn", "error"). Controls ValidationManager behavior globally.

### Caching Configuration
- `CACHE_BACKEND` (default: "hybrid"): Cache backend type ("memory", "file", "hybrid").
- `CACHE_TTL` (default: "2700"): Default cache TTL in seconds (45 minutes).
- `CACHE_MAX_MEMORY_ITEMS` (default: "1000"): Maximum items in memory cache.
- `CACHE_MAX_FILE_SIZE_MB` (default: "100"): Maximum cache file size in MB.
- `CACHE_DIRECTORY` (default: "cache"): Directory for file-based cache storage.
- `CACHE_STRATEGY` (default: "ttl"): Cache eviction strategy ("ttl", "lru", "lfu", "adaptive").
- `CACHE_AUTO_CLEANUP` (default: "true"): Enable automatic cleanup of expired entries.

Notes:
- Ensure variable names match exactly. If you previously used `CHARTIMG_API_KEY`, rename it to `CHART_IMG_API_KEY`.

## Portfolio Review System

FinWiz includes an automated portfolio analysis system that evaluates existing holdings and provides keep/sell recommendations.

### Data Sources
- **ETF Holdings**: `data/etf.csv` with columns: Name, Ticker, Currency
- **Stock Holdings**: `data/stock.csv` with columns: Name, Ticker, Currency  
- **Ticker Normalization**: Handles Yahoo Finance prefixes (e.g., "YAHOO:AAPL" → "AAPL")
- **Validation**: Uses TickerExistenceValidationTool to verify ticker existence across multiple exchanges

### Analysis Process
1. **CSV Ingestion**: Reads portfolio data from configurable CSV files with automatic ticker normalization
2. **Validation**: Checks ticker existence across multiple exchanges using TickerExistenceValidationTool
3. **Scoring**: Calculates composite scores based on validation results and asset class characteristics
4. **Risk Assessment**: Standardized 0-5 risk scoring with human-readable levels using RiskAssessmentStandardized schema
5. **Decision Logic**: Keep/sell recommendations based on configurable thresholds (KEEP_THRESHOLD)
6. **Alternative Identification**: Suggests better alternatives for underperforming holdings (future enhancement)

### Configuration
- `PORTFOLIO_REVIEW_ENABLED` (default: "true"): Enable/disable portfolio review functionality
- `PORTFOLIO_ETF_CSV` (default: "data/etf.csv"): Path to ETF portfolio CSV file
- `PORTFOLIO_STOCK_CSV` (default: "data/stock.csv"): Path to stock portfolio CSV file
- `KEEP_THRESHOLD` (default: 0.55): Minimum composite score for KEEP recommendation
- `DELTA_THRESHOLD` (default: 0.10): Score difference threshold for alternatives
- `MAX_RISK_STEP` (default: 1): Maximum risk level increase for alternatives

### Output Schema
The portfolio review generates a structured JSON output conforming to the `PortfolioReview` schema:
- **PortfolioReview**: Contains analysis timestamp, base currency, and holdings list
- **HoldingDecision**: Individual holding analysis with asset class, decision (KEEP/SELL), composite score, risk assessment, rationale bullets, and citations
- **Alternative**: Alternative investment suggestions with ticker, name, composite score, risk score, key metrics, thesis bullets, and citations (up to 3 per holding)
- **RiskAssessmentStandardized**: Standardized risk scoring (0-5 scale) with human-readable levels and risk factors

## Data Validation Infrastructure

FinWiz implements a comprehensive validation system built around centralized management and configurable strictness modes. The system provides structured error handling, schema registry management, and contract validation across all crew boundaries.

### Validation Components

#### ValidationManager
The central orchestrator for all validation operations:
- Coordinates with SchemaRegistry for dynamic schema lookup
- Supports configurable validation modes (off/warn/error) via `VALIDATION_STRICTNESS` environment variable
- Provides structured error handling with detailed context through ValidationResult objects
- Validates crew outputs, reporter inputs, and arbitrary data against registered schemas
- Integrates with ContractValidator for boundary contract compliance
- Handles Pydantic validation errors with graceful degradation based on strictness mode

#### SchemaRegistry
Centralized registry for Pydantic models:
- Single point of control for all validation schemas
- Dynamic schema lookup by name or crew type
- Automatic registration of existing FinWiz schemas on initialization
- Support for crew-specific output validation with `register_crew_schema()`
- Global singleton instance accessible via `get_registry()`
- Pre-registered schemas include ReporterInput, ValidatedTicker, RiskAssessmentStandardized, and all crew-specific models

#### ValidationResult
Structured validation outcome with:
- Boolean validation status (`is_valid`)
- Detailed error and warning collections with field paths and context
- Sanitized/cleaned data output (`sanitized_data`)
- Contextual information for debugging and remediation
- Helper methods: `add_error()`, `add_warning()`, `has_errors`, `has_warnings`
- Pydantic model with strict validation (`extra='forbid'`)

#### Validation Modes
Configurable via `VALIDATION_STRICTNESS` environment variable:
- **off**: Validation disabled, original data passed through unchanged
- **warn**: Validation errors converted to warnings, processing continues with original data (default)
- **error**: Validation errors halt processing, strict enforcement of data contracts

### Usage Examples

```python
from finwiz.validation import get_validation_manager

# Get the global validation manager
manager = get_validation_manager()

# Validate crew output
result = manager.validate_crew_output(data, "stock", "analysis")
if result.is_valid:
    processed_data = result.sanitized_data
else:
    for error in result.errors:
        print(f"Error at {error.field_path}: {error.message}")

# Validate reporter input
result = manager.validate_reporter_input(reporter_data)

# Set validation mode programmatically
manager.set_strictness_mode(ValidationMode.ERROR)
```

## Data Schemas & Validation

FinWiz uses strict Pydantic v2 models with `extra='forbid'` to prevent schema drift:

### Core Schemas
- `ReporterInput`: Aggregate input for the final reporter
- `RiskAssessmentStandardized`: Standardized 0-5 risk scoring
- `ValidatedTicker`: Ticker validation results

### Asset-Specific Schemas
- **Stock**: `TenKInsight`, `MarketSentiment`
- **ETF**: `ETFFactsheet`, `ETFTopHolding`
- **Crypto**: `CryptoThesis`
- **Portfolio**: `PortfolioReview`, `HoldingDecision`, `Alternative`

### Schema Export
Generate JSON schemas from Pydantic models:
```bash
uv run python -m finwiz.schemas.export
```

## Persistent Financial Planning

FinWiz supports loading and updating existing financial plans from previous sessions:

### Session Management
- **Automatic Loading**: Checks for existing report at `report/finwiz_family_financial_plan.html`
- **State Preservation**: Maintains previous analysis and recommendations
- **Incremental Updates**: Updates existing plans with new market data and analysis
- **Backup Creation**: Archives previous versions in `archive/` directory

### File Structure
```
report/
├── finwiz_family_financial_plan.html    # Current active plan
archive/
├── finwiz_family_financial_plan_June 13, 2025.html    # Archived versions
└── finwiz_family_financial_plan_v1.html
```

### Implementation Details
- HTML parsing extracts previous recommendations and portfolio structure
- New analysis integrates with existing plan structure
- Maintains consistency in formatting and section organization
- Preserves user customizations and manual adjustments

## Standardized Sentiment Analysis

FinWiz implements a comprehensive sentiment analysis system with consistent methodology across all asset classes.

### StandardizedSentimentAnalysisTool

The core sentiment analysis tool provides:

#### Features
- **Multi-Source News Aggregation**: Collects news from financial sources (Yahoo Finance, MarketWatch, Reuters) for stocks/ETFs and crypto-specific sources (CoinDesk, CoinTelegraph) for cryptocurrencies
- **Weighted Sentiment Scoring**: Calculates both mean and confidence-weighted sentiment scores with confidence intervals
- **Article Deduplication**: Removes duplicate articles based on headline similarity
- **Trending Topics Extraction**: Identifies trending topics with mention counts, relevance scores, and associated sentiment
- **Top Articles Selection**: Provides top 3 positive and negative articles with scores and citations
- **Consistent Methodology**: Standardized approach across stocks, ETFs, and cryptocurrencies

#### Input Parameters
```python
StandardizedSentimentInput(
    symbol: str,                    # Asset symbol (ticker, crypto symbol)
    asset_class: str,              # "stock", "etf", or "crypto"
    max_articles: int = 50,        # Maximum articles to analyze (10-100)
    days_back: int = 30,           # Days to look back for news (7-90)
    include_trending: bool = True   # Whether to extract trending topics
)
```

#### Output Structure
```python
{
    "symbol": "AAPL",
    "asset_class": "stock",
    "analysis_date": "2025-08-31T...",
    "articles_analyzed": 25,
    "mean_score": 0.234,           # Simple average sentiment
    "weighted_score": 0.287,       # Confidence-weighted sentiment
    "confidence_interval": [0.1, 0.4],  # 25th-75th percentile range
    "counts": {"pos": 12, "neu": 8, "neg": 5},
    "top_pos": [...],              # Top 3 positive articles
    "top_neg": [...],              # Top 3 negative articles
    "trending_topics": [...],      # Trending topics with sentiment
    "methodology": "Standardized cross-asset sentiment analysis..."
}
```

### CrossAssetSentimentComparatorTool

Companion tool for comparative sentiment analysis across asset classes. Provides methodology information for cross-asset sentiment comparison with relative scoring.

### Usage Guidelines

1. **Asset-Specific Sources**: The tool automatically selects appropriate news sources based on asset class
2. **Fallback Behavior**: If news collection fails, the tool provides sample articles to ensure consistent output structure
3. **Error Handling**: Graceful error handling with informative error messages and partial results when possible
4. **Performance**: Optimized for batch processing with configurable article limits and time ranges

### Testing Coverage

The standardized sentiment analysis tools include comprehensive test coverage:

- **Unit Tests**: Complete test suite in `tests/unit/tools/test_standardized_sentiment_tool.py` and `tests/test_standardized_sentiment_tool.py`
- **Input Validation**: Tests for parameter validation, range checking, and asset class validation
- **Sentiment Calculation**: Tests for positive, negative, and neutral sentiment detection with various article types
- **Article Processing**: Tests for deduplication, trending topics extraction, and top articles selection
- **Error Handling**: Tests for API failures, missing data, and graceful degradation scenarios
- **Integration Scenarios**: Tests for mixed sentiment articles, cross-asset analysis, and complete workflow validation
- **Mock Strategy**: All external API calls are mocked to ensure deterministic, fast-running tests

## Caching System

FinWiz includes an intelligent caching system to improve performance and reduce API costs.

### CacheManager

The `CacheManager` provides comprehensive caching capabilities with multiple backends and strategies:

```python
from finwiz.utils.cache_manager import get_cache_manager, CacheConfig, CacheBackend

# Get the global cache manager
cache = get_cache_manager()

# Basic usage
await cache.set("my_key", {"data": "value"}, ttl=3600)
result = await cache.get("my_key")

# Advanced configuration
config = CacheConfig(
    backend=CacheBackend.HYBRID,
    default_ttl=2700,  # 45 minutes
    max_memory_items=1000,
    strategy=CacheStrategy.LRU
)
cache = CacheManager(config)
```

### Cache Backends

- **Memory**: Fast in-memory caching with configurable size limits
- **File**: Persistent file-based caching with compression support
- **Hybrid**: Combines memory and file caching for optimal performance

### Cache Strategies

- **TTL**: Time-to-live based expiration (default)
- **LRU**: Least Recently Used eviction
- **LFU**: Least Frequently Used eviction
- **Adaptive**: Dynamic strategy based on access patterns

### Cache Decorators

```python
from finwiz.utils.cache_manager import cached, cache_key

# Cache function results
@cached(key="stock_data", ttl=1800)
async def get_stock_data(ticker):
    # Expensive API call
    return await fetch_stock_data(ticker)

# Generate cache keys
key = cache_key("stock", ticker, "daily")
```

### Performance Monitoring

```python
# Get comprehensive cache statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Memory usage: {stats['total_size_mb']:.1f} MB")
```

## Dynamic Test Data Framework

FinWiz uses Faker for generating realistic test data and pytest-mock for consistent mocking.

### Test Data Generation

```python
from tests.fixtures.api_test_mocks import APITestMocks
from faker import Faker

fake = Faker()

# Generate realistic financial data
ticker = fake.stock_ticker()
company_name = fake.company()
price = fake.stock_price()
```

### Standardized Mocking

```python
def test_stock_analysis(mocker):
    # Use standardized mock setups
    mocks = APITestMocks(mocker)
    mocks.setup_yahoo_finance_success()
    
    # Test with dynamic data
    result = analyze_stock(fake.stock_ticker())
    assert result.recommendation in ["BUY", "HOLD", "SELL"]
```

## Quantitative Analysis Framework

FinWiz includes a comprehensive quantitative analysis framework built on professional-grade financial libraries.

### Core Components

#### Backtesting Engine (`finwiz.quantitative.backtesting`)
- **Framework**: Built on Backtrader for professional strategy development
- **Strategy Base Class**: `StrategyFramework` with built-in risk management
- **Position Sizing**: Multiple methods including fixed amount, percentage of portfolio, Kelly criterion
- **Risk Management**: Stop-loss, take-profit, and maximum drawdown controls
- **Performance Metrics**: Comprehensive analysis including Sharpe ratio, maximum drawdown, win rate

```python
from finwiz.quantitative import get_backtesting_engine, SimpleMovingAverageStrategy

engine = get_backtesting_engine()
result = engine.run_strategy_backtest(
    SimpleMovingAverageStrategy,
    symbol="AAPL",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1)
)
```

#### Technical Analysis Engine (`finwiz.quantitative.technical`)
- **Library**: TA-Lib integration with 150+ technical indicators
- **Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic, ATR, ADX, CCI, Williams %R, Fibonacci
- **Signal Generation**: Automated buy/sell signals with confidence scoring
- **Confluence Detection**: Identify zones where multiple indicators align
- **Multi-Timeframe**: Support for different timeframes and data frequencies

```python
from finwiz.quantitative.technical import TechnicalAnalysisEngine

engine = TechnicalAnalysisEngine()
result = engine.analyze_symbol(data, "AAPL", "1d", indicators=[
    TechnicalIndicator.RSI,
    TechnicalIndicator.MACD,
    TechnicalIndicator.BOLLINGER_BANDS
])
```

#### Performance Analytics (`finwiz.quantitative.performance`)
- **Metrics**: Sharpe, Sortino, Calmar ratios, maximum drawdown, VaR, CVaR
- **Portfolio Optimization**: PyPortfolioOpt integration for efficient frontier
- **Benchmark Comparison**: Alpha, beta, tracking error, information ratio
- **Visualization**: Performance charts and optimization plots (requires Plotly)

```python
from finwiz.quantitative import get_performance_analyzer

analyzer = get_performance_analyzer()
report = analyzer.analyze_performance(
    returns=strategy_returns,
    benchmark_returns=benchmark_returns,
    strategy_name="My Strategy"
)
```

#### Portfolio Optimization (`finwiz.quantitative.optimization`)
- **Methods**: Mean-variance, risk parity, Black-Litterman, hierarchical risk parity
- **Objectives**: Maximum Sharpe ratio, minimum volatility, maximum return
- **Constraints**: Weight bounds, sector limits, turnover constraints
- **Efficient Frontier**: Generate and visualize efficient portfolios

```python
from finwiz.quantitative.optimization import PortfolioOptimizer

optimizer = PortfolioOptimizer()
result = optimizer.optimize_portfolio(
    inputs=portfolio_inputs,
    objective=ObjectiveFunction.MAX_SHARPE,
    method=OptimizationMethod.MEAN_VARIANCE
)
```

#### Derivatives Pricing (`finwiz.quantitative.derivatives`)
- **Library**: QuantLib integration for professional derivatives pricing
- **Options**: Black-Scholes, binomial, Monte Carlo pricing models
- **Greeks**: Delta, gamma, theta, vega, rho calculation
- **Bonds**: Yield curve analysis, duration, convexity
- **Implied Volatility**: Newton-Raphson method for volatility calculation

```python
from finwiz.quantitative.derivatives import DerivativesPricer, OptionParameters

pricer = DerivativesPricer()
result = pricer.price_option(
    OptionParameters(
        underlying_price=100.0,
        strike_price=105.0,
        time_to_expiry=0.25,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type=OptionType.CALL
    )
)
```

#### Stock Screening (`finwiz.quantitative.screening`)
- **Universes**: S&P 500, NASDAQ 100, Russell 2000, Dow 30, custom lists
- **Criteria**: Fundamental metrics (P/E, ROE, debt ratios) and technical indicators
- **Scoring**: Multi-criteria composite scoring with configurable weights
- **Filtering**: Advanced filtering with min/max values and custom logic

```python
from finwiz.quantitative.screening import StockScreener, ScreeningFilter

screener = StockScreener()
results, summary = screener.screen_stocks(
    filters=[
        ScreeningFilter(criteria=ScreeningCriteria.PE_RATIO, min_value=5, max_value=20),
        ScreeningFilter(criteria=ScreeningCriteria.ROE, min_value=0.15)
    ],
    universe=ScreeningUniverse.SP500,
    max_results=50
)
```

### Configuration

Quantitative analysis is configured through environment variables and configuration classes:

```bash
# Optional quantitative analysis dependencies
QUANTITATIVE_ENABLED=true
BACKTEST_INITIAL_CAPITAL=100000
BACKTEST_COMMISSION=0.001
RISK_FREE_RATE=0.02
```

### Dependencies

The quantitative framework requires additional dependencies:
- **Backtrader**: Strategy backtesting framework
- **TA-Lib**: Technical analysis library
- **PyPortfolioOpt**: Portfolio optimization (optional)
- **QuantLib**: Derivatives pricing (optional)
- **Plotly**: Visualization (optional)
- **SciPy**: Statistical functions

Install with:
```bash
uv pip install backtrader ta-lib
# Optional dependencies
uv pip install PyPortfolioOpt QuantLib plotly scipy
```

### Integration with Crews

The quantitative framework integrates with existing crews through the `QuantitativeAnalysisTool`:

```python
# In crew configuration
tools = [
    QuantitativeAnalysisTool(),
    # ... other tools
]
```

The tool provides comprehensive analysis results that can be incorporated into crew outputs using the quantitative schemas in `src/finwiz/schemas/quantitative.py`.

## Quantitative Analysis Framework

FinWiz includes a comprehensive quantitative analysis framework built on professional-grade financial libraries. See [Quantitative Analysis Documentation](quantitative_analysis.md) for detailed information.

### Core Components

#### Backtesting Engine (`finwiz.quantitative.backtesting`)
Professional backtesting framework using Backtrader:

```python
from finwiz.quantitative import get_backtesting_engine, SimpleMovingAverageStrategy

engine = get_backtesting_engine()
result = engine.run_strategy_backtest(
    SimpleMovingAverageStrategy,
    symbol="AAPL",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 1, 1),
    strategy_params={"short_period": 20, "long_period": 50}
)
```

#### Technical Analysis Engine (`finwiz.quantitative.technical`)
TA-Lib integration with 150+ technical indicators:

```python
from finwiz.quantitative.technical import TechnicalAnalysisEngine, TechnicalIndicator

engine = TechnicalAnalysisEngine()
result = engine.analyze_symbol(
    data=price_data,
    symbol="AAPL",
    timeframe="1d",
    indicators=[TechnicalIndicator.RSI, TechnicalIndicator.MACD, TechnicalIndicator.BOLLINGER_BANDS]
)
```

#### Performance Analytics (`finwiz.quantitative.performance`)
Risk-adjusted performance metrics and portfolio optimization:

```python
from finwiz.quantitative import get_performance_analyzer

analyzer = get_performance_analyzer()
report = analyzer.analyze_performance(
    returns=strategy_returns,
    benchmark_returns=benchmark_returns,
    strategy_name="My Strategy"
)
```

#### Portfolio Optimization (`finwiz.quantitative.optimization`)
Modern portfolio theory implementation:

```python
from finwiz.quantitative.optimization import PortfolioOptimizer, ObjectiveFunction

optimizer = PortfolioOptimizer()
result = optimizer.optimize_portfolio(
    inputs=portfolio_inputs,
    objective=ObjectiveFunction.MAX_SHARPE
)
```

#### Derivatives Pricing (`finwiz.quantitative.derivatives`)
Options and bond pricing using QuantLib (optional):

```python
from finwiz.quantitative.derivatives import DerivativesPricer, OptionParameters

pricer = DerivativesPricer()
result = pricer.price_option(option_params)
```

#### Stock Screening (`finwiz.quantitative.screening`)
Multi-criteria stock screening and ranking:

```python
from finwiz.quantitative.screening import StockScreener, ScreeningFilter

screener = StockScreener()
results, summary = screener.screen_stocks(
    filters=screening_filters,
    universe=ScreeningUniverse.SP500
)
```

### Configuration

```bash
# Quantitative Analysis Configuration (Optional)
QUANTITATIVE_ENABLED=true
BACKTEST_INITIAL_CAPITAL=100000
BACKTEST_COMMISSION=0.001
RISK_FREE_RATE=0.02
```

### Dependencies

**Required:**
- backtrader (backtesting)
- ta-lib (technical analysis)
- numpy, pandas (data processing)
- yfinance (data provider)

**Optional:**
- QuantLib (derivatives pricing)
- PyPortfolioOpt (portfolio optimization)
- plotly (visualizations)
- scipy (statistical functions)

## Testing

- Framework: `pytest`; mocking: `pytest-mock`.
- Structure: place tests under a top-level `tests/` directory using `test_*.py` files.
- Run commands:

```bash
uv run pytest
```

- Use markers to manage scope/speed (e.g., integration tests):

```bash
uv run pytest -m "not integration"
```

- Quantitative tests:

```bash
# Run quantitative unit tests
uv run pytest tests/unit/quantitative/ -v

# Run quantitative integration tests
uv run pytest tests/integration/test_quantitative_analysis_integration.py -v
```

- Guidelines:
  - Mock external APIs/tools and filesystem for determinism.
  - Use Faker for dynamic test data generation.
  - Prefer small unit tests, add integration tests for crew flows.
  - Quantitative tests include comprehensive coverage of all analysis components.
  - Ensure CI runs `uv run pytest` as default.
