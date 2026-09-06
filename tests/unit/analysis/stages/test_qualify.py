"""Unit tests for the qualify stage StageResult contract."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from finwiz.analysis.stages._ledger import RunLedger
from finwiz.analysis.stages._resilience import StageContext
from finwiz.analysis.stages.qualify import (
    _promote_to_qualitative,
    _QualitativeInsightsRaw,
    qualify,
)
from finwiz.schemas.hybrid_analysis import QualitativeInsights, QuantitativeAnalysis
from finwiz.schemas.hybrid_analysis.fact_pack import EquityFacts, FactPack
from finwiz.schemas.stage_contract import StageOutcome


def test_qualify_returns_ok(tmp_path: Path, mocker: Any) -> None:
    fake_qual = QualitativeInsights()
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        return_value=fake_qual,
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    quant = QuantitativeAnalysis.model_construct()
    result = qualify(ctx, quant, {})
    assert result.provenance.outcome == StageOutcome.OK
    assert result.payload is fake_qual


def test_qualify_records_ledger_entry(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        return_value=QualitativeInsights(),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert any(e.stage == "qualify" for e in ctx.ledger.entries)


def test_qualify_failure_becomes_failed(tmp_path: Path, mocker: Any) -> None:
    mocker.patch(
        "finwiz.analysis.stages.qualify._try_ai_qualify",
        side_effect=RuntimeError("crew error"),
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert result.payload is None
    assert result.provenance.outcome == StageOutcome.FAILED


def test_qualify_degraded_when_ai_returns_none(tmp_path: Path, mocker: Any) -> None:
    """v0.3.0 regression: AI null must produce DEGRADED, not silent OK."""
    mocker.patch("finwiz.analysis.stages.qualify._try_ai_qualify", return_value=None)
    fake_proxy = QualitativeInsights.model_construct()
    mocker.patch(
        "finwiz.analysis.stages.qualify._python_proxy_qualify",
        return_value=fake_proxy,
    )
    ctx = StageContext(
        ticker="AAPL",
        run_id="r1",
        ledger=RunLedger(run_id="r1", artifact_dir=tmp_path),
        extras={"analysis_ctx": mocker.MagicMock()},
    )
    result = qualify(ctx, QuantitativeAnalysis.model_construct(), {})
    assert result.provenance.outcome == StageOutcome.DEGRADED
    assert result.provenance.fallback_used == "python_proxy_qualitative"
    assert result.payload is fake_proxy


# ---------------------------------------------------------------------------
# WS2 — Bridging schema regression tests (2026-04-28 LLM/Pydantic thrash)
# ---------------------------------------------------------------------------


class TestQualitativeInsightsRaw:
    """The bridging schema must accept output where the LLM still emits
    Python-controlled fields. The 2026-04-28 cascade was driven by the LLM
    setting ``fact_pack.freshness`` and ``fact_pack.fetched_at`` to values
    that contradicted each other — Pydantic rejected, CrewAI retried, and
    the 600s per-holding budget was exhausted. With ``extra="ignore"`` the
    bridging schema silently drops those keys.
    """

    def test_raw_drops_llm_supplied_fact_pack(self) -> None:
        # Mimic an LLM output that contradicts itself on freshness/fetched_at —
        # exactly the shape that thrashed CrewAI's retry loop on 2026-04-28.
        payload = {
            "ai_confidence": 0.6,
            "fact_pack": {
                "corporate_structure": "Independent",
                "recent_events": ["x" * 250],
                "leadership": "y" * 1500,
                "fetched_at": "2026-04-15T08:00:00+00:00",
                "freshness": "fresh",
                "confidence": 0.5,
                "source_citations": [],
            },
            "fetched_at": "2026-04-15T08:00:00+00:00",
            "freshness": "fresh",
            "analysis_timestamp": "2026-04-28T18:39:00+00:00",
        }
        raw = _QualitativeInsightsRaw.model_validate(payload)
        # No fact_pack / analysis_timestamp keys leak through to the bridging schema.
        dumped = raw.model_dump()
        assert "fact_pack" not in dumped
        assert "analysis_timestamp" not in dumped
        assert "freshness" not in dumped
        assert dumped["ai_confidence"] == 0.6

    def test_raw_accepts_no_fact_pack_at_all(self) -> None:
        raw = _QualitativeInsightsRaw.model_validate({"ai_confidence": 0.5})
        assert raw.ai_confidence == 0.5
        assert raw.investment_synthesis is None


class TestPromoteToQualitative:
    """Promotion attaches the deterministic fact_pack and a fresh timestamp."""

    def test_promote_attaches_python_fact_pack(self) -> None:
        raw = _QualitativeInsightsRaw(ai_confidence=0.7)
        fetched_at = datetime.now(UTC)
        fp = FactPack(
            asset_class="stock",
            details=EquityFacts(business_summary="Independent", leadership="CEO: Jane Doe"),
            fetched_at=fetched_at,
            freshness=FactPack.derive_freshness(fetched_at),
            confidence=0.8,
            source_citations=[],
        )
        promoted = _promote_to_qualitative(raw, fact_pack=fp)
        assert isinstance(promoted, QualitativeInsights)
        assert promoted.fact_pack is not None
        assert promoted.fact_pack.details.leadership == "CEO: Jane Doe"
        assert promoted.analysis_timestamp is not None
        assert promoted.ai_confidence == 0.7

    def test_promote_without_fact_pack_yields_none_field(self) -> None:
        raw = _QualitativeInsightsRaw(ai_confidence=0.4)
        promoted = _promote_to_qualitative(raw, fact_pack=None)
        assert promoted.fact_pack is None
        assert promoted.analysis_timestamp is not None
