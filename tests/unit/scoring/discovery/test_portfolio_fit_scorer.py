"""Unit tests for PortfolioFitScorer (Portfolio-Aware Opportunity Cascade)."""

from __future__ import annotations

import pytest

from finwiz.schemas.newcomer_discovery import PortfolioGapProfile
from finwiz.scoring.discovery.portfolio_fit_scorer import NEUTRAL_FIT, PortfolioFitScorer


@pytest.fixture
def scorer() -> PortfolioFitScorer:
    return PortfolioFitScorer()


def _profile(**overrides) -> PortfolioGapProfile:
    base = {
        "session_id": "t",
        "holdings": ["AAPL", "MSFT"],
        "sector_weights": {"Technology": 1.0},
        "underweight_sectors": ["Healthcare", "Energy"],
        "holding_returns": {"AAPL": [0.01, -0.02, 0.03, 0.0, 0.01]},
        "mean_risk_score": 0.5,
        "is_empty": False,
    }
    base.update(overrides)
    return PortfolioGapProfile(**base)


def test_empty_profile_returns_neutral(scorer: PortfolioFitScorer) -> None:
    profile = PortfolioGapProfile(is_empty=True)
    fit, gap = scorer.score(profile, sector="Technology")
    assert fit == NEUTRAL_FIT
    assert gap is None


def test_no_usable_inputs_returns_neutral(scorer: PortfolioFitScorer) -> None:
    fit, gap = scorer.score(_profile())  # no sector/returns/risk supplied
    assert fit == NEUTRAL_FIT


def test_underweight_sector_scores_high_and_labels_gap(scorer: PortfolioFitScorer) -> None:
    fit, gap = scorer.score(_profile(), sector="Healthcare")
    assert fit > 0.9  # 1 - held_share(0.0) = 1.0
    assert gap == "Healthcare"


def test_overheld_sector_scores_low(scorer: PortfolioFitScorer) -> None:
    fit, gap = scorer.score(_profile(), sector="Technology")
    assert fit < 0.1  # 1 - held_share(1.0) = 0.0
    assert gap is None


def test_diversification_rewards_low_correlation(scorer: PortfolioFitScorer) -> None:
    # Candidate perfectly anti-correlated to AAPL -> abs corr 1.0 -> low diversification
    anti = [-0.01, 0.02, -0.03, 0.0, -0.01]
    corr_fit, _ = scorer.score(_profile(), returns=anti)
    # Candidate uncorrelated-ish -> higher diversification
    uncorr = [0.02, 0.02, -0.01, 0.03, -0.02]
    uncorr_fit, _ = scorer.score(_profile(), returns=uncorr)
    assert uncorr_fit >= corr_fit


def test_lower_risk_than_average_scores_higher(scorer: PortfolioFitScorer) -> None:
    safe, _ = scorer.score(_profile(), risk_score=0.9)  # safer than mean 0.5
    risky, _ = scorer.score(_profile(), risk_score=0.1)  # riskier than mean
    assert safe > risky


def test_missing_sector_redistributes_weight(scorer: PortfolioFitScorer) -> None:
    # Only risk term available -> fit equals the risk term itself (weight renormalized)
    fit, _ = scorer.score(_profile(), risk_score=0.9)
    assert fit == pytest.approx(0.5 + (0.9 - 0.5))  # 0.9


def test_fit_is_bounded(scorer: PortfolioFitScorer) -> None:
    fit, _ = scorer.score(_profile(), sector="Healthcare", risk_score=2.0)  # absurd risk
    assert 0.0 <= fit <= 1.0


def test_score_for_slot_rewards_same_sector(scorer: PortfolioFitScorer) -> None:
    # Same-sector candidate for a Tech slot gets nudged up vs plain score
    plain, _ = scorer.score(_profile(), sector="Technology")
    slot, gap = scorer.score_for_slot(_profile(), slot_sector="Technology", sector="Technology")
    assert slot > plain
    assert gap == "Technology"
