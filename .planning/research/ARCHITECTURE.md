# Architecture Patterns: News Sentiment, Macro Indicators & Data Provider Integration

**Domain:** Financial analysis platform data enrichment
**Researched:** 2026-02-08

## Recommended Architecture

Extend the existing layered architecture with three new data subsystems that slot into the existing Infrastructure and Domain layers. No changes needed to the Presentation or Application layers until the reporting enrichment phase.

```
Presentation (reporting/, templates/)
    |
Application (flows/, orchestrators/)
    |                         |
Domain (schemas/, scoring/)   |
    |                         |
Infrastructure:               |
  data/adapters/              |-- EXISTING
  data/data_source_orch.      |
                              |
  data/news/                  |-- NEW: News subsystem
    news_adapter_base.py      |
    finnhub_news_adapter.py   |
    gnews_adapter.py          |
    rss_adapter.py            |
    news_orchestrator.py      |
                              |
  data/macro/                 |-- NEW: Macro subsystem
    macro_adapter_base.py     |
    fred_adapter.py           |
    macro_orchestrator.py     |
                              |
  data/sentiment/             |-- NEW: Sentiment engine
    sentiment_scorer.py       |   (VADER-based, replaces keyword matching)
    fear_greed_adapter.py     |
    sentiment_orchestrator.py |
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `data/news/` | Fetch raw news articles from multiple sources with waterfall fallback | `data/sentiment/` (passes articles for scoring), cache layer |
| `data/macro/` | Fetch macroeconomic indicators from FRED with caching | `orchestrators/extraction/market_context.py` (fills MacroIndicators), cache layer |
| `data/sentiment/` | Score articles with VADER, aggregate per-holding, fetch Fear & Greed | `scoring/` (provides sentiment component), `reporting/` (provides display data) |
| `scoring/` (modified) | Accept sentiment + macro inputs for composite scoring | `data/sentiment/`, `data/macro/` via orchestrator |
| `schemas/` (extended) | New Pydantic models for news articles, sentiment scores, macro snapshots | All components above |
| `config/features/` (extended) | Feature flags for new data sources | All new adapters |
| `config/endpoints.py` (extended) | New API base URLs | All new adapters |

### Data Flow

```
1. Flow starts (flows/orchestrator.py -- Phase 3: Deep Analysis)
   |
2. DeepAnalysisOrchestrator triggers data collection
   |
   +--> EXISTING: DataSourceOrchestrator.get_fundamental_data(ticker)
   |
   +--> NEW: MacroOrchestrator.get_macro_snapshot()        [once per session, cached]
   |      |
   |      +--> FredAdapter.get_series("GDP", "UNRATE", "CPIAUCSL", "FEDFUNDS", "T10Y2Y")
   |      +--> Cache result (6-hour TTL)
   |
   +--> NEW: NewsOrchestrator.get_news(ticker)             [per holding, cached 1h]
   |      |
   |      +--> FinnhubNewsAdapter.company_news(ticker)     [primary]
   |      +--> GNewsAdapter.search(ticker)                 [fallback]
   |      +--> RSSAdapter.fetch_feeds(ticker)              [tertiary]
   |      +--> Deduplicate across sources
   |
   +--> NEW: SentimentOrchestrator.score_articles(articles) [per holding]
   |      |
   |      +--> VADER.polarity_scores(headline) for each article
   |      +--> Aggregate: weighted average by source reliability
   |      +--> Return SentimentResult (score, confidence, article_count)
   |
   +--> NEW: FearGreedAdapter.get_index()                  [once per session, cached 4h]
   |
3. All data collected --> Scoring engine
   |
   +--> DeepAnalysisScorer.calculate_composite_score(ticker, asset_class, data)
         |
         data now includes:
           data["sentiment_score"]      = 0.35  (VADER aggregate)
           data["sentiment_confidence"] = 0.8
           data["macro_snapshot"]       = {gdp_growth: 2.1, unemployment: 3.8, ...}
           data["fear_greed_index"]     = 45
         |
         +--> FundamentalScorer (40% or adjusted)
         +--> TechnicalScorer (30% or adjusted)
         +--> RiskScorer (30% or adjusted, now with sentiment + macro inputs)
```

## Patterns to Follow

### Pattern 1: Adapter + Orchestrator with Waterfall Fallback

**What:** Each data domain (news, macro, sentiment) gets its own adapter base class and orchestrator, following the proven pattern in `data/data_source_orchestrator.py`.

**When:** Any new data source integration.

**Example:**
```python
# data/news/news_adapter_base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NewsArticle:
    """Standardized news article structure."""

    ticker: str
    title: str
    summary: str
    url: str
    source: str
    published_at: datetime
    sentiment_score: float | None = None  # Filled by sentiment engine


