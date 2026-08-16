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

    porter = _porter_prompt("AAPL", "Tech", "Consumer Electronics", "", "16 août 2026")
    assert "250 caractères" in porter
