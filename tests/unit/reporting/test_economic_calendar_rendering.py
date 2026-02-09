"""Tests for economic calendar section rendering in HTML report."""

from finwiz.reporting.section_generators import generate_economic_calendar_section

SAMPLE_CALENDAR = {
    "economic_events": [
        {
            "event": "FOMC Meeting",
            "country": "US",
            "date": "2026-03-15",
            "impact": "high",
            "estimate": 4.50,
            "prev": 4.50,
        },
        {
            "event": "CPI Release",
            "country": "US",
            "date": "2026-03-12",
            "impact": "high",
            "estimate": 3.10,
            "prev": 3.20,
        },
    ],
    "earnings_events": [
        {
            "symbol": "AAPL",
            "date": "2026-04-25",
            "eps_estimate": 2.35,
        },
        {
            "symbol": "MSFT",
            "date": "2026-04-24",
            "eps_estimate": 3.10,
        },
    ],
}


class TestEconomicCalendarEmptyWhenNoData:
    """Verify section returns empty string when no data."""

    def test_returns_empty_when_none(self):
        assert generate_economic_calendar_section(None) == ""

    def test_returns_empty_when_empty_dict(self):
        assert generate_economic_calendar_section({}) == ""


class TestEconomicCalendarRendersWithData:
    """Verify calendar section renders correctly with data."""

    def test_contains_section_header(self):
        html = generate_economic_calendar_section(SAMPLE_CALENDAR)
        assert "Calendrier Economique" in html

    def test_contains_economic_events(self):
        html = generate_economic_calendar_section(SAMPLE_CALENDAR)
        assert "FOMC Meeting" in html
        assert "2026-03-15" in html

    def test_contains_earnings_events(self):
        html = generate_economic_calendar_section(SAMPLE_CALENDAR)
        assert "AAPL" in html
        assert "2026-04-25" in html
        assert "2.35" in html

    def test_contains_french_column_headers(self):
        html = generate_economic_calendar_section(SAMPLE_CALENDAR)
        assert "Evenement" in html
        assert "Estimation" in html
        assert "Precedent" in html
        assert "Symbole" in html
        assert "BPA Estime" in html


class TestEconomicCalendarEmptyLists:
    """Verify handling of empty event lists."""

    def test_handles_empty_economic_events(self):
        data = {"economic_events": [], "earnings_events": SAMPLE_CALENDAR["earnings_events"]}
        html = generate_economic_calendar_section(data)
        assert "Aucun evenement economique programme" in html
        assert "AAPL" in html

    def test_handles_empty_earnings_events(self):
        data = {"economic_events": SAMPLE_CALENDAR["economic_events"], "earnings_events": []}
        html = generate_economic_calendar_section(data)
        assert "FOMC Meeting" in html
        assert "Aucune date de resultats a venir" in html


class TestEconomicCalendarMaxRows:
    """Verify row limits for tables."""

    def test_max_economic_events_limited(self):
        """Providing 20+ events should be limited to 15 rows."""
        many_events = [{"event": f"Event {i}", "country": "US", "date": f"2026-04-{i:02d}", "impact": "low"} for i in range(1, 22)]
        data = {"economic_events": many_events, "earnings_events": []}
        html = generate_economic_calendar_section(data)
        assert "Event 15" in html
        assert "Event 16" not in html

    def test_max_earnings_events_limited(self):
        """Providing 25+ earnings should be limited to 20 rows."""
        many_earnings = [{"symbol": f"TK{i:02d}", "date": f"2026-05-{(i % 28) + 1:02d}", "eps_estimate": float(i)} for i in range(1, 26)]
        data = {"economic_events": [], "earnings_events": many_earnings}
        html = generate_economic_calendar_section(data)
        assert "TK20" in html
        assert "TK21" not in html
