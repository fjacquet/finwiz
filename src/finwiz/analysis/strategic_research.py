"""Strategic analysis research orchestrator.

Three independent Perplexity calls (PESTEL/SWOT/Porter's Five Forces) per
holding, plus a portfolio-level synthesis call. Every asset class — stock,
ETF, crypto — gets all three frameworks; each prompt builder takes an
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
import logging
from typing import Any

from crewai_custom_tools import perplexity_structured

from finwiz.schemas.hybrid_analysis.strategic import (
    MAX_BULLET_CHARS,
    MAX_BULLETS_PESTEL,
    MAX_BULLETS_SWOT,
    MAX_PORTFOLIO_PROSE_CHARS,
    MAX_PROSE_CHARS,
    MAX_RATIONALE_CHARS,
    MAX_VERDICT_CHARS,
    FiveForcesAnalysis,
    PestelAnalysis,
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


def _pestel_focus(asset_class: str) -> str:
    """The dimensions to cover, tailored to what the asset class actually is."""
    if asset_class == "etf":
        return (
            "Pour un ETF, traite les six dimensions à travers : régime réglementaire et "
            "fiscal, concentration sectorielle et géographique, frais et qualité de "
            "réplication, liquidité."
        )
    if asset_class == "crypto":
        return (
            "Pour un actif crypto, traite les six dimensions à travers : posture "
            "réglementaire par juridiction, économie du protocole et émission, effets de "
            "réseau et activité des développeurs, risque de conservation et de contrepartie."
        )
    return "Couvre les six dimensions PESTEL classiques (politique, économique, social, technologique, environnemental, légal) pour l'entreprise."


def _pestel_caps_fragment(current_date: str) -> str:
    """Output-budget language shared by every asset-class branch.

    Interpolated from ``MAX_BULLETS_PESTEL``/``MAX_BULLET_CHARS`` — never
    hardcoded — so the model's actual output budget always matches what
    ``PestelAnalysis``'s validators will accept. Dropping this in any
    per-asset-class branch is what let the model overrun its output limit
    and return unparseable JSON, which opened the circuit breaker and killed
    31 holdings.
    """
    return (
        f"Pour chacune des six dimensions : au maximum {MAX_BULLETS_PESTEL} puces, chacune "
        f"de {MAX_BULLET_CHARS} caractères maximum. Pas de paragraphes, pas de prose. "
        f"Chaque puce cite une évolution des 12 mois précédant {current_date}. "
        f"Liste ensuite au maximum {MAX_BULLETS_PESTEL} menaces et {MAX_BULLETS_PESTEL} "
        f"opportunités, même format. "
        f"Termine en attribuant strategic_score et confidence."
    )


def _pestel_prompt(ticker: str, sector: str, industry: str, description: str, current_date: str, *, asset_class: str = "stock") -> str:
    return (
        _date_preamble(current_date) + f"Analyse PESTEL pour {ticker} ({sector} / {industry}).\n"
        f"Description: {description or 'Non fournie'}\n\n"
        f"{_pestel_focus(asset_class)}\n\n"
        f"{_pestel_caps_fragment(current_date)}"
    )


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


def _portfolio_prompt(per_holding_payload: str, current_date: str) -> str:
    return (
        _date_preamble(current_date) + "Voici les analyses stratégiques (PESTEL/SWOT/Five Forces) déjà produites pour "
        "chaque ligne du portefeuille au format JSON :\n\n"
        f"{per_holding_payload}\n\n"
        f"Synthétise une posture stratégique au niveau PORTEFEUILLE à la date du {current_date} :\n"
        f"- macro_environment_summary : thèmes PESTEL transversaux (régulatoire, macro, géopolitique), "
        f"{MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        "- portfolio_strengths / weaknesses / opportunities / threats : SWOT agrégé.\n"
        f"- competitive_landscape_summary : industries avec moats les plus forts/faibles, "
        f"{MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        "- dominant_themes : 3 à 5 thèmes stratégiques récurrents.\n"
        f"- overall_assessment : narratif final, {MAX_PORTFOLIO_PROSE_CHARS} caractères maximum.\n"
        f"- macro_verdict / competitive_verdict / swot_verdict : UNE phrase chacun, "
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
) -> StrategicAnalysis:
    """Run PESTEL + SWOT + Porter in parallel for one holding.

    Returns a :class:`StrategicAnalysis` even on partial failure — fields are
    independently None so a failure of one framework does not break the others.

    ``asset_class`` ("stock"/"etf"/"crypto") is forwarded to each prompt
    builder so the questions asked actually fit the asset — every asset
    class gets all three frameworks, just framed differently.

    ``current_date`` anchors the prompts so the model anchors its claims to today
    rather than its training cutoff (defaults to today in long French form).
    """
    date_anchor = current_date or _today_french()
    pestel_coro = perplexity_structured(
        prompt=_pestel_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=PestelAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    swot_coro = perplexity_structured(
        prompt=_swot_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
        schema=SwotAnalysis,
        system=SYSTEM_FR,
        timeout=timeout,
    )
    porter_coro = perplexity_structured(
        prompt=_porter_prompt(ticker, sector, industry, description, date_anchor, asset_class=asset_class),
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
    asset_class: str = "stock",
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
    narrative = await perplexity_structured(
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
"""Char budget for the portfolio-synthesis payload (~60K tokens).

