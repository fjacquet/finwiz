"""Unit tests for newcomer discovery schemas."""

import pytest
from pydantic import ValidationError

from finwiz.schemas.newcomer_discovery import (
    EnrichmentResult,
    NewcomerCandidate,
    NewcomerDiscoveryResult,
)


class TestNewcomerCandidate:
    """Tests for NewcomerCandidate schema validation."""

    def test_valid_candidate(self):
        """Valid candidate is created without errors."""
        c = NewcomerCandidate(
            ticker="TSLA", name="Tesla Inc.", asset_class="stock",
            source="universe", composite_score=0.85, grade="A",
            recommendation="BUY", rationale="Strong growth",
        )
        assert c.ticker == "TSLA"
        assert c.composite_score == 0.85
        assert c.enrichment is None

    def test_minimal_candidate(self):
        """Candidate with only required fields."""
        c = NewcomerCandidate(ticker="X", asset_class="etf")
        assert c.ticker == "X"
        assert c.composite_score == 0.0
        assert c.grade == ""
        assert c.recommendation == "REVIEW"

    def test_score_range_validation(self):
        """Score outside 0-1 range raises ValidationError."""
        with pytest.raises(ValidationError):
            NewcomerCandidate(ticker="BAD", asset_class="stock", composite_score=1.5)
        with pytest.raises(ValidationError):
            NewcomerCandidate(ticker="BAD", asset_class="stock", composite_score=-0.1)

    def test_empty_ticker_rejected(self):
        """Empty ticker string is rejected."""
        with pytest.raises(ValidationError):
            NewcomerCandidate(ticker="", asset_class="stock")

    def test_invalid_asset_class(self):
        """Asset class outside literal set is rejected."""
        with pytest.raises(ValidationError):
            NewcomerCandidate(ticker="X", asset_class="bond")

    def test_model_dump_serialization(self):
        """model_dump() produces serializable dict."""
        c = NewcomerCandidate(
            ticker="AMZN", asset_class="stock", composite_score=0.9,
            grade="A", metadata={"sector": "tech"},
        )
        d = c.model_dump()
        assert d["ticker"] == "AMZN"
        assert d["composite_score"] == 0.9
        assert d["metadata"]["sector"] == "tech"
        assert d["enrichment"] is None

    def test_with_enrichment(self):
        """Candidate with enrichment data."""
        enrichment = EnrichmentResult(
            articles_found=5, summary="Positive outlook",
            key_insights=["Strong earnings"], success=True,
        )
        c = NewcomerCandidate(
            ticker="GOOG", asset_class="stock",
            composite_score=0.88, enrichment=enrichment,
        )
        assert c.enrichment is not None
        assert c.enrichment.articles_found == 5

    def test_extra_fields_forbidden(self):
        """Extra fields are rejected (model_config extra='forbid')."""
        with pytest.raises(ValidationError):
            NewcomerCandidate(ticker="X", asset_class="stock", unknown_field="bad")


class TestEnrichmentResult:
    """Tests for EnrichmentResult schema validation."""

    def test_valid_enrichment(self):
        """Valid enrichment result is created."""
        e = EnrichmentResult(
            source="perplexity_sonar", query="TSLA analysis",
            articles_found=3, summary="Positive outlook",
            key_insights=["Strong Q4", "EV market share"], success=True,
        )
        assert e.articles_found == 3
        assert len(e.key_insights) == 2

    def test_default_values(self):
        """Enrichment with all defaults."""
        e = EnrichmentResult()
        assert e.source == "perplexity_sonar"
        assert e.articles_found == 0
        assert e.success is True
        assert e.error_message is None

    def test_failed_enrichment(self):
        """Failed enrichment has error message."""
        e = EnrichmentResult(success=False, error_message="API timeout")
        assert not e.success
        assert e.error_message == "API timeout"

    def test_model_dump(self):
        """model_dump() serialization works."""
        e = EnrichmentResult(articles_found=2, summary="test")
        d = e.model_dump()
        assert d["articles_found"] == 2
        assert d["summary"] == "test"


class TestNewcomerDiscoveryResult:
    """Tests for NewcomerDiscoveryResult schema validation."""

    def test_valid_result(self):
        """Valid discovery result with candidates."""
        candidates = [
            NewcomerCandidate(ticker="A", asset_class="stock", composite_score=0.9),
            NewcomerCandidate(ticker="B", asset_class="stock", composite_score=0.8),
        ]
        r = NewcomerDiscoveryResult(
            asset_class="stock", session_id="sess-1",
            timestamp="2026-01-01T00:00:00", candidates=candidates,
            total_candidates=2, summary="Found 2 candidates",
        )
        assert r.total_candidates == 2
        assert len(r.candidates) == 2

    def test_empty_result(self):
        """Discovery result with no candidates."""
        r = NewcomerDiscoveryResult(
            asset_class="etf", session_id="sess-2",
            timestamp="2026-01-01T00:00:00", summary="No candidates",
        )
        assert r.total_candidates == 0
        assert r.candidates == []

    def test_enrichment_tracking(self):
        """Enrichment attempt/success counts are tracked."""
        r = NewcomerDiscoveryResult(
            asset_class="crypto", session_id="s",
            timestamp="2026-01-01T00:00:00", summary="test",
            enrichment_attempted=5, enrichment_succeeded=3,
        )
        assert r.enrichment_attempted == 5
        assert r.enrichment_succeeded == 3

    def test_model_dump_serialization(self):
        """Full model serialization produces valid dict."""
        c = NewcomerCandidate(ticker="X", asset_class="stock", composite_score=0.5)
        r = NewcomerDiscoveryResult(
            asset_class="stock", session_id="s",
            timestamp="2026-01-01T00:00:00", candidates=[c],
            total_candidates=1, summary="test",
        )
        d = r.model_dump()
        assert isinstance(d, dict)
        assert len(d["candidates"]) == 1
        assert d["candidates"][0]["ticker"] == "X"

    def test_missing_required_fields(self):
        """Missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            NewcomerDiscoveryResult(session_id="s", timestamp="2026-01-01T00:00:00")
