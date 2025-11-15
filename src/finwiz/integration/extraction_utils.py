"""
Utility functions for A+ opportunity extraction.

This module provides helper functions for generating summaries, calculating
confidence scores, and extracting recommendations from opportunity data.
"""

import logging
from typing import Any


class ExtractionUtils:
    """Utility functions for opportunity extraction and analysis."""

    def __init__(self) -> None:
        """Initialize extraction utilities."""
        self.logger = logging.getLogger(__name__)

    def generate_discovery_summary(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> str:
        """Generate a summary of the discovery analysis."""
        total_opportunities = len(stocks) + len(etfs) + len(cryptos)

        if total_opportunities == 0:
            return "No A+ opportunities identified in current market conditions."

        summary_parts = []

        if stocks:
            a_plus_stocks = [s for s in stocks if s["grade"] == "A+"]
            summary_parts.append(f"{len(stocks)} stock opportunities identified ({len(a_plus_stocks)} A+ grade)")

        if etfs:
            a_plus_etfs = [e for e in etfs if e["grade"] == "A+"]
            summary_parts.append(f"{len(etfs)} ETF opportunities identified ({len(a_plus_etfs)} A+ grade)")

        if cryptos:
            a_plus_cryptos = [c for c in cryptos if c["grade"] == "A+"]
            summary_parts.append(f"{len(cryptos)} crypto opportunities identified ({len(a_plus_cryptos)} A+ grade)")

        summary = f"Discovery analysis identified {total_opportunities} high-quality investment opportunities: " + ", ".join(summary_parts)
        summary += ". Opportunities selected based on fundamental analysis, competitive moats, valuation attractiveness, and portfolio integration potential."

        return summary

    def calculate_confidence_score(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> float:
        """Calculate overall confidence score based on data availability and quality."""
        if not any([stocks, etfs, cryptos]):
            return 0.0

        # Base confidence on data availability
        base_confidence = 0.7

        # Boost confidence based on number of opportunities
        total_opportunities = len(stocks) + len(etfs) + len(cryptos)
        if total_opportunities >= 10:
            base_confidence += 0.2
        elif total_opportunities >= 5:
            base_confidence += 0.1

        # Boost confidence based on A+ grades
        a_plus_count = sum(
            [
                len([s for s in stocks if s["grade"] == "A+"]),
                len([e for e in etfs if e["grade"] == "A+"]),
                len([c for c in cryptos if c["grade"] == "A+"]),
            ]
        )

        if a_plus_count >= 5:
            base_confidence += 0.1
        elif a_plus_count >= 2:
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def extract_allocation_recommendations(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> list[dict]:
        """Extract allocation recommendations from all opportunities."""
        recommendations = []

        for idx, stock in enumerate(stocks, start=1):
            if stock.get("allocation_recommendation"):
                recommendations.append(
                    {
                        "asset_type": "stock",
                        "symbol": stock["symbol"],
                        "allocation": stock["allocation_recommendation"],
                        "grade": stock["grade"],
                        "rank": idx,
                    }
                )

        for idx, etf in enumerate(etfs, start=1):
            if etf.get("allocation_recommendation"):
                recommendations.append(
                    {
                        "asset_type": "etf",
                        "symbol": etf["symbol"],
                        "allocation": etf["allocation_recommendation"],
                        "grade": etf["grade"],
                        "rank": idx,
                    }
                )

        for idx, crypto in enumerate(cryptos, start=1):
            if crypto.get("allocation_recommendation"):
                recommendations.append(
                    {
                        "asset_type": "crypto",
                        "symbol": crypto["symbol"],
                        "allocation": crypto["allocation_recommendation"],
                        "grade": crypto["grade"],
                        "rank": idx,
                    }
                )

        return recommendations

    def extract_replacement_notes(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> list[str]:
        """Extract replacement notes from all opportunities."""
        notes = []

        for stock in stocks:
            if stock.get("replacement_note"):
                notes.append(f"{stock['symbol']}: {stock['replacement_note']}")

        for etf in etfs:
            if etf.get("replacement_note"):
                notes.append(f"{etf['symbol']}: {etf['replacement_note']}")

        for crypto in cryptos:
            if crypto.get("replacement_note"):
                notes.append(f"{crypto['symbol']}: {crypto['replacement_note']}")

        return notes