class BaseNewsAdapter(ABC):
    """Base class for news source adapters."""

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    async def get_company_news(self, ticker: str, days_back: int = 7, max_articles: int = 20) -> list[NewsArticle]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass
```

```python
# data/news/news_orchestrator.py
class NewsOrchestrator:
    """Orchestrate multi-source news acquisition with waterfall fallback."""

    def __init__(self) -> None:
        self.adapters: list[BaseNewsAdapter] = [
            FinnhubNewsAdapter(timeout_seconds=5.0),
            GNewsAdapter(timeout_seconds=5.0),
            RSSAdapter(timeout_seconds=5.0),
        ]

    async def get_news(self, ticker: str, days_back: int = 7) -> list[NewsArticle]:
        all_articles: list[NewsArticle] = []
        for adapter in self.adapters:
            if not adapter.is_available():
                continue
            try:
                articles = await adapter.get_company_news(ticker, days_back)
                all_articles.extend(articles)
            except Exception as e:
                logger.warning(f"{adapter.source_name} failed: {e}")
                continue
        return self._deduplicate(all_articles)
```

### Pattern 2: Session-Level vs Per-Holding Data

**What:** Macro indicators and Fear & Greed are session-level (same for all holdings). News and sentiment are per-holding. Separate collection cadence prevents redundant API calls.

**When:** Collecting data that applies to the whole portfolio vs individual assets.

**Example:**
```python
# In DeepAnalysisOrchestrator or FinwizFlow
class SessionData:
    """Data collected once per analysis session."""

    macro_snapshot: MacroSnapshot | None = None
    fear_greed_index: int | None = None
    economic_calendar: list[EconomicEvent] = []


# Collected once at session start
session_data = SessionData()
session_data.macro_snapshot = await macro_orchestrator.get_snapshot()
session_data.fear_greed_index = await fear_greed_adapter.get_index()

# Per-holding analysis passes session data
for holding in portfolio:
    articles = await news_orchestrator.get_news(holding.ticker)
    sentiment = sentiment_scorer.score_articles(articles)
    data = {
        **collected_fundamental_data,
        "sentiment_score": sentiment.overall_score,
        "macro_snapshot": session_data.macro_snapshot,
        "fear_greed_index": session_data.fear_greed_index,
    }
    result = scorer.calculate_composite_score(holding.ticker, holding.asset_class, data)
```

### Pattern 3: Feature Flag Gating with Graceful Degradation

**What:** All new data sources gated behind feature flags with fallback strategies, following the existing `FeatureFlagConfig` pattern.

**When:** Any new external dependency.

**Example:**
```python
# config/features/definitions.py -- add to create_default_flags()
(
    FeatureFlagConfig(
        name="news_sentiment",
        enabled=get_env_bool("FF_NEWS_SENTIMENT_ENABLED", True),
        strategy=FeatureFlagStrategy.CIRCUIT_BREAKER,
        fallback_strategy=FallbackStrategy.CACHED_ONLY,
        circuit_breaker_threshold=3,
        circuit_breaker_timeout=600,
        description="Enable Finnhub/gnews/RSS news collection and VADER sentiment scoring",
        tags={"data", "sentiment"},
    ),
)
```

### Pattern 4: VADER Scoring as Pure Function

**What:** VADER sentiment scoring is a pure, deterministic function with no side effects. No async, no API calls, no caching needed at the scoring level.

**When:** Scoring any text content.

**Example:**
```python
# data/sentiment/sentiment_scorer.py
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class VaderSentimentScorer:
    """Deterministic sentiment scoring using VADER lexicon."""

    def __init__(self) -> None:
        self._analyzer = SentimentIntensityAnalyzer()

    def score_headline(self, text: str) -> float:
        """Score a single headline. Returns -1.0 to 1.0 compound score."""
        scores = self._analyzer.polarity_scores(text)
        return scores["compound"]

    def score_articles(self, articles: list[NewsArticle], source_weights: dict[str, float] | None = None) -> SentimentResult:
        """Score and aggregate multiple articles."""
        if not articles:
            return SentimentResult(score=0.0, confidence=0.0, article_count=0)

        weighted_scores = []
        for article in articles:
            score = self.score_headline(f"{article.title} {article.summary}")
            weight = (source_weights or {}).get(article.source, 0.5)
            weighted_scores.append(score * weight)
            article.sentiment_score = score

        avg_score = sum(weighted_scores) / sum((source_weights or {}).get(a.source, 0.5) for a in articles)
        confidence = min(1.0, len(articles) / 10)  # Full confidence at 10+ articles

        return SentimentResult(
            score=avg_score,
            confidence=confidence,
            article_count=len(articles),
        )
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Mixing News Fetching with Sentiment Scoring

