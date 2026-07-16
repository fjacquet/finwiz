# Domain Pitfalls

> **Stale as of 2026-07**: The local `rate_limiter_config.py`, `APIProvider` enum, and `aiolimiter` extension points this document references were removed in the 2026-07 tool centralization (waves 1-4); rate limiting now lives in `crewai-custom-tools`' bounded registry (`crewai_custom_tools.core.rate_limiter`). Refresh this document before using it for v5 planning.

**Domain:** Adding news sentiment, macroeconomic indicators, and data intelligence to existing Python financial analysis platform (FinWiz)
**Researched:** 2026-02-08
**Overall Confidence:** HIGH (verified against existing codebase patterns + multiple external sources)

---

## Critical Pitfalls

Mistakes that cause rewrites, incorrect scoring, or cascading system failures.

---

### Pitfall 1: Weight Dilution -- Blindly Redistributing Composite Weights

**What goes wrong:** Adding sentiment (e.g., 10%) and macro (e.g., 10%) to the existing 40/30/30 fundamental/technical/risk composite forces all existing weights to shrink. If done naively -- say reducing each proportionally to 32/24/24/10/10 -- every existing grade shifts. An asset that was A- (0.86) might drop to B+ (0.80) purely because of weight redistribution, not because anything about the asset changed. Users see unexplained grade shifts across the entire portfolio.

**Why it happens:** Developers treat weight addition as a simple arithmetic rebalance without understanding that every existing test, threshold, and grade boundary was calibrated to the 40/30/30 split. The `ScoringThresholds` dataclass in `scoring/thresholds.py` has 50+ threshold constants tuned to the current weight distribution.

**Consequences:**
- Every existing unit test involving composite scores breaks.
- Grade distributions shift (more Bs, fewer As) causing user confusion.
- Recommendation thresholds (BUY >= 0.85, SELL < 0.65) no longer align with the new score distribution.
- The adaptive weight logic in `_compute_weighted_score()` (quality companies get 50/25/25) becomes inconsistent with the new factor count.

**Prevention:**
1. Add sentiment and macro as **additive adjustment factors** on top of the existing 40/30/30, not as replacement weights. For example: `final_score = composite_40_30_30 * (1 + sentiment_adjustment + macro_adjustment)` where adjustments are clamped to +/-0.05.
2. Alternatively, implement a **two-tier scoring system**: the existing composite produces a base score, then a separate "intelligence overlay" adjusts it. This preserves all existing test baselines.
3. If weights must change, run a full **recalibration pass**: recompute all 4500+ test expectations, regenerate grade distributions from historical data, and validate that the new distribution matches the old one within tolerance.

**Detection:** Before merging weight changes, run the full test suite and check that the grade distribution histogram (A/B/C/D/F counts) for a reference portfolio stays within 5% of the previous distribution.

**Phase:** Phase 1 (Scoring Architecture) -- must be designed correctly before any data providers are integrated.

---

### Pitfall 2: Free News API Budget Exhaustion in Production

**What goes wrong:** Free-tier news APIs have aggressively low limits that look sufficient in development (testing 2-3 tickers) but fail catastrophically in production (66+ holdings). A portfolio scan exhausts the daily budget within minutes, and subsequent tickers get empty sentiment data -- which silently degrades scores rather than failing loudly.

**Why it happens:** Free tier limits are per-day, not per-minute:
- **NewsAPI.org**: 100 requests/day (developer plan, cannot be used in production per ToS)
- **Finnhub**: 60 calls/minute (generous per-minute, but news sentiment endpoint has separate undocumented daily caps on free tier)
- **Marketaux**: 100 requests/day on free plan
- **NewsData.io**: 200 credits/day on free plan

For a 66-holding portfolio where each holding needs ~3 API calls (company news, sector news, general market), that is 198 calls -- already exceeding NewsAPI and Marketaux daily limits in a single run.

