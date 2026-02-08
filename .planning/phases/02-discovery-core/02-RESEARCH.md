# Phase 2 Research: Discovery Core

## Existing Codebase Analysis

### Schema Patterns

Schemas live in `schemas/` with strict Pydantic v2 conventions:
- `model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)`
- `Field(...)` with `description`, validators (`ge`, `le`, `gt`)
- Common types imported from `schemas/common.py`: `AssetClass`, `RiskAssessmentStandardized`, `RiskLevel`
- Grade type from `schemas/portfolio_review.py`: `Grade = Literal["A+", "A", "B+", "B", "C+", "C", "D", "F"]`

**Existing discovery schema** (`schemas/investment_discovery.py`):
- Already has `InvestmentCandidate`, `APlusCriteria`, `APlusAnalysis`, `APlusDiscoveryResult`
- These are the **existing crew-based** discovery schemas — the new newcomer discovery schemas (DISC-01) are **separate and additional**
- New schemas should be named `NewcomerCandidate`, `EnrichmentResult`, `NewcomerDiscoveryResult` per requirements
- Place in `schemas/newcomer_discovery.py` (new file)

### Scoring Infrastructure

**`scoring/grading_system.py`**:
- `score_to_grade(composite_score: float) -> GradeInfo` — takes 0.0-1.0, returns GradeInfo dataclass
- `GradeInfo` has: `grade`, `percentage`, `description`, `action`, `emoji`, `css_class`
- Grade thresholds: A+ >= 0.95, A >= 0.85, B+ >= 0.80, B >= 0.75, C+ >= 0.70, C >= 0.65, D >= 0.50, F < 0.50
- `Grade = Literal["A+", "A", "B+", "B", "C+", "C", "D", "F"]`

**`scoring/thresholds.py`**:
- `ScoringThresholds` dataclass with all threshold constants
- `DEFAULT_THRESHOLDS` global instance, `get_thresholds()` accessor
- Contains weights for composite scoring: 40% fundamental, 30% technical, 30% risk
- Per-asset weights defined (stock ROE/debt/growth/margin, ETF expense/tracking/AUM, crypto market_cap/volume/age/supply)

**`tools/screening_criteria.py`**:
- `ScreeningCriteria` class with `get_default_criteria(asset_type)` and `passes_screening_filters()`
- Returns dict-based criteria per asset type (etf/stock/crypto)
- CandidateScorer should **reuse** this class for filter logic

**`tools/screening_ranking.py`**:
- `ScreeningCandidate` Pydantic model (symbol, name, asset_type, preliminary_score, meets_a_plus_criteria, etc.)
- `ScreeningRanking` class with `calculate_preliminary_score()` method per asset type
- Already has weight-based scoring for ETF (expense 40%, AUM 30%, tracking 20%, history 10%), Stock (ROE 30%, growth 25%, debt 20%, market_cap 15%, FCF 10%), Crypto (market_cap 35%, volume 25%, age 20%, institutional 10%, utility 10%)
- **Note**: `ScreeningCandidate` in `screening_ranking.py` is a Pydantic model but lives in `tools/`, not `schemas/` — violates project rules. The new `NewcomerCandidate` must go in `schemas/`.

### Current Discovery (Mocked)

Three identical-pattern files in `scoring/`:
- `scoring/stock_analyzer.py` → `analyze_stock_opportunities(session_id)` — returns hardcoded MSFT, NVDA, GOOGL
- `scoring/etf_analyzer.py` → `analyze_etf_opportunities(session_id)` — returns hardcoded VTI, VXUS, BND
- `scoring/crypto_analyzer.py` → `analyze_crypto_opportunities(session_id)` — returns hardcoded BTC, ETH

All return `dict[str, Any]` with keys: `opportunities` (list of dicts), `analysis_summary`, `performance_metrics`.

**These files will be replaced by real discovery in Phase 3** (feature flag routing). Phase 2 only builds the components.

### Available Tools & Libraries

| Library | Available | Usage for Discovery |
|---------|-----------|-------------------|
| yfinance | Yes | ETF holdings (`Ticker.get_funds_data().top_holdings`), price history, fundamentals |
| TA-Lib | Yes | RSI, momentum calculations for MomentumScanner |
| pandas 3.0.0 | Yes | Data manipulation |
| numpy 1.26.4 | Yes | Numerical calculations |
| requests | Yes | SEC EDGAR EFTS API calls |

**Existing tools relevant to discovery**:
- `tools/yahoo_finance_etf_holdings_tool.py` — `YahooFinanceETFHoldingsTool` wraps yfinance ETF holdings
- `tools/yahoo_finance_history_tool.py` — price history
- `tools/yahoo_finance_ticker_info_tool.py` — ticker fundamentals
- `tools/sec_tool.py` — SEC filing search (uses `sec_api` paid package)
- `tools/enhanced_sec_tool.py` — enhanced SEC analysis with risk scoring
- `tools/technical_algorithms.py` — RSI, MACD, Fibonacci calculations
- `tools/screening_utils.py` — `ScreeningUtils` class with static universe lists (stock, ETF, crypto)

