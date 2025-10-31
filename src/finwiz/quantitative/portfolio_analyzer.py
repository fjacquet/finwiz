"""
Portfolio analysis engine for FinWiz rebalancing system.

This module provides comprehensive portfolio analysis capabilities including
current weighting calculations, deviation analysis, risk metrics, and
rebalancing need identification.
"""

import logging
from typing import Any

from finwiz.schemas.portfolio_rebalancing import (
    Holding,
    PortfolioAnalysis,
    PortfolioMetrics,
    PriceData,
    RebalancingNeed,
    TradeAction,
)

logger = logging.getLogger(__name__)


class PortfolioAnalysisError(Exception):
    """Base exception for portfolio analysis errors."""

    pass


class InsufficientDataError(PortfolioAnalysisError):
    """Raised when insufficient data is available for analysis."""

    def __init__(self, missing_data: list[str]) -> None:
        """Initialize with list of missing data items."""
        super().__init__(f"Insufficient data for analysis: {', '.join(missing_data)}")
        self.missing_data = missing_data


class PortfolioAnalyzer:
    """
    Analyzes portfolio composition and calculates current weightings.

    Provides comprehensive analysis of portfolio holdings including current weightings,
    deviations from targets, risk metrics, and rebalancing recommendations.
    """

    def __init__(self) -> None:
        """Initialize the portfolio analyzer."""
        logger.info("Portfolio analyzer initialized")

    def calculate_current_weightings(self, holdings: list[Holding], prices: dict[str, float]) -> dict[str, float]:
        """
        Calculate current portfolio weightings based on holdings and prices.

        Args:
            holdings: List of portfolio holdings
            prices: Dictionary mapping symbols to current prices

        Returns:
            Dictionary mapping symbols to current weights (0.0 to 1.0)

        Raises:
            InsufficientDataError: If price data is missing for any holdings
            PortfolioAnalysisError: If calculation fails

        """
        logger.debug(f"Calculating weightings for {len(holdings)} holdings")

        if not holdings:
            raise PortfolioAnalysisError("Cannot calculate weightings for empty portfolio")

        # Check for missing price data
        missing_prices = []
        for holding in holdings:
            if holding.symbol not in prices:
                missing_prices.append(holding.symbol)

        if missing_prices:
            raise InsufficientDataError([f"price for {symbol}" for symbol in missing_prices])

        try:
            # Calculate market values for each position
            position_values = {}
            total_value = 0.0

            for holding in holdings:
                price = prices[holding.symbol]
                if price <= 0:
                    raise PortfolioAnalysisError(f"Invalid price for {holding.symbol}: {price}")

                market_value = holding.shares * price
                position_values[holding.symbol] = market_value
                total_value += market_value

            if total_value <= 0:
                raise PortfolioAnalysisError("Total portfolio value must be positive")

            # Calculate weightings
            weightings = {}
            for symbol, value in position_values.items():
                weightings[symbol] = value / total_value

            logger.debug(f"Calculated weightings for portfolio value: ${total_value:,.2f}")
            return weightings

        except Exception as e:
            if isinstance(e, (PortfolioAnalysisError, InsufficientDataError)):
                raise
            logger.error(f"Error calculating weightings: {e}")
            raise PortfolioAnalysisError(f"Failed to calculate weightings: {e}") from e

    def identify_rebalancing_needs(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
        tolerance_bands: dict[str, float],
        global_tolerance: float = 0.05,
    ) -> list[RebalancingNeed]:
        """
        Identify positions requiring rebalancing based on tolerance bands.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            tolerance_bands: Position-specific tolerance bands
            global_tolerance: Default tolerance for positions without specific bands

        Returns:
            List of RebalancingNeed objects for positions requiring attention

        Raises:
            PortfolioAnalysisError: If analysis fails

        """
        logger.debug("Identifying rebalancing needs")

        if not current_weights or not target_weights:
            raise PortfolioAnalysisError("Current and target weights are required")

        try:
            rebalancing_needs = []

            # Check each position in target weights
            for symbol, target_weight in target_weights.items():
                current_weight = current_weights.get(symbol, 0.0)
                deviation = current_weight - target_weight

                # Get tolerance band for this position
                tolerance = tolerance_bands.get(symbol, global_tolerance)

                # Check if deviation exceeds tolerance
                exceeds_tolerance = abs(deviation) > tolerance

                # Calculate urgency score (0.0 to 1.0)
                urgency_score = min(abs(deviation) / tolerance, 1.0) if tolerance > 0 else 1.0

                # Determine recommended action
                if not exceeds_tolerance:
                    recommended_action = TradeAction.HOLD
                elif deviation > 0:
                    # Overweight - recommend sell
                    recommended_action = TradeAction.SELL
                else:
                    # Underweight - recommend buy
                    recommended_action = TradeAction.BUY

                rebalancing_need = RebalancingNeed(
                    symbol=symbol,
                    current_weight=current_weight,
                    target_weight=target_weight,
                    deviation=deviation,
                    tolerance_band=tolerance,
                    exceeds_tolerance=exceeds_tolerance,
                    urgency_score=urgency_score,
                    recommended_action=recommended_action,
                )

                rebalancing_needs.append(rebalancing_need)

            # Sort by urgency score (highest first)
            rebalancing_needs.sort(key=lambda x: x.urgency_score, reverse=True)

            positions_needing_action = sum(1 for need in rebalancing_needs if need.exceeds_tolerance)
            logger.debug(f"Identified {positions_needing_action} positions needing rebalancing")

            return rebalancing_needs

        except Exception as e:
            logger.error(f"Error identifying rebalancing needs: {e}")
            raise PortfolioAnalysisError(f"Failed to identify rebalancing needs: {e}") from e

    def calculate_portfolio_metrics(self, holdings: list[Holding], prices: dict[str, float]) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics.

        Args:
            holdings: List of portfolio holdings
            prices: Dictionary mapping symbols to current prices

        Returns:
            PortfolioMetrics object with calculated metrics

        Raises:
            InsufficientDataError: If required data is missing
            PortfolioAnalysisError: If calculation fails

        """
        logger.debug("Calculating portfolio metrics")

        if not holdings:
            raise PortfolioAnalysisError("Cannot calculate metrics for empty portfolio")

        try:
            # Calculate basic metrics
            weightings = self.calculate_current_weightings(holdings, prices)
            total_value = sum(holding.shares * prices[holding.symbol] for holding in holdings)

            # Number of positions
            number_of_positions = len(holdings)

            # Largest position weight
            largest_position_weight = max(weightings.values()) if weightings else 0.0

            # Concentration risk score (0-10 scale)
            concentration_risk_score = self._calculate_concentration_risk(weightings)

            # Diversification ratio (Herfindahl-Hirschman Index based)
            diversification_ratio = self._calculate_diversification_ratio(weightings)

            # Effective number of positions
            effective_number_of_positions = self._calculate_effective_positions(weightings)

            # Calculate turnover if rebalanced (placeholder - would need target weights)
            turnover_if_rebalanced = 0.0  # This would be calculated in rebalancing context

            # Cash weight (assume no cash for now)
            cash_weight = 0.0

            metrics = PortfolioMetrics(
                total_value=total_value,
                number_of_positions=number_of_positions,
                largest_position_weight=largest_position_weight,
                concentration_risk_score=concentration_risk_score,
                diversification_ratio=diversification_ratio,
                effective_number_of_positions=effective_number_of_positions,
                turnover_if_rebalanced=turnover_if_rebalanced,
                cash_weight=cash_weight,
            )

            logger.debug(f"Calculated metrics for portfolio: ${total_value:,.2f}, {number_of_positions} positions")
            return metrics

        except Exception as e:
            if isinstance(e, (PortfolioAnalysisError, InsufficientDataError)):
                raise
            logger.error(f"Error calculating portfolio metrics: {e}")
            raise PortfolioAnalysisError(f"Failed to calculate portfolio metrics: {e}") from e

    def analyze_current_portfolio(self, holdings: list[Holding], prices: dict[str, PriceData], target_weights: dict[str, float] | None = None) -> PortfolioAnalysis:
        """
        Perform comprehensive analysis of current portfolio.

        Args:
            holdings: List of portfolio holdings
            prices: Dictionary mapping symbols to PriceData objects
            target_weights: Optional target weights for deviation calculation

        Returns:
            PortfolioAnalysis object with complete analysis

        Raises:
            InsufficientDataError: If required data is missing
            PortfolioAnalysisError: If analysis fails

        """
        logger.info(f"Analyzing portfolio with {len(holdings)} holdings")

        try:
            # Convert PriceData to simple price dict
            price_dict = {symbol: price_data.price for symbol, price_data in prices.items()}

            # Calculate current weightings
            weightings = self.calculate_current_weightings(holdings, price_dict)

            # Calculate total value
            total_value = sum(holding.shares * price_dict[holding.symbol] for holding in holdings)

            # Calculate deviations from target (if provided)
            deviations_from_target = {}
            positions_needing_rebalancing = []

            if target_weights:
                for symbol in weightings:
                    target = target_weights.get(symbol, 0.0)
                    deviation = weightings[symbol] - target
                    deviations_from_target[symbol] = deviation

                    # Simple threshold for identifying positions needing rebalancing
                    if abs(deviation) > 0.05:  # 5% threshold
                        positions_needing_rebalancing.append(symbol)

            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(weightings)

            analysis = PortfolioAnalysis(
                total_value=total_value,
                weightings=weightings,
                deviations_from_target=deviations_from_target,
                positions_needing_rebalancing=positions_needing_rebalancing,
                risk_metrics=risk_metrics,
            )

            logger.info(f"Portfolio analysis complete: ${total_value:,.2f} total value")
            return analysis

        except Exception as e:
            if isinstance(e, (PortfolioAnalysisError, InsufficientDataError)):
                raise
            logger.error(f"Error analyzing portfolio: {e}")
            raise PortfolioAnalysisError(f"Failed to analyze portfolio: {e}") from e

    def compare_allocations(self, current_weights: dict[str, float], target_weights: dict[str, float]) -> dict[str, dict[str, Any]]:
        """
        Create detailed comparison between current and target allocations.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights

        Returns:
            Dictionary with detailed comparison data for each position

        """
        logger.debug("Comparing current vs target allocations")

        comparison = {}

        # Get all symbols from both current and target
        all_symbols = set(current_weights.keys()) | set(target_weights.keys())

        for symbol in all_symbols:
            current = current_weights.get(symbol, 0.0)
            target = target_weights.get(symbol, 0.0)
            deviation = current - target
            deviation_pct = (deviation / target * 100) if target > 0 else float("inf") if current > 0 else 0.0

            comparison[symbol] = {
                "current_weight": current,
                "target_weight": target,
                "absolute_deviation": deviation,
                "relative_deviation_pct": deviation_pct,
                "status": self._get_position_status(deviation, target),
                "priority": abs(deviation),  # Simple priority based on absolute deviation
            }

        logger.debug(f"Completed allocation comparison for {len(all_symbols)} positions")
        return comparison

    def _calculate_concentration_risk(self, weightings: dict[str, float]) -> float:
        """
        Calculate concentration risk score (0-10 scale).

        Higher scores indicate higher concentration risk.
        """
        if not weightings:
            return 0.0

        # Use Herfindahl-Hirschman Index as base
        hhi = sum(weight**2 for weight in weightings.values())

        # Convert to 0-10 scale (1.0 = maximum concentration, 0.0 = perfect diversification)
        # For a portfolio, HHI ranges from 1/n (equal weights) to 1.0 (single asset)
        n_positions = len(weightings)
        min_hhi = 1.0 / n_positions if n_positions > 0 else 1.0
        max_hhi = 1.0

        if max_hhi <= min_hhi:
            return 0.0

        # Normalize to 0-1 range, then scale to 0-10
        normalized_risk = (hhi - min_hhi) / (max_hhi - min_hhi)
        return min(normalized_risk * 10.0, 10.0)

    def _calculate_diversification_ratio(self, weightings: dict[str, float]) -> float:
        """
        Calculate diversification ratio (0-1 scale).

        Higher values indicate better diversification.
        """
        if not weightings:
            return 0.0

        n_positions = len(weightings)
        if n_positions <= 1:
            return 0.0

        # Use inverse of normalized HHI
        hhi = sum(weight**2 for weight in weightings.values())
        current_diversification = 1.0 / hhi if hhi > 0 else 0.0

        # Normalize to 0-1 scale
        return min(current_diversification / n_positions, 1.0)

    def _calculate_effective_positions(self, weightings: dict[str, float]) -> float:
        """
        Calculate effective number of positions.

        This is the reciprocal of the sum of squared weights.
        """
        if not weightings:
            return 0.0

        hhi = sum(weight**2 for weight in weightings.values())
        return 1.0 / hhi if hhi > 0 else 0.0

    def _calculate_risk_metrics(self, weightings: dict[str, float]) -> dict[str, float]:
        """Calculate various risk metrics for the portfolio."""
        return {
            "concentration_risk": self._calculate_concentration_risk(weightings),
            "diversification_ratio": self._calculate_diversification_ratio(weightings),
            "effective_positions": self._calculate_effective_positions(weightings),
            "largest_position": max(weightings.values()) if weightings else 0.0,
            "top_5_concentration": sum(sorted(weightings.values(), reverse=True)[:5]) if weightings else 0.0,
        }

    def _get_position_status(self, deviation: float, target_weight: float) -> str:
        """Get human-readable status for a position."""
        if abs(deviation) < 0.01:  # Within 1%
            return "On Target"
        elif deviation > 0:
            if deviation > 0.1:  # More than 10% over
                return "Significantly Overweight"
            elif deviation > 0.05:  # More than 5% over
                return "Overweight"
            else:
                return "Slightly Overweight"
        else:  # deviation < 0
            if abs(deviation) > 0.1:  # More than 10% under
                return "Significantly Underweight"
            elif abs(deviation) > 0.05:  # More than 5% under
                return "Underweight"
            else:
                return "Slightly Underweight"

    def calculate_rebalancing_impact(
        self,
        current_weights: dict[str, float],
        target_weights: dict[str, float],
        total_portfolio_value: float,
    ) -> dict[str, Any]:
        """
        Calculate the impact of rebalancing on portfolio composition.

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            total_portfolio_value: Total portfolio value

        Returns:
            Dictionary with rebalancing impact analysis

        """
        logger.debug("Calculating rebalancing impact")

        try:
            # Calculate required changes
            changes = {}
            total_turnover = 0.0
            positions_to_buy = []
            positions_to_sell = []

            for symbol in set(current_weights.keys()) | set(target_weights.keys()):
                current = current_weights.get(symbol, 0.0)
                target = target_weights.get(symbol, 0.0)
                weight_change = target - current
                dollar_change = weight_change * total_portfolio_value

                changes[symbol] = {
                    "weight_change": weight_change,
                    "dollar_change": dollar_change,
                    "action": "BUY" if weight_change > 0 else "SELL" if weight_change < 0 else "HOLD",
                }

                # Track turnover (sum of absolute changes)
                total_turnover += abs(weight_change)

                # Categorize positions
                if weight_change > 0.01:  # More than 1% increase
                    positions_to_buy.append(symbol)
                elif weight_change < -0.01:  # More than 1% decrease
                    positions_to_sell.append(symbol)

            # Calculate metrics
            turnover_percentage = (total_turnover / 2) * 100  # Divide by 2 to avoid double counting
            number_of_trades = len(positions_to_buy) + len(positions_to_sell)

            impact_analysis = {
                "total_turnover_percentage": turnover_percentage,
                "number_of_trades_required": number_of_trades,
                "positions_to_buy": positions_to_buy,
                "positions_to_sell": positions_to_sell,
                "position_changes": changes,
                "estimated_complexity": self._assess_rebalancing_complexity(number_of_trades, turnover_percentage),
            }

            logger.debug(f"Rebalancing impact: {turnover_percentage:.1f}% turnover, {number_of_trades} trades")
            return impact_analysis

        except Exception as e:
            logger.error(f"Error calculating rebalancing impact: {e}")
            raise PortfolioAnalysisError(f"Failed to calculate rebalancing impact: {e}") from e

    def _assess_rebalancing_complexity(self, number_of_trades: int, turnover_percentage: float) -> str:
        """Assess the complexity of the rebalancing operation."""
        if number_of_trades == 0:
            return "No Action Required"
        elif number_of_trades <= 2 and turnover_percentage <= 10:
            return "Simple"
        elif number_of_trades <= 5 and turnover_percentage <= 25:
            return "Moderate"
        elif number_of_trades <= 10 and turnover_percentage <= 50:
            return "Complex"
        else:
            return "Very Complex"
