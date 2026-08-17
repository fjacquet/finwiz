"""Tests for strategic research prompts."""


def test_prompts_state_the_output_limits():
    """The caps must be requested, not only enforced.

    A prompt that asks for essays and a schema that clamps them means paying for
    tokens that are then thrown away.
    """
    from finwiz.analysis.strategic_research import _porter_prompt, _swot_prompt

    swot = _swot_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "4 puces" in swot
    assert "400 caractères" in swot

    porter = _porter_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "250 caractères" in porter
    assert "400 caractères" in porter


def test_portfolio_prompt_states_verdict_and_prose_limits():
    """The portfolio-level prompt must ask for the same caps the schema enforces.

    Task 4 capped the three per-holding prompts; the portfolio prompt was left
    uncapped even after the schema grew clamps for its own prose and verdicts.
    """
    from finwiz.analysis.strategic_research import _portfolio_prompt

    prompt = _portfolio_prompt("{}", "16 août 2026")
    assert "800 caractères" in prompt
    assert "200 caractères" in prompt
    assert "competitive_verdict" in prompt
    assert "swot_verdict" in prompt


def test_prompts_interpolate_constants_not_hardcoded(mocker):
    """Verify that prompt builders use the constants, not hardcoded values.

    This prevents silent desynchronization where a future edit could replace
    an interpolation with a literal digit, causing the prompt to diverge from
    the schema's actual caps.
    """
    import finwiz.analysis.strategic_research as strategic_research
    from finwiz.analysis.strategic_research import _porter_prompt, _portfolio_prompt, _swot_prompt

    # Patch constants to distinctive values and verify they appear in prompts
    mocker.patch.object(strategic_research, "MAX_BULLETS_SWOT", 9)
    mocker.patch.object(strategic_research, "MAX_RATIONALE_CHARS", 444)
    mocker.patch.object(strategic_research, "MAX_VERDICT_CHARS", 555)
    mocker.patch.object(strategic_research, "MAX_PORTFOLIO_PROSE_CHARS", 666)

    swot = _swot_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "9 puces" in swot, "SWOT should interpolate MAX_BULLETS_SWOT"

    porter = _porter_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "444 caractères" in porter, "Porter should interpolate MAX_RATIONALE_CHARS"

    portfolio = _portfolio_prompt("{}", "16 août 2026")
    assert "555 caractères" in portfolio, "Portfolio prompt should interpolate MAX_VERDICT_CHARS"
    assert "666 caractères" in portfolio, "Portfolio prompt should interpolate MAX_PORTFOLIO_PROSE_CHARS"


class TestPortfolioPayloadLegend:
    """The synthesis prompt must explain the payload it sends.

    ``_serialize_holdings`` states the invariant "``n`` always reports the true
    count, so the model cannot mistake the extremes for the whole portfolio" --
    but ``n`` reaches the model as a bare two-character key. Enforcing that
    invariant in Python while never expressing it to its only consumer is how a
    posture ends up describing 10 of 64 positions, which is the defect this
    whole branch exists to fix, one layer up.
    """

    def test_the_prompt_glosses_every_abbreviated_payload_key(self) -> None:
        from finwiz.analysis.strategic_research import _portfolio_prompt

        prompt = _portfolio_prompt('{"n": 64}', "2026-08-17")

        for key in ("n", "swot_mean", "moat_mean", "distribution", "weakest", "strongest"):
            assert key in prompt, f"payload key {key!r} is sent but never explained"
        # The single-letter keys inside weakest/strongest entries.
        assert "t = ticker" in prompt
        assert "c = score composite" in prompt
        assert "T = principale menace" in prompt
        assert "S = principale force" in prompt

    def test_the_prompt_says_n_is_the_whole_portfolio_not_what_was_shown(self) -> None:
        from finwiz.analysis.strategic_research import _portfolio_prompt

        prompt = _portfolio_prompt('{"n": 64}', "2026-08-17")

        assert "TOTAL" in prompt
        assert "UNIQUEMENT les positions extrêmes" in prompt
