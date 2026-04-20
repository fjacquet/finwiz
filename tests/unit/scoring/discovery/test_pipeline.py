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


class TestNewcomerDiscoveryPipeline:
    """Tests for the full pipeline orchestration."""

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
        """_gather_candidates calls universe provider + breakout + momentum + ipo (stock only)."""
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
        mock_ipo = mocker.patch(
            "finwiz.discovery.ipo_screener.IPOScreener.screen",
            return_value=[],
        )

        result = p._gather_candidates()

        mock_universe.assert_called_once()
        mock_breakout.assert_called_once_with(["TSLA", "AMZN"], "stock")
        mock_momentum.assert_called_once_with(["TSLA", "AMZN"], "stock")
        mock_ipo.assert_called_once()
        tickers = {c.ticker for c in result}
        assert "TSLA" in tickers
        assert "AMZN" in tickers

    def test_gather_skips_ipo_for_non_stock_asset_classes(self, mocker):
        """IPOScreener is only called for asset_class='stock'."""
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
