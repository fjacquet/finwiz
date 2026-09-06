"""Presentation for fact packs. The only place class labels are defined.

The prompt and the HTML report both read from here, so a label cannot say
"Direction" in one and "Émetteur" in the other for the same holding.
"""

from __future__ import annotations

from finwiz.schemas.hybrid_analysis.fact_pack import CryptoFacts, EquityFacts, FactPack, FundFacts

_MAX_HOLDINGS_SHOWN = 5


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}".replace(".", ",") + " %"


def _supply(facts: CryptoFacts) -> str:
    circulating = "—" if facts.circulating_supply is None else f"{facts.circulating_supply:,.0f}".replace(",", " ")
    if facts.supply_is_capped and facts.max_supply is not None:
        cap = f"{facts.max_supply:,.0f}".replace(",", " ")
        return f"{circulating} en circulation, plafond {cap}"
    return f"{circulating} en circulation, aucun plafond"


Row = tuple[str, str | list[str]]


def _equity_rows(facts: EquityFacts) -> list[Row]:
    rows: list[Row] = [("Structure", facts.business_summary), ("Direction", facts.leadership)]
    if facts.recent_events:
        source = "dépôts réglementaires" if facts.events_from_filings else "presse"
        rows.append((f"Événements récents ({source})", list(facts.recent_events)))
    return rows


def _fund_rows(facts: FundFacts) -> list[Row]:
    rows: list[Row] = [("Émetteur", facts.issuer)]
    if facts.legal_type:
        rows.append(("Forme", facts.legal_type))
    if facts.inception_year is not None:
        rows.append(("Création", str(facts.inception_year)))
    rows.append(("Frais courants", _pct(facts.expense_ratio)))
    if facts.top_holdings:
        lines = [f"{h.symbol} ({h.name}) {_pct(h.weight)}" for h in facts.top_holdings[:_MAX_HOLDINGS_SHOWN]]
        rows.append(("Principales lignes", lines))
    if facts.asset_mix:
        buckets = [f"{k} {_pct(v)}" for k, v in sorted(facts.asset_mix.items(), key=lambda kv: -kv[1]) if v > 0]
        if buckets:
            rows.append(("Allocation", buckets))
    return rows


def _crypto_rows(facts: CryptoFacts) -> list[Row]:
    rows: list[Row] = [("Protocole", facts.description)]
    if facts.launched_year is not None:
        rows.append(("Lancement", str(facts.launched_year)))
    rows.append(("Offre", _supply(facts)))
    if facts.market_cap is not None:
        rows.append(("Capitalisation", f"{facts.market_cap:,.0f}".replace(",", " ")))
    return rows


def to_rows(pack: FactPack) -> list[Row]:
    """Ordered (label, value) pairs suited to the pack's asset class.

    A value is a plain ``str`` when it is prose (a business summary, an
    issuer name -- content with no internal structure a consumer should
    reparse) and a ``list[str]`` when it is genuinely a list (holdings,
    recent events, allocation buckets). Before this contract, every value
    was a string, and multi-item ones were newline-joined with a "- "
    marker that each of the three consumers (the prompt, the HTML report,
    the report-card table cell) decoded by hand, differently -- and the
    prompt's decoding was wrong: it prefixed every row with "- ", so a
    fund's holdings sat at the same indentation as "- Émetteur", reading to
    the model as sibling facts about the fund rather than as a list nested
    under one fact. Making the type explicit lets each consumer format
    correctly instead of guessing from whether a string happens to contain
    "\\n".
    """
    details = pack.details
    if isinstance(details, FundFacts):
        return _fund_rows(details)
    if isinstance(details, CryptoFacts):
        return _crypto_rows(details)
    return _equity_rows(details)


def to_prompt_block(pack: FactPack) -> str:
    """The fact pack as one block for the qualitative prompt.

    A list-valued row is indented beneath its own label rather than joined
    onto one line or given its own top-level "- " marker -- either would
    read, inside the block the prompt itself calls AUTORITAIRE, as several
    sibling facts about the fund instead of the items of one fact.
    """
    header = f"📋 FACT PACK (sources structurées, fraîcheur : {pack.freshness}, confidence : {pack.confidence:.2f})"
    lines = [header]
    for label, value in to_rows(pack):
        if isinstance(value, list):
            lines.append(f"- {label} :")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {label} : {value}")
    return "\n".join(lines)
