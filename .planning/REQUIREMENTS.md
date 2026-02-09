# Requirements: FinWiz v4 -- Data Intelligence & Smart Scoring

**Defined:** 2026-02-08
**Core Value:** Smarter scoring by factoring in news sentiment and macroeconomic context, not just technicals and fundamentals.

## v4 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Data Foundation

- [ ] **DATA-01**: Finnhub news adapter fetches per-ticker company news with waterfall fallback
- [ ] **DATA-02**: FRED macro adapter fetches key economic indicators (Fed funds rate, CPI, unemployment, GDP growth, 10Y yield, 2Y yield, VIX)
- [ ] **DATA-03**: Fear & Greed Index adapter fetches current market sentiment gauge (0-100)
- [ ] **DATA-04**: Pydantic schemas for NewsArticle, NewsSentimentResult, and MacroSnapshot in schemas/
- [ ] **DATA-05**: Feature flags for news sentiment (FF_NEWS_SENTIMENT) and macro indicators (FF_MACRO_INDICATORS) with circuit breaker strategy
- [ ] **DATA-06**: Finnhub and FRED API endpoints registered in config/endpoints.py
- [ ] **DATA-07**: Finnhub and FRED registered in APIProvider enum and rate limiter config
- [ ] **DATA-08**: News deduplication across multiple sources using existing Jaccard similarity pattern
- [ ] **DATA-09**: Source reliability weighting for news articles using existing tier system

### Sentiment Scoring

- [ ] **SENT-01**: Headline sentiment scoring using Finnhub pre-computed sentiment with VADER as local fallback
- [ ] **SENT-02**: Aggregate sentiment score per holding (weighted average by source reliability)
- [ ] **SENT-03**: Sentiment confidence metric based on article count, source diversity, and recency
- [ ] **SENT-04**: Temporal decay weighting -- recent articles weighted more than older ones (exponential decay)
- [ ] **SENT-05**: Explicit "no news" handling -- absence of news is None, not neutral (0.0)

### Macro Context

- [ ] **MACRO-01**: Real VIX data replaces hardcoded default of 20.0 in assess_market_regime()
- [ ] **MACRO-02**: Real Fed funds rate replaces hardcoded estimates in _estimate_interest_rate()
- [ ] **MACRO-03**: CPI/inflation data from FRED fills existing MacroIndicators schema gaps
- [ ] **MACRO-04**: 10Y and 2Y Treasury yields from FRED for yield curve analysis
- [ ] **MACRO-05**: Yield curve spread computation (10Y-2Y) with regime classification (inverted/flat/normal/steep)
- [ ] **MACRO-06**: Market regime detection using real VIX + yield curve data instead of hardcoded thresholds
- [ ] **MACRO-07**: Macro data collected ONCE per analysis run (session-level), not per holding

### Smart Scoring

- [ ] **SCORE-01**: Sentiment factor integrated into composite scoring as additive adjustment overlay (not weight redistribution)
- [ ] **SCORE-02**: Sentiment scoring starts at weight=0.0 (feature-flagged off) with configurable weight via ScoringThresholds
- [ ] **SCORE-03**: Macro context adjusts risk scoring weights dynamically based on market regime
- [ ] **SCORE-04**: Per-asset-class macro sensitivity -- stocks, ETFs, and crypto respond differently to macro indicators

### Report Enrichment

- [ ] **REPORT-01**: Sentiment section per holding showing score, confidence, article count, and top headlines
- [ ] **REPORT-02**: Macro dashboard section showing VIX, yield curve, GDP, CPI, Fed rate with traffic-light indicators
- [ ] **REPORT-03**: Fear & Greed Index gauge displayed in macro dashboard
- [ ] **REPORT-04**: Economic calendar section showing upcoming FOMC, CPI releases, earnings dates from Finnhub

### Discovery Fix

- [ ] **DISC-01**: Discovery pipeline returns real screened candidates instead of hardcoded/mocked generic data

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Sentiment Enhancements

- **SENT-F01**: FinBERT integration behind feature flag for higher accuracy on financial text
- **SENT-F02**: Sector-relative sentiment normalization (compare holding sentiment to sector average)
- **SENT-F03**: Historical sentiment trend tracking (7/14/30 day moving averages)

### Macro Enhancements

- **MACRO-F01**: Historical macro overlay charts (FRED time series plotted alongside holding performance)
- **MACRO-F02**: PMI, consumer confidence, and credit spread indicators

### Data Provider Enhancements

- **DATA-F01**: gnews adapter as secondary news source
- **DATA-F02**: RSS feed adapter (feedparser) as tertiary news source
- **DATA-F03**: Earnings surprise integration from Finnhub
- **DATA-F04**: Additional market data providers (Polygon, Finnhub market data) for broader coverage

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming news | Batch analysis; WebSocket complexity adds zero value |
| AI-generated sentiment per article | Violates AI Minimalism; $0.01+/article, non-deterministic |
| Social media scraping (Twitter/Reddit) | Noisy signal, paid APIs, bot contamination |
| Custom sentiment model training | Requires labeled data, GPU infra, ongoing maintenance |
| Automated trading signals from sentiment | Sentiment alone has R-squared ~0.01; irresponsible |
| Macro forecasting / predictions | Even central banks get it wrong |
| On-chain crypto sentiment | Requires paid specialized APIs (LunarCrush, Santiment) |
| Full NLP pipeline (NER, topic modeling) | Over-engineering; 500MB+ dependencies for marginal gain |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 13 | Pending |
| DATA-02 | Phase 13 | Pending |
| DATA-03 | Phase 13 | Pending |
| DATA-04 | Phase 13 | Pending |
| DATA-05 | Phase 13 | Pending |
| DATA-06 | Phase 13 | Pending |
| DATA-07 | Phase 13 | Pending |
| DATA-08 | Phase 13 | Pending |
| DATA-09 | Phase 13 | Pending |
| DISC-01 | Phase 13 | Pending |
| SENT-01 | Phase 14 | Pending |
| SENT-02 | Phase 14 | Pending |
| SENT-03 | Phase 14 | Pending |
| SENT-04 | Phase 14 | Pending |
| SENT-05 | Phase 14 | Pending |
| SCORE-01 | Phase 14 | Pending |
| SCORE-02 | Phase 14 | Pending |
| MACRO-01 | Phase 15 | Pending |
| MACRO-02 | Phase 15 | Pending |
| MACRO-03 | Phase 15 | Pending |
| MACRO-04 | Phase 15 | Pending |
| MACRO-05 | Phase 15 | Pending |
| MACRO-06 | Phase 15 | Pending |
| MACRO-07 | Phase 15 | Pending |
| SCORE-03 | Phase 15 | Pending |
| SCORE-04 | Phase 15 | Pending |
| REPORT-01 | Phase 16 | Pending |
| REPORT-02 | Phase 16 | Pending |
| REPORT-03 | Phase 16 | Pending |
| REPORT-04 | Phase 16 | Pending |

**Coverage:**
- v4 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-02-08*
*Last updated: 2026-02-09 after roadmap creation*
