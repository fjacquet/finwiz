"""
Market Context Extractor for extracting market regime and context indicators from discovery crew outputs.

This module provides extraction logic for market context including regime type, VIX levels,
inflation rates, interest rate trends, and macroeconomic indicators.
"""

import logging

from pydantic import BaseModel, Field

from finwiz.schemas.investment_discovery import APlusDiscoveryResult, MarketRegime


class VIXIndicators(BaseModel):
    """VIX volatility indicators."""

    current_vix: float = Field(..., ge=0.0, le=100.0, description="Current VIX level")
    vix_percentile: float = Field(..., ge=0.0, le=100.0, description="Historical percentile")
    vix_trend: str = Field(..., description="VIX trend (rising/falling/stable)")
    volatility_regime: str = Field(..., description="Volatility regime (low/normal/elevated/extreme)")


class MacroIndicators(BaseModel):
    """Macroeconomic indicators."""

    inflation_rate: float = Field(..., ge=-5.0, le=20.0, description="Current inflation rate percentage")
    interest_rate: float = Field(..., ge=0.0, le=20.0, description="Current interest rate percentage")
    interest_rate_trend: str = Field(..., description="Interest rate trend (rising/falling/stable)")
    gdp_growth: float | None = Field(None, description="GDP growth rate percentage")
    unemployment_rate: float | None = Field(None, description="Unemployment rate percentage")


class MarketContextSummary(BaseModel):
    """Summary of market context for reporting."""

    market_regime: MarketRegime = Field(..., description="Current market regime assessment")
    vix_indicators: VIXIndicators = Field(..., description="VIX volatility indicators")
    macro_indicators: MacroIndicators = Field(..., description="Macroeconomic indicators")
    risk_environment: str = Field(..., description="Risk environment (favorable/neutral/challenging)")
    allocation_implications: list[str] = Field(default_factory=list, description="How context affects allocations")


