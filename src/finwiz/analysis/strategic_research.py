"""Strategic analysis research orchestrator.

Three independent Perplexity calls (PESTEL/SWOT/Porter's Five Forces) per stock,
plus a portfolio-level synthesis call. All run via direct Perplexity Sonar Pro
with native ``response_format: json_schema`` — no CrewAI agent layer (single
provider call + native structured output = no reasoning needed).

Each framework is asked to self-rate its ``strategic_score`` and ``confidence``;
Python only averages them into a composite — no item-counting heuristics.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from crewai_custom_tools import perplexity_structured

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_PESTEL,
    MAX_BULLETS_SWOT,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    FiveForcesAnalysis,
    PestelAnalysis,
    PortfolioStrategicPosture,
    StrategicAnalysis,
    SwotAnalysis,
)

logger = logging.getLogger(__name__)


_FR_MONTHS = {1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin", 7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"}


def _today_french() -> str:
    """Today's date in long French form, e.g. ``26 avril 2026``."""
    import datetime as _dt

    today = _dt.date.today()
    return f"{today.day} {_FR_MONTHS[today.month]} {today.year}"


SYSTEM_FR = (
    "Tu es un analyste stratégique financier expert. Réponds en français, "
    "avec des faits récents vérifiables et des citations. "
    "Tu DOIS retourner un JSON valide qui respecte exactement le schéma fourni. "
    "🚨 ANTI-HALLUCINATION : tes données d'entraînement sont obsolètes — "
    "fie-toi UNIQUEMENT à ta recherche web actuelle pour la structure corporate "
    "(acquisitions, divestitures, fusions, joint-ventures, partenariats, équipe "
    "dirigeante). Si la recherche web contredit ta mémoire, la recherche web "
    "gagne TOUJOURS. Tous tes constats doivent être cohérents avec la date du jour. "
    "Évalue toi-même les champs strategic_score (0=défavorable, 1=très favorable) "
    "et confidence (0=incertain, 1=très confiant) en te basant sur la qualité "
    "et la fraîcheur des sources que tu as consultées."
)


def _date_preamble(current_date: str) -> str:
    return f"📅 Aujourd'hui : {current_date}. Toutes tes affirmations factuelles doivent être valides à cette date.\n\n"


def _pestel_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + f"Analyse PESTEL pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"Pour chacune des six dimensions (politique, économique, social, technologique, "
        f"environnemental, légal) : au maximum {MAX_BULLETS_PESTEL} puces, chacune de "
        f"{MAX_BULLET_CHARS} caractères maximum. Pas de paragraphes, pas de prose. "
        f"Chaque puce cite une évolution des 12 mois précédant {current_date}. "
        f"Liste ensuite au maximum {MAX_BULLETS_PESTEL} menaces et {MAX_BULLETS_PESTEL} "
        f"opportunités, même format. "
        f"Termine en attribuant strategic_score et confidence."
    )


def _swot_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + f"Analyse SWOT pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"Liste au maximum {MAX_BULLETS_SWOT} puces par catégorie (forces, faiblesses, "
        f"opportunités, menaces) reflétant la situation au {current_date}. Sois spécifique : "
        f"chiffres, parts de marché, avantages produit, dépendances, risques concurrentiels "
        f"— vérifiés via recherche web. Donne ensuite un strategic_assessment (≤ {MAX_PROSE_CHARS} "
        f"caractères). Évalue strategic_score (équilibre S+O vs W+T) et confidence."
    )


def _porter_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + f"Analyse des Cinq Forces de Porter pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"Pour chacune des cinq forces (menace de nouveaux entrants, pouvoir de négociation "
        f"des fournisseurs, pouvoir de négociation des clients, menace des produits de "
        f"substitution, intensité concurrentielle) au {current_date}, attribue une "
        f"intensité (LOW/MEDIUM/HIGH) où LOW = favorable à l'entreprise, et fournis "
        f"une rationale (≤ {MAX_RATIONALE_CHARS} caractères) avec preuves vérifiées "
        f"(concurrents nommés actuels, parts de marché récentes). Termine par "
        f"competitive_position_summary (≤ {MAX_PROSE_CHARS} caractères, force du moat actuel). "
        f"Évalue strategic_score (1 = moat large, 0 = pas de moat) et confidence."
    )


def _portfolio_prompt(per_holding_payload: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + "Voici les analyses stratégiques (PESTEL/SWOT/Five Forces) déjà produites pour "
        "chaque ligne du portefeuille au format JSON :\n\n"
        f"{per_holding_payload}\n\n"
        f"Synthétise une posture stratégique au niveau PORTEFEUILLE à la date du {current_date} :\n"
        "- macro_environment_summary : thèmes PESTEL transversaux (régulatoire, macro, géopolitique).\n"
        "- portfolio_strengths / weaknesses / opportunities / threats : SWOT agrégé.\n"
        "- competitive_landscape_summary : industries avec moats les plus forts/faibles.\n"
        "- dominant_themes : 3 à 5 thèmes stratégiques récurrents.\n"
        "- overall_assessment : narratif final.\n"
        "Évalue strategic_score (favorabilité stratégique globale du portefeuille) et confidence."
    )


