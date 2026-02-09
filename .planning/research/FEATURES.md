# Feature Landscape

**Domain:** News sentiment, macroeconomic indicators, data intelligence, and smart composite scoring for financial portfolio analysis
**Researched:** 2026-02-08
**Mode:** Ecosystem (subsequent milestone -- extending existing FinWiz platform)

## Table Stakes

Features users expect from a "market-context-aware" portfolio analyzer. Missing any of these makes the sentiment/macro upgrade feel incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Per-ticker news aggregation** | Every modern screener (Finnhub, EODHD, Bloomberg) shows recent news per holding. Analysts need to see what is being said about their holdings. | Low | Finnhub `company_news` + gnews + RSS feeds. Existing `SentimentAnalyzer` already fetches from Alpha Vantage + Yahoo Finance. Extend with new sources via `NewsOrchestrator` pattern. |
| **Headline sentiment scores** | Every modern platform shows sentiment polarity. Users expect a numeric score, not just "positive/negative" labels. | Low | VADER `SentimentIntensityAnalyzer` replaces current keyword matching in `_calculate_keyword_sentiment()`. Drop-in upgrade path. Deterministic, <1ms per headline. |
| **Aggregate sentiment score per holding** | Single number to feed into composite scorer. Without this, sentiment data is informational-only and does not affect investment decisions. | Low | Weighted average of individual article scores. Existing `SentimentAnalysisResult.overall_sentiment_score` pattern already in place. |
| **Macro environment summary** | GDP growth, CPI/inflation, unemployment rate, Fed funds rate -- the "big 4" that every investor expects when a platform claims macro awareness. | Medium | FRED API provides all four. The existing `MacroIndicators` schema and `MarketContextExtractor` already define the data shape with `_extract_gdp_growth()` and `_extract_unemployment_rate()` -- currently return `None` with TODOs. FRED fills these directly. |
| **VIX / volatility index display** | VIX is the most universally recognized market fear gauge. If you claim "market context," VIX must be visible. | Low | Already available via `yfinance` (`^VIX`) or FRED (`VIXCLS` series). The existing `assess_market_regime()` in `scoring_criteria.py` uses VIX but with a hardcoded default of 20.0. Replace with real data. |
| **Fear and Greed Index display** | Common market-wide sentiment barometer. CNN Fear and Greed is the most recognized one-number market mood indicator. | Low | Single API call via `fear-and-greed` library. Returns 0-100 value. Display in report header or macro dashboard section. |
| **News source attribution** | Users need to trust the data sources. Showing "based on 15 articles from 3 sources" builds confidence. Showing just a number with no source is suspicious. | Low | Track which source provided each article (Finnhub, RSS, gnews). Follow existing `DataLineage` pattern in `schemas/data_lineage.py`. |
| **Sentiment confidence / data quality flag** | When sentiment is based on only 2 articles vs 50, users need to know. Low-article-count sentiment is unreliable. | Low | Already partially in `SentimentAnalysisResult.confidence_level`. Extend existing confidence calculation to account for article count, source diversity, and recency. Surface prominently in report alongside the score. |

## Differentiators

