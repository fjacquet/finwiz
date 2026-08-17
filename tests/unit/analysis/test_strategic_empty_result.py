"""A strategic gather that produced nothing must say so, not hand back an empty shell.

``gather_strategic_analysis`` used to return ``StrategicAnalysis(swot=None,
five_forces=None)`` after logging that both frameworks had failed. That
object is truthy end-to-end: it survives ``if ticker and sa``, validates
cleanly (all fields are Optional), and lands in the portfolio coverage set —
so a total provider outage rendered "64 / 64 holdings · 100.0 %" above a
score synthesized from 64 empty objects.

The absence of data must be representable. ``None`` is that representation, and
every caller already handles it (``stages/__init__.py`` guards
``if strategic is not None``; ``_safe_strategic`` already returns ``None`` on an
exception).
"""

from __future__ import annotations

import pytest

from finwiz.schemas.hybrid_analysis.strategic import SwotAnalysis


@pytest.fixture
def strategic_research():
    import finwiz.analysis.strategic_research as module

    return module


def _swot() -> SwotAnalysis:
    return SwotAnalysis(strategic_score=0.62, confidence=0.7)


class TestAllFrameworksFailed:
    async def test_gather_returns_none_when_both_frameworks_fail(self, strategic_research, mocker):
        """No evidence at all must not be dressed up as a StrategicAnalysis."""
        mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))

        result = await strategic_research.gather_strategic_analysis(ticker="AAPL")

        assert result is None

    def test_gather_sync_returns_none_when_both_frameworks_fail(self, strategic_research, mocker):
        mocker.patch.object(strategic_research, "perplexity_with_retry", new=mocker.AsyncMock(return_value=None))

        assert strategic_research.gather_strategic_analysis_sync(ticker="AAPL") is None

    def test_safe_strategic_passes_the_none_through(self, mocker):
        """_safe_strategic must not resurrect an empty object from a None gather."""
        from finwiz.analysis.stages.qualify import _safe_strategic

        mocker.patch("finwiz.analysis.strategic_research.gather_strategic_analysis_sync", return_value=None)

        assert _safe_strategic("AAPL", "Tech", "Software", "desc") is None


class TestPartialResultsSurvive:
    """A partial result carries real evidence and must NOT be discarded.

    Of 26 strategic blobs in the last production run, 25 were complete and one
    was partial. Turning "both failed" into ``None`` must not turn "one of two
    succeeded" into ``None`` as well — that would be the lost-data failure
    mode instead of the wrong-data one.
    """

    async def test_gather_returns_the_analysis_when_only_swot_succeeds(self, strategic_research, mocker):
        swot = _swot()
        # Dispatch on the requested schema, not on call order: asyncio.gather
        # makes the await order an implementation detail.
        mocker.patch.object(
            strategic_research,
            "perplexity_with_retry",
            new=mocker.AsyncMock(side_effect=lambda **kwargs: swot if kwargs["schema"] is SwotAnalysis else None),
        )

        result = await strategic_research.gather_strategic_analysis(ticker="AAPL")

        assert result is not None
        assert result.swot is swot
        assert result.five_forces is None
        assert result.composite_strategic_score is not None
