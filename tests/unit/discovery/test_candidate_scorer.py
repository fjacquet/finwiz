"""
Unit tests for CandidateScorer source-aware scoring.

These tests prove the fix for the "all Discovered Opportunities graded F" bug:
signal-based sources (momentum, breakout) must be scored on their own
composite, not routed through the fundamentals-oriented ScreeningRanking
which zero-penalizes their missing ROE/revenue/FCF fields.
"""

from __future__ import annotations

import pytest

from finwiz.discovery.candidate_scorer import SIGNAL_BASED_SOURCES, CandidateScorer
from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(
    source: str,
    composite_score: float,
    *,
    ticker: str = "TST",
    asset_class: str = "stock",
    metadata: dict | None = None,
    market_cap: float | None = None,
) -> NewcomerCandidate:
    """Build a NewcomerCandidate for tests with sensible defaults."""
    return NewcomerCandidate(
        ticker=ticker,
        name=ticker,
        asset_class=asset_class,  # type: ignore[arg-type]
        source=source,
        composite_score=composite_score,
        grade="",
        market_cap=market_cap,
        metadata=metadata or {},
    )


class TestSignalBasedSources:
    """Momentum/breakout candidates must be scored on their own composite."""

    @pytest.fixture
    def scorer(self) -> CandidateScorer:
        return CandidateScorer()

    def test_signal_sources_constant_covers_momentum_and_breakout(self) -> None:
        assert "momentum" in SIGNAL_BASED_SOURCES
        assert "breakout" in SIGNAL_BASED_SOURCES

    def test_strong_momentum_candidate_is_not_graded_f(self, scorer: CandidateScorer) -> None:
        """A momentum candidate with composite 0.82 should grade B+, not F."""
        candidate = _make_candidate(
            source="momentum",
            composite_score=0.82,
            ticker="GOOG",
            metadata={"rsi": 73.2, "volume_ratio": 1.0, "momentum_roc": 15.26},
        )

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score == pytest.approx(0.82)
        assert scored.grade == "B+"
        assert scored.grade != "F"

    def test_momentum_candidate_preserves_source_composite(self, scorer: CandidateScorer) -> None:
        """No fundamentals blend for momentum — score must equal the input."""
        candidate = _make_candidate(source="momentum", composite_score=0.62)

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score == pytest.approx(0.62)

    def test_breakout_candidate_preserves_source_composite(self, scorer: CandidateScorer) -> None:
        candidate = _make_candidate(source="breakout", composite_score=0.85)

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score == pytest.approx(0.85)
        assert scored.grade == "A"

    def test_weak_momentum_candidate_still_grades_f(self, scorer: CandidateScorer) -> None:
        """Legitimately weak momentum (<0.50) should still get F — no free passes."""
        candidate = _make_candidate(source="momentum", composite_score=0.31)

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score == pytest.approx(0.31)
        assert scored.grade == "F"

    def test_momentum_bug_regression_sample(self, scorer: CandidateScorer) -> None:
        """Regression: pre-fix, 55/55 discovery opportunities graded F.

        This mirrors the shape of the actual bad run: three strong momentum
        candidates with no fundamentals. Before the fix, preliminary
        collapsed to ~0.25 and blend produced ~0.30-0.43 → all F. After the
        fix, each composite is preserved and all grade ≥ C.
        """
        candidates = [
            _make_candidate(source="momentum", composite_score=0.72, ticker="GOOG"),
            _make_candidate(source="momentum", composite_score=0.68, ticker="DASH"),
            _make_candidate(source="breakout", composite_score=0.81, ticker="SNX"),
        ]

        scored = scorer.score_and_grade(candidates)

        grades = {c.ticker: c.grade for c in scored}
        assert grades["GOOG"] != "F"
        assert grades["DASH"] != "F"
        assert grades["SNX"] != "F"


class TestFundamentalsBasedSources:
    """IPO/universe candidates keep using ScreeningRanking (unchanged behavior)."""

    @pytest.fixture
    def scorer(self) -> CandidateScorer:
        return CandidateScorer()

    def test_ipo_candidate_with_strong_fundamentals(self, scorer: CandidateScorer) -> None:
        """High ROE / growth / low debt / large cap should score well via ScreeningRanking."""
        candidate = _make_candidate(
            source="ipo",
            composite_score=0.0,  # default — forces pure preliminary path
            market_cap=150e9,
            metadata={
                "roe": 0.28,
                "revenue_growth": 0.25,
                "debt_to_equity": 0.15,
                "fcf_positive": True,
                "fcf_growing": True,
                "market_cap": 150e9,
            },
        )

        [scored] = scorer.score_and_grade([candidate])

        # ROE(0.3) + growth(0.25) + debt(0.2) + cap(0.15) + fcf(0.1) = 1.0
        assert scored.composite_score == pytest.approx(1.0)
        assert scored.grade == "A+"

    def test_ipo_candidate_missing_fundamentals_grades_f(self, scorer: CandidateScorer) -> None:
        """IPO with no fundamentals data: expected to fail screening (current behavior).

        This is correct — an IPO screener candidate without fundamentals is
        a legitimate F. Only signal-based sources get the preservation.
        """
        candidate = _make_candidate(source="ipo", composite_score=0.0)

        [scored] = scorer.score_and_grade([candidate])

        assert scored.grade == "F"

    def test_unknown_source_routes_through_screening_ranking(self, scorer: CandidateScorer) -> None:
        """Empty / unknown source falls through to the fundamentals path."""
        candidate = _make_candidate(
            source="",
            composite_score=0.0,
            market_cap=50e9,
            metadata={
                "roe": 0.22,
                "revenue_growth": 0.18,
                "debt_to_equity": 0.25,
                "market_cap": 50e9,
                "fcf_positive": True,
            },
        )

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score > 0.5
        assert scored.grade != "F"


class TestBlendingBehavior:
    """Fundamentals-rich sources still blend with non-default composite_score."""

    @pytest.fixture
    def scorer(self) -> CandidateScorer:
        return CandidateScorer()

    def test_ipo_with_non_default_composite_blends(self, scorer: CandidateScorer) -> None:
        """IPO candidate with composite_score=0.9 blends: 0.6 * prelim + 0.4 * 0.9."""
        candidate = _make_candidate(
            source="ipo",
            composite_score=0.9,  # source signal
            market_cap=150e9,
            metadata={
                "roe": 0.28,
                "revenue_growth": 0.25,
                "debt_to_equity": 0.15,
                "fcf_positive": True,
                "fcf_growing": True,
                "market_cap": 150e9,
            },
        )

        [scored] = scorer.score_and_grade([candidate])

        # preliminary=1.0 → blended = 0.6*1.0 + 0.4*0.9 = 0.96
        assert scored.composite_score == pytest.approx(0.96)
        assert scored.grade == "A+"

    def test_signal_source_never_blends(self, scorer: CandidateScorer) -> None:
        """Momentum composite 0.96 must land at exactly 0.96, no blend dilution."""
        candidate = _make_candidate(source="momentum", composite_score=0.96)

        [scored] = scorer.score_and_grade([candidate])

        assert scored.composite_score == pytest.approx(0.96)
        assert scored.grade == "A+"