These figures are measured against a specific 64-holding fixture at the
Task 3 field caps (see ``tests/unit/analysis/test_strategic_digest.py``) —
approximate and fixture-dependent, not a promise about every real portfolio.
A different mix of populated fields shifts every number below.

Task 7 added the six raw PESTEL dimension bullets (political/economic/
social/technological/environmental/legal) to the digest — the material the
portfolio prompt asks the model to synthesize into cross-holding themes,
previously collected per-holding via a paid Perplexity call and never sent
to the one prompt that needed them. A first attempt gated the dimensions
behind a single all-or-nothing rung tried only at full bullet count (3):
that rung measured ~461K chars, ~92% over budget, so for the real portfolio
it was *always* skipped and the dimensions never actually reached the
prompt — the ladder fell straight through to the no-dimensions rung every
time, silently inert.

The ladder was restructured so dimensions shrink alongside bullet count
instead of toggling off entirely, and — since ``key_threats``/
``key_opportunities`` are the model's own summary of the six dimensions
(derived evidence), while the dimensions themselves are the primary
evidence a Perplexity call was paid to produce — the derived summary is
shed *before* the dimensions, not the other way round. Measured for 64
holdings at this fixture:

| Rung | bullets | prose | pestel summary | pestel dims | chars | fits 240K? |
|---|---|---|---|---|---|---|
| 1 | 3 | yes | yes | yes | 461,110 | no |
| 2 | 2 | yes | yes | yes | 330,550 | no |
| 3 | 1 | yes | yes | yes | 199,990 | **yes** |
| 4 | 1 | yes | no  | yes | 171,830 | yes |
| 5 | 1 | no  | no  | yes | 118,518 | yes |

Rung 3 is the one actually selected for the real 64-holding portfolio: the
dimensions now reach the prompt, at 1 bullet per dimension plus 1 threat and
1 opportunity — strictly more informative than the pre-restructure result
(no dimensions at all), and with ~17% margin under budget. Rungs 4 and 5
exist for portfolios dense or large enough that rung 3 doesn't fit; they are
not expected to fire for the current portfolio size, but keep the ladder
graceful rather than a hard cliff into the scores-only floor.

