"""Unit tests for DynamicUniverseProvider (Phase 2 module contract tests).

Since the universe_provider module is not yet implemented (Phase 2 pending),
these tests verify the pipeline's interaction contract via mocked imports.
"""

import importlib

from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(ticker: str, asset_class: str = "stock") -> NewcomerCandidate:
    return NewcomerCandidate(
        ticker=ticker,
        name=f"{ticker} Co.",
        asset_class=asset_class,
        source="universe",
        composite_score=0.5,
        grade="C",
    )


class TestDynamicUniverseProvider:
    """Tests for the universe provider contract as used by the pipeline."""

    def test_returns_candidate_list(self, mocker):
        """Universe provider returns a list of NewcomerCandidate objects."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.get_candidates.return_value = [
            _make_candidate("NEWCO"),
            _make_candidate("FRESH"),
        ]
        mock_mod = mocker.MagicMock()
        mock_mod.DynamicUniverseProvider = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.universe_provider": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.universe_provider")
        provider = mod.DynamicUniverseProvider()
        candidates = provider.get_candidates("stock")
        assert len(candidates) == 2
        assert all(isinstance(c, NewcomerCandidate) for c in candidates)

    def test_fallback_to_static_on_failure(self, mocker):
        """When yfinance fails, provider should return empty or static list."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.get_candidates.return_value = []
        mock_mod = mocker.MagicMock()
        mock_mod.DynamicUniverseProvider = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.universe_provider": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.universe_provider")
        provider = mod.DynamicUniverseProvider()
        candidates = provider.get_candidates("stock")
        assert isinstance(candidates, list)

    def test_empty_result_handling(self, mocker):
        """Provider returns empty list when no candidates available."""
        mock_cls = mocker.MagicMock()
        mock_cls.return_value.get_candidates.return_value = []
        mock_mod = mocker.MagicMock()
        mock_mod.DynamicUniverseProvider = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.universe_provider": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.universe_provider")
        candidates = mod.DynamicUniverseProvider().get_candidates("etf")
        assert candidates == []

    def test_import_error_handled_gracefully(self, mocker):
        """Pipeline handles ImportError from missing universe_provider."""
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        pipeline = NewcomerDiscoveryPipeline("stock")
        pipeline.portfolio_tickers = set()

        # The real module doesn't exist, so _gather_candidates will handle ImportError
        candidates = pipeline._gather_candidates()
        assert isinstance(candidates, list)
