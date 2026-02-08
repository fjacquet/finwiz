"""
Discovery components for finding newcomer investment candidates.

Pure Python ($0 cost) -- no AI calls. Components:
- DynamicUniverseProvider: mines ETF holdings for candidate tickers
- IPOScreener: finds recent IPO filings via SEC EDGAR
- BreakoutDetector: detects price/volume breakouts
- MomentumScanner: scans for momentum signals (RSI, volume anomaly)
- CandidateScorer: scores and grades candidates
"""

from finwiz.discovery.universe_provider import DynamicUniverseProvider

__all__ = [
    "DynamicUniverseProvider",
    # Added by 02-02:
    # "IPOScreener",
    # "BreakoutDetector",
    # "MomentumScanner",
    # "CandidateScorer",
]
