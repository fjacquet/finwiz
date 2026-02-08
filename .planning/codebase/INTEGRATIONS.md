# External Integrations

**Analysis Date:** 2026-02-07

## APIs & External Services

**AI/LLM Providers:**

- OpenAI - Primary LLM provider
  - SDK/Client: `langchain-openai`, `crewai`
  - Auth: `OPENAI_API_KEY`
  - Model: Configurable via `OPENAI_MODEL_NAME` (default: gpt-4o-mini)
  - Timeout: `OPENAI_TIMEOUT` (default: 300s)
  - Usage: Agent reasoning, analysis generation

- Anthropic - Alternative LLM provider
  - SDK/Client: `langchain`, `crewai`
  - Auth: `ANTHROPIC_API_KEY`
  - Usage: Optional alternative to OpenAI

- Perplexity AI - Research and search
  - SDK/Client: `perplexityai` package
  - Auth: `PPLX_API_KEY`
  - Endpoint: `https://api.perplexity.ai/chat/completions`
  - Feature flag: `FF_PERPLEXITY_RESEARCH`
  - Circuit breaker: Threshold 10, timeout 300s
  - Implementation: `src/finwiz/tools/perplexity_search_tool.py`

- OpenRouter - Multi-model gateway
  - Auth: `OPENROUTER_API_KEY`
  - Model selection: `LLM_MODEL_STANDARD`, `LLM_MODEL_MINI`, `LLM_MODEL_MANAGER`, `LLM_MODEL_PLANNING`, `LLM_MODEL_THINKING`
  - Recommended models: Grok 4.1 Fast, Gemini 3 Flash, Claude Opus 4.5, DeepSeek V3.2

**Search & Research:**

- Serper - Web search API
  - SDK/Client: Custom integration
  - Auth: `SERPER_API_KEY`
  - Usage: Market research, news search

- SerpAPI - Alternative search API
  - SDK/Client: `serpapi` package
  - Auth: `SERPAPI_API_KEY`

- Firecrawl - Web scraping
  - SDK/Client: `firecrawl-py` >=2.7.1
  - Auth: `FIRECRAWL_API_KEY`
  - Usage: Website data extraction

- Tavily - Research API
  - SDK/Client: `tavily-python` >=0.7.5
  - Auth: `TAVILY_API_KEY`

- Brave Search - Alternative search
  - Auth: `BRAVE_API_KEY`

**Financial Data - Market Data:**

- Yahoo Finance - Primary market data source
  - SDK/Client: `yfinance` >=0.2.62
  - Auth: None (public API)
  - Config: `src/finwiz/config/yfinance_config.py`
  - Features: Stock prices, company info, ETF holdings, news
  - Retries: Configurable via `FINWIZ_YFINANCE__RETRIES` (default: 2)
  - Tools: `src/finwiz/tools/yahoo_finance_*.py` (11 specialized tools)

- Alpha Vantage - Fundamental data
  - SDK/Client: Custom HTTP client
  - Auth: `ALPHA_VANTAGE_API_KEY`
  - Rate limit: 5 calls/min (free), 75 calls/min (premium)
  - Config: `ALPHA_VANTAGE_RATE_LIMIT`
  - Implementation: `src/finwiz/tools/alpha_vantage_tool.py`

- TwelveData - Real-time market data
  - SDK/Client: Custom HTTP client
  - Auth: `TWELVE_DATA_API_KEY`, `TWELVEDATA_API_KEY`
  - Feature flag: `FF_TWELVE_DATA`
  - Circuit breaker: Threshold 3, timeout 900s
  - Implementation: `src/finwiz/tools/twelve_data_*.py`

**Financial Data - SEC Filings:**

- SEC EDGAR - Public company filings
  - SDK/Client: `sec-edgar-downloader` >=5.0.0
  - Auth: None (public data)
  - Implementation: `src/finwiz/tools/sec_tool.py`

- SEC API - SEC filings API
  - SDK/Client: `sec-api` >=1.0.32
  - Auth: `SEC_API_API_KEY`

