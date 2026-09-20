"""Render the SWOT/Porter research as one block for the deep-analysis prompt.

One renderer owns the wording, like ``analysis/fact_pack/render.py`` does for
the fact pack, so the crew prompt cannot drift from what the research
produced. The block is capped so a verbose model cannot push the per-holding
data out of the model's attention or past the cache budget.
"""

from __future__ import annotations

from finwiz.schemas.hybrid_analysis.strategic import MAX_BULLETS_SWOT, FiveForcesAnalysis, ForceRating, StrategicAnalysis, SwotAnalysis

STRATEGIC_BLOCK_MAX_CHARS = 2000
RATIONALE_PREVIEW_CHARS = 160
UNAVAILABLE = "Recherche stratégique non disponible."

_FORCE_LABELS: tuple[tuple[str, str], ...] = (
    ("threat_of_new_entrants", "Nouveaux entrants"),
    ("bargaining_power_suppliers", "Fournisseurs"),
    ("bargaining_power_customers", "Clients"),
    ("threat_of_substitutes", "Substituts"),
    ("competitive_rivalry", "Rivalité"),
)


def _bullets(items: list[str]) -> str:
    kept = [item.strip() for item in items[:MAX_BULLETS_SWOT] if item and item.strip()]
    return " | ".join(kept) if kept else "—"


def _preview(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _swot_lines(swot: SwotAnalysis | None) -> list[str]:
    if swot is None:
        return ["SWOT : non disponible"]
    return [
        "SWOT",
        f"- Forces : {_bullets(swot.strengths)}",
        f"- Faiblesses : {_bullets(swot.weaknesses)}",
        f"- Opportunités : {_bullets(swot.opportunities)}",
        f"- Menaces : {_bullets(swot.threats)}",
        f"- Synthèse : {_preview(swot.strategic_assessment, 400) or '—'}",
    ]


def _force_line(label: str, force: ForceRating) -> str:
    return f"- {label} : {force.intensity} — {_preview(force.rationale, RATIONALE_PREVIEW_CHARS) or '—'}"


def _porter_lines(porter: FiveForcesAnalysis | None) -> list[str]:
    if porter is None:
        return ["Porter : non disponible"]
    lines = ["Porter"]
    lines.extend(_force_line(label, getattr(porter, attr)) for attr, label in _FORCE_LABELS)
    lines.append(f"- Position : {_preview(porter.competitive_position_summary, 400) or '—'}")
    return lines


def _score(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def to_prompt_block(strategic: StrategicAnalysis | None, current_date: str) -> str:
    """The strategic research as one block for the qualitative prompt.

    ``None`` (both frameworks failed) renders one explicit line so the model
    knows the section is absent rather than guessing it was never asked.
    """
    if strategic is None:
        return UNAVAILABLE
    swot_score = _score(strategic.swot.strategic_score if strategic.swot else None)
    moat_score = _score(strategic.five_forces.strategic_score if strategic.five_forces else None)
    header = f"🧭 RECHERCHE STRATÉGIQUE (web, au {current_date}, score SWOT {swot_score}, moat {moat_score})"
    lines = [header, *_swot_lines(strategic.swot), *_porter_lines(strategic.five_forces)]
    block = "\n".join(lines)
    if len(block) > STRATEGIC_BLOCK_MAX_CHARS:
        block = block[: STRATEGIC_BLOCK_MAX_CHARS - 1].rstrip() + "…"
    return block