## Component Design Research

### DISC-01: Schemas (`schemas/newcomer_discovery.py`)

**NewcomerCandidate** fields needed:
- `ticker: str` — ticker symbol
- `name: str` — company/fund name
- `asset_class: AssetClass` — stock/etf/crypto (use existing enum)
- `source: Literal["ipo", "breakout", "momentum", "universe"]` — how discovered
- `discovery_date: datetime`
- `composite_score: float` (0.0-1.0)
- `grade: Grade` — from score_to_grade()
- `grade_info: str` — grade description
- `market_cap: float | None`
- `sector: str | None`
- `key_metrics: dict[str, Any]` — source-specific metrics
- `rationale: str` — why this was flagged

**EnrichmentResult** fields:
- `ticker: str`
- `enrichment_source: Literal["perplexity", "sec", "yahoo"]`
- `summary: str`
- `risk_factors: list[str]`
- `catalysts: list[str]`
- `enriched_at: datetime`
- `confidence: float` (0.0-1.0)

**NewcomerDiscoveryResult** fields:
- `asset_class: AssetClass`
- `run_timestamp: datetime`
- `candidates: list[NewcomerCandidate]`
- `total_screened: int`
- `sources_used: list[str]`
- `top_picks: list[str]` — top N tickers
- `enrichments: list[EnrichmentResult]` — (populated in Phase 3)
- `performance_metrics: dict[str, Any]` — execution stats

### DISC-02: DynamicUniverseProvider

**Location**: `src/finwiz/discovery/universe_provider.py` (new `discovery/` package)

**yfinance ETF holdings API**:
```python
import yfinance as yf
t = yf.Ticker("SPY")
fd = t.get_funds_data()
holdings_df = fd.top_holdings  # DataFrame: index=Symbol, columns=[Name, Holding Percent]
```
- Returns top ~10 holdings per ETF
- To build universe: query multiple major ETFs (SPY, QQQ, VTI, VGT, etc.)
- Deduplicate resulting tickers
- Filter to unique tickers not already in user's portfolio

**Fallback**: Use existing `ScreeningUtils._get_stock_universe()` / `_get_etf_universe()` / `_get_crypto_universe()` static lists.

**Design**:
```python
class DynamicUniverseProvider:
    def __init__(self, seed_etfs: list[str] | None = None): ...
    def get_universe(self, asset_class: str) -> list[str]: ...
    def _mine_etf_holdings(self) -> list[str]: ...
    def _fallback_static_universe(self, asset_class: str) -> list[str]: ...
```

### DISC-03: IPOScreener

**Location**: `src/finwiz/discovery/ipo_screener.py`

**SEC EDGAR EFTS API** (free, no API key needed):
- Endpoint: `https://efts.sec.gov/LATEST/search-index`
- Query S-1/S-1A filings: `?q="S-1"&forms=S-1&dateRange=custom&startdt=YYYY-MM-DD&enddt=YYYY-MM-DD`
- Response contains: `hits.hits[]._source.{ciks, display_names, file_date, root_forms, form, adsh, sics}`
- `display_names` includes company name and ticker (if available): `"CleanCore Solutions, Inc.  (ZONE)  (CIK 0001956741)"`
- Rate limit: 10 requests/second per SEC fair access policy
- Requires `User-Agent` header with contact info

**Design**:
```python
class IPOScreener:
    def screen(self, lookback_days: int = 180) -> list[NewcomerCandidate]: ...
    def _query_sec_efts(self, start_date: str, end_date: str) -> list[dict]: ...
    def _extract_ticker_from_display_name(self, display_name: str) -> str | None: ...
    def _get_fundamentals(self, ticker: str) -> dict[str, Any]: ...
```

**Key consideration**: Not all S-1 filers have tickers at filing time. Parse from `display_names` field using regex for `(TICKER)` pattern. Filter out those without tickers.

### DISC-04: BreakoutDetector

**Location**: `src/finwiz/discovery/breakout_detector.py`

**Breakout signals** (price/volume on small/mid-cap $200M-$50B):
1. **Price breakout**: Price exceeds N-day high with volume > 2x average
2. **Volume breakout**: Volume spike > 3x 20-day average
3. **Range breakout**: Price breaks out of consolidation range (Bollinger Band squeeze)

**Data source**: yfinance price history (`Ticker.history(period="3mo")`)

**Design**:
```python
class BreakoutDetector:
    def detect(self, universe: list[str]) -> list[NewcomerCandidate]: ...
    def _check_price_breakout(self, ticker: str, history: pd.DataFrame) -> float: ...
    def _check_volume_breakout(self, ticker: str, history: pd.DataFrame) -> float: ...
    def _get_market_cap(self, ticker: str) -> float | None: ...
    def _filter_by_market_cap(self, ticker: str, min_cap: float, max_cap: float) -> bool: ...
```

