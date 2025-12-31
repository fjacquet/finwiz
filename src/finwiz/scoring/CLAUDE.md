# Scoring Module

This directory contains Python-based scoring algorithms for financial analysis. Following AI Minimalism principles, all scoring is deterministic Python - NOT AI.

## Directory Structure

```
scoring/
├── asset_analyzers/           # Strategy pattern analyzers
│   ├── base.py                # Abstract base analyzer
│   ├── stock_analyzer.py      # Stock-specific scoring
│   ├── etf_analyzer.py        # ETF-specific scoring
│   ├── crypto_analyzer.py     # Crypto-specific scoring
│   └── factory.py             # Analyzer factory
│
├── __init__.py
├── deep_analysis_scorer.py    # MAIN: Composite scoring engine
├── fundamental_scorer.py      # Fundamental analysis scoring
├── technical_scorer.py        # Technical analysis scoring
├── technical_fallback.py      # Technical fallbacks
├── risk_scorer.py             # Risk assessment scoring
├── scoring_thresholds.py      # Score thresholds
├── scoring_utils.py           # Scoring utilities
├── portfolio_deep_analyzer.py # Portfolio-level analysis
├── crew_export_generator.py   # Generate crew export objects
├── score_result_builder.py    # Build scoring results with grades
│
├── # Legacy (to be migrated)
├── stock_analyzer.py          # Legacy stock analyzer
├── etf_analyzer.py            # Legacy ETF analyzer
└── crypto_analyzer.py         # Legacy crypto analyzer
```

## Major Entry Points

### Main Scorer

| File | Class | Purpose |
|------|-------|---------|
| `deep_analysis_scorer.py` | `DeepAnalysisScorer` | Main composite scoring engine |
| `portfolio_deep_analyzer.py` | `PortfolioDeepAnalyzer` | Portfolio-level scoring |
| `crew_export_generator.py` | `CrewExportGenerator` | Generate crew export objects |
| `score_result_builder.py` | `ScoreResultBuilder` | Build scoring results with grades |

### Component Scorers

| File | Class | Purpose |
|------|-------|---------|
| `fundamental_scorer.py` | `FundamentalScorer` | Score fundamentals (P/E, ROE, etc.) |
| `technical_scorer.py` | `TechnicalScorer` | Score technicals (RSI, MACD, etc.) |
| `risk_scorer.py` | `RiskScorer` | Score risk (volatility, drawdown, etc.) |

### Asset Analyzers (Strategy Pattern)

| File | Class | Purpose |
|------|-------|---------|
| `asset_analyzers/base.py` | `AssetAnalyzer` | Abstract base class |
| `asset_analyzers/stock_analyzer.py` | `StockAnalyzer` | Stock-specific logic |
| `asset_analyzers/etf_analyzer.py` | `ETFAnalyzer` | ETF-specific logic |
| `asset_analyzers/crypto_analyzer.py` | `CryptoAnalyzer` | Crypto-specific logic |
| `asset_analyzers/factory.py` | `AnalyzerFactory` | Get analyzer by asset class |

## AI Minimalism Benefit

```
┌──────────────────────────────────────────────────────┐
│              Python Scoring Engine                    │
├──────────────────────────────────────────────────────┤
│  Cost:        $0 (no API calls)                      │
│  Speed:       <100ms per holding                     │
│  Reliability: 100% (deterministic)                   │
│  Scalability: Unlimited                              │
└──────────────────────────────────────────────────────┘

vs

┌──────────────────────────────────────────────────────┐
│              AI-based Scoring                         │
├──────────────────────────────────────────────────────┤
│  Cost:        ~$0.05 per holding                     │
│  Speed:       5-15s per holding                      │
│  Reliability: ~95% (may hallucinate)                 │
│  Scalability: Rate limited                           │
└──────────────────────────────────────────────────────┘
```

## Usage

### DeepAnalysisScorer