**What:** Fetching news articles and computing sentiment in the same class/method.
**Why bad:** Violates single responsibility. Cannot swap VADER for FinBERT later. Cannot test scoring without mocking HTTP calls. Cannot cache articles and scores independently.
**Instead:** Separate NewsOrchestrator (fetches articles) from SentimentScorer (scores text). The orchestrator in `DeepAnalysisOrchestrator` chains them together.

### Anti-Pattern 2: Calling FRED API Per Holding

**What:** Fetching GDP/CPI/unemployment for each of 20 holdings in a portfolio.
**Why bad:** Macro data is the same for all holdings. 20 redundant API calls, wastes FRED rate limit.
**Instead:** Fetch macro snapshot ONCE at session start, pass to each holding analysis. Cache with 6-hour TTL.

### Anti-Pattern 3: Hardcoding Sentiment Weights in the Scorer

**What:** Embedding `weight_sentiment = 0.15` directly in `DeepAnalysisScorer._compute_weighted_score()`.
**Why bad:** Cannot tune weights without code changes. Cannot A/B test configurations.
**Instead:** Add sentiment weight to `ScoringThresholds` dataclass in `scoring/thresholds.py`. Allow override via environment variable or config.

### Anti-Pattern 4: Treating All News Sources as Equal

**What:** Averaging sentiment scores without considering source reliability.
**Why bad:** A blog post and a Bloomberg article should not have equal weight. Dilutes signal.
**Instead:** Use the existing `get_source_reliability_score()` tier system from `sentiment_sources.py` to weight articles before aggregation.

### Anti-Pattern 5: Making Sentiment a Blocking Dependency

**What:** Failing the entire analysis if Finnhub is down or VADER encounters an error.
**Why bad:** Sentiment is supplementary, not critical. Core analysis should work without it.
**Instead:** Feature flag with `FallbackStrategy.DEFAULT_VALUES` -- if sentiment fails, use neutral (0.0) with confidence 0.0, and note it in data quality metrics.

## Scalability Considerations

| Concern | 10 Holdings | 100 Holdings | 1000 Holdings |
|---------|-------------|--------------|---------------|
| Finnhub API calls | 10 calls (<1s) | 100 calls (~2s, within 60/min) | 1000 calls (~17 batches of 60, ~17min) |
| FRED API calls | 1 call (session-level) | 1 call | 1 call |
| VADER scoring | ~200 articles (<1s) | ~2000 articles (~2s) | ~20000 articles (~20s) |
| Cache effectiveness | Low (fresh each run) | Medium (some tickers repeat) | High (many tickers cached between runs) |
| Rate limit mitigation | None needed | aiolimiter for Finnhub | Batch with delay + aiolimiter + cache |

For 1000+ holdings, implement batch prefetching for Finnhub news (like existing `batch_data_prefetcher.py`) with async semaphore limiting to 50 concurrent requests, respecting the 60/min cap.

## Pydantic Schema Extensions

New schemas to add in `schemas/`:

```python
# schemas/news.py
class NewsArticle(BaseModel):
    ticker: str
    title: str
    summary: str = ""
    url: str
    source: str  # "finnhub", "gnews", "rss"
    published_at: datetime
    sentiment_score: float | None = None
    source_reliability: float = Field(ge=0.0, le=1.0, default=0.5)


class NewsSentimentResult(BaseModel):
    ticker: str
    overall_score: float = Field(ge=-1.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    article_count: int = Field(ge=0)
    positive_count: int = Field(ge=0)
    negative_count: int = Field(ge=0)
    neutral_count: int = Field(ge=0)
    articles: list[NewsArticle] = Field(default_factory=list)
    sources_used: list[str] = Field(default_factory=list)
    analysis_timestamp: datetime


# schemas/macro.py
class MacroSnapshot(BaseModel):
    """Point-in-time macroeconomic data from FRED."""

    gdp_growth_rate: float | None = None  # FRED: A191RL1Q225SBEA
    unemployment_rate: float | None = None  # FRED: UNRATE
    cpi_yoy_change: float | None = None  # FRED: CPIAUCSL
    fed_funds_rate: float | None = None  # FRED: FEDFUNDS
    treasury_10y_yield: float | None = None  # FRED: GS10
    treasury_2y_yield: float | None = None  # FRED: GS2
    yield_curve_spread: float | None = None  # 10Y - 2Y
    vix_level: float | None = None  # FRED: VIXCLS
    fear_greed_index: int | None = None  # CNN Fear & Greed
    snapshot_timestamp: datetime
    data_source: str = "FRED"
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)
```

## Sources

- Existing codebase patterns: `data/data_source_orchestrator.py`, `data/adapters/base_adapter.py`, `scoring/deep_analysis_scorer.py`, `config/features/definitions.py`, `orchestrators/extraction/market_context.py`
- [Finnhub API](https://finnhub.io/docs/api)
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/)
- [VADER (GitHub)](https://github.com/cjhutto/vaderSentiment)
