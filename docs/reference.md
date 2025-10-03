# FinWiz Technical Reference

This document provides a technical reference for the FinWiz project, covering its architecture, components, and advanced features.

## Project Architecture

FinWiz is built on the [CrewAI](https://github.com/joaomdmoura/crewai) framework and follows a modular architecture designed for extensibility and maintainability. **The codebase has undergone significant modernization to improve code organization and maintainability.**

For detailed CrewAI feature usage patterns and best practices, see:
- [CrewAI Feature Usage Guide](crewai_feature_usage_guide.md) - Comprehensive guide for proper CrewAI implementation
- [CrewAI Compliance Checklist](crewai_compliance_checklist.md) - Checklist for ensuring consistent feature usage

### Core Components

- **Crews**: The core of the application. Each crew is a specialized team of AI agents designed to perform a specific type of financial analysis (e.g., Crypto, Stocks, ETFs).
- **Agents**: The individual AI workers within a crew. Each agent has a specific role, goal, and set of tools. Agent configurations are defined in `agents.yaml` files. **AI Reasoning**: Agents now support reasoning capabilities with `reasoning=True` for transparent decision-making processes.
- **Tasks**: The specific assignments for agents. Tasks define the work to be done, the expected output, and which agent should perform it. Task configurations are defined in `tasks.yaml` files.
- **Tools**: The functions and APIs that agents can use to perform their tasks. This includes web search tools, data scraping tools, and financial data APIs.
- **Flow**: The `crewai.flow` orchestrates the execution of the different crews in a predefined sequence.
- **Testing Infrastructure**: Comprehensive test suite with pytest and pytest-mock, featuring realistic test data generation, standardized mocking patterns, and robust coverage measurement.

### Modernized Architecture

The codebase has been systematically modernized with the following improvements:

#### File Decomposition
- **Large files split**: Monolithic files (1000+ lines) decomposed into focused modules under 200 lines
- **Single responsibility**: Each module has a clear, focused purpose
- **Extracted components**: Calculations, formatting, utilities, and models separated into dedicated files

#### Key Modernization Areas

**Main Application Structure:**
- `main.py` (reduced from 1291 lines) → Core application logic
- `flow_state.py` (extracted) → Flow state management
- `crew_factory.py` (extracted) → Crew initialization logic

**Quantitative Analysis Framework:**
- `quantitative/technical.py` (reduced from 1323 lines) → Core technical analysis
- `quantitative/technical/technical_indicators.py` (extracted) → TA-Lib wrappers
- `quantitative/technical/technical_models.py` (extracted) → Pydantic models and enums
- `quantitative/technical/basic_indicators.py` (extracted) → Basic indicators
- `quantitative/technical/advanced_indicators.py` (extracted) → Advanced indicators

**Tool Modernization:**
- `tools/market_screening_tool.py` (reduced from 1062 lines) → Core screening logic
- `tools/screening_criteria.py` (extracted) → Screening criteria
- `tools/screening_utils.py` (extracted) → Screening utilities
- `tools/screening_ranking.py` (extracted) → Ranking algorithms
- `tools/technical_analyzer.py` (reduced from 821 lines) → Core technical analysis
- `tools/technical_algorithms.py` (extracted) → Mathematical algorithms and calculations
- `tools/technical_patterns.py` (extracted) → Pattern recognition and confluence detection
- `tools/technical_models.py` (extracted) → Technical analysis data models

**Portfolio Rebalancing:**
- `tools/rebalancing_report_generator.py` (reduced from 1129 lines) → Core reporting
- `tools/rebalancing_formatters.py` (extracted) → HTML formatting
- `tools/rebalancing_calculations.py` (extracted) → Calculations
- `tools/rebalancing_templates.py` (extracted) → Template management

**Sentiment Analysis:**
- `tools/enhanced_sentiment_tool.py` (reduced from 822 lines) → Core sentiment analysis
- `tools/sentiment_calculations.py` (extracted) → Sentiment calculations
- `tools/sentiment_sources.py` (extracted) → Data source integrations

**Data Integration:**
- `integration/data_accessor.py` (reduced from 1026 lines) → Core data access
- `integration/data_validation.py` (extracted) → Validation logic
- `integration/data_cache.py` (extracted) → Caching logic
- `integration/data_transformation.py` (extracted) → Data transformation

#### Scientific Package Optimization
- Manual calculations replaced with pandas/numpy vectorized operations
- `pandas.Series.mean()` instead of manual `sum()/len()` calculations
- `pandas.groupby()` for aggregation operations
- `pandas.rolling()` for moving averages
- Numpy broadcasting for efficient array operations

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

### 4. Portfolio Rebalancing Crew

- **Objective**: To provide intelligent portfolio rebalancing analysis and optimization.
- **Tasks**: Analyzes current portfolio composition, generates optimal trade recommendations, performs cost analysis, and validates against risk constraints.
- **Output**: Comprehensive rebalancing report with trade recommendations, cost analysis, and scenario comparisons in HTML and PDF formats.

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
- `StandardizedSentimentAnalysisTool`: Comprehensive sentiment analysis with consistent methodology across all asset classes. Features weighted scoring, trending topics extraction, confidence intervals, article deduplication, and multi-source news aggregation. **Enhanced with optional Perplexity Sonar integration** for recent market insights.
- `CrossAssetSentimentComparatorTool`: Comparative sentiment analysis across different asset classes for relative trend identification.
- `PerplexityAnalysisIntegration`: Enhanced research capabilities using Perplexity Sonar Search with structured data parsing, circuit breaker protection, and graceful fallback mechanisms.

### Advanced Technical Analysis Framework

FinWiz includes a comprehensive technical analysis framework built with modular architecture for advanced pattern recognition and signal generation:

#### TechnicalAnalyzer
The main orchestrator that coordinates comprehensive technical analysis including:
- **Fibonacci Analysis**: Retracement and extension level calculations with trend identification
- **Support/Resistance Detection**: Dynamic level identification with strength scoring and volume confirmation
- **Multi-Indicator Confluence**: Detection of zones where multiple technical indicators align
- **Signal Generation**: Overall buy/sell/neutral signals with confidence scoring
- **Pattern Recognition**: Advanced pivot point analysis and trend pattern identification

#### Technical Analysis Modules
- **`TechnicalAlgorithms`**: Mathematical calculations for technical indicators including:
  - RSI (Relative Strength Index) with customizable periods
  - MACD (Moving Average Convergence Divergence) with signal line crossovers
  - Bollinger Bands with dynamic volatility bands
  - Fibonacci retracements and extensions with standard ratios (0.382, 0.618, etc.)
  - Moving averages and trend analysis

- **`TechnicalPatterns`**: Pattern recognition algorithms for:
  - Support and resistance level identification with touch count validation
  - Confluence zone detection with configurable tolerance levels
  - Pivot point analysis for swing highs and lows
  - Overall signal determination with weighted indicator consensus
  - Volume confirmation for level validation

- **`TechnicalModels`**: Comprehensive Pydantic data models including:
  - `PriceData`: Historical price data structure with validation
  - `FibonacciLevels`: Complete Fibonacci analysis results
  - `SupportResistance`: Support and resistance level analysis
  - `IndicatorSignal`: Individual technical indicator signals
  - `ConfluenceZone`: Multi-indicator alignment zones
  - `TechnicalAnalysisResult`: Complete analysis output with all components

#### Usage Example
```python
from finwiz.tools.technical_analyzer import TechnicalAnalyzer
from finwiz.tools.technical_models import PriceData

analyzer = TechnicalAnalyzer()
result = analyzer.analyze("AAPL", price_data)

# Access comprehensive analysis components
fibonacci_levels = result.fibonacci_levels
support_resistance = result.support_resistance
confluence_zones = result.confluence_zones
overall_signal = result.overall_signal  # "buy", "sell", or "neutral"
confidence = result.signal_confidence   # 0.0 to 1.0
```

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

### Portfolio Rebalancing Tools
- `PortfolioRebalancingTool`: Comprehensive portfolio rebalancing analysis framework with professional-grade capabilities:
  - **Trade Recommendations**: Generate optimal buy/sell recommendations to maintain target allocations
  - **Multiple Optimization Methods**: Choose from minimize trades, minimize costs, or risk-aware strategies
  - **Cost Analysis**: Calculate transaction costs including commissions, spreads, and market impact
  - **Risk Management**: Apply concentration limits, turnover monitoring, and volatility-based recommendations
  - **Scenario Analysis**: Compare different rebalancing approaches and what-if scenarios
  - **Performance Tracking**: Monitor rebalancing effectiveness with historical analysis
  - Supports fractional shares, multiple asset classes, and configurable tolerance bands
  - Integrates with existing portfolio monitoring and alerting systems

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
- `PPLX_API_KEY`: Perplexity API key for Sonar Search integration (requires `FF_PERPLEXITY_RESEARCH=true`).

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
- `ReporterInput`: Aggregate input for the final reporter with strict validation
- `RiskAssessmentStandardized`: Standardized 0-5 risk scoring with bounded validation
- `ValidatedTicker`: Ticker validation results

### Asset-Specific Schemas
- **Stock**: `TenKInsight`, `MarketSentiment`
- **ETF**: `ETFFactsheet`, `ETFTopHolding`
- **Crypto**: `CryptoThesis`
- **Portfolio**: `PortfolioReview`, `HoldingDecision`, `Alternative`

### Contract Testing
FinWiz includes comprehensive contract tests to ensure schema compliance:
- **`test_contract_reporter.py`**: Validates ReporterInput with `extra='forbid'` and minimal valid payloads
- **`test_contract_stock.py`**: Tests TenKInsight and MarketSentiment schema validation
- **`test_contract_risk.py`**: Enforces standardized 0-5 risk scale bounds and label consistency

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

## Perplexity Sonar Integration

FinWiz includes optional integration with Perplexity Sonar Search for enhanced research capabilities across sentiment, technical, and fundamental analysis.

### Overview

The Perplexity Sonar integration provides:
- **Enhanced Research Capabilities**: Access to recent market insights and analysis
- **Multi-Analysis Support**: Sentiment, technical, and fundamental analysis contexts
- **Circuit Breaker Protection**: Automatic fallback on API failures
- **Structured Data Parsing**: Converts raw responses to structured SonarArticle objects
- **Graceful Degradation**: Seamless fallback to existing data providers

### Configuration

Enable Perplexity integration through environment variables:

```bash
# Enable Perplexity research feature flag
FF_PERPLEXITY_RESEARCH=true

# Configure API key
PPLX_API_KEY=your_perplexity_api_key_here

# Optional: Configure circuit breaker settings
FF_PERPLEXITY_BREAKER_THRESHOLD=5
FF_PERPLEXITY_BREAKER_TIMEOUT=300
```

### Integration Points

The Perplexity integration enhances existing analysis tools:

#### Enhanced Sentiment Analysis
- **Tool**: `StandardizedSentimentAnalysisTool`
- **Enhancement**: Additional Sonar articles for recent market sentiment
- **Fallback**: Yahoo Finance and Alpha Vantage news sources

#### Enhanced Crypto Analysis
- **Tool**: `EnhancedCryptoAnalysisTool`
- **Enhancement**: Regulatory updates and adoption news via Sonar
- **Context**: Crypto-specific search queries for blockchain and regulatory insights

#### Enhanced ETF Analysis
- **Tool**: `EnhancedETFAnalysisTool`
- **Enhancement**: Recent ETF performance updates and holdings changes
- **Context**: ETF-specific search queries for fund performance and expense ratio changes

### PerplexityAnalysisIntegration Class

Core integration wrapper providing structured search methods:

```python
from finwiz.tools.perplexity_analysis_integration import PerplexityAnalysisIntegration

# Initialize integration
integration = PerplexityAnalysisIntegration()

# Check availability
if integration.is_available:
    # Perform financial news search
    result = await integration.search_financial_news(
        query="AAPL earnings sentiment market reaction",
        ticker="AAPL",
        asset_type="stock",
        analysis_type="sentiment",
        max_results=10
    )
```

### SonarSearchResult Schema

Structured response format for Perplexity searches:

```python
{
    "query": "AAPL earnings sentiment",
    "ticker": "AAPL",
    "asset_type": "stock",
    "analysis_type": "sentiment",
    "results": [
        {
            "title": "Apple Reports Strong Q3 Earnings",
            "url": "https://example.com/article",
            "summary": "Apple exceeded expectations...",
            "publisher": "Financial Times",
            "published_date": "2024-07-31",
            "relevance_score": 0.95,
            "content_type": "news",
            "analysis_type": "sentiment"
        }
    ],
    "total_results": 8,
    "search_time_ms": 1250,
    "success": true,
    "retry_count": 0
}
```

### Circuit Breaker Protection

The integration includes comprehensive circuit breaker protection:

#### Failure Tracking
- **Threshold**: Configurable failure count before circuit opens (default: 5)
- **Timeout**: Configurable timeout before retry attempts (default: 300 seconds)
- **Recovery**: Automatic circuit closure on successful operations

#### Fallback Strategies
- **Cached Data**: Use previously cached Sonar results when available
- **Existing Providers**: Seamless fallback to Yahoo Finance, Alpha Vantage, etc.
- **Graceful Degradation**: Continue analysis without Perplexity enhancement

### Error Handling and Logging

Comprehensive error handling with structured logging:

#### Error Classification
- **Rate Limit Errors**: Automatic retry with exponential backoff
- **API Key Errors**: Clear configuration guidance
- **Network Errors**: Retry with circuit breaker protection
- **Parsing Errors**: Graceful fallback with error logging

#### Structured Logging
- **Request Logging**: Query length and analysis type (content redacted)
- **Performance Metrics**: Latency, result count, HTTP status
- **Failure Tracking**: Error types and retry attempts
- **Feature Flag Status**: Integration enabled/disabled state

### Feature Flag Integration

The Perplexity integration is controlled by the feature flag system:

```python
from finwiz.utils.feature_flags import get_feature_flags

flags = get_feature_flags()

# Check if Perplexity research is enabled
if flags.is_enabled("perplexity_research"):
    # Integration is available
    pass

# Record success/failure for circuit breaker
flags.record_success("perplexity_research")
flags.record_failure("perplexity_research")
```

### Usage Examples

#### Sentiment Analysis Enhancement
```python
# Enhanced sentiment analysis with Perplexity integration
from finwiz.tools.enhanced_sentiment_tool import EnhancedSentimentAnalysisTool

tool = EnhancedSentimentAnalysisTool()
result = tool._run(
    ticker="AAPL",
    asset_type="stock",
    days_back=7,
    max_articles=20
)

# Result includes both traditional and Sonar articles
print(f"Yahoo articles: {len(result['yahoo_articles'])}")
print(f"Sonar articles: {len(result['sonar_articles'])}")
```

#### Crypto Analysis Enhancement
```python
# Enhanced crypto analysis with regulatory insights
from finwiz.tools.enhanced_crypto_tool import EnhancedCryptoAnalysisTool

tool = EnhancedCryptoAnalysisTool()
result = tool._run(
    symbol="BTC",
    include_perplexity=True
)

# Result includes Perplexity insights for regulatory updates
print(f"Perplexity insights: {len(result['perplexity_insights'])}")
```

### Testing and Validation

The Perplexity integration includes comprehensive testing:

#### Unit Tests
- **Feature Flag Integration**: Test enabled/disabled states
- **Circuit Breaker**: Test failure thresholds and recovery
- **Error Handling**: Test various error scenarios
- **Data Parsing**: Test response parsing and validation

#### Integration Tests
- **API Mocking**: Mock Perplexity API responses
- **Fallback Testing**: Test graceful degradation scenarios
- **Performance Testing**: Test timeout and retry behavior

### Security and Privacy

The integration follows security best practices:

#### API Key Management
- **Environment Variables**: Secure API key storage
- **Validation**: Startup validation of required keys
- **Error Redaction**: Sensitive information redacted from logs

#### Content Handling
- **Content Redaction**: Article content not logged for privacy
- **Metadata Only**: Only metadata and performance metrics logged
- **GDPR Compliance**: No personal data stored or logged

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

## Portfolio Rebalancing System

FinWiz includes a comprehensive portfolio rebalancing system designed for professional portfolio management with intelligent optimization and risk management.

### Core Architecture

The portfolio rebalancing system follows a modular architecture with clear separation of concerns:

#### PortfolioRebalancingOrchestrator
Main orchestrator class that coordinates the entire rebalancing workflow:
- Price data retrieval and validation
- Portfolio analysis and deviation calculation
- Optimization strategy execution
- Risk constraint validation
- Report generation and formatting

#### RebalancingEngine
Core optimization engine with multiple strategies:
- **MINIMIZE_TRADES**: Reduces the number of transactions (ideal for high-cost accounts)
- **MINIMIZE_COSTS**: Optimizes for lowest total transaction costs
- **RISK_AWARE**: Considers risk metrics and concentration limits

#### Portfolio Analysis Components
- **PortfolioAnalyzer**: Calculates current weightings, deviations, and portfolio metrics
- **CostAnalyzer**: Models transaction costs including commissions, spreads, and market impact
- **RiskManager**: Validates against concentration limits and risk constraints
- **ScenarioAnalyzer**: Provides what-if analysis and scenario comparisons

#### Data Management
- **PortfolioPriceService**: Real-time price data retrieval with caching and fallback mechanisms
- **RebalancingHistoryTracker**: Historical tracking and performance attribution analysis
- **PortfolioConfigurationManager**: Configuration management with versioning support

### Configuration Options

#### Portfolio Configuration
```python
PortfolioConfiguration(
    holdings=[Holding(symbol="AAPL", shares=100.0)],
    target_weights={"AAPL": 0.4, "GOOGL": 0.35, "MSFT": 0.25},
    tolerance_bands={"AAPL": 0.03, "GOOGL": 0.05},  # Position-specific tolerances
    global_tolerance=0.05,                           # Default tolerance
    available_capital=5000.0,                        # Additional capital
    transaction_cost_rate=0.001,                     # Transaction cost rate
    min_trade_size=100.0,                           # Minimum trade size
    rebalancing_method=RebalancingMethod.MINIMIZE_TRADES
)
```

#### Environment Variables
- `PORTFOLIO_REBALANCING_ENABLED` (default: "true"): Enable/disable rebalancing functionality
- `REBALANCING_DEFAULT_TOLERANCE` (default: "0.05"): Default tolerance band
- `REBALANCING_MIN_TRADE_SIZE` (default: "100.0"): Minimum trade size
- `REBALANCING_TRANSACTION_COST_RATE` (default: "0.001"): Default transaction cost rate

### Output Schemas

#### RebalancingResult
Complete rebalancing analysis result:
- Current portfolio analysis with weightings and deviations
- Trade recommendations with quantities and cost estimates
- Cost analysis with total transaction costs and impact
- Risk analysis and constraint validation results
- Overall recommendation and urgency assessment

#### TradeRecommendation
Individual trade recommendation:
- Symbol, action (BUY/SELL), and quantity
- Current and target weights
- Trade value and estimated costs
- Rationale and priority scoring
- Risk impact assessment

### Integration Examples

#### Basic Rebalancing
```python
from finwiz.orchestrators.portfolio_rebalancing import PortfolioRebalancingOrchestrator

orchestrator = PortfolioRebalancingOrchestrator()
result = await orchestrator.rebalance_portfolio(config)

# Access trade recommendations
for trade in result.trade_recommendations:
    print(f"{trade.action} {trade.quantity} shares of {trade.symbol}")
    print(f"Estimated cost: ${trade.total_estimated_cost:.2f}")
```

#### Scenario Analysis
```python
# Compare different methods
methods = [RebalancingMethod.MINIMIZE_TRADES, RebalancingMethod.MINIMIZE_COSTS]
results = {}

for method in methods:
    config.rebalancing_method = method
    results[method] = await orchestrator.rebalance_portfolio(config)

# Compare total costs
for method, result in results.items():
    print(f"{method}: ${result.cost_analysis.total_transaction_costs:.2f}")
```

#### Historical Tracking
```python
from finwiz.quantitative.rebalancing_history_tracker import RebalancingHistoryTracker

tracker = RebalancingHistoryTracker()
await tracker.record_rebalancing_action(result, portfolio_id="my-portfolio")

# Analyze historical performance
analytics = await tracker.generate_rebalancing_analytics("my-portfolio")
print(f"Average rebalancing frequency: {analytics.average_frequency_days} days")
```

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

## Testing Infrastructure

### Framework and Standards
- **Framework**: `pytest` exclusively with `pytest-mock` for all mocking (never `unittest.mock`)
- **Structure**: Tests organized under `tests/` directory with clear categorization:
  - `tests/unit/` - Fast, isolated unit tests (< 5 seconds execution)
  - `tests/integration/` - Integration tests with external services
  - `tests/fixtures/` - Reusable test data and mock responses
- **Naming Convention**: `test_should_{behavior}_when_{condition}` for descriptive test names

### Test Execution Commands

```bash
# Unit tests only (default, fast execution)
uv run pytest -m "not integration"

# All tests including integration
uv run pytest

# Coverage measurement
uv run pytest --cov=src/finwiz

# Specific test categories
uv run pytest tests/unit/crews/
uv run pytest tests/integration/ -m integration
uv run pytest tests/unit/quantitative/ -v
uv run pytest tests/integration/test_quantitative_analysis_integration.py -v
```

### Specialized Test Categories

**Portfolio Rebalancing Tests**:
```bash
# Portfolio rebalancing unit tests
uv run pytest tests/unit/quantitative/test_portfolio_*rebalancing* -v

# Portfolio rebalancing integration tests
uv run pytest tests/integration/test_portfolio_rebalancing* -v

# Portfolio rebalancing performance tests
uv run pytest tests/performance/test_portfolio_rebalancing_performance.py -v
```

**AI Reasoning Tests**:
```bash
# AI reasoning integration tests
uv run pytest tests/integration/test_ai_reasoning_integration.py -v

# AI reasoning configuration tests
uv run pytest tests/unit/test_ai_reasoning_configuration.py -v
```

**Contract Validation Tests**:
```bash
# Schema contract validation
uv run pytest tests/test_contract_*.py -v
```

### Test Infrastructure Features

#### Comprehensive Fixtures System
- **Faker Integration**: Realistic test data generation with fixed seeds for reproducibility
- **Financial Data Factory**: Specialized factories for stock, ETF, and crypto test data
- **Mock Patterns**: Standardized mocking patterns for CrewAI, APIs, and file operations
- **Serialization Helpers**: Custom JSON encoders for CrewAI objects and datetime handling

#### Coverage Stabilization
- **Import Error Resolution**: All test files import successfully without module errors
- **Mocking Standardization**: Converted from `unittest.mock` to `pytest-mock` exclusively
- **JSON Serialization**: Custom serializers for UsageMetrics, datetime, and Pydantic objects
- **Test Isolation**: Independent test execution without shared state dependencies
- **Performance**: All unit tests execute in under 5 seconds per suite

#### Quality Standards
- **Mock Strategy**: All external dependencies mocked (APIs, file system, LLM calls)
- **Test Structure**: Arrange-Act-Assert pattern with clear assertions
- **Error Handling**: Robust error handling with clear failure messages
- **Coverage Requirements**: Minimum 80% code coverage with focus on critical paths

### Testing Guidelines

#### Mock Strategy by Component
```python
# CrewAI Components
mocker.patch('finwiz.crews.stock_crew.StockCrew.crew')
mocker.patch('crewai.Crew.kickoff', return_value=mock_result)

# External APIs
mocker.patch('finwiz.tools.yahoo_finance_tool.get_stock_data')
mocker.patch('finwiz.tools.alpha_vantage_tool.get_company_overview')

# File Operations
mocker.patch('builtins.open', mocker.mock_open(read_data=mock_data))
mocker.patch('json.dump')
```

#### Test Data Generation
```python
# Use Faker fixtures for realistic data
def test_stock_analysis(fake_stock_data):
    result = analyze_stock(fake_stock_data["ticker"])
    assert result.price == fake_stock_data["price"]

# Use factory methods for customized data
def test_high_pe_stock():
    stock_data = FinancialDataFactory.create_stock_data(pe_ratio=50.0)
    result = analyze_stock(stock_data["ticker"])
    assert result.recommendation == "SELL"
```

#### AI Reasoning Test Patterns
```python
def test_should_show_ai_reasoning_in_output(mocker):
    # Arrange
    mock_crew = mocker.patch('finwiz.crews.stock_crew.StockCrew')
    mock_result = mocker.Mock()
    mock_result.raw = "AI reasoning: Based on analysis..."
    
    # Act
    result = mock_crew.crew().kickoff(inputs={"test": "data"})
    
    # Assert
    assert "ai reasoning" in str(result.raw).lower()
    assert "analysis" in str(result.raw).lower()
```

### Coverage and Quality Monitoring
- **Coverage Targets**: Minimum 80% overall, 90% for critical modules
- **Coverage Reporting**: HTML and terminal formats with line-by-line analysis
- **Performance Monitoring**: Test execution time tracking and optimization
- **Quality Gates**: Automated quality checks in CI/CD pipeline

For detailed testing documentation, see:
- [Test Coverage Stabilization Guide](test_coverage_stabilization.md)
- [Test Fixtures Documentation](../tests/fixtures/README.md)
- [Test Organization Guide](../tests/README.md)