**Market cap filter**: Use `yf.Ticker(ticker).info.get("marketCap")` to filter $200M-$50B.

### DISC-05: MomentumScanner

**Location**: `src/finwiz/discovery/momentum_scanner.py`

**Momentum signals**:
1. **Volume anomaly**: Current volume > 2x 20-day SMA volume
2. **RSI**: TA-Lib `talib.RSI()` — look for RSI crossing above 50 (bullish) or extreme values
3. **Momentum**: Rate of change over 10/20 periods

**Available TA-Lib functions**:
```python
import talib
rsi = talib.RSI(close_prices, timeperiod=14)
mom = talib.MOM(close_prices, timeperiod=10)
roc = talib.ROC(close_prices, timeperiod=10)
```

**Design**:
```python
class MomentumScanner:
    def scan(self, universe: list[str]) -> list[NewcomerCandidate]: ...
    def _calculate_volume_anomaly(self, history: pd.DataFrame) -> float: ...
    def _calculate_rsi_signal(self, closes: np.ndarray) -> float: ...
    def _calculate_momentum_signal(self, closes: np.ndarray) -> float: ...
    def _composite_momentum_score(self, volume: float, rsi: float, momentum: float) -> float: ...
```

### DISC-06: CandidateScorer

**Location**: `src/finwiz/discovery/candidate_scorer.py`

**Reuse existing infrastructure**:
- `ScreeningCriteria.get_default_criteria(asset_type)` for filtering thresholds
- `ScreeningCriteria.passes_screening_filters()` for pass/fail
- `score_to_grade()` from `scoring/grading_system.py` for grade assignment
- `ScreeningRanking.calculate_preliminary_score()` from `tools/screening_ranking.py` for detailed scoring

**Design**:
```python
class CandidateScorer:
    def score_and_grade(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]: ...
    def _calculate_score(self, candidate: NewcomerCandidate) -> float: ...
    def _assign_grade(self, score: float) -> tuple[Grade, str]: ...
    def _passes_filters(self, candidate: NewcomerCandidate) -> bool: ...
```

## Integration Points

1. **Schema imports**: New schemas in `schemas/newcomer_discovery.py` import `AssetClass`, `Grade`, `RiskAssessmentStandardized` from existing schemas
2. **Scoring reuse**: CandidateScorer reuses `ScreeningCriteria`, `score_to_grade()`, `ScreeningRanking.calculate_preliminary_score()`
3. **Tool reuse**: Universe provider reuses yfinance (same as `YahooFinanceETFHoldingsTool`), IPO screener uses SEC EFTS API (new, free)
4. **TA-Lib**: MomentumScanner uses TA-Lib for RSI/momentum (already a project dependency)
5. **No flow integration yet**: Phase 2 builds standalone components. Phase 3 wires them into the flow.

## Risks and Considerations

1. **yfinance rate limits**: ETF holdings fetches are network calls. DynamicUniverseProvider should cache results and handle failures gracefully.
2. **SEC EFTS API fair access**: 10 req/sec limit. IPOScreener must respect this. User-Agent header required.
3. **S-1 ticker extraction**: Not all S-1 filers have tickers in `display_names`. Regex parsing may miss some.
4. **Market cap filtering**: yfinance `info` dict may not always have `marketCap`. Need fallback/skip logic.
5. **TA-Lib NaN handling**: RSI/momentum return NaN for insufficient data periods. Must handle gracefully.
6. **File size limit**: Each module must stay under 300 lines. The components are well-scoped for this.
7. **No `__init__.py` needed yet**: Discovery package needs `__init__.py` for imports.

## Recommendations

1. **New package**: Create `src/finwiz/discovery/` with `__init__.py`, one file per component.
2. **Schema file**: `schemas/newcomer_discovery.py` — keep separate from existing `investment_discovery.py`.
3. **Reuse aggressively**: Don't rewrite scoring logic. Import from `screening_criteria.py`, `grading_system.py`, `screening_ranking.py`.
4. **Error-tolerant design**: Each screener should return partial results on individual ticker failures (log and skip).
5. **No AI calls**: All Phase 2 components are pure Python ($0 cost), consistent with AI Minimalism.
6. **Testing**: Each component should be independently testable with mocked yfinance/SEC responses. Tests come in Phase 3 (DISC-11).

## File Plan

| Requirement | File | Est. Lines |
|-------------|------|-----------|
| DISC-01 | `schemas/newcomer_discovery.py` | ~80 |
| DISC-02 | `discovery/universe_provider.py` | ~120 |
| DISC-03 | `discovery/ipo_screener.py` | ~150 |
| DISC-04 | `discovery/breakout_detector.py` | ~150 |
| DISC-05 | `discovery/momentum_scanner.py` | ~140 |
| DISC-06 | `discovery/candidate_scorer.py` | ~100 |
| (package) | `discovery/__init__.py` | ~15 |

Total: ~755 lines across 7 files. All under 300-line limit.

## RESEARCH COMPLETE
