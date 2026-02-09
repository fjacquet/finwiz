# Technology Stack: News Sentiment, Macro Indicators & Additional Data Providers

**Project:** FinWiz Milestone -- Data Enrichment & Sentiment
**Researched:** 2026-02-08
**Overall confidence:** MEDIUM-HIGH (verified against PyPI, official docs, and existing codebase patterns)

## Recommended Stack Additions

### News Data Sources

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `finnhub-python` | `>=2.4.27` | Company news + market news API | FREE tier: 60 calls/min, company_news and market_news endpoints available on free plan, pre-built sentiment scores for US companies, official Python client, returns structured JSON. Fills the gap where Alpha Vantage NEWS_SENTIMENT requires API key and CoinMarketCap requires paid key. |
| `feedparser` | `>=6.0.12` | RSS feed aggregation from financial news outlets | FREE, zero API keys, mature (1M+ weekly downloads), parses RSS/Atom/RDF. Yahoo Finance, Reuters, Bloomberg all have public RSS feeds. Provides a completely free fallback news source that never rate-limits. |
| `gnews` | `>=0.4.3` | Google News search for ticker-specific news | FREE, scrapes Google News RSS, no API key required, returns structured JSON with title/description/URL/date. Good for broad news coverage across 141+ countries. Lightweight supplement when Finnhub and RSS miss stories. |

### Sentiment Analysis (NLP)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `vaderSentiment` | `>=3.3.2` | Headline-level sentiment scoring | Deterministic (no ML model loading), MIT license, zero dependencies beyond requests, returns compound score -1 to +1. Runs in <1ms per headline. Aligns with AI Minimalism principle: Python for deterministic tasks. Replaces current keyword-matching approach with validated lexicon+rules engine that handles capitalization, punctuation, negation, and degree modifiers. |

**Why NOT FinBERT/Transformers:** FinBERT achieves 91% F1 vs VADER's ~63% on academic benchmarks, but requires ~500MB model download, GPU-optional inference at ~50ms/headline, and PyTorch/transformers dependency chain. FinWiz's AI Minimalism principle says "use Python for deterministic tasks, AI only for qualitative reasoning." Sentiment scoring is a deterministic input to the composite scorer. VADER is the right tradeoff: fast, free, deterministic, good enough for headline-level scoring where the scoring engine already aggregates across 10-20+ articles. Consider FinBERT as a future differentiator if VADER proves insufficient, gated behind a feature flag.

### Macroeconomic Data

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `fredapi` | `>=0.5.2` | FRED API client for US macro indicators | FREE API key (instant registration), 800K+ time series, direct pandas integration. Provides GDP, CPI, unemployment, fed funds rate, yield curve, VIX -- exactly what the existing `MacroIndicators` schema needs. Already listed in pyproject.toml mypy overrides (fredapi.*) suggesting prior consideration. The existing `MarketContextExtractor` has `_extract_gdp_growth()` and `_extract_unemployment_rate()` returning None with TODO comments -- FRED fills these directly. |

**Why NOT pandas-datareader for FRED:** pandas-datareader's FRED reader is a thin wrapper over the same API, but fredapi has search(), get_series_info(), and vintage date support. fredapi is more purpose-built and already anticipated in the codebase (mypy config).

**Why NOT wbgapi (World Bank):** World Bank data is annual, lagged 6-12 months, and focused on development economics. FRED provides monthly/quarterly US macro data with near-real-time updates -- far more relevant for investment analysis.

### Additional Market Data Providers

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `finnhub-python` | `>=2.4.27` | Economic calendar, earnings calendar, market status, quote data | Same library as news (dual purpose). FREE tier includes economic calendar (FOMC dates, employment reports, CPI releases), earnings calendars, and basic market data. Supplements existing yfinance/Alpha Vantage/Tiingo chain with forward-looking event data that none of the current sources provide. |
| `fear-and-greed` | `>=0.0.8` | CNN Fear & Greed Index | FREE, scrapes CNN data endpoint, returns current index + historical values. Provides market-wide sentiment indicator for the composite scorer. Simple, focused library. |

