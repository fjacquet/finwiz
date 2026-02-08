"""
IPO screener for newcomer discovery.

Queries the SEC EDGAR EFTS API for recent S-1/S-1A filings
to find recently-IPO'd companies as investment candidates.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timedelta
from typing import Any, ClassVar

import requests
import yfinance as yf

from finwiz.schemas.newcomer_discovery import NewcomerCandidate
from finwiz.tools.logger import get_logger


class IPOScreener:
    """Screens for recent IPO candidates via SEC EDGAR EFTS API."""

    SEC_EFTS_URL: ClassVar[str] = "https://efts.sec.gov/LATEST/search-index"
    SEC_USER_AGENT: ClassVar[str] = "FinWiz Research bot@finwiz.local"
    REQUEST_DELAY: ClassVar[float] = 0.15  # ~6.6 req/sec, under 10 req/sec limit

    def __init__(self) -> None:
        """Initialize IPO screener."""
        self._logger = get_logger(__name__)

    def screen(
        self,
        lookback_days: int = 180,
        max_candidates: int = 20,
    ) -> list[NewcomerCandidate]:
        """Screen for recent IPO candidates from SEC EDGAR filings.

        Args:
            lookback_days: How far back to search for S-1 filings.
            max_candidates: Maximum number of candidates to return.

        Returns:
            List of NewcomerCandidate objects for recently-IPO'd companies.
        """
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        start_date = (datetime.utcnow() - timedelta(days=lookback_days)).strftime(
            "%Y-%m-%d",
        )

        self._logger.info(
            "Screening SEC EDGAR for IPOs between %s and %s",
            start_date,
            end_date,
        )

        hits = self._query_sec_efts(start_date, end_date)
        if not hits:
            self._logger.warning("No S-1 filings found from SEC EDGAR")
            return []

        # Extract and deduplicate tickers
        seen: set[str] = set()
        unique_hits: list[dict[str, Any]] = []
        for hit in hits:
            ticker = self._extract_ticker_from_display_name(
                hit.get("display_name", ""),
            )
            if ticker and ticker not in seen:
                seen.add(ticker)
                unique_hits.append({**hit, "ticker": ticker})

        self._logger.info(
            "Found %d unique tickers from %d filing hits",
            len(unique_hits),
            len(hits),
        )

        # Enrich and build candidates
        candidates: list[NewcomerCandidate] = []
        for hit_data in unique_hits[:max_candidates]:
            ticker = hit_data["ticker"]
            try:
                fundamentals = self._enrich_with_fundamentals(ticker)
                candidate = NewcomerCandidate(
                    ticker=ticker,
                    source="ipo",
                    asset_class="stock",
                    composite_score=0.5,
                    grade="",
                    rationale=f"Recent IPO filing (S-1) dated {hit_data.get('file_date', 'unknown')}",
                    market_cap=fundamentals.get("market_cap"),
                    sector=fundamentals.get("sector"),
                    name=fundamentals.get("name", ticker),
                    metadata={
                        "filing_date": hit_data.get("file_date"),
                        "form_type": hit_data.get("form_type"),
                        "cik": hit_data.get("cik"),
                    },
                )
                candidates.append(candidate)
            except (ValueError, KeyError, TypeError):
                self._logger.warning(
                    "Failed to build candidate for ticker %s",
                    ticker,
                    exc_info=True,
                )

        self._logger.info("IPO screening returned %d candidates", len(candidates))
        return candidates

    def _query_sec_efts(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Query SEC EDGAR EFTS API for S-1 filings.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.

        Returns:
            List of filing hit dicts with display_name, file_date, form_type.
        """
        url = (
            f"{self.SEC_EFTS_URL}"
            f'?q=%22S-1%22&forms=S-1,S-1/A'
            f"&dateRange=custom&startdt={start_date}&enddt={end_date}"
            f"&from=0&size=40"
        )
        headers = {
            "User-Agent": self.SEC_USER_AGENT,
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            time.sleep(self.REQUEST_DELAY)
        except (requests.RequestException, ValueError) as exc:
            self._logger.warning("SEC EFTS API request failed: %s", exc)
            return []

        raw_hits = data.get("hits", {}).get("hits", [])
        results: list[dict[str, Any]] = []
        for hit in raw_hits:
            source = hit.get("_source", {})
            display_names = source.get("display_names", [])
            display_name = display_names[0] if display_names else ""
            results.append(
                {
                    "display_name": display_name,
                    "file_date": source.get("file_date", ""),
                    "form_type": source.get("form_type", ""),
                    "cik": source.get("entity_id", ""),
                },
            )

        self._logger.debug("SEC EFTS returned %d raw hits", len(results))
        return results

    def _extract_ticker_from_display_name(
        self,
        display_name: str,
    ) -> str | None:
        """Extract ticker symbol from SEC display name.

        SEC display_names format: "Company Name, Inc.  (TICK)  (CIK 0001234567)"

        Args:
            display_name: SEC filing display name string.

        Returns:
            Ticker string or None if no valid ticker found.
        """
        matches = re.findall(r"\(([A-Z]{1,5})\)", display_name)
        for match in matches:
            if match == "CIK" or any(c.isdigit() for c in match):
                continue
            return match
        return None

    def _enrich_with_fundamentals(self, ticker: str) -> dict[str, Any]:
        """Enrich ticker with fundamental data from yfinance.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            Dict with market_cap, sector, and name (None values on failure).
        """
        try:
            info = yf.Ticker(ticker).info
            return {
                "market_cap": info.get("marketCap"),
                "sector": info.get("sector"),
                "name": info.get("longName") or info.get("shortName") or ticker,
            }
        except (ValueError, KeyError, OSError):
            self._logger.warning(
                "Failed to enrich fundamentals for %s",
                ticker,
                exc_info=True,
            )
            return {"market_cap": None, "sector": None, "name": ticker}