**Consequences:**
- Silent data gaps: Holdings analyzed later in the run get no sentiment data.
- Score inconsistency: Early holdings get sentiment adjustment, later holdings do not, creating systematic bias toward holdings analyzed first.
- The existing `GracefulDegradationManager` in `infrastructure/resilience/degradation.py` will fall back to default data, but default sentiment data (neutral/0.0) is not the same as "no data available" -- it masks the absence.

**Prevention:**
1. **Budget-aware scheduling**: Before a run, calculate `tickers * calls_per_ticker` and compare against daily budget. If over budget, switch to a tiered strategy: full sentiment for top holdings by portfolio weight, cached/stale sentiment for the rest.
2. **Explicit "no data" vs "neutral"**: Never use 0.0 or "neutral" as a fallback for missing sentiment. Use `None` or a sentinel value, and handle it in the scorer by skipping the sentiment adjustment entirely for that holding.
3. **Add news API providers to `APIProvider` enum and `DEFAULT_RATE_LIMITS`**: Extend `rate_limiter_config.py` with `FINNHUB_NEWS`, `NEWSAPI`, `MARKETAUX` entries with accurate daily limits (not just per-minute).
4. **Cache aggressively**: News sentiment for a ticker should be cached for 4-6 hours minimum. Same news articles do not change sentiment within that window.

**Detection:** Log a WARNING when > 50% of daily API budget is consumed. Log an ERROR and halt sentiment collection when > 90% is consumed, falling back to cache-only mode.

**Phase:** Phase 2 (Data Provider Integration) -- must be solved before sentiment scoring is operational.

---

### Pitfall 3: Sentiment Scoring Garbage-In-Garbage-Out

**What goes wrong:** Using a general-purpose sentiment analyzer (VADER, TextBlob) on financial news produces systematically wrong scores. Financial language is domain-specific: "company beats expectations" is positive, "Fed cuts rates" is contextually positive or negative depending on the asset class, "hostile takeover bid" is positive for target shareholders but negative for the acquirer. General NLP tools miss all of this.

**Why it happens:** VADER was trained on social media text and product reviews. Its lexicon does not understand financial concepts. Research shows VADER achieves roughly 65-70% accuracy on financial text compared to FinBERT's 91%+ accuracy on the SEntFiN dataset.

**Consequences:**
- Sentiment scores are noise, not signal. Adding noise to a deterministic scoring engine actively degrades prediction quality.
- Contradicts the project's AI Minimalism principle: "Python for deterministic tasks, AI only for qualitative reasoning." If sentiment scoring is not deterministic and not accurate, it violates the architectural principle.
- False confidence: the system reports sentiment as a scored factor, but the factor is unreliable.

**Prevention:**
1. **Use FinBERT (ProsusAI/finBERT) as the primary sentiment model.** It is domain-trained on financial text and achieves 91%+ accuracy. It runs locally in Python, costs $0, and produces deterministic output for the same input.
2. **Do NOT use VADER or TextBlob for financial sentiment.** If FinBERT is too heavy (requires ~500MB model), use a distilled FinBERT or the `nlptown/bert-base-multilingual-uncased-sentiment` model which is smaller.
3. **Validate with a known-label test set**: Create a fixture of 50-100 financial headlines with manually labeled sentiment. Run every sentiment model change against this fixture. If accuracy drops below 85%, reject the change.
4. **Asset-class-aware sentiment**: "Fed raises rates" is negative for growth stocks, positive for bank stocks, neutral for gold ETFs. Build a mapping of macro-event types to per-asset-class sentiment adjustments.

**Detection:** Track sentiment accuracy against a labeled test set in CI. Add a `make check-sentiment-accuracy` target.

**Phase:** Phase 2 (Sentiment Engine) -- FinBERT selection is a day-1 decision that affects the entire pipeline.

---

### Pitfall 4: Macroeconomic Data Staleness and Look-Ahead Bias

**What goes wrong:** Macroeconomic indicators (GDP, CPI, unemployment) are released with significant lag and revised multiple times. GDP advance estimate arrives ~30 days after quarter end, second estimate ~60 days, "final" ~90 days. CPI is monthly with ~2 week lag. Using the latest available value as if it represents current conditions introduces look-ahead bias in backtesting and stale-data artifacts in live scoring.

