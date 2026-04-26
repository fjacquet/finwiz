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

from finwiz.schemas.hybrid_analysis.strategic import (
    FiveForcesAnalysis,
    PestelAnalysis,
    PortfolioStrategicPosture,
    StrategicAnalysis,
    SwotAnalysis,
)
from finwiz.tools.perplexity_structured import perplexity_structured

logger = logging.getLogger(__name__)


SYSTEM_FR = (
    "Tu es un analyste stratégique financier expert. Réponds en français, "
    "avec des faits récents vérifiables et des citations. "
    "Tu DOIS retourner un JSON valide qui respecte exactement le schéma fourni. "
    "Évalue toi-même les champs strategic_score (0=défavorable, 1=très favorable) "
    "et confidence (0=incertain, 1=très confiant) en te basant sur la qualité "
    "et la fraîcheur des sources que tu as consultées."
)


def _pestel_prompt(ticker: str, sector: str, industry: str, description: str) -> str:
    return (
        f"Analyse PESTEL pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        "Couvre les six dimensions (politique, économique, social, technologique, "
        "environnemental, légal) en 2-4 phrases chacune, en citant des évolutions "
        "récentes (12 derniers mois). Liste ensuite les menaces et opportunités les "
        "plus matérielles. Termine en attribuant strategic_score (favorabilité globale "
        "de l'environnement PESTEL pour cette entreprise) et confidence."
    )


def _swot_prompt(ticker: str, sector: str, industry: str, description: str) -> str:
    return (
        f"Analyse SWOT pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        "Liste 3-6 éléments par catégorie (forces, faiblesses, opportunités, menaces). "
        "Sois spécifique : chiffres, parts de marché, avantages produit, dépendances, "
        "risques concurrentiels. Donne ensuite un strategic_assessment (paragraphe de "
        "synthèse). Évalue strategic_score (équilibre S+O vs W+T) et confidence."
    )


def _porter_prompt(ticker: str, sector: str, industry: str, description: str) -> str:
    return (
        f"Analyse des Cinq Forces de Porter pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        "Pour chacune des cinq forces (menace de nouveaux entrants, pouvoir de négociation "
        "des fournisseurs, pouvoir de négociation des clients, menace des produits de "
        "substitution, intensité concurrentielle), attribue une intensité (LOW/MEDIUM/HIGH) "
        "où LOW = favorable à l'entreprise, et fournis une rationale courte avec preuves. "
        "Termine par competitive_position_summary (force du moat). Évalue strategic_score "
        "(1 = moat large, 0 = pas de moat) et confidence."
    )


def _portfolio_prompt(per_holding_payload: str) -> str:
    return (
        "Voici les analyses stratégiques (PESTEL/SWOT/Five Forces) déjà produites pour "
        "chaque ligne du portefeuille au format JSON :\n\n"
        f"{per_holding_payload}\n\n"
        "Synthétise une posture stratégique au niveau PORTEFEUILLE :\n"
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
) -> StrategicAnalysis:
    """Run PESTEL + SWOT + Porter in parallel for one stock.

    Returns a :class:`StrategicAnalysis` even on partial failure — fields are
    independently None so a failure of one framework does not break the others.
    """
    pestel_coro = perplexity_structured(
        prompt=_pestel_prompt(ticker, sector, industry, description),
        schema=PestelAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    swot_coro = perplexity_structured(
        prompt=_swot_prompt(ticker, sector, industry, description),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    porter_coro = perplexity_structured(
        prompt=_porter_prompt(ticker, sector, industry, description),
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
) -> PortfolioStrategicPosture | None:
    """Synthesize a portfolio-wide PortfolioStrategicPosture from per-holding analyses.

    Args:
        holdings_strategic: ``{ticker: StrategicAnalysis}`` for each holding analyzed.
        timeout: HTTP timeout for the synthesis call.
    """
    if not holdings_strategic:
        logger.info("No per-holding strategic analyses provided; skipping portfolio synthesis")
        return None

    payload = _serialize_holdings(holdings_strategic)
    return await perplexity_structured(
        prompt=_portfolio_prompt(payload),
        schema=PortfolioStrategicPosture,
        system=SYSTEM_FR,
        search_recency="week",
        timeout=timeout,
    )


def synthesize_portfolio_posture_sync(
    holdings_strategic: dict[str, StrategicAnalysis],
    *,
    timeout: float = 90.0,
) -> PortfolioStrategicPosture | None:
    """Synchronous wrapper for portfolio synthesis."""
    coro = synthesize_portfolio_posture(holdings_strategic, timeout=timeout)
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Compact JSON of per-holding analyses for the portfolio prompt."""
    import json

    compact: dict[str, Any] = {}
    for ticker, sa in holdings_strategic.items():
        compact[ticker] = sa.model_dump(mode="json", exclude_none=True)
    return json.dumps(compact, ensure_ascii=False, indent=2)[:30000]