**Financial Data - Other:**

- Intrinio - Financial data platform
  - SDK/Client: `intrinio` >=0.2.1
  - Auth: API key (env var not documented)

- EOD Historical Data - End-of-day data
  - SDK/Client: `eod` >=0.2.1
  - Auth: API key (env var not documented)

- Quandl - Economic data
  - SDK/Client: `quandl` >=3.7.0
  - Auth: API key (env var not documented)

**Cryptocurrency:**

- CoinMarketCap - Crypto market data
  - Auth: `COINMARKETCAP_API_KEY`, `CMC_PRO_API_KEY`
  - Implementation: Tools for crypto analysis

- Kraken - Crypto exchange API
  - Auth: `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`
  - Usage: Crypto trading data

**Charting:**

- ChartImg - Chart generation API
  - Auth: `CHART_IMG_API_KEY`, `CHARTIMG_API_KEY`
  - Feature flag: `FF_CHART_ANALYSIS`
  - Circuit breaker: Threshold 2, timeout 600s

## Data Storage

**Databases:**

- Supabase (PostgreSQL)
  - Connection: Environment variables (not explicitly documented)
  - Client: `supabase` >=2.22.4, `asyncpg` >=0.30.0
  - Usage: Crew output caching, analysis storage
  - Note: Disabled for synchronous Python analyzer due to event loop conflicts
  - Implementation: Referenced in `src/finwiz/scoring/portfolio_deep_analyzer.py`

**Vector Databases:**

- Qdrant - Remote vector search
  - Client: `qdrant-client` >=1.16.0
  - Usage: LangChain embeddings, RAG

- FAISS - Local vector search
  - Client: `faiss-cpu` >=1.9.0
  - Usage: Local embeddings, similarity search

**File Storage:**

- Local filesystem - Primary storage
  - Locations: `cache/`, `output/`, `htmlcov/`, `logs/`
  - Reports: HTML and PDF in `output/`

**Caching:**

- Hybrid cache system
  - Backend: `CACHE_BACKEND` (memory, file, hybrid)
  - TTL: `CACHE_TTL` (default: 2700s = 45 minutes)
  - Max memory items: `CACHE_MAX_MEMORY_ITEMS` (default: 10000)
  - Max file size: `CACHE_MAX_FILE_SIZE_MB` (default: 100MB)
  - Directory: `CACHE_DIRECTORY` (default: `cache/`)
  - Strategy: `CACHE_STRATEGY` (ttl, lru, lfu, adaptive)
  - Compression: `CACHE_ENABLE_COMPRESSION` (default: true)
  - Implementation: `src/finwiz/infrastructure/caching/manager.py`

## Authentication & Identity

**Auth Provider:**

- None detected - No user authentication system
  - Application runs locally or in trusted environment
  - API keys managed via environment variables

**API Key Management:**

- Storage: `.env` file (not committed)
- Loading: `python-dotenv` >=1.0.1
- Validation: Optional rotation via `FINWIZ_ENABLE_API_KEY_ROTATION` (default: false)

## Monitoring & Observability

**Error Tracking:**

- None - No third-party error tracking service

**Logs:**

- Local logging - Custom logger in `src/finwiz/tools/logger.py`
  - Level: `FINWIZ_LOG_LEVEL` (default: INFO)
  - Structured: `FINWIZ_LOG_STRUCTURED` (default: true)
  - Retention: `FINWIZ_LOG_RETENTION_DAYS` (default: 30)
  - Output: `logs/` directory

**Metrics:**

- Internal metrics collection
  - Enabled: `FINWIZ_ENABLE_METRICS` (default: true)
  - Implementation: `src/finwiz/infrastructure/health/monitoring.py`

**Telemetry:**

- CrewAI telemetry disabled - `CREWAI_DISABLE_TELEMETRY=true`
- OpenTelemetry SDK disabled - `OTEL_SDK_DISABLED=true`

## CI/CD & Deployment

**Hosting:**

