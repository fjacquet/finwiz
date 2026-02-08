"""
Discovery components for finding newcomer investment candidates.

Pure Python ($0 cost) -- no AI calls. Components:
- DynamicUniverseProvider: mines ETF holdings for candidate tickers
- IPOScreener: finds recent IPO filings via SEC EDGAR
- BreakoutDetector: detects price/volume breakouts
- MomentumScanner: scans for momentum signals (RSI, volume anomaly)
- CandidateScorer: scores and grades candidates
"""

from finwiz.discovery.breakout_detector import BreakoutDetector
from finwiz.discovery.candidate_scorer import CandidateScorer
from finwiz.discovery.ipo_screener import IPOScreener
from finwiz.discovery.momentum_scanner import MomentumScanner
from finwiz.discovery.universe_provider import DynamicUniverseProvider

__all__ = [
    "BreakoutDetector",
    "CandidateScorer",
    "DynamicUniverseProvider",
    "IPOScreener",
    "MomentumScanner",
]
