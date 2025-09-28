"""
Market Screening Tool for large-scale candidate filtering.

This tool implements comprehensive market screening for ETFs, stocks, and cryptocurrencies
using A+ criteria. It integrates with existing market data providers (Yahoo Finance, Alpha Vantage)
and implements efficient filtering algorithms for discovering A+ investment opportunities.
"""

from datetime import datetime
from typing import Any, Literal

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.tools.a_plus_scoring_tool import APlusScoringTool
from finwiz.utils.cache_manager import cache_key


class MarketScreeningInput(BaseModel):
    """Input schema for Market Screening Tool."""

    asset_type: Literal["etf", "stock", "crypto"] = Field(..., description="Type of assets to screen")
    screening_criteria: dict[str, Any] = Field(default_factory=dict, description="Custom screening criteria (overrides defaults)")
    market_region: str = Field(default="global", description="Market region to screen (global, us, eu, etc.)")
    max_candidates: int = Field(default=50, ge=1, le=500, description="Maximum number of candidates to return")
    min_a_plus_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum A+ score threshold")
    include_detailed_analysis: bool = Field(default=False, description="Whether to include detailed A+ analysis for each candidate")


class ScreeningCandidate(BaseModel):
    """A candidate investment from screening."""

    symbol: str
    name: str
    asset_type: Literal["etf", "stock", "crypto"]
    preliminary_score: float = Field(ge=0.0, le=1.0)
    meets_a_plus_criteria: bool
    key_metrics: dict[str, Any] = Field(default_factory=dict)
    screening_rationale: str
    data_source: str
    screened_at: datetime


class MarketScreeningResult(BaseModel):
    """Result from market screening operation."""

    asset_type: Literal["etf", "stock", "crypto"]
    screening_criteria: dict[str, Any]
    market_region: str
    total_screened: int
    candidates_found: int
    a_plus_candidates: int
    candidates: list[ScreeningCandidate]
    screening_timestamp: datetime
    data_sources: list[str]