- GitHub Pages - Documentation only
  - Platform: Static site hosting
  - Deployment: Automated via GitHub Actions
  - URL: `https://fjacquet.github.io/finwiz`

**CI Pipeline:**

- GitHub Actions
  - Workflow: `.github/workflows/docs.yml`
  - Triggers: Push to main (docs changes), PR, manual dispatch
  - Jobs: Build, deploy, validate
  - Runner: ubuntu-latest, Python 3.12
  - Build tool: uv, MkDocs

**Application Deployment:**

- No CI/CD detected - Local execution only
  - Entry point: `uv run python src/finwiz/main.py`
  - CLI commands: `kickoff`, `run_crew`, `plot` (via `pyproject.toml`)

## Environment Configuration

**Required env vars:**

- `OPENAI_API_KEY` - OpenAI API access
- `SERPER_API_KEY` - Web search
- `FIRECRAWL_API_KEY` - Web scraping
- `PPLX_API_KEY` - Perplexity research

**Optional env vars:**

- LLM: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`
- Financial: `ALPHA_VANTAGE_API_KEY`, `TWELVE_DATA_API_KEY`, `SEC_API_API_KEY`
- Crypto: `COINMARKETCAP_API_KEY`, `KRAKEN_API_KEY`, `KRAKEN_API_SECRET`
- Search: `SERPAPI_API_KEY`, `BRAVE_API_KEY`, `TAVILY_API_KEY`
- Charts: `CHART_IMG_API_KEY`

**Secrets location:**

- `.env` file in project root (gitignored)
- Environment-specific configs in `config/*.env`

## Webhooks & Callbacks

**Incoming:**

- None - No webhook endpoints detected

**Outgoing:**

- None - No outbound webhooks configured

## Feature Flags & Circuit Breakers

**Feature Toggles:**

- Environment-based - All flags in `.env` with `FF_` prefix
- Implementation: `src/finwiz/config/features/flags.py`
- Key flags: `FF_PERPLEXITY_RESEARCH`, `FF_TWELVE_DATA`, `FF_CHART_ANALYSIS`, `FF_PORTFOLIO_REBALANCING`

**Circuit Breakers:**

- Perplexity: `FF_PERPLEXITY_BREAKER_THRESHOLD=10`, `FF_PERPLEXITY_BREAKER_TIMEOUT=300`
- TwelveData: `FF_TWELVE_DATA_BREAKER_THRESHOLD=3`, `FF_TWELVE_DATA_BREAKER_TIMEOUT=900`
- ChartImg: `FF_CHART_BREAKER_THRESHOLD=2`, `FF_CHART_BREAKER_TIMEOUT=600`
- Rebalancing: `FF_REBALANCING_BREAKER_THRESHOLD=2`, `FF_REBALANCING_BREAKER_TIMEOUT=600`
- Implementation: `src/finwiz/infrastructure/resilience/rate_limiter.py`

## Rate Limiting

**API Provider Rate Limits:**

- Alpha Vantage: `ALPHA_VANTAGE_RATE_LIMIT` (default: 5 calls/min)
- Application: `FINWIZ_RATE_LIMIT_ENABLED=true`, `FINWIZ_RATE_LIMIT_REQUESTS_PER_MINUTE=60`
- Implementation: APIProvider enum in `src/finwiz/infrastructure/resilience/rate_limiter.py`

## Retry & Resilience

**Retry Configuration:**

- Max retries: `FINWIZ_MAX_RETRIES` (default: 3)
- Base delay: `FINWIZ_RETRY_BASE_DELAY` (default: 2s)
- Max delay: `FINWIZ_RETRY_MAX_DELAY` (default: 60s)
- Implementation: `src/finwiz/config/resilience_config.py`

**Timeouts:**

- Holding analysis: `FINWIZ_HOLDING_TIMEOUT` (default: 300s)
- Flow execution: `FINWIZ_FLOW_TIMEOUT` (default: 7200s)
- Request timeout: `FINWIZ_REQUEST_TIMEOUT` (default: 30s)

---

*Integration audit: 2026-02-07*
