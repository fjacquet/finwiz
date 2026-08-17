"""The deep-analysis crew must not be able to author `strategic_analysis`.

`strategic_analysis` (PESTEL/SWOT/Porter) is a Python-gathered field, filled
only by `gather_strategic_analysis` via `stages/__init__.py:107-108`. No agent
or task config under `src/finwiz/crews/` prompts for it. If the LLM-facing
bridging schema (`_QualitativeInsightsRaw`) still declares the field, the
model fills it unprompted whenever it recognizes the company — and a
hallucinated PESTEL/SWOT is indistinguishable downstream from a researched
one, so it silently counts as full coverage.

See the 2026-08-16 end-to-end run: DIS and ORCL lost all three Perplexity
framework calls to HTTP 429 (`gather_strategic_analysis` correctly returned
`None`), yet both still carried a full `strategic_analysis` in their
`*_enriched.json` — with zero `[n]` citation markers, unlike the
Perplexity-grounded holdings.
"""

from __future__ import annotations

from finwiz.analysis.stages.qualify import _QualitativeInsightsRaw


def test_the_crew_cannot_author_strategic_analysis() -> None:
    """Only gather_strategic_analysis may fill this field.

    The model fills any field present in the schema it is handed, whether or
    not a task asks for it. A PESTEL the model invented is indistinguishable
    from a researched one downstream, and counts as full coverage.
    """
    assert "strategic_analysis" not in _QualitativeInsightsRaw.model_fields


def test_a_strategic_analysis_the_model_emits_is_dropped() -> None:
    """extra="ignore" must swallow it rather than promoting it."""
    raw = _QualitativeInsightsRaw.model_validate(
        {
            "ai_confidence": 0.8,
            "strategic_analysis": {"pestel": {"strategic_score": 0.9, "confidence": 0.9}},
        },
    )

    assert not hasattr(raw, "strategic_analysis")
    assert "strategic_analysis" not in raw.model_dump()