Features that set FinWiz apart. Not expected, but create high value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Smart composite scoring with sentiment + macro** | Most tools score fundamentals/technicals OR sentiment, not both in one composite. Combining them in a single weighted score is the core value proposition of this milestone. | Medium | Integrate VADER sentiment and FRED macro data into existing 40/30/30 scorer. New weight allocation: 35% fundamental + 25% technical + 25% risk + 15% sentiment. Or use macro regime to dynamically adjust the existing weights (bull = more technical weight, bear = more risk weight). |
| **Yield curve analysis** | The 10Y-2Y Treasury spread is the single most reliable recession predictor. VIX + yield curve slope together outperform either alone for regime detection (per academic research: ScienceDirect 2023). | Medium | FRED series: `DGS10` (10-year), `DGS2` (2-year). Compute spread. Classify: inverted (<0), flat (0-0.5), normal (>0.5), steep (>1.5). |
| **Market regime detection with real data** | Current `assess_market_regime()` uses hardcoded VIX default of 20.0 and hardcoded inflation of 3.0. Real FRED data enables actual regime classification. Already sketched in `get_dynamic_criteria()` but not connected to `DeepAnalysisScorer`. | Medium | Replace `_estimate_interest_rate()` returning 5.0/4.5/5.5 with actual Fed Funds Rate from FRED (`FEDFUNDS` series). Wire VIX + yield curve into `assess_market_regime()`. Feed regime into scorer's adaptive weights. |
| **Multi-source news deduplication** | Avoids counting the same story from 3 sources as 3x the signal. Without deduplication, aggregate sentiment is biased toward widely-syndicated stories. | Medium | Existing `_is_duplicate_article()` in enhanced sentiment tool uses Jaccard similarity. Extend to cross-source dedup across Finnhub + gnews + RSS. |
| **Sentiment trend direction** | Not just "what is sentiment now" but "is it improving or deteriorating?" A 7/14/30-day trend line is far more useful than a snapshot. | Medium | Requires storing or fetching historical sentiment data points and computing a simple moving average or slope. Can use Alpha Vantage's `time_from` parameter for historical ranges. |
| **Macro dashboard in report** | A dedicated "Market Environment" section in the HTML report showing VIX, yield curve, GDP trend, inflation, unemployment, Fear and Greed -- all in one visual panel with traffic-light indicators. | Medium | Extends `ReportSectionBuilder`. Needs HTML/CSS template work. Color-coded gauges (green/yellow/red). `ReportSectionBuilder` already supports adding arbitrary sections and has `EMOJI_MAP` for visual cues. |
| **Economic calendar awareness** | Flag upcoming FOMC meetings, jobs reports, CPI releases. These events cause volatility and should be noted in analysis. | Medium | Finnhub free tier includes `economic_calendar` endpoint. Display as "upcoming events" in report. Forward-looking context that no current source provides. |
| **Earnings surprise integration** | Earnings beats/misses are high-signal sentiment events. A stock that just beat estimates by 20% is materially different from one that missed. | Medium | Finnhub provides `earnings_surprises` endpoint on free tier. Quantitative signal, not AI. Feeds directly into fundamental score modifier. |
| **Source reliability weighting** | Not all news sources are equal signal quality. Reuters/Bloomberg carry more weight than random blogs. | Low | Existing `get_source_reliability_score()` has tier system. Extend to weight VADER scores by source reliability. |
| **Sentiment-adjusted risk scores** | High negative sentiment + high volatility = amplified risk signal. Sentiment should modify risk assessment, not replace it. | Medium | Modify `RiskScorer` to incorporate sentiment momentum as a risk factor. Additive to existing volatility/drawdown/beta. |

## Anti-Features

Features to explicitly NOT build. These are tempting but counterproductive for FinWiz.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time sentiment streaming** | FinWiz runs batch analysis (`crewai flow kickoff`), not a trading terminal. Real-time streaming adds WebSocket complexity, state management, and infrastructure cost for zero benefit in a batch workflow. Session runs take 1-5 minutes; real-time adds no value. | Fetch sentiment at analysis time. Cache for the session duration (1-4 hour TTL). Freshness within hours is sufficient for portfolio analysis. |
| **AI-generated sentiment summaries per article** | Violates AI Minimalism. Using GPT/Claude to classify sentiment per article costs $0.01-0.05 per article. With 50 articles per holding and 20 holdings, that is $10-50 per analysis run. Non-deterministic. Slow. | Use VADER for deterministic scores ($0, <1ms/headline). Let the existing AI crews provide qualitative context in their narrative reports. |
| **Social media scraping (Twitter/Reddit raw)** | X/Twitter API is $100+/month. Reddit API changes frequently. Raw social data has terrible signal-to-noise ratio. Bot contamination is severe. Scraping is legally questionable. | Use pre-aggregated sentiment from providers (Alpha Vantage, Finnhub, Perplexity Sonar) that already filter social signals. Stick to financial news sources with editorial standards. |
| **Custom sentiment model training** | Training a proprietary model requires labeled financial data (thousands of examples), GPU infrastructure, and ongoing maintenance. | Use VADER (validated lexicon+rules engine). Consider FinBERT (`ProsusAI/finbert`, 79% accuracy, pre-trained) as a future upgrade behind a feature flag if VADER proves insufficient on financial text. |
| **Automated trading signals from sentiment** | Academic research consistently shows sentiment alone has R-squared of ~0.01 for next-day price prediction. Generating BUY/SELL signals from sentiment alone is irresponsible. | Sentiment is a *modifier* on existing scores, not a signal generator. It adjusts confidence and risk assessment, not direction. Keep the "Python wins" philosophy. |
| **Macro forecasting / economic predictions** | Predicting GDP or inflation is out of scope. Even central banks get it wrong. Building ML models to forecast macro is unreliable. | Display *current* macro data and *recent trends*. Let the user interpret. Show leading indicators (yield curve, VIX) without making predictions. |
| **Crypto-specific on-chain sentiment** | On-chain metrics (whale transactions, exchange flows) require specialized paid APIs (LunarCrush, Santiment). | CoinMarketCap integration already exists for crypto basics. Focus on news sentiment which applies to all asset classes equally. |
| **Full NLP pipeline (NER, topic modeling)** | Over-engineering for the scoring use case. transformers/spaCy add 500MB+ dependencies for marginal improvement over VADER + keyword extraction. | VADER for scores, existing `_extract_trending_topics()` for topics. Save full NLP for future milestone if demand warrants. |

