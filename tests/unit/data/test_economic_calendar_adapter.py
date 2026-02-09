"""Tests for EconomicCalendarAdapter.

Verifies Finnhub economic calendar and earnings calendar functionality,
caching, graceful error handling, and availability checks.
"""

from __future__ import annotations

from finwiz.data.adapters.economic_calendar_adapter import EconomicCalendarAdapter
from finwiz.schemas.economic_calendar import EarningsEvent, EconomicCalendar


class TestEconomicCalendarAdapter:
    """Test EconomicCalendarAdapter behavior."""

    def test_is_available_with_key(self, mocker):
        """Adapter is available when FINNHUB_API_KEY is set."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})
        adapter = EconomicCalendarAdapter()
        assert adapter.is_available() is True

    def test_is_available_without_key(self, mocker):
        """Adapter is not available when FINNHUB_API_KEY is missing."""
        mocker.patch.dict("os.environ", {}, clear=True)
        adapter = EconomicCalendarAdapter()
        assert adapter.is_available() is False

    def test_get_economic_calendar_success(self, mocker):
        """Economic calendar returns filtered US high-impact events."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_response = {
            "economicCalendar": [
                {
                    "country": "US",
                    "event": "FOMC Meeting Minutes",
                    "date": "2026-02-15",
                    "impact": "high",
                    "actual": None,
                    "estimate": None,
                    "prev": None,
                },
                {
                    "country": "US",
                    "event": "CPI Release",
                    "date": "2026-02-12",
                    "impact": "high",
                    "actual": 3.1,
                    "estimate": 3.0,
                    "prev": 2.9,
                },
                {
                    "country": "EU",
                    "event": "ECB Rate Decision",
                    "date": "2026-02-14",
                    "impact": "high",
                    "actual": None,
                    "estimate": None,
                    "prev": None,
                },
                {
                    "country": "US",
                    "event": "Minor Housing Starts",
                    "date": "2026-02-16",
                    "impact": "low",
                    "actual": None,
                    "estimate": None,
                    "prev": None,
                },
            ]
        }

        mock_client = mocker.MagicMock()
        mock_client.calendar_economic.return_value = mock_response
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        calendar = adapter.get_economic_calendar(days_ahead=30)

        assert isinstance(calendar, EconomicCalendar)
        # Should include FOMC and CPI (US + high impact keyword), exclude EU and low-impact
        assert len(calendar.economic_events) == 2
        event_names = [e.event for e in calendar.economic_events]
        assert "FOMC Meeting Minutes" in event_names
        assert "CPI Release" in event_names
        assert calendar.days_ahead == 30

    def test_get_economic_calendar_api_error(self, mocker):
        """Graceful handling: API error returns empty calendar."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_client = mocker.MagicMock()
        mock_client.calendar_economic.side_effect = RuntimeError("API rate limit exceeded")
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        calendar = adapter.get_economic_calendar()

        assert isinstance(calendar, EconomicCalendar)
        assert len(calendar.economic_events) == 0

    def test_get_earnings_calendar_success(self, mocker):
        """Earnings calendar returns events for requested tickers."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_response = {
            "earningsCalendar": [
                {
                    "symbol": "AAPL",
                    "date": "2026-02-20",
                    "epsEstimate": 2.10,
                    "epsActual": None,
                    "revenueEstimate": 120000000000.0,
                },
            ]
        }

        mock_client = mocker.MagicMock()
        mock_client.earnings_calendar.return_value = mock_response
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        events = adapter.get_earnings_calendar(["AAPL"])

        assert len(events) == 1
        assert isinstance(events[0], EarningsEvent)
        assert events[0].symbol == "AAPL"
        assert events[0].eps_estimate == 2.10
        assert events[0].revenue_estimate == 120000000000.0

    def test_get_earnings_calendar_partial_failure(self, mocker):
        """One ticker failure does not abort others."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        call_count = 0

        def mock_earnings_calendar(**kwargs):
            nonlocal call_count
            call_count += 1
            symbol = kwargs.get("symbol", "")
            if symbol == "FAIL":
                raise RuntimeError("API error for FAIL")
            return {
                "earningsCalendar": [
                    {
                        "symbol": symbol,
                        "date": "2026-03-01",
                        "epsEstimate": 1.50,
                        "epsActual": None,
                        "revenueEstimate": None,
                    }
                ]
            }

        mock_client = mocker.MagicMock()
        mock_client.earnings_calendar.side_effect = mock_earnings_calendar
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        events = adapter.get_earnings_calendar(["AAPL", "FAIL", "MSFT"])

        # AAPL and MSFT succeed, FAIL is skipped gracefully
        assert len(events) == 2
        symbols = [e.symbol for e in events]
        assert "AAPL" in symbols
        assert "MSFT" in symbols

    def test_economic_calendar_caching(self, mocker):
        """Economic calendar is fetched once and cached."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_response = {"economicCalendar": []}
        mock_client = mocker.MagicMock()
        mock_client.calendar_economic.return_value = mock_response
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        adapter.get_economic_calendar()
        adapter.get_economic_calendar()

        # Finnhub client should only be called once due to caching
        mock_client.calendar_economic.assert_called_once()

    def test_earnings_calendar_caching(self, mocker):
        """Earnings calendar is cached per ticker."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_response = {
            "earningsCalendar": [
                {
                    "symbol": "AAPL",
                    "date": "2026-02-20",
                    "epsEstimate": 2.10,
                    "epsActual": None,
                    "revenueEstimate": None,
                }
            ]
        }
        mock_client = mocker.MagicMock()
        mock_client.earnings_calendar.return_value = mock_response
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        adapter.get_earnings_calendar(["AAPL"])
        adapter.get_earnings_calendar(["AAPL"])

        # Finnhub client should only be called once due to caching
        mock_client.earnings_calendar.assert_called_once()

    def test_get_economic_calendar_nested_response(self, mocker):
        """Handle Finnhub responses with nested 'result' key."""
        mocker.patch.dict("os.environ", {"FINNHUB_API_KEY": "test-key"})

        mock_response = {
            "economicCalendar": {
                "result": [
                    {
                        "country": "US",
                        "event": "GDP Growth Rate",
                        "date": "2026-02-28",
                        "impact": "high",
                        "actual": None,
                        "estimate": 2.5,
                        "prev": 2.3,
                    }
                ]
            }
        }

        mock_client = mocker.MagicMock()
        mock_client.calendar_economic.return_value = mock_response
        mocker.patch("finnhub.Client", return_value=mock_client)

        adapter = EconomicCalendarAdapter()
        calendar = adapter.get_economic_calendar()

        assert len(calendar.economic_events) == 1
        assert calendar.economic_events[0].event == "GDP Growth Rate"
