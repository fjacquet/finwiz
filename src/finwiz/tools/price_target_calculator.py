"""
Price Target Calculator - Calculate actionable buy/sell price targets for holdings.

This module calculates price targets by:
- Computing fair value estimates (DCF for stocks, NAV for ETFs)
- Detecting technical support/resistance levels
- Generating buy/sell/stop-loss targets
- Supporting multi-currency with FX risk notes
- Providing data source citations and confidence scoring
"""

from datetime import datetime

from pydantic import BaseModel, Field

from finwiz.schemas.portfolio_review import AssetClass, PriceTargets
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PriceHistory(BaseModel):
    """Price history data for technical analysis."""

    prices: list[float] = Field(default_factory=list)
    dates: list[datetime] = Field(default_factory=list)
    currency: str = "USD"


class FundamentalData(BaseModel):
    """Fundamental data for fair value calculation."""

    # Stock fundamentals
    earnings_per_share: float | None = None
    pe_ratio: float | None = None
    book_value_per_share: float | None = None
    free_cash_flow: float | None = None
    growth_rate: float | None = None

    # ETF fundamentals
    nav: float | None = None
    expense_ratio: float | None = None
    tracking_error: float | None = None

    # Crypto fundamentals
    market_cap: float | None = None
    volume_24h: float | None = None
    volatility: float | None = None


