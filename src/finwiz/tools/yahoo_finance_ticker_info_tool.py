"""Tool for fetching Yahoo Finance Ticker Information."""

from datetime import UTC, datetime

import yfinance as yf  # type: ignore[import-untyped]  # yfinance has no official type stubs
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.schemas.tools import GetTickerInfoInput
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class YahooFinanceTickerInfoTool(BaseTool):
    """
    Get basic information about a financial instrument from Yahoo Finance.

    This tool retrieves key data points about a stock, ETF, or cryptocurrency
    including current price, market cap, 52-week range, and more.
    """

    name: str = "Yahoo Finance Ticker Info Tool"
    description: str = (
        "Get current information about stocks, ETFs, or cryptocurrencies including price,"
        " market cap, P/E ratio, volume, and other key stats."
    )
    args_schema: type[BaseModel] = GetTickerInfoInput

    def _run(self, ticker: str, prefetched_data: dict | None = None) -> dict:
        """
        Execute the Yahoo Finance ticker info lookup.

        Args:
            ticker: Stock ticker symbol
            prefetched_data: Optional pre-fetched data from batch operation

        Returns:
            Dictionary with ticker information

        """
        # Check for pre-fetched data first
        if prefetched_data is not None and ticker in prefetched_data:
            logger.debug(f"Using pre-fetched data for {ticker} (source: batch)")
            cached_info = prefetched_data[ticker]

            # Add source indicator for debugging
            cached_info["data_source"] = "prefetched"
            return cached_info

        # Fall back to live API call
        logger.debug(f"Fetching live data for {ticker} (source: API)")
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info

            # Format a clean subset of the most important information
            result = {
                "symbol": ticker,
                "name": info.get("shortName", "N/A"),
                "currency": info.get("currency", "N/A"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                "previous_close": info.get("previousClose", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "volume": info.get("volume", "N/A"),
                "average_volume": info.get("averageVolume", "N/A"),
                "52wk_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52wk_low": info.get("fiftyTwoWeekLow", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
            }

            # Add timestamp for freshness validation
            result["timestamp"] = datetime.now(UTC).isoformat()

            # Add market time if available from Yahoo Finance
            if "regularMarketTime" in info:
                try:
                    market_time = datetime.fromtimestamp(info["regularMarketTime"], tz=UTC)
                    result["market_time"] = market_time.isoformat()
                    logger.debug(f"Market time for {ticker}: {market_time}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse market time for {ticker}: {e}")

            # Remove N/A values for cleaner output (but keep timestamp)
            cleaned_result = {k: v for k, v in result.items() if v != "N/A"}

            # Ensure timestamp is always included
            if "timestamp" not in cleaned_result:
                cleaned_result["timestamp"] = result["timestamp"]

            # Add source indicator
            cleaned_result["data_source"] = "live_api"

            return cleaned_result
        except Exception as e:
            logger.error(f"Failed to get ticker info for {ticker}: {e}")
            return {"error": f"Failed to get ticker info for {ticker}: {str(e)}"}