async def gather_strategic_analysis(
    *,
    ticker: str,
    sector: str = "",
    industry: str = "",
    description: str = "",
    timeout: float = 60.0,
    current_date: str | None = None,
) -> StrategicAnalysis:
    """Run PESTEL + SWOT + Porter in parallel for one stock.

    Returns a :class:`StrategicAnalysis` even on partial failure — fields are
    independently None so a failure of one framework does not break the others.

    ``current_date`` anchors the prompts so the model anchors its claims to today
    rather than its training cutoff (defaults to today in long French form).
    """
    date_anchor = current_date or _today_french()
    pestel_coro = perplexity_structured(
        prompt=_pestel_prompt(ticker, sector, industry, description, date_anchor),
        schema=PestelAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    swot_coro = perplexity_structured(
        prompt=_swot_prompt(ticker, sector, industry, description, date_anchor),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    porter_coro = perplexity_structured(
        prompt=_porter_prompt(ticker, sector, industry, description, date_anchor),
        schema=FiveForcesAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    pestel, swot, porter = await asyncio.gather(pestel_coro, swot_coro, porter_coro)

    if pestel is None and swot is None and porter is None:
        logger.warning(f"All three strategic analyses failed for {ticker}")

    return StrategicAnalysis(pestel=pestel, swot=swot, five_forces=porter)


def gather_strategic_analysis_sync(
    *,
    ticker: str,
    sector: str = "",
    industry: str = "",
    description: str = "",
    timeout: float = 60.0,
    current_date: str | None = None,
) -> StrategicAnalysis:
    """Synchronous wrapper for the async gather. Safe to call from non-async code paths."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    coro = gather_strategic_analysis(
        ticker=ticker,
        sector=sector,
        industry=industry,
        description=description,
        timeout=timeout,
        current_date=current_date,
    )

    if loop and loop.is_running():
        # We're inside an event loop — run in a worker thread to avoid nested-loop errors
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()

    return asyncio.run(coro)


async def synthesize_portfolio_posture(
    holdings_strategic: dict[str, StrategicAnalysis],
    *,
    timeout: float = 90.0,
    current_date: str | None = None,
) -> PortfolioStrategicPosture | None:
    """Synthesize a portfolio-wide PortfolioStrategicPosture from per-holding analyses.

    Args:
        holdings_strategic: ``{ticker: StrategicAnalysis}`` for each holding analyzed.
        timeout: HTTP timeout for the synthesis call.
        current_date: Long-form French date anchor (defaults to today).
    """
    if not holdings_strategic:
        logger.info("No per-holding strategic analyses provided; skipping portfolio synthesis")
        return None

    payload = _serialize_holdings(holdings_strategic)
    date_anchor = current_date or _today_french()
    return await perplexity_structured(
        prompt=_portfolio_prompt(payload, date_anchor),
        schema=PortfolioStrategicPosture,
        system=SYSTEM_FR,
        search_recency_filter="week",
        timeout=timeout,
    )


def synthesize_portfolio_posture_sync(
    holdings_strategic: dict[str, StrategicAnalysis],
    *,
    timeout: float = 90.0,
    current_date: str | None = None,
) -> PortfolioStrategicPosture | None:
    """Synchronous wrapper for portfolio synthesis."""
    coro = synthesize_portfolio_posture(holdings_strategic, timeout=timeout, current_date=current_date)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


SYNTHESIS_PAYLOAD_BUDGET_CHARS = 240_000
"""Char budget for the portfolio-synthesis payload (~60K tokens).

With the Task 3 caps a 64-holding portfolio lands near 190K, so the degradation
ladder below is a guard-rail rather than the normal path.
"""


def _digest_one(sa: StrategicAnalysis, *, bullets: int, include_prose: bool) -> dict[str, Any]:
    """One holding's contribution at a given detail level."""
    out: dict[str, Any] = {}
    if sa.pestel:
        out["pestel"] = {"score": sa.pestel.strategic_score, "threats": sa.pestel.key_threats[:bullets], "opportunities": sa.pestel.key_opportunities[:bullets]}
    if sa.swot:
        out["swot"] = {"score": sa.swot.strategic_score, "strengths": sa.swot.strengths[:bullets], "threats": sa.swot.threats[:bullets]}
        if include_prose:
            out["swot"]["assessment"] = sa.swot.strategic_assessment
    if sa.five_forces:
        out["moat"] = {"score": sa.five_forces.strategic_score}
        if include_prose:
            out["moat"]["summary"] = sa.five_forces.competitive_position_summary
    return out


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Compact JSON digest of every holding, fitted to the budget.

    Detail degrades before the holding list does. Dropping a holding is not an
    operation this function can perform: the 2026-08-16 posture was synthesized
    from 1 of 64 holdings because the old implementation ended in ``[:30000]``.
    """
    import json

    for bullets, include_prose in ((3, True), (2, True), (1, True), (1, False)):
        compact = {ticker: _digest_one(sa, bullets=bullets, include_prose=include_prose) for ticker, sa in holdings_strategic.items()}
        payload = json.dumps(compact, ensure_ascii=False, default=str)
        if len(payload) <= SYNTHESIS_PAYLOAD_BUDGET_CHARS:
            return payload

    # Floor: scores only. Still every holding.
    scores = {
        ticker: {
            "pestel": sa.pestel.strategic_score if sa.pestel else None,
            "swot": sa.swot.strategic_score if sa.swot else None,
            "moat": sa.five_forces.strategic_score if sa.five_forces else None,
        }
        for ticker, sa in holdings_strategic.items()
    }
    return json.dumps(scores, ensure_ascii=False, default=str)
