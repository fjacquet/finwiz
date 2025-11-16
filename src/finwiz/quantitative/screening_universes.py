"""
Stock universe definitions for screening.

This module provides predefined stock universes and universe-related utilities.
"""


class UniverseProvider:
    """Provides stock universes for screening."""

    @staticmethod
    def get_sp500_symbols() -> list[str]:
        """Get S&P 500 symbols (mock implementation)."""
        # In real implementation, fetch from reliable source
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK.B", "UNH", "JNJ"]

    @staticmethod
    def get_nasdaq100_symbols() -> list[str]:
        """Get NASDAQ 100 symbols (mock implementation)."""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "ADBE", "CRM"]

    @staticmethod
    def get_russell2000_symbols() -> list[str]:
        """Get Russell 2000 symbols (mock implementation)."""
        return ["AMC", "GME", "BBBY", "CLOV", "WISH", "PLTR", "SOFI", "HOOD", "RIVN", "LCID"]

    @staticmethod
    def get_dow30_symbols() -> list[str]:
        """Get Dow 30 symbols (mock implementation)."""
        return ["AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "AMGN", "CRM", "V", "BA"]
