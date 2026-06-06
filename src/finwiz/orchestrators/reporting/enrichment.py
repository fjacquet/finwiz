"""Report enrichment mixin: discovery/sentiment/strategic/calendar gathering + Python report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from finwiz.schemas.portfolio_review import PortfolioReview

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

        # Extract holdings sentiment from enriched JSON files
        holdings_sentiment = self._extract_holdings_sentiment(deep_analysis_results)

        # Collect economic calendar data
        economic_calendar = self._collect_economic_calendar(portfolio_review)

        # Synthesize portfolio-level strategic posture from per-holding strategic analyses (best-effort).
        portfolio_strategic_posture = self._synthesize_portfolio_strategic(deep_analysis_results)

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
        )

        return report_path

    def _extract_holdings_strategic(self, deep_analysis_results: dict[str, Any] | None) -> dict[str, dict] | None:
        """Walk enriched JSON files and pull each holding's StrategicAnalysis dict.

        Mirrors :meth:`_extract_holdings_sentiment`. Returns ``{ticker: dict}`` where
        each value is the raw :class:`StrategicAnalysis` model_dump (or None if no
        strategic analyses were generated, e.g. ETF/crypto-only portfolios).
        """
        if not deep_analysis_results:
            return None
        strategic: dict[str, dict] = {}
        session_id = self.state.session_id or "default"
        for asset_class in ["stock", "etf", "crypto"]:
            for base_dir in [f"output/enriched/{session_id}/{asset_class}", f"output/enriched/{asset_class}"]:
                enriched_dir = Path(base_dir)
                if not enriched_dir.exists():
                    continue
                for json_file in enriched_dir.glob("*_enriched.json"):
                    try:
                        data = json.loads(json_file.read_text())
                        ticker = data.get("ticker")
                        qual = data.get("qualitative") or {}
                        sa = qual.get("strategic_analysis") if isinstance(qual, dict) else None
                        if ticker and sa:
                            strategic[ticker] = sa
                    except Exception as e:
                        self.logger.debug(f"Could not extract strategic from {json_file}: {e}")
        return strategic if strategic else None

    def _synthesize_portfolio_strategic(self, deep_analysis_results: dict[str, Any] | None) -> dict | None:
        """Synthesize a portfolio-level :class:`PortfolioStrategicPosture` via Perplexity.

        Best-effort: any failure (no strategic data, API down, parse error) returns
        None so the rest of the report still renders.
        """
        try:
            holdings_strategic_dicts = self._extract_holdings_strategic(deep_analysis_results)
            if not holdings_strategic_dicts:
                return None

            from finwiz.analysis.strategic_research import synthesize_portfolio_posture_sync
            from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

            holdings_models: dict[str, StrategicAnalysis] = {}
            for ticker, sa_dict in holdings_strategic_dicts.items():
                try:
                    holdings_models[ticker] = StrategicAnalysis.model_validate(sa_dict)
                except Exception as e:
                    self.logger.debug(f"Skipping {ticker} for portfolio synthesis (invalid schema): {e}")

            if not holdings_models:
                return None

            posture = synthesize_portfolio_posture_sync(holdings_models)
            if posture is None:
                self.logger.info("Portfolio strategic synthesis returned no posture")
                return None
            return posture.model_dump(mode="json")
        except Exception as e:
            self.logger.warning(f"Portfolio strategic synthesis failed (non-fatal): {e}")
            return None

    def _extract_holdings_sentiment(self, deep_analysis_results: dict[str, Any] | None) -> dict[str, dict] | None:
        """Extract sentiment_summary from enriched JSON files for all holdings.

        Scans enriched JSON files for sentiment_summary data added by Plan 16-01.

        Returns:
            Dict mapping ticker -> sentiment_summary dict, or None if no data found.
        """
        if not deep_analysis_results:
            return None

        sentiment_data: dict[str, dict] = {}
        session_id = self.state.session_id or "default"

        for asset_class in ["stock", "etf", "crypto"]:
            for base_dir in [f"output/enriched/{session_id}/{asset_class}", f"output/enriched/{asset_class}"]:
                enriched_dir = Path(base_dir)
                if not enriched_dir.exists():
                    continue
                for json_file in enriched_dir.glob("*_enriched.json"):
                    try:
                        data = json.loads(json_file.read_text())
                        ticker = data.get("ticker")
                        summary = data.get("sentiment_summary")
                        if ticker and summary and isinstance(summary, dict):
                            sentiment_data[ticker] = summary
                    except Exception as e:
                        self.logger.debug(f"Could not extract sentiment from {json_file}: {e}")

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
