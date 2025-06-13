"""
Tool for fetching Yahoo Finance ETF Holdings.
"""
import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GetETFHoldingsInput(BaseModel):
    """Input schema for getting ETF holdings."""

    ticker: str = Field(..., description="The ETF ticker symbol (e.g., 'VTI', 'SPY').")


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