## Feature Dependencies

```
FRED API adapter ---------> MacroIndicators (fills real data: GDP, CPI, unemployment, rates)
MacroIndicators ----------> MarketContextExtractor (replaces hardcoded estimates)
MarketContextExtractor ---> assess_market_regime() (VIX + yield curve -> regime)
assess_market_regime() ---> Composite Scorer (macro-adjusted weights)

Finnhub adapter ----------> NewsOrchestrator (primary news source)
gnews adapter ------------> NewsOrchestrator (secondary news source)
feedparser RSS adapter ---> NewsOrchestrator (tertiary fallback)
NewsOrchestrator ---------> VADER sentiment scoring (per-article scores)

VADER sentiment scoring --> Per-holding sentiment score (aggregate)
Per-holding sentiment ----> Composite Scorer (sentiment component weight)
Per-holding sentiment ----> Report section (sentiment display in HTML)

Fear & Greed Index -------> Report header (market-wide indicator)
Fear & Greed Index -------> Risk assessment (market-wide risk input)

Finnhub economic calendar -> Report section (upcoming events)
Finnhub earnings surprises -> Fundamental score modifier

Sentiment + Macro --------> Report enrichment (enhanced sections + dashboard)

(Existing components touched:)
Existing SentimentAnalyzer --> stays as fallback when new sources unavailable
Existing assess_market_regime() --> upgraded to use real FRED/VIX data
Existing EnrichedAnalysis schema --> extended with sentiment_score, macro_context
Existing DeepAnalysisScorer --> modified weights to include sentiment dimension
Existing ScoringThresholds --> new weight_sentiment field
```

## MVP Recommendation

### Phase 1 -- Data Foundation (fetch data, define schemas)

Prioritize:
1. **FRED macro indicators** -- Fills existing `MacroIndicators` schema gaps (GDP, unemployment currently return `None`). Highest signal-to-effort ratio: one adapter fills 4+ data points. Uses `fredapi` library. Pure Python, $0, deterministic.
2. **VIX real data** -- Replace hardcoded default of 20.0 in `assess_market_regime()` with real VIX via yfinance (`^VIX`). Minimal code change, immediate accuracy improvement.
3. **Finnhub news adapter** -- Primary news source with free tier (60 calls/min). Provides company news, economic calendar, and earnings surprises.
4. **Fear and Greed Index** -- Single API call, high-value market context signal. `fear-and-greed` library.
5. **Sentiment/macro schema extensions** -- Add optional `sentiment_score`, `sentiment_confidence`, `macro_context` fields to `QuantitativeAnalysis` and `EnrichedAnalysis`. Schema-first approach ensures type safety.

### Phase 2 -- Scoring Integration (wire data into scorer)

