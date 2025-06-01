"""
Tools for interacting with Yahoo Finance via yfinance library.

This module provides CrewAI-compatible tools to access financial market data
through the Yahoo Finance API using the yfinance library.
"""

import datetime

# No type imports needed here
import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GetTickerInfoInput(BaseModel):
    """Input schema for getting ticker information."""

    ticker: str = Field(
        ..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')"
    )


class GetTickerHistoryInput(BaseModel):
    """Input schema for getting ticker price history."""

    ticker: str = Field(
        ..., description="The ticker symbol (e.g., 'AAPL', 'VTI', 'BTC-USD')"
    )
    period: str = Field(
        "1y", description="Valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max"
    )
    interval: str = Field(
        "1d",
        description="Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo",
    )


class GetCompanyInfoInput(BaseModel):
    """Input schema for getting company information."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'MSFT').")


class GetETFHoldingsInput(BaseModel):
    """Input schema for getting ETF holdings."""

    ticker: str = Field(..., description="The ETF ticker symbol (e.g., 'VTI', 'SPY').")


class GetTickerNewsInput(BaseModel):
    """Input schema for getting news for a ticker."""

    ticker: str = Field(..., description="The ticker symbol (e.g., 'AAPL', 'BTC-USD').")
    limit: int = Field(5, description="Maximum number of news items to return.")


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
                "current_price": info.get(
                    "currentPrice", info.get("regularMarketPrice", "N/A")
                ),
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

            # Remove N/A values for cleaner output
            return {k: v for k, v in result.items() if v != "N/A"}
        except Exception as e:
            return {"error": f"Failed to get ticker info for {ticker}: {str(e)}"}


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

    def _run(self, ticker: str, period: str = "1y", interval: str = "1d") -> dict:
        """Execute the Yahoo Finance historical data lookup."""
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
                "price_change": round(
                    latest.get("close", 0) - earliest.get("close", 0), 2
                ),
                "price_change_percent": round(
                    (latest.get("close", 0) / earliest.get("close", 1) - 1) * 100, 2
                ),
                "data_points": len(history_list),
            }

            return {
                "summary": summary,
                "history": history_list[
                    -10:
                ],  # Return only last 10 data points to avoid overloading
            }
        except Exception as e:
            return {"error": f"Failed to get history for {ticker}: {str(e)}"}


class YahooFinanceCompanyInfoTool(BaseTool):
    """
    Get detailed company information from Yahoo Finance.

    This tool retrieves comprehensive company data including business description,
    financial metrics, and key performance indicators.
    """

    name: str = "Yahoo Finance Company Info Tool"
    description: str = (
        "Get detailed company information including business description, "
        "key financial metrics, and company profile."
    )
    args_schema: type[BaseModel] = GetCompanyInfoInput

    def _run(self, ticker: str) -> dict:
        """Execute the Yahoo Finance company info lookup."""
        try:
            ticker_data = yf.Ticker(ticker)
            info = ticker_data.info

            # Create a focused company profile
            company_info = {
                "symbol": ticker,
                "name": info.get("longName", "N/A"),
                "industry": info.get("industry", "N/A"),
                "sector": info.get("sector", "N/A"),
                "website": info.get("website", "N/A"),
                "country": info.get("country", "N/A"),
                "employees": info.get("fullTimeEmployees", "N/A"),
                "business_summary": info.get("longBusinessSummary", "N/A"),
                "financial_metrics": {
                    "revenue": info.get("totalRevenue", "N/A"),
                    "profit_margin": info.get("profitMargins", "N/A"),
                    "ebitda": info.get("ebitda", "N/A"),
                    "debt_to_equity": info.get("debtToEquity", "N/A"),
                    "return_on_equity": info.get("returnOnEquity", "N/A"),
                    "revenue_growth": info.get("revenueGrowth", "N/A"),
                    "earnings_growth": info.get("earningsGrowth", "N/A"),
                },
                "valuation_metrics": {
                    "market_cap": info.get("marketCap", "N/A"),
                    "pe_ratio": info.get("trailingPE", "N/A"),
                    "forward_pe": info.get("forwardPE", "N/A"),
                    "price_to_book": info.get("priceToBook", "N/A"),
                    "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
                },
            }

            # Clean up N/A values
            return {
                k: v
                if not isinstance(v, dict)
                else {k2: v2 for k2, v2 in v.items() if v2 != "N/A"}
                for k, v in company_info.items()
                if v != "N/A"
            }
        except Exception as e:
            return {"error": f"Failed to get company info for {ticker}: {str(e)}"}


class YahooFinanceETFHoldingsTool(BaseTool):
    """
    Get holdings information for an ETF from Yahoo Finance.

    This tool retrieves detailed holdings data for ETFs including
    top holdings, sector allocations, and geographical exposure.
    """

    name: str = "Yahoo Finance ETF Holdings Tool"
    description: str = (
        "Get detailed holdings information for ETFs, including top holdings, "
        "sector allocations, and asset breakdown."
    )
    args_schema: type[BaseModel] = GetETFHoldingsInput

    def _run(self, ticker: str) -> dict:
        """Execute the Yahoo Finance ETF holdings lookup."""
        try:
            etf_data = yf.Ticker(ticker)

            # Get basic ETF info
            info = etf_data.info

            # Get holdings if available
            holdings = []
            try:
                holdings_data = etf_data.get_holdings()
                if not holdings_data.empty:
                    for symbol, row in holdings_data.iterrows():
                        holding = {
                            "symbol": symbol,
                            "name": row.get("Name", "N/A"),
                            "weight": row.get("% Assets", "N/A"),
                            "shares": row.get("Shares", "N/A"),
                        }
                        holdings.append(holding)
            except Exception:
                pass

            # Get sector breakdown if available
            sector_data = {}
            try:
                sector_data = etf_data.get_sector_data()
                if isinstance(sector_data, dict):
                    sector_data = {k: float(v) for k, v in sector_data.items()}
            except Exception:
                pass

            result = {
                "symbol": ticker,
                "name": info.get("shortName", "N/A"),
                "asset_class": info.get("categoryName", "N/A"),
                "expense_ratio": info.get("annualReportExpenseRatio", "N/A"),
                "aum": info.get("totalAssets", "N/A"),
                "top_holdings": holdings[:10],  # Top 10 holdings
                "sector_breakdown": sector_data,
            }

            return {k: v for k, v in result.items() if v != "N/A" and v != []}
        except Exception as e:
            return {"error": f"Failed to get ETF holdings for {ticker}: {str(e)}"}


class YahooFinanceNewsTool(BaseTool):
    """
    Get recent news for a financial instrument from Yahoo Finance.

    This tool retrieves recent news articles related to a specific stock,
    ETF, or cryptocurrency ticker symbol.
    """

    name: str = "Yahoo Finance News Tool"
    description: str = (
        "Get recent news articles for stocks, ETFs, or cryptocurrencies, "
        "including headlines, publishers, and links to full articles."
    )
    args_schema: type[BaseModel] = GetTickerNewsInput

    def _run(self, ticker: str, limit: int = 5) -> dict:
        """Execute the Yahoo Finance news lookup."""
        try:
            ticker_data = yf.Ticker(ticker)
            news = ticker_data.news

            if not news:
                return {"error": f"No news found for {ticker}"}

            news_items = []
            for item in news[:limit]:
                news_items.append(
                    {
                        "title": item.get("title", "N/A"),
                        "publisher": item.get("publisher", "N/A"),
                        "link": item.get("link", "N/A"),
                        "published": datetime.datetime.fromtimestamp(
                            item.get("providerPublishTime", 0)
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        "summary": item.get("summary", "N/A")[:200] + "..."
                        if len(item.get("summary", "")) > 200
                        else item.get("summary", "N/A"),
                    }
                )

            return {"symbol": ticker, "news_count": len(news_items), "news": news_items}
        except Exception as e:
            return {"error": f"Failed to get news for {ticker}: {str(e)}"}
