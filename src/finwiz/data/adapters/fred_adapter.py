"""FRED macroeconomic data adapter.

Fetches key macro indicators from the Federal Reserve Economic Data (FRED) API.
Data is collected ONCE per session and cached.

Transient failures are absorbed with per-series exponential-backoff retry
(tenacity, 3 attempts, 1-8s backoff).  The last successful snapshot is
persisted to output/cache/fred_snapshot.json using Pydantic's JSON
serializer so that a day of total FRED outage still yields a warm snapshot.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from finwiz.schemas.macro import MacroSnapshot
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# FRED series IDs for each macro indicator
FRED_SERIES: dict[str, str] = {
    "fed_rate": "FEDFUNDS",
    "cpi_yoy": "CPIAUCSL",
    "unemployment_rate": "UNRATE",
    "gdp_growth": "A191RL1Q225SBEA",
    "treasury_10y": "DGS10",
    "treasury_2y": "DGS2",
    "vix": "VIXCLS",
}

# FRED unit transforms, applied server-side, for series whose raw form is not
# what the field name promises.
#
# CPIAUCSL is an index level (~332 in 2025), not a rate, so taking its latest
# observation as ``cpi_yoy`` put "IPC (Inflation) 332.8 %" in front of the
# family — and pinned the indicator permanently red, since the scorer's band
# tops out at 5 %. ``pc1`` asks FRED for percent change from a year ago, which
# is the year-over-year rate every consumer of this field already assumes.
FRED_SERIES_UNITS: dict[str, str] = {
    "cpi_yoy": "pc1",
}

# On-disk fallback cache (JSON via Pydantic serializer).
FRED_CACHE_PATH = Path("output") / "cache" / "fred_snapshot.json"
FRED_CACHE_MAX_AGE = timedelta(days=7)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _fetch_series_with_retry(fred, series_id: str, observation_start: str, units: str | None = None):
    """Fetch a single FRED series with exponential backoff retry.

    ``units`` is a FRED server-side transform (e.g. ``pc1`` for percent change
    from a year ago); omitted, the series comes back in its native form.
    """
    if units is not None:
        return fred.get_series(series_id, observation_start=observation_start, units=units)
    return fred.get_series(series_id, observation_start=observation_start)


class FREDAdapter:
    """FRED macro data adapter. Data collected ONCE per session."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.api_key: str | None = os.getenv("FRED_API_KEY")
        self.timeout_seconds = timeout_seconds
        self._cached_snapshot: MacroSnapshot | None = None

    def is_available(self) -> bool:
        """Check if FRED API key is configured."""
        return self.api_key is not None

    def get_macro_snapshot(self) -> MacroSnapshot:
        """Get macro snapshot. Cached per session (collected ONCE).

        Raises:
            RuntimeError: If FRED API key is not configured.
        """
        if self._cached_snapshot is not None:
            return self._cached_snapshot

        if not self.api_key:
            raise RuntimeError("FRED_API_KEY not configured")

        from fredapi import Fred

        fred = Fred(api_key=self.api_key)

        data: dict[str, float | None] = {}
        sources: dict[str, str] = {}
        lookback = datetime.now(tz=UTC) - timedelta(days=365)
        observation_start = lookback.strftime("%Y-%m-%d")
        failed_series: list[str] = []

        for field, series_id in FRED_SERIES.items():
            units = FRED_SERIES_UNITS.get(field)
            try:
                series = _fetch_series_with_retry(fred, series_id, observation_start, units)
                series = series.dropna()
                if not series.empty:
                    data[field] = float(series.iloc[-1])
                    sources[field] = f"FRED:{series_id}({units})" if units else f"FRED:{series_id}"
                else:
                    data[field] = None
                    logger.warning(f"FRED series {series_id} returned no data for {field}")
            except Exception as e:
                logger.warning(f"FRED series {series_id} failed after retries for {field}: {e}")
                data[field] = None
                failed_series.append(field)

        # Calculate yield curve spread
        yield_curve_spread: float | None = None
        if data.get("treasury_10y") is not None and data.get("treasury_2y") is not None:
            yield_curve_spread = data["treasury_10y"] - data["treasury_2y"]  # type: ignore[operator]
            sources["yield_curve_spread"] = "computed:DGS10-DGS2"

        snapshot = MacroSnapshot(
            fed_rate=data.get("fed_rate"),
            cpi_yoy=data.get("cpi_yoy"),
            unemployment_rate=data.get("unemployment_rate"),
            gdp_growth=data.get("gdp_growth"),
            treasury_10y=data.get("treasury_10y"),
            treasury_2y=data.get("treasury_2y"),
            yield_curve_spread=yield_curve_spread,
            vix=data.get("vix"),
            data_sources=sources,
        )

        # If everything failed, fall back to on-disk snapshot (if any).
        if not sources and failed_series:
            cached = self._load_cached_snapshot()
            if cached is not None:
                self._cached_snapshot = cached
                return cached
            logger.warning("FRED: all series failed and no cached snapshot available")

        self._cached_snapshot = snapshot

        # Persist successful snapshot for future runs.
        if sources:
            self._persist_snapshot(snapshot)

        logger.info(f"FRED macro snapshot collected: {len(sources)} indicators available")
        return snapshot

    def _persist_snapshot(self, snapshot: MacroSnapshot) -> None:
        """Write snapshot to disk as JSON via Pydantic's model_dump_json."""
        try:
            FRED_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            FRED_CACHE_PATH.write_text(
                snapshot.model_dump_json(indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(f"Failed to persist FRED snapshot to {FRED_CACHE_PATH}: {e}")

    def _load_cached_snapshot(self) -> MacroSnapshot | None:
        """Load the last successful snapshot from disk, if any.

        Emits a WARNING with the cache age.  Returns None if the cache is
        absent or unreadable.
        """
        if not FRED_CACHE_PATH.exists():
            return None
        try:
            raw = FRED_CACHE_PATH.read_text(encoding="utf-8")
            snapshot = MacroSnapshot.model_validate_json(raw)
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to load cached FRED snapshot: {e}")
            return None

        fetched_utc = snapshot.fetched_at
        if fetched_utc.tzinfo is None:
            fetched_utc = fetched_utc.replace(tzinfo=UTC)
        age = datetime.now(tz=UTC) - fetched_utc
        if age > FRED_CACHE_MAX_AGE:
            logger.warning(
                "FRED cache is stale (age=%s, max=%s); using anyway as last resort",
                age,
                FRED_CACHE_MAX_AGE,
            )
        else:
            logger.warning(
                "FRED API fully unavailable; using cached snapshot (age=%s)",
                age,
            )
        return snapshot
