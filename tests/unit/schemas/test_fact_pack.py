"""Tests for FactPack schema (v5.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis.fact_pack import FactPack


def _build(fetched_at: datetime | None = None, freshness: str = "fresh") -> FactPack:
    return FactPack(
        corporate_structure="Independent — divested VMware Nov 2021",
        recent_events=["Q4 earnings beat expectations"],
        leadership="Michael Dell (CEO), Yvonne McGill (CFO)",
        fetched_at=fetched_at or datetime.now(UTC),
        freshness=freshness,
        confidence=0.9,
        source_citations=["https://example.com/source1"],
    )


class TestFreshnessDerivation:
    @pytest.mark.parametrize(
        ("days_old", "expected"),
        [
            (0, "fresh"),
            (1, "fresh"),
            (2.9, "fresh"),
            (3, "recent"),
            (5, "recent"),
            (6.9, "recent"),
            (7, "stale"),
            (10, "stale"),
            (14, "stale"),
            (30, "stale"),
            (89.9, "stale"),
        ],
    )
    def test_derive_freshness_table(self, days_old: float, expected: str) -> None:
        fetched = datetime.now(UTC) - timedelta(days=days_old)
        assert FactPack.derive_freshness(fetched) == expected

    def test_month_old_pack_is_stale_not_an_error(self) -> None:
        """Regression guard: a 16d+ cache entry used to raise ValueError, which
        FactPackCache.get() caught and returned None — indistinguishable from no
        cache at all. A rate-limited run then had nothing to fall back on and the
        holding died outright, instead of degrading to a labelled stale answer.
        Corporate structure and leadership do not turn over in a fortnight.
        """
        month_old = datetime.now(UTC) - timedelta(days=30)
        assert FactPack.derive_freshness(month_old) == "stale"

    def test_derive_freshness_raises_beyond_new_horizon(self) -> None:
        ancient = datetime.now(UTC) - timedelta(days=91)
        with pytest.raises(ValueError, match="older than 90 days"):
            FactPack.derive_freshness(ancient)


class TestFactPackValidation:
    def test_minimal_valid_factpack(self) -> None:
        fp = _build()
        assert fp.corporate_structure
        assert fp.confidence == 0.9

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FactPack(
                corporate_structure="x",
                recent_events=[],
                leadership="x",
                fetched_at=datetime.now(UTC),
                freshness="fresh",
                confidence=0.5,
                source_citations=[],
                unknown_field="boom",  # type: ignore[call-arg]
            )

    def test_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FactPack(
                corporate_structure="x",
                recent_events=[],
                leadership="x",
                fetched_at=datetime.now(UTC),
                freshness="fresh",
                confidence=1.5,
                source_citations=[],
            )

    def test_recent_events_max_length(self) -> None:
        with pytest.raises(ValidationError):
            FactPack(
                corporate_structure="x",
                recent_events=[f"event {i}" for i in range(11)],
                leadership="x",
                fetched_at=datetime.now(UTC),
                freshness="fresh",
                confidence=0.5,
                source_citations=[],
            )


class TestAILiesAboutFreshness:
    """The model_validator catches AI lies about freshness."""

    def test_lying_freshness_raises(self) -> None:
        # Fetched 5 days ago (recent) but claims fresh — should raise
        fetched = datetime.now(UTC) - timedelta(days=5)
        with pytest.raises(ValidationError, match="contradicts"):
            FactPack(
                corporate_structure="x",
                recent_events=[],
                leadership="x",
                fetched_at=fetched,
                freshness="fresh",  # LIE — should be "recent"
                confidence=0.5,
                source_citations=[],
            )

    def test_fetched_at_naive_treated_as_utc(self) -> None:
        """Naive datetime (no tz) gets coerced to UTC for derivation."""
        naive = datetime.now() - timedelta(hours=1)  # 1h ago, naive
        derived = FactPack.derive_freshness(naive)
        assert derived == "fresh"


class TestStageContractIntegration:
    def test_stage_name_includes_fact_pack(self) -> None:
        from finwiz.schemas.stage_contract import StageOutcome, StageProvenance

        # Should be able to construct provenance with stage="fact_pack"
        prov = StageProvenance(
            stage="fact_pack",
            outcome=StageOutcome.OK,
            duration_ms=42,
        )
        assert prov.stage == "fact_pack"

    def test_fact_pack_stage_cannot_degrade(self) -> None:
        """Trust-spine invariant preserved: only `qualify` may DEGRADE."""
        from finwiz.schemas.stage_contract import StageOutcome, StageProvenance

        with pytest.raises(ValidationError, match="DEGRADED"):
            StageProvenance(
                stage="fact_pack",
                outcome=StageOutcome.DEGRADED,
                duration_ms=1,
            )


class TestAttachToQualitativeInsights:
    def test_fact_pack_field_attaches(self) -> None:
        from finwiz.schemas.hybrid_analysis import QualitativeInsights

        fp = _build()
        qual = QualitativeInsights(fact_pack=fp)
        assert qual.fact_pack is not None
        assert qual.fact_pack.confidence == 0.9

    def test_fact_pack_field_defaults_to_none(self) -> None:
        from finwiz.schemas.hybrid_analysis import QualitativeInsights

        qual = QualitativeInsights()
        assert qual.fact_pack is None


class TestSourcesUsed:
    def test_sources_used_round_trips(self):
        fetched_at = datetime.now(UTC)
        pack = FactPack(
            corporate_structure="Apple Inc. designs...",
            leadership="Tim Cook, CEO",
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=1.0,
            sources_used=["yfinance.info", "yfinance.sec_filings"],
        )
        assert pack.sources_used == ["yfinance.info", "yfinance.sec_filings"]

    def test_a_pack_cached_before_sources_used_existed_still_loads(self):
        """The 58 packs already in cache/fact_packs were written without this field.

        FactPack is extra="forbid", so the field had to be added explicitly; this
        pins that adding it did not invalidate everything already on disk.
        """
        fetched_at = datetime.now(UTC)
        legacy = {
            "corporate_structure": "Apple Inc. designs...",
            "recent_events": [],
            "leadership": "Tim Cook, CEO",
            "fetched_at": fetched_at.isoformat(),
            "freshness": FactPack.derive_freshness(fetched_at),
            "confidence": 0.8,
            "source_citations": [],
        }
        assert FactPack.model_validate(legacy).sources_used == []
