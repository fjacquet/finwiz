"""Strategic analysis research orchestrator.

Two independent Perplexity calls (SWOT/Porter's Five Forces) per
holding, plus a portfolio-level synthesis call. Every asset class — stock,
ETF, crypto — gets both frameworks; each prompt builder takes an
``asset_class`` and asks a question that actually fits the asset (moats and
competitors for stocks, fees and concentration for ETFs, protocol economics
and regulatory posture for crypto) while requesting the exact same output
caps in every branch. All run via direct Perplexity Sonar Pro with native
``response_format: json_schema`` — no CrewAI agent layer (single provider
call + native structured output = no reasoning needed).

Each framework is asked to self-rate its ``strategic_score`` and ``confidence``;
Python only averages them into a composite — no item-counting heuristics.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from finwiz.infrastructure.resilience.perplexity_retry import perplexity_with_retry
from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLETS_SWOT,
    MAX_PORTFOLIO_PROSE_CHARS,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    MAX_VERDICT_CHARS,
    FiveForcesAnalysis,
    PortfolioPostureNarrative,
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


# The wrapper's ``timeout`` is per *attempt*, not a total budget -- so attempts
# multiply the worst case. Strategic research is the last thing to run inside a
# holding's 900 s ``asyncio.wait_for`` (stages/__init__.py), and the tightest
# holdings observed on 2026-08-16 reached it with ~240 s left. At the wrapper's
# default of 4 attempts the worst case per framework is 4x60+backoff ~= 247 s,
# which exceeds that headroom and would lose the whole holding -- strictly worse
# than losing one framework. Three attempts bound it to ~184 s, inside every
# headroom actually observed.
#
# The portfolio synthesis call deliberately keeps the wrapper default: it runs
# once, after every holding, outside any per-holding budget.
_FRAMEWORK_MAX_ATTEMPTS = 3

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


def _swot_focus(asset_class: str) -> str:
    """What to be specific about, tailored to what the asset class actually is."""
    if asset_class == "etf":
        return "Sois spécifique : concentration sectorielle/géographique, frais (TER), qualité de réplication, liquidité, risques de contrepartie — vérifiés via recherche web."
    if asset_class == "crypto":
        return (
            "Sois spécifique : économie du protocole, activité des développeurs, effets de "
            "réseau, posture réglementaire par juridiction, risques de conservation — "
            "vérifiés via recherche web."
        )
    return "Sois spécifique : chiffres, parts de marché, avantages produit, dépendances, risques concurrentiels — vérifiés via recherche web."


def _swot_caps_fragment(current_date: str) -> str:
    """Output-budget language shared by every asset-class branch."""
    return (
        f"Liste au maximum {MAX_BULLETS_SWOT} puces par catégorie (forces, faiblesses, "
        f"opportunités, menaces) reflétant la situation au {current_date}. "
        f"Donne ensuite un strategic_assessment (≤ {MAX_PROSE_CHARS} caractères). "
        f"Évalue strategic_score (équilibre S+O vs W+T) et confidence."
    )


def _swot_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str, *, asset_class: str = "stock") -> str:
    return (
        _date_preamble(current_date) + f"Analyse SWOT pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"{_swot_focus(asset_class)}\n\n"
        f"{_swot_caps_fragment(current_date)}"
    )


def _porter_focus(asset_class: str) -> str:
    """Which forces to rate, remapped to what actually competes in this asset class."""
    if asset_class == "etf":
        return (
            "Pour un ETF, adapte les cinq forces à la concurrence entre émetteurs : menace "
            "de nouveaux émetteurs/produits concurrents, pouvoir de négociation du "
            "fournisseur d'indice, pouvoir de négociation des investisseurs (sensibilité aux "
            "frais), menace des ETF ou fonds indiciels de substitution, intensité de la "
            "guerre des frais entre émetteurs"
        )
    if asset_class == "crypto":
        return (
            "Pour un actif crypto, adapte les cinq forces à l'écosystème du protocole : "
            "menace de nouveaux protocoles ou layer-2 entrants, pouvoir de négociation des "
            "validateurs ou mineurs, pouvoir de négociation des plateformes d'échange et "
            "fournisseurs de liquidité, menace des chaînes ou tokens de substitution, "
            "intensité de la concurrence réglementaire et technique entre protocoles"
        )
    return (
        "Pour chacune des cinq forces (menace de nouveaux entrants, pouvoir de négociation "
        "des fournisseurs, pouvoir de négociation des clients, menace des produits de "
        "substitution, intensité concurrentielle)"
    )


def _porter_caps_fragment(current_date: str) -> str:
    """Output-budget language shared by every asset-class branch."""
    return (
        f"au {current_date}, attribue une intensité (LOW/MEDIUM/HIGH) où LOW = favorable, "
        f"et fournis une rationale (≤ {MAX_RATIONALE_CHARS} caractères) avec preuves "
        f"vérifiées (acteurs nommés actuels, parts de marché récentes). Termine par "
        f"competitive_position_summary (≤ {MAX_PROSE_CHARS} caractères, force du moat "
        f"actuel). Évalue strategic_score (1 = moat large, 0 = pas de moat) et confidence."
    )


def _porter_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str, *, asset_class: str = "stock") -> str:
    return (
        _date_preamble(current_date) + f"Analyse des Cinq Forces de Porter pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"{_porter_focus(asset_class)} {_porter_caps_fragment(current_date)}"
    )


# The payload's keys are abbreviated to keep it fixed-size, which makes them
# opaque to the only thing that reads them. ``_serialize_holdings`` states the
# invariant "``n`` always reports the true count, so the model cannot mistake
# the extremes for the whole portfolio" -- but ``n`` arrives as a bare
# two-character key. Enforcing that invariant in Python without expressing it to
# the model is how a posture ends up describing 10 of 64 positions.
_PAYLOAD_LEGEND = (
    "Lecture du JSON :\n"
    "- n : nombre TOTAL de lignes analysées dans le portefeuille. La posture doit porter sur ces n lignes.\n"
    "- swot_mean / moat_mean : scores moyens sur ces n lignes (SWOT, Porter).\n"
    "- distribution : répartition des n lignes par tranche de score composite — c'est par là que les lignes "
    "non nommées ci-dessous sont représentées.\n"
    "- weakest / strongest : UNIQUEMENT les positions extrêmes, pas le portefeuille. "
    "t = ticker, c = score composite, T = principale menace, S = principale force.\n"
)


def _portfolio_prompt(per_holding_payload: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + "Voici la synthèse des analyses stratégiques (SWOT / Five Forces) "
        "du portefeuille au format JSON — agrégats et positions extrêmes :\n\n"
        f"{per_holding_payload}\n\n"
        f"{_PAYLOAD_LEGEND}\n"
        f"Synthétise une posture stratégique au niveau PORTEFEUILLE à la date du {current_date} :\n"
        "- portfolio_strengths / weaknesses / opportunities / threats : SWOT agrégé.\n"
        f"- competitive_landscape_summary : industries avec moats les plus forts/faibles, "
        f"{MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        "- dominant_themes : 3 à 5 thèmes stratégiques récurrents.\n"
        f"- overall_assessment : narratif final, {MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        f"- competitive_verdict / swot_verdict : UNE phrase chacun, "
        f"{MAX_VERDICT_CHARS} caractères maximum, compréhensible par un lecteur non financier.\n"
        "Évalue strategic_score (favorabilité stratégique globale du portefeuille) et confidence."
    )


async def gather_strategic_analysis(
    *,
    ticker: str,
    sector: str = "",
    industry: str = "",
    description: str = "",
    asset_class: str = "stock",
    timeout: float = 60.0,
    current_date: str | None = None,
) -> StrategicAnalysis | None:
    """Run SWOT + Porter in parallel for one holding.

    Returns a :class:`StrategicAnalysis` on *partial* failure — fields are
    independently None so a failure of one framework does not break the
    other, and one surviving framework is real evidence worth keeping.

    Returns ``None`` when **both** fail: no evidence at all must not be
    dressed up as an analysis object. Callers already handle ``None``
    (``analysis/stages/__init__.py`` guards ``if strategic is not None``).

    ``asset_class`` ("stock"/"etf"/"crypto") is forwarded to each prompt
    builder so the questions asked actually fit the asset — every asset
    class gets both frameworks, just framed differently.

    ``current_date`` anchors the prompts so the model anchors its claims to today
    rather than its training cutoff (defaults to today in long French form).
    """
    date_anchor = current_date or _today_french()
    swot_coro = perplexity_with_retry(
        prompt=_swot_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        search_recency_filter="month",
        timeout=timeout,
        max_attempts=_FRAMEWORK_MAX_ATTEMPTS,
    )
    porter_coro = perplexity_with_retry(
        prompt=_porter_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=FiveForcesAnalysis,
        system=SYSTEM_FR,
        search_recency_filter="month",
        timeout=timeout,
        max_attempts=_FRAMEWORK_MAX_ATTEMPTS,
    )
    swot, porter = await asyncio.gather(swot_coro, porter_coro)

    if swot is None and porter is None:
        # The absence of data must be representable. Returning
        # StrategicAnalysis(swot=None, five_forces=None) here produced a
        # truthy, schema-valid blob that survived every downstream check:
        # `if ticker and sa`, `model_validate`, and the portfolio coverage
        # set. A total provider outage therefore rendered
        # "64 / 64 holdings · 100.0 %" in green above a score the model was
        # forced to invent from `{"T0": {}, "T1": {}, ...}` -- the 2026-08-16
        # defect with the numbers inverted, and harder to spot.
        logger.warning(f"Both strategic analyses failed for {ticker}; returning None (no evidence, not an empty analysis)")
        return None

    return StrategicAnalysis(swot=swot, five_forces=porter)


def gather_strategic_analysis_sync(
    *,
    ticker: str,
    sector: str = "",
    industry: str = "",
    description: str = "",
    asset_class: str = "stock",
    timeout: float = 60.0,
    current_date: str | None = None,
) -> StrategicAnalysis | None:
    """Synchronous wrapper for the async gather. Safe to call from non-async code paths.

    Propagates the async gather's ``None`` unchanged — see
    :func:`gather_strategic_analysis` for why both-failed is ``None``.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    coro = gather_strategic_analysis(
        ticker=ticker,
        sector=sector,
        industry=industry,
        description=description,
        asset_class=asset_class,
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
    holdings_covered: int,
    holdings_total: int,
    value_covered_pct: float,
    uncovered_tickers: list[str] | None = None,
    timeout: float = 90.0,
    current_date: str | None = None,
) -> PortfolioStrategicPosture | None:
    """Synthesize a portfolio-wide PortfolioStrategicPosture from per-holding analyses.

    Coverage is a Python fact, never an LLM one — the model is asked to fill
    :class:`PortfolioPostureNarrative` (no coverage fields), and Python merges
    the caller-supplied coverage numbers into that response *before*
    constructing the final :class:`PortfolioStrategicPosture`. Validating the
    full schema straight out of the LLM response would fail every time
    (the model can't supply holdings_covered/holdings_total/value_covered_pct),
    turning every synthesis into a lost posture.

    Args:
        holdings_strategic: ``{ticker: StrategicAnalysis}`` for each holding analyzed.
        holdings_covered: Count of holdings with a real strategic analysis.
        holdings_total: Count of holdings in the portfolio.
        value_covered_pct: Share of portfolio value covered, 0-100.
        uncovered_tickers: Tickers with no strategic analysis (default: none).
        timeout: HTTP timeout for the synthesis call.
        current_date: Long-form French date anchor (defaults to today).
    """
    if not holdings_strategic:
        logger.info("No per-holding strategic analyses provided; skipping portfolio synthesis")
        return None

    payload = _serialize_holdings(holdings_strategic)
    date_anchor = current_date or _today_french()
    narrative = await perplexity_with_retry(
        prompt=_portfolio_prompt(payload, date_anchor),
        schema=PortfolioPostureNarrative,
        system=SYSTEM_FR,
        search_recency_filter="week",
        timeout=timeout,
    )
    if narrative is None:
        return None

    merged = narrative.model_dump()
    merged.update(
        holdings_covered=holdings_covered,
        holdings_total=holdings_total,
        value_covered_pct=value_covered_pct,
        uncovered_tickers=uncovered_tickers or [],
    )
    return PortfolioStrategicPosture.model_validate(merged)


