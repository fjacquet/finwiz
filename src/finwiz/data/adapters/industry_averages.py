"""Industry averages adapter for fundamental data fallback."""

from datetime import datetime

from finwiz.tools.logger import get_logger

from .base_adapter import BaseDataAdapter, FundamentalData

# Industry average data (conservative estimates based on historical sector averages)
INDUSTRY_AVERAGES = {
    "Technology": {
        "return_on_equity": 0.18,
        "debt_to_equity": 0.35,
        "revenue_growth": 0.12,
        "profit_margin": 0.15,
    },
    "Financial": {
        "return_on_equity": 0.12,
        "debt_to_equity": 1.50,  # Banks typically have higher leverage
        "revenue_growth": 0.06,
        "profit_margin": 0.20,
    },
    "Healthcare": {
        "return_on_equity": 0.15,
        "debt_to_equity": 0.45,
        "revenue_growth": 0.08,
        "profit_margin": 0.12,
    },
    "Consumer Discretionary": {
        "return_on_equity": 0.14,
        "debt_to_equity": 0.55,
        "revenue_growth": 0.07,
        "profit_margin": 0.08,
    },
    "Consumer Staples": {
        "return_on_equity": 0.16,
        "debt_to_equity": 0.50,
        "revenue_growth": 0.04,
        "profit_margin": 0.10,
    },
    "Energy": {
        "return_on_equity": 0.10,
        "debt_to_equity": 0.60,
        "revenue_growth": 0.05,
        "profit_margin": 0.06,
    },
    "Industrials": {
        "return_on_equity": 0.13,
        "debt_to_equity": 0.50,
        "revenue_growth": 0.06,
        "profit_margin": 0.08,
    },
    "Materials": {
        "return_on_equity": 0.11,
        "debt_to_equity": 0.45,
        "revenue_growth": 0.05,
        "profit_margin": 0.07,
    },
    "Real Estate": {
        "return_on_equity": 0.08,
        "debt_to_equity": 1.20,  # REITs typically have higher leverage
        "revenue_growth": 0.04,
        "profit_margin": 0.25,
    },
    "Utilities": {
        "return_on_equity": 0.09,
        "debt_to_equity": 1.00,  # Utilities typically have higher leverage
        "revenue_growth": 0.03,
        "profit_margin": 0.12,
    },
    "Communication Services": {
        "return_on_equity": 0.14,
        "debt_to_equity": 0.65,
        "revenue_growth": 0.08,
        "profit_margin": 0.15,
    },
    # Default fallback for unknown sectors
    "Default": {
        "return_on_equity": 0.12,
        "debt_to_equity": 0.50,
        "revenue_growth": 0.06,
        "profit_margin": 0.10,
    },
}


class IndustryAveragesAdapter(BaseDataAdapter):
    """
    Industry averages adapter for fundamental data fallback.

    This adapter provides sector-specific average values as a last resort
    when all other data sources fail. It returns conservative estimates
    based on historical sector averages.

    Confidence: 0.5 (low confidence - these are generic averages)
    Warning: Always includes warning flag for fallback usage
    """

    def __init__(self, timeout_seconds: float = 0.1) -> None:
        """
        Initialize industry averages adapter.

        Args:
            timeout_seconds: Not used (data is local), but kept for interface consistency

        """
        super().__init__(timeout_seconds)
        self.logger = get_logger(__name__)

    @property
    def source_name(self) -> str:
        """Return the name of this data source."""
        return "industry_averages"

    def is_available(self) -> bool:
        """Industry averages are always available."""
        return True

    async def get_fundamental_data(self, ticker: str, sector: str | None = None) -> FundamentalData:
        """
        Get industry average fundamental data.

        Args:
            ticker: Stock ticker symbol (used for logging only)
            sector: Industry sector (e.g., 'Technology', 'Financial')
                   If None, uses 'Default' averages

        Returns:
            FundamentalData with industry average metrics

        Raises:
            DataAcquisitionError: Should not raise (always succeeds)

        """
        # Determine which sector to use
        sector_key = sector if sector in INDUSTRY_AVERAGES else "Default"

        # Get industry averages
        averages = INDUSTRY_AVERAGES[sector_key]

        # Create warnings
        warnings = ["Using industry average data as fallback", f"Sector: {sector_key}", "Low confidence - generic averages only", "All other data sources failed or timed out"]

        # Log fallback usage
        self.logger.warning(f"Using industry averages for {ticker} (sector: {sector_key}) - all other data sources failed")

        # Create FundamentalData object
        fundamental_data = FundamentalData(
            ticker=ticker,
            source="IndustryAverages",
            timestamp=datetime.now(),
            confidence=0.5,  # Low confidence for generic averages
            return_on_equity=averages["return_on_equity"],
            debt_to_equity=averages["debt_to_equity"],
            revenue_growth=averages["revenue_growth"],
            profit_margin=averages["profit_margin"],
            raw_data={"sector": sector_key, "averages": averages, "note": "Industry average data - not company-specific"},
            warnings=warnings,
        )

        return fundamental_data

    def get_available_sectors(self) -> list[str]:
        """
        Get list of available sectors.

        Returns:
            List of sector names (excluding 'Default')

        """
        return [sector for sector in INDUSTRY_AVERAGES.keys() if sector != "Default"]

    def get_sector_averages(self, sector: str) -> dict[str, float] | None:
        """
        Get averages for a specific sector.

        Args:
            sector: Sector name

        Returns:
            Dictionary of averages, or None if sector not found

        """
        return INDUSTRY_AVERAGES.get(sector)
