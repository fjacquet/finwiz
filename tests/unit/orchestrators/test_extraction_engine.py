"""
Unit tests for ExtractionEngine's market_context / backtesting_metrics markers.

market_context and validation_results were written against the raw CrewAI
discovery-crew kickoff shape; the pipeline actually wired into
DiscoveryOrchestrator today (NewcomerDiscoveryPipeline) never emits either
field into consolidated_discovery.json. Task-11 Ruling 23 (11c) requires these
two extractors to report an explicit, named "unavailable" marker rather than a
silent empty result that reads the same as "we looked and there was nothing".
"""

import json

from finwiz.orchestrators.extraction.engine import ExtractionEngine


class TestMarketContextUnavailable:
    """market_context has no producer in the current discovery pipeline."""

    def test_returns_named_unavailable_marker(self, tmp_path):
        """The marker must be distinguishable from a genuine empty result ({} or None)."""
        engine = ExtractionEngine(output_dir=tmp_path)

        result = engine._extract_market_context()

        assert result is not None
        assert result != {}
        assert result["unavailable"] is True
        assert result["field"] == "market_context"
        assert result.get("reason")

    def test_marker_returned_even_when_discovery_output_exists(self, tmp_path):
        """No producer exists for this field regardless of whether discovery ran."""
        discovery_dir = tmp_path / "discovery"
        discovery_dir.mkdir()
        with open(discovery_dir / "consolidated_discovery.json", "w") as f:
            json.dump({"opportunities": [{"ticker": "AAPL", "grade": "A+", "asset_class": "stock"}]}, f)

        engine = ExtractionEngine(output_dir=tmp_path)

        result = engine._extract_market_context()

        assert result == {
            "unavailable": True,
            "field": "market_context",
            "reason": ExtractionEngine._NO_PRODUCER_REASON,
        }


class TestBacktestingMetricsUnavailable:
    """backtesting_metrics (validation_results) has no producer in the current discovery pipeline."""

    def test_returns_named_unavailable_marker(self, tmp_path):
        """The marker must be distinguishable from a genuine empty result ({} or None)."""
        engine = ExtractionEngine(output_dir=tmp_path)

        result = engine._extract_backtesting_metrics()

        assert result is not None
        assert result != {}
        assert result["unavailable"] is True
        assert result["field"] == "backtesting_metrics"
        assert result.get("reason")

    def test_backtesting_marker_distinguishable_from_market_context_marker(self, tmp_path):
        """Both extractors share a reason string but must carry different 'field' values."""
        engine = ExtractionEngine(output_dir=tmp_path)

        market_context = engine._extract_market_context()
        backtesting_metrics = engine._extract_backtesting_metrics()

        assert market_context["field"] != backtesting_metrics["field"]
