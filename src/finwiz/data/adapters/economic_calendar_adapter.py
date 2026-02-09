"""Finnhub economic calendar adapter.

Fetches upcoming economic events and earnings dates from Finnhub.
Session-level caching. Feature-flag gated (economic_calendar).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from finwiz.schemas.economic_calendar import (
    EarningsEvent,
    EconomicCalendar,
    EconomicEvent,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# High-impact economic event keywords
_HIGH_IMPACT_KEYWORDS = {"FOMC", "CPI", "GDP", "employment", "payroll", "interest rate", "Fed", "inflation", "PMI", "retail sales"}


class EconomicCalendarAdapter:
    """Finnhub economic calendar adapter with session-level caching.

    Fetches economic events and earnings dates. No API key required
    for basic access, but FINNHUB_API_KEY improves rate limits.
    """

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.finnhub_key: str | None = os.getenv("FINNHUB_API_KEY")
        self._cached_calendar: EconomicCalendar | None = None
        self._cached_earnings: dict[str, list[EarningsEvent]] = {}

    def is_available(self) -> bool:
        """Check if Finnhub API key is configured."""
        return self.finnhub_key is not None

    def get_economic_calendar(self, days_ahead: int = 30) -> EconomicCalendar:
        """Get upcoming economic events from Finnhub.

        Filters for US events and high-impact events (FOMC, CPI, GDP, employment).
        Results are cached per session.

        Args:
            days_ahead: Number of days to look ahead.

        Returns:
            EconomicCalendar with filtered economic events.
        """
        if self._cached_calendar is not None:
            return self._cached_calendar

        events: list[EconomicEvent] = []

        try:
            import finnhub

            client = finnhub.Client(api_key=self.finnhub_key)

            today = datetime.now()
            end_date = today + timedelta(days=days_ahead)

            response = client.calendar_economic(
                _from=today.strftime("%Y-%m-%d"),
                to=end_date.strftime("%Y-%m-%d"),
            )

            raw_events = []
            if isinstance(response, dict):
                raw_events = response.get("economicCalendar", []) or response.get("result", []) or []
                # Finnhub may wrap in another layer
                if isinstance(raw_events, dict):
                    raw_events = raw_events.get("result", []) or []

            for item in raw_events:
                country = item.get("country", "")
                event_name = item.get("event", "")

                # Filter: US events only, and high-impact events
                if country != "US":
                    continue

                is_high_impact = any(kw.lower() in event_name.lower() for kw in _HIGH_IMPACT_KEYWORDS)
                impact = item.get("impact", None)
                if not is_high_impact and impact not in ("high", "3"):
                    continue

                events.append(
                    EconomicEvent(
                        event=event_name,
                        country=country,
                        date=item.get("date", today.strftime("%Y-%m-%d")),
                        impact=str(impact) if impact else ("high" if is_high_impact else None),
                        actual=_safe_float(item.get("actual")),
                        estimate=_safe_float(item.get("estimate")),
                        prev=_safe_float(item.get("prev")),
                    )
                )

            logger.info(f"Economic calendar: {len(events)} high-impact US events in next {days_ahead} days")

        except Exception as e:
            logger.warning(f"Economic calendar fetch failed: {e}")

        calendar = EconomicCalendar(
            economic_events=events,
            fetched_at=datetime.now(),
            days_ahead=days_ahead,
        )
        self._cached_calendar = calendar
        return calendar

    def get_earnings_calendar(self, tickers: list[str], days_ahead: int = 30) -> list[EarningsEvent]:
        """Get upcoming earnings dates for specific tickers from Finnhub.

        Results are cached per ticker per session. Individual ticker failures
        do not abort processing of remaining tickers.

        Args:
            tickers: List of ticker symbols.
            days_ahead: Number of days to look ahead.

        Returns:
            List of EarningsEvent for tickers with upcoming earnings.
        """
        results: list[EarningsEvent] = []

        for ticker in tickers:
            ticker_upper = ticker.upper()

            # Check cache
            if ticker_upper in self._cached_earnings:
                results.extend(self._cached_earnings[ticker_upper])
                continue

            try:
                import finnhub

                client = finnhub.Client(api_key=self.finnhub_key)

                today = datetime.now()
                end_date = today + timedelta(days=days_ahead)

                response = client.earnings_calendar(
                    _from=today.strftime("%Y-%m-%d"),
                    to=end_date.strftime("%Y-%m-%d"),
                    symbol=ticker_upper,
                )

                raw_earnings = []
                if isinstance(response, dict):
                    raw_earnings = response.get("earningsCalendar", []) or response.get("result", []) or []

                ticker_events: list[EarningsEvent] = []
                for item in raw_earnings:
                    ticker_events.append(
                        EarningsEvent(
                            symbol=item.get("symbol", ticker_upper),
                            date=item.get("date", today.strftime("%Y-%m-%d")),
                            eps_estimate=_safe_float(item.get("epsEstimate")),
                            eps_actual=_safe_float(item.get("epsActual")),
                            revenue_estimate=_safe_float(item.get("revenueEstimate")),
                        )
                    )

                self._cached_earnings[ticker_upper] = ticker_events
                results.extend(ticker_events)

                if ticker_events:
                    logger.info(f"Earnings calendar: {len(ticker_events)} events for {ticker_upper}")

            except Exception as e:
                logger.warning(f"Earnings calendar fetch failed for {ticker_upper}: {e}")
                self._cached_earnings[ticker_upper] = []

        return results


def _safe_float(value: object) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
        return result
    except (ValueError, TypeError):
        return None
