"""Tests for the strategic schema caps that bound SWOT/Porter field sizes.

An over-long AI response must be clamped, never rejected — rejecting it would
turn model verbosity into a lost holding, which is the failure this whole
plan exists to remove.
"""

import logging

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_SWOT,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    FiveForcesAnalysis,
    ForceRating,
    SwotAnalysis,
    _coerce_str_list,
)


def test_strategic_analysis_has_two_frameworks():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    assert set(StrategicAnalysis.model_fields) == {"swot", "five_forces"}


def test_a_legacy_analysis_carrying_pestel_still_validates():
    """Stale *_enriched.json is reused when re-analysis fails; it must not break."""
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    analysis = StrategicAnalysis.model_validate(
        {
            "pestel": {"political": ["x"], "strategic_score": 0.9, "confidence": 0.9},
            "swot": {"strengths": ["s"], "strategic_score": 0.6, "confidence": 0.7},
        },
    )

    assert not hasattr(analysis, "pestel")
    assert analysis.composite_strategic_score == 0.6


def test_an_empty_analysis_still_has_no_composite():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis

    assert StrategicAnalysis().composite_strategic_score is None


def test_a_partial_analysis_still_counts():
    from finwiz.schemas.hybrid_analysis.strategic import StrategicAnalysis, SwotAnalysis

    analysis = StrategicAnalysis(swot=SwotAnalysis(strategic_score=0.62))

    assert analysis.composite_strategic_score == 0.62


def test_prose_fields_are_clamped():
    swot = SwotAnalysis.model_validate({"strategic_assessment": "a" * 9000, "strategic_score": 0.5, "confidence": 0.5})

    assert len(swot.strategic_assessment) <= MAX_PROSE_CHARS


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
    assert MAX_BULLETS_SWOT == 4
    assert MAX_BULLET_CHARS == 200
    assert MAX_PROSE_CHARS == 400
    assert MAX_RATIONALE_CHARS == 250


class TestCoerceStrListDataLoss:
    """`_coerce_str_list` must never turn non-empty input into `[]`.

    Before this fix, anything that wasn't already a `list` (a prose string,
    a dict, a bare scalar) silently became `[]` — data vanished with no
    trace. These pin the fix: only genuinely absent data (`None`, `""`)
    is allowed to yield an empty list.
    """

    def test_none_yields_empty_list(self):
        assert _coerce_str_list(None) == []

    def test_empty_string_yields_empty_list(self):
        assert _coerce_str_list("") == []

    def test_blank_string_yields_empty_list(self):
        assert _coerce_str_list("   \n  ") == []

    def test_bare_prose_string_becomes_single_bullet(self):
        text = "Tariff exposure is elevated given the trade policy environment."
        assert _coerce_str_list(text) == [text]

    def test_multiline_string_splits_into_bullets(self):
        text = "Elevated tariff exposure\nWeak currency hedging\nRegulatory uncertainty"
        assert _coerce_str_list(text) == [
            "Elevated tariff exposure",
            "Weak currency hedging",
            "Regulatory uncertainty",
        ]

    def test_dash_marker_lines_strip_the_marker(self):
        text = "- Elevated tariff exposure\n- Weak currency hedging\n- Regulatory uncertainty"
        assert _coerce_str_list(text) == [
            "Elevated tariff exposure",
            "Weak currency hedging",
            "Regulatory uncertainty",
        ]

    def test_bullet_marker_lines_strip_the_marker(self):
        text = "• Elevated tariff exposure\n• Weak currency hedging"
        assert _coerce_str_list(text) == ["Elevated tariff exposure", "Weak currency hedging"]

    def test_empty_fragments_between_newlines_are_stripped(self):
        text = "- Elevated tariff exposure\n\n\n- Weak currency hedging\n"
        assert _coerce_str_list(text) == ["Elevated tariff exposure", "Weak currency hedging"]

    def test_dict_routes_through_coerce_prose(self):
        result = _coerce_str_list({"regulation": "elevated", "trade_policy": "hostile"})
        assert result == ["regulation: elevated | trade_policy: hostile"]

    def test_scalar_int_becomes_single_stringified_bullet(self):
        assert _coerce_str_list(3) == ["3"]

    def test_scalar_float_becomes_single_stringified_bullet(self):
        assert _coerce_str_list(0.7) == ["0.7"]

    def test_list_of_strings_is_unaffected(self):
        assert _coerce_str_list(["a", "b"]) == ["a", "b"]

    def test_list_of_dicts_is_unaffected(self):
        result = _coerce_str_list([{"name": "Tariffs", "severity": "high"}])
        assert result == ["Tariffs (Sévérité: high)"]

    def test_unexpected_shape_logs_a_warning(self, caplog):
        with caplog.at_level(logging.WARNING, logger="finwiz.schemas.hybrid_analysis.strategic"):
            _coerce_str_list("a lone paragraph of prose")
        assert len(caplog.records) == 1
        assert caplog.records[0].levelno == logging.WARNING
        assert "str" in caplog.records[0].message

    def test_none_and_empty_string_do_not_log(self, caplog):
        with caplog.at_level(logging.WARNING, logger="finwiz.schemas.hybrid_analysis.strategic"):
            _coerce_str_list(None)
            _coerce_str_list("")
        assert caplog.records == []

    def test_list_input_does_not_log(self, caplog):
        with caplog.at_level(logging.WARNING, logger="finwiz.schemas.hybrid_analysis.strategic"):
            _coerce_str_list(["a", "b"])
        assert caplog.records == []


