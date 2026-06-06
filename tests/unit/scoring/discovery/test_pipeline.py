"""Unit tests for NewcomerDiscoveryPipeline."""

import time

import pytest

from finwiz.schemas.newcomer_discovery import (
    NewcomerCandidate,
    NewcomerDiscoveryResult,
)
from finwiz.scoring.discovery.pipeline import (
    ENRICHMENT_SCORE_THRESHOLD,
    NewcomerDiscoveryPipeline,
)


def _make_candidate(ticker: str, score: float = 0.5, asset_class: str = "stock") -> NewcomerCandidate:
    """Helper to build a NewcomerCandidate."""
    return NewcomerCandidate(
        ticker=ticker,
        name=f"{ticker} Inc.",
        asset_class=asset_class,
        source="test",
        composite_score=score,
        grade="B",
        recommendation="REVIEW",
        rationale="Test candidate",
    )


def _disable_portfolio_aware(mocker) -> None:
    """Force the legacy signal-gated path by disabling portfolio_aware_discovery."""
    mocker.patch(
        "finwiz.config.features.flags.is_feature_enabled",
        side_effect=lambda name, *a, **k: name != "portfolio_aware_discovery",
    )


class TestNewcomerDiscoveryPipeline:
    """Tests for the full (legacy signal-gated) pipeline orchestration."""

    @pytest.fixture(autouse=True)
    def _legacy_path(self, mocker):
        _disable_portfolio_aware(mocker)

    @pytest.fixture
    def pipeline(self, mocker):
        """Pipeline with mocked CSV loading."""
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = {"AAPL", "MSFT", "GOOGL"}
        return p

    def test_excludes_portfolio_tickers(self, pipeline, mocker):
        """Candidates already in portfolio are filtered out."""
        candidates = [
            _make_candidate("AAPL", 0.9),  # in portfolio
            _make_candidate("TSLA", 0.85),  # not in portfolio
            _make_candidate("MSFT", 0.88),  # in portfolio
            _make_candidate("AMZN", 0.82),  # not in portfolio
        ]
        mocker.patch.object(pipeline, "_gather_candidates", return_value=candidates)
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("test-session")
        tickers = [c.ticker for c in result.candidates]
        assert "AAPL" not in tickers
        assert "MSFT" not in tickers
        assert "TSLA" in tickers
        assert "AMZN" in tickers

    def test_discover_returns_valid_result(self, pipeline, mocker):
        """discover() returns NewcomerDiscoveryResult with correct fields."""
        candidates = [_make_candidate("TSLA", 0.9), _make_candidate("AMZN", 0.8)]
        mocker.patch.object(pipeline, "_gather_candidates", return_value=candidates)
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("sess-123")
        assert isinstance(result, NewcomerDiscoveryResult)
        assert result.asset_class == "stock"
        assert result.session_id == "sess-123"
        assert result.total_candidates == 2
        assert "Discovered" in result.summary

    def test_persists_result_to_json(self, pipeline, mocker, tmp_path):
        """Results are written to output/discovery/newcomer_stock.json."""
        mocker.patch.object(pipeline, "_gather_candidates", return_value=[])
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))

        mock_persist = mocker.patch.object(pipeline, "_persist_result")
        pipeline.discover("test-session")
        mock_persist.assert_called_once()

    def test_to_legacy_format_shape(self, pipeline):
        """_to_legacy_format returns dict with expected keys."""
        result = NewcomerDiscoveryResult(
            asset_class="stock",
            session_id="s1",
            timestamp="2026-01-01T00:00:00",
            candidates=[_make_candidate("TSLA", 0.9)],
            total_candidates=1,
            summary="test",
        )
        legacy = pipeline._to_legacy_format(result, time.time())
        assert "opportunities" in legacy
        assert "analysis_summary" in legacy
        assert "performance_metrics" in legacy
        assert legacy["performance_metrics"]["method"] == "newcomer_discovery_pipeline"
        assert len(legacy["opportunities"]) == 1
        assert legacy["opportunities"][0]["ticker"] == "TSLA"

    def test_screener_failure_doesnt_crash(self, pipeline, mocker):
        """If one screener raises, pipeline continues with other screeners."""
        mocker.patch(
            "finwiz.discovery.universe_provider.DynamicUniverseProvider.get_universe",
            side_effect=RuntimeError("universe failed"),
        )
        mocker.patch(
            "finwiz.discovery.breakout_detector.BreakoutDetector.detect",
            side_effect=ImportError("not found"),
        )
        mocker.patch(
            "finwiz.discovery.momentum_scanner.MomentumScanner.scan",
            side_effect=ImportError("not found"),
        )
        mocker.patch(
            "finwiz.discovery.ipo_screener.IPOScreener.screen",
            side_effect=ImportError("not found"),
        )
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("test-session")
        assert result.total_candidates == 0

    def test_empty_candidates_returns_empty_result(self, pipeline, mocker):
        """If no candidates found, returns result with empty list."""
        mocker.patch.object(pipeline, "_gather_candidates", return_value=[])
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("test-session")
        assert result.total_candidates == 0
        assert result.candidates == []

    def test_enrichment_failure_returns_unenriched(self, pipeline, mocker):
        """If Perplexity enrichment fails, candidates proceed without enrichment."""
        candidates = [_make_candidate("TSLA", 0.95)]
        mocker.patch.object(pipeline, "_gather_candidates", return_value=candidates)
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(
            pipeline,
            "_enrich_top_candidates",
            side_effect=lambda c: (c, 1, 0),  # attempted 1, succeeded 0
        )
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("test-session")
        assert result.total_candidates == 1
        assert result.candidates[0].enrichment is None

    def test_candidates_sorted_by_score_descending(self, pipeline, mocker):
        """Candidates are returned sorted by composite_score descending."""
        candidates = [
            _make_candidate("LOW", 0.5),
            _make_candidate("HIGH", 0.95),
            _make_candidate("MID", 0.7),
        ]
        mocker.patch.object(pipeline, "_gather_candidates", return_value=candidates)
        mocker.patch.object(pipeline, "_score_candidates", side_effect=lambda c: c)
        mocker.patch.object(pipeline, "_enrich_top_candidates", side_effect=lambda c: (c, 0, 0))
        mocker.patch.object(pipeline, "_persist_result")

        result = pipeline.discover("test-session")
        scores = [c.composite_score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)


