"""Holding analysis processing and data extraction utilities."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import AssetClass
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class HoldingAnalysis(BaseModel):
    """Complete analysis for a single holding."""

    # Basic info
    ticker: str
    name: str
    asset_class: AssetClass
    currency: str

    # Analysis data
    fundamental_analysis: dict | None = None
    technical_analysis: dict | None = None
    sec_citations: list[dict] = Field(default_factory=list)

    # Metadata
    analysis_date: datetime
    data_freshness: Literal["fresh", "recent", "stale"]
    crew_analysis_used: str | None = None
    composite_score: float = Field(ge=0.0, le=1.0, default=0.65)
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.5)


class HoldingProcessor:
    """Process holding analysis data and extract information from crew outputs."""

    @staticmethod
    def map_cached_to_holding_analysis(
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str,
        cached_data: dict,
    ) -> HoldingAnalysis:
        """
        Map cached crew output to HoldingAnalysis schema.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class
            currency: Currency
            name: Holding name
            cached_data: Cached crew output

        Returns:
            HoldingAnalysis with mapped data

        """
        age_days = cached_data.get("age_days", 0)

        # Determine freshness
        if age_days <= 2:
            freshness = "fresh"
        elif age_days <= 7:
            freshness = "recent"
        else:
            freshness = "stale"

        # Extract analysis data from crew output
        fundamental_analysis = HoldingProcessor.extract_fundamental_analysis(cached_data, asset_class)
        technical_analysis = HoldingProcessor.extract_technical_analysis(cached_data)
        sec_citations = HoldingProcessor.extract_sec_citations(cached_data)

        # Extract composite score if available
        composite_score = HoldingProcessor.extract_composite_score(cached_data)

        return HoldingAnalysis(
            ticker=ticker,
            name=name or ticker,
            asset_class=asset_class,
            currency=currency,
            fundamental_analysis=fundamental_analysis,
            technical_analysis=technical_analysis,
            sec_citations=sec_citations,
            analysis_date=datetime.now(),
            data_freshness=freshness,
            crew_analysis_used=f"{asset_class}_crew",
            composite_score=composite_score,
            confidence_level=0.8 if freshness == "fresh" else 0.6,
        )

    @staticmethod
    def extract_fundamental_analysis(data: dict, asset_class: AssetClass) -> dict | None:
        """Extract fundamental analysis from crew output."""
        # For stocks: look for 10-K insights, financial metrics
        if asset_class == "stock":
            pydantic_output = data.get("pydantic")
            if pydantic_output and isinstance(pydantic_output, dict):
                return {
                    "ten_k_insights": pydantic_output.get("ten_k_insights", {}),
                    "financial_metrics": pydantic_output.get("financial_metrics", {}),
                }

        # For ETFs: look for expense ratio, holdings, tracking error
        elif asset_class == "etf":
            pydantic_output = data.get("pydantic")
            if pydantic_output and isinstance(pydantic_output, dict):
                return {
                    "expense_ratio": pydantic_output.get("expense_ratio"),
                    "tracking_error": pydantic_output.get("tracking_error"),
                    "holdings": pydantic_output.get("holdings", []),
                }

        return None

    @staticmethod
    def extract_technical_analysis(data: dict[str, Any]) -> dict | None:
        """Extract technical analysis from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            return {
                "technical_indicators": pydantic_output.get("technical_indicators", {}),
                "price_patterns": pydantic_output.get("price_patterns", {}),
            }
        return None

    @staticmethod
    def extract_sec_citations(data: dict[str, Any]) -> list[dict]:
        """Extract SEC citations from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            citations = pydantic_output.get("sec_citations", [])
            if isinstance(citations, list):
                return citations
        return []

    @staticmethod
    def extract_composite_score(data: dict[str, Any]) -> float:
        """Extract composite score from crew output."""
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            score = pydantic_output.get("composite_score")
            if isinstance(score, (int, float)):
                return float(score)
        return 0.65  # Default baseline

    @staticmethod
    def create_baseline_analysis(
        ticker: str,
        asset_class: AssetClass,
        currency: str,
        name: str,
    ) -> HoldingAnalysis:
        """
        Create baseline analysis when no crew data available.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class
            currency: Currency
            name: Holding name

        Returns:
            Baseline HoldingAnalysis

        """
        # Baseline scores by asset class
        baseline_scores = {
            "stock": 0.60,
            "etf": 0.65,
            "crypto": 0.55,
        }

        return HoldingAnalysis(
            ticker=ticker,
            name=name or ticker,
            asset_class=asset_class,
            currency=currency,
            fundamental_analysis=None,
            technical_analysis=None,
            sec_citations=[],
            analysis_date=datetime.now(),
            data_freshness="stale",
            crew_analysis_used=None,
            composite_score=baseline_scores.get(asset_class, 0.60),
            confidence_level=0.3,  # Low confidence for baseline
        )

    @staticmethod
    def contains_ticker_analysis(data: dict, ticker: str) -> bool:
        """
        Check if crew output contains analysis for the given ticker.

        Args:
            data: Crew output data
            ticker: Ticker to search for

        Returns:
            True if ticker analysis found

        """
        # Check various possible locations in crew output
        # This is a simplified check - actual implementation would be more robust
        raw_output = data.get("raw_output", "")
        if ticker.upper() in raw_output.upper():
            return True

        # Check pydantic output if present
        pydantic_output = data.get("pydantic")
        if pydantic_output and isinstance(pydantic_output, dict):
            ticker_field = pydantic_output.get("ticker", "")
            if ticker.upper() == ticker_field.upper():
                return True

        return False

    @staticmethod
    def load_cached_analysis(
        ticker: str,
        output_dir: "Path",
        asset_class: str,
        max_age_days: int = 7,
    ) -> dict | None:
        """
        Load cached analysis from file system.

        Args:
            ticker: Ticker symbol
            output_dir: Output directory for asset class
            asset_class: Asset class name
            max_age_days: Maximum age in days for cache validity

        Returns:
            Cached analysis dict if found and fresh, None otherwise

        """
        import json
        from datetime import datetime

        latest_file = output_dir / f"{asset_class}_latest.json"
        if not latest_file.exists():
            return None

        try:
            with open(latest_file) as f:
                data = json.load(f)

            # Check if this analysis is for our ticker
            if not HoldingProcessor.contains_ticker_analysis(data, ticker):
                return None

            # Check age
            file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
            age = datetime.now() - file_mtime
            age_days = age.days

            if age_days <= max_age_days:
                logger.info(
                    "Found cached analysis",
                    extra={
                        "ticker": ticker,
                        "age_days": age_days,
                        "file": str(latest_file),
                    },
                )
                data["age_days"] = age_days
                return data

            logger.info(
                "Cached analysis too old",
                extra={"ticker": ticker, "age_days": age_days},
            )
        except Exception as e:
            logger.error(
                "Error reading cached analysis",
                extra={"ticker": ticker, "error": str(e)},
            )

        return None
