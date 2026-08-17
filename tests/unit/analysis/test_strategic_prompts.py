"""Tests for strategic research prompts."""


def test_prompts_state_the_output_limits():
    """The caps must be requested, not only enforced.

    A prompt that asks for essays and a schema that clamps them means paying for
    tokens that are then thrown away.
    """
    from finwiz.analysis.strategic_research import _pestel_prompt, _porter_prompt, _swot_prompt

    pestel = _pestel_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "3 puces" in pestel
    assert "200 caractères" in pestel

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
    from finwiz.analysis.strategic_research import _pestel_prompt, _porter_prompt, _portfolio_prompt, _swot_prompt

    # Patch constants to distinctive values and verify they appear in prompts
    mocker.patch.object(strategic_research, "MAX_BULLETS_PESTEL", 7)
    mocker.patch.object(strategic_research, "MAX_BULLET_CHARS", 333)
    mocker.patch.object(strategic_research, "MAX_BULLETS_SWOT", 9)
    mocker.patch.object(strategic_research, "MAX_RATIONALE_CHARS", 444)
    mocker.patch.object(strategic_research, "MAX_VERDICT_CHARS", 555)
    mocker.patch.object(strategic_research, "MAX_PORTFOLIO_PROSE_CHARS", 666)

    pestel = _pestel_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "7 puces" in pestel, "PESTEL should interpolate MAX_BULLETS_PESTEL"
    assert "333 caractères" in pestel, "PESTEL should interpolate MAX_BULLET_CHARS"

    swot = _swot_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "9 puces" in swot, "SWOT should interpolate MAX_BULLETS_SWOT"

    porter = _porter_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "444 caractères" in porter, "Porter should interpolate MAX_RATIONALE_CHARS"

    portfolio = _portfolio_prompt("{}", "16 août 2026")
    assert "555 caractères" in portfolio, "Portfolio prompt should interpolate MAX_VERDICT_CHARS"
    assert "666 caractères" in portfolio, "Portfolio prompt should interpolate MAX_PORTFOLIO_PROSE_CHARS"