class TestPortfolioTickerLoading:
    """Tests for portfolio ticker loading and normalization."""

    def test_loads_tickers_from_csv(self, mocker, tmp_path):
        """Reads tickers from CSV files."""
        csv_path = tmp_path / "stock.csv"
        csv_path.write_text("Ticker,Name\nAAPL,Apple\nTSLA,Tesla\n")

        mocker.patch(
            "finwiz.scoring.discovery.pipeline.Path",
            side_effect=lambda p: tmp_path / p.split("/")[-1] if "/" in p else tmp_path / p,
        )
        mocker.patch.object(NewcomerDiscoveryPipeline, "__init__", lambda self, ac: None)
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.asset_class = "stock"
        pipeline.portfolio_tickers = set()

        # Manually call with a real csv
        import csv as csv_mod
        from io import StringIO

        content = "Ticker,Name\nAAPL,Apple\nTSLA,Tesla\n"
        reader = csv_mod.DictReader(StringIO(content))
        for row in reader:
            ticker = (row.get("Ticker") or "").strip()
            if ticker:
                pipeline.portfolio_tickers.add(ticker.upper())

        assert "AAPL" in pipeline.portfolio_tickers
        assert "TSLA" in pipeline.portfolio_tickers

    def test_normalizes_yahoo_prefix(self, mocker):
        """Yahoo: prefix is stripped from tickers."""
        mocker.patch.object(NewcomerDiscoveryPipeline, "__init__", lambda self, ac: None)
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.portfolio_tickers = set()

        # Simulate the normalization logic
        ticker = "Yahoo:MSFT"
        if ticker.upper().startswith("YAHOO:"):
            ticker = ticker.split(":", 1)[1]
        pipeline.portfolio_tickers.add(ticker.upper())

        assert "MSFT" in pipeline.portfolio_tickers
        assert "YAHOO:MSFT" not in pipeline.portfolio_tickers

    def test_missing_csv_doesnt_crash(self, mocker):
        """Pipeline initializes without error when CSV files are missing."""
        mocker.patch("finwiz.scoring.discovery.pipeline.Path.exists", return_value=False)
        pipeline = NewcomerDiscoveryPipeline("stock")
        assert isinstance(pipeline.portfolio_tickers, set)


