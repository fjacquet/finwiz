"""Tests for FactPack schema (v5.2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from finwiz.schemas.hybrid_analysis.fact_pack import (
    CryptoFacts,
    EquityFacts,
    FactPack,
    FundFacts,
    FundHolding,
)


def _build(fetched_at: datetime | None = None, freshness: str = "fresh") -> FactPack:
    _fetched_at = fetched_at or datetime.now(UTC)
    return FactPack(
        asset_class="stock",
        details=EquityFacts(
            business_summary="Independent — divested VMware Nov 2021",
            leadership="Michael Dell (CEO), Yvonne McGill (CFO)",
            recent_events=["Q4 earnings beat expectations"],
            events_from_filings=False,
        ),
        fetched_at=_fetched_at,
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
        assert fp.details.business_summary
        assert fp.confidence == 0.9

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            FactPack(
                asset_class="stock",
                details=EquityFacts(business_summary="x", leadership="x", recent_events=[], events_from_filings=False),
                fetched_at=datetime.now(UTC),
                freshness="fresh",
                confidence=0.5,
                source_citations=[],
                unknown_field="boom",  # type: ignore[call-arg]
            )

    def test_confidence_out_of_range_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FactPack(
                asset_class="stock",
                details=EquityFacts(business_summary="x", leadership="x", recent_events=[], events_from_filings=False),
                fetched_at=datetime.now(UTC),
                freshness="fresh",
                confidence=1.5,
                source_citations=[],
            )

    def test_recent_events_max_length(self) -> None:
        with pytest.raises(ValidationError):
            EquityFacts(
                business_summary="x",
                leadership="x",
                recent_events=[f"event {i}" for i in range(11)],
                events_from_filings=False,
            )


class TestAILiesAboutFreshness:
    """The model_validator catches AI lies about freshness."""

    def test_lying_freshness_raises(self) -> None:
        # Fetched 5 days ago (recent) but claims fresh — should raise
        fetched = datetime.now(UTC) - timedelta(days=5)
        with pytest.raises(ValidationError, match="contradicts"):
            FactPack(
                asset_class="stock",
                details=EquityFacts(business_summary="x", leadership="x", recent_events=[], events_from_filings=False),
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
            asset_class="stock",
            details=EquityFacts(business_summary="Apple Inc. designs...", leadership="Tim Cook, CEO", recent_events=[], events_from_filings=False),
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=1.0,
            sources_used=["yfinance.info", "yfinance.sec_filings"],
        )
        assert pack.sources_used == ["yfinance.info", "yfinance.sec_filings"]

    def test_a_pack_cached_before_sources_used_existed_still_loads(self):
        """Backward-compat: packs cached without asset_class or details cannot validate.

        The 58 packs already in cache/fact_packs were written before this refactor.
        They lack asset_class and details, so they fail validation now.
        The cache is invalidated once by Task 7 (run-gate final sweep) for this reason.
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
        with pytest.raises(ValidationError):
            FactPack.model_validate(legacy)


class TestPerClassDetails:
    @staticmethod
    def _envelope(**overrides):
        fetched_at = datetime.now(UTC)
        base = {
            "asset_class": "stock",
            "fetched_at": fetched_at,
            "freshness": FactPack.derive_freshness(fetched_at),
            "confidence": 1.0,
            "details": EquityFacts(business_summary="Designs phones.", leadership="Tim Cook (CEO)", recent_events=["2026-09-01 8-K: Changes"], events_from_filings=True),
        }
        return {**base, **overrides}

    def test_an_equity_pack_carries_equity_facts(self):
        pack = FactPack(**self._envelope())
        assert pack.details.kind == "equity"
        assert pack.details.leadership == "Tim Cook (CEO)"

    def test_a_fund_pack_carries_fund_facts(self):
        details = FundFacts(
            issuer="BlackRock Asset Management Ireland - ETF",
            legal_type="Exchange Traded Fund",
            inception_year=2020,
            expense_ratio=0.002,
            turnover=0.0,
            top_holdings=[FundHolding(symbol="NVDA", name="NVIDIA Corp", weight=0.077756)],
            asset_mix={"stockPosition": 0.9942},
            sector_weights={"technology": 0.25},
        )
        pack = FactPack(**self._envelope(asset_class="etf", details=details))
        assert pack.details.kind == "fund"
        assert pack.details.top_holdings[0].symbol == "NVDA"

    def test_a_capped_and_an_uncapped_crypto_are_distinguishable(self):
        """maxSupply == 0 means 'no cap'. It is information, not absence."""
        btc = CryptoFacts(
            description="Bitcoin is...",
            launched_year=2010,
            circulating_supply=20080456.0,
            max_supply=21000000.0,
            supply_is_capped=True,
            market_cap=1.6e12,
            volume_24h_market_cap_pct=0.0125,
        )
        eth = CryptoFacts(
            description="Ethereum is...",
            launched_year=2015,
            circulating_supply=122023856.0,
            max_supply=None,
            supply_is_capped=False,
            market_cap=4.0e11,
            volume_24h_market_cap_pct=0.02,
        )

        assert btc.supply_is_capped is True and btc.max_supply == 21000000.0
        assert eth.supply_is_capped is False and eth.max_supply is None

    def test_an_unknown_discriminator_is_rejected(self):
        """A payload naming a class we do not model must not validate.

        Asserting on a payload that is merely incomplete would pass for the
        wrong reason -- it would fail on a missing required field rather than
        on the discriminator.
        """
        envelope = self._envelope(asset_class="etf")
        envelope["details"] = {"kind": "commodity", "issuer": "Somebody"}
        with pytest.raises(ValidationError):
            FactPack.model_validate(envelope)

    def test_business_summary_is_capped_at_two_thousand(self):
        with pytest.raises(ValidationError):
            EquityFacts(
                business_summary="x" * 2001,
                leadership="Someone",
                recent_events=[],
                events_from_filings=False,
            )

    def test_crypto_supply_cap_consistency_rejects_capped_with_no_max(self):
        """supply_is_capped=True requires max_supply to be not None."""
        with pytest.raises(ValidationError, match="contradicts"):
            CryptoFacts(
                description="Bitcoin is...",
                supply_is_capped=True,
                max_supply=None,
            )

    def test_crypto_supply_cap_consistency_rejects_uncapped_with_max(self):
        """supply_is_capped=False requires max_supply to be None."""
        with pytest.raises(ValidationError, match="contradicts"):
            CryptoFacts(
                description="Ethereum is...",
                supply_is_capped=False,
                max_supply=21000000.0,
            )
