# FinWiz: AI-Powered Financial Research Platform

**FinWiz** is a sophisticated financial analysis platform powered by autonomous AI agents built with the [CrewAI](https://github.com/joaomdmoura/crewai) framework. It leverages specialized crews of AI agents to perform in-depth research and generate comprehensive reports on various financial instruments, including cryptocurrencies, stocks, and ETFs.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- `uv` package manager ([install here](https://docs.astral.sh/uv/getting-started/installation/))
- API keys for at least one AI provider (OpenAI, Anthropic, Perplexity, etc.)

### Installation

```bash
# Clone the repository
git clone https://github.com/finwiz/finwiz.git
cd finwiz

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running FinWiz

```bash
# Analyze a portfolio
uv run python -m finwiz.main --portfolio portfolio.json

# Discover A+ investments
uv run python -m finwiz.discovery --asset-class stock

# Rebalance a portfolio
uv run python -m finwiz.rebalancing --portfolio portfolio.json
```

## ✨ Key Features

### Core Capabilities

- **Specialized Research Crews**: Dedicated crews for Crypto, Stocks, and ETFs with tailored agents and tasks
- **Portfolio Analysis**: Comprehensive automated portfolio review with keep/sell recommendations and risk assessment
- **Portfolio Rebalancing**: Professional-grade rebalancing with intelligent trade recommendations and cost analysis
- **A+ Investment Discovery**: Proactive discovery of exceptional investment opportunities (A+ grade, score ≥ 0.95)
- **Quantitative Analysis**: Professional-grade backtesting, technical analysis, portfolio optimization, and derivatives pricing
- **Real-Time Data**: Live data retrieval from multiple sources ensuring current information
- **Structured Output**: Detailed reports in HTML and PDF formats with strict schema validation

### Advanced Features

- **Asynchronous Execution**: 10-20x performance improvements through async operations and batch processing
- **Perplexity Sonar Integration**: Enhanced research capabilities with circuit breaker protection
- **Intelligent Caching**: Advanced caching with TTL support and multiple backends
- **Data Validation**: Centralized validation system with configurable strictness modes
- **Python Scoring Engine**: High-performance deterministic scoring (10-20x faster, 100% cost reduction)
- **Comprehensive Testing**: Extensive test coverage with mocked external dependencies

## 📂 Project Structure

```
finwiz/
├── src/finwiz/
│   ├── crews/                    # AI agent crews for different asset classes
│   │   ├── crypto_crew/
│   │   ├── etf_crew/
│   │   ├── stock_crew/
│   │   ├── portfolio_rebalancing_crew/
│   │   ├── investment_discovery_crew/
│   │   └── report_crew/
│   ├── flows/                    # Flow orchestration and coordination
│   ├── orchestrators/            # Portfolio analysis and rebalancing logic
│   ├── quantitative/             # Quantitative analysis framework
│   │   ├── technical/            # Technical analysis components
│   │   ├── backtesting.py        # Backtrader integration
│   │   ├── optimization.py       # Portfolio optimization
│   │   ├── derivatives.py        # Derivatives pricing
│   │   └── screening.py          # Stock screening
│   ├── integration/              # Data integration and validation
│   ├── schemas/                  # Pydantic data models
│   ├── tools/                    # Custom financial analysis tools
│   └── utils/                    # Utility functions and helpers
├── tests/                        # Comprehensive test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test fixtures and factories
├── docs/                         # Documentation (Diátaxis framework)
│   ├── tutorials/                # Learning-oriented guides
│   ├── how-to/                   # Problem-solving guides
│   ├── reference/                # API and configuration reference
│   └── explanations/             # Conceptual explanations
└── pyproject.toml               # Project configuration
```

## 📚 Documentation

FinWiz uses the [Diátaxis framework](https://diataxis.fr/) for documentation organization:

- **[Tutorials](docs/tutorials/)** - Learn by doing with step-by-step guides
- **[How-To Guides](docs/how-to/)** - Solve specific problems and tasks
- **[Reference](docs/reference/)** - API documentation and configuration reference
- **[Explanations](docs/explanations/)** - Understand concepts and architecture

### Key Documentation

- **[Getting Started](docs/tutorials/)** - First steps with FinWiz
- **[Agent Configuration](docs/reference/agent_configuration.md)** - Configure AI agents
- **[Tool Configuration](docs/reference/tool_configuration.md)** - Configure analysis tools
- **[Data Sources](docs/reference/data_sources.md)** - Available data providers
- **[Testing Guide](docs/how-to/testing.md)** - Write and run tests
- **[Performance Monitoring](docs/how-to/PERFORMANCE_MONITORING.md)** - Monitor system performance

## 🏗️ Architecture

### Modular Design

FinWiz follows a modular architecture with clear separation of concerns:

- **Crews**: Autonomous AI agents organized by asset class
- **Orchestrators**: Coordinate crew execution and manage workflows
- **Tools**: Specialized tools for data retrieval and analysis
- **Schemas**: Strict Pydantic models for data validation
- **Integration**: Centralized data access and validation layer

### Recent Modernization (Phase 2B)

The codebase has undergone significant modernization:

- **Decomposed Large Files**: Monolithic files split into focused modules (e.g., 1062-line screening tool → 5 focused modules)
- **Improved Organization**: Better directory structure with clear separation of concerns
- **Enhanced Type Safety**: Comprehensive type hints and mypy strict mode compliance
- **Better Testing**: Reorganized test structure with improved organization
- **Code Quality**: Reduced complexity, improved maintainability, better documentation

## 🔧 Configuration

### Environment Variables

```bash
# AI Provider Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PERPLEXITY_API_KEY=pplx-...
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=...
XAI_API_KEY=...

# Optional: Data Provider Keys
ALPHA_VANTAGE_API_KEY=...
TWELVE_DATA_API_KEY=...
COINMARKETCAP_API_KEY=...

# Optional: Feature Flags
DEEP_ANALYSIS_ENABLED=true
PERPLEXITY_RESEARCH_ENABLED=true
VALIDATION_STRICTNESS=warn  # off, warn, or error
```

### Configuration Files

- **`pyproject.toml`** - Project metadata and dependencies
- **`mkdocs.yml`** - Documentation site configuration
- **`.env`** - Local environment variables (not committed)
- **`src/finwiz/crews/*/config/`** - Agent and task configurations (YAML)

## 🧪 Testing

FinWiz has comprehensive test coverage with unit and integration tests:

```bash
# Run all tests
uv run pytest

# Run specific test suite
uv run pytest tests/unit/tools/

# Run with coverage
uv run pytest --cov=src/finwiz --cov-report=html

# Run specific test
uv run pytest tests/unit/tools/test_market_screening_tool.py::test_should_screen_stocks
```

### Testing Standards

- **Unit Tests**: Fast, isolated tests with mocked dependencies
- **Integration Tests**: Test real interactions between components
- **Fixtures**: Comprehensive test data generation with Faker
- **Mocking**: pytest-mock for all external dependencies (unittest.mock is banned)

See [Testing Guide](docs/how-to/testing.md) for detailed information.

## 📊 Data Validation

FinWiz implements strict data validation at multiple levels:

- **Schema Validation**: Pydantic v2 models with `extra='forbid'`
- **Validation Manager**: Centralized validation with configurable strictness
- **Data Freshness**: Automatic validation of data timestamps
- **Error Context**: Detailed error messages with field-level context

Configuration via `VALIDATION_STRICTNESS`:

- `off` - Validation disabled (development only)
- `warn` - Errors converted to warnings (default)
- `error` - Strict enforcement, halt on errors (production)

## 🚀 Performance

FinWiz is optimized for performance:

- **Asynchronous Operations**: 10-20x speedup through async/await
- **Batch Processing**: Concurrent crew execution for portfolio analysis
- **Intelligent Caching**: TTL-based caching with multiple backends
- **Python Scoring**: Deterministic scoring engine (10-20x faster than AI)
- **Data Prefetching**: Advanced batch data retrieval

## 🔐 Security

- **API Key Management**: Environment variables only, never hardcoded
- **Input Validation**: Strict Pydantic validation for all inputs
- **Rate Limiting**: Configured rate limits for API calls
- **Error Handling**: Graceful degradation with clear error messages
- **Type Safety**: mypy strict mode for compile-time type checking

## 📈 Development Workflow

### Using Taskmaster

FinWiz uses [Taskmaster](https://github.com/taskmaster-ai/taskmaster) for task management:

```bash
# Initialize Taskmaster
task-master init

# Parse requirements
task-master parse-prd .taskmaster/docs/prd.txt

# Daily workflow
task-master next                    # Get next task
task-master show <id>              # View task details
task-master set-status --id=<id> --status=done  # Mark complete
```

### Development Standards

- **Type Hints**: Full type annotations with mypy strict mode
- **Testing**: Comprehensive test coverage (80%+ target)
- **Documentation**: Docstrings for all public functions
- **Code Style**: Black formatting, isort imports, ruff linting
- **Git Workflow**: Feature branches, meaningful commits, pull requests

See [Development Standards](docs/how-to/testing.md) for detailed guidelines.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Follow code standards** - See development guidelines above
3. **Write tests** - Maintain 80%+ coverage
4. **Update documentation** - Keep docs in sync with code
5. **Submit a pull request** - Include clear description of changes

## 📝 License

FinWiz is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Email**: support@finwiz.dev

## 🎯 Roadmap

### Current Phase (Phase 2B)

- ✅ Codebase modernization and refactoring
- ✅ Improved code organization and modularity
- ✅ Enhanced type safety and testing
- 🔄 Performance optimization and benchmarking

### Upcoming

- Enhanced real-time portfolio monitoring
- Advanced scenario analysis and stress testing
- Machine learning-based pattern recognition
- Mobile app for portfolio management
- API for third-party integrations

## 📊 Project Statistics

- **Lines of Code**: ~50,000+ (production code)
- **Test Coverage**: 80%+ (unit and integration tests)
- **Documentation**: Comprehensive (Diátaxis framework)
- **Type Coverage**: 95%+ (mypy strict mode)
- **Modules**: 100+ (well-organized and focused)

## 🙏 Acknowledgments

FinWiz is built on top of excellent open-source projects:

- [CrewAI](https://github.com/joaomdmoura/crewai) - AI agent framework
- [Pydantic](https://github.com/pydantic/pydantic) - Data validation
- [Backtrader](https://github.com/mementum/backtrader) - Backtesting engine
- [TA-Lib](https://github.com/ta-lib/ta-lib-python) - Technical analysis
- [PyPortfolioOpt](https://github.com/robertmartin8/pyportfolioopt) - Portfolio optimization
- [FastAPI](https://github.com/tiangolo/fastapi) - Web framework

---

**Last Updated**: November 2025
**Version**: 2.0 (Post-Phase 2B Modernization)
**Status**: Active Development