class PriceTargetCalculator:
    """Calculate actionable buy/sell price targets for holdings."""

    def __init__(self) -> None:
        """Initialize the price target calculator."""
        self.logger = logger

    def calculate_targets(
        self,
        ticker: str,
        asset_class: AssetClass,
        current_price: float,
        currency: str,
        price_history: PriceHistory | None = None,
        fundamental_data: FundamentalData | None = None,
        decision: str = "KEEP",
    ) -> PriceTargets:
        """
        Calculate buy/sell/stop-loss price targets.

        Args:
            ticker: Ticker symbol
            asset_class: Asset class (stock/etf/crypto)
            current_price: Current market price
            currency: Currency denomination
            price_history: Historical price data for technical analysis
            fundamental_data: Fundamental data for fair value calculation
            decision: Current recommendation (KEEP/SELL/BUY)

        Returns:
            PriceTargets with specific levels and rationale

        """
        self.logger.info(
            "Calculating price targets",
            extra={
                "ticker": ticker,
                "asset_class": asset_class,
                "current_price": current_price,
                "decision": decision,
            },
        )

        # Calculate fair value estimate
        fair_value = self._calculate_fair_value(
            asset_class=asset_class,
            current_price=current_price,
            fundamental_data=fundamental_data,
        )

        # Calculate technical levels
        support_levels, resistance_levels = self._calculate_technical_levels(
            current_price=current_price,
            price_history=price_history,
        )

        # Generate buy/sell targets based on decision
        if decision == "KEEP":
            buy_primary, buy_secondary, buy_rationale = self._calculate_buy_targets(
                current_price=current_price,
                fair_value=fair_value,
                support_levels=support_levels,
                asset_class=asset_class,
            )
            sell_primary, sell_secondary, stop_loss, sell_rationale = self._calculate_sell_targets(
                current_price=current_price,
                fair_value=fair_value,
                resistance_levels=resistance_levels,
                asset_class=asset_class,
                is_keep=True,
            )
        elif decision == "SELL":
            buy_primary, buy_secondary, buy_rationale = None, None, "Not recommended - position should be exited"
            sell_primary, sell_secondary, stop_loss, sell_rationale = self._calculate_sell_targets(
                current_price=current_price,
                fair_value=fair_value,
                resistance_levels=resistance_levels,
                asset_class=asset_class,
                is_keep=False,
            )
        else:  # BUY
            buy_primary, buy_secondary, buy_rationale = self._calculate_buy_targets(
                current_price=current_price,
                fair_value=fair_value,
                support_levels=support_levels,
                asset_class=asset_class,
                is_new_position=True,
            )
            sell_primary, sell_secondary, stop_loss, sell_rationale = self._calculate_sell_targets(
                current_price=current_price,
                fair_value=fair_value,
                resistance_levels=resistance_levels,
                asset_class=asset_class,
                is_keep=False,
            )

        # Determine calculation method and confidence
        calculation_method = self._get_calculation_method(
            asset_class=asset_class,
            has_fundamental=fundamental_data is not None,
            has_technical=price_history is not None,
        )

        confidence = self._calculate_confidence(
            has_fundamental=fundamental_data is not None,
            has_technical=price_history is not None,
            fair_value=fair_value,
            current_price=current_price,
        )

        # Data sources
        data_sources = self._get_data_sources(asset_class=asset_class)

        return PriceTargets(
            current_price=current_price,
            currency=currency,
            fair_value_estimate=fair_value,
            buy_target_primary=buy_primary,
            buy_target_secondary=buy_secondary,
            buy_rationale=buy_rationale,
            sell_target_primary=sell_primary,
            sell_target_secondary=sell_secondary,
            stop_loss_level=stop_loss,
            sell_rationale=sell_rationale,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            calculation_method=calculation_method,
            confidence_level=confidence,
            data_as_of=datetime.now(),
            data_sources=data_sources,
        )

    def _calculate_fair_value(
        self,
        asset_class: AssetClass,
        current_price: float,
        fundamental_data: FundamentalData | None,
    ) -> float | None:
        """
        Calculate fair value estimate.

        Args:
            asset_class: Asset class
            current_price: Current market price
            fundamental_data: Fundamental data

        Returns:
            Fair value estimate or None if cannot calculate

        """
        if not fundamental_data:
            return None

        if asset_class == "stock":
            return self._calculate_stock_fair_value(current_price, fundamental_data)
        elif asset_class == "etf":
            return self._calculate_etf_fair_value(current_price, fundamental_data)
        elif asset_class == "crypto":
            # Crypto fair value is harder to determine - use technical analysis primarily
            return None

        return None

    def _calculate_stock_fair_value(
        self,
        current_price: float,
        fundamental_data: FundamentalData,
    ) -> float | None:
        """Calculate fair value for stocks using multiple methods."""
        fair_values = []

        # Method 1: P/E based valuation
        if fundamental_data.earnings_per_share and fundamental_data.pe_ratio:
            # Use industry average P/E (assume 15-20 for mature companies)
            target_pe = 17.5
            pe_fair_value = fundamental_data.earnings_per_share * target_pe
            fair_values.append(pe_fair_value)

        # Method 2: Book value based
        if fundamental_data.book_value_per_share:
            # Assume 1.5x book value for quality companies
            book_fair_value = fundamental_data.book_value_per_share * 1.5
            fair_values.append(book_fair_value)

        # Method 3: DCF approximation
        if fundamental_data.free_cash_flow and fundamental_data.growth_rate:
            # Simplified DCF: FCF * (1 + growth) / (discount_rate - growth)
            discount_rate = 0.10  # 10% discount rate
            if discount_rate > fundamental_data.growth_rate:
                dcf_value = (
                    fundamental_data.free_cash_flow
                    * (1 + fundamental_data.growth_rate)
                    / (discount_rate - fundamental_data.growth_rate)
                )
                fair_values.append(dcf_value)

        # Return average of available methods
        if fair_values:
            return sum(fair_values) / len(fair_values)

        # Fallback: assume current price is close to fair value
        return current_price

    def _calculate_etf_fair_value(
        self,
        current_price: float,
        fundamental_data: FundamentalData,
    ) -> float | None:
        """Calculate fair value for ETFs based on NAV."""
        if fundamental_data.nav:
            # ETF fair value is NAV, adjusted for tracking error
            if fundamental_data.tracking_error:
                # Adjust for tracking error (negative impact)
                adjustment = 1 - (fundamental_data.tracking_error / 100)
                return fundamental_data.nav * adjustment
            return fundamental_data.nav

        # Fallback: current price is close to NAV for most ETFs
        return current_price

    def _calculate_technical_levels(
        self,
        current_price: float,
        price_history: PriceHistory | None,
    ) -> tuple[list[float], list[float]]:
        """
        Calculate technical support and resistance levels.

        Args:
            current_price: Current market price
            price_history: Historical price data

        Returns:
            Tuple of (support_levels, resistance_levels)

        """
        if not price_history or not price_history.prices:
            # Use simple percentage-based levels if no history
            support_levels = [
                round(current_price * 0.95, 2),  # 5% below
                round(current_price * 0.90, 2),  # 10% below
            ]
            resistance_levels = [
                round(current_price * 1.05, 2),  # 5% above
                round(current_price * 1.10, 2),  # 10% above
            ]
            return support_levels, resistance_levels

        prices = price_history.prices

        # Find recent lows (support) and highs (resistance)
        support_levels = []
        resistance_levels = []

        # Method 1: Recent swing lows/highs
        if len(prices) >= 20:
            recent_prices = prices[-20:]
            recent_low = min(recent_prices)
            recent_high = max(recent_prices)

            if recent_low < current_price:
                support_levels.append(round(recent_low, 2))
            if recent_high > current_price:
                resistance_levels.append(round(recent_high, 2))

        # Method 2: Moving average levels
        if len(prices) >= 50:
            ma_50 = sum(prices[-50:]) / 50
            if ma_50 < current_price:
                support_levels.append(round(ma_50, 2))
            elif ma_50 > current_price:
                resistance_levels.append(round(ma_50, 2))

        # Method 3: Psychological levels (round numbers)
        # Find nearest round numbers
        magnitude = 10 ** (len(str(int(current_price))) - 1)
        lower_round = int(current_price / magnitude) * magnitude
        upper_round = lower_round + magnitude

        if lower_round < current_price and lower_round not in support_levels:
            support_levels.append(float(lower_round))
        if upper_round > current_price and upper_round not in resistance_levels:
            resistance_levels.append(float(upper_round))

        # Sort and limit to top 3 each
        support_levels = sorted(set(support_levels), reverse=True)[:3]
        resistance_levels = sorted(set(resistance_levels))[:3]

        return support_levels, resistance_levels

    def _calculate_buy_targets(
        self,
        current_price: float,
        fair_value: float | None,
        support_levels: list[float],
        asset_class: AssetClass,
        is_new_position: bool = False,
    ) -> tuple[float | None, float | None, str]:
        """
        Calculate buy targets for KEEP or BUY recommendations.

        Returns:
            Tuple of (primary_target, secondary_target, rationale)

        """
        if is_new_position:
            # For new positions, buy at current price or better
            primary = current_price
            secondary = support_levels[0] if support_levels else round(current_price * 0.95, 2)
            rationale = (
                f"Initier position au prix actuel de {current_price:.2f} ou mieux. "
                f"Niveau d'accumulation secondaire à {secondary:.2f} si le prix baisse."
            )
        else:
            # For existing positions (KEEP), buy on dips
            if fair_value and fair_value > current_price:
                # Undervalued - buy on any dip
                primary = support_levels[0] if support_levels else round(current_price * 0.95, 2)
                secondary = support_levels[1] if len(support_levels) > 1 else round(current_price * 0.90, 2)
                discount_pct = ((fair_value - current_price) / fair_value) * 100
                rationale = (
                    f"Position sous-évaluée de {discount_pct:.1f}%. "
                    f"Renforcer à {primary:.2f} (support principal) "
                    f"ou {secondary:.2f} (support secondaire)."
                )
            else:
                # Fairly valued or overvalued - wait for significant dip
                primary = support_levels[0] if support_levels else round(current_price * 0.90, 2)
                secondary = support_levels[1] if len(support_levels) > 1 else round(current_price * 0.85, 2)
                rationale = (
                    f"Position correctement valorisée. "
                    f"Renforcer uniquement sur correction significative à {primary:.2f} "
                    f"ou {secondary:.2f}."
                )

        return primary, secondary, rationale

    def _calculate_sell_targets(
        self,
        current_price: float,
        fair_value: float | None,
        resistance_levels: list[float],
        asset_class: AssetClass,
        is_keep: bool,
    ) -> tuple[float | None, float | None, float | None, str]:
        """
        Calculate sell targets and stop-loss.

        Returns:
            Tuple of (primary_target, secondary_target, stop_loss, rationale)

        """
        # Calculate stop-loss based on asset class volatility
        if asset_class == "crypto":
            stop_loss_pct = 0.20  # 20% for crypto (high volatility)
        elif asset_class == "stock":
            stop_loss_pct = 0.15  # 15% for stocks
        else:  # ETF
            stop_loss_pct = 0.10  # 10% for ETFs (lower volatility)

        stop_loss = round(current_price * (1 - stop_loss_pct), 2)

        if not is_keep:
            # SELL recommendation - exit position
            primary = current_price
            secondary = resistance_levels[0] if resistance_levels else round(current_price * 1.05, 2)
            rationale = (
                f"Sortir de la position au prix actuel de {current_price:.2f} ou mieux. "
                f"Si le prix monte à {secondary:.2f}, vendre progressivement. "
                f"Stop-loss strict à {stop_loss:.2f}."
            )
        else:
            # KEEP recommendation - take profits at resistance
            if fair_value and current_price > fair_value:
                # Overvalued - consider taking profits
                overvalue_pct = ((current_price - fair_value) / fair_value) * 100
                primary = resistance_levels[0] if resistance_levels else round(current_price * 1.10, 2)
                secondary = resistance_levels[1] if len(resistance_levels) > 1 else round(current_price * 1.20, 2)
                rationale = (
                    f"Position surévaluée de {overvalue_pct:.1f}%. "
                    f"Prendre des bénéfices partiels à {primary:.2f} (résistance) "
                    f"ou {secondary:.2f} (résistance forte). "
                    f"Stop-loss de protection à {stop_loss:.2f}."
                )
            else:
                # Fairly valued or undervalued - hold with trailing stop
                primary = resistance_levels[0] if resistance_levels else round(current_price * 1.15, 2)
                secondary = resistance_levels[1] if len(resistance_levels) > 1 else round(current_price * 1.30, 2)
                rationale = (
                    f"Conserver la position. "
                    f"Objectif de prise de bénéfices à {primary:.2f} "
                    f"et {secondary:.2f} en cas de forte hausse. "
                    f"Stop-loss de protection à {stop_loss:.2f}."
                )

        return primary, secondary, stop_loss, rationale

    def _get_calculation_method(
        self,
        asset_class: AssetClass,
        has_fundamental: bool,
        has_technical: bool,
    ) -> str:
        """Get description of calculation method used."""
        methods = []

        if has_fundamental:
            if asset_class == "stock":
                methods.append("DCF/P-E/Valeur comptable")
            elif asset_class == "etf":
                methods.append("Valeur liquidative (NAV)")

        if has_technical:
            methods.append("Analyse technique (supports/résistances)")

        if not methods:
            methods.append("Niveaux basés sur pourcentages")

        return " + ".join(methods)

    def _calculate_confidence(
        self,
        has_fundamental: bool,
        has_technical: bool,
        fair_value: float | None,
        current_price: float,
    ) -> float:
        """Calculate confidence level in price targets."""
        confidence = 0.5  # Base confidence

        # Increase confidence if we have fundamental data
        if has_fundamental and fair_value:
            confidence += 0.2

        # Increase confidence if we have technical data
        if has_technical:
            confidence += 0.2

        # Increase confidence if fair value is significantly different from current price
        if fair_value and abs(fair_value - current_price) / current_price > 0.10:
            confidence += 0.1

        return min(confidence, 1.0)

    def _get_data_sources(self, asset_class: AssetClass) -> list[str]:
        """Get list of data sources used."""
        sources = ["Yahoo Finance"]

        if asset_class == "stock":
            sources.append("SEC EDGAR")
        elif asset_class == "etf":
            sources.append("ETF Provider")
        elif asset_class == "crypto":
            sources.append("CoinMarketCap")

        return sources
