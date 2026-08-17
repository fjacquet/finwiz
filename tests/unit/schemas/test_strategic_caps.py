"""Tests for the strategic schema caps that bound PESTEL/SWOT/Porter field sizes.

An over-long AI response must be clamped, never rejected — rejecting it would
turn model verbosity into a lost holding, which is the failure this whole
plan exists to remove.
"""

import logging

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_PESTEL,
    MAX_BULLETS_SWOT,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    FiveForcesAnalysis,
    ForceRating,
    PestelAnalysis,
    StrategicAnalysis,
    SwotAnalysis,
    _coerce_str_list,
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


def test_long_paragraph_still_clamped_through_pestel_dimension():
    """A prose paragraph, once coerced to a bullet, is still subject to
    MAX_BULLET_CHARS and the per-field bullet cap — coercion must not
    reopen the unbounded-length hole `_clamp_bullets` exists to close.
    """
    pestel = PestelAnalysis.model_validate({"political": "x" * 5000})

    assert len(pestel.political) == 1
    assert len(pestel.political[0]) <= MAX_BULLET_CHARS


class TestMultilineCoercionRespectsMaxItemsCap:
    """A multiline string coerced by `_coerce_str_list` must still respect
    the per-field max-item cap, not just the per-bullet char cap.

    A 10-line string coerced into 10 bullets, when only MAX_BULLETS_PESTEL
    (or MAX_BULLETS_SWOT) survive, is exactly the unbounded-list shape this
    branch exists to prevent — the char-clamp alone does not stop it.
    """

    def test_pestel_dimension_multiline_string_is_capped_to_max_bullets_pestel(self):
        lines = [f"factor {i}" for i in range(10)]
        text = "\n".join(lines)

        pestel = PestelAnalysis.model_validate({"political": text})

        assert len(pestel.political) == MAX_BULLETS_PESTEL
        assert pestel.political == lines[:MAX_BULLETS_PESTEL]

    def test_swot_list_multiline_string_is_capped_to_max_bullets_swot(self):
        lines = [f"strength {i}" for i in range(10)]
        text = "\n".join(lines)

        swot = SwotAnalysis.model_validate({"strengths": text})

        assert len(swot.strengths) == MAX_BULLETS_SWOT
        assert swot.strengths == lines[:MAX_BULLETS_SWOT]

    def test_cap_tracks_the_constant_not_a_hardcoded_digit(self, mocker):
        """Patch MAX_BULLETS_PESTEL/MAX_BULLETS_SWOT to distinctive values
        and verify the multiline-coercion truncation follows — pins that
        the cap is read from the constant at call time, not a hardcoded
        3/4 baked in anywhere along the coercion path. A regression that
        applied the wrong cap to the wrong framework would also be caught
        here, since PESTEL and SWOT are patched to different values.
        """
        import finwiz.schemas.hybrid_analysis.strategic as strategic

        mocker.patch.object(strategic, "MAX_BULLETS_PESTEL", 5)
        mocker.patch.object(strategic, "MAX_BULLETS_SWOT", 6)

        lines = [f"item {i}" for i in range(10)]
        text = "\n".join(lines)

        pestel = strategic.PestelAnalysis.model_validate({"political": text})
        swot = strategic.SwotAnalysis.model_validate({"strengths": text})

        assert len(pestel.political) == 5
        assert pestel.political == lines[:5]
        assert len(swot.strengths) == 6
        assert swot.strengths == lines[:6]


class TestPestelOldOnDiskShapeRegression:
    """Regression for the real data-loss path: `*_enriched.json` files
    written before PESTEL dimensions became `list[str]` stored each
    dimension as a plain string (see git history for
    src/finwiz/schemas/hybrid_analysis/strategic.py, commit 47c5019d,
    where e.g. ``political: str = Field(default="", ...)``). Re-validating
    that old shape today must not silently drop all six dimensions.
    """

    OLD_SHAPE_STRATEGIC_ANALYSIS = {
        "pestel": {
            "political": "Stable regulatory environment with pro-business trade policy.",
            "economic": "Exposed to currency headwinds from a strong home-market dollar.",
            "social": "Strong brand loyalty among the core demographic.",
            "technological": "R&D spend trails the top two competitors in the category.",
            "environmental": "Under scrutiny for packaging waste in EU markets.",
            "legal": "Ongoing antitrust review of the largest acquisition to date.",
            "key_threats": ["Tariff escalation", "Currency volatility"],
            "key_opportunities": ["Emerging market expansion"],
            "strategic_score": 0.62,
            "confidence": 0.7,
        },
        "swot": {
            "strengths": ["Brand loyalty", "Balance sheet strength"],
            "weaknesses": ["R&D underinvestment"],
            "opportunities": ["Emerging markets"],
            "threats": ["Tariffs"],
            "strategic_assessment": "Solid moat, needs to reinvest.",
            "strategic_score": 0.6,
            "confidence": 0.65,
        },
    }

    def test_old_shape_dimensions_survive_as_bullets_not_empty_lists(self):
        analysis = StrategicAnalysis.model_validate(self.OLD_SHAPE_STRATEGIC_ANALYSIS)

        assert analysis.pestel is not None
        assert analysis.pestel.political == ["Stable regulatory environment with pro-business trade policy."]
        assert analysis.pestel.economic == ["Exposed to currency headwinds from a strong home-market dollar."]
        assert analysis.pestel.social == ["Strong brand loyalty among the core demographic."]
        assert analysis.pestel.technological == ["R&D spend trails the top two competitors in the category."]
        assert analysis.pestel.environmental == ["Under scrutiny for packaging waste in EU markets."]
        assert analysis.pestel.legal == ["Ongoing antitrust review of the largest acquisition to date."]

    def test_old_shape_round_trips_through_model_dump_and_revalidate(self):
        """Simulates the real enrichment.py path: write, read back as a
        dict from disk (model_dump), then re-validate the raw dict again.
        """
        first_pass = StrategicAnalysis.model_validate(self.OLD_SHAPE_STRATEGIC_ANALYSIS)
        dumped = first_pass.model_dump()

        second_pass = StrategicAnalysis.model_validate(dumped)

        assert second_pass.pestel.political == first_pass.pestel.political
        assert all(second_pass.pestel.political)


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
