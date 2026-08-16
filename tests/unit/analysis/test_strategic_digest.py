"""Tests for the portfolio-synthesis payload digest.

The 2026-08-16 posture was synthesized from 1 of 64 holdings because
``_serialize_holdings`` ended in ``[:30000]``: against a 626,286-char payload
that kept 4.8%, only AAPL's entry survived, and it was cut mid-object.

The invariant under test: detail may degrade, the holding list may not.
Dropping a holding is not an operation ``_serialize_holdings`` is allowed to
perform.
"""

import json

from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, PestelAnalysis, StrategicAnalysis, SwotAnalysis


def _rich_holding() -> StrategicAnalysis:
    """A holding with every field ``_digest_one`` reads at rung 1+ populated near its cap.

    ``_digest_one`` at rung 1 (no dimensions) reads only ``key_threats``/
    ``key_opportunities`` from pestel — not ``political``/``economic``/etc,
    which default to ``[]`` here and are read only at rung 0 (see
    ``_rich_holding_with_dimensions`` below) — plus ``strengths``/``threats``/
    ``strategic_assessment`` from swot and ``competitive_position_summary``
    from five_forces. Populating those specific fields near the Task 3 caps
    (3 PESTEL bullets / 4 SWOT bullets / 200 chars per bullet / 400 chars
    prose) is what makes each holding's digest large enough to force the
    degradation ladder.
    """
    pestel = PestelAnalysis(
        key_threats=["t" * 200] * 3,
        key_opportunities=["o" * 200] * 3,
        strategic_score=0.6,
        confidence=0.7,
    )
    swot = SwotAnalysis(
        strengths=["s" * 200] * 4,
        threats=["h" * 200] * 4,
        strategic_assessment="a" * 400,
        strategic_score=0.5,
        confidence=0.6,
    )
    five_forces = FiveForcesAnalysis(
        competitive_position_summary="m" * 400,
        strategic_score=0.4,
        confidence=0.5,
    )
    return StrategicAnalysis(pestel=pestel, swot=swot, five_forces=five_forces)


def _rich_holding_with_dimensions() -> StrategicAnalysis:
    """``_rich_holding`` plus the six PESTEL dimension bullets, populated near their cap.

    These are read only at rung 0 (``include_dimensions=True``) — the extra
    detail the portfolio-synthesis prompt asks for ("thèmes PESTEL
    transversaux") but that was never forwarded before Task 7.
    """
    sa = _rich_holding()
    assert sa.pestel is not None
    dims = {
        "political": ["p" * 200] * 3,
        "economic": ["e" * 200] * 3,
        "social": ["s" * 200] * 3,
        "technological": ["x" * 200] * 3,
        "environmental": ["n" * 200] * 3,
        "legal": ["l" * 200] * 3,
    }
    pestel = sa.pestel.model_copy(update=dims)
    return sa.model_copy(update={"pestel": pestel})


def test_every_holding_survives_the_digest():
    """Detail may shrink. The holding list may not.

    The 2026-08-16 posture was built from 1 of 64 holdings because the
    serializer ended in [:30000]. At the real 240K budget, a 64-holding
    portfolio at near-max detail (measured: rung-1 digest is ~219K chars,
    under budget) must not lose a single ticker.
    """
    from finwiz.analysis.strategic_research import _serialize_holdings

    holdings = {f"TICK{i}": _rich_holding() for i in range(64)}

    payload = _serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 64
    for i in range(64):
        assert f"TICK{i}" in parsed


def test_digest_shrinks_detail_under_budget(mocker):
    """Under a tight budget, the ladder degrades detail rung by rung — it does not drop holdings.

    Measured at rung 1 (bullets=3) a 64-holding payload of this fixture is
    ~219K chars; at rung 2 (bullets=2) ~167K; at rung 3 (bullets=1) ~115K.
    Patching the budget to 140_000 sits below rung 1 and rung 2 but above
    rung 3, so rung 3 must be the one selected. This is asserted directly by
    checking the bullet-list lengths, not merely inferred from payload size.
    """
    from finwiz.analysis import strategic_research

    mocker.patch.object(strategic_research, "SYNTHESIS_PAYLOAD_BUDGET_CHARS", 140_000)
    holdings = {f"T{i}": _rich_holding() for i in range(64)}

    payload = strategic_research._serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 64
    for i in range(64):
        assert f"T{i}" in parsed

    # Rung 3 (bullets=1, include_prose=True): bullet lists trimmed below the
    # rung-1 count of 3, but prose survives — this distinguishes "degraded to
    # rung 3" from both "still at rung 1" and "fell through to the scores-only
    # floor" (which would have no "pestel"/"swot" keys at all).
    sample = parsed["T0"]
    assert len(sample["pestel"]["threats"]) == 1
    assert len(sample["pestel"]["opportunities"]) == 1
    assert len(sample["swot"]["strengths"]) == 1
    assert len(sample["swot"]["threats"]) == 1
    assert "assessment" in sample["swot"]
    assert "summary" in sample["moat"]

    assert len(payload) <= 140_000 * 1.1