class TestScreenerWiring:
    """Tests that screener classes are wired to the correct import paths."""

    def test_all_screeners_importable_from_finwiz_discovery(self):
        """All 5 discovery classes import from finwiz.discovery.* (not finwiz.scoring.discovery.*)."""
        from finwiz.discovery.breakout_detector import BreakoutDetector
        from finwiz.discovery.candidate_scorer import CandidateScorer
        from finwiz.discovery.ipo_screener import IPOScreener
        from finwiz.discovery.momentum_scanner import MomentumScanner
        from finwiz.discovery.universe_provider import DynamicUniverseProvider

        assert hasattr(DynamicUniverseProvider, "get_universe")
        assert hasattr(IPOScreener, "screen")
        assert hasattr(BreakoutDetector, "detect")
        assert hasattr(MomentumScanner, "scan")
        assert hasattr(CandidateScorer, "score_and_grade")

    def test_gather_candidates_calls_real_screeners(self, mocker):
        """_gather_candidates calls universe provider + breakout + momentum (IPO excluded)."""
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = set()

        mock_universe = mocker.patch(
            "finwiz.discovery.universe_provider.DynamicUniverseProvider.get_universe",
            return_value=["TSLA", "AMZN"],
        )
        mock_breakout = mocker.patch(
            "finwiz.discovery.breakout_detector.BreakoutDetector.detect",
            return_value=[_make_candidate("TSLA", 0.85)],
        )
        mock_momentum = mocker.patch(
            "finwiz.discovery.momentum_scanner.MomentumScanner.scan",
            return_value=[_make_candidate("AMZN", 0.82)],
        )

        result = p._gather_candidates()

        mock_universe.assert_called_once()
        mock_breakout.assert_called_once_with(["TSLA", "AMZN"], "stock")
        mock_momentum.assert_called_once_with(["TSLA", "AMZN"], "stock")
        tickers = {c.ticker for c in result}
        assert "TSLA" in tickers
        assert "AMZN" in tickers

    def test_gather_excludes_ipo_screener_entirely(self, mocker):
        """IPOScreener is intentionally removed from the opportunity pipeline.

        SEC S-1 filings have no fundamentals or trading history — they grade
        F uniformly and are events, not investable signals.
        """
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = set()

        mocker.patch(
            "finwiz.discovery.universe_provider.DynamicUniverseProvider.get_universe",
            return_value=["TSLA"],
        )
        mocker.patch(
            "finwiz.discovery.breakout_detector.BreakoutDetector.detect",
            return_value=[],
        )
        mocker.patch(
            "finwiz.discovery.momentum_scanner.MomentumScanner.scan",
            return_value=[],
        )
        mock_ipo = mocker.patch(
            "finwiz.discovery.ipo_screener.IPOScreener.screen",
            return_value=[_make_candidate("IPO1", 0.5)],
        )

        p._gather_candidates()
        mock_ipo.assert_not_called()

    def test_gather_skips_ipo_for_non_stock_asset_classes(self, mocker):
        """IPOScreener is not called for any asset class (backwards-compat assertion)."""
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("etf")
        p.portfolio_tickers = set()

        mocker.patch(
            "finwiz.discovery.universe_provider.DynamicUniverseProvider.get_universe",
            return_value=["SPY"],
        )
        mocker.patch(
            "finwiz.discovery.breakout_detector.BreakoutDetector.detect",
            return_value=[],
        )
        mocker.patch(
            "finwiz.discovery.momentum_scanner.MomentumScanner.scan",
            return_value=[],
        )
        mock_ipo = mocker.patch(
            "finwiz.discovery.ipo_screener.IPOScreener.screen",
            return_value=[],
        )

        p._gather_candidates()
        mock_ipo.assert_not_called()


