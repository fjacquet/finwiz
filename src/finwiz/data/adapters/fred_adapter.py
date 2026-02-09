"""FRED macroeconomic data adapter.

Fetches key macro indicators from the Federal Reserve Economic Data (FRED) API.
Data is collected ONCE per session and cached.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

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

        for field, series_id in FRED_SERIES.items():
            try:
                series = fred.get_series(series_id, observation_start=lookback.strftime("%Y-%m-%d"))
                # Drop NaN values and get the latest
                series = series.dropna()
                if not series.empty:
                    data[field] = float(series.iloc[-1])
                    sources[field] = f"FRED:{series_id}"
                else:
                    data[field] = None
                    logger.warning(f"FRED series {series_id} returned no data for {field}")
            except Exception as e:
                logger.warning(f"FRED series {series_id} failed for {field}: {e}")
                data[field] = None

        # Calculate yield curve spread
        yield_curve_spread: float | None = None
        if data.get("treasury_10y") is not None and data.get("treasury_2y") is not None:
            yield_curve_spread = data["treasury_10y"] - data["treasury_2y"]  # type: ignore[operator]
            sources["yield_curve_spread"] = "computed:DGS10-DGS2"

        self._cached_snapshot = MacroSnapshot(
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
        logger.info(f"FRED macro snapshot collected: {len(sources)} indicators available")
        return self._cached_snapshot