class MarketContextExtractor:
    """
    Extracts market context indicators from discovery crew outputs.

    This class provides methods to extract and structure market context data including
    regime type, VIX levels, inflation rates, interest rate trends, and macroeconomic
    indicators for comprehensive risk assessment and allocation recommendations.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Initialize the market context extractor.

        Args:
            logger: Optional logger instance for logging operations

        """
        self.logger = logger or logging.getLogger(__name__)
        self.logger.info("MarketContextExtractor initialized")

    def extract_market_regime(self, discovery_result: APlusDiscoveryResult) -> MarketRegime | None:
        """
        Extract market regime from APlusDiscoveryResult.

        Args:
            discovery_result: APlusDiscoveryResult containing market context

        Returns:
            MarketRegime with extracted data, or None if unavailable

        """
        try:
            # Extract market regime directly from discovery result
            market_regime = discovery_result.market_context

            self.logger.info(
                f"Extracted market regime: {market_regime.regime_type}, "
                f"VIX: {market_regime.vix_level:.2f}, "
                f"Stress: {market_regime.market_stress_level}"
            )
            return market_regime

        except Exception as e:
            self.logger.error(f"Failed to extract market regime: {e}")
            return None

    def extract_vix_indicators(self, discovery_result: APlusDiscoveryResult) -> VIXIndicators | None:
        """
        Extract VIX indicators with percentile calculations from discovery result.

        Args:
            discovery_result: APlusDiscoveryResult containing VIX data

        Returns:
            VIXIndicators with extracted data, or None if unavailable

        """
        try:
            market_regime = discovery_result.market_context
            current_vix = market_regime.vix_level

            # Calculate VIX percentile based on historical ranges
            vix_percentile = self._calculate_vix_percentile(current_vix)

            # Determine VIX trend based on current level and stress
            vix_trend = self._determine_vix_trend(market_regime)

            # Classify volatility regime
            volatility_regime = self._classify_volatility_regime(current_vix)

            indicators = VIXIndicators(
                current_vix=current_vix,
                vix_percentile=vix_percentile,
                vix_trend=vix_trend,
                volatility_regime=volatility_regime,
            )

            self.logger.info(
                f"Extracted VIX indicators: {current_vix:.2f} ({vix_percentile:.1f}th percentile, {volatility_regime} regime)"
            )
            return indicators

        except Exception as e:
            self.logger.error(f"Failed to extract VIX indicators: {e}")
            return None

    def extract_macro_indicators(self, discovery_result: APlusDiscoveryResult) -> MacroIndicators | None:
        """
        Extract macroeconomic indicators from discovery result.

        Args:
            discovery_result: APlusDiscoveryResult containing macro data

        Returns:
            MacroIndicators with extracted data, or None if unavailable

        """
        try:
            market_regime = discovery_result.market_context

            # Extract core macro indicators
            indicators = MacroIndicators(
                inflation_rate=market_regime.inflation_rate,
                interest_rate=self._estimate_interest_rate(market_regime),
                interest_rate_trend=market_regime.interest_rate_trend,
                gdp_growth=self._extract_gdp_growth(discovery_result),
                unemployment_rate=self._extract_unemployment_rate(discovery_result),
            )

            self.logger.info(
                f"Extracted macro indicators: Inflation {indicators.inflation_rate:.2f}%, "
                f"Interest rate trend: {indicators.interest_rate_trend}"
            )
            return indicators

        except Exception as e:
            self.logger.error(f"Failed to extract macro indicators: {e}")
            return None

    def get_market_context_summary(self, discovery_result: APlusDiscoveryResult) -> MarketContextSummary | None:
        """
        Generate comprehensive market context summary for reporting.

        Args:
            discovery_result: APlusDiscoveryResult containing market context

        Returns:
            MarketContextSummary with aggregated context data, or None if unavailable

        """
        try:
            # Extract all components
            market_regime = self.extract_market_regime(discovery_result)
            vix_indicators = self.extract_vix_indicators(discovery_result)
            macro_indicators = self.extract_macro_indicators(discovery_result)

            if not all([market_regime, vix_indicators, macro_indicators]):
                self.logger.warning("Incomplete market context data, using conservative assumptions")
                return self._create_conservative_summary()

            # Assess risk environment
            risk_environment = self._assess_risk_environment(market_regime, vix_indicators, macro_indicators)

            # Generate allocation implications
            allocation_implications = self._generate_allocation_implications(
                market_regime, vix_indicators, macro_indicators, risk_environment
            )

            summary = MarketContextSummary(
                market_regime=market_regime,
                vix_indicators=vix_indicators,
                macro_indicators=macro_indicators,
                risk_environment=risk_environment,
                allocation_implications=allocation_implications,
            )

            self.logger.info(
                f"Generated market context summary: {risk_environment} risk environment, "
                f"{len(allocation_implications)} allocation implications"
            )
            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate market context summary: {e}")
            return None

    # Private helper methods

    def _calculate_vix_percentile(self, current_vix: float) -> float:
        """
        Calculate VIX percentile based on historical ranges.

        Historical VIX ranges (approximate):
        - 10-15: Very low (10th-30th percentile)
        - 15-20: Normal (30th-60th percentile)
        - 20-30: Elevated (60th-85th percentile)
        - 30-40: High (85th-95th percentile)
        - 40+: Extreme (95th+ percentile)
        """
        if current_vix < 10:
            return 5.0
        elif current_vix < 15:
            return 10.0 + (current_vix - 10) * 4.0  # 10-30th percentile
        elif current_vix < 20:
            return 30.0 + (current_vix - 15) * 6.0  # 30-60th percentile
        elif current_vix < 30:
            return 60.0 + (current_vix - 20) * 2.5  # 60-85th percentile
        elif current_vix < 40:
            return 85.0 + (current_vix - 30) * 1.0  # 85-95th percentile
        else:
            return min(95.0 + (current_vix - 40) * 0.5, 99.0)  # 95-99th percentile

    def _determine_vix_trend(self, market_regime: MarketRegime) -> str:
        """Determine VIX trend based on market stress level and regime."""
        stress_level = market_regime.market_stress_level
        regime_type = market_regime.regime_type

        # High stress or volatile regime suggests rising VIX
        if stress_level == "high" or regime_type == "volatile":
            return "rising"
        # Low stress and bull market suggests falling VIX
        elif stress_level == "low" and regime_type == "bull":
            return "falling"
        # Otherwise stable
        else:
            return "stable"

    def _classify_volatility_regime(self, vix_level: float) -> str:
        """Classify volatility regime based on VIX level."""
        if vix_level < 15:
            return "low"
        elif vix_level < 20:
            return "normal"
        elif vix_level < 30:
            return "elevated"
        else:
            return "extreme"

    def _estimate_interest_rate(self, market_regime: MarketRegime) -> float:
        """
        Estimate current interest rate based on trend.

        This is a simplified estimation. In production, this would come from
        actual Fed funds rate or similar data source.
        """
        trend = market_regime.interest_rate_trend

        # Rough estimates based on 2024-2025 environment
        if trend == "rising":
            return 5.5  # Higher end of recent range
        elif trend == "falling":
            return 4.5  # Lower end of recent range
        else:
            return 5.0  # Mid-range

    def _extract_gdp_growth(self, discovery_result: APlusDiscoveryResult) -> float | None:
        """
        Extract GDP growth rate from discovery result if available.

        Args:
            discovery_result: APlusDiscoveryResult that may contain GDP data

        Returns:
            GDP growth rate or None if unavailable

        """
        # GDP growth is not currently in the schema, return None
        # This can be enhanced when GDP data is added to discovery results
        return None

    def _extract_unemployment_rate(self, discovery_result: APlusDiscoveryResult) -> float | None:
        """
        Extract unemployment rate from discovery result if available.

        Args:
            discovery_result: APlusDiscoveryResult that may contain unemployment data

        Returns:
            Unemployment rate or None if unavailable

        """
        # Unemployment rate is not currently in the schema, return None
        # This can be enhanced when unemployment data is added to discovery results
        return None

    def _assess_risk_environment(
        self, market_regime: MarketRegime, vix_indicators: VIXIndicators, macro_indicators: MacroIndicators
    ) -> str:
        """
        Assess overall risk environment based on all indicators.

        Returns:
            Risk environment classification: favorable, neutral, or challenging

        """
        # Count risk factors
        risk_factors = 0

        # Market regime factors
        if market_regime.regime_type in ["bear", "volatile"]:
            risk_factors += 2
        elif market_regime.regime_type == "sideways":
            risk_factors += 1

        # VIX factors
        if vix_indicators.volatility_regime in ["elevated", "extreme"]:
            risk_factors += 2
        elif vix_indicators.volatility_regime == "normal":
            risk_factors += 1

        # Market stress
        if market_regime.market_stress_level == "high":
            risk_factors += 2
        elif market_regime.market_stress_level == "medium":
            risk_factors += 1

        # Macro factors
        if macro_indicators.inflation_rate > 4.0:
            risk_factors += 1
        if macro_indicators.interest_rate_trend == "rising":
            risk_factors += 1

        # Classify based on total risk factors
        if risk_factors <= 2:
            return "favorable"
        elif risk_factors <= 5:
            return "neutral"
        else:
            return "challenging"

    def _generate_allocation_implications(
        self,
        market_regime: MarketRegime,
        vix_indicators: VIXIndicators,
        macro_indicators: MacroIndicators,
        risk_environment: str,
    ) -> list[str]:
        """Generate allocation implications based on market context."""
        implications: list[str] = []

        # Regime-based implications
        if market_regime.regime_type == "bull":
            implications.append("Bull market supports growth-oriented allocations with higher equity exposure")
        elif market_regime.regime_type == "bear":
            implications.append("Bear market favors defensive positioning with increased cash and quality bonds")
        elif market_regime.regime_type == "sideways":
            implications.append("Sideways market suggests balanced allocation with focus on income generation")
        elif market_regime.regime_type == "volatile":
            implications.append("Volatile market requires reduced position sizes and increased diversification")

        # VIX-based implications
        if vix_indicators.volatility_regime == "extreme":
            implications.append("Extreme volatility warrants significant risk reduction and hedging strategies")
        elif vix_indicators.volatility_regime == "elevated":
            implications.append("Elevated volatility suggests cautious positioning with defensive tilts")
        elif vix_indicators.volatility_regime == "low":
            implications.append("Low volatility environment allows for tactical risk-taking in quality assets")

        # Interest rate implications
        if macro_indicators.interest_rate_trend == "rising":
            implications.append("Rising rates favor shorter duration bonds and value stocks over growth")
        elif macro_indicators.interest_rate_trend == "falling":
            implications.append("Falling rates support longer duration bonds and growth-oriented equities")

        # Inflation implications
        if macro_indicators.inflation_rate > 4.0:
            implications.append("High inflation favors real assets, commodities, and inflation-protected securities")
        elif macro_indicators.inflation_rate < 2.0:
            implications.append("Low inflation supports traditional fixed income and growth equities")

        # Overall risk environment
        if risk_environment == "challenging":
            implications.append("Challenging environment requires conservative positioning and capital preservation focus")
        elif risk_environment == "favorable":
            implications.append("Favorable environment supports opportunistic positioning in quality growth assets")

        return implications

    def _create_conservative_summary(self) -> MarketContextSummary:
        """Create conservative market context summary when data is incomplete."""
        from datetime import datetime

        self.logger.warning("Creating conservative market context summary due to missing data")

        # Conservative assumptions
        conservative_regime = MarketRegime(
            regime_type="sideways",
            vix_level=20.0,  # Neutral VIX
            inflation_rate=3.0,  # Moderate inflation
            interest_rate_trend="stable",
            market_stress_level="medium",
            assessment_date=datetime.now(),
        )

        conservative_vix = VIXIndicators(
            current_vix=20.0,
            vix_percentile=50.0,
            vix_trend="stable",
            volatility_regime="normal",
        )

        conservative_macro = MacroIndicators(
            inflation_rate=3.0,
            interest_rate=5.0,
            interest_rate_trend="stable",
            gdp_growth=None,
            unemployment_rate=None,
        )

        return MarketContextSummary(
            market_regime=conservative_regime,
            vix_indicators=conservative_vix,
            macro_indicators=conservative_macro,
            risk_environment="neutral",
            allocation_implications=[
                "Using conservative assumptions due to incomplete market data",
                "Balanced allocation recommended with focus on quality and diversification",
                "Monitor market conditions closely for tactical adjustments",
            ],
        )