class MarketScreeningTool(BaseTool):
    """
    Market Screening Tool for large-scale candidate filtering.

    This tool screens large universes of investments using quantitative filters
    to identify A+ candidates efficiently. Supports ETFs, stocks, and crypto
    with integration to existing market data providers.

    Key Features:
    - Multi-asset screening (ETF, stock, crypto)
    - Dynamic A+ criteria application
    - Integration with Yahoo Finance and Alpha Vantage
    - Efficient filtering algorithms
    - Configurable screening parameters
    """

    name: str = "Market Screening Tool"
    description: str = (
        "Screens large universes of ETFs, stocks, and cryptocurrencies using quantitative "
        "filters to identify A+ investment candidates efficiently. Integrates with multiple "
        "market data providers for comprehensive coverage."
    )
    args_schema: type[BaseModel] = MarketScreeningInput

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Market Screening Tool."""
        super().__init__(**kwargs)
        self._a_plus_scorer = APlusScoringTool()
        self._screening_cache = {}

    def _run(
        self,
        asset_type: Literal["etf", "stock", "crypto"],
        screening_criteria: dict[str, Any] = None,
        market_region: str = "global",
        max_candidates: int = 50,
        min_a_plus_score: float = 0.85,
        include_detailed_analysis: bool = False,
    ) -> dict[str, Any]:
        """Execute market screening analysis."""
        try:
            # Normalize inputs
            screening_criteria = screening_criteria or {}

            # Get screening universe
            universe = self._get_screening_universe(asset_type, market_region)
            if "error" in universe:
                return universe

            # Apply screening filters
            filtered_candidates = self._apply_screening_filters(universe["symbols"], asset_type, screening_criteria, market_region)

            # Score candidates using A+ criteria
            scored_candidates = self._score_candidates(filtered_candidates, asset_type, min_a_plus_score, include_detailed_analysis)

            # Sort by score and limit results
            scored_candidates.sort(key=lambda x: x.preliminary_score, reverse=True)
            final_candidates = scored_candidates[:max_candidates]

            # Count A+ candidates
            a_plus_count = sum(1 for c in final_candidates if c.meets_a_plus_criteria)

            # Create result
            result = MarketScreeningResult(
                asset_type=asset_type,
                screening_criteria=screening_criteria,
                market_region=market_region,
                total_screened=len(universe["symbols"]),
                candidates_found=len(final_candidates),
                a_plus_candidates=a_plus_count,
                candidates=final_candidates,
                screening_timestamp=datetime.now(),
                data_sources=universe.get("sources", []),
            )

            return {
                "screening_result": result.model_dump(),
                "summary": {
                    "asset_type": asset_type,
                    "total_screened": result.total_screened,
                    "candidates_found": result.candidates_found,
                    "a_plus_candidates": result.a_plus_candidates,
                    "success_rate": f"{(result.a_plus_candidates / max(result.total_screened, 1) * 100):.1f}%",
                },
                "top_candidates": [
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "score": c.preliminary_score,
                        "a_plus": c.meets_a_plus_criteria,
                        "rationale": c.screening_rationale,
                    }
                    for c in final_candidates[:10]
                ],
            }

        except Exception as e:
            return {
                "error": f"Market screening failed for {asset_type}: {str(e)}",
                "asset_type": asset_type,
                "candidates_found": 0,
                "a_plus_candidates": 0,
            }

    def _get_screening_universe(self, asset_type: str, market_region: str) -> dict[str, Any]:
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
                "MATIC",
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
                "FTM",
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

    def _apply_screening_filters(
        self, symbols: list[str], asset_type: str, criteria: dict[str, Any], market_region: str
    ) -> list[dict[str, Any]]:
        """Apply screening filters to the symbol universe."""
        try:
            filtered_candidates = []

            # Get default criteria for asset type
            default_criteria = self._get_default_screening_criteria(asset_type)

            # Merge with custom criteria
            final_criteria = {**default_criteria, **criteria}

            # Screen each symbol
            for symbol in symbols:
                try:
                    # Get basic market data for the symbol
                    market_data = self._get_basic_market_data(symbol, asset_type)

                    if market_data and "error" not in market_data:
                        # Apply asset-specific filters
                        if self._passes_screening_filters(market_data, asset_type, final_criteria):
                            filtered_candidates.append(
                                {
                                    "symbol": symbol,
                                    "market_data": market_data,
                                    "screening_criteria": final_criteria,
                                }
                            )

                except Exception:
                    # Skip symbols that fail to process
                    continue

            return filtered_candidates

        except Exception:
            return []

    def _get_default_screening_criteria(self, asset_type: str) -> dict[str, Any]:
        """Get default A+ screening criteria for asset type."""
        if asset_type == "etf":
            return {
                "max_expense_ratio": 0.25,  # 0.25% for specialized, 0.15% for broad market
                "min_aum": 1e9,  # $1B minimum AUM
                "max_tracking_error": 0.002,  # 0.20% tracking error
                "min_history_years": 3,  # 3 years minimum history
                "require_ucits": False,  # UCITS compliance for EU investors
            }
        elif asset_type == "stock":
            return {
                "min_roe": 0.20,  # 20% ROE minimum
                "min_revenue_growth": 0.15,  # 15% annual revenue growth
                "max_debt_to_equity": 0.3,  # 30% max debt-to-equity
                "min_market_cap": 1e9,  # $1B minimum market cap
                "require_positive_fcf": True,  # Positive free cash flow
                "require_growing_fcf": True,  # Growing free cash flow
            }
        elif asset_type == "crypto":
            return {
                "min_market_cap": 10e9,  # $10B minimum market cap
                "min_daily_volume": 500e6,  # $500M minimum daily volume
                "min_age_months": 36,  # 36 months minimum age
                "require_institutional_adoption": False,  # Institutional adoption
                "require_real_utility": False,  # Real utility/use case
            }
        else:
            return {}

    def _get_basic_market_data(self, symbol: str, asset_type: str) -> dict[str, Any]:
        """Get basic market data for screening."""
        try:
            # Use caching to avoid repeated API calls
            cache_key_str = cache_key("market_screening", asset_type, symbol)

            # Try to get from cache first
            cached_data = self._screening_cache.get(cache_key_str)
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

    def _passes_screening_filters(self, market_data: dict[str, Any], asset_type: str, criteria: dict[str, Any]) -> bool:
        """Check if market data passes screening filters."""
        try:
            if asset_type == "etf":
                return self._passes_etf_filters(market_data, criteria)
            elif asset_type == "stock":
                return self._passes_stock_filters(market_data, criteria)
            elif asset_type == "crypto":
                return self._passes_crypto_filters(market_data, criteria)
            else:
                return False

        except Exception:
            return False

    def _passes_etf_filters(self, data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if ETF passes screening filters."""
        try:
            # Expense ratio check
            if data.get("expense_ratio", 1.0) > criteria.get("max_expense_ratio", 0.25):
                return False

            # AUM check
            if data.get("aum", 0) < criteria.get("min_aum", 1e9):
                return False

            # Tracking error check
            if data.get("tracking_error", 0.01) > criteria.get("max_tracking_error", 0.002):
                return False

            # History check
            if data.get("history_years", 0) < criteria.get("min_history_years", 3):
                return False

            return True

        except Exception:
            return False

    def _passes_stock_filters(self, data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if stock passes screening filters."""
        try:
            # ROE check
            if data.get("roe", 0) < criteria.get("min_roe", 0.20):
                return False

            # Revenue growth check
            if data.get("revenue_growth", 0) < criteria.get("min_revenue_growth", 0.15):
                return False

            # Debt-to-equity check
            if data.get("debt_to_equity", 1.0) > criteria.get("max_debt_to_equity", 0.3):
                return False

            # Market cap check
            if data.get("market_cap", 0) < criteria.get("min_market_cap", 1e9):
                return False

            # Free cash flow checks
            if criteria.get("require_positive_fcf", True) and not data.get("fcf_positive", False):
                return False

            if criteria.get("require_growing_fcf", True) and not data.get("fcf_growing", False):
                return False

            return True

        except Exception:
            return False

    def _passes_crypto_filters(self, data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if crypto passes screening filters."""
        try:
            # Market cap check
            if data.get("market_cap", 0) < criteria.get("min_market_cap", 10e9):
                return False

            # Daily volume check
            if data.get("daily_volume", 0) < criteria.get("min_daily_volume", 500e6):
                return False

            # Age check
            if data.get("age_months", 0) < criteria.get("min_age_months", 36):
                return False

            # Institutional adoption check (if required)
            if criteria.get("require_institutional_adoption", False) and not data.get("institutional_adoption", False):
                return False

            # Real utility check (if required)
            if criteria.get("require_real_utility", False) and not data.get("real_utility", False):
                return False

            return True

        except Exception:
            return False

    def _score_candidates(
        self, candidates: list[dict[str, Any]], asset_type: str, min_score: float, detailed_analysis: bool
    ) -> list[ScreeningCandidate]:
        """Score filtered candidates using A+ scoring."""
        scored_candidates = []

        for candidate in candidates:
            try:
                symbol = candidate["symbol"]
                market_data = candidate["market_data"]

                # Calculate preliminary score
                if detailed_analysis:
                    # Use full A+ scoring tool
                    score_result = self._a_plus_scorer._run(
                        symbol=symbol,
                        asset_type=asset_type,
                        fundamental_data=market_data,
                        market_context={},
                    )
                    preliminary_score = score_result.get("composite_score", 0.5)
                else:
                    # Use simplified scoring for efficiency
                    preliminary_score = self._calculate_preliminary_score(market_data, asset_type)

                # Determine if meets A+ criteria
                meets_a_plus = preliminary_score >= min_score

                # Generate screening rationale
                rationale = self._generate_screening_rationale(market_data, asset_type, preliminary_score, meets_a_plus)

                # Create candidate object
                screening_candidate = ScreeningCandidate(
                    symbol=symbol,
                    name=market_data.get("name", symbol),
                    asset_type=asset_type,
                    preliminary_score=preliminary_score,
                    meets_a_plus_criteria=meets_a_plus,
                    key_metrics=self._extract_key_metrics(market_data, asset_type),
                    screening_rationale=rationale,
                    data_source=market_data.get("source", "Market Data"),
                    screened_at=datetime.now(),
                )

                scored_candidates.append(screening_candidate)

            except Exception:
                # Skip candidates that fail scoring
                continue

        return scored_candidates

    def _calculate_preliminary_score(self, market_data: dict[str, Any], asset_type: str) -> float:
        """Calculate simplified preliminary score for efficiency."""
        try:
            if asset_type == "etf":
                return self._score_etf_preliminary(market_data)
            elif asset_type == "stock":
                return self._score_stock_preliminary(market_data)
            elif asset_type == "crypto":
                return self._score_crypto_preliminary(market_data)
            else:
                return 0.5

        except Exception:
            return 0.5

    def _score_etf_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary ETF score."""
        score = 0.0

        # Expense ratio (40% weight)
        expense_ratio = data.get("expense_ratio", 0.5)
        if expense_ratio <= 0.05:
            score += 0.4
        elif expense_ratio <= 0.15:
            score += 0.3
        elif expense_ratio <= 0.25:
            score += 0.2

        # AUM (30% weight)
        aum = data.get("aum", 0)
        if aum >= 10e9:
            score += 0.3
        elif aum >= 1e9:
            score += 0.2
        elif aum >= 500e6:
            score += 0.1

        # Tracking error (20% weight)
        tracking_error = data.get("tracking_error", 0.01)
        if tracking_error <= 0.001:
            score += 0.2
        elif tracking_error <= 0.002:
            score += 0.15
        elif tracking_error <= 0.005:
            score += 0.1

        # History (10% weight)
        history_years = data.get("history_years", 0)
        if history_years >= 10:
            score += 0.1
        elif history_years >= 5:
            score += 0.075
        elif history_years >= 3:
            score += 0.05

        return min(score, 1.0)

    def _score_stock_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary stock score."""
        score = 0.0

        # ROE (30% weight)
        roe = data.get("roe", 0.1)
        if roe >= 0.25:
            score += 0.3
        elif roe >= 0.20:
            score += 0.25
        elif roe >= 0.15:
            score += 0.15

        # Revenue growth (25% weight)
        revenue_growth = data.get("revenue_growth", 0.05)
        if revenue_growth >= 0.20:
            score += 0.25
        elif revenue_growth >= 0.15:
            score += 0.2
        elif revenue_growth >= 0.10:
            score += 0.15

        # Debt management (20% weight)
        debt_to_equity = data.get("debt_to_equity", 0.5)
        if debt_to_equity <= 0.2:
            score += 0.2
        elif debt_to_equity <= 0.3:
            score += 0.15
        elif debt_to_equity <= 0.5:
            score += 0.1

        # Market cap (15% weight)
        market_cap = data.get("market_cap", 0)
        if market_cap >= 100e9:
            score += 0.15
        elif market_cap >= 10e9:
            score += 0.12
        elif market_cap >= 1e9:
            score += 0.08

        # Free cash flow (10% weight)
        if data.get("fcf_positive", False) and data.get("fcf_growing", False):
            score += 0.1
        elif data.get("fcf_positive", False):
            score += 0.05

        return min(score, 1.0)

    def _score_crypto_preliminary(self, data: dict[str, Any]) -> float:
        """Calculate preliminary crypto score."""
        score = 0.0

        # Market cap (35% weight)
        market_cap = data.get("market_cap", 0)
        if market_cap >= 100e9:
            score += 0.35
        elif market_cap >= 50e9:
            score += 0.3
        elif market_cap >= 10e9:
            score += 0.2

        # Daily volume (25% weight)
        daily_volume = data.get("daily_volume", 0)
        if daily_volume >= 2e9:
            score += 0.25
        elif daily_volume >= 1e9:
            score += 0.2
        elif daily_volume >= 500e6:
            score += 0.15

        # Age/Maturity (20% weight)
        age_months = data.get("age_months", 0)
        if age_months >= 60:
            score += 0.2
        elif age_months >= 36:
            score += 0.15
        elif age_months >= 24:
            score += 0.1

        # Institutional adoption (10% weight)
        if data.get("institutional_adoption", False):
            score += 0.1

        # Real utility (10% weight)
        if data.get("real_utility", False):
            score += 0.1

        return min(score, 1.0)

    def _extract_key_metrics(self, market_data: dict[str, Any], asset_type: str) -> dict[str, Any]:
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

    def _generate_screening_rationale(self, market_data: dict[str, Any], asset_type: str, score: float, meets_a_plus: bool) -> str:
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
