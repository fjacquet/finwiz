"""Batched market-data helpers for the Portfolio-Aware Opportunity Cascade.

Provides two cheap, batch-oriented primitives used by the gap profile and the
discovery pipeline:

* :func:`get_returns` — one batched ``yf.download`` for many tickers, returning
  daily simple returns as plain lists.
* :func:`get_sectors` — per-ticker ``.info`` sector lookup.

Both memoize to a per-day on-disk JSON cache under ``output/cache/`` so a second
run on the same day is served from disk (the warm-run speed lever). The async
:class:`CacheManager` is intentionally not used here — these helpers are called
from synchronous discovery orchestrators.

All functions degrade gracefully: any fetch failure yields an empty/missing
entry rather than raising, so the cascade falls back to neutral fit.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from finwiz.discovery.ticker_hygiene import is_tradable
from finwiz.discovery.ticker_utils import to_yfinance_symbol
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

_CACHE_DIR = Path("output") / "cache"
# In-process memo so repeated calls within one run never re-read disk or network.
_returns_memo: dict[str, list[float]] = {}
_sectors_memo: dict[str, str | None] = {}


def _today_tag() -> str:
    return date.today().isoformat()


def _cache_path(kind: str) -> Path:
    return _CACHE_DIR / f"{kind}_{_today_tag()}.json"


def _load_cache(kind: str) -> dict[str, object]:
    path = _cache_path(kind)
    try:
        if path.exists():
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError) as e:
        logger.warning("Failed to read %s cache: %s", kind, e)
    return {}


def _save_cache(kind: str, data: dict[str, object]) -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _cache_path(kind).open("w", encoding="utf-8") as f:
            json.dump(data, f, default=str)
    except OSError as e:
        logger.warning("Failed to write %s cache: %s", kind, e)


def get_returns(
    tickers: list[str],
    asset_class: str = "stock",
    period: str = "6mo",
) -> dict[str, list[float]]:
    """Return daily simple returns per ticker via a single batched download.

    Args:
        tickers: Bare ticker symbols.
        asset_class: Drives yfinance symbol normalization (crypto ``-USD``).
        period: yfinance history period.

    Returns:
        Mapping of bare ticker -> list of daily returns. Tickers that fail to
        download are omitted.
    """
    if not tickers:
        return {}

    wanted = sorted({t.upper() for t in tickers if is_tradable(t)})
    out: dict[str, list[float]] = {}
    missing: list[str] = []
    for t in wanted:
        if t in _returns_memo:
            out[t] = _returns_memo[t]
        else:
            missing.append(t)

    if missing:
        disk = _load_cache("returns")
        still_missing: list[str] = []
        for t in missing:
            cached = disk.get(t)
            if isinstance(cached, list):
                try:
                    series = [float(x) for x in cached]
                except (TypeError, ValueError):
                    # Corrupted cache entry -> treat as a miss and re-fetch, rather
                    # than aborting get_returns() and breaking the fail-soft path.
                    still_missing.append(t)
                    continue
                _returns_memo[t] = series
                out[t] = series
            else:
                still_missing.append(t)

        if still_missing:
            fetched = _download_returns(still_missing, asset_class, period)
            disk_update = dict(disk)
            for t in still_missing:
                series = fetched.get(t, [])
                _returns_memo[t] = series
                if series:
                    out[t] = series
                    disk_update[t] = series
            _save_cache("returns", disk_update)

    return out


def _download_returns(tickers: list[str], asset_class: str, period: str) -> dict[str, list[float]]:
    """Batch-download close prices and convert to daily returns. Best effort."""
    import yfinance as yf

    query_map = {to_yfinance_symbol(t, asset_class): t for t in tickers}
    result: dict[str, list[float]] = {}
    try:
        data = yf.download(
            list(query_map.keys()),
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
            threads=True,
        )
    except Exception as e:
        logger.warning("Batch price download failed for %d tickers: %s", len(tickers), e)
        return result

    if data is None or getattr(data, "empty", True):
        return result

    for query_sym, bare in query_map.items():
        try:
            if hasattr(data.columns, "levels") and query_sym in data.columns.get_level_values(0):
                closes = data[query_sym]["Close"].dropna()
            elif "Close" in getattr(data, "columns", []):  # single-ticker frame
                closes = data["Close"].dropna()
            else:
                continue
            returns = closes.pct_change().dropna().tolist()
            if returns:
                result[bare] = [float(x) for x in returns]
        except (KeyError, ValueError, TypeError):
            continue
    return result


def get_sectors(tickers: list[str], asset_class: str = "stock") -> dict[str, str | None]:
    """Return a ``ticker -> sector`` map via cached per-ticker ``.info`` lookups.

    Missing/failed sectors map to ``None`` (the sector term is then skipped
    downstream). ETFs and crypto generally have no equity sector and map to
    ``None`` by design.
    """
    if not tickers:
        return {}

    wanted = sorted({t.upper() for t in tickers if is_tradable(t)})
    out: dict[str, str | None] = {}
    missing: list[str] = []
    for t in wanted:
        if t in _sectors_memo:
            out[t] = _sectors_memo[t]
        else:
            missing.append(t)

    if missing:
        disk = _load_cache("sectors")
        disk_update = dict(disk)
        still_missing = [t for t in missing if t not in disk]
        for t in missing:
            if t in disk:
                raw = disk[t]
                sector: str | None = raw if isinstance(raw, str) else None
                _sectors_memo[t] = sector
                out[t] = sector

        if still_missing:
            fetched = _fetch_sectors(still_missing, asset_class)
            for t in still_missing:
                sector = fetched.get(t)
                _sectors_memo[t] = sector
                out[t] = sector
                disk_update[t] = sector
            _save_cache("sectors", disk_update)

    return out


# Calibration target: a candidate up ~12%+ over a 6-month window with ordinary
# daily volatility (~1.5%) must be able to reach the C floor (0.65,
# grading_system.py:39-90), while a flat/mediocre/declining candidate at the
# same volatility must not. The original gain of 4 centered at zero return
# compressed realistic candidates into 0.50-0.65, so the grade ladder was
# unreachable and discovery reported "0 opportunities" for a universe it had
# graded rather than searched. The floor itself stays at C -- weak signals are
# excluded, never low-graded. Values verified against a grid of representative
# (cumulative return, daily volatility) pairs, not just the zero-volatility
# degenerate case: see tests/unit/discovery/test_market_data.py.
_MOMENTUM_GAIN = 9.0
_MOMENTUM_CENTER = 0.05
_VOL_PENALTY = 12.0


def factor_score_from_returns(returns: list[float] | None) -> float | None:
    """Standalone quality factor score in ``[0, 1]`` from a daily-return series.

    Blends momentum (period cumulative return, logistic-squashed) with a
    low-volatility bonus. This lets *every* universe ticker get a standalone
    score from the same bulk download used for correlation — so recall is no
    longer gated by whether a ticker tripped a breakout/momentum signal.

    Returns ``None`` when the series is too short to be meaningful.
    """
    if not returns or len(returns) < 5:
        return None

    import numpy as np

    arr = np.asarray(returns, dtype=float)
    cumulative = float(np.prod(1.0 + arr) - 1.0)
    momentum = 1.0 / (1.0 + np.exp(-_MOMENTUM_GAIN * (cumulative - _MOMENTUM_CENTER)))
    daily_vol = float(arr.std())
    vol_score = max(0.0, min(1.0, 1.0 - daily_vol * _VOL_PENALTY))
    score = 0.7 * momentum + 0.3 * vol_score
    return max(0.0, min(1.0, float(score)))


def _fetch_sectors(tickers: list[str], asset_class: str) -> dict[str, str | None]:
    """Per-ticker sector lookup via yfinance ``.info``. Best effort."""
    import yfinance as yf

    result: dict[str, str | None] = {}
    for bare in tickers:
        try:
            info = yf.Ticker(to_yfinance_symbol(bare, asset_class)).info
            sector = info.get("sector")
            result[bare] = sector if isinstance(sector, str) and sector else None
        except Exception:
            result[bare] = None
    return result
