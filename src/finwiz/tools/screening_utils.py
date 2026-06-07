"""
Utility functions for market screening operations.

This module contains utility functions for data fetching, universe generation,
and other helper operations used in market screening.
"""

from typing import Any

from finwiz.infrastructure.caching.manager import cache_key


class ScreeningUtils:
    """Utility functions for market screening operations."""

    def __init__(self) -> None:
        """Initialize screening utilities."""
        self._screening_cache: dict[str, Any] = {}

    def get_screening_universe(self, asset_type: str, market_region: str) -> dict[str, Any]:
        """Get the universe of symbols to screen."""
        try:
            if asset_type == "etf":
                return self._get_etf_universe(market_region)
            elif asset_type == "stock":
                return self._get_stock_universe(market_region)
            elif asset_type == "crypto":
                return self._get_crypto_universe(market_region)
            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

        except Exception as e:
            return {"error": f"Failed to get screening universe: {e}"}

    def _get_etf_universe(self, market_region: str) -> dict[str, Any]:
        """Get ETF universe for screening."""
        try:
            # Common ETF symbols by region
            etf_universes = {
                "us": [
                    # Broad Market ETFs
                    "SPY",
                    "VOO",
                    "IVV",
                    "VTI",
                    "ITOT",
                    "SPTM",
                    # International ETFs
                    "VEA",
                    "IEFA",
                    "EFA",
                    "VWO",
                    "IEMG",
                    "EEM",
                    # Sector ETFs
                    "XLK",
                    "XLF",
                    "XLV",
                    "XLE",
                    "XLI",
                    "XLY",
                    "XLP",
                    "XLU",
                    "XLRE",
                    "XLB",
                    "XLC",
                    # Bond ETFs
                    "BND",
                    "AGG",
                    "TLT",
                    "IEF",
                    "SHY",
                    "VTEB",
                    "LQD",
                    "HYG",
                    # Commodity ETFs
                    "GLD",
                    "SLV",
                    "DBC",
                    "USO",
                    "UNG",
                    # Factor ETFs
                    "VTV",
                    "VUG",
                    "VB",
                    "VBK",
                    "VBR",
                    "MTUM",
                    "QUAL",
                    "USMV",
                    "VLUE",
                    # International Developed
                    "VGK",
                    "VPL",
                    "VSS",
                    "VNQ",
                    "VNQI",
                ],
                "eu": [
                    # European UCITS ETFs (common symbols)
                    "VWRL",
                    "VWRA",
                    "IWDA",
                    "EUNL",
                    "IUSN",
                    "IUSA",
                    "CSEM",
                    "VFEM",
                    "VEUR",
                    "IEUR",
                    "VMID",
                    "ZPRG",
                    "VGOV",
                    "IEAG",
                    "CORP",
                    "VGEA",
                ],
                "global": [],  # Will combine all regions
            }

            if market_region == "global":
                symbols = etf_universes["us"] + etf_universes["eu"]
            else:
                symbols = etf_universes.get(market_region, etf_universes["us"])

            return {
                "symbols": symbols,
                "count": len(symbols),
                "sources": ["Static ETF Universe", "Yahoo Finance"],
            }

        except Exception as e:
            return {"error": f"Failed to get ETF universe: {e}"}

    def _get_stock_universe(self, market_region: str) -> dict[str, Any]:
        """Get stock universe for screening."""
        try:
            # Major stock symbols by region
            stock_universes = {
                "us": [
                    # Mega Cap Tech
                    "AAPL",
                    "MSFT",
                    "GOOGL",
                    "GOOG",
                    "AMZN",
                    "NVDA",
                    "META",
                    "TSLA",
                    # Large Cap Growth
                    "NFLX",
                    "CRM",
                    "ADBE",
                    "PYPL",
                    "INTC",
                    "AMD",
                    "QCOM",
                    "AVGO",
                    # Large Cap Value
                    "BRK.B",
                    "JPM",
                    "JNJ",
                    "PG",
                    "UNH",
                    "HD",
                    "V",
                    "MA",
                    "DIS",
                    "NFLX",
                    # Financial Services
                    "BAC",
                    "WFC",
                    "GS",
                    "MS",
                    "C",
                    "AXP",
                    "BLK",
                    "SCHW",
                    # Healthcare
                    "PFE",
                    "ABBV",
                    "TMO",
                    "ABT",
                    "LLY",
                    "MRK",
                    "BMY",
                    "AMGN",
                    # Consumer
                    "KO",
                    "PEP",
                    "WMT",
                    "COST",
                    "MCD",
                    "SBUX",
                    "NKE",
                    "TGT",
                    # Industrial
                    "BA",
                    "CAT",
                    "GE",
                    "MMM",
                    "HON",
                    "UPS",
                    "RTX",
                    "LMT",
                    # Energy
                    "XOM",
                    "CVX",
                    "COP",
                    "EOG",
                    "SLB",
                    "PSX",
                    "VLO",
                    "MPC",
                ],
                "eu": [
                    # European Large Caps
                    "ASML",
                    "SAP",
                    "LVMH",
                    "NVO",
                    "ROG",
                    "NESN",
                    "MC",
                    "OR",
                    "RMS",
                    "CDI",
                    "SU",
                    "TTE",
                    "SHEL",
                    "AZN",
                    "RDSA",
                ],
                "global": [],  # Will combine regions
            }

            if market_region == "global":
                symbols = stock_universes["us"] + stock_universes["eu"]
            else:
                symbols = stock_universes.get(market_region, stock_universes["us"])

            return {
                "symbols": symbols,
                "count": len(symbols),
                "sources": ["Static Stock Universe", "Yahoo Finance", "Alpha Vantage"],
            }

        except Exception as e:
            return {"error": f"Failed to get stock universe: {e}"}

    def _get_crypto_universe(self, market_region: str) -> dict[str, Any]:
        """Get cryptocurrency universe for screening."""
        try:
            # Top cryptocurrencies by market cap
            crypto_symbols = [
                # Top 10 by market cap
                "BTC",
                "ETH",
                "BNB",
                "XRP",
                "ADA",
                "SOL",
                "DOGE",
                "DOT",
                "AVAX",
                "POL",  # formerly MATIC (Polygon migrated to POL in 2024)
                # DeFi and Layer 1s
                "LINK",
                "UNI",
                "AAVE",
                "COMP",
                "MKR",
                "SNX",
                "CRV",
                "SUSHI",
                # Layer 2 and Scaling
                "LRC",
                "IMX",
                "MINA",
                "ALGO",
                "ATOM",
                "NEAR",
                "S",  # formerly FTM (Fantom rebranded to Sonic in 2024)
                "ONE",
                # Store of Value / Digital Gold
                "LTC",
                "BCH",
                "XMR",
                "ZEC",
                "DASH",
                # Enterprise/Utility
                "VET",
                "THETA",
                "FIL",
                "GRT",
                "BAT",
                "ENJ",
                "MANA",
                "SAND",
            ]

            return {
                "symbols": crypto_symbols,
                "count": len(crypto_symbols),
                "sources": ["Static Crypto Universe", "CoinGecko API"],
            }

        except Exception as e:
            return {"error": f"Failed to get crypto universe: {e}"}

    def get_basic_market_data(self, symbol: str, asset_type: str) -> dict[str, Any]:
        """Get basic market data for screening."""
        try:
            # Use caching to avoid repeated API calls
            cache_key_str = cache_key("market_screening", asset_type, symbol)

            # Try to get from cache first
            cached_data: dict[str, Any] | None = self._screening_cache.get(cache_key_str)
            if cached_data:
                return cached_data

            # Fetch fresh data based on asset type
            if asset_type == "etf":
                data = self._get_etf_market_data(symbol)
            elif asset_type == "stock":
                data = self._get_stock_market_data(symbol)
            elif asset_type == "crypto":
                data = self._get_crypto_market_data(symbol)
            else:
                return {"error": f"Unsupported asset type: {asset_type}"}

            # Cache the result
            if data and "error" not in data:
                self._screening_cache[cache_key_str] = data

            return data

        except Exception as e:
            return {"error": f"Failed to get market data for {symbol}: {e}"}

    def _get_etf_market_data(self, symbol: str) -> dict[str, Any]:
        """Get ETF market data for screening."""
        try:
            # Simulate ETF data - in production would use real APIs
            etf_data_map = {
                "SPY": {
                    "name": "SPDR S&P 500 ETF Trust",
                    "expense_ratio": 0.0945,
                    "aum": 400e9,
                    "tracking_error": 0.001,
                    "history_years": 25,
                    "issuer": "SPDR",
                },
                "VOO": {
                    "name": "Vanguard S&P 500 ETF",
                    "expense_ratio": 0.03,
                    "aum": 300e9,
                    "tracking_error": 0.0008,
                    "history_years": 12,
                    "issuer": "Vanguard",
                },
                "VTI": {
                    "name": "Vanguard Total Stock Market ETF",
                    "expense_ratio": 0.03,
                    "aum": 250e9,
                    "tracking_error": 0.0012,
                    "history_years": 20,
                    "issuer": "Vanguard",
                },
            }

            # Get data or create default
            data = etf_data_map.get(
                symbol,
                {
                    "name": f"ETF {symbol}",
                    "expense_ratio": 0.20,  # Default 0.20%
                    "aum": 5e8,  # Default $500M
                    "tracking_error": 0.005,  # Default 0.50%
                    "history_years": 2,  # Default 2 years
                    "issuer": "Unknown",
                },
            )

            data["symbol"] = symbol
            data["asset_type"] = "etf"
            return data

        except Exception as e:
            return {"error": f"Failed to get ETF data: {e}"}

    def _get_stock_market_data(self, symbol: str) -> dict[str, Any]:
        """Get stock market data for screening."""
        try:
            # Simulate stock data - in production would use real APIs
            stock_data_map = {
                "AAPL": {
                    "name": "Apple Inc.",
                    "market_cap": 3000e9,
                    "roe": 0.28,
                    "revenue_growth": 0.08,
                    "debt_to_equity": 0.15,
                    "fcf_positive": True,
                    "fcf_growing": True,
                },
                "MSFT": {
                    "name": "Microsoft Corporation",
                    "market_cap": 2800e9,
                    "roe": 0.35,
                    "revenue_growth": 0.12,
                    "debt_to_equity": 0.20,
                    "fcf_positive": True,
                    "fcf_growing": True,
                },
                "GOOGL": {
                    "name": "Alphabet Inc.",
                    "market_cap": 1800e9,
                    "roe": 0.22,
                    "revenue_growth": 0.15,
                    "debt_to_equity": 0.10,
                    "fcf_positive": True,
                    "fcf_growing": True,
                },
            }

            # Get data or create default
            data = stock_data_map.get(
                symbol,
                {
                    "name": f"Stock {symbol}",
                    "market_cap": 5e8,  # Default $500M
                    "roe": 0.12,  # Default 12% ROE
                    "revenue_growth": 0.05,  # Default 5% growth
                    "debt_to_equity": 0.5,  # Default 50% debt-to-equity
                    "fcf_positive": False,  # Default no FCF
                    "fcf_growing": False,
                },
            )

            data["symbol"] = symbol
            data["asset_type"] = "stock"
            return data

        except Exception as e:
            return {"error": f"Failed to get stock data: {e}"}

    def _get_crypto_market_data(self, symbol: str) -> dict[str, Any]:
        """Get crypto market data for screening."""
        try:
            # Simulate crypto data - in production would use real APIs
            crypto_data_map = {
                "BTC": {
                    "name": "Bitcoin",
                    "market_cap": 800e9,
                    "daily_volume": 15e9,
                    "age_months": 180,
                    "institutional_adoption": True,
                    "real_utility": True,
                },
                "ETH": {
                    "name": "Ethereum",
                    "market_cap": 400e9,
                    "daily_volume": 8e9,
                    "age_months": 100,
                    "institutional_adoption": True,
                    "real_utility": True,
                },
                "ADA": {
                    "name": "Cardano",
                    "market_cap": 15e9,
                    "daily_volume": 300e6,
                    "age_months": 80,
                    "institutional_adoption": False,
                    "real_utility": True,
                },
            }

            # Get data or create default
            data = crypto_data_map.get(
                symbol,
                {
                    "name": f"Crypto {symbol}",
                    "market_cap": 1e9,  # Default $1B
                    "daily_volume": 50e6,  # Default $50M
                    "age_months": 24,  # Default 2 years
                    "institutional_adoption": False,
                    "real_utility": False,
                },
            )

            data["symbol"] = symbol
            data["asset_type"] = "crypto"
            return data

        except Exception as e:
            return {"error": f"Failed to get crypto data: {e}"}

    def extract_key_metrics(self, market_data: dict[str, Any], asset_type: str) -> dict[str, Any]:
        """Extract key metrics for display."""
        if asset_type == "etf":
            return {
                "expense_ratio": market_data.get("expense_ratio"),
                "aum": market_data.get("aum"),
                "tracking_error": market_data.get("tracking_error"),
                "history_years": market_data.get("history_years"),
            }
        elif asset_type == "stock":
            return {
                "market_cap": market_data.get("market_cap"),
                "roe": market_data.get("roe"),
                "revenue_growth": market_data.get("revenue_growth"),
                "debt_to_equity": market_data.get("debt_to_equity"),
            }
        elif asset_type == "crypto":
            return {
                "market_cap": market_data.get("market_cap"),
                "daily_volume": market_data.get("daily_volume"),
                "age_months": market_data.get("age_months"),
                "institutional_adoption": market_data.get("institutional_adoption"),
            }
        else:
            return {}

    def generate_screening_rationale(self, market_data: dict[str, Any], asset_type: str, score: float, meets_a_plus: bool) -> str:
        """Generate rationale for screening result."""
        symbol = market_data.get("symbol", "Unknown")
        name = market_data.get("name", symbol)

        if meets_a_plus:
            rationale = f"{name} ({symbol}) qualifies as A+ candidate with score {score:.2f}. "
        else:
            rationale = f"{name} ({symbol}) shows potential with score {score:.2f} but needs improvement for A+ status. "

        # Add asset-specific rationale
        if asset_type == "etf":
            expense_ratio = market_data.get("expense_ratio", 0.5)
            aum = market_data.get("aum", 0)
            rationale += f"Expense ratio: {expense_ratio:.2f}%, AUM: ${aum / 1e9:.1f}B. "

        elif asset_type == "stock":
            roe = market_data.get("roe", 0.1)
            growth = market_data.get("revenue_growth", 0.05)
            rationale += f"ROE: {roe:.1%}, Revenue growth: {growth:.1%}. "

        elif asset_type == "crypto":
            market_cap = market_data.get("market_cap", 0)
            volume = market_data.get("daily_volume", 0)
            rationale += f"Market cap: ${market_cap / 1e9:.1f}B, Daily volume: ${volume / 1e6:.0f}M. "

        if meets_a_plus:
            rationale += "Meets all A+ screening criteria for further analysis."
        else:
            rationale += "Consider for monitoring as fundamentals improve."

        return rationale