class TestPortfolioAwareDiscovery:
    """Tests for the Portfolio-Aware Opportunity Cascade wide-scoring path."""

    @pytest.fixture
    def pipeline(self, mocker):
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = set()
        return p

    def _wire(self, pipeline, mocker, *, universe, signals=None, returns=None, sectors=None, profile=None):
        from finwiz.schemas.newcomer_discovery import PortfolioGapProfile

        mocker.patch.object(pipeline, "_build_universe", return_value=universe)
        mocker.patch.object(pipeline, "_signal_standalone_scores", return_value=(signals or {}, {}))
        mocker.patch("finwiz.discovery.market_data.get_returns", return_value=returns or {})
        mocker.patch("finwiz.discovery.market_data.get_sectors", return_value=sectors or {})
        mocker.patch(
            "finwiz.orchestrators.gap_profile_orchestrator.load_gap_profile",
            return_value=profile or PortfolioGapProfile(is_empty=True),
        )

    def test_scores_whole_universe_not_just_signals(self, pipeline, mocker):
        """Recall is un-gated: names with NO breakout/momentum signal still get scored."""
        rets = {
            "TSLA": [0.01, 0.02, -0.01, 0.03, 0.0, 0.01],
            "AMZN": [0.0, 0.01, 0.01, -0.02, 0.02, 0.0],
            "NFLX": [0.02, -0.01, 0.0, 0.01, 0.01, 0.0],
        }
        # Default (empty) gap profile -> fail-soft path.
        self._wire(pipeline, mocker, universe=["TSLA", "AMZN", "NFLX"], signals={}, returns=rets)
        candidates = pipeline._gather_portfolio_aware_candidates()
        assert {c.ticker for c in candidates} == {"TSLA", "AMZN", "NFLX"}
        # Recall preserved AND every candidate still scored (not collapsed to 0).
        assert all(c.composite_score > 0 for c in candidates)

    def test_empty_profile_preserves_standalone_score(self, pipeline, mocker):
        """Fail-soft: an empty gap profile must NOT halve scores (regression for PR #45 Codex P2).

        composite_score must equal the standalone factor score, not factor x 0.5,
        so A/A+ grades and the 0.80 enrichment cutoff stay reachable.
        """
        from finwiz.discovery.market_data import factor_score_from_returns

        rets = {"TSLA": [0.05, 0.04, 0.06, 0.03, 0.05, 0.04]}  # strong momentum
        self._wire(pipeline, mocker, universe=["TSLA"], signals={}, returns=rets)
        candidates = pipeline._gather_portfolio_aware_candidates()
        expected = factor_score_from_returns(rets["TSLA"])
        assert candidates[0].composite_score == pytest.approx(expected)
        assert candidates[0].portfolio_fit_score is None

    def test_multiplicative_blend_and_gap_fill(self, pipeline, mocker):
        """final = factor x portfolio_fit: over-held sector ~0, gap sector ~factor."""
        from finwiz.schemas.newcomer_discovery import PortfolioGapProfile

        profile = PortfolioGapProfile(
            sector_weights={"Technology": 1.0},
            underweight_sectors=[],
            holding_returns={},  # no correlation term -> only sector term applies
            is_empty=False,
        )
        rets = {
            "TECHCO": [0.01, 0.02, 0.0, 0.01, 0.02, 0.01],
            "HEALTHCO": [0.01, 0.02, 0.0, 0.01, 0.02, 0.01],
        }
        sectors = {"TECHCO": "Technology", "HEALTHCO": "Healthcare"}
        self._wire(pipeline, mocker, universe=["TECHCO", "HEALTHCO"], returns=rets, sectors=sectors, profile=profile)
        candidates = {c.ticker: c for c in pipeline._gather_portfolio_aware_candidates()}
        # Over-held Technology -> fit ~0 -> final ~0
        assert candidates["TECHCO"].composite_score < 0.05
        # Absent Healthcare sector -> fit ~1 -> final ~factor (> tech)
        assert candidates["HEALTHCO"].composite_score > candidates["TECHCO"].composite_score
        assert candidates["HEALTHCO"].gap_filled == "Healthcare"

    def test_no_actionable_filter_low_grades_survive(self, pipeline, mocker):
        """Low-scoring candidates are NOT dropped (filter noise out via top-N, not grade-gate)."""
        from finwiz.schemas.newcomer_discovery import PortfolioGapProfile

        profile = PortfolioGapProfile(sector_weights={"Technology": 1.0}, holding_returns={}, is_empty=False)
        rets = {"TECHCO": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
        self._wire(pipeline, mocker, universe=["TECHCO"], returns=rets, sectors={"TECHCO": "Technology"}, profile=profile)
        candidates = pipeline._gather_portfolio_aware_candidates()
        # A near-zero (grade F) candidate still appears — no hard grade drop in wide stage.
        assert any(c.ticker == "TECHCO" for c in candidates)

    def test_signal_score_used_when_present(self, pipeline, mocker):
        """When a ticker trips a signal, its richer signal composite is the standalone factor."""
        from finwiz.schemas.newcomer_discovery import PortfolioGapProfile

        profile = PortfolioGapProfile(sector_weights={}, holding_returns={}, is_empty=False)
        self._wire(
            pipeline,
            mocker,
            universe=["TSLA"],
            signals={"TSLA": 0.9},
            returns={"TSLA": [0.001, 0.001, 0.001, 0.001, 0.001]},
            sectors={"TSLA": "Healthcare"},
            profile=profile,
        )
        candidates = pipeline._gather_portfolio_aware_candidates()
        assert candidates[0].momentum_score == pytest.approx(0.9)


class TestEnrichment:
    """Tests for the Perplexity enrichment integration."""

    @pytest.fixture
    def pipeline(self, mocker):
        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        p = NewcomerDiscoveryPipeline("stock")
        p.portfolio_tickers = set()
        return p

    def test_skips_when_perplexity_disabled(self, pipeline, mocker):
        """Enrichment is skipped when Perplexity is disabled."""
        mocker.patch(
            "finwiz.tools.perplexity_feature_utils.initialize_perplexity_integration",
            return_value=None,
        )
        mocker.patch(
            "finwiz.tools.perplexity_feature_utils.is_perplexity_enabled",
            return_value=False,
        )
        candidates = [_make_candidate("TSLA", 0.95)]
        result, attempted, succeeded = pipeline._enrich_top_candidates(candidates)
        assert attempted == 0
        assert succeeded == 0
        assert result[0].enrichment is None

    def test_skips_below_threshold(self, pipeline, mocker):
        """Candidates below ENRICHMENT_SCORE_THRESHOLD are not enriched."""
        mocker.patch(
            "finwiz.tools.perplexity_feature_utils.initialize_perplexity_integration",
            return_value=mocker.MagicMock(),
        )
        mocker.patch(
            "finwiz.tools.perplexity_feature_utils.is_perplexity_enabled",
            return_value=True,
        )
        candidates = [_make_candidate("LOW", ENRICHMENT_SCORE_THRESHOLD - 0.01)]
        result, attempted, succeeded = pipeline._enrich_top_candidates(candidates)
        assert attempted == 0
        assert succeeded == 0
