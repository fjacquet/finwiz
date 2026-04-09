"""Tool for fetching Yahoo Finance News."""

import datetime

import yfinance as yf  # yfinance has no official type stubs
from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schema from centralized location
from finwiz.schemas.tools import GetTickerNewsInput


class YahooFinanceNewsTool(BaseTool):
    """
    Get recent news for a financial instrument from Yahoo Finance.

    This tool retrieves recent news articles related to a specific stock,
    ETF, or cryptocurrency ticker symbol.
    """

    name: str = "Yahoo Finance News Tool"
    description: str = "Get recent news articles for stocks, ETFs, or cryptocurrencies, including headlines, publishers, and links to full articles."
    args_schema: type[BaseModel] = GetTickerNewsInput

    def _run(self, ticker: str, limit: int = 5) -> str:
        """Execute the Yahoo Finance news lookup."""
        try:
            ticker_obj = yf.Ticker(ticker)
            news = ticker_obj.news

            if not news:
                return f"No recent news found for {ticker}."

            # Limit the number of news items
            news = news[:limit]

            # Format the news items
            result = f"Recent news for {ticker}:\n\n"

            for i, item in enumerate(news, 1):
                title = item.get("title", "No title")
                publisher = item.get("publisher", "Unknown publisher")
                link = item.get("link", "#")
                published = item.get("providerPublishTime", None)

                if published:
                    # Convert timestamp to datetime
                    published_date = datetime.datetime.fromtimestamp(published)
                    published_str = published_date.strftime("%Y-%m-%d %H:%M")
                else:
                    published_str = "Unknown date"

                result += f"{i}. {title}\n"
                result += f"   Publisher: {publisher} | Date: {published_str}\n"
                result += f"   Link: {link}\n\n"

            return result
        except Exception as e:
            return f"Error retrieving news for {ticker}: {e!s}"