Prioritize:
6. **VADER sentiment scoring** -- Replace keyword matching in existing sentiment tools with validated lexicon+rules engine. Deterministic, $0, <1ms per headline.
7. **gnews + feedparser RSS** -- Fallback news sources for broader coverage.
8. **Composite score with sentiment** -- Rebalance weights to include sentiment (e.g., 35/25/25/15 or adaptive). Feature-flag gated (`FF_SMART_SCORING_ENABLED=false` by default until validated).
9. **Market regime from real data** -- Wire VIX + yield curve into `assess_market_regime()`. Feed regime into scorer's adaptive weights.

### Phase 3 -- Report Enrichment (display in HTML)

Prioritize:
10. **Sentiment section in report** -- Article count, score, trend direction, top headlines. Use existing `ReportSectionBuilder`. The `FRENCH_SECTIONS` dict already has `sentiment_marche`.
11. **Macro dashboard section** -- Traffic-light indicators for VIX, yield curve, GDP, CPI. One-glance market environment summary with color-coded gauges.
12. **Fear and Greed display** -- Single gauge/number in the macro dashboard.
13. **Economic calendar** -- Upcoming FOMC/CPI/jobs dates from Finnhub.

### Defer to Future Milestones

- **Sector-relative sentiment**: Requires cross-holding aggregation and many API calls per run. Defer until caching is more mature.
- **Historical macro overlay charts**: Nice-to-have visualization, not scoring-critical. Plotly is already in dependencies.
- **Earnings surprise integration**: Requires scheduling/calendar awareness. Can be added incrementally.
- **Sentiment trend tracking**: Requires historical sentiment storage (cache/database extension).
- **FinBERT upgrade**: Consider behind feature flag if VADER accuracy proves insufficient on financial text. FinBERT achieves ~79% accuracy vs VADER's ~63% on financial benchmarks, but requires ~500MB model + PyTorch dependency.
- **Multi-provider fallback chain**: Important for reliability but does not add new analytical capability. Can be done incrementally.

## Integration Points with Existing Pipeline

| Existing Component | How It Changes | Risk Level |
|-------------------|----------------|------------|
| `DeepAnalysisScorer._compute_weighted_score()` | New weight for sentiment dimension. Must remain backward-compatible (weight defaults to 0 if sentiment unavailable). Feature-flag gated. | **HIGH** -- Core scoring logic. Extensive testing required. Wrong weights = wrong recommendations. |
| `ScoringThresholds` dataclass | Add `weight_sentiment: float = 0.0` (default OFF). Existing 40/30/30 unchanged unless flag enabled. | **LOW** -- Additive change, default preserves current behavior. |
| `QuantitativeAnalysis` schema | Add optional `sentiment_score: float | None`, `sentiment_confidence: float | None`, `macro_regime: str | None` fields with defaults of None. | **LOW** -- Optional fields. Fully backward compatible. |
| `EnrichedAnalysis` schema | Add optional `market_context: dict | None` field (macro indicators, regime, VIX). | **LOW** -- Same approach. |
| `deep_analysis_pipeline.py` | New step between `collect_raw_data()` and `calculate_quantitative()`: collect sentiment + macro data. Follows existing functional pipeline pattern. | **MEDIUM** -- Pipeline modification but additive. New function `collect_market_context()` composed in same style. |
| `MacroIndicators` + `MarketContextExtractor` | Fill existing schema fields with real FRED data instead of hardcoded estimates. Replaces `_extract_gdp_growth()` etc. | **MEDIUM** -- Changes data values but schema already exists. |
| `assess_market_regime()` in `scoring_criteria.py` | Wire real VIX + yield curve data. Replace `vix_level = market_context.get("vix", 20.0)` with actual value. | **MEDIUM** -- Threshold logic already exists, just needs real inputs. |
| `SentimentAnalyzer` (existing) | Optionally replaced by VADER-based scorer. Keep as fallback when feature flag disabled. | **MEDIUM** -- Must not break existing flows. Feature-flag gated. |
| `ReportSectionBuilder` | Add new section types for sentiment and macro. `FRENCH_SECTIONS` already has `sentiment_marche`. | **LOW** -- Purely additive. |
| `tool_factories.py` | Register new tools (FRED data, enhanced sentiment, Fear and Greed). | **LOW** -- Additive. Follows existing pattern. |
| `config/endpoints.py` | Add `FINNHUB_BASE`, `FRED_BASE` URLs. | **LOW** -- Additive. |
| `config/features/flags.py` | Add new feature flags for sentiment, macro, smart scoring. | **LOW** -- Follows existing pattern. |

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| Table stakes features | HIGH | Verified against multiple financial platforms (Finnhub, EODHD, Alpha Vantage, Bloomberg Terminal). Standard patterns across the industry. |
| VADER recommendation | HIGH | Validated lexicon, well-documented on PyPI/GitHub, <1ms/headline, aligns with AI Minimalism. Existing STACK.md research concurs. |
| FinBERT as future upgrade | HIGH | Well-documented on HuggingFace (26K+ downloads/month), peer-reviewed paper (arXiv 1908.10063), active development (EMNLP 2025 workshop paper). Clear upgrade path if VADER insufficient. |
| FRED API / fredapi | HIGH | Official Federal Reserve API. Python library is stable (PyPI, GitHub). 816K+ time series. Free API key. Existing codebase already references `fredapi` in mypy config. |
| Composite scoring rebalance | MEDIUM | Academic literature confirms sentiment has limited standalone predictive power (R-squared ~0.01). As a *modifier* on existing scores, it adds value, but weight calibration requires backtesting. Feature-flag gating is essential. |
| Market regime detection | MEDIUM | VIX + yield curve approach supported by academic research (ScienceDirect 2023). Practical implementation straightforward but threshold tuning is empirical. |
| Anti-features assessment | HIGH | Based on FinWiz's stated philosophy (AI Minimalism, Python wins, $0 deterministic scoring) and academic evidence on sentiment limitations (ACM Computing Surveys, 2024). |
| Report enrichment | HIGH | `ReportSectionBuilder` is well-architected for adding new sections. Existing patterns are clear. Low risk. |

