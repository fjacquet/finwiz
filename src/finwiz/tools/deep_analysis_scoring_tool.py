"""
Deep Analysis Scoring Tool - Wraps Python scorer for CrewAI agents.

This tool enables CrewAI agents to execute the DeepAnalysisScorer Python class
for deterministic, testable investment scoring (AI Minimalism principle).
"""

from typing import Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from finwiz.scoring.deep_analysis_scorer import DeepAnalysisScorer
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DeepAnalysisScoringInput(BaseModel):
    """Input schema for deep analysis scoring tool."""

    ticker: str = Field(..., description="Ticker symbol (e.g., 'AAPL', 'BTC-USD')")
    asset_class: str = Field(..., description="Asset class: 'stock', 'etf', or 'crypto'")
    current_price: float = Field(..., description="Current price of the asset")

    # Stock critical fields
    roe: float | None = Field(None, description="Return on Equity (for stocks)")
    debt_to_equity: float | None = Field(None, description="Debt to Equity ratio (for stocks)")
    revenue_growth: float | None = Field(None, description="Revenue growth rate (for stocks)")
    profit_margin: float | None = Field(None, description="Profit margin (for stocks)")

    # ETF critical fields
    expense_ratio: float | None = Field(None, description="Expense ratio (for ETFs)")
    tracking_error: float | None = Field(None, description="Tracking error (for ETFs)")
    aum: float | None = Field(None, description="Assets under management (for ETFs)")

    # Crypto critical fields
    market_cap: float | None = Field(None, description="Market capitalization (for crypto)")
    volume_24h: float | None = Field(None, description="24-hour trading volume (for crypto)")
    age_years: float | None = Field(None, description="Age in years (for crypto)")

    # Risk metrics (all asset classes)
    volatility: float | None = Field(None, description="Historical volatility")
    beta: float | None = Field(None, description="Beta coefficient")
    max_drawdown: float | None = Field(None, description="Maximum drawdown")

    # Technical indicators (optional)
    rsi: float | None = Field(None, description="Relative Strength Index (optional)")
    macd: float | None = Field(None, description="MACD value (optional)")


class DeepAnalysisScoringTool(BaseTool):
    """
    Tool for executing Python-based investment scoring.

    This tool wraps the DeepAnalysisScorer class to provide deterministic,
    testable investment analysis. It replaces AI-based scoring with real
    Python calculations for 10-20x speedup and 100% cost reduction.

    Performance:
    - Execution time: <1 second (vs 30-60 seconds with AI)
    - LLM calls: 0 (vs 5-10 with AI reasoning)
    - Cost: $0 (vs $0.01-0.02 with AI)
    - Reliability: 100% deterministic
    """

    name: str = "Deep Analysis Scorer"
    description: str = """Execute Python-based investment scoring for any asset.

    This tool calculates composite scores, grades, and recommendations using
    deterministic Python formulas. It requires critical fields based on asset class:

    - Stocks: current_price, roe, debt_to_equity, revenue_growth, volatility, beta
    - ETFs: current_price, expense_ratio, volatility
    - Crypto: current_price, market_cap, volume_24h, age_years, volatility

    Returns structured results with grade (A+ to F), composite score (0.0-1.0),
    recommendation (BUY/HOLD/SELL), and detailed component scores.

    Usage: Call this tool ONCE with all collected data to get final scores.
    DO NOT attempt to calculate scores yourself - this tool does it all."""

    args_schema: type[BaseModel] = DeepAnalysisScoringInput

    def __init__(self):
        """Initialize the scoring tool with DeepAnalysisScorer instance."""
        super().__init__()
        self.scorer = DeepAnalysisScorer()
        self.logger = logger

    def _run(
        self,
        ticker: str,
        asset_class: str,
        current_price: float,
        roe: float | None = None,
        debt_to_equity: float | None = None,
        revenue_growth: float | None = None,
        profit_margin: float | None = None,
        expense_ratio: float | None = None,
        tracking_error: float | None = None,
        aum: float | None = None,
        market_cap: float | None = None,
        volume_24h: float | None = None,
        age_years: float | None = None,
        volatility: float | None = None,
        beta: float | None = None,
        max_drawdown: float | None = None,
        rsi: float | None = None,
        macd: float | None = None,
    ) -> str:
        """
        Execute Python scoring calculations.

        Returns:
            JSON string with scoring results

        """
        self.logger.info(f"🔢 Executing Python scorer for {ticker} ({asset_class})")

        try:
            # Build data dict from parameters
            data = {
                "current_price": current_price,
                "volatility": volatility,
                "beta": beta,
                "max_drawdown": max_drawdown,
                "rsi": rsi,
                "macd": macd,
            }

            # Add asset-specific fields
            if asset_class == "stock":
                data.update({
                    "roe": roe,
                    "debt_to_equity": debt_to_equity,
                    "revenue_growth": revenue_growth,
                    "profit_margin": profit_margin,
                })
            elif asset_class == "etf":
                data.update({
                    "expense_ratio": expense_ratio,
                    "tracking_error": tracking_error,
                    "aum": aum,
                })
            elif asset_class == "crypto":
                data.update({
                    "market_cap": market_cap,
                    "volume_24h": volume_24h,
                    "age_years": age_years,
                })

            # Remove None values
            data = {k: v for k, v in data.items() if v is not None}

            # Execute Python scorer
            result = self.scorer.calculate_composite_score(
                ticker=ticker,
                asset_class=asset_class,
                data=data
            )

            # Convert result to JSON
            import json
            result_dict = {
                "ticker": result.ticker,
                "asset_class": result.asset_class,
                "composite_score": result.composite_score,
                "grade": result.grade,
                "recommendation": result.recommendation,
                "rationale": result.rationale,
                "fundamental_score": result.fundamental_score,
                "technical_score": result.technical_score,
                "risk_score": result.risk_score,
                "confidence_level": result.confidence_level,
            }

            self.logger.info(f"✅ Scored {ticker}: {result.grade} ({result.composite_score:.3f}) - {result.recommendation}")

            return json.dumps(result_dict, indent=2)

        except Exception as e:
            self.logger.error(f"❌ Scoring failed for {ticker}: {e}")
            # Return error result
            import json
            return json.dumps({
                "ticker": ticker,
                "error": str(e),
                "grade": "F",
                "composite_score": 0.0,
                "recommendation": "SELL",
            })
