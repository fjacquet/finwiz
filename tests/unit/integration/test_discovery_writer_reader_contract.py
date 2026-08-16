"""Regression test for the discovery writer/reader contract.

``NewcomerDiscoveryPipeline._to_legacy_format`` (the writer -- the sole
producer of ``output/discovery/a_plus_{stocks,etfs,crypto}.json``, see
``scoring/stock_analyzer.py`` / ``etf_analyzer.py`` / ``crypto_analyzer.py``)
and ``APlusDataExtractor.extract_aplus_opportunities`` (the reader) must agree
on the shape of that JSON. If they drift, a successful discovery run that
found real opportunities renders as a confident, silent zero -- exactly the
class of bug this branch exists to eliminate elsewhere (market_context,
backtesting_metrics).

This test builds the writer's *exact* payload by calling the real
``_to_legacy_format`` for all three asset classes (never a hand-written dict,
which could itself drift from the writer), writes it to the files the reader
actually consumes, and asserts a non-empty, correctly-populated collection
comes back. That's the contract; without this test the two sides can drift
apart again silently.
"""

import json
import time

import pytest

from finwiz.orchestrators.extraction.aplus import APlusDataExtractor
from finwiz.schemas.newcomer_discovery import NewcomerCandidate, NewcomerDiscoveryResult
from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

_FILENAMES = {"stock": "a_plus_stocks.json", "etf": "a_plus_etfs.json", "crypto": "a_plus_crypto.json"}


def _make_candidate(ticker: str, name: str, asset_class: str) -> NewcomerCandidate:
    """Build an A+-grade candidate as the newcomer discovery pipeline would."""
    return NewcomerCandidate(
        ticker=ticker,
        name=name,
        asset_class=asset_class,
        source="test",
        composite_score=0.9,
        grade="A+",
        recommendation="BUY",
        rationale="Strong fundamentals",
    )


@pytest.fixture
def discovery_output_dir(tmp_path, mocker):
    """Write the writer's real payload for each asset class to a temp output dir.

    Mirrors exactly what DiscoveryOrchestrator._save_discovery_results does:
    dump the dict _to_legacy_format returns straight to
    output/discovery/a_plus_{asset_class}.json.
    """
    mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")

    output_dir = tmp_path / "output"
    discovery_dir = output_dir / "discovery"
    discovery_dir.mkdir(parents=True)

    candidates_by_class = {
        "stock": [_make_candidate("NVDA", "NVIDIA Corporation", "stock")],
        "etf": [_make_candidate("VWCE", "Vanguard FTSE All-World UCITS ETF", "etf")],
        "crypto": [_make_candidate("BTC-USD", "Bitcoin", "crypto")],
    }

    for asset_class, candidates in candidates_by_class.items():
        pipeline = NewcomerDiscoveryPipeline(asset_class)
        result = NewcomerDiscoveryResult(
            asset_class=asset_class,
            session_id="s1",
            timestamp="2026-01-01T00:00:00",
            candidates=candidates,
            total_candidates=len(candidates),
            summary="test discovery run",
        )
        payload = pipeline._to_legacy_format(result, time.time())
        (discovery_dir / _FILENAMES[asset_class]).write_text(json.dumps(payload, default=str))

    return output_dir


class TestDiscoveryWriterReaderContract:
    """A successful discovery run must not render as a confident zero."""

    def test_real_writer_payload_survives_extraction_for_all_asset_classes(self, discovery_output_dir):
        extractor = APlusDataExtractor(output_dir=discovery_output_dir)

        collection = extractor.extract_aplus_opportunities()

        assert collection is not None, "extraction returned None for a real, populated writer payload"

        assert len(collection.stock_opportunities) == 1, "stock opportunity from the writer's payload was dropped"
        assert collection.stock_opportunities[0].symbol == "NVDA"
        assert collection.stock_opportunities[0].name == "NVIDIA Corporation"
        assert collection.stock_opportunities[0].grade == "A+"

        assert len(collection.etf_opportunities) == 1, "ETF opportunity from the writer's payload was dropped"
        assert collection.etf_opportunities[0].symbol == "VWCE"

        assert len(collection.crypto_opportunities) == 1, "crypto opportunity from the writer's payload was dropped"
        assert collection.crypto_opportunities[0].symbol == "BTC"  # -USD suffix stripped by the extractor

        assert collection.discovery_summary != "No A+ opportunities identified in current market conditions."

    def test_writer_rationale_and_recommendation_survive_into_the_collection(self, discovery_output_dir):
        """The writer's flat rationale/recommendation must not be silently discarded.

        _to_legacy_format emits candidate["rationale"] = "Strong fundamentals" and
        candidate["recommendation"] = "BUY" (see _make_candidate above). Neither is
        read by the moat/diversification/technology-derived structured rationale,
        so before the fix both were dropped for every candidate this pipeline
        produces -- confirmed by direct inspection before the fix: the extracted
        opportunity's rationale was `[]` for stock and crypto candidates built from
        this exact payload shape.
        """
        extractor = APlusDataExtractor(output_dir=discovery_output_dir)

        collection = extractor.extract_aplus_opportunities()

        assert collection is not None
        for opportunities in (collection.stock_opportunities, collection.etf_opportunities, collection.crypto_opportunities):
            assert len(opportunities) == 1
            rationale = opportunities[0].rationale
            assert "Strong fundamentals" in rationale, f"writer's rationale text missing from {rationale}"
            assert "Recommendation: BUY" in rationale, f"writer's recommendation missing from {rationale}"

    def test_unmeasured_key_metrics_are_marked_unavailable_not_zero(self, discovery_output_dir):
        """A metric this pipeline never measures must not be reported as a real zero.

        _to_legacy_format never emits fundamentals/cost_metrics/market_cap_usd/
        technology for any candidate, so before the fix every one of these came
        back as a fabricated 0 / 0.0 / "" / "$0" -- indistinguishable from a real
        measurement (and, for ETF's ter/aum, reading as an excellent one on the
        exact axis the TER gate exists to screen).
        """
        extractor = APlusDataExtractor(output_dir=discovery_output_dir)

        collection = extractor.extract_aplus_opportunities()

        assert collection is not None

        stock_metrics = collection.stock_opportunities[0].key_metrics
        assert stock_metrics["roe_3y_avg"] == {"unavailable": True, "field": "roe_3y_avg", "reason": stock_metrics["roe_3y_avg"]["reason"]}, (
            "roe_3y_avg must be a named-unavailable marker, not a bare 0"
        )
        assert stock_metrics["roe_3y_avg"]["unavailable"] is True
        assert stock_metrics["revenue_cagr_5y"]["unavailable"] is True
        assert stock_metrics["debt_to_equity"]["unavailable"] is True
        assert stock_metrics["market_cap_usd"]["unavailable"] is True, "0 for market_cap_usd reads as a real, tiny company, not 'unknown'"

        etf_metrics = collection.etf_opportunities[0].key_metrics
        assert etf_metrics["ter"]["unavailable"] is True, "an unmeasured TER must not read as a real 0.0 (which passes the gate)"
        assert etf_metrics["aum_usd"]["unavailable"] is True
        assert etf_metrics["aum_formatted"]["unavailable"] is True, 'an unmeasured AUM must not render as "$0"'

        crypto_metrics = collection.crypto_opportunities[0].key_metrics
        assert crypto_metrics["market_cap_usd"]["unavailable"] is True
        assert crypto_metrics["volume_24h_usd"]["unavailable"] is True
