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
    """Orchestrates newcomer discovery for a single asset class."""

    def __init__(self, asset_class: str) -> None:
        self.asset_class = asset_class
        self.portfolio_tickers: set[str] = set()
        self._load_portfolio_tickers()

    # ------------------------------------------------------------------
    # Portfolio exclusion
    # ------------------------------------------------------------------

    def _load_portfolio_tickers(self) -> None:
        """Load tickers from all portfolio CSVs for exclusion."""
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
                    for row in csv.DictReader(f):
                        ticker = (row.get("Ticker") or "").strip()
                        if not ticker:
                            continue
                        if ticker.upper().startswith("YAHOO:"):
                            ticker = ticker.split(":", 1)[1]
                        upper = ticker.upper()
                        self.portfolio_tickers.add(upper)
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

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------

    def discover(self, session_id: str) -> NewcomerDiscoveryResult:
        """Run the full discovery pipeline for this asset class."""
        from finwiz.schemas.newcomer_discovery import NewcomerDiscoveryResult

        start_time = time.time()
        candidates = self._gather_candidates()
        logger.info("Gathered %d raw candidates for %s", len(candidates), self.asset_class)

        candidates = [c for c in candidates if c.ticker.upper() not in self.portfolio_tickers]
        logger.info("%d candidates remain after portfolio exclusion", len(candidates))

        candidates = self._score_candidates(candidates)
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        candidates, enrich_tried, enrich_ok = self._enrich_top_candidates(candidates)

        result = NewcomerDiscoveryResult(
            asset_class=self.asset_class, session_id=session_id,
            timestamp=datetime.now().isoformat(), candidates=candidates,
            total_candidates=len(candidates),
            summary=f"Discovered {len(candidates)} {self.asset_class} newcomer candidates",
            enrichment_attempted=enrich_tried, enrichment_succeeded=enrich_ok,
        )
        self._persist_result(result, self.asset_class)
        elapsed = time.time() - start_time
        logger.info("Discovery pipeline for %s completed in %.2fs (%d candidates)", self.asset_class, elapsed, len(candidates))
        return result

    # ------------------------------------------------------------------
    # Candidate gathering
    # ------------------------------------------------------------------

    def _gather_candidates(self) -> list[NewcomerCandidate]:
        """Gather candidates from universe provider and all screeners (deduplicated)."""
        candidates: list[NewcomerCandidate] = []
        seen: set[str] = set()

        def _add(new: list[NewcomerCandidate]) -> None:
            for c in new:
                key = c.ticker.upper()
                if key not in seen:
                    seen.add(key)
                    candidates.append(c)

        screeners: list[tuple[str, str, str]] = [
            ("finwiz.scoring.discovery.universe_provider", "DynamicUniverseProvider", "get_candidates"),
            ("finwiz.scoring.discovery.ipo_screener", "IPOScreener", "screen"),
            ("finwiz.scoring.discovery.breakout_detector", "BreakoutDetector", "detect"),
            ("finwiz.scoring.discovery.momentum_scanner", "MomentumScanner", "scan"),
        ]
        for module_path, cls_name, method_name in screeners:
            try:
                import importlib
                mod = importlib.import_module(module_path)
                cls = getattr(mod, cls_name)
                method = getattr(cls(), method_name)
                _add(method(self.asset_class))
            except ImportError:
                logger.warning("%s not available (Phase 2 pending)", cls_name)
            except (ValueError, OSError) as e:
                logger.warning("%s failed: %s", cls_name, e)
            except Exception as e:
                logger.warning("%s unexpected error: %s", cls_name, e)
        return candidates

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_candidates(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]:
        """Score each candidate via CandidateScorer.  Returns as-is if scorer unavailable."""
        try:
            from finwiz.scoring.discovery.candidate_scorer import CandidateScorer
            return [CandidateScorer().score(c) for c in candidates]
        except ImportError:
            logger.warning("CandidateScorer not available (Phase 2 pending)")
            return candidates
        except Exception as e:
            logger.warning("Candidate scoring failed: %s", e)
            return candidates

    # ------------------------------------------------------------------
    # Perplexity enrichment
    # ------------------------------------------------------------------

    def _enrich_top_candidates(
        self, candidates: list[NewcomerCandidate],
    ) -> tuple[list[NewcomerCandidate], int, int]:
        """Enrich top-scoring candidates with Perplexity research.

        Enriches candidates with ``composite_score >= ENRICHMENT_SCORE_THRESHOLD``
        (capped at ``MAX_ENRICHMENT_CANDIDATES``).  Returns candidates unchanged
        when Perplexity is disabled or fails.
        """
        from finwiz.schemas.newcomer_discovery import EnrichmentResult

        try:
            from finwiz.tools.perplexity_feature_utils import (
                initialize_perplexity_integration,
                is_perplexity_enabled,
                record_perplexity_failure,
                record_perplexity_success,
            )
        except ImportError:
            logger.warning("Perplexity feature utils not available, skipping enrichment")
            return candidates, 0, 0

        try:
            integration = initialize_perplexity_integration("newcomer_discovery")
        except Exception as e:
            logger.warning("Failed to initialize Perplexity integration: %s", e)
            return candidates, 0, 0

        if not is_perplexity_enabled(integration):
            logger.info("Perplexity enrichment disabled or unavailable, skipping")
            return candidates, 0, 0

        top = [c for c in candidates if c.composite_score >= ENRICHMENT_SCORE_THRESHOLD]
        top = sorted(top, key=lambda c: c.composite_score, reverse=True)[:MAX_ENRICHMENT_CANDIDATES]
        if not top:
            return candidates, 0, 0

        attempted, succeeded = len(top), 0
        top_tickers = {c.ticker for c in top}

        for candidate in candidates:
            if candidate.ticker not in top_tickers:
                continue
            try:
                import asyncio
                query = f"{candidate.ticker} investment analysis outlook"
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    logger.warning("Event loop running, skipping enrichment for %s", candidate.ticker)
                    continue
                result = asyncio.run(integration.search_financial_news(
                    query=query, ticker=candidate.ticker,
                    asset_type=self.asset_class, analysis_type="fundamental",
                ))
                if result.success:
                    candidate.enrichment = EnrichmentResult(
                        source="perplexity_sonar", query=query,
                        articles_found=result.total_results,
                        summary="; ".join(a.summary[:200] for a in result.results[:3] if a.summary),
                        key_insights=[a.title for a in result.results[:5]], success=True,
                    )
                    record_perplexity_success("newcomer_discovery", result.total_results, candidate.ticker)
                    succeeded += 1
                else:
                    logger.warning("Perplexity unsuccessful for %s: %s", candidate.ticker, result.error_message)
                    record_perplexity_failure("newcomer_discovery", candidate.ticker, result.error_message or "unknown")
            except Exception as e:
                logger.warning("Perplexity enrichment failed for %s: %s", candidate.ticker, e)
                try:
                    record_perplexity_failure("newcomer_discovery", candidate.ticker, str(e))
                except (ValueError, OSError):
                    pass

        logger.info("Enrichment complete: %d attempted, %d succeeded", attempted, succeeded)
        return candidates, attempted, succeeded

    # ------------------------------------------------------------------
    # Persistence & format conversion
    # ------------------------------------------------------------------

    def _persist_result(self, result: NewcomerDiscoveryResult, asset_class: str) -> None:
        """Save results to ``output/discovery/newcomer_{asset_class}.json``."""
        try:
            discovery_dir = Path("output") / "discovery"
            discovery_dir.mkdir(parents=True, exist_ok=True)
            out = discovery_dir / f"newcomer_{asset_class}.json"
            with open(out, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            logger.info("Saved newcomer discovery results to %s", out)
        except OSError as e:
            logger.warning("Failed to write discovery results: %s", e)
        except Exception as e:
            logger.warning("Unexpected error persisting results: %s", e)

    def _to_legacy_format(self, result: NewcomerDiscoveryResult, start_time: float) -> dict[str, Any]:
        """Convert to dict format expected by DiscoveryOrchestrator."""
        opportunities: list[dict[str, Any]] = [
            {
                "ticker": c.ticker, "name": getattr(c, "name", c.ticker),
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
                "cost_usd": 0.0, "llm_calls_made": 0,
                "method": "newcomer_discovery_pipeline",
            },
        }
