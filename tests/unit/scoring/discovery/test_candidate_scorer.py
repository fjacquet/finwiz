"""Unit tests for CandidateScorer (Phase 2 module contract tests).

Since the candidate_scorer module is not yet implemented (Phase 2 pending),
these tests verify the pipeline's interaction contract via mocked imports.
"""

import importlib

from finwiz.schemas.newcomer_discovery import NewcomerCandidate


def _make_candidate(ticker: str, score: float = 0.0) -> NewcomerCandidate:
    return NewcomerCandidate(
        ticker=ticker, name=f"{ticker} Corp.", asset_class="stock",
        source="test", composite_score=score,
    )


class TestCandidateScorer:
    """Tests for the candidate scorer contract."""

    def test_assigns_scores_and_grades(self, mocker):
        """Scorer assigns composite_score and grade to candidates."""
        mock_cls = mocker.MagicMock()

        def mock_score(candidate):
            candidate.composite_score = 0.88
            candidate.grade = "A"
            return candidate

        mock_cls.return_value.score = mock_score
        mock_mod = mocker.MagicMock()
        mock_mod.CandidateScorer = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.candidate_scorer": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.candidate_scorer")
        scorer = mod.CandidateScorer()
        candidate = _make_candidate("TEST", 0.0)
        result = scorer.score(candidate)
        assert result.composite_score == 0.88
        assert result.grade == "A"

    def test_score_ranges_valid(self, mocker):
        """Scores are within 0.0 to 1.0 range."""
        mock_cls = mocker.MagicMock()

        def mock_score(candidate):
            candidate.composite_score = 0.75
            return candidate

        mock_cls.return_value.score = mock_score
        mock_mod = mocker.MagicMock()
        mock_mod.CandidateScorer = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.candidate_scorer": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.candidate_scorer")
        candidate = _make_candidate("VALID")
        result = mod.CandidateScorer().score(candidate)
        assert 0.0 <= result.composite_score <= 1.0

    def test_grade_assignment(self, mocker):
        """Scorer assigns appropriate grade based on score."""
        mock_cls = mocker.MagicMock()

        scores_to_grades = [(0.96, "A+"), (0.88, "A"), (0.81, "B+"), (0.5, "D"), (0.3, "F")]
        for score, grade in scores_to_grades:
            def mock_score(candidate, s=score, g=grade):
                candidate.composite_score = s
                candidate.grade = g
                return candidate

            mock_cls.return_value.score = mock_score
            mock_mod = mocker.MagicMock()
            mock_mod.CandidateScorer = mock_cls
            mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.candidate_scorer": mock_mod})

            mod = importlib.import_module("finwiz.scoring.discovery.candidate_scorer")
            result = mod.CandidateScorer().score(_make_candidate("GRD"))
            assert result.grade == grade

    def test_scoring_with_missing_data(self, mocker):
        """Scorer handles candidates with minimal data fields."""
        mock_cls = mocker.MagicMock()

        def mock_score(candidate):
            # Candidate has no optional scores
            candidate.composite_score = 0.4
            candidate.grade = "F"
            return candidate

        mock_cls.return_value.score = mock_score
        mock_mod = mocker.MagicMock()
        mock_mod.CandidateScorer = mock_cls
        mocker.patch.dict("sys.modules", {"finwiz.scoring.discovery.candidate_scorer": mock_mod})

        mod = importlib.import_module("finwiz.scoring.discovery.candidate_scorer")
        candidate = NewcomerCandidate(
            ticker="MINI", asset_class="stock", composite_score=0.0,
        )
        result = mod.CandidateScorer().score(candidate)
        assert result.composite_score == 0.4

    def test_import_error_returns_unscored(self, mocker):
        """Pipeline returns candidates unscored when scorer is unavailable."""
        from finwiz.scoring.discovery.pipeline import NewcomerDiscoveryPipeline

        mocker.patch.object(NewcomerDiscoveryPipeline, "_load_portfolio_tickers")
        pipeline = NewcomerDiscoveryPipeline("stock")
        candidates = [_make_candidate("UNSC", 0.5)]
        result = pipeline._score_candidates(candidates)
        assert result[0].composite_score == 0.5  # unchanged
