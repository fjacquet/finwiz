"""Report enrichment mixin: discovery/sentiment/strategic/calendar gathering + Python report generation."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from finwiz.schemas.portfolio_review import HoldingDecision, PortfolioReview

if TYPE_CHECKING:
    from finwiz.flow_state import FinwizState


class ReportEnrichmentMixin:
    """Gathers enrichment inputs (discovery, sentiment, strategic, calendar) and renders the Python report."""

    # Provided by ReportingOrchestrator.__init__
    state: FinwizState
    logger: Any

    def _read_json_file(self, file_path: str) -> dict[str, Any]:  # pragma: no cover - provided by data-loading mixin
        """Declared for type-checking; implemented by ReportDataLoadingMixin."""
        raise NotImplementedError

    def _read_discovery_results(self) -> dict[str, Any] | None:
        """Read discovery results from JSON file."""
        try:
            self.logger.info("Reading discovery results from JSON file...")

            # Try to load consolidated discovery file
            discovery_path = Path("output/discovery/consolidated_discovery.json")
            if discovery_path.exists():
                data = self._read_json_file(str(discovery_path))
                self.logger.info(f"Loaded discovery results: {len(data.get('opportunities', []))} opportunities")
                return data

            self.logger.warning("No discovery results file found")
            return None

        except Exception as e:
            self.logger.error(f"Failed to read discovery results: {e}")
            return None

    def _generate_python_report(
        self,
        portfolio_review: PortfolioReview,
        deep_analysis_results: dict[str, Any] | None,
    ) -> str:
        """Generate Python-based HTML report."""
        from finwiz.reporting.python_report_generator import generate_python_report

        session_id = self.state.session_id or "default"

        # Load discovery results if available
        discovery_results = self._read_discovery_results()

        # Load stress test results from state if available
        stress_test_results: list[dict[str, Any]] | None = getattr(self.state, "stress_test_results", None) or None

        # Load macro snapshot from state (set by DeepAnalysisOrchestrator in Plan 16-01)
        macro_snapshot: dict | None = getattr(self.state, "macro_snapshot", None) or None

        # Read every enriched JSON file once; the three extractors below all
        # distill from this single parsed set (avoids re-globbing + re-parsing 3x).
        # Filter to the current portfolio's tickers so leftover *_enriched.json from
        # a prior run (the non-session-scoped output/{asset_class} dir is never
        # cleared) can't surface stale holdings in sentiment/strategic/insights.
        enriched_records = self._filter_records_to_holdings(self._iter_enriched_records(), portfolio_review)

        # Extract holdings sentiment from enriched JSON files
        holdings_sentiment = self._extract_holdings_sentiment(deep_analysis_results, records=enriched_records)

        # Collect economic calendar data
        economic_calendar = self._collect_economic_calendar(portfolio_review)

        # Synthesize portfolio-level strategic posture from per-holding strategic analyses (best-effort).
        portfolio_strategic_posture = self._synthesize_portfolio_strategic(deep_analysis_results, records=enriched_records, holdings=portfolio_review.holdings)

        # Distill per-holding "quintessence" cards from the costly enriched JSON (best-effort).
        holdings_insights = self._extract_holdings_insights(deep_analysis_results, records=enriched_records)

        # Gap-fill opportunity shortlist: prefer state, fall back to the on-disk file.
        opportunity_shortlist = self._load_opportunity_shortlist()

        # Real LLM cost read live from the token monitor (state.llm_* is populated after report()).
        cost_summary = self._read_live_cost_summary()

        report_path = generate_python_report(
            portfolio_review=portfolio_review,
            deep_analysis_results=deep_analysis_results,
            session_id=session_id,
            discovery_results=discovery_results,
            stress_test_results=stress_test_results,
            holdings_sentiment=holdings_sentiment,
            macro_snapshot=macro_snapshot,
            economic_calendar=economic_calendar,
            portfolio_strategic_posture=portfolio_strategic_posture,
            run_ledger=getattr(self.state, "run_ledger", None),
            deep_analysis_coverage=getattr(self.state, "deep_analysis_coverage", None),
            holdings_insights=holdings_insights,
            opportunity_shortlist=opportunity_shortlist,
            cost_summary=cost_summary,
        )

        self._write_posture_page(
            report_path,
            portfolio_strategic_posture,
            holdings_strategic=self._extract_holdings_strategic(deep_analysis_results, records=enriched_records),
        )

        return report_path

    def _write_posture_page(
        self,
        report_path: str,
        portfolio_strategic_posture: dict[str, Any] | None,
        *,
        holdings_strategic: dict[str, dict] | None,
    ) -> None:
        """Write the dedicated posture page beside the family report.

        Best-effort by design: the family report is the primary deliverable and
        must be returned regardless of whether this companion page could be
        written. The failure is still logged -- at warning level, with the
        traceback -- rather than swallowed silently: a bare ``except Exception``
        in this same mixin once turned a `TypeError` into a silently missing
        posture section (Task 7). Catching broadly here is deliberate (an
        uncaught exception would propagate to the caller's outer handler and
        fail the whole report, even though the family HTML is already on disk),
        but catching broadly must not mean discarding the traceback -- without
        it, a genuine programming error is a single log line with no way to
        diagnose it from the log alone.
        """
        if not portfolio_strategic_posture:
            return
        try:
            from finwiz.reporting.sections.posture_page import generate_posture_page

            posture_path = Path(report_path).parent / "finwiz_posture_strategique.html"
            posture_path.write_text(
                generate_posture_page(portfolio_strategic_posture, holdings_strategic=holdings_strategic),
                encoding="utf-8",
            )
            self.logger.info("Posture page written: %s", posture_path)
        except Exception as e:
            self.logger.warning("Failed to write posture page beside %s: %s", report_path, e, exc_info=True)

    def _load_opportunity_shortlist(self) -> Any:
        """Return the gap-fill opportunity shortlist (state preferred, file fallback).

        Best-effort: returns None on any failure so the report still renders.
        """
        shortlist = getattr(self.state, "opportunity_shortlist", None)
        if shortlist:
            return shortlist
        try:
            shortlist_path = Path("output/discovery/opportunity_shortlist.json")
            if shortlist_path.exists():
                return json.loads(shortlist_path.read_text())
        except Exception as e:
            self.logger.debug(f"Could not load opportunity shortlist file: {e}")
        return None

    def _read_live_cost_summary(self) -> dict[str, Any] | None:
        """Read the live LLM cost summary from the token monitor (best-effort).

        ``state.llm_total_cost`` / ``llm_cost_summary`` are populated only *after*
        report generation, so we read the monitor directly at report time.
        """
        try:
            from finwiz.infrastructure.monitoring.litellm_callback import get_token_monitor

            monitor = get_token_monitor()
            if monitor is None:
                return None
            return monitor.get_cost_summary()
        except Exception as e:
            self.logger.debug(f"Live cost summary unavailable: {e}")
            return None

    def _iter_enriched_files(self) -> Iterator[tuple[str, Path]]:
        """Yield ``(asset_class, json_file_path)`` for the current run's enriched files.

        Single source of truth for *locating* per-holding enriched JSON, shared by
        :meth:`_iter_enriched_records` and by ``CrewHtmlMixin.generate_enriched_html_reports``
        so the directory list cannot drift between them.

        ``DeepAnalysisOrchestrator._store_enriched_analysis`` writes the canonical
        files to ``output/{asset_class}/{ticker}_enriched.json``; the
        ``output/enriched/...`` dirs are session-scoped overrides used by some
        pipelines. Per asset class, probe in priority order and use **only** the
        first directory that exists, so a prior run's files in a lower-priority
        directory don't leak in.
        """
        session_id = self.state.session_id or "default"
        for asset_class in ["stock", "etf", "crypto"]:
            for base_dir in [
                f"output/enriched/{session_id}/{asset_class}",
                f"output/enriched/{asset_class}",
                f"output/{asset_class}",
            ]:
                enriched_dir = Path(base_dir)
                if not enriched_dir.exists():
                    continue
                yield from ((asset_class, json_file) for json_file in enriched_dir.glob("*_enriched.json"))
                # First existing dir wins (highest priority); stop probing fallbacks.
                break

    def _iter_enriched_records(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """Yield ``(asset_class, enriched_json)`` for the current run's enriched files.

        Parses each file located by :meth:`_iter_enriched_files`. Fail-soft:
        unreadable/invalid files are skipped with a debug log.
        """
        for asset_class, json_file in self._iter_enriched_files():
            try:
                data = json.loads(json_file.read_text())
            except Exception as e:
                self.logger.debug(f"Could not read enriched file {json_file}: {e}")
                continue
            if isinstance(data, dict):
                yield asset_class, data

    @staticmethod
    def _filter_records_to_holdings(
        records: Iterator[tuple[str, dict[str, Any]]] | list[tuple[str, dict[str, Any]]],
        portfolio_review: PortfolioReview,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Keep only enriched records whose ticker is in the current portfolio.

        Guards against stale ``*_enriched.json`` from a prior run leaking in via the
        non-session-scoped ``output/{asset_class}`` dir. When the portfolio carries
        no tickers, no filter is applied (degrades to the unfiltered set).
        """
        tickers = {h.ticker for h in portfolio_review.holdings if getattr(h, "ticker", None)}
        if not tickers:
            return list(records)
        return [(asset_class, data) for asset_class, data in records if data.get("ticker") in tickers]

    def _extract_holdings_insights(
        self,
        deep_analysis_results: dict[str, Any] | None,
        records: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> dict[str, dict] | None:
        """Distill per-holding "quintessence" insight cards from enriched JSON files.

        For each ticker, distills the most decision-relevant fields from
        ``data["qualitative"]`` into a flat dict consumed by
        :func:`finwiz.reporting.sections.insights.generate_holdings_insight_cards`.

        ``records`` is the shared parsed output of :meth:`_iter_enriched_records`;
        when omitted (e.g. direct/test calls) it is read on demand.

        Returns ``{ticker: distilled_dict}`` or ``None`` when no holding carries
        qualitative data (ETF/crypto-only or unanalyzed portfolios).
        """
        if not deep_analysis_results:
            return None

        insights: dict[str, dict] = {}
        for asset_class, data in self._iter_enriched_records() if records is None else records:
            ticker = data.get("ticker")
            qual = data.get("qualitative")
            if not ticker or not isinstance(qual, dict):
                continue
            distilled = self._distill_qualitative(qual)
            if distilled:
                distilled["report_link"] = f"{asset_class}/{ticker}_report.html"
                distilled["grade"] = data.get("final_grade", "")
                insights[ticker] = distilled

        return insights if insights else None

    @staticmethod
    def _distill_qualitative(qual: dict[str, Any]) -> dict[str, Any]:
        """Flatten the most decision-relevant qualitative fields into a card dict.

        Pure dict access (fail-soft): any absent sub-object simply omits its keys.
        """

        def _section(name: str) -> dict[str, Any]:
            val = qual.get(name)
            return val if isinstance(val, dict) else {}

        def _first(items: Any) -> str:
            return str(items[0]) if isinstance(items, list) and items else ""

        synth = _section("investment_synthesis")
        sec = _section("sec_insights")
        fund = _section("fundamental_context")
        risks = _section("contextual_risks")
        tech = _section("technical_strategy")
        fact = _section("fact_pack")

        # Key risks: first of regulatory / competitive / operational (best signal, no flood).
        key_risks = [
            r
            for r in (
                _first(risks.get("regulatory_risks")),
                _first(risks.get("competitive_risks")),
                _first(risks.get("operational_risks")),
            )
            if r
        ]

        action_plan = synth.get("action_plan")
        action_plan = action_plan if isinstance(action_plan, dict) else {}
        immediate_actions = action_plan.get("immediate_actions")

        distilled: dict[str, Any] = {
            "thesis": synth.get("investment_thesis", ""),
            "bull_case": synth.get("bull_case", ""),
            "bear_case": synth.get("bear_case", ""),
            "scenario_probabilities": synth.get("scenario_probabilities"),
            "final_recommendation": synth.get("final_recommendation", "HOLD"),
            "recommendation_confidence": synth.get("recommendation_confidence", ""),
            "immediate_actions": (immediate_actions or [])[:2],
            "moat": _first(sec.get("competitive_advantages")),
            "top_sec_risk": _first(sec.get("risk_factors")),
            "growth_drivers": (fund.get("growth_drivers") or [])[:2],
            "competitive_positioning": fund.get("competitive_positioning", ""),
            "key_risks": key_risks,
            "price_target_rationale": tech.get("entry_exit_strategy", ""),
        }

        if fact:
            distilled["fact_pack"] = {
                "corporate_structure": fact.get("corporate_structure", ""),
                "recent_events": (fact.get("recent_events") or [])[:3],
                "leadership": fact.get("leadership", ""),
                "freshness": fact.get("freshness", ""),
                "source_citations": (fact.get("source_citations") or [])[:5],
            }

        # Drop a card that distilled to nothing meaningful (no thesis, no facts, no recommendation signal).
        has_signal = any(distilled.get(k) for k in ("thesis", "bull_case", "bear_case", "moat", "top_sec_risk", "competitive_positioning")) or "fact_pack" in distilled
        return distilled if has_signal else {}

    def _extract_holdings_strategic(
        self,
        deep_analysis_results: dict[str, Any] | None,
        records: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> dict[str, dict] | None:
        """Walk enriched JSON files and pull each holding's StrategicAnalysis dict.

        ``records`` is the shared parsed output of :meth:`_iter_enriched_records`;
        when omitted it is read on demand. Returns ``{ticker: dict}`` where each
        value is the raw :class:`StrategicAnalysis` model_dump (or None if no
        strategic analyses were generated, e.g. ETF/crypto-only portfolios).
        """
        if not deep_analysis_results:
            return None
        strategic: dict[str, dict] = {}
        for _asset_class, data in self._iter_enriched_records() if records is None else records:
            ticker = data.get("ticker")
            qual = data.get("qualitative") or {}
            sa = qual.get("strategic_analysis") if isinstance(qual, dict) else None
            if ticker and sa:
                strategic[ticker] = sa
        return strategic if strategic else None

    def _strategic_coverage(
        self,
        holdings: list[HoldingDecision],
        covered_tickers: set[str],
    ) -> tuple[int, int, float, list[str]]:
        """Derive (holdings_covered, holdings_total, value_covered_pct, uncovered_tickers) honestly.

        ``holdings`` is ``portfolio_review.holdings`` — the authoritative list
        of every holding in the *current* portfolio (priced or not). It is the
        true denominator: unlike ``deep_analysis_results``, it can't silently
        omit a holding that simply wasn't re-analyzed this run.

        ``value_covered_pct`` is weighted by ``HoldingDecision.eur_value`` so a
        single large uncovered position can't hide behind a healthy
        count-based ratio — the report this task exists to fix printed "71%"
        off 1 of 64 holdings, and by count alone there is no way to tell
        whether the missing 63 were 2% of the portfolio's value or 40% of it.
        When *no* holding in the portfolio carries a priced ``eur_value``
        (e.g. an unpriced CSV import), there is nothing to weight by value —
        Python does not invent one. It degrades to the honest count-based
        ratio and logs the degrade explicitly, rather than defaulting to a
        fabricated 100%.
        """
        all_tickers = sorted({h.ticker for h in holdings if h.ticker})
        holdings_total = len(all_tickers)
        covered_tickers = covered_tickers & set(all_tickers)
        holdings_covered = len(covered_tickers)
        uncovered_tickers = sorted(set(all_tickers) - covered_tickers)

        priced_values = {h.ticker: h.eur_value for h in holdings if h.ticker and h.eur_value is not None}
        total_priced_value = sum(priced_values.values())
        if total_priced_value > 0:
            covered_value = sum(v for t, v in priced_values.items() if t in covered_tickers)
            value_covered_pct = round(100.0 * covered_value / total_priced_value, 1)
        else:
            value_covered_pct = round(100.0 * holdings_covered / holdings_total, 1) if holdings_total else 0.0
            self.logger.warning(
                "No priced holdings (eur_value) in the portfolio; value_covered_pct "
                "falls back to the count-based coverage ratio (%d/%d) as an honest "
                "proxy instead of a fabricated percentage.",
                holdings_covered,
                holdings_total,
            )
        return holdings_covered, holdings_total, value_covered_pct, uncovered_tickers

    def _synthesize_portfolio_strategic(
        self,
        deep_analysis_results: dict[str, Any] | None,
        records: list[tuple[str, dict[str, Any]]] | None = None,
        *,
        holdings: list[HoldingDecision],
    ) -> dict | None:
        """Synthesize a portfolio-level :class:`PortfolioStrategicPosture` via Perplexity.

        ``holdings`` (``portfolio_review.holdings``) is required, not optional:
        it is the only source of the true portfolio denominator and of the
        per-holding EUR values that make ``value_covered_pct`` honest rather
        than a count-based approximation.

        Best-effort for *runtime* failures (no strategic data, API down, parse
        error) — those still return None so the rest of the report renders.
        Programming errors (wrong call signature, wrong attribute) are NOT
        swallowed: a prior version of this method wrapped its whole body in a
        bare ``except Exception`` that turned a `TypeError` from a stale call
        site into a silent "non-fatal" warning, dropping the entire strategic
        posture section with no visible failure.
        """
        try:
            holdings_strategic_dicts = self._extract_holdings_strategic(deep_analysis_results, records=records)
            if not holdings_strategic_dicts:
                return None

            from finwiz.analysis.strategic_research import synthesize_portfolio_posture_sync
            from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

            holdings_models: dict[str, StrategicAnalysis] = {}
            for ticker, sa_dict in holdings_strategic_dicts.items():
                try:
                    model = StrategicAnalysis.model_validate(sa_dict)
                except Exception as e:
                    self.logger.debug(f"Skipping {ticker} for portfolio synthesis (invalid schema): {e}")
                    continue
                # Validating is not the same as carrying evidence. All three
                # framework fields are Optional, so an all-None blob -- what a
                # fully-failed strategic gather used to write to disk, and what
                # legacy *_enriched.json files still contain -- validates
                # cleanly and would otherwise be counted as covered by count
                # AND by value, named in no gap list. composite_strategic_score
                # is None exactly when no framework produced a rating; it is
                # the same predicate stages/synthesize.py uses before
                # recomputing a holding's grade off strategic data.
                if model.composite_strategic_score is None:
                    self.logger.warning("Excluding %s from strategic coverage: no framework produced a rating (all-None strategic_analysis)", ticker)
                    continue
                holdings_models[ticker] = model

            if not holdings_models:
                self.logger.warning("No holding carries usable strategic evidence; skipping portfolio posture synthesis rather than synthesizing one from empty objects")
                return None

            holdings_covered, holdings_total, value_covered_pct, uncovered_tickers = self._strategic_coverage(holdings, set(holdings_models))

            posture = synthesize_portfolio_posture_sync(
                holdings_models,
                holdings_covered=holdings_covered,
                holdings_total=holdings_total,
                value_covered_pct=value_covered_pct,
                uncovered_tickers=uncovered_tickers,
            )
            if posture is None:
                self.logger.info("Portfolio strategic synthesis returned no posture")
                return None
            return posture.model_dump(mode="json")
        except (TypeError, AttributeError):
            # Programming errors, not runtime/API failures — let them propagate
            # instead of being logged as "non-fatal" and silently dropping the
            # whole section.
            raise
        except Exception as e:
            self.logger.warning(f"Portfolio strategic synthesis failed (non-fatal): {e}")
            return None

    def _extract_holdings_sentiment(
        self,
        deep_analysis_results: dict[str, Any] | None,
        records: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> dict[str, dict] | None:
        """Extract sentiment_summary from enriched JSON files for all holdings.

        Scans enriched JSON files for sentiment_summary data added by Plan 16-01.
        ``records`` is the shared parsed output of :meth:`_iter_enriched_records`;
        when omitted it is read on demand.

        Returns:
            Dict mapping ticker -> sentiment_summary dict, or None if no data found.
        """
        if not deep_analysis_results:
            return None

        sentiment_data: dict[str, dict] = {}
        for _asset_class, data in self._iter_enriched_records() if records is None else records:
            ticker = data.get("ticker")
            summary = data.get("sentiment_summary")
            if ticker and summary and isinstance(summary, dict):
                sentiment_data[ticker] = summary

        return sentiment_data if sentiment_data else None

    def _collect_economic_calendar(self, portfolio_review: PortfolioReview) -> dict | None:
        """Collect economic calendar data for report rendering.

        Returns:
            Dict with economic_events and earnings_events, or None.
        """
        try:
            from finwiz.data.sentiment_collector import SentimentMacroCollector

            tickers = [h.ticker for h in portfolio_review.holdings if h.ticker]
            collector = SentimentMacroCollector()
            return collector.collect_economic_calendar(tickers=tickers)
        except Exception as e:
            self.logger.debug(f"Economic calendar collection skipped: {e}")
            return None
