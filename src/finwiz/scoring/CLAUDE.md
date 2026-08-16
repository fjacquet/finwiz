# Scoring Module

Python-based deterministic scoring for financial analysis. All scoring is pure Python — NOT AI (AI Minimalism).

## Directory Structure

```
scoring/
├── __init__.py                    # Exports: DeepAnalysisScorer, PortfolioDeepAnalyzer
├── deep_analysis_scorer.py        # MAIN: Composite scoring (40% fundamental, 30% technical, 30% risk)
├── fundamental_scorer.py          # Fundamental analysis scoring (P/E, ROE, etc.)
├── technical_scorer.py            # Technical analysis scoring (RSI, MACD, etc.)
├── risk_scorer.py                 # Risk assessment scoring (volatility, drawdown)
├── technical_fallback.py          # Fallback when technical data unavailable
├── thresholds.py                  # ScoringThresholds, DEFAULT_THRESHOLDS, get_thresholds()
├── utils.py                       # calculate_threshold_score(), interpolate_threshold_score()
├── grading_system.py              # score_to_grade(), GradeInfo, Grade type, format_grade_display()
├── portfolio_deep_analyzer.py     # PortfolioDeepAnalyzer, analyze_portfolio_with_python()
├── crew_export_generator.py       # CrewExportGenerator
├── score_result_builder.py        # ScoreResultBuilder
│
├── asset_analyzers/               # Strategy pattern — per-asset scoring
│   ├── __init__.py
│   ├── base.py                    # AssetAnalyzer (abstract)
│   ├── stock_analyzer.py          # StockAnalyzer
│   ├── etf_analyzer.py            # ETFAnalyzer
│   ├── crypto_analyzer.py         # CryptoAnalyzer
│   └── factory.py                 # AnalyzerFactory.get_analyzer(asset_class)
│
├── discovery/                     # Newcomer discovery pipeline (recall strategy gated by portfolio_aware_discovery)
│   ├── __init__.py                # Exports: NewcomerDiscoveryPipeline
│   └── pipeline.py               # NewcomerDiscoveryPipeline orchestrator
│
├── # Discovery analyzers — always route through NewcomerDiscoveryPipeline; no mocked/legacy fallback
├── stock_analyzer.py              # analyze_stock_opportunities()
├── etf_analyzer.py                # analyze_etf_opportunities()
└── crypto_analyzer.py             # analyze_crypto_opportunities()
```

## Entry Points

| File | Class/Function | Purpose |
|------|---------------|---------|
| `deep_analysis_scorer.py` | `DeepAnalysisScorer` | Composite scoring engine |
| `grading_system.py` | `score_to_grade()` | Convert score (0-1) to letter grade (A+ to F) |
| `grading_system.py` | `GradeInfo` | Grade with label, description, action |
| `portfolio_deep_analyzer.py` | `analyze_portfolio_with_python()` | Score entire portfolio |
| `asset_analyzers/factory.py` | `AnalyzerFactory` | Get analyzer by asset class |

## Grading Thresholds

```
A+ >= 0.95 | A >= 0.85 | B+ >= 0.80 | B >= 0.75
C+ >= 0.70 | C >= 0.65 | D >= 0.50  | F < 0.50
```

## Usage

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer
from finwiz.scoring.grading_system import score_to_grade

scorer = DeepAnalysisScorer()
result = scorer.calculate_composite_score(ticker="AAPL", asset_class="stock", data={...})
grade_info = score_to_grade(result.composite_score)
```

## Related Modules

- `finwiz.analysis` — Uses scorer in deep analysis pipeline
- `finwiz.schemas.crew_exports` — Export schemas with scores
- `finwiz.quantitative` — Quantitative calculations feeding scorers
