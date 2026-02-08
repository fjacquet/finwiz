"""
Valuation Tool - CrewAI tool wrapper for price target calculations.

This tool provides AI agents with access to multiple valuation methodologies
including DCF, P/E multiples, and technical analysis-based targets. It wraps
the utility functions from finwiz.quantitative.price_targets for use in CrewAI crews.

Usage in crews:
    from finwiz.tools.valuation_tool import ValuationTool

    tool = ValuationTool()
    result = tool.calculate_stock_valuation(
        ticker="AAPL",
        current_price=150.0,
        earnings_per_share=6.50,
        cash_flows=[100, 110, 121, 133],
        discount_rate=0.10
    )
"""

import json
from typing import Any

import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.quantitative.price_targets import (
    PriceTarget,
    calculate_consensus_target,
    calculate_dcf_target,
    calculate_pe_target,
    calculate_support_resistance_targets,
    calculate_technical_target,
)
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class ValuationInput(BaseModel):
    """Input schema for valuation calculations."""

    ticker: str = Field(..., description="Stock ticker symbol")
    current_price: float = Field(..., description="Current market price")

    # DCF inputs (optional)
    cash_flows: list[float] | None = Field(None, description="Projected annual free cash flows")
    discount_rate: float | None = Field(None, description="Discount rate (WACC) as decimal")
    terminal_growth: float | None = Field(None, description="Terminal growth rate as decimal")
    shares_outstanding: float | None = Field(None, description="Number of shares outstanding")

    # P/E inputs (optional)
    earnings_per_share: float | None = Field(None, description="Earnings per share")
    target_pe_ratio: float | None = Field(None, description="Target P/E multiple")
    sector_avg_pe: float | None = Field(None, description="Sector average P/E")

    # Technical inputs (optional)
    price_history: list[float] | None = Field(None, description="Historical prices for technical analysis")


class ValuationTool(BaseTool):
    """
    Tool for calculating stock valuations using multiple methodologies.

    This tool provides AI agents with access to:
    - DCF (Discounted Cash Flow) valuation
    - P/E multiple-based targets
    - Technical analysis targets
    - Consensus targets combining multiple methods

    The tool returns structured results with confidence levels and
    upside/downside percentages for each valuation method.
    """

    name: str = "valuation_tool"
    description: str = """
    Calculate stock price targets using multiple valuation methodologies.

    Supports:
    - DCF valuation (requires cash_flows, discount_rate, terminal_growth)
    - P/E multiple valuation (requires earnings_per_share, target_pe_ratio)
    - Technical analysis (requires price_history)
    - Consensus target combining all methods

    Returns JSON with target prices, upside percentages, confidence levels,
    and detailed assumptions for each method.

    Input format:
    {
        "ticker": "AAPL",
        "current_price": 150.0,
        "cash_flows": [100, 110, 121, 133],
        "discount_rate": 0.10,
        "terminal_growth": 0.03,
        "shares_outstanding": 16000000000,
        "earnings_per_share": 6.50,
        "target_pe_ratio": 25.0,
        "price_history": [140, 145, 150, 148, 152]
    }
    """

    def _run(self, **kwargs: Any) -> str:
        """
        Execute valuation calculations.

        Args:
            **kwargs: Valuation parameters (see ValuationInput schema)

        Returns:
            JSON string with valuation results

        """
        try:
            # Validate input
            input_data = ValuationInput(**kwargs)

            logger.info(f"Calculating valuation for {input_data.ticker}")

            results = {"ticker": input_data.ticker, "current_price": input_data.current_price, "valuations": {}}

            targets: list[PriceTarget] = []

            # DCF valuation
            if input_data.cash_flows and input_data.discount_rate is not None and input_data.terminal_growth is not None:
                dcf_target = calculate_dcf_target(
                    cash_flows=input_data.cash_flows,
                    discount_rate=input_data.discount_rate,
                    terminal_growth=input_data.terminal_growth,
                    shares_outstanding=input_data.shares_outstanding,
                    current_price=input_data.current_price,
                )
                results["valuations"]["dcf"] = dcf_target.to_dict()
                targets.append(dcf_target)
                logger.debug(f"DCF target: ${dcf_target.target_price:.2f}")

            # P/E valuation
            if input_data.earnings_per_share is not None and input_data.target_pe_ratio is not None:
                pe_target = calculate_pe_target(
                    earnings_per_share=input_data.earnings_per_share,
                    target_pe_ratio=input_data.target_pe_ratio,
                    current_price=input_data.current_price,
                    sector_avg_pe=input_data.sector_avg_pe,
                )
                results["valuations"]["pe_multiple"] = pe_target.to_dict()
                targets.append(pe_target)
                logger.debug(f"P/E target: ${pe_target.target_price:.2f}")

            # Technical analysis
            if input_data.price_history and len(input_data.price_history) >= 10:
                prices = pd.Series(input_data.price_history)

                # Fibonacci target
                fib_target = calculate_technical_target(prices, method="fibonacci", current_price=input_data.current_price)
                results["valuations"]["technical_fibonacci"] = fib_target.to_dict()
                targets.append(fib_target)

                # Support/Resistance
                sr_targets = calculate_support_resistance_targets(prices, current_price=input_data.current_price)
                results["valuations"]["support_resistance"] = {
                    "resistance": sr_targets["resistance"].to_dict(),
                    "support": sr_targets["support"].to_dict(),
                }

                logger.debug("Technical targets calculated")

            # Consensus target
            if len(targets) > 1:
                consensus = calculate_consensus_target(targets)
                results["valuations"]["consensus"] = consensus.to_dict()
                logger.info(f"Consensus target: ${consensus.target_price:.2f} (confidence: {consensus.confidence:.2f})")

            # Summary
            results["summary"] = {
                "methods_used": len(targets),
                "has_dcf": "dcf" in results["valuations"],
                "has_pe": "pe_multiple" in results["valuations"],
                "has_technical": "technical_fibonacci" in results["valuations"],
                "has_consensus": "consensus" in results["valuations"],
            }

            return json.dumps(results, indent=2, default=str)

        except Exception as e:
            error_msg = f"Valuation calculation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg, "ticker": kwargs.get("ticker", "unknown")}, default=str)


# Convenience function for tool factories
def get_valuation_tool() -> ValuationTool:
    """
    Get ValuationTool instance for use in crew tool lists.

    Returns:
        ValuationTool instance

    """
    return ValuationTool()
