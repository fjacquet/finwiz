"""
Portfolio configuration validation utilities.

This module contains validation logic for portfolio configurations,
including weight validation, consistency checks, and error reporting.
"""

from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class PortfolioConfigurationValidator:
    """Validator for portfolio configurations with comprehensive validation rules."""

    def __init__(self) -> None:
        """Initialize the portfolio configuration validator."""
        self.logger = logger

    def validate_configuration(self, config: PortfolioConfiguration) -> list[str]:
        """
        Validate portfolio configuration and return list of errors.

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages

        """
        errors = []

        try:
            # Check target weights sum
            errors.extend(self._validate_target_weights(config))

            # Check holdings consistency
            errors.extend(self._validate_holdings_consistency(config))

            # Check tolerance bands
            errors.extend(self._validate_tolerance_bands(config))

            # Check for duplicate holdings
            errors.extend(self._validate_duplicate_holdings(config))

            # Check minimum trade size
            errors.extend(self._validate_trade_parameters(config))

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def _validate_target_weights(self, config: PortfolioConfiguration) -> list[str]:
        """Validate target weights for the portfolio."""
        errors = []

        # Check target weights sum
        total_weight = sum(config.target_weights.values())
        if total_weight > 1.01:
            errors.append(f"Target weights sum to {total_weight:.1%}, exceeds 100%")
        elif total_weight < 0.95:
            errors.append(f"Target weights sum to {total_weight:.1%}, significantly below 100%")

        # Check for zero or negative weights
        for symbol, weight in config.target_weights.items():
            if weight <= 0:
                errors.append(f"Target weight for {symbol} is {weight}, must be positive")
            elif weight > 0.5:
                errors.append(f"Target weight for {symbol} is {weight:.1%}, exceeds 50% (concentration risk)")

        return errors

    def _validate_holdings_consistency(self, config: PortfolioConfiguration) -> list[str]:
        """Validate consistency between holdings and target weights."""
        errors = []

        holding_symbols = {holding.symbol for holding in config.holdings}
        target_symbols = set(config.target_weights.keys())

        missing_targets = holding_symbols - target_symbols
        if missing_targets:
            errors.append(f"Missing target weights for holdings: {', '.join(missing_targets)}")

        extra_targets = target_symbols - holding_symbols
        if extra_targets:
            errors.append(f"Target weights for non-held symbols: {', '.join(extra_targets)}")

        return errors

    def _validate_tolerance_bands(self, config: PortfolioConfiguration) -> list[str]:
        """Validate tolerance bands configuration."""
        errors = []

        target_symbols = set(config.target_weights.keys())

        for symbol, tolerance in config.tolerance_bands.items():
            if symbol not in target_symbols:
                errors.append(f"Tolerance band for non-existent symbol: {symbol}")
            elif tolerance <= 0 or tolerance > 0.5:
                errors.append(f"Invalid tolerance for {symbol}: {tolerance:.1%}")

        return errors

    def _validate_duplicate_holdings(self, config: PortfolioConfiguration) -> list[str]:
        """Validate that there are no duplicate holdings."""
        errors = []

        symbols_seen = set()
        for holding in config.holdings:
            if holding.symbol in symbols_seen:
                errors.append(f"Duplicate holding for symbol: {holding.symbol}")
            symbols_seen.add(holding.symbol)

        return errors

    def _validate_trade_parameters(self, config: PortfolioConfiguration) -> list[str]:
        """Validate trading parameters."""
        errors = []

        # Check minimum trade size
        if config.min_trade_size <= 0:
            errors.append(f"Minimum trade size must be positive: {config.min_trade_size}")

        # Check transaction cost rate
        if config.transaction_cost_rate < 0 or config.transaction_cost_rate > 0.1:
            errors.append(f"Transaction cost rate should be between 0% and 10%: {config.transaction_cost_rate:.1%}")

        return errors

    def validate_weights_sum_to_one(self, weights: dict[str, float], tolerance: float = 0.01) -> bool:
        """
        Check if weights sum to approximately 1.0.

        Args:
            weights: Dictionary of symbol to weight mappings
            tolerance: Acceptable deviation from 1.0

        Returns:
            True if weights sum is within tolerance of 1.0

        """
        total = sum(weights.values())
        return abs(total - 1.0) <= tolerance

    def validate_weight_bounds(self, weights: dict[str, float], min_weight: float = 0.0, max_weight: float = 1.0) -> list[str]:
        """
        Validate that all weights are within specified bounds.

        Args:
            weights: Dictionary of symbol to weight mappings
            min_weight: Minimum allowed weight
            max_weight: Maximum allowed weight

        Returns:
            List of validation errors

        """
        errors = []

        for symbol, weight in weights.items():
            if weight < min_weight:
                errors.append(f"Weight for {symbol} ({weight:.1%}) below minimum ({min_weight:.1%})")
            elif weight > max_weight:
                errors.append(f"Weight for {symbol} ({weight:.1%}) above maximum ({max_weight:.1%})")

        return errors

    def validate_diversification(self, weights: dict[str, float], max_single_weight: float = 0.3) -> list[str]:
        """
        Validate portfolio diversification by checking concentration limits.

        Args:
            weights: Dictionary of symbol to weight mappings
            max_single_weight: Maximum allowed weight for any single position

        Returns:
            List of validation warnings

        """
        warnings = []

        for symbol, weight in weights.items():
            if weight > max_single_weight:
                warnings.append(f"High concentration in {symbol}: {weight:.1%} (limit: {max_single_weight:.1%})")

        # Check if portfolio is too concentrated in top positions
        sorted_weights = sorted(weights.values(), reverse=True)
        if len(sorted_weights) >= 3:
            top_3_concentration = sum(sorted_weights[:3])
            if top_3_concentration > 0.7:
                warnings.append(f"Top 3 positions represent {top_3_concentration:.1%} of portfolio (high concentration)")

        return warnings

    def validate_rebalancing_feasibility(self, config: PortfolioConfiguration) -> list[str]:
        """
        Validate that rebalancing is feasible given the configuration.

        Args:
            config: Portfolio configuration to validate

        Returns:
            List of validation errors

        """
        errors = []

        # Check if available capital is sufficient for minimum trades
        if config.available_capital < config.min_trade_size:
            errors.append(f"Available capital ({config.available_capital}) less than minimum trade size ({config.min_trade_size})")

        # Check if tolerance bands are reasonable relative to target weights
        for symbol, target_weight in config.target_weights.items():
            tolerance = config.tolerance_bands.get(symbol, config.global_tolerance)

            # Calculate absolute tolerance in dollar terms
            target_value = target_weight * (config.available_capital + sum(h.current_value for h in config.holdings))
            tolerance_value = tolerance * target_value

            if tolerance_value < config.min_trade_size:
                errors.append(
                    f"Tolerance band for {symbol} ({tolerance:.1%}) results in trades smaller than minimum "
                    f"({tolerance_value:.2f} < {config.min_trade_size})"
                )

        return errors