**Why it happens:** Developers fetch the "latest" FRED value and treat it as current truth. But "latest" GDP might be Q3 2025 data when it is February 2026 -- a 5-month lag. Additionally, GDP revisions average +0.45 percentage points from advance to final, meaning the number used during initial scoring will differ from the eventual "true" value.

**Consequences:**
- **Stale signals**: A macro score computed in February using Q3 GDP data is 5 months old. If Q4 was a recession quarter, the macro score is falsely optimistic.
- **Look-ahead bias in backtesting**: If you backtest using final-revised GDP values that were not available at the time, your historical sentiment/macro scores are unrealistically accurate.
- **Revision whiplash**: GDP gets revised from 2.1% to 2.6% to 2.3% across three releases. Each revision changes the macro score for every holding in the portfolio, creating phantom recommendation changes.

**Prevention:**
1. **Publish a data freshness metadata object** for every macro indicator: `{indicator: "GDP", value: 2.3, reference_period: "Q3-2025", release_date: "2025-12-22", next_release: "2026-01-30", vintage: "advance"}`. Include this in the scorer so it can weight the indicator by its freshness.
2. **Freshness-weighted scoring**: A macro indicator released 1 week ago gets full weight. One released 3 months ago gets 50% weight. One released 6+ months ago gets 10% weight. This naturally dampens stale data's influence.
3. **Use leading indicators, not lagging ones**: Instead of GDP (lagging, revised), use PMI (monthly, not revised), initial jobless claims (weekly, not revised), yield curve slope (daily, real-time). These are more actionable for investment scoring.
4. **Never backtest with revised data**: Use FRED's ALFRED (Archival FRED) API to get point-in-time vintage data. The `fredapi` Python library supports `get_series_as_of_date()` for this purpose.

**Detection:** Add a `macro_freshness_score` field (0.0-1.0) to each macro indicator used. Alert when average freshness across indicators drops below 0.5.

**Phase:** Phase 3 (Macro Indicators) -- must be architected correctly from the start to avoid look-ahead bias baked into the scoring model.

---

### Pitfall 5: Pipeline Latency Explosion from Sequential API Calls

**What goes wrong:** Adding 3 new data sources (news API, sentiment model, macro API) to the existing per-holding analysis pipeline adds ~2-5 seconds per source per holding. For 66 holdings sequentially, that is 66 * 10s = 11 extra minutes. The existing pipeline already takes 20-40 minutes with batch prefetch. Adding sentiment and macro without proper async batching pushes it past 1 hour.

**Why it happens:** The existing `BatchDataPreFetcher` batches yfinance calls efficiently (ONE call for all tickers). But news APIs typically require per-ticker queries (no batch endpoint). Developers add the new API calls inside the per-holding loop in `deep_analysis_pipeline.py` without extending the batch prefetch pattern.

**Consequences:**
- Total analysis time exceeds user patience threshold.
- Rate limiters introduce sequential waits: Finnhub at 60/min = 1 sec/ticker, Marketaux at 100/day = hard stop after ~33 tickers.
- The existing `memory_manager` (Requirement 17.70) may flag memory pressure if news article text is buffered for all tickers simultaneously.

**Prevention:**
1. **Extend `BatchDataPreFetcher`** with a `_fetch_news_sentiment_batch()` method that pre-fetches all news and computes sentiment before the per-holding loop. Cache results in the session cache alongside yfinance data.
2. **Async parallel fetching**: Use `aiohttp` (already in the project) to fetch news for multiple tickers concurrently, respecting rate limits via the existing `AsyncLimiter` from `aiolimiter`.
3. **Decouple news fetching from sentiment computation**: Fetch all raw news in batch (network-bound), then compute FinBERT sentiment scores in batch on GPU/CPU (compute-bound). These are different bottlenecks and should be parallelized differently.
4. **FRED macro data needs ONE call**: Unlike per-ticker news, macro indicators are market-wide. Fetch all macro series once per run, not per holding. Store in a shared `MacroContext` object.

