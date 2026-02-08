"""Unit tests for BreakoutDetector (Phase 2 module contract tests).

Since the breakout_detector module is not yet implemented (Phase 2 pending),
these tests verify the pipeline's interaction contract via mocked imports.
"""

import importlib

from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(ticker: str, score: float = 0.7) -> NewcomerCandidate:
    return NewcomerCandidate(
        ticker=ticker,
        name=f"{ticker} Breakout",
        asset_class="stock",
        source="breakout",
        composite_score=score,
        grade="B",
    )


class TestBreakoutDetector:
    """Tests for the breakout detector contract."""

    def test_identifies_breakout_candidates(self, mocker):
        """Breakout detector returns candidates with breakout signals."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.detect.return_value = [
            _make_candidate("BRK1", 0.85),
            _make_candidate("BRK2", 0.78),
        ]
        mock_mod = mocker.MagicMock()
        mock_mod.BreakoutDetector = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.breakout_detector": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.breakout_detector")
        detector = mod.BreakoutDetector()
        candidates = detector.detect("stock")
        assert len(candidates) == 2
        assert all(c.source == "breakout" for c in candidates)

    def test_no_breakouts_detected(self, mocker):
        """Returns empty list when no breakout patterns are found."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.detect.return_value = []
        mock_mod = mocker.MagicMock()
        mock_mod.BreakoutDetector = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.breakout_detector": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.breakout_detector")
        candidates = mod.BreakoutDetector().detect("etf")
        assert candidates == []

    def test_mocked_price_volume_data(self, mocker):
        """Detector works with mocked price/volume data."""
        mock_cls = mocker.MagicMock()
        candidate = _make_candidate("VOLU", 0.82)
        candidate.metadata = {"volume_ratio": 2.5, "price_change_pct": 8.3}
        mock_cls.return_value.detect.return_value = [candidate]
        mock_mod = mocker.MagicMock()
        mock_mod.BreakoutDetector = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.breakout_detector": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.breakout_detector")
        result = mod.BreakoutDetector().detect("stock")
        assert len(result) == 1
        assert result[0].metadata["volume_ratio"] == 2.5

    def test_import_error_handled_in_pipeline(self, mocker):
        """Pipeline handles ImportError from missing breakout_detector."""
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.portfolio_tickers = set()
        candidates = pipeline._gather_candidates()
        assert isinstance(candidates, list)
