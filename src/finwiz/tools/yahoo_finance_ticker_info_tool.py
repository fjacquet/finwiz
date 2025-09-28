"""Tool for fetching Yahoo Finance Ticker Information."""

import logging
from datetime import UTC, datetime

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class GetTickerInfoInput(BaseModel):
    """Input schema for getting ticker information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')")


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

    def _run(self, ticker: str) -> dict:
        """Execute the Yahoo Finance ticker info lookup."""
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

            return cleaned_result
        except Exception as e:
            logger.error(f"Failed to get ticker info for {ticker}: {e}")
            return {"error": f"Failed to get ticker info for {ticker}: {str(e)}"}
