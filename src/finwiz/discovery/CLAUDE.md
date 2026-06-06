# Discovery Module

Individual discovery components for finding newcomer investment candidates.

## Directory Structure

```
discovery/
├── __init__.py                # Exports all 5 discovery classes
├── universe_provider.py       # DynamicUniverseProvider: ETF holdings via yfinance + static fallback
├── ipo_screener.py            # IPOScreener: SEC EDGAR EFTS API for S-1/S-1A filings
├── breakout_detector.py       # BreakoutDetector: Price/volume breakout signals ($200M-$50B cap)
├── momentum_scanner.py        # MomentumScanner: RSI + volume anomaly + ROC via TA-Lib
└── candidate_scorer.py        # CandidateScorer: Grades candidates using ScreeningRanking + score_to_grade()
```

## Entry Points

| File | Class | Purpose |
|------|-------|---------|
| `universe_provider.py` | `DynamicUniverseProvider` | Mine stock/ETF/crypto universe from ETF holdings |
| `ipo_screener.py` | `IPOScreener` | Find recent IPO candidates from SEC filings |
| `breakout_detector.py` | `BreakoutDetector` | Detect price/volume breakout patterns |
| `momentum_scanner.py` | `MomentumScanner` | Scan for momentum signals (RSI, volume, ROC) |
| `candidate_scorer.py` | `CandidateScorer` | Score and grade candidates (A+ to F) |
| `market_data.py` | `get_returns`, `get_sectors`, `factor_score_from_returns` | Batched prices/sectors (per-day file cache) + standalone factor score for the Portfolio-Aware Opportunity Cascade |

## Usage

```python
from finwiz.discovery import (
    DynamicUniverseProvider,
    IPOScreener,
    BreakoutDetector,
    MomentumScanner,
    CandidateScorer,
)

provider = DynamicUniverseProvider()
tickers = provider.get_universe("stock")

scorer = CandidateScorer()
scored = scorer.score_and_grade(candidates)
```

## Related Modules

- `finwiz.schemas.newcomer_discovery` — Pydantic models (NewcomerCandidate, EnrichmentResult, NewcomerDiscoveryResult)
- `finwiz.scoring.discovery.pipeline` — NewcomerDiscoveryPipeline orchestrating these components
- `finwiz.scoring.grading_system` — `score_to_grade()` used by CandidateScorer
- `finwiz.tools.screening_ranking` — ScreeningRanking used for preliminary scoring