def test_digest_falls_back_to_scores_only_floor_without_dropping_holdings(mocker):
    """Even a budget too small for every rung must keep every holding — as scores only.

    A budget of 100 chars is smaller than even the floor payload for a single
    holding, let alone 64, so every rung (including bullets=1/no-prose) will
    overshoot and the function must fall through to the scores-only floor.
    Never dropping a holding is the invariant; this proves it holds at the
    floor as well as at the top of the ladder.
    """
    from finwiz.analysis import strategic_research

    mocker.patch.object(strategic_research, "SYNTHESIS_PAYLOAD_BUDGET_CHARS", 100)
    holdings = {f"T{i}": _rich_holding() for i in range(64)}

    payload = strategic_research._serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 64
    for i in range(64):
        assert f"T{i}" in parsed
        entry = parsed[f"T{i}"]
        # Floor payload: scores only (a bare float per framework), no bullet
        # lists or prose fields — proves this is the floor, not a rung.
        assert set(entry.keys()) <= {"pestel", "swot", "moat"}
        for value in entry.values():
            assert isinstance(value, float) or value is None


def test_digest_one_includes_pestel_dimensions_only_when_asked():
    """The six PESTEL dimensions (political/economic/.../legal) are what the portfolio
    prompt asks the model to synthesize into cross-holding themes — Task 7 forwards
    them, but only at the rung that explicitly requests them."""
    from finwiz.analysis.strategic_research import _digest_one

    sa = _rich_holding_with_dimensions()

    without = _digest_one(sa, bullets=3, include_prose=True, include_dimensions=False)
    assert "dimensions" not in without["pestel"]

    with_dims = _digest_one(sa, bullets=3, include_prose=True, include_dimensions=True)
    assert with_dims["pestel"]["dimensions"]["political"] == sa.pestel.political[:3]
    assert with_dims["pestel"]["dimensions"]["economic"] == sa.pestel.economic[:3]
    assert with_dims["pestel"]["dimensions"]["social"] == sa.pestel.social[:3]
    assert with_dims["pestel"]["dimensions"]["technological"] == sa.pestel.technological[:3]
    assert with_dims["pestel"]["dimensions"]["environmental"] == sa.pestel.environmental[:3]
    assert with_dims["pestel"]["dimensions"]["legal"] == sa.pestel.legal[:3]


def test_serialize_holdings_includes_dimensions_at_top_rung_for_a_small_portfolio(mocker):
    """A small enough portfolio fits the dimensions-included rung 0 within budget."""
    from finwiz.analysis import strategic_research

    holdings = {f"T{i}": _rich_holding_with_dimensions() for i in range(5)}

    payload = strategic_research._serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 5
    assert "dimensions" in parsed["T0"]["pestel"]
    assert parsed["T0"]["pestel"]["dimensions"]["political"] == ["p" * 200] * 3


def test_serialize_holdings_drops_dimensions_first_when_budget_bites(mocker):
    """Dimensions are the first thing shed by the ladder — dropped before bullet counts
    shrink or prose is cut. A budget that fits rung 1 (no dimensions) but not rung 0
    (with dimensions) must select rung 1, not degrade further."""
    from finwiz.analysis import strategic_research

    holdings = {f"T{i}": _rich_holding_with_dimensions() for i in range(64)}
    rung0_size = len(strategic_research._serialize_holdings({t: sa for t, sa in list(holdings.items())[:5]}))  # sanity: rung 0 works at small scale
    assert rung0_size > 0

    # Budget sits between the measured rung-1 size (~219K) and rung-0 size
    # (~461K) for 64 holdings: too small for dimensions, plenty for rung 1.
    mocker.patch.object(strategic_research, "SYNTHESIS_PAYLOAD_BUDGET_CHARS", 300_000)

    payload = strategic_research._serialize_holdings(holdings)
    parsed = json.loads(payload)

    assert len(parsed) == 64
    assert "dimensions" not in parsed["T0"]["pestel"]
    # Still full rung-1 detail (not further degraded to rung 2/3).
    assert len(parsed["T0"]["pestel"]["threats"]) == 3
    assert "assessment" in parsed["T0"]["swot"]