### Supporting Libraries (already in project, no new install needed)

| Library | Already Installed | Purpose for New Features |
|---------|-------------------|--------------------------|
| `aiohttp` | Yes (used in SentimentAnalyzer) | Async HTTP for Finnhub/FRED API calls |
| `aiolimiter` | Yes (`>=1.2.1`) | Rate limiting for Finnhub (60 calls/min) and FRED |
| `pandas` | Yes (`>=2.3.2`) | FRED data processing (fredapi returns pandas Series) |
| `pydantic` | Yes (`>=2.11.7`) | Schemas for news, sentiment, macro data models |
| `beautifulsoup4` | Yes (`>=4.14.2`) | Optional: parsing RSS content if feedparser needs help |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| News API | Finnhub (free tier) | NewsAPI.org | NewsAPI free tier is developer-only (non-commercial), 100 requests/day max, cannot be used in production. Finnhub free tier allows commercial use with 60 calls/min. |
| News API | Finnhub | Financial Modeling Prep | FMP free tier limited to 250 calls/day, requires attribution. Finnhub is more generous. |
| Sentiment NLP | VADER | TextBlob | TextBlob accuracy 41-78% vs VADER 63% on financial text. TextBlob is slower (creates full NLP objects). VADER designed specifically for short text/social media, better for headlines. |
| Sentiment NLP | VADER | FinBERT (transformers) | Overkill: 500MB model, PyTorch dependency, ~50ms/headline. Violates AI Minimalism. Consider only if VADER proves insufficient, behind feature flag. |
| Sentiment NLP | VADER | LLM-based (GPT/Claude) | Expensive ($0.01+/headline), slow (1-2s/headline), non-deterministic. Violates both AI Minimalism and $0 cost target for scoring. |
| Macro Data | fredapi (FRED) | Quandl | Quandl already in pyproject.toml but most free datasets discontinued after Nasdaq acquisition. FRED is the gold standard for US macro data with guaranteed free access. |
| Macro Data | fredapi (FRED) | pandas-datareader | Less feature-rich FRED client. fredapi has better search, vintage dates, and is more actively maintained. |
| Market Data | Finnhub (economic calendar) | TradingEconomics | TradingEconomics API is paid-only ($20/mo minimum). Finnhub includes free economic calendar. |
| Google News | gnews | pygooglenews | pygooglenews appears abandoned (last update 2021). gnews is actively maintained with recent releases. |
| Fear/Greed | fear-and-greed | Manual CNN scraping | fear-and-greed wraps the same CNN endpoint but handles edge cases, returns typed data. No reason to rewrite. |
| Stock Screener | Not adding | finvizfinance | Python 3.11 max compatibility listed (not 3.12). Scraping-based (fragile). FinWiz already has screening via existing tools. |

## Integration Points with Existing Architecture

### Adapter Pattern (data/adapters/)

New data sources should follow the existing `BaseDataAdapter` pattern in `data/adapters/base_adapter.py`. However, news, sentiment, and macro data have different shapes than the current `FundamentalData` dataclass. Recommendation:

1. **Create parallel adapter interfaces** for the new data types:
   - `BaseNewsAdapter` -- returns standardized `NewsArticle` list
   - `BaseMacroAdapter` -- returns standardized `MacroSnapshot`
   - `BaseSentimentAdapter` -- wraps VADER, returns scored articles

2. **New orchestrator layer** (`data/news_orchestrator.py`, `data/macro_orchestrator.py`) following the pattern of the existing `DataSourceOrchestrator` with waterfall fallback:
   - News: Finnhub -> gnews -> feedparser (RSS)
   - Macro: fredapi (FRED) primary, with cached fallback

3. **Integrate with existing caching** via `AnalysisCacheManager` and `@cache_result` decorator:
   - News: 1-hour TTL (hot cache)
   - Macro indicators: 6-hour TTL (warm cache, data updates infrequently)
   - Fear & Greed: 4-hour TTL
   - Sentiment scores: Cache alongside their source articles

### Scoring Engine (scoring/)

