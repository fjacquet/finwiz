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


def _equity_rows(facts: EquityFacts) -> list[tuple[str, str]]:
    rows = [("Structure", facts.business_summary), ("Direction", facts.leadership)]
    if facts.recent_events:
        source = "dépôts réglementaires" if facts.events_from_filings else "presse"
        rows.append((f"Événements récents ({source})", "\n".join(f"- {e}" for e in facts.recent_events)))
    return rows


def _fund_rows(facts: FundFacts) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = [("Émetteur", facts.issuer)]
    if facts.legal_type:
        rows.append(("Forme", facts.legal_type))
    if facts.inception_year is not None:
        rows.append(("Création", str(facts.inception_year)))
    rows.append(("Frais courants", _pct(facts.expense_ratio)))
    if facts.top_holdings:
        lines = [f"- {h.symbol} ({h.name}) {_pct(h.weight)}" for h in facts.top_holdings[:_MAX_HOLDINGS_SHOWN]]
        rows.append(("Principales lignes", "\n".join(lines)))
    if facts.asset_mix:
        mix = ", ".join(f"{k} {_pct(v)}" for k, v in sorted(facts.asset_mix.items(), key=lambda kv: -kv[1]) if v > 0)
        if mix:
            rows.append(("Allocation", mix))
    return rows


def _crypto_rows(facts: CryptoFacts) -> list[tuple[str, str]]:
    rows = [("Protocole", facts.description)]
    if facts.launched_year is not None:
        rows.append(("Lancement", str(facts.launched_year)))
    rows.append(("Offre", _supply(facts)))
    if facts.market_cap is not None:
        rows.append(("Capitalisation", f"{facts.market_cap:,.0f}".replace(",", " ")))
    return rows


def to_rows(pack: FactPack) -> list[tuple[str, str]]:
    """Ordered (label, value) pairs suited to the pack's asset class."""
    details = pack.details
    if isinstance(details, FundFacts):
        return _fund_rows(details)
    if isinstance(details, CryptoFacts):
        return _crypto_rows(details)
    return _equity_rows(details)


def to_prompt_block(pack: FactPack) -> str:
    """The fact pack as one block for the qualitative prompt."""
    header = f"📋 FACT PACK (sources structurées, fraîcheur : {pack.freshness}, confidence : {pack.confidence:.2f})"
    body = "\n".join(f"- {label} : {value}" for label, value in to_rows(pack))
    return f"{header}\n{body}"