**Detection:** Add timing metrics per pipeline step. Alert if any new step adds > 5 seconds per holding on average.

**Phase:** Phase 2 (Data Provider Integration) -- must extend existing batch patterns, not create parallel ones.

---

## Moderate Pitfalls

Mistakes that cause significant rework or quality issues but are recoverable.

---

### Pitfall 6: Conflating "No News" with "Neutral Sentiment"

**What goes wrong:** When a ticker has no news articles (common for small-cap stocks, obscure ETFs, or less-covered crypto), the system assigns sentiment = 0.0 (neutral). This is semantically wrong. "No news" means "unknown sentiment" -- it should not influence the composite score at all. Treating it as neutral artificially stabilizes scores for holdings that are actually data-poor.

**Prevention:**
1. Return `sentiment_score: None` (not 0.0) when no articles are found.
2. In the scorer, skip the sentiment adjustment when `sentiment_score is None`. The existing `DataQualityMetrics` pattern (used in `_initialize_tracking()`) should track sentiment data availability.
3. Log a data quality warning: "No news articles found for {ticker} -- sentiment factor excluded from composite."
4. Report the data gap in the final HTML report so users know which holdings lack sentiment data.

**Phase:** Phase 2 (Sentiment Engine) -- design-time decision.

---

### Pitfall 7: Macro Indicators Treated Uniformly Across Asset Classes

**What goes wrong:** A rising interest rate is negative for growth stocks (higher discount rate), positive for bank stocks (wider net interest margin), irrelevant for gold ETFs, and complex for crypto. Applying the same macro adjustment to all asset classes creates false signals.

**Prevention:**
1. Build an **asset-class-to-macro sensitivity matrix**: for each macro indicator (interest rates, inflation, GDP growth, unemployment), define a per-asset-class coefficient. The existing `ScoringThresholds` dataclass pattern (separate thresholds per asset class) is the right model.
2. For crypto specifically, macro indicators have minimal direct correlation. Use crypto-specific indicators instead: Bitcoin dominance, total crypto market cap, DeFi TVL.
3. Leverage the existing **strategy pattern** in `scoring/asset_analyzers/` (StockAnalyzer, ETFAnalyzer, CryptoAnalyzer). Each analyzer should have its own `apply_macro_adjustment()` method.

**Phase:** Phase 3 (Macro Indicators) -- architecture decision.

---

### Pitfall 8: FinBERT Model Loading Destroys Startup Time and Memory

**What goes wrong:** FinBERT (ProsusAI/finBERT) is a ~500MB model. Loading it on every pipeline invocation adds 10-30 seconds of startup time and consumes 1-2GB RAM. In a serverless or CLI context, this is unacceptable.

**Prevention:**
1. **Lazy-load the model once per session**, not per holding. Store in a module-level singleton (matching the pattern of `_rate_limiter` and `_degradation_manager` in `infrastructure/resilience/`).
2. **Use ONNX-optimized FinBERT** for inference: 3-5x faster, ~50% memory reduction.
3. **Gate behind feature flag**: Add `FF_SENTIMENT_ANALYSIS=true/false` to `config/features/definitions.py`. When disabled, skip model loading entirely. This matches the existing `FF_NEWCOMER_DISCOVERY` pattern.
4. **Consider a lightweight alternative**: `cardiffnlp/twitter-roberta-base-sentiment-latest` (fine-tuned on financial tweets) is smaller (~300MB) and may be sufficient for headline-level sentiment.

**Detection:** Monitor startup time in CI. Alert if cold start exceeds 15 seconds.

**Phase:** Phase 2 (Sentiment Engine) -- must be solved during initial model integration.

---

### Pitfall 9: Sentiment Temporal Decay Ignored

**What goes wrong:** A negative news article from 2 weeks ago is weighted the same as one from 2 hours ago. Old sentiment signals decay in relevance. If the system fetches "last 30 days of news" and averages sentiment equally, a stale scandal will drag down scores long after the market has priced it in.

