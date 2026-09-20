"""The composite score tolerates a fundamental score that could not be computed."""

import pytest

from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer


@pytest.fixture
def scorer(mocker):
    """A scorer whose additive overlays are neutralized.

    _compute_weighted_score applies a sentiment and a macro overlay after the
    composite. Both are gated on feature flags and can read real data, so they
    are stubbed to keep this test about the weighting alone.
    """
    instance = DeepAnalysisScorer()
    mocker.patch.object(instance, "_calculate_sentiment_overlay", return_value=(0.0, {"sentiment_overlay_applied": False}))
    mocker.patch.object(instance, "_calculate_macro_overlay", return_value=(0.0, {"macro_overlay_applied": False}))
    return instance


def test_composite_renormalizes_when_fundamental_is_none(scorer):
    scores = {"fundamental_score": None, "fundamental_details": {}, "technical_score": 0.8, "risk_score": 0.6}

    composite = scorer._compute_weighted_score(scores, {"asset_class": "crypto"})

    # technical 0.30 and risk 0.30 renormalize to 0.5 each: 0.5*0.8 + 0.5*0.6
    assert composite == pytest.approx(0.7)
    assert scores["weights_used"]["fundamental"] == 0.0


def test_composite_is_unchanged_when_fundamental_is_present(scorer):
    scores = {"fundamental_score": 0.9, "fundamental_details": {}, "technical_score": 0.8, "risk_score": 0.6}

    composite = scorer._compute_weighted_score(scores, {"asset_class": "crypto"})

    assert composite == pytest.approx(0.4 * 0.9 + 0.3 * 0.8 + 0.3 * 0.6)
