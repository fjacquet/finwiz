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
    async def test_fetch_routes_through_retry_wrapper(self, mocker: Any) -> None:
        """fetch_fact_pack must call perplexity_with_retry (Task 1's wrapper), not
        perplexity_structured directly, so the single fact_pack call gets retry +
        backoff instead of failing outright on the first timeout/429.
        """
        called = mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_with_retry",
            new=mocker.AsyncMock(return_value=None),
        )

        result = await fetch_fact_pack("NVDA", "NVIDIA Corp", "Technology", "Semiconductors")

        assert result is None
        assert called.await_count == 1
        assert called.await_args.kwargs["schema"] is _FactPackRaw
        assert called.await_args.kwargs["search_recency_filter"] == "month"

    @pytest.mark.asyncio
    async def test_fetch_returns_factpack_with_python_freshness(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_with_retry",
            new=mocker.AsyncMock(return_value=_build_raw()),
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies", "Tech", "Hardware")
        assert fp is not None
        assert fp.corporate_structure.startswith("Independent")
        assert fp.freshness == "fresh"  # Just fetched
        assert fp.confidence == 0.92
        # Python set fetched_at, NOT AI
        assert fp.fetched_at.tzinfo is not None

    @pytest.mark.asyncio
    async def test_fetch_returns_none_when_wrapper_raises(self, mocker: Any) -> None:
        """perplexity_with_retry already catches every exception internally and
        returns None on failure, so it shouldn't raise in normal operation. The
        try/except in fetch_fact_pack is defensive depth at the stage boundary
        (guards against the wrapper's contract changing later) rather than
        something this call site currently relies on for a *known* failure mode.
        """
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_with_retry",
            new=mocker.AsyncMock(side_effect=RuntimeError("unexpected")),
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies")
        assert fp is None

    @pytest.mark.asyncio
    async def test_fetch_returns_none_on_wrapper_returning_none(self, mocker: Any) -> None:
        mocker.patch(
            "finwiz.analysis.fact_pack_research.perplexity_with_retry",
            new=mocker.AsyncMock(return_value=None),
        )
        fp = await fetch_fact_pack("DELL", "Dell Technologies")
        assert fp is None


# ---------------------------------------------------------------------------
# WS-D.2 — Truncating-validator regression tests (2026-04-29 follow-up)
# ---------------------------------------------------------------------------


class TestFactPackRawTruncatingValidators:
    """The Perplexity LLM repeatedly returned events longer than 200 chars on
    the 2026-04-29 run, which made the deterministic fact_pack stage fail
    intermittently and short-circuited the whole pipeline. Validators are
    now *truncating / filtering* — they normalize the LLM's output and log
    a warning, but never raise.
    """

    def test_truncates_overlong_event(self, caplog) -> None:
        import logging

        long_event = "A" * 250
        # Truncation is logged at DEBUG (by-design normalization, not a warning).
        caplog.set_level(logging.DEBUG, logger="finwiz.analysis.fact_pack_research")
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "Independent",
                "recent_events": [long_event],
                "leadership": "CEO: Jane Doe",
                "confidence": 0.7,
                "source_citations": [],
            },
        )
        assert len(raw.recent_events[0]) == 200
        assert any("recent_events[0] truncated" in r.message for r in caplog.records)

    def test_drops_empty_events(self) -> None:
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "Independent",
                "recent_events": ["valid event", "", "   ", "another"],
                "leadership": "CEO",
                "confidence": 0.5,
                "source_citations": [],
            },
        )
        assert raw.recent_events == ["valid event", "another"]

    def test_truncates_overlong_leadership(self, caplog) -> None:
        import logging

        long_leadership = "B" * 1500
        caplog.set_level(logging.WARNING, logger="finwiz.analysis.fact_pack_research")
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "Independent",
                "recent_events": [],
                "leadership": long_leadership,
                "confidence": 0.5,
                "source_citations": [],
            },
        )
        assert len(raw.leadership) == 1000
        assert any("leadership truncated" in r.message for r in caplog.records)

    def test_truncates_overlong_corporate_structure(self, caplog) -> None:
        import logging

        long_struct = "C" * 2500
        caplog.set_level(logging.WARNING, logger="finwiz.analysis.fact_pack_research")
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": long_struct,
                "recent_events": [],
                "leadership": "CEO",
                "confidence": 0.5,
                "source_citations": [],
            },
        )
        assert len(raw.corporate_structure) == 2000
        assert any("corporate_structure truncated" in r.message for r in caplog.records)

    def test_drops_invalid_citation_urls(self, caplog) -> None:
        import logging

        caplog.set_level(logging.WARNING, logger="finwiz.analysis.fact_pack_research")
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "Independent",
                "recent_events": [],
                "leadership": "CEO",
                "confidence": 0.5,
                "source_citations": [
                    "https://example.com/ok",
                    "ftp://bad.example.com",
                    "not-a-url",
                    "http://also-ok.example.com",
                ],
            },
        )
        assert raw.source_citations == [
            "https://example.com/ok",
            "http://also-ok.example.com",
        ]
        assert any("Dropped 2 non-http(s)" in r.message for r in caplog.records)

    def test_substitutes_placeholder_for_empty_prose(self) -> None:
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "  ",
                "recent_events": [],
                "leadership": "",
                "confidence": 0.5,
                "source_citations": [],
            },
        )
        # Both prose fields default to the French placeholder rather than raising.
        assert raw.leadership == "Information indisponible"
        assert raw.corporate_structure == "Information indisponible"

    def test_extra_fields_ignored(self) -> None:
        # extra="ignore" — LLM may emit extra keys; they must not raise.
        raw = _FactPackRaw.model_validate(
            {
                "corporate_structure": "Independent",
                "recent_events": [],
                "leadership": "CEO",
                "confidence": 0.5,
                "source_citations": [],
                "fetched_at": "2026-04-15T08:00:00+00:00",
                "freshness": "fresh",
                "unknown_llm_field": "garbage",
            },
        )
        assert raw.confidence == 0.5
