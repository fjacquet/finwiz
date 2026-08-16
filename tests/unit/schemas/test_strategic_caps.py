"""Tests for the strategic schema caps that bound PESTEL/SWOT/Porter field sizes.

An over-long AI response must be clamped, never rejected — rejecting it would
turn model verbosity into a lost holding, which is the failure this whole
plan exists to remove.
"""

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_PESTEL,
    MAX_BULLETS_SWOT,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    FiveForcesAnalysis,
    ForceRating,
    PestelAnalysis,
    SwotAnalysis,
)


def test_oversized_model_output_is_clamped_not_rejected():
    """An over-long response must be trimmed, never raise.

    Rejecting would turn verbosity into a lost holding, which is the failure this
    whole plan exists to remove.
    """
    pestel = PestelAnalysis.model_validate(
        {
            "political": ["x" * 5000, "y" * 5000, "z" * 5000, "w" * 5000, "v" * 5000],
            "strategic_score": 0.7,
            "confidence": 0.8,
        }
    )

    assert len(pestel.political) == 3
    assert all(len(b) <= MAX_BULLET_CHARS for b in pestel.political)


def test_prose_fields_are_clamped():
    swot = SwotAnalysis.model_validate({"strategic_assessment": "a" * 9000, "strategic_score": 0.5, "confidence": 0.5})

    assert len(swot.strategic_assessment) <= MAX_PROSE_CHARS


def test_pestel_all_six_dimensions_are_clamped_lists():
    pestel = PestelAnalysis.model_validate(
        {
            "political": ["p1", "p2", "p3", "p4"],
            "economic": ["e1", "e2", "e3", "e4"],
            "social": ["s1", "s2", "s3", "s4"],
            "technological": ["t1", "t2", "t3", "t4"],
            "environmental": ["v1", "v2", "v3", "v4"],
            "legal": ["l1", "l2", "l3", "l4"],
        }
    )

    for dimension in (pestel.political, pestel.economic, pestel.social, pestel.technological, pestel.environmental, pestel.legal):
        assert isinstance(dimension, list)
        assert len(dimension) == MAX_BULLETS_PESTEL


def test_pestel_key_threats_and_opportunities_are_clamped():
    pestel = PestelAnalysis.model_validate(
        {
            "key_threats": ["t1", "t2", "t3", "t4", "t5"],
            "key_opportunities": ["o1", "o2", "o3", "o4", "o5"],
        }
    )

    assert len(pestel.key_threats) == MAX_BULLETS_PESTEL
    assert len(pestel.key_opportunities) == MAX_BULLETS_PESTEL


def test_pestel_under_limit_values_pass_through_unchanged():
    pestel = PestelAnalysis.model_validate({"political": ["short bullet"]})

    assert pestel.political == ["short bullet"]


def test_pestel_dimension_accepts_dict_items_like_prior_contract():
    """The model sometimes returns dicts where strings are expected; that
    coercion behavior (via _coerce_str_list) must survive clamping."""
    pestel = PestelAnalysis.model_validate(
        {"political": [{"name": "Tariffs", "severity": "high"}]},
    )

    assert pestel.political == ["Tariffs (Sévérité: high)"]


def test_swot_lists_are_clamped_to_max_bullets_swot():
    swot = SwotAnalysis.model_validate(
        {
            "strengths": ["s1", "s2", "s3", "s4", "s5", "s6"],
            "weaknesses": ["w1", "w2", "w3", "w4", "w5"],
            "opportunities": ["o1", "o2", "o3", "o4", "o5"],
            "threats": ["t1", "t2", "t3", "t4", "t5"],
        }
    )

    assert len(swot.strengths) == MAX_BULLETS_SWOT
    assert len(swot.weaknesses) == MAX_BULLETS_SWOT
    assert len(swot.opportunities) == MAX_BULLETS_SWOT
    assert len(swot.threats) == MAX_BULLETS_SWOT


def test_force_rating_rationale_is_clamped():
    rating = ForceRating.model_validate({"intensity": "HIGH", "rationale": "r" * 900})

    assert len(rating.rationale) <= MAX_RATIONALE_CHARS


def test_five_forces_summary_is_clamped():
    forces = FiveForcesAnalysis.model_validate({"competitive_position_summary": "c" * 900})

    assert len(forces.competitive_position_summary) <= MAX_PROSE_CHARS


def test_clamp_constants_have_expected_values():
    assert MAX_BULLETS_PESTEL == 3
    assert MAX_BULLETS_SWOT == 4
    assert MAX_BULLET_CHARS == 200
    assert MAX_PROSE_CHARS == 400
    assert MAX_RATIONALE_CHARS == 250
