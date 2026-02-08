"""EODHistoricalData adapter for fundamental data acquisition."""

import asyncio
import builtins
import os
from datetime import datetime
from typing import Any

import aiohttp

from finwiz.tools.logger import get_logger

from .base_adapter import BaseDataAdapter, DataAcquisitionError, FundamentalData, TimeoutError


def _safe_float(value: Any) -> float | None:
    """Safely convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _try_fields(data: dict, fields: list[str]) -> float | None:
    """Try to extract a float from the first matching field."""
    for field in fields:
        result = _safe_float(data.get(field))
        if result is not None:
            return result
    return None


def _normalize_pct(value: float | None, threshold: float = 2.0) -> float | None:
    """Convert percentage to decimal if value looks like a percentage."""
    if value is None:
        return None
    return value / 100 if abs(value) > threshold else value


class EODAdapter(BaseDataAdapter):
    """EODHistoricalData adapter. Coverage: 70K+ tickers, emerging markets."""

    def __init__(self, timeout_seconds: float = 3.0, api_key: str | None = None) -> None:
        super().__init__(timeout_seconds)
        self.logger = get_logger(__name__)
        self.api_key = api_key or os.getenv("EOD_API_KEY")
        if not self.api_key:
            self.logger.warning("EOD API key not found, adapter will be unavailable")
        self.base_url = "https://eodhistoricaldata.com/api/fundamentals"

    @property
    def source_name(self) -> str:
        return "eod"

    def is_available(self) -> bool:
        return self.api_key is not None

    async def get_fundamental_data(self, ticker: str) -> FundamentalData:
        """Get fundamental data from EODHistoricalData."""
        if not self.is_available():
            raise DataAcquisitionError("EOD API key not available")
        try:
            data = await asyncio.wait_for(self._fetch_eod_data(ticker), timeout=self.timeout_seconds)
            return self._parse_eod_data(ticker, data)
        except builtins.TimeoutError:
            raise TimeoutError(f"EOD request timed out after {self.timeout_seconds}s for {ticker}")
        except Exception as e:
            raise DataAcquisitionError(f"EOD error for {ticker}: {e!s}")

    async def _fetch_eod_data(self, ticker: str) -> dict[str, Any]:
        """Fetch data from EODHistoricalData API."""
        if "." not in ticker:
            ticker = f"{ticker}.US"

        url = f"{self.base_url}/{ticker}"
        assert self.api_key is not None  # guaranteed by is_available() check
        params = {"api_token": self.api_key, "fmt": "json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise DataAcquisitionError(f"EOD API returned status {response.status} for {ticker}")
                return await response.json()

    def _parse_eod_data(self, ticker: str, data: dict[str, Any]) -> FundamentalData:
        """Parse EOD API response into FundamentalData."""
        highlights = data.get("Highlights", {}) or {}
        valuation = data.get("Valuation", {}) or {}
        balance = self._get_latest_statement(data, "Balance_Sheet")
        income = self._get_latest_statement(data, "Income_Statement")

        warnings: list[str] = []
        roe = self._extract_roe(highlights, valuation, balance, income, warnings)
        de = self._extract_debt_to_equity(highlights, valuation, balance, warnings)
        growth = self._extract_revenue_growth(highlights, warnings)
        margin = self._extract_profit_margin(highlights, valuation, income, warnings)

        result = FundamentalData(
            ticker=ticker.split(".")[0],
            source="EOD",
            timestamp=datetime.now(),
            confidence=0.8,
            return_on_equity=roe,
            debt_to_equity=de,
            revenue_growth=growth,
            profit_margin=margin,
            raw_data=data,
            warnings=warnings,
        )
        if warnings:
            self.logger.debug(f"EOD warnings for {ticker}: {warnings}")
        return result

    def _get_latest_statement(self, data: dict[str, Any], statement_type: str) -> dict:
        """Get the most recent financial statement."""
        financials = data.get("Financials", {}) or {}
        statements = financials.get(statement_type, {}) or {}
        quarterly = statements.get("quarterly", {}) or {}
        if quarterly:
            latest_key = sorted(quarterly.keys(), reverse=True)[0]
            return quarterly[latest_key]
        yearly = statements.get("yearly", {}) or {}
        if yearly:
            latest_key = sorted(yearly.keys(), reverse=True)[0]
            return yearly[latest_key]
        return {}

    def _extract_roe(self, highlights: dict, valuation: dict, balance: dict, income: dict, warnings: list[str]) -> float | None:
        """Extract Return on Equity from EOD data."""
        # Try pre-calculated ratios first
        for source, field in [(highlights, "ReturnOnEquityTTM"), (valuation, "ReturnOnEquity")]:
            val = _normalize_pct(_safe_float(source.get(field)))
            if val is not None:
                return val

        # Calculate from net income / stockholders equity
        net_income = _safe_float(income.get("netIncome"))
        equity = _try_fields(balance, ["totalStockholderEquity", "stockholderEquity", "totalEquity"])
        if net_income is not None and equity is not None and equity != 0:
            warnings.append("ROE calculated from net income and stockholders equity")
            return net_income / equity

        warnings.append("ROE not available in EOD data")
        return None

    def _extract_debt_to_equity(self, highlights: dict, valuation: dict, balance: dict, warnings: list[str]) -> float | None:
        """Extract Debt to Equity ratio from EOD data."""
        for source, field in [(highlights, "DebtToEquity"), (valuation, "DebtToEquityRatio")]:
            val = _safe_float(source.get(field))
            if val is not None:
                return val

        # Calculate from balance sheet
        total_debt = _safe_float(balance.get("totalDebt"))
        if total_debt is None:
            lt = _safe_float(balance.get("longTermDebt")) or 0
            st = _safe_float(balance.get("shortTermDebt")) or 0
            total_debt = (lt + st) if (lt or st) else None
        equity = _try_fields(balance, ["totalStockholderEquity", "stockholderEquity", "totalEquity"])
        if total_debt is not None and equity is not None and equity != 0:
            warnings.append("Debt-to-equity calculated from balance sheet")
            return total_debt / equity

        warnings.append("Debt-to-equity ratio not available in EOD data")
        return None

    def _extract_revenue_growth(self, highlights: dict, warnings: list[str]) -> float | None:
        """Extract Revenue Growth from EOD data."""
        for field in ["RevenueGrowth", "QuarterlyRevenueGrowthYOY"]:
            val = _normalize_pct(_safe_float(highlights.get(field)), threshold=10)
            if val is not None:
                return val
        warnings.append("Revenue growth not available in EOD data")
        return None

    def _extract_profit_margin(self, highlights: dict, valuation: dict, income: dict, warnings: list[str]) -> float | None:
        """Extract Profit Margin from EOD data."""
        for source, field in [(highlights, "ProfitMargin"), (valuation, "NetProfitMargin")]:
            val = _normalize_pct(_safe_float(source.get(field)))
            if val is not None:
                return val

        # Calculate from income statement
        net_income = _safe_float(income.get("netIncome"))
        revenue = _try_fields(income, ["totalRevenue", "revenue"])
        if net_income is not None and revenue is not None and revenue != 0:
            warnings.append("Profit margin calculated from income statement")
            return net_income / revenue

        warnings.append("Profit margin not available in EOD data")
        return None
