# Technology Stack

**Analysis Date:** 2026-02-07

## Languages

**Primary:**

- Python 3.12 (cpython-3.12.11-macos-aarch64-none) - All source code

**Secondary:**

- YAML - Agent and task configurations (`crews/*/config/`)
- Markdown - Documentation (`docs/`, MkDocs)

## Runtime

**Environment:**

- CPython 3.12.11

**Package Manager:**

- uv (modern Python package manager)
- Lockfile: `uv.lock` (present, managed)

## Frameworks

**Core:**

- CrewAI >=1.5.0 - AI agent framework with flow orchestration
  - Extras: `google-genai`, `tools`
  - Configured as flow type in `pyproject.toml`

**Web/API:**

- FastAPI >=0.128.0 - API endpoints (portfolio rebalancing API)

**AI/LLM:**

- LangChain >=0.3.27 - LLM orchestration
- LangChain OpenAI >=1.0.3 - OpenAI integration
- LangChain Community >=0.3.29 - Community integrations
- LiteLLM >=1.80.0 - Multi-provider LLM gateway

**Financial Analysis:**

- Backtrader >=1.9.78.123 - Backtesting framework
- TA-Lib >=0.6.6 - Technical analysis indicators
- QuantLib >=1.39 - Quantitative finance library
- PyPortfolioOpt >=1.5.5 - Portfolio optimization
- Empyrical-Reloaded >=0.5.12 - Performance metrics

**Data Processing:**

- Pandas >=2.3.2 - Data analysis
- NumPy >=1.26.4 - Numerical computing
- SciPy >=1.15.3 - Scientific computing
- Statsmodels >=0.14.5 - Statistical modeling

**Testing:**

- pytest >=8.4.1 - Test runner
- pytest-mock >=3.14.1 - Mocking (unittest.mock BANNED)
- pytest-cov >=7.0.0 - Coverage reporting (65% minimum)
- pytest-asyncio >=0.24.0 - Async test support
- pytest-timeout >=2.4.0 - Test timeouts
- Hypothesis >=6.148.1 - Property-based testing
- Faker >=33.1.0 - Test data generation

**Build/Dev:**

- Hatchling - Build backend
- Ruff >=0.11.13 - Linting and formatting (180 char line length)
- Mypy >=1.17.1 - Static type checking
- Pre-commit >=4.0.1 - Git hooks
- Bandit >=1.8.6 - Security scanning
- Safety >=3.2.4 - Dependency vulnerability scanning
- pip-audit >=2.9.0 - Dependency auditing

**Documentation:**

- MkDocs >=1.6.1 - Documentation site generator
- MkDocs Material >=9.6.22 - Material theme
- MkDocs Mermaid2 Plugin >=1.2.3 - Diagram support
- MkDocs Awesome Pages >=2.10.1 - Page organization
- MkDocs Git Revision Date >=1.5.0 - Git-based dates

## Key Dependencies

**Critical:**

- crewai[google-genai,tools] >=1.5.0 - Core agent framework
- pydantic >=2.11.7 - Data validation (all schemas in `schemas/`)
- yfinance >=0.2.62 - Primary market data source
- python-dotenv >=1.0.1 - Environment configuration

**Infrastructure:**

- supabase >=2.22.4 - PostgreSQL database client
- asyncpg >=0.30.0 - Async PostgreSQL driver
- qdrant-client >=1.16.0 - Vector database client
- faiss-cpu >=1.9.0 - Local vector search

**Web Scraping:**

- firecrawl-py >=2.7.1 - Web scraping
- beautifulsoup4 >=4.14.2 - HTML parsing
- unstructured >=0.18.11 - Document processing

**Data Sources:**

- sec-edgar-downloader >=5.0.0 - SEC filings
- sec-api >=1.0.32 - SEC API client
- intrinio >=0.2.1 - Financial data API
- eod >=0.2.1 - End-of-day data
- quandl >=3.7.0 - Economic data
- serpapi >=0.1.5 - Search API
- tavily-python >=0.7.5 - Research API
- perplexityai >=0.12.0 - Perplexity AI integration

**Utilities:**

- plotly >=6.3.0 - Interactive charts
- nest-asyncio >=1.6.0 - Nested event loops
- trio >=0.31.0 - Async I/O
- cryptography >=46.0.3 - Encryption utilities

## Configuration

**Environment:**

- Configuration: Pydantic BaseSettings in `src/finwiz/config/settings.py`
- Environment files: `.env`, `config/development.env`, `config/staging.env`, `config/production.env`
- Environment prefix: `FINWIZ_`
- Nested delimiter: `__`

**Build:**

- `pyproject.toml` - Project metadata, dependencies, tool configs
- `ruff.toml` - Code quality rules (in pyproject.toml)
- `mypy.ini` - Type checking configuration
- `.pre-commit-config.yaml` - Pre-commit hooks

**Testing:**

- Pytest config in `pyproject.toml`
- Default markers: `integration`, `unit`, `slow`, `asyncio`, `performance`, `benchmark`, `crew`, `flow`
- Default run excludes integration tests (`-m "not integration"`)
- Coverage threshold: 65%
- Test paths: `tests/`

**Code Quality:**

- Line length: 180 characters
- Python target: py312
- Formatter: Ruff (double quotes, 4-space indent)
- Linter: Ruff (E, F, W, I, UP, TID rules)
- Type checker: Mypy (gradual adoption, strict for `utils/` and `schemas/`)

## Platform Requirements

**Development:**

- Python 3.12+ (3.13 not supported per `requires-python = ">=3.12,<3.13"`)
- uv package manager
- macOS/Linux (primary development on macOS ARM64)

**Production:**

- Deployment: Not containerized (no Dockerfile detected)
- Documentation: GitHub Pages (MkDocs Material)
- CI/CD: GitHub Actions (docs deployment)
- Hosting: No production hosting detected in codebase

---

*Stack analysis: 2026-02-07 (updated 2026-02-08 after v2)*
