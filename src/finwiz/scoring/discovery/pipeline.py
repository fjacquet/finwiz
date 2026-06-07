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
from typing import TYPE_CHECKING, Any, Literal

from finwiz.tools.logger import get_logger

if TYPE_CHECKING:
    from finwiz.schemas.newcomer_discovery import NewcomerCandidate, NewcomerDiscoveryResult

logger = get_logger(__name__)

ENRICHMENT_SCORE_THRESHOLD = 0.80
MAX_ENRICHMENT_CANDIDATES = 10


class NewcomerDiscoveryPipeline:
    """Orchestrates newcomer discovery for a single asset class."""

    def __init__(self, asset_class: Literal["stock", "etf", "crypto"]) -> None:
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

    # Cap per-asset-class candidates surfaced (whole-universe scoring can be wide).
    MAX_SURFACED_CANDIDATES = 100

    def discover(self, session_id: str) -> NewcomerDiscoveryResult:
        """Run the full discovery pipeline for this asset class.

        When the ``portfolio_aware_discovery`` flag is enabled, scores the whole
        universe by ``standalone_factor x portfolio_fit`` (recall un-gated).
        Otherwise falls back to the legacy signal-gated path.
        """
        from finwiz.config.features.flags import is_feature_enabled
        from finwiz.schemas.newcomer_discovery import NewcomerDiscoveryResult

        start_time = time.time()

        if is_feature_enabled("portfolio_aware_discovery"):
            candidates = self._gather_portfolio_aware_candidates()
        else:
            candidates = self._gather_candidates()
            logger.info("Gathered %d raw candidates for %s", len(candidates), self.asset_class)
            candidates = [c for c in candidates if c.ticker.upper() not in self.portfolio_tickers]
            logger.info("%d candidates remain after portfolio exclusion", len(candidates))
            candidates = self._score_candidates(candidates)

        # Drop weak grades (D/D±/F) on BOTH paths. The portfolio-aware cascade
        # un-gates *recall* (breakout/momentum become factor inputs, not filters)
        # but must still EXCLUDE noise from the surfaced opportunity list rather
        # than emit it low-graded — otherwise the a_plus_*/consolidated outputs
        # fill with F/D candidates. See feedback rule: filter, don't low-grade.
        candidates = self._filter_actionable(candidates)

        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        candidates = candidates[: self.MAX_SURFACED_CANDIDATES]
        candidates, enrich_tried, enrich_ok = self._enrich_top_candidates(candidates)

        result = NewcomerDiscoveryResult(
            asset_class=self.asset_class,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            candidates=candidates,
            total_candidates=len(candidates),
            summary=f"Discovered {len(candidates)} {self.asset_class} newcomer candidates",
            enrichment_attempted=enrich_tried,
            enrichment_succeeded=enrich_ok,
        )
        self._persist_result(result, self.asset_class)
        elapsed = time.time() - start_time
        logger.info("Discovery pipeline for %s completed in %.2fs (%d candidates)", self.asset_class, elapsed, len(candidates))
        return result

    # ------------------------------------------------------------------
    # Candidate gathering
    # ------------------------------------------------------------------

    def _gather_candidates(self) -> list[NewcomerCandidate]:
        """Gather candidates from universe provider and signal-based screeners.

        Pipeline:
          1. Build ticker universe via DynamicUniverseProvider (excludes portfolio).
          2. Run universe-consuming screeners (Breakout, Momentum) against it.
          3. Deduplicate candidates by upper-cased ticker.

        IPOScreener is intentionally excluded: SEC S-1 filings have no
        trading history or fundamentals, get a hardcoded composite of 0.5,
        and uniformly grade F — they are events, not investable signals.
        """
        candidates: list[NewcomerCandidate] = []
        seen: set[str] = set()

        def _add(new: list[NewcomerCandidate]) -> None:
            for c in new:
                key = c.ticker.upper()
                if key not in seen:
                    seen.add(key)
                    candidates.append(c)

        # Step 1: build ticker universe (excludes portfolio holdings).
        universe: list[str] = []
        try:
            from finwiz.discovery.universe_provider import DynamicUniverseProvider

            universe = DynamicUniverseProvider().get_universe(
                self.asset_class,
                exclude_tickers=list(self.portfolio_tickers),
            )
        except ImportError as e:
            logger.warning("DynamicUniverseProvider import failed: %s", e)
        except Exception as e:
            logger.warning("DynamicUniverseProvider failed: %s", e)

        # Step 2: universe-consuming screeners (Breakout, Momentum).
        if universe:
            try:
                from finwiz.discovery.breakout_detector import BreakoutDetector

                _add(BreakoutDetector().detect(universe, self.asset_class))
            except ImportError as e:
                logger.warning("BreakoutDetector import failed: %s", e)
            except (ValueError, OSError) as e:
                logger.warning("BreakoutDetector failed: %s", e)
            except Exception as e:
                logger.warning("BreakoutDetector unexpected error: %s", e)

            try:
                from finwiz.discovery.momentum_scanner import MomentumScanner

                _add(MomentumScanner().scan(universe, self.asset_class))
            except ImportError as e:
                logger.warning("MomentumScanner import failed: %s", e)
            except (ValueError, OSError) as e:
                logger.warning("MomentumScanner failed: %s", e)
            except Exception as e:
                logger.warning("MomentumScanner unexpected error: %s", e)

        return candidates

    # ------------------------------------------------------------------
    # Portfolio-aware wide scoring (Portfolio-Aware Opportunity Cascade)
    # ------------------------------------------------------------------

    def _gather_portfolio_aware_candidates(self) -> list[NewcomerCandidate]:
        """Score the WHOLE universe by ``standalone_factor x portfolio_fit``.

        Recall is no longer gated by breakout/momentum signals: every universe
        ticker with usable price data is scored. Breakout/Momentum still run,
        but only to supply a richer standalone score for the names they flag —
        they are factor producers, not filters.
        """
        from finwiz.discovery.market_data import factor_score_from_returns, get_returns, get_sectors
        from finwiz.orchestrators.gap_profile_orchestrator import load_gap_profile
        from finwiz.schemas.newcomer_discovery import NewcomerCandidate
        from finwiz.scoring.discovery.portfolio_fit_scorer import PortfolioFitScorer
        from finwiz.scoring.grading_system import score_to_grade

        universe = self._build_universe()
        if not universe:
            logger.warning("Empty universe for %s; no candidates", self.asset_class)
            return []
        logger.info("Portfolio-aware scoring of %d %s universe tickers", len(universe), self.asset_class)

        profile = load_gap_profile()
        fit_scorer = PortfolioFitScorer()
        returns = get_returns(universe, self.asset_class)
        sectors = get_sectors(universe, self.asset_class)
        signal_scores, signal_meta = self._signal_standalone_scores(universe)

        candidates: list[NewcomerCandidate] = []
        for ticker in universe:
            key = ticker.upper()
            series = returns.get(key)
            factor = signal_scores.get(key)
            if factor is None:
                factor = factor_score_from_returns(series)
            if factor is None:
                continue  # no usable data -> cannot score, excluded (logged in bulk)

            fit, gap = fit_scorer.score(
                profile,
                sector=sectors.get(key),
                returns=series,
                risk_score=None,
            )
            # fit is None when no portfolio-fit signal is computable (empty gap
            # profile or no usable inputs): degrade to the standalone factor score
            # rather than multiplying by a neutral 0.5, which would halve every
            # score and make A/A+ grades + the 0.80 enrichment cutoff unreachable.
            final = factor if fit is None else max(0.0, min(1.0, factor * fit))
            grade_info = score_to_grade(final)
            fit_desc = "n/a (standalone)" if fit is None else f"{fit:.2f}"
            meta = signal_meta.get(key, {})
            candidates.append(
                NewcomerCandidate(
                    ticker=ticker,
                    name=str(meta.get("name", ticker)),
                    asset_class=self.asset_class,
                    source=str(meta.get("source", "universe")),
                    composite_score=final,
                    grade=grade_info.grade,
                    recommendation=grade_info.action,
                    portfolio_fit_score=fit,
                    gap_filled=gap,
                    momentum_score=factor,
                    sector=sectors.get(key),
                    rationale=(f"factor {factor:.2f} x portfolio_fit {fit_desc} = {final:.2f}" + (f"; fills {gap}" if gap else "")),
                )
            )
        logger.info("Portfolio-aware scoring produced %d scored %s candidates", len(candidates), self.asset_class)
        return candidates

    def _build_universe(self) -> list[str]:
        """Build the (portfolio-excluded) ticker universe for this asset class."""
        try:
            from finwiz.discovery.universe_provider import DynamicUniverseProvider

            return DynamicUniverseProvider().get_universe(
                self.asset_class,
                exclude_tickers=list(self.portfolio_tickers),
            )
        except Exception as e:
            logger.warning("Universe build failed for %s: %s", self.asset_class, e)
            return []

    def _signal_standalone_scores(self, universe: list[str]) -> tuple[dict[str, float], dict[str, dict[str, Any]]]:
        """Run Breakout/Momentum as factor producers (not gates).

        Returns ``(scores, meta)`` keyed by upper-cased ticker, where ``scores``
        is the best signal composite for flagged names and ``meta`` carries
        ``name``/``source`` for richer candidate display. Names not flagged are
        simply absent (they fall back to the price-derived factor score).
        """
        scores: dict[str, float] = {}
        meta: dict[str, dict[str, Any]] = {}

        def _absorb(found: list[NewcomerCandidate]) -> None:
            for c in found:
                key = c.ticker.upper()
                if c.composite_score > scores.get(key, 0.0):
                    scores[key] = c.composite_score
                    meta[key] = {"name": c.name or c.ticker, "source": c.source or "signal"}

        try:
            from finwiz.discovery.breakout_detector import BreakoutDetector

            _absorb(BreakoutDetector().detect(universe, self.asset_class))
        except Exception as e:
            logger.warning("BreakoutDetector failed (non-fatal): %s", e)
        try:
            from finwiz.discovery.momentum_scanner import MomentumScanner

            _absorb(MomentumScanner().scan(universe, self.asset_class))
        except Exception as e:
            logger.warning("MomentumScanner failed (non-fatal): %s", e)
        return scores, meta

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_candidates(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]:
        """Score and grade candidates via CandidateScorer.  Returns as-is if scorer unavailable."""
        if not candidates:
            return candidates
        try:
            from finwiz.discovery.candidate_scorer import CandidateScorer

            return CandidateScorer().score_and_grade(candidates)
        except ImportError as e:
            logger.warning("CandidateScorer import failed: %s", e)
            return candidates
        except Exception as e:
            logger.warning("Candidate scoring failed: %s", e)
            return candidates

    def _filter_actionable(self, candidates: list[NewcomerCandidate]) -> list[NewcomerCandidate]:
        """Drop D/F candidates from the opportunity surface (grade<C dropped)."""
        if not candidates:
            return candidates
        try:
            from finwiz.discovery.candidate_scorer import filter_actionable_candidates

            return filter_actionable_candidates(candidates)
        except ImportError as e:
            logger.warning("filter_actionable_candidates import failed: %s", e)
            return candidates

    # ------------------------------------------------------------------
    # Perplexity enrichment
    # ------------------------------------------------------------------

    def _enrich_top_candidates(
        self,
        candidates: list[NewcomerCandidate],
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
                result = asyncio.run(
                    integration.search_financial_news(
                        query=query,
                        ticker=candidate.ticker,
                        asset_type=self.asset_class,
                        analysis_type="fundamental",
                    )
                )
                if result.success:
                    candidate.enrichment = EnrichmentResult(
                        source="perplexity_sonar",
                        query=query,
                        articles_found=result.total_results,
                        summary="; ".join(a.summary[:200] for a in result.results[:3] if a.summary),
                        key_insights=[a.title for a in result.results[:5]],
                        success=True,
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
                "ticker": c.ticker,
                "name": getattr(c, "name", c.ticker),
                "grade": getattr(c, "grade", ""),
                "composite_score": c.composite_score,
                "recommendation": getattr(c, "recommendation", "REVIEW"),
                "rationale": getattr(c, "rationale", ""),
                "portfolio_fit_score": getattr(c, "portfolio_fit_score", None),
                "gap_filled": getattr(c, "gap_filled", None),
                "sector": getattr(c, "sector", None),
                "asset_class": getattr(c, "asset_class", self.asset_class),
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
