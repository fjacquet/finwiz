"""Fund facts from yfinance `funds_data`.

Each accessor on `funds_data` performs its own fetch and can fail on its own, so
each is guarded separately: a fund keeps its expense ratio when its holdings are
unavailable, and vice versa. Nothing here may raise — spec §6.
"""

from __future__ import annotations

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
    # yfinance yields numpy.float64; Pydantic accepts it but json.dumps does not.
    return None if value is None else float(value)


def _holdings(frame: Any) -> list[FundHolding]:
    if frame is None or getattr(frame, "empty", True):
        return []
    rows: list[FundHolding] = []
    for symbol, row in frame.iterrows():
        name = str(row.get("Name") or "").strip()
        weight = row.get("Holding Percent")
        if not name or weight is None:
            continue
        rows.append(FundHolding(symbol=str(symbol), name=name[:200], weight=float(weight)))
        if len(rows) >= _MAX_HOLDINGS:
            break
    return rows


def _floats(mapping: Any) -> dict[str, float]:
    if not isinstance(mapping, dict):
        return {}
    return {str(k): float(v) for k, v in mapping.items() if isinstance(v, int | float)}


def _check_expense_ratio_tripwire(symbol: str, expense_ratio: float | None) -> None:
    """Log a WARNING when yfinance disagrees with the repo's manual table by >5bps.

    yfinance stays authoritative regardless of the outcome — the manual table
    (`data/etf_expense_ratios.yaml`) exists as a fallback for funds yfinance
    doesn't cover, not as a source of truth to override it with.
    """
    if expense_ratio is None:
        return
    fallback = get_fallback_expense_ratio(symbol)
    if fallback is None:
        return
    if abs(expense_ratio - fallback) > _EXPENSE_RATIO_DISAGREEMENT_THRESHOLD:
        logger.warning(f"fact_pack: {symbol} expense ratio disagreement: yfinance={expense_ratio} data/etf_expense_ratios.yaml={fallback}")


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


def fund_facts(query_symbol: str, info: dict[str, Any]) -> tuple[FundFacts | None, tuple[str, ...]]:
    """Build fund facts, or ``None`` when the fund has no identifiable issuer."""
    issuer = (info.get("fundFamily") or "").strip()
    if not issuer:
        logger.warning(f"fact_pack: {query_symbol} has no fundFamily; cannot build fund facts")
        return None, ()

    inception_year = _inception_year(query_symbol, info)
    operations, holdings_frame, asset_mix, sector_weights = _collect_funds_data(query_symbol)

    expense_ratio = _operations_value(operations, query_symbol, _EXPENSE_RATIO_ROW)
    _check_expense_ratio_tripwire(query_symbol, expense_ratio)

    facts = FundFacts(
        issuer=issuer[:200],
        legal_type=(info.get("legalType") or "").strip()[:100],
        inception_year=inception_year,
        expense_ratio=expense_ratio,
        turnover=_operations_value(operations, query_symbol, _TURNOVER_ROW),
        top_holdings=_holdings(holdings_frame),
        asset_mix=asset_mix,
        sector_weights=sector_weights,
    )
    return facts, (_QUOTE_URL.format(symbol=query_symbol),)
