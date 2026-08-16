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
    """A holding with every field ``_digest_one`` reads populated near its cap.

    ``_digest_one`` reads only ``key_threats``/``key_opportunities`` from
    pestel (not ``political``/``economic``, which default to ``[]`` and are
    never read), plus ``strengths``/``threats``/``strategic_assessment`` from
    swot and ``competitive_position_summary`` from five_forces. Populating
    those specific fields near the Task 3 caps (3 PESTEL bullets / 4 SWOT
    bullets / 200 chars per bullet / 400 chars prose) is what makes each
    holding's digest large enough to force the degradation ladder.
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