```python
from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer

scorer = DeepAnalysisScorer()

# Calculate composite score
result = scorer.calculate_composite_score(
    ticker="AAPL",
    asset_class="stock",
    data={
        "roe": 0.25,
        "debt_to_equity": 0.3,
        "revenue_growth": 0.15,
        "rsi": 55,
        "macd_signal": "bullish",
        "volatility_30d": 0.22,
        # ... more metrics
    }
)

print(f"Grade: {result.grade}")           # "A"
print(f"Score: {result.composite_score}") # 0.78
print(f"Recommendation: {result.recommendation}") # "BUY"
```

### Asset-Specific Analyzer

```python
from finwiz.scoring.asset_analyzers.factory import AnalyzerFactory

# Get appropriate analyzer
analyzer = AnalyzerFactory.get_analyzer("stock")

# Calculate fundamental score
fundamental_score, details = analyzer.calculate_fundamental_score({
    "roe": 0.25,
    "debt_to_equity": 0.3,
    "revenue_growth": 0.15
})

print(f"Fundamental Score: {fundamental_score:.2f}")
print(f"Details: {details}")
```

### Component Scorers

```python
from finwiz.scoring.fundamental_scorer import FundamentalScorer
from finwiz.scoring.technical_scorer import TechnicalScorer
from finwiz.scoring.risk_scorer import RiskScorer

# Fundamental scoring
fundamental = FundamentalScorer()
f_score = fundamental.score({
    "pe_ratio": 25,
    "pb_ratio": 5.5,
    "roe": 0.22,
    "debt_to_equity": 0.4
})

# Technical scoring
technical = TechnicalScorer()
t_score = technical.score({
    "rsi": 55,
    "macd_signal": "bullish",
    "sma_50_200": "golden_cross"
})

# Risk scoring
risk = RiskScorer()
r_score = risk.score({
    "volatility_30d": 0.22,
    "max_drawdown": -0.15,
    "beta": 1.1
})

# Composite
composite = 0.4 * f_score + 0.3 * t_score + 0.3 * (1 - r_score/5)
```

## Strategy Pattern

```python
from abc import ABC, abstractmethod

class AssetAnalyzer(ABC):
    """Abstract base class for asset-specific analyzers."""

    @abstractmethod
    def calculate_fundamental_score(
        self, data: dict
    ) -> tuple[float, dict]:
        """Calculate fundamental score for this asset type."""
        pass

    @abstractmethod
    def calculate_technical_score(
        self, data: dict
    ) -> tuple[float, dict]:
        """Calculate technical score for this asset type."""
        pass

    @abstractmethod
    def get_asset_specific_metrics(self) -> list[str]:
        """Return list of required metrics for this asset type."""
        pass


class StockAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        # Stock-specific: P/E, P/B, ROE, etc.
        pass


class CryptoAnalyzer(AssetAnalyzer):
    def calculate_fundamental_score(self, data: dict) -> tuple[float, dict]:
        # Crypto-specific: TVL, active addresses, etc.
        pass
```

## Grading System

```python
from finwiz.scoring.scoring_thresholds import get_grade

score = 0.85

# Get letter grade
grade = get_grade(score)
# Returns: Grade.A_PLUS

# Thresholds:
# A+: >= 0.95
# A:  >= 0.85
# A-: >= 0.80
# B+: >= 0.75
# B:  >= 0.70
# B-: >= 0.65
# C+: >= 0.60
# C:  >= 0.55
# C-: >= 0.50
# D:  >= 0.40
# F:  < 0.40
```

## Testing

```bash
# Test all scoring
uv run pytest tests/unit/scoring/ -v

# Test deep analysis scorer
uv run pytest tests/unit/scoring/test_deep_analysis_scorer.py -v

# Test asset analyzers
uv run pytest tests/unit/scoring/test_asset_analyzers.py -v
```

## Related Modules

- `finwiz.quantitative` - Quantitative calculations
- `finwiz.tools.deep_analysis_scoring_tool` - Tool wrapper
- `finwiz.schemas.crew_exports` - Export with scores
- `finwiz.flow_state.DeepAnalysisResult` - Result schema
