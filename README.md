# FinWiz: AI-Powered Financial Research Crews

**FinWiz** is a sophisticated financial analysis platform powered by autonomous AI agents built with the [CrewAI](https://github.com/joaomdmoura/crewai) framework. It leverages specialized crews of AI agents to perform in-depth research and generate comprehensive reports on various financial instruments, including cryptocurrencies, stocks, and ETFs.

## ✨ Features

- **Specialized Research Crews**: Dedicated crews for Crypto, Stocks, and ETFs, each with tailored agents and tasks.
- **Portfolio Review & Analysis**: Comprehensive automated portfolio analysis with keep/sell recommendations, risk assessment, and alternative investment suggestions for existing holdings.
- **Dynamic Configuration**: Agents and tasks are configured via YAML files, allowing for easy customization and extension.
- **Asynchronous Task Execution**: Leverages async operations to significantly speed up I/O-bound tasks like web scraping and API calls, improving overall performance.
- **Real-Time Data Retrieval**: Employs a suite of tools to fetch live data from the web, ensuring analyses are based on the most current information.
- **Structured Output**: Generates detailed reports in HTML and PDF formats with strict schema validation.
- **Enhanced Financial Analysis**: Standardized multi-source sentiment analysis, technical indicators, and chart generation capabilities with comprehensive testing coverage.
- **Quantitative Analysis Framework**: Professional-grade backtesting engine with Backtrader, technical analysis with TA-Lib, portfolio optimization, derivatives pricing, and performance analytics.
- **Persistent Financial Planning**: Loads and updates existing financial plans from previous sessions.
- **Advanced Data Validation**: Centralized validation system with ValidationManager, SchemaRegistry, configurable strictness modes (off/warn/error), and structured error handling with detailed context.
- **Intelligent Caching System**: Advanced caching layer with TTL support, multiple backends (memory/file/hybrid), and performance monitoring.
- **Dynamic Test Data Framework**: Faker-based test data generation with pytest-mock integration for reliable, deterministic testing.
- **Comprehensive Testing**: Extensive test coverage with unit tests, integration tests, and mocked external dependencies for reliable CI/CD.
- **Modular and Extendable**: The project is structured to be easily extendable with new crews, agents, or tools.

## 📂 Project Structure

The project follows a modular structure to keep the codebase organized and maintainable:

```text
finwiz/
├── src/finwiz/
│   ├── crews/                # Contains the definitions for each financial crew
│   │   ├── crypto_crew/
│   │   ├── etf_crew/
│   │   ├── stock_crew/
│   │   └── report_crew/      # Final report generation crew
│   ├── orchestrators/        # Flow coordination and portfolio analysis
│   ├── quantitative/         # Quantitative analysis framework
│   │   ├── backtesting.py    # Backtrader-based backtesting engine
│   │   ├── technical.py      # TA-Lib technical analysis engine
│   │   ├── performance.py    # Performance analytics and optimization
│   │   ├── derivatives.py    # QuantLib derivatives pricing
│   │   ├── optimization.py   # Portfolio optimization (PyPortfolioOpt)
│   │   ├── screening.py      # Stock screening and filtering
│   │   ├── data.py          # Historical data management
│   │   └── config.py        # Quantitative analysis configuration
│   ├── schemas/              # Pydantic data models with strict validation
│   ├── tools/                # Custom tools for financial analysis and data handling
│   ├── templates/            # Report templates
│   ├── validation/           # Core validation infrastructure and schema registry
│   └── utils/                # Utility functions (e.g., config loaders)
├── docs/                     # Project documentation
│   └── schemas/              # JSON schemas and examples
├── data/                     # Input data files (CSV portfolios)
├── output/                   # Generated reports from the crews
├── input/                    # Processing inputs
├── logs/                     # Application logs
├── archive/                  # Processed file archive
├── .env                      # Environment variables (API keys, etc.)
├── pyproject.toml            # Project dependencies and metadata
└── README.md                 # This file
```

## 🚀 Getting Started

Follow these instructions to set up and run FinWiz on your local machine.

### Prerequisites

- Python 3.10+
- A Python package manager like `pip` with `uv`.
- API keys for any services you wish to use (e.g., Serper, Firecrawl).

### Installation

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd finwiz
   ```

2. **Set up environment variables:**

   - If an `.env.example` file exists, copy it to `.env`:

     ```bash
     cp .env.example .env
     ```

   - Open the `.env` file and add your API keys:

     ```bash
     # Required API Keys
     OPENAI_API_KEY=your_openai_key_here
     SERPER_API_KEY=your_serper_key_here
     FIRECRAWL_API_KEY=your_firecrawl_key_here
     
     # Optional Enhanced Features
     ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
     TWELVE_DATA_API_KEY=your_twelve_data_key_here
     CHART_IMG_API_KEY=your_chart_img_key_here
     COINMARKETCAP_API_KEY=your_coinmarketcap_key_here
     
     # Configuration
     PORTFOLIO_REVIEW_ENABLED=true
     VALIDATION_STRICTNESS=warn  # Options: off, warn, error
     CACHE_BACKEND=hybrid        # Options: memory, file, hybrid
     CACHE_TTL=2700             # Cache TTL in seconds (45 minutes default)
     ```

3. **Install dependencies:**

   The project uses `uv` for dependency management, and dependencies are defined in `pyproject.toml`.

   ```bash
   uv pip install . # Install the project and its dependencies
   ```

4. **Install WeasyPrint System Dependencies:**

   FinWiz uses WeasyPrint to generate PDF reports from HTML. WeasyPrint requires certain system-level libraries to be installed.

   - **macOS (using Homebrew):**

     ```bash
     brew install pango cairo libffi gdk-pixbuf
     ```

   - **Debian/Ubuntu Linux:**

     ```bash
     sudo apt-get update
     sudo apt-get install python3-dev python3-pip python3-setuptools python3-wheel python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
     ```

   - **Windows:** Please refer to the [WeasyPrint documentation](https://doc.weasyprint.org/stable/first_steps.html#windows) for installation instructions, typically involving installing GTK+.

### Running the Flow

To kick off the entire financial analysis workflow, run the main flow:

```bash
crewai flow kickoff
```

This command will execute the predefined sequence of crews (Crypto, Stock, ETF, Portfolio Review) and generate the final reports in both HTML and PDF formats in the `output/` directory.

### Portfolio Data Setup

For portfolio analysis functionality, create CSV files with your holdings:

1. **ETF Holdings**: Create `data/etf.csv` with columns: Name, Ticker, Currency
2. **Stock Holdings**: Create `data/stock.csv` with columns: Name, Ticker, Currency

Example CSV format:
```csv
Name,Ticker,Currency
Apple Inc,AAPL,USD
Microsoft Corporation,MSFT,USD
```

The system will automatically analyze these holdings and provide keep/sell recommendations.

## 🤖 Crews Overview

FinWiz is composed of several specialized crews:

- **Crypto Crew**: Analyzes the cryptocurrency market, focusing on technical analysis, risk assessment, and investment strategies for specific digital assets.
- **Stock Crew**: Conducts research on publicly traded stocks, performing technical analysis, screening, and risk assessment to identify promising investment opportunities.
- **ETF Crew**: Specializes in Exchange-Traded Funds (ETFs), analyzing market trends, screening for suitable funds, and assessing risk to provide investment strategies.
- **Report Crew**: Consolidates all analysis into comprehensive HTML reports with no external tools, ensuring clean separation of concerns.

## 📊 Portfolio Analysis

FinWiz includes automated portfolio review capabilities:

- **Keep/Sell Recommendations**: Analyzes existing holdings and provides actionable recommendations
- **Risk Assessment**: Standardized risk scoring across all asset classes (0-5 scale)
- **Alternative Suggestions**: Identifies better alternatives for underperforming holdings
- **CSV Integration**: Reads portfolio data from `data/etf.csv` and `data/stock.csv`
- **Validation**: Ticker existence validation across multiple exchanges and asset classes

## 📈 Quantitative Analysis Framework

FinWiz includes a comprehensive quantitative analysis framework for professional-grade financial modeling and backtesting:

### Backtesting Engine
- **Backtrader Integration**: Professional backtesting framework with strategy development capabilities
- **Strategy Framework**: Base classes for custom trading strategies with risk management
- **Performance Metrics**: Comprehensive performance analysis including Sharpe ratio, maximum drawdown, and risk-adjusted returns
- **Multi-Strategy Support**: Compare multiple strategies across different timeframes and assets

### Technical Analysis Engine
- **TA-Lib Integration**: Professional technical analysis with 150+ indicators
- **Signal Generation**: Automated buy/sell signal generation with confidence scoring
- **Confluence Detection**: Identify zones where multiple indicators align
- **Multi-Timeframe Analysis**: Analyze patterns across different timeframes

### Portfolio Optimization
- **Modern Portfolio Theory**: Mean-variance optimization with efficient frontier calculation
- **Risk Parity**: Equal risk contribution portfolio construction
- **Black-Litterman Model**: Bayesian approach to portfolio optimization
- **Hierarchical Risk Parity**: Advanced diversification using machine learning clustering

### Derivatives Pricing
- **QuantLib Integration**: Professional derivatives pricing library
- **Options Pricing**: Black-Scholes, binomial, and Monte Carlo models
- **Greeks Calculation**: Delta, gamma, theta, vega, and rho for risk management
- **Bond Analytics**: Yield curve analysis, duration, and convexity calculations

### Stock Screening
- **Fundamental Screening**: Filter stocks based on financial metrics
- **Technical Screening**: Screen based on technical indicators and patterns
- **Multi-Criteria Scoring**: Composite scoring across multiple factors
- **Universe Support**: Screen across S&P 500, NASDAQ 100, Russell 2000, and custom lists

### Performance Analytics
- **Risk-Adjusted Metrics**: Sharpe, Sortino, and Calmar ratios
- **Drawdown Analysis**: Maximum drawdown and recovery time analysis
- **Benchmark Comparison**: Alpha, beta, and tracking error calculation
- **Portfolio Attribution**: Performance attribution analysis

## 🔬 Enhanced Analysis Features

FinWiz provides sophisticated financial analysis through specialized tools:

### Technical Analysis
- **Multi-Indicator Synthesis**: RSI, MACD, Bollinger Bands analysis via Twelve Data API
- **Chart Generation**: Visual chart analysis using Chart-img API with base64 embedding
- **Pattern Recognition**: LLM-based technical pattern identification
- **Support/Resistance**: Automated level detection and confluence analysis

### Sentiment Analysis
- **Standardized Methodology**: Consistent sentiment analysis across all asset classes (stocks, ETFs, crypto)
- **Multi-Source Integration**: Alpha Vantage, Yahoo Finance, CoinMarketCap news aggregation with asset-specific sources
- **Weighted Scoring**: Confidence-weighted sentiment calculation with statistical confidence intervals
- **Trending Topics**: Automated extraction of trending topics with relevance scoring and sentiment correlation
- **Article Deduplication**: Intelligent removal of duplicate articles based on headline similarity
- **Impact Assessment**: Top positive/negative articles with scores and citations for transparency

### Data Validation & Quality
- **Schema Enforcement**: Strict Pydantic v2 models with `extra='forbid'` validation
- **Configurable Validation**: Off/warn/error modes for different deployment environments
- **Contract Testing**: Automated validation of data contracts between crews
- **Error Handling**: Graceful degradation with detailed error reporting

### Performance & Caching
- **Intelligent Caching**: Multi-backend caching system (memory/file/hybrid) with configurable TTL
- **Cache Strategies**: LRU, LFU, TTL, and adaptive eviction strategies
- **Performance Monitoring**: Comprehensive cache statistics and hit rate tracking
- **Cache Warming**: Pre-loading of frequently accessed data for optimal performance

## ⚡ Performance Enhancements

### Asynchronous Execution

To improve performance, FinWiz leverages asynchronous task execution for I/O-bound operations. Tasks that involve fetching data from the web or calling external APIs are marked with `async_execution=True`.

**Important Note:** When using a `Process.sequential` workflow in CrewAI, the final task in the sequence **must be synchronous**. All other tasks can be asynchronous. This is a current limitation of the framework that FinWiz adheres to.

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Agent Handbook](docs/agent_handbook.md)**: Guidelines and standards for AI agents
- **[Design Principles](docs/DESIGN_PRINCIPLES.md)**: Core architectural principles and patterns
- **[Technical Reference](docs/reference.md)**: Complete API and configuration reference
- **[Quantitative Analysis](docs/quantitative_analysis.md)**: Comprehensive guide to quantitative analysis framework
- **[Validation System](docs/validation_system.md)**: Data validation infrastructure guide
- **[Caching System](docs/caching_system.md)**: Intelligent caching capabilities
- **[Migration Guide](docs/migration_guide.md)**: Guide for upgrading to latest features
- **[Schemas Documentation](docs/schemas/README.md)**: Pydantic models and JSON schemas

## 🔧 Development

### Code Quality
- **Linting**: `ruff check . && ruff format .`
- **Testing**: `uv run pytest -m "not integration"`
- **Coverage**: `uv run pytest --cov=src/finwiz`

### Performance Monitoring
- **Cache Statistics**: Monitor hit rates and performance metrics
- **Validation Metrics**: Track validation errors and warnings
- **API Rate Limits**: Automatic throttling and retry strategies

---

Happy analyzing!


export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
