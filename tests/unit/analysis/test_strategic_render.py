"""to_prompt_block renders the SWOT/Porter research as one prompt block for the crew."""

from __future__ import annotations

from finwiz.analysis.strategic_render import RATIONALE_PREVIEW_CHARS, STRATEGIC_BLOCK_MAX_CHARS, UNAVAILABLE, to_prompt_block
from finwiz.schemas.hybrid_analysis.strategic import FiveForcesAnalysis, ForceRating, StrategicAnalysis, SwotAnalysis

_DATE = "20 septembre 2026"


def _full() -> StrategicAnalysis:
    swot = SwotAnalysis(
        strengths=["Marque forte", "Trésorerie nette"],
        weaknesses=["Dépendance à un fournisseur"],
        opportunities=["Marché indien"],
        threats=["Réglementation UE"],
        strategic_assessment="Position solide malgré la pression réglementaire.",
        strategic_score=0.7,
        confidence=0.8,
    )
    porter = FiveForcesAnalysis(
        threat_of_new_entrants=ForceRating(intensity="LOW", rationale="Capex élevé"),
        bargaining_power_suppliers=ForceRating(intensity="MEDIUM", rationale="Deux fondeurs"),
        bargaining_power_customers=ForceRating(intensity="HIGH", rationale="Clients concentrés " * 20),
        threat_of_substitutes=ForceRating(intensity="LOW", rationale="Peu d'alternatives"),
        competitive_rivalry=ForceRating(intensity="HIGH", rationale="Guerre des prix"),
        competitive_position_summary="Moat large sur le segment premium.",
        strategic_score=0.65,
        confidence=0.75,
    )
    return StrategicAnalysis(swot=swot, five_forces=porter)


def test_none_renders_the_unavailable_line() -> None:
    assert to_prompt_block(None, _DATE) == UNAVAILABLE


def test_full_block_lists_swot_and_five_forces() -> None:
    block = to_prompt_block(_full(), _DATE)
    assert block.startswith("🧭 RECHERCHE STRATÉGIQUE (web, au 20 septembre 2026")
    assert "score SWOT 0.70" in block and "moat 0.65" in block
    assert "- Forces : Marque forte | Trésorerie nette" in block
    assert "- Menaces : Réglementation UE" in block
    assert "- Synthèse : Position solide malgré la pression réglementaire." in block
    assert "- Nouveaux entrants : LOW — Capex élevé" in block
    assert "- Rivalité : HIGH — Guerre des prix" in block
    assert "- Position : Moat large sur le segment premium." in block


def test_rationale_is_previewed_and_block_is_capped() -> None:
    block = to_prompt_block(_full(), _DATE)
    clients_line = next(line for line in block.splitlines() if line.startswith("- Clients :"))
    assert len(clients_line) <= len("- Clients : HIGH — ") + RATIONALE_PREVIEW_CHARS + 1
    assert len(block) <= STRATEGIC_BLOCK_MAX_CHARS


def test_missing_framework_renders_non_disponible() -> None:
    only_swot = StrategicAnalysis(swot=_full().swot, five_forces=None)
    block = to_prompt_block(only_swot, _DATE)
    assert "Porter : non disponible" in block
    assert "- Forces : Marque forte" in block
    only_porter = StrategicAnalysis(swot=None, five_forces=_full().five_forces)
    assert "SWOT : non disponible" in to_prompt_block(only_porter, _DATE)


def test_empty_swot_lists_render_a_dash() -> None:
    empty = StrategicAnalysis(swot=SwotAnalysis(), five_forces=None)
    assert "- Forces : —" in to_prompt_block(empty, _DATE)