def test_long_paragraph_still_clamped_through_swot_list():
    """A prose paragraph, once coerced to a bullet, is still subject to
    MAX_BULLET_CHARS and the per-field bullet cap — coercion must not
    reopen the unbounded-length hole `_clamp_bullets` exists to close.
    """
    swot = SwotAnalysis.model_validate({"strengths": "x" * 5000})

    assert len(swot.strengths) == 1
    assert len(swot.strengths[0]) <= MAX_BULLET_CHARS


class TestMultilineCoercionRespectsMaxItemsCap:
    """A multiline string coerced by `_coerce_str_list` must still respect
    the per-field max-item cap, not just the per-bullet char cap.

    A 10-line string coerced into 10 bullets, when only MAX_BULLETS_SWOT
    survive, is exactly the unbounded-list shape this branch exists to
    prevent — the char-clamp alone does not stop it.
    """

    def test_swot_list_multiline_string_is_capped_to_max_bullets_swot(self):
        lines = [f"strength {i}" for i in range(10)]
        text = "\n".join(lines)

        swot = SwotAnalysis.model_validate({"strengths": text})

        assert len(swot.strengths) == MAX_BULLETS_SWOT
        assert swot.strengths == lines[:MAX_BULLETS_SWOT]

    def test_cap_tracks_the_constant_not_a_hardcoded_digit(self, mocker):
        """Patch MAX_BULLETS_SWOT to a distinctive value and verify the
        multiline-coercion truncation follows — pins that the cap is read
        from the constant at call time, not a hardcoded 4 baked in anywhere
        along the coercion path.
        """
        import finwiz.schemas.hybrid_analysis.strategic as strategic

        mocker.patch.object(strategic, "MAX_BULLETS_SWOT", 6)

        lines = [f"item {i}" for i in range(10)]
        text = "\n".join(lines)

        swot = strategic.SwotAnalysis.model_validate({"strengths": text})

        assert len(swot.strengths) == 6
        assert swot.strengths == lines[:6]


def test_the_posture_schema_has_no_macro_fields():
    """PESTEL is gone, so nothing can fill a macro summary or verdict."""
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative

    fields = PortfolioPostureNarrative.model_fields

    assert "macro_environment_summary" not in fields
    assert "macro_verdict" not in fields
    assert "competitive_verdict" in fields
    assert "swot_verdict" in fields


def test_a_legacy_posture_carrying_macro_fields_still_validates():
    """Stale artifacts must not fail validation — they are reused on re-analysis failure."""
    from finwiz.schemas.hybrid_analysis.strategic import PortfolioPostureNarrative

    posture = PortfolioPostureNarrative.model_validate(
        {
            "macro_verdict": "Environnement porteur.",
            "macro_environment_summary": "- Politique : durcissement",
            "competitive_verdict": "Moats solides.",
            "swot_verdict": "Équilibré.",
            "strategic_score": 0.71,
            "confidence": 0.83,
        },
    )

    assert not hasattr(posture, "macro_verdict")
    assert posture.competitive_verdict == "Moats solides."
