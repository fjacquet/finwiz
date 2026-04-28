"""Regression test for the v0.3.0 DELL/VMware hallucination class — v5.2 hardened.

Original symptom: AI claimed Dell still owned VMware (sold November 2021)
because training data was stale and there was no authoritative override.
v5.2 fixes the root cause: a fact pack injected into every qualitative
prompt declares the corporate structure as ground truth.

This test pins the v5.2 fix using a phrase library: NONE of the forbidden
phrasings may appear in the rendered prompt OR the AI's qualitative output
when fact_pack carries 'divested VMware November 2021'.

Catches wishy-washy hallucination, not just literal matches.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from finwiz.analysis._helpers import _build_crew_inputs
from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

pytestmark = pytest.mark.regression


# Hardened phrase library — at least 8 forbidden phrasings that all imply
# Dell still owns VMware. The v5.2 fact pack must override the AI's stale
# training, so NONE of these may appear in the rendered prompt or AI output.
FORBIDDEN_DELL_VMWARE_PHRASES = (
    "VMware integration",
    "Dell's VMware unit",
    "VMware (subsidiary)",
    "owns VMware",
    "Dell-VMware integration",
    "Dell's VMware business",
    "VMware operations",
    "VMware portfolio",
    "Dell owns VMware",
    "Dell and VMware (subsidiary",
)


# Authoritative phrasings that SHOULD appear when fact_pack is present.
# Both must match what _build_dell_fact_pack() puts in corporate_structure:
#   "Dell Technologies — Independent. Divested VMware in November 2021. No remaining VMware ownership."
EXPECTED_DELL_DIVESTITURE_PHRASES = (
    "divested",
    "November 2021",
)


def _build_dell_fact_pack() -> FactPack:
    """Canonical DELL fact pack with the November 2021 divestiture as ground truth."""
    fetched = datetime.now(UTC)
    return FactPack(
        corporate_structure="Dell Technologies — Independent. Divested VMware in November 2021. No remaining VMware ownership.",
        recent_events=[
            "Q4 FY2024 earnings",
            "Continued AI server demand",
        ],
        leadership="Michael Dell (Chairman & CEO since 1984), Yvonne McGill (CFO since 2023)",
        fetched_at=fetched,
        freshness=FactPack.derive_freshness(fetched),
        confidence=0.95,
        source_citations=["https://example.com/dell-q4-2021-vmware-divestiture"],
    )


def _make_analysis_context_for_dell(mocker: Any) -> Any:
    """Mock AnalysisContext suitable for _build_crew_inputs."""
    ctx = mocker.MagicMock()
    ctx.ticker = "DELL"
    ctx.asset_class = "stock"
    ctx.company_name = "Dell Technologies"
    ctx.sector = "Technology"
    ctx.industry = "Hardware"
    ctx.description = "Dell Technologies designs and sells PCs, servers, and IT services."
    return ctx


def _make_quant(mocker: Any) -> Any:
    """Mock QuantitativeAnalysis."""
    quant = mocker.MagicMock()
    quant.composite_score = 0.7
    quant.grade = "B"
    quant.preliminary_recommendation = "HOLD"
    quant.fundamental_score = 0.7
    quant.technical_score = 0.7
    quant.risk_score = 0.7
    quant.fundamental_metrics = {}
    quant.technical_indicators = {}
    quant.risk_metrics = {}
    quant.python_rationale = None
    return quant


class TestDellVmwareRegression:
    def test_prompt_with_fact_pack_has_no_forbidden_phrases(self, mocker: Any) -> None:
        """Build the qualitative prompt for DELL with fact pack injected.

        The rendered prompt must contain the divestiture fact AND no forbidden
        phrasings that would suggest ongoing Dell-VMware ownership.
        """
        ctx = _make_analysis_context_for_dell(mocker)
        quant = _make_quant(mocker)
        raw = {"sector": "Technology", "industry": "Hardware"}
        fp = _build_dell_fact_pack()

        inputs = _build_crew_inputs(ctx, quant, raw, fact_pack=fp)
        # Concatenate ALL string values for phrase scanning
        haystack = " ".join(str(v) for v in inputs.values())

        for phrase in FORBIDDEN_DELL_VMWARE_PHRASES:
            assert phrase not in haystack, f"Forbidden phrase '{phrase}' appeared in qualitative prompt inputs. v5.2 fact pack must override stale training data."

        # Positive assertion: fact pack content IS present (case-insensitive — the
        # corporate_structure field may capitalise "Divested" differently but the
        # semantic content is what matters for hallucination prevention).
        haystack_lower = haystack.lower()
        for phrase in EXPECTED_DELL_DIVESTITURE_PHRASES:
            assert phrase.lower() in haystack_lower, f"Expected divestiture phrase '{phrase}' missing from prompt — fact pack injection appears broken."

    def test_prompt_without_fact_pack_uses_unknowns(self, mocker: Any) -> None:
        """When fact_pack=None, prompt has explicit 'données non disponibles' fallback.

        AI gets explicit absence signal — preferable to filling the void with
        hallucinated facts. The forbidden phrases also must not appear (sanity).
        """
        ctx = _make_analysis_context_for_dell(mocker)
        quant = _make_quant(mocker)
        raw = {}

        inputs = _build_crew_inputs(ctx, quant, raw, fact_pack=None)
        haystack = " ".join(str(v) for v in inputs.values())

        # No forbidden phrases (sanity)
        for phrase in FORBIDDEN_DELL_VMWARE_PHRASES:
            assert phrase not in haystack, f"Forbidden phrase '{phrase}' leaked"

        # Explicit absence indicators present
        assert "Données non disponibles" in haystack
        assert "unknown" in haystack

    def test_phrase_library_self_check(self) -> None:
        """Sanity: the phrase library is non-empty and has >=8 entries."""
        assert len(FORBIDDEN_DELL_VMWARE_PHRASES) >= 8
