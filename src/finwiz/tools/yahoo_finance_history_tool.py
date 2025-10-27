"""Tool for fetching Yahoo Finance Ticker History."""

from datetime import UTC, datetime

import yfinance as yf  # type: ignore[import-untyped]  # yfinance has no official type stubs
from crewai.tools import BaseTool
from pydantic import BaseModel

from finwiz.schemas.tools import GetTickerHistoryInput
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class YahooFinanceHistoryTool(BaseTool):
    """
    Get historical price data for a financial instrument from Yahoo Finance.

    This tool retrieves historical price data for stocks, ETFs, or cryptocurrencies
    over a specified time period and interval.
    """

    name: str = "Yahoo Finance History Tool"
    description: str = (
        "Get historical price data (open, high, low, close, volume) for stocks, ETFs,"
        " or cryptocurrencies over various time periods and intervals."
    )
    args_schema: type[BaseModel] = GetTickerHistoryInput

    def _run(self, ticker: str, period: str = "1y", interval: str = "1d", prefetched_data: dict | None = None) -> dict:
        """
        Execute the Yahoo Finance historical data lookup.

        Args:
            ticker: Stock ticker symbol
            period: Time period for historical data (e.g., '1y', '2y', '5y')
            interval: Data interval (e.g., '1d', '1wk', '1mo')
            prefetched_data: Optional pre-fetched historical data from batch operation

        Returns:
            Dictionary with historical price data and summary statistics

        """
        # Check for pre-fetched data first
        if prefetched_data is not None and ticker in prefetched_data:
            logger.debug(f"Using pre-fetched historical data for {ticker} (source: batch)")
            cached_history = prefetched_data[ticker]

            # Add source indicator for debugging
            cached_history["data_source"] = "prefetched"
            return cached_history

        # Fall back to live API call
        logger.debug(f"Fetching live historical data for {ticker} (source: API)")
        try:
            ticker_data = yf.Ticker(ticker)
            history = ticker_data.history(period=period, interval=interval)

            if history.empty:
                return {"error": f"No historical data available for {ticker}"}

            # Format the data for easier consumption
            history_list = []
            for date, row in history.iterrows():
                history_list.append(
                    {
                        "date": date.strftime("%Y-%m-%d"),
                        "open": round(float(row.get("Open", 0)), 2),
                        "high": round(float(row.get("High", 0)), 2),
                        "low": round(float(row.get("Low", 0)), 2),
                        "close": round(float(row.get("Close", 0)), 2),
                        "volume": int(row.get("Volume", 0)),
                    }
                )

            # Add summary statistics
            latest = history_list[-1] if history_list else {}
            earliest = history_list[0] if history_list else {}

            summary = {
                "symbol": ticker,
                "period": period,
                "interval": interval,
                "start_date": earliest.get("date", "N/A"),
                "end_date": latest.get("date", "N/A"),
                "price_change": round(latest.get("close", 0) - earliest.get("close", 0), 2),
                "price_change_percent": round((latest.get("close", 0) / earliest.get("close", 1) - 1) * 100, 2),
                "data_points": len(history_list),
            }

            # Add timestamp for freshness validation
            result = {
                "summary": summary,
                "history": history_list[-10:],  # Return only last 10 data points to avoid overloading
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Use the latest data point date as the data timestamp if available
            if history_list:
                latest_date = history_list[-1]["date"]
                try:
                    # Convert date string back to datetime for better timestamp
                    data_date = datetime.strptime(latest_date, "%Y-%m-%d")
                    result["data_time"] = data_date.replace(tzinfo=UTC).isoformat()
                    logger.debug(f"Latest data point for {ticker}: {latest_date}")
                except ValueError as e:
                    logger.warning(f"Could not parse latest date for {ticker}: {e}")

            # Add source indicator
            result["data_source"] = "live_api"

            return result
        except Exception as e:
            return {"error": f"Failed to get history for {ticker}: {str(e)}"}
