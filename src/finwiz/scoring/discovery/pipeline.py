"""
NewcomerDiscoveryPipeline - end-to-end discovery orchestration.

Orchestrates universe provider, screeners, scanner, and scorer
to find newcomer investment candidates for a given asset class.
Excludes tickers already held in the user's portfolio.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.schemas.newcomer_discovery import NewcomerCandidate, NewcomerDiscoveryResult

logger = get_logger(__name__)

ENRICHMENT_SCORE_THRESHOLD = 0.80
MAX_ENRICHMENT_CANDIDATES = 10


class NewcomerDiscoveryPipeline:
    """Orchestrates newcomer discovery for a single asset class.

    Gathers candidates from multiple screeners, excludes portfolio
    holdings, scores them, and persists results to JSON.
    """

    def __init__(self, asset_class: str) -> None:
        """Initialize pipeline for the given asset class.

        Args:
            asset_class: One of "stock", "etf", or "crypto".
        """
        self.asset_class = asset_class
        self.portfolio_tickers: set[str] = set()
        self._load_portfolio_tickers()

    def _load_portfolio_tickers(self) -> None:
        """Load tickers from all portfolio CSVs for exclusion.

        Reads stock.csv, etf.csv, and crypto.csv.  Normalizes by
        stripping ``Yahoo:`` prefix and handling crypto ``-USD`` suffix.
        """
        csv_files: dict[str, Path] = {
            "stock": Path("data/stock.csv"),
            "etf": Path("data/etf.csv"),
            "crypto": Path("data/crypto.csv"),
        }
        for asset_type, csv_path in csv_files.items():
            try:
                if not csv_path.exists():
                    continue
                with csv_path.open(newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        ticker = (row.get("Ticker") or "").strip()
                        if not ticker:
                            continue
                        if ticker.upper().startswith("YAHOO:"):
                            ticker = ticker.split(":", 1)[1]
                        upper = ticker.upper()
                        self.portfolio_tickers.add(upper)
                        # For crypto, keep both BTC and BTC-USD forms
                        if asset_type == "crypto":
                            if upper.endswith("-USD"):
                                self.portfolio_tickers.add(upper[:-4])
                            else:
                                self.portfolio_tickers.add(f"{upper}-USD")
            except (FileNotFoundError, OSError) as e:
                logger.warning("Could not read portfolio CSV %s: %s", csv_path, e)
            except Exception as e:
                logger.warning("Unexpected error reading %s: %s", csv_path, e)

        logger.info("Loaded %d portfolio tickers for exclusion", len(self.portfolio_tickers))

    def discover(self, session_id: str) -> NewcomerDiscoveryResult:
        """Run the full discovery pipeline for this asset class.

        Args:
            session_id: Unique session identifier for tracking.

        Returns:
            NewcomerDiscoveryResult with scored and filtered candidates.
        """
        from finwiz.schemas.newcomer_discovery import NewcomerDiscoveryResult

        start_time = time.time()

        # 1. Gather candidates from all screeners
        candidates = self._gather_candidates()
        logger.info("Gathered %d raw candidates for %s", len(candidates), self.asset_class)

        # 2. Exclude portfolio holdings
        candidates = [c for c in candidates if c.ticker.upper() not in self.portfolio_tickers]
        logger.info("%d candidates remain after portfolio exclusion", len(candidates))

        # 3. Score candidates
        candidates = self._score_candidates(candidates)

        # 4. Sort by composite_score descending
        candidates.sort(key=lambda c: c.composite_score, reverse=True)

        # 5. Build result
        result = NewcomerDiscoveryResult(
            asset_class=self.asset_class,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            candidates=candidates,
            total_candidates=len(candidates),
            summary=f"Discovered {len(candidates)} {self.asset_class} newcomer candidates",
        )

        # 6. Persist to JSON
        self._persist_result(result, self.asset_class)

        elapsed = time.time() - start_time
        logger.info(
            "Discovery pipeline for %s completed in %.2fs (%d candidates)",
            self.asset_class, elapsed, len(candidates),
        )
        return result

    def _gather_candidates(self) -> list[NewcomerCandidate]:
        """Gather candidates from universe provider and all screeners.

        Each screener is called independently; a single failure does not
        prevent others from contributing.  Deduplicated by ticker.
        """
        candidates: list[NewcomerCandidate] = []
        seen: set[str] = set()

        def _add(new: list[NewcomerCandidate]) -> None:
            for c in new:
                key = c.ticker.upper()
                if key not in seen:
                    seen.add(key)
                    candidates.append(c)

        # Universe provider
        try:
            from finwiz.scoring.discovery.universe_provider import DynamicUniverseProvider
            _add(DynamicUniverseProvider().get_candidates(self.asset_class))
        except ImportError:
            logger.warning("DynamicUniverseProvider not available (Phase 2 pending)")
        except (ValueError, OSError) as e:
            logger.warning("Universe provider failed: %s", e)
        except Exception as e:
            logger.warning("Universe provider unexpected error: %s", e)

        # IPO screener
        try:
            from finwiz.scoring.discovery.ipo_screener import IPOScreener
            _add(IPOScreener().screen(self.asset_class))
        except ImportError:
            logger.warning("IPOScreener not available (Phase 2 pending)")
        except (ValueError, OSError) as e:
            logger.warning("IPO screener failed: %s", e)
        except Exception as e:
            logger.warning("IPO screener unexpected error: %s", e)

        # Breakout detector
        try:
            from finwiz.scoring.discovery.breakout_detector import BreakoutDetector
            _add(BreakoutDetector().detect(self.asset_class))
        except ImportError:
            logger.warning("BreakoutDetector not available (Phase 2 pending)")
        except (ValueError, OSError) as e:
            logger.warning("Breakout detector failed: %s", e)
        except Exception as e:
            logger.warning("Breakout detector unexpected error: %s", e)

        # Momentum scanner
        try:
            from finwiz.scoring.discovery.momentum_scanner import MomentumScanner
            _add(MomentumScanner().scan(self.asset_class))
        except ImportError:
            logger.warning("MomentumScanner not available (Phase 2 pending)")
        except (ValueError, OSError) as e:
            logger.warning("Momentum scanner failed: %s", e)
        except Exception as e:
            logger.warning("Momentum scanner unexpected error: %s", e)

        return candidates

    def _score_candidates(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]:
        """Score each candidate via CandidateScorer.  Returns as-is if scorer unavailable."""
        try:
            from finwiz.scoring.discovery.candidate_scorer import CandidateScorer
            scorer = CandidateScorer()
            return [scorer.score(c) for c in candidates]
        except ImportError:
            logger.warning("CandidateScorer not available (Phase 2 pending)")
            return candidates
        except (ValueError, TypeError) as e:
            logger.warning("Candidate scoring failed: %s", e)
            return candidates
        except Exception as e:
            logger.warning("Candidate scoring unexpected error: %s", e)
            return candidates

    def _persist_result(self, result: NewcomerDiscoveryResult, asset_class: str) -> None:
        """Save results to ``output/discovery/newcomer_{asset_class}.json`` with ``default=str``."""
        try:
            discovery_dir = Path("output") / "discovery"
            discovery_dir.mkdir(parents=True, exist_ok=True)
            output_file = discovery_dir / f"newcomer_{asset_class}.json"
            with open(output_file, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            logger.info("Saved newcomer discovery results to %s", output_file)
        except OSError as e:
            logger.warning("Failed to write discovery results: %s", e)
        except Exception as e:
            logger.warning("Unexpected error persisting results: %s", e)

    def _to_legacy_format(self, result: NewcomerDiscoveryResult, start_time: float) -> dict[str, Any]:
        """Convert to dict format expected by DiscoveryOrchestrator.

        Args:
            result: Pipeline result to convert.
            start_time: ``time.time()`` recorded before pipeline ran.

        Returns:
            Dict with ``opportunities``, ``analysis_summary``, ``performance_metrics``.
        """
        opportunities: list[dict[str, Any]] = [
            {
                "ticker": c.ticker,
                "name": getattr(c, "name", c.ticker),
                "grade": getattr(c, "grade", ""),
                "composite_score": c.composite_score,
                "recommendation": getattr(c, "recommendation", "REVIEW"),
                "rationale": getattr(c, "rationale", ""),
            }
            for c in result.candidates
        ]
        return {
            "opportunities": opportunities,
            "analysis_summary": result.summary,
            "performance_metrics": {
                "execution_time_seconds": time.time() - start_time,
                "opportunities_found": len(opportunities),
                "cost_usd": 0.0,
                "llm_calls_made": 0,
                "method": "newcomer_discovery_pipeline",
            },
        }