The existing `DeepAnalysisScorer` uses 40% fundamental + 30% technical + 30% risk. Sentiment and macro data feed into this as:

- **Sentiment score** -- new input to `RiskScorer` or as a 4th component
- **Macro indicators** -- feed into `MarketContextExtractor` (replacing hardcoded estimates)
- **Fear & Greed** -- market-wide sentiment input to risk assessment

### Feature Flag Gating

All new data sources should be gated behind feature flags following the existing pattern in `config/features/`:
- `FF_NEWS_SENTIMENT_ENABLED` -- enables Finnhub/gnews/RSS news collection
- `FF_MACRO_INDICATORS_ENABLED` -- enables FRED macro data collection
- `FF_FEAR_GREED_ENABLED` -- enables Fear & Greed index collection
- Each with `FallbackStrategy.CACHED_ONLY` as default fallback

### Endpoints Configuration

New API base URLs should be added to `config/endpoints.py`:
```python
FINNHUB_BASE: str = os.getenv("FINNHUB_BASE_URL", "https://finnhub.io/api/v1")
FRED_BASE: str = os.getenv("FRED_BASE_URL", "https://api.stlouisfed.org/fred")
```

## Environment Variables (New)

```bash
# News Data Sources
FINNHUB_API_KEY=...                    # Required for Finnhub (free registration)
FF_NEWS_SENTIMENT_ENABLED=true         # Feature flag for news collection

# Macroeconomic Data
FRED_API_KEY=...                       # Required for FRED (free registration)
FF_MACRO_INDICATORS_ENABLED=true       # Feature flag for macro data

# Market Sentiment
FF_FEAR_GREED_ENABLED=true             # Feature flag for Fear & Greed index

# Optional tuning
NEWS_MAX_ARTICLES_PER_SOURCE=20        # Max articles to fetch per source
NEWS_LOOKBACK_DAYS=7                   # Days to look back for news
MACRO_CACHE_TTL_HOURS=6                # Macro data cache TTL
```

## Installation

```bash
# New dependencies (add to pyproject.toml)
uv add finnhub-python>=2.4.27
uv add feedparser>=6.0.12
uv add gnews>=0.4.3
uv add vaderSentiment>=3.3.2
uv add fredapi>=0.5.2
uv add fear-and-greed>=0.0.8
```

Estimated total new dependency footprint: ~5MB (all lightweight, no ML frameworks).

## Version Verification Summary

| Package | Version | Source | Confidence |
|---------|---------|--------|------------|
| finnhub-python | 2.4.27 | PyPI (Jan 2026 release confirmed) | HIGH |
| feedparser | 6.0.12 | PyPI (Sep 2025 release) | HIGH |
| gnews | 0.4.3 | PyPI (confirmed available) | MEDIUM |
| vaderSentiment | 3.3.2 | PyPI (confirmed, MIT license) | HIGH |
| fredapi | 0.5.2 | PyPI (confirmed, GitHub active) | HIGH |
| fear-and-greed | 0.0.8 | PyPI (confirmed) | MEDIUM |

## Sources

- [Finnhub API Documentation](https://finnhub.io/docs/api)
- [Finnhub Python Client (GitHub)](https://github.com/Finnhub-Stock-API/finnhub-python)
- [finnhub-python PyPI](https://pypi.org/project/finnhub-python/)
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/)
- [fredapi (GitHub)](https://github.com/mortada/fredapi)
- [fredapi PyPI](https://pypi.org/project/fredapi/)
- [vaderSentiment (GitHub)](https://github.com/cjhutto/vaderSentiment)
- [vaderSentiment PyPI](https://pypi.org/project/vaderSentiment/)
- [feedparser PyPI](https://pypi.org/project/feedparser/)
- [gnews PyPI](https://pypi.org/project/gnews/)
- [fear-and-greed PyPI](https://pypi.org/project/fear-and-greed/)
- [FinBERT (GitHub)](https://github.com/ProsusAI/finBERT) -- considered but not recommended
- [Finnhub Rate Limits](https://finnhub.io/docs/api/rate-limit)
- [FRED Web Services](https://fred.stlouisfed.org/docs/api/fred/)