**Prevention:**
1. Apply **exponential time decay** to sentiment scores: `weighted_sentiment = sentiment * exp(-lambda * hours_since_publication)`. A reasonable lambda gives 50% weight at 48 hours, 10% at 1 week.
2. Use a **recency-weighted average**: compute separate scores for "last 24h", "last 7d", "last 30d" and weight them 50/30/20.
3. The existing `CacheTTLRegistry` in `infrastructure/caching/ttl_config.py` should add a `NEWS_SENTIMENT` data type with a 4-6 hour TTL to prevent truly stale sentiment from persisting.

**Phase:** Phase 2 (Sentiment Scoring Algorithm).

---

### Pitfall 10: FRED API Key Sharing Causes Rate Limit Collision

**What goes wrong:** FRED's free tier allows 120 requests per minute per API key. If the same key is used for both batch prefetch and on-demand macro queries, the two call paths compete for the same rate limit budget, causing unexpected 429 errors in the macro pathway when a batch prefetch is running.

**Prevention:**
1. **Centralize FRED calls**: All FRED data should be fetched in the batch prefetch phase, not on-demand during scoring. Macro data changes slowly (daily at most), so fetching once per run is sufficient.
2. **Add `FRED` to the `APIProvider` enum** in `rate_limiter_config.py` with `requests_per_minute=120, requests_per_day=10000` (FRED's actual limits).
3. **Register FRED in `GracefulDegradationManager`** with appropriate fallback: if FRED is down, use the last cached macro snapshot (macro data is valid for hours/days, unlike price data).

**Phase:** Phase 3 (Macro Data Provider) -- infrastructure registration.

---

### Pitfall 11: NewsAPI.org Terms of Service Violation

**What goes wrong:** NewsAPI.org's free "Developer" plan explicitly states: "The Developer plan may be used for development and testing in a development environment only." Using it in production (even for a personal project that runs scheduled analysis) violates their ToS, risking sudden API key revocation.

**Prevention:**
1. **Do not use NewsAPI.org for production**: Use Finnhub (free tier is production-legal, 60 calls/min) or Marketaux (free tier allows production use with attribution).
2. If NewsAPI.org is used for development/testing, ensure the fallback chain switches to a production-legal provider when `NODE_ENV=production` or equivalent.
3. Document the provider selection rationale so future developers do not accidentally promote NewsAPI.org to production.

**Phase:** Phase 2 (Data Provider Selection) -- day-1 vendor decision.

---

## Minor Pitfalls

Issues that cause annoyance, technical debt, or minor quality degradation.

---

### Pitfall 12: Sentiment Score Scale Mismatch

**What goes wrong:** FinBERT outputs probabilities in [0, 1] for positive/negative/neutral. VADER outputs a compound score in [-1, 1]. The existing composite score operates on [0, 1]. Mixing scales without normalization produces nonsensical composite scores.

**Prevention:**
1. Define a **canonical sentiment scale** for the project: 0.0 (most negative) to 1.0 (most positive), matching the existing scorer convention.
2. Every sentiment provider adapter must normalize to this scale before the result enters the scoring pipeline.
3. Add a schema validator (Pydantic model) for sentiment results: `SentimentResult(score: float = Field(ge=0.0, le=1.0))`.

**Phase:** Phase 2 (Sentiment Schema Design).

---

### Pitfall 13: Over-Fetching News Articles Burns API Credits and Memory

**What goes wrong:** Fetching 100 articles per ticker to "be thorough" when only the top 5-10 headlines matter for sentiment. Each extra article costs an API credit and adds text to process through FinBERT. For 66 tickers * 100 articles = 6,600 articles through a transformer model -- unnecessary and slow.

**Prevention:**
1. Fetch **top 10 articles per ticker** by relevance/recency.
2. For general market sentiment, fetch top 20 market-wide articles (not per ticker).
3. Aggregate sentiment at the headline level first (fast, lightweight). Only use full article text for tickers where headline sentiment is ambiguous (mixed positive/negative headlines).

**Phase:** Phase 2 (Data Provider Integration).

---

### Pitfall 14: Circular Dependency Between Sentiment and AI Crews

**What goes wrong:** The existing architecture has AI crews generating qualitative insights in `generate_qualitative()`. If sentiment data is fed to both the deterministic scorer AND the AI crew, the AI might echo the sentiment score in its qualitative output, creating a circular amplification effect. A negative sentiment score leads the AI to write negative qualitative analysis, which reinforces the negative signal.

**Prevention:**
1. **Sentiment goes to the deterministic scorer only**, not to the AI crew. The AI crew should analyze fundamentals and technicals qualitatively. Sentiment is already captured quantitatively.
2. This aligns with the existing principle: "When Python and AI disagree, Python wins." Keep sentiment in the Python-controlled deterministic path.
3. If the AI crew needs context about market mood, provide it as read-only context ("market sentiment is currently bearish") without letting it affect the quantitative score.

**Phase:** Phase 4 (Report Enrichment / AI Integration) -- architectural boundary.

---

### Pitfall 15: Testing Sentiment and Macro with Live APIs in CI

**What goes wrong:** Tests that call Finnhub, FRED, or FinBERT model inference in CI are slow (model loading), flaky (API rate limits), and expensive (API credits). They break CI on every API hiccup.

**Prevention:**
1. **All sentiment/macro tests must use fixtures**, following the existing pattern in `tests/conftest.py` (Faker-generated data).
2. Create `tests/fixtures/sentiment/` with pre-computed FinBERT results for known headlines.
3. Create `tests/fixtures/macro/` with FRED snapshots for known dates.
4. Integration tests (marked `@pytest.mark.integration`) can call real APIs but are excluded from default `make test`.
5. Mock FinBERT model inference in unit tests using the existing `mocker.patch()` pattern (not `unittest.mock` -- banned per project rules).

**Phase:** Phase 2 (Testing Infrastructure) -- must be set up before any sentiment/macro code lands.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation | Severity |
|-------------|---------------|------------|----------|
| Scoring Architecture | Weight dilution destroying existing grades (Pitfall 1) | Additive adjustment model, not weight redistribution | CRITICAL |
| Data Provider Integration | Free API budget exhaustion (Pitfall 2) | Budget-aware scheduling, aggressive caching | CRITICAL |
| Sentiment Engine | VADER/TextBlob inaccuracy on financial text (Pitfall 3) | Use FinBERT from day 1 | CRITICAL |
| Macro Indicators | Data staleness and look-ahead bias (Pitfall 4) | Freshness-weighted scoring, leading indicators, ALFRED for backtesting | CRITICAL |
| Pipeline Performance | Latency explosion from sequential calls (Pitfall 5) | Extend BatchDataPreFetcher pattern | CRITICAL |
| Sentiment Engine | "No news" conflated with "neutral" (Pitfall 6) | Explicit None handling | MODERATE |
| Macro Indicators | Uniform macro sensitivity across asset classes (Pitfall 7) | Per-asset-class sensitivity matrix | MODERATE |
| Sentiment Engine | FinBERT model loading overhead (Pitfall 8) | Lazy singleton, ONNX, feature flag | MODERATE |
| Sentiment Scoring | Temporal decay ignored (Pitfall 9) | Exponential decay weighting | MODERATE |
| Macro Data Provider | FRED rate limit collision (Pitfall 10) | Centralized fetch in batch prefetch | MODERATE |
| Data Provider Selection | NewsAPI.org ToS violation (Pitfall 11) | Use Finnhub or Marketaux for production | MODERATE |
| Sentiment Schema | Score scale mismatch between providers (Pitfall 12) | Canonical [0,1] scale, Pydantic validation | MINOR |
| Data Provider Integration | Over-fetching articles (Pitfall 13) | Top 10 articles per ticker | MINOR |
| AI Integration | Circular sentiment amplification via AI crews (Pitfall 14) | Sentiment to scorer only, not to AI crews | MINOR |
| Testing | Live API calls in CI (Pitfall 15) | Fixtures and mock patterns | MINOR |

---

## Codebase-Specific Integration Risks

These are risks specific to FinWiz's existing architecture:

| Existing Component | Risk When Adding Sentiment/Macro | Mitigation |
|---|---|---|
| `DeepAnalysisScorer._compute_weighted_score()` | Changing weight sum from 1.0 breaks adaptive 50/25/25 logic | Keep weights at 1.0, use adjustment overlay |
| `ScoringThresholds` (50+ constants) | New factors need new thresholds, exponential configuration growth | New `SentimentThresholds` and `MacroThresholds` dataclasses, composed into `ScoringThresholds` |
| `BatchDataPreFetcher.prefetch_all_data()` | Adding news API calls inside yfinance batch method breaks batch efficiency | New `_fetch_news_batch()` and `_fetch_macro_batch()` methods as separate pipeline steps |
| `CacheTTLRegistry` (6 data types) | No existing category for news/sentiment or macro data | Add `NEWS_SENTIMENT` and `MACRO_DATA` to `CacheDataType` enum |
| `APIProvider` enum (10 providers) | News/macro providers missing from rate limiter | Add FINNHUB, MARKETAUX, FRED to enum and `DEFAULT_RATE_LIMITS` |
| `GracefulDegradationManager` (6 services) | No fallback defined for news/sentiment/macro failures | Add service configs with appropriate cache-based fallbacks |
| `AnalysisContext` (immutable dataclass) | Needs sentiment and macro data passed through pipeline | Extend context or create `SentimentContext` / `MacroContext` sidecar objects |
| Feature flags (`definitions.py`) | No flags for sentiment/macro features | Add `FF_SENTIMENT_ANALYSIS`, `FF_MACRO_INDICATORS` with circuit breaker strategy |
| `DataQualityMetrics` | Does not track sentiment/macro data presence | Extend expected fields list per asset class |

---

## Sources

- [Finnhub API Rate Limits](https://finnhub.io/docs/api/rate-limit) -- 60 calls/minute free tier, 30 calls/second hard cap
- [NewsAPI.org Pricing and ToS](https://newsapi.org/pricing) -- 100 requests/day, dev-only for free tier
- [FinBERT GitHub (ProsusAI)](https://github.com/ProsusAI/finBERT) -- Financial sentiment model, 91%+ accuracy
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/) -- 120 requests/minute, vintage data support via ALFRED
- [Richmond Fed: How Data Revisions and Uncertainty Affect Monetary Policy](https://www.richmondfed.org/publications/research/economic_brief/2026/eb_26-01) -- GDP revision patterns
- [St. Louis Fed: Data Revisions with FRED](https://www.stlouisfed.org/publications/page-one-economics/2022/08/01/data-revisions-with-fred) -- ALFRED vintage data
- [fredapi PyPI](https://pypi.org/project/fredapi/) -- Python client with `get_series_as_of_date()` for vintage data
- [ACM Computing Surveys: Financial Sentiment Analysis Techniques](https://dl.acm.org/doi/10.1145/3649451) -- Comprehensive survey of FSA pitfalls
- [Label Your Data: Sentiment Analysis Methods and Challenges 2026](https://labelyourdata.com/articles/natural-language-processing/sentiment-analysis) -- VADER vs FinBERT accuracy comparison
- [DZone: Improving Sentiment Score Accuracy with FinBERT](https://dzone.com/articles/improving-sentiment-score-accuracy-with-finbert-an) -- FinBERT vs VADER comparison data
- [Finnhub API Issue #122](https://github.com/finnhubio/Finnhub-API/issues/122) -- Rate limit problems on free plan
- [Best Financial Data APIs 2026](https://www.nb-data.com/p/best-financial-data-apis-in-2026) -- API reliability comparison
- [Harvard: Macro-Finance Model with Sentiment](https://scholar.harvard.edu/files/maxted/files/macrofinancesentimentmain_nov13.pdf) -- Sentiment as bridge between macro and markets
