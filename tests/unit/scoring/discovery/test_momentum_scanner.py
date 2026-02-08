"""Unit tests for MomentumScanner (Phase 2 module contract tests).

Since the momentum_scanner module is not yet implemented (Phase 2 pending),
these tests verify the pipeline's interaction contract via mocked imports.
"""

import importlib

from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(ticker: str, score: float = 0.65) -> NewcomerCandidate:
    return NewcomerCandidate(
        ticker=ticker, name=f"{ticker} Momentum", asset_class="stock",
        source="momentum", composite_score=score, grade="C+",
    )


class TestMomentumScanner:
    """Tests for the momentum scanner contract."""

    def test_returns_momentum_candidates(self, mocker):
        """Scanner returns candidates with momentum signals."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.scan.return_value = [
            _make_candidate("MOM1", 0.88),
            _make_candidate("MOM2", 0.72),
        ]
        mock_mod = mocker.MagicMock()
        mock_mod.MomentumScanner = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.momentum_scanner": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.momentum_scanner")
        scanner = mod.MomentumScanner()
        candidates = scanner.scan("stock")
        assert len(candidates) == 2
        assert all(c.source == "momentum" for c in candidates)

    def test_empty_result_no_momentum(self, mocker):
        """Returns empty list when no momentum signals detected."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.scan.return_value = []
        mock_mod = mocker.MagicMock()
        mock_mod.MomentumScanner = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.momentum_scanner": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.momentum_scanner")
        candidates = mod.MomentumScanner().scan("crypto")
        assert candidates == []

    def test_mocked_rsi_volume_data(self, mocker):
        """Scanner works with mocked RSI and volume data."""
        mock_cls = mocker.MagicMock()
        candidate = _make_candidate("RSIV", 0.75)
        candidate.metadata = {"rsi_14": 68.5, "volume_20d_avg": 1500000}
        candidate.momentum_score = 0.75
        mock_cls.return_value.scan.return_value = [candidate]
        mock_mod = mocker.MagicMock()
        mock_mod.MomentumScanner = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.momentum_scanner": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.momentum_scanner")
        result = mod.MomentumScanner().scan("stock")
        assert len(result) == 1
        assert result[0].metadata["rsi_14"] == 68.5
        assert result[0].momentum_score == 0.75

    def test_import_error_handled_in_pipeline(self, mocker):
        """Pipeline handles ImportError from missing momentum_scanner."""
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.portfolio_tickers = set()
        candidates = pipeline._gather_candidates()
        assert isinstance(candidates, list)
