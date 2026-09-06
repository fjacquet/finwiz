"""Fund facts from yfinance `funds_data`.

Each accessor on `funds_data` performs its own fetch and can fail on its own, so
each is guarded separately: a fund keeps its expense ratio when its holdings are
unavailable, and vice versa. Nothing here may raise — spec §6.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Any

from finwiz.analysis.fact_pack.sources import yfinance_source
from finwiz.quantitative.etf.etf_expense_fallback import get_fallback_expense_ratio
from finwiz.schemas.hybrid_analysis.fact_pack import FundFacts, FundHolding
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_QUOTE_URL = "https://finance.yahoo.com/quote/{symbol}"
_EXPENSE_RATIO_ROW = "Annual Report Expense Ratio"
_TURNOVER_ROW = "Annual Holdings Turnover"
_MAX_HOLDINGS = 25
_SOURCES = ("yfinance.info", "yfinance.funds_data")
_EXPENSE_RATIO_FALLBACK_SOURCE = "etf_expense_ratios.yaml"
# yfinance is authoritative; the repo's manual table is only a tripwire. A
# disagreement beyond this is worth a human glancing at, not acting on.
_EXPENSE_RATIO_DISAGREEMENT_THRESHOLD = 0.0005


def _operations_value(operations: Any, symbol: str, row: str) -> float | None:
    """Read one metric from the operations frame.

    Columns are `[<symbol>, "Category Average"]`; the fund's own column is
    preferred and the first column is the fallback, because the header is
    whatever yfinance echoed back for the query.
    """
    if operations is None or getattr(operations, "empty", True):
        return None
    if row not in operations.index:
        return None
    column = symbol if symbol in operations.columns else operations.columns[0]
    value = operations.loc[row, column]
    # Cast for type purity, not because json.dumps would choke: numpy.float64
    # subclasses float and serialises fine, and Pydantic would coerce it anyway.
    # numpy.int64 is the one that breaks json.dumps -- no current field takes an
    # integer from a DataFrame, but the cast is cheap insurance if one ever does.
    return None if value is None else float(value)


def _holdings(frame: Any) -> list[FundHolding]:
    """One bad row must cost that row, not the table.

    See fund_facts's own construction guard for why: without this, a single
    NaN or out-of-range weight (yfinance is scraped, not contractual) raised
    out of `FundHolding` construction, escaped into `fund_facts`'s `try`, and
    discarded the whole pack -- issuer, expense ratio, asset mix, everything
    -- for nine other holdings that were perfectly fine.
    """
    if frame is None or getattr(frame, "empty", True):
        return []
    rows: list[FundHolding] = []
    for symbol, row in frame.iterrows():
        name = str(row.get("Name") or "").strip()
        weight = row.get("Holding Percent")
        if not name or weight is None:
            continue
        try:
            weight_f = float(weight)
        except (TypeError, ValueError):
            logger.warning(f"fact_pack: holding {symbol} has a non-numeric weight ({weight!r}); dropping this row only")
            continue
        # Layer 1: a missing "Holding Percent" in a pandas frame is NaN, not
        # None, so the None-check above doesn't catch it -- and FundHolding's
        # own `ge=0.0, le=1.0` bound is not enforced by this source. An
        # unusable weight is UNKNOWN, not a fact to repair to a boundary: for
        # a holdings row the weight *is* the content, so the row is dropped,
        # never clamped to 0.0 or 1.0.
        if not math.isfinite(weight_f) or not (0.0 <= weight_f <= 1.0):
            logger.warning(f"fact_pack: holding {symbol} has an out-of-domain weight ({weight!r}); dropping this row only")
            continue
        try:
            # Layer 2: the checks above cover every constraint this module
            # knows about; this is the backstop for one it doesn't.
            rows.append(FundHolding(symbol=str(symbol), name=name[:200], weight=weight_f))
        except Exception as e:
            logger.warning(f"fact_pack: holding {symbol} dropped, failed FundHolding construction: {e}")
            continue
        if len(rows) >= _MAX_HOLDINGS:
            break
    return rows


def _floats(mapping: Any) -> dict[str, float]:
    if not isinstance(mapping, dict):
        return {}
    return {str(k): float(v) for k, v in mapping.items() if isinstance(v, int | float)}


def _check_expense_ratio_tripwire(symbol: str, expense_ratio: float, fallback: float) -> None:
    """Log a WARNING when a genuine (non-zero) yfinance value disagrees with the repo's manual table by >5bps.

    yfinance stays authoritative regardless of the outcome — the manual table
    (`data/etf_expense_ratios.yaml`) exists as a fallback for funds yfinance
    doesn't cover, not as a source of truth to override it with.
    """
    if abs(expense_ratio - fallback) > _EXPENSE_RATIO_DISAGREEMENT_THRESHOLD:
        logger.warning(f"fact_pack: {symbol} expense ratio disagreement: yfinance={expense_ratio} data/etf_expense_ratios.yaml={fallback}")


def _resolve_expense_ratio(symbol: str, expense_ratio: float | None) -> tuple[float | None, str | None]:
    """Correct yfinance's `0.0`-as-missing encoding, using the curated table.

    yfinance encodes an unknown expense ratio as a literal `0.0` rather than
    omitting the row -- the same trap as `maxSupply == 0` meaning "uncapped"
    for crypto (see `CryptoFacts.supply_is_capped`). A live sweep of the
    portfolio's 27 ETFs on 2026-09-06 found five funds reporting `ter=0.0`,
    and not one was a genuine zero-fee fund. Treating a false zero as data
    matters here specifically: `score()` weights expense_ratio at 0.30, the
    heaviest single field, so a fabricated zero would score full marks on the
    figure investors check hardest.

    Returns `(resolved_expense_ratio, source_name_or_None)` -- the source name
    is only non-None when the table's value was substituted in, so the
    substitution is visible in the pack's provenance rather than silent.
    """
    if expense_ratio is None:
        return None, None
    if expense_ratio > 0:
        fallback = get_fallback_expense_ratio(symbol)
        if fallback is not None:
            _check_expense_ratio_tripwire(symbol, expense_ratio, fallback)
        return expense_ratio, None

    # expense_ratio == 0.0: a false zero, never a real one in this portfolio.
    fallback = get_fallback_expense_ratio(symbol)
    if fallback is None:
        logger.warning(f"fact_pack: {symbol} yfinance reports expense_ratio=0.0 (treated as missing, not a fee waiver); no data/etf_expense_ratios.yaml entry to fall back to")
        return None, None
    logger.warning(f"fact_pack: {symbol} yfinance reports a false zero expense ratio; substituting data/etf_expense_ratios.yaml value {fallback}")
    return fallback, _EXPENSE_RATIO_FALLBACK_SOURCE


def _normalize_turnover(symbol: str, turnover: float | None) -> float | None:
    """A negative Annual Holdings Turnover is not meaningful; treat as unknown.

    Observed live on 2026-09-06: a real portfolio ETF reports -0.6146, and
    `FundFacts.turnover` is `ge=0.0` -- constructing a fund's facts must not
    raise on a source's bad number. Returning None says only what's true, that
    this figure isn't usable; clamping to 0.0 would assert a fact ("zero
    turnover") the source never provided.
    """
    if turnover is not None and turnover < 0:
        logger.debug(f"fact_pack: {symbol} negative Annual Holdings Turnover ({turnover}) treated as unknown")
        return None
    return turnover


def _inception_year(query_symbol: str, info: dict[str, Any]) -> int | None:
    inception = info.get("fundInceptionDate")
    if not isinstance(inception, int | float):
        return None
    try:
        return datetime.fromtimestamp(float(inception), tz=UTC).year
    except (OSError, OverflowError, ValueError) as e:
        logger.debug(f"fact_pack: {query_symbol} unusable fundInceptionDate: {e}")
        return None


def _funds_data(query_symbol: str) -> Any:
    """Fetch `funds_data` for the symbol, or ``None`` if the network call fails."""
    try:
        return yfinance_source._ticker(query_symbol).funds_data
    except Exception as e:
        logger.warning(f"fact_pack: {query_symbol} funds_data unavailable: {e}")
        return None


def _collect_funds_data(query_symbol: str) -> tuple[Any, Any, dict[str, float], dict[str, float]]:
    """Gather operations, holdings, asset mix and sector weights.

    Each accessor fetches independently and is guarded on its own, per the
    module docstring: a fund keeps its expense ratio when its holdings are
    unavailable, and vice versa.
    """
    funds = _funds_data(query_symbol)
    if funds is None:
        return None, None, {}, {}

    operations = holdings_frame = None
    for attribute, setter in (("fund_operations", "operations"), ("top_holdings", "holdings")):
        try:
            value = getattr(funds, attribute)
        except Exception as e:
            logger.debug(f"fact_pack: {query_symbol} funds_data.{attribute} unavailable: {e}")
            continue
        if setter == "operations":
            operations = value
        else:
            holdings_frame = value

    asset_mix: dict[str, float] = {}
    try:
        asset_mix = _floats(funds.asset_classes)
    except Exception as e:
        logger.debug(f"fact_pack: {query_symbol} funds_data.asset_classes unavailable: {e}")

    sector_weights: dict[str, float] = {}
    try:
        sector_weights = _floats(funds.sector_weightings)
    except Exception as e:
        logger.debug(f"fact_pack: {query_symbol} funds_data.sector_weightings unavailable: {e}")

    return operations, holdings_frame, asset_mix, sector_weights


def fund_facts(query_symbol: str, info: dict[str, Any]) -> tuple[FundFacts | None, tuple[str, ...], tuple[str, ...]]:
    """Build fund facts, or ``None`` when the fund has no identifiable issuer or when construction fails unexpectedly (spec §6: no source may raise).

    Returns ``(facts, citations, sources)``. ``sources`` names what fed the
    pack -- always the yfinance surfaces, plus ``"etf_expense_ratios.yaml"``
    exactly when the expense ratio came from the curated table rather than
    yfinance (see `_resolve_expense_ratio`).
    """
    issuer = (info.get("fundFamily") or "").strip()
    if not issuer:
        logger.warning(f"fact_pack: {query_symbol} has no fundFamily; cannot build fund facts")
        return None, (), ()

    inception_year = _inception_year(query_symbol, info)
    operations, holdings_frame, asset_mix, sector_weights = _collect_funds_data(query_symbol)

    expense_ratio, expense_ratio_source = _resolve_expense_ratio(query_symbol, _operations_value(operations, query_symbol, _EXPENSE_RATIO_ROW))
    turnover = _normalize_turnover(query_symbol, _operations_value(operations, query_symbol, _TURNOVER_ROW))
    sources = _SOURCES if expense_ratio_source is None else (*_SOURCES, expense_ratio_source)

    try:
        facts = FundFacts(
            issuer=issuer[:200],
            legal_type=(info.get("legalType") or "").strip()[:100],
            inception_year=inception_year,
            expense_ratio=expense_ratio,
            turnover=turnover,
            top_holdings=_holdings(holdings_frame),
            asset_mix=asset_mix,
            sector_weights=sector_weights,
        )
    except Exception as e:
        # Layer 2: layer 1 (the normalization above) covers every constraint
        # this module knows about; this is the backstop for one it doesn't.
        # Logged at ERROR -- unlike the warnings above, this means the
        # enumeration above is incomplete and should never fire silently.
        logger.error(f"fact_pack: {query_symbol} FundFacts construction failed unexpectedly: {e}")
        return None, (), ()

    return facts, (_QUOTE_URL.format(symbol=query_symbol),), sources