def synthesize_portfolio_posture_sync(
    holdings_strategic: dict[str, StrategicAnalysis],
    *,
    holdings_covered: int,
    holdings_total: int,
    value_covered_pct: float,
    uncovered_tickers: list[str] | None = None,
    timeout: float = 90.0,
    current_date: str | None = None,
) -> PortfolioStrategicPosture | None:
    """Synchronous wrapper for portfolio synthesis."""
    coro = synthesize_portfolio_posture(
        holdings_strategic,
        holdings_covered=holdings_covered,
        holdings_total=holdings_total,
        value_covered_pct=value_covered_pct,
        uncovered_tickers=uncovered_tickers,
        timeout=timeout,
        current_date=current_date,
    )
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
"""Guard for the portfolio-synthesis payload (~60K tokens).

Task 3 replaced the per-holding digest (39,001 chars for 64 holdings, and
growing linearly with portfolio size) with fixed-size aggregates plus the 5
weakest and 5 strongest holdings — a shape that costs ~3,000 chars at any
portfolio size. This budget is no longer a trimming target the payload is
degraded down to; it should never trigger. If it does, that signals unusually
long bullets in the extreme entries, not a large portfolio.
"""


_EXTREMES = 5
"""Holdings named at each end. Fixed, so the payload does not scale with the portfolio."""

