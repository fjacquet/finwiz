"""Tests for fact_pack_research fetcher (v5.2)."""

from __future__ import annotations

from typing import Any

import pytest

from finwiz.analysis.fact_pack_research import (
    _build_prompt,
    _FactPackRaw,
    fetch_fact_pack,
)


def _build_raw() -> _FactPackRaw:
    return _FactPackRaw(
        corporate_structure="Independent — divested VMware November 2021.",
        recent_events=["Q4 earnings beat"],
        leadership="Michael Dell (CEO)",
        confidence=0.92,
        source_citations=["https://example.com/dell"],
    )


class TestPromptBuilder:
    def test_prompt_contains_today_and_company(self) -> None:
        prompt = _build_prompt("DELL", "Dell Technologies", "Technology", "Hardware")
        assert "Dell Technologies" in prompt
        assert "DELL" in prompt
        assert "Technology" in prompt
        # French today date should contain a French month
        assert any(m in prompt for m in ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"])

    def test_prompt_handles_missing_sector(self) -> None:
        prompt = _build_prompt("X", "Xenon", None, None)
        assert "secteur inconnu" in prompt
        assert "industrie inconnue" in prompt


class TestFetchFactPack:
    @pytest.mark.asyncio
    async def test_fetch_returns_factpack_with_python_freshness(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_structured",
            return_value=_build_raw(),
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies", "Tech", "Hardware")
        assert fp is not None
        assert fp.corporate_structure.startswith("Independent")
        assert fp.freshness == "fresh"  # Just fetched
        assert fp.confidence == 0.92
        # Python set fetched_at, NOT AI
        assert fp.fetched_at.tzinfo is not None

    @pytest.mark.asyncio
    async def test_fetch_returns_none_on_perplexity_failure(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_structured",
            side_effect=RuntimeError("Perplexity down"),
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies")
        assert fp is None

    @pytest.mark.asyncio
    async def test_fetch_returns_none_on_perplexity_returning_none(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_structured",
            return_value=None,
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies")
        assert fp is None
