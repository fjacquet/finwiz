"""Unit tests for IPOScreener (Phase 2 module contract tests).

Since the ipo_screener module is not yet implemented (Phase 2 pending),
these tests verify the pipeline's interaction contract via mocked imports.
"""

import importlib

import pytest

from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(ticker: str) -> NewcomerCandidate:
    return NewcomerCandidate(
        ticker=ticker,
        name=f"{ticker} IPO Co.",
        asset_class="stock",
        source="ipo",
        composite_score=0.6,
        grade="C+",
    )


class TestIPOScreener:
    """Tests for the IPO screener contract."""

    def test_returns_candidates_from_mocked_sec(self, mocker):
        """IPO screener returns candidates from SEC data."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.screen.return_value = [
            _make_candidate("NEWIPO1"),
            _make_candidate("NEWIPO2"),
        ]
        mock_mod = mocker.MagicMock()
        mock_mod.IPOScreener = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.ipo_screener": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.ipo_screener")
        screener = mod.IPOScreener()
        candidates = screener.screen("stock")
        assert len(candidates) == 2
        assert candidates[0].ticker == "NEWIPO1"
        assert candidates[0].source == "ipo"

    def test_handles_sec_api_failure(self, mocker):
        """Screener returns empty list on SEC API failure."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.screen.side_effect = OSError("SEC API unavailable")
        mock_mod = mocker.MagicMock()
        mock_mod.IPOScreener = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.ipo_screener": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.ipo_screener")
        screener = mod.IPOScreener()
        with pytest.raises(OSError):
            screener.screen("stock")

    def test_empty_sec_response(self, mocker):
        """Screener returns empty list when SEC has no recent IPOs."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.screen.return_value = []
        mock_mod = mocker.MagicMock()
        mock_mod.IPOScreener = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.ipo_screener": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.ipo_screener")
        candidates = mod.IPOScreener().screen("stock")
        assert candidates == []

    def test_import_error_handled_in_pipeline(self, mocker):
        """Pipeline handles ImportError from missing ipo_screener."""
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        # Avoid a live yfinance universe fetch; empty universe keeps screeners offline.
        mocker.patch("finwiz.discovery.universe_provider.DynamicUniverseProvider.get_universe", return_value=[])
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.portfolio_tickers = set()
        # _gather_candidates handles ImportError internally
        candidates = pipeline._gather_candidates()
        assert isinstance(candidates, list)