## Sources

- Existing codebase: `data/adapters/base_adapter.py`, `orchestrators/extraction/market_context.py`, `tools/sentiment_analyzer.py`, `tools/enhanced_sentiment_tool.py`, `tools/scoring/scoring_criteria.py`
- [Finnhub API Documentation](https://finnhub.io/docs/api) -- News sentiment, economic calendar endpoints
- [Finnhub Python Client](https://github.com/Finnhub-Stock-API/finnhub-python) -- Official Python client
- [FRED API Documentation](https://fred.stlouisfed.org/docs/api/fred/) -- 816K+ economic time series
- [fredapi PyPI](https://pypi.org/project/fredapi/) -- Python wrapper for FRED
- [vaderSentiment GitHub](https://github.com/cjhutto/vaderSentiment) -- Validated sentiment lexicon
- [ProsusAI/FinBERT on HuggingFace](https://huggingface.co/ProsusAI/finbert) -- Financial sentiment NLP model (future upgrade path)
- [FinBERT Paper](https://arxiv.org/abs/1908.10063) -- 79% accuracy on financial text
- [CNN Fear and Greed Index](https://www.cnn.com/markets/fear-and-greed) -- Composite of 7 market indicators
- [fear-greed-index Python wrapper](https://github.com/DidierRLopes/fear-greed-index) -- Python library
- [VIX-Yield Curve Recession Prediction (ScienceDirect 2023)](https://www.sciencedirect.com/science/article/abs/pii/S0169207023000389) -- VIX + yield curve outperforms spread alone
- [ACM Survey: Financial Sentiment Analysis](https://dl.acm.org/doi/full/10.1145/3649451) -- Comprehensive survey confirming sentiment limitations as standalone predictor
- [Moody's: Power of News Sentiment](https://www.moodys.com/web/en/us/insights/digital-transformation/the-power-of-news-sentiment-in-modern-financial-analysis.html) -- Industry perspective
- [EODHD Financial News API](https://eodhd.com/financial-apis/stock-market-financial-news-api) -- Alternative provider (considered, not recommended due to cost)
- [Alpha Vantage](https://www.alphavantage.co/) -- Already integrated in FinWiz
- [Macro-Quantamental Scorecards (Macrosynergy)](https://macrosynergy.com/research/macro-scorecards-a-python-building-kit-for-fixed-income-markets/) -- Approach to normalizing macro indicators into scores