_SCORE_BUCKETS = ((0.5, "<0.5"), (0.65, "0.5-0.65"), (0.8, "0.65-0.8"))


def _bucket(score: float) -> str:
    for upper, label in _SCORE_BUCKETS:
        if score < upper:
            return label
    return ">=0.8"


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Portfolio aggregates plus the extreme holdings, as a JSON string.

    A portfolio posture is a judgement about distribution and outliers, not a
    reading of every line. Sending all 64 digests cost ~39,000 chars to produce
    ~2,000 chars of verdict and grew linearly with the portfolio; this shape is
    ~3,000 chars at any size.

    The mid-pack holdings are represented by ``distribution``, never dropped
    silently: ``n`` always reports the true count, so the model cannot mistake
    the extremes for the whole portfolio.
    """
    rows: list[tuple[float, str, StrategicAnalysis]] = []
    for ticker, sa in sorted(holdings_strategic.items()):
        composite = sa.composite_strategic_score
        if composite is None:
            continue
        rows.append((composite, ticker, sa))
    rows.sort(key=lambda r: (r[0], r[1]))

    swot_scores = [sa.swot.strategic_score for _, _, sa in rows if sa.swot is not None]
    moat_scores = [sa.five_forces.strategic_score for _, _, sa in rows if sa.five_forces is not None]

    distribution: dict[str, int] = {}
    for composite, _, _ in rows:
        label = _bucket(composite)
        distribution[label] = distribution.get(label, 0) + 1

    def _weak(entry: tuple[float, str, StrategicAnalysis]) -> dict[str, Any]:
        composite, ticker, sa = entry
        threats = sa.swot.threats if sa.swot else []
        return {"t": ticker, "c": round(composite, 2), "T": threats[0] if threats else None}

    def _strong(entry: tuple[float, str, StrategicAnalysis]) -> dict[str, Any]:
        composite, ticker, sa = entry
        strengths = sa.swot.strengths if sa.swot else []
        return {"t": ticker, "c": round(composite, 2), "S": strengths[0] if strengths else None}

    # weakest/strongest must be disjoint at every n -- naming the same ticker as
    # both the portfolio's weakest and strongest position is a contradiction the
    # model would have to paper over. Splitting at the midpoint keeps both ends
    # represented without overlap: at n >= 2 * _EXTREMES this reduces to exactly
    # rows[:_EXTREMES] / rows[-_EXTREMES:] (unchanged from before this fix, since
    # rows[len(rows) - _EXTREMES:] == rows[-_EXTREMES:] once half == _EXTREMES);
    # below that it shrinks symmetrically, leaving any single middle holding
    # unnamed (still counted in `n` and `distribution`) rather than duplicated.
    half = min(_EXTREMES, len(rows) // 2)
    if not rows:
        weak_rows: list[tuple[float, str, StrategicAnalysis]] = []
        strong_rows: list[tuple[float, str, StrategicAnalysis]] = []
    elif half == 0:
        # Exactly one holding (half == 0 only for len(rows) in {0, 1}, and the
        # empty case is handled above). It cannot be named as both the
        # portfolio's weakest and strongest position, so pick one deliberately:
        # `weakest`, because a one-holding portfolio is maximally concentrated,
        # and its downside is the more actionable framing for the posture
        # narrative than its upside.
        weak_rows = rows[:1]
        strong_rows = []
    else:
        weak_rows = rows[:half]
        strong_rows = rows[len(rows) - half :]

    payload = {
        "n": len(rows),
        "swot_mean": round(sum(swot_scores) / len(swot_scores), 2) if swot_scores else None,
        "moat_mean": round(sum(moat_scores) / len(moat_scores), 2) if moat_scores else None,
        "distribution": distribution,
        "weakest": [_weak(r) for r in weak_rows],
        "strongest": [_strong(r) for r in strong_rows],
    }

    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    if len(serialized) > SYNTHESIS_PAYLOAD_BUDGET_CHARS:
        logger.warning(
            f"Synthesis payload {len(serialized)} chars exceeds the {SYNTHESIS_PAYLOAD_BUDGET_CHARS} budget "
            f"for {len(rows)} holdings — the payload is meant to be size-independent, so this indicates "
            f"unusually long bullets rather than a large portfolio."
        )
    return serialized
