"""
Market Screening Tool for large-scale candidate filtering.

This tool implements comprehensive market screening for ETFs, stocks, and cryptocurrencies
using A+ criteria. It integrates with existing market data providers (Yahoo Finance, Alpha Vantage)
and implements efficient filtering algorithms for discovering A+ investment opportunities.
"""

from datetime import datetime
from typing import Any, Literal

from crewai.tools import BaseTool
from pydantic import BaseModel

# Import schemas from centralized location
from finwiz.schemas.tools import MarketScreeningInput, MarketScreeningResult
from finwiz.tools.screening_criteria import ScreeningCriteria
from finwiz.tools.screening_ranking import ScreeningRanking
from finwiz.tools.screening_utils import ScreeningUtils


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
        self._utils = ScreeningUtils()
        self._criteria = ScreeningCriteria()
        self._ranking = ScreeningRanking()

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
            universe = self._utils.get_screening_universe(asset_type, market_region)
            if "error" in universe:
                return universe

            # Apply screening filters
            filtered_candidates = self._apply_screening_filters(universe["symbols"], asset_type, screening_criteria, market_region)

            # Score candidates using A+ criteria
            scored_candidates = self._ranking.score_candidates(
                filtered_candidates, asset_type, min_a_plus_score, include_detailed_analysis
            )

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

    def _apply_screening_filters(
        self, symbols: list[str], asset_type: str, criteria: dict[str, Any], market_region: str
    ) -> list[dict[str, Any]]:
        """Apply screening filters to the symbol universe."""
        try:
            filtered_candidates = []

            # Get default criteria for asset type
            default_criteria = self._criteria.get_default_criteria(asset_type)

            # Merge with custom criteria
            final_criteria = {**default_criteria, **criteria}

            # Screen each symbol
            for symbol in symbols:
                try:
                    # Get basic market data for the symbol
                    market_data = self._utils.get_basic_market_data(symbol, asset_type)

                    if market_data and "error" not in market_data:
                        # Apply asset-specific filters
                        if self._criteria.passes_screening_filters(market_data, asset_type, final_criteria):
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