Landing on rung 3 used to mean *building and serializing all 64 holdings
three times* — once each for rungs 1 and 2, discarded, before the kept
attempt at rung 3 — on every single synthesis call. ``_serialize_holdings``
now estimates the likely starting rung from one sample holding (cheap, O(1))
before doing any real O(n) digest-and-serialize, so the common case costs
exactly one full serialization instead of three. See its docstring for the
correctness guarantee: a wrong estimate can only cost an extra real
serialization, never a dropped holding.
"""


def _digest_one(sa: StrategicAnalysis, *, bullets: int, include_prose: bool, include_pestel_dimensions: bool = False, include_pestel_summary: bool = True) -> dict[str, Any]:
    """One holding's contribution at a given detail level.

    ``include_pestel_dimensions`` adds the six raw PESTEL dimensions
    (political/economic/social/technological/environmental/legal) — the
    material the portfolio prompt actually asks the model to synthesize into
    "thèmes PESTEL transversaux". Before Task 7 these were never forwarded at
    all: the synthesis call paid for a Perplexity PESTEL run per holding and
    withheld the six dimensions from the one prompt that needed them,
    sending only ``key_threats``/``key_opportunities``.

    ``include_pestel_summary`` gates those ``key_threats``/``key_opportunities``
    fields. They are the model's own *summary* of the six dimensions — derived
    evidence, not primary evidence — so the degradation ladder in
    :func:`_serialize_holdings` drops them (``include_pestel_summary=False``)
    *before* it drops the dimensions themselves. An all-or-nothing dimensions
    flag would mean dimensions are either included at full bullet count (too
    large for the real portfolio) or never included at all; shrinking bullet
    count while keeping both, then dropping the derived summary while keeping
    the primary evidence, is what actually gets dimensions to the prompt.
    """
    out: dict[str, Any] = {}
    if sa.pestel:
        pestel: dict[str, Any] = {"score": sa.pestel.strategic_score}
        if include_pestel_summary:
            pestel["threats"] = sa.pestel.key_threats[:bullets]
            pestel["opportunities"] = sa.pestel.key_opportunities[:bullets]
        if include_pestel_dimensions:
            pestel["dimensions"] = {
                "political": sa.pestel.political[:bullets],
                "economic": sa.pestel.economic[:bullets],
                "social": sa.pestel.social[:bullets],
                "technological": sa.pestel.technological[:bullets],
                "environmental": sa.pestel.environmental[:bullets],
                "legal": sa.pestel.legal[:bullets],
            }
        out["pestel"] = pestel
    if sa.swot:
        out["swot"] = {"score": sa.swot.strategic_score, "strengths": sa.swot.strengths[:bullets], "threats": sa.swot.threats[:bullets]}
        if include_prose:
            out["swot"]["assessment"] = sa.swot.strategic_assessment
    if sa.five_forces:
        out["moat"] = {"score": sa.five_forces.strategic_score}
        if include_prose:
            out["moat"]["summary"] = sa.five_forces.competitive_position_summary
    return out


_SERIALIZE_RUNGS: tuple[tuple[int, bool, bool, bool], ...] = (
    (3, True, True, True),  # full detail
    (2, True, True, True),  # fewer bullets, still both pestel fields
    (1, True, True, True),  # fewest bullets, still both pestel fields
    (1, True, False, True),  # drop the derived pestel summary, keep dimensions (primary evidence)
    (1, False, False, True),  # drop prose too, dimensions still present
)
"""(bullets, include_prose, include_pestel_summary, include_pestel_dimensions) per rung, finest first."""


def _digest_all(holdings_strategic: dict[str, StrategicAnalysis], rung: tuple[int, bool, bool, bool]) -> dict[str, Any]:
    """Digest every holding at one rung. The one place that does the O(n) work."""
    bullets, include_prose, include_pestel_summary, include_pestel_dimensions = rung
    return {
        ticker: _digest_one(sa, bullets=bullets, include_prose=include_prose, include_pestel_summary=include_pestel_summary, include_pestel_dimensions=include_pestel_dimensions)
        for ticker, sa in holdings_strategic.items()
    }


def _serialize_holdings(holdings_strategic: dict[str, StrategicAnalysis]) -> str:
    """Compact JSON digest of every holding, fitted to the budget.

    Detail degrades before the holding list does. Dropping a holding is not an
    operation this function can perform: the 2026-08-16 posture was synthesized
    from 1 of 64 holdings because the old implementation ended in ``[:30000]``.

    Degradation order: full detail -> fewer bullets (dimensions and derived
    summary shrink together) -> drop the PESTEL derived summary
    (key_threats/key_opportunities) while keeping the PESTEL dimensions,
    since the dimensions are the primary evidence a Perplexity call was paid
    for and the derived summary is the model's own restatement of it -> drop
    prose -> scores-only floor (see below), which drops the dimensions too.

    An earlier version toggled dimensions on only at full bullet count (3)
    and off everywhere else — all-or-nothing. For the real 64-holding
    portfolio, "on" (~461K chars) always overflowed the 240K budget and "off"
    was the only rung ever selected, so the dimensions never actually reached
    the prompt. Shrinking bullets while keeping both fields, then shedding
    the derived summary before the dimensions, is what gets them there.

    Rung selection is estimate-then-verify, not brute-force-from-the-top. A
    naive version rebuilds the full per-holding digest for *every* holding and
    serializes it at every rung, discarding all but the last, purely to
    measure ``len(payload)``. For the real 64-holding portfolio that means two
    full ~330-460K-char dict-builds-and-serializes thrown away on every single
    synthesis call, before ever landing on the rung it was always going to
    land on. Instead: digest and serialize *one* holding at each rung (O(1)
    per rung, not O(n)) to estimate the finest rung likely to fit, then do a
    real, full verification starting there — stepping to a coarser rung only
    if the estimate undershot. The estimate can only cost one extra real
    serialization when it's wrong; it can never cause a holding to be
    dropped, because every real candidate payload is still checked against
    the budget before being returned, and the floor below is unchanged.
    """
    import json

    if not holdings_strategic:
        return "{}"

    holding_count = len(holdings_strategic)
    sample_ticker, sample_sa = next(iter(holdings_strategic.items()))

    start_index = len(_SERIALIZE_RUNGS) - 1
    for index, rung in enumerate(_SERIALIZE_RUNGS):
        bullets, include_prose, include_pestel_summary, include_pestel_dimensions = rung
        sample_entry = json.dumps(
            {
                sample_ticker: _digest_one(
                    sample_sa, bullets=bullets, include_prose=include_prose, include_pestel_summary=include_pestel_summary, include_pestel_dimensions=include_pestel_dimensions
                )
            },
            ensure_ascii=False,
            default=str,
        )
        if len(sample_entry) * holding_count <= SYNTHESIS_PAYLOAD_BUDGET_CHARS:
            start_index = index
            break

    for rung in _SERIALIZE_RUNGS[start_index:]:
        payload = json.dumps(_digest_all(holdings_strategic, rung), ensure_ascii=False, default=str)
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
