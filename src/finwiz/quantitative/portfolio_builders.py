"""
Portfolio builders and template management.

This module contains portfolio building utilities, template management,
and system template definitions for common investment strategies.
"""

from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_rebalancing import Holding, RebalancingMethod
from finwiz.tools.logger import get_logger

# Import enums and models from the models module
from .portfolio_config_models import ConfigurationTemplate, StrategyTemplate

logger = get_logger(__name__)


class PortfolioBuilder:
    """Builder for creating portfolio configurations from templates and strategies."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize portfolio builder.

        Args:
            storage_path: Path to store template files

        """
        self.storage_path = storage_path
        self.templates_path = storage_path / "templates"
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def create_from_template(self, template: ConfigurationTemplate, holdings: list[Holding], name: str, description: str = "") -> dict[str, Any]:
        """
        Create a portfolio configuration from a template.

        Args:
            template: Template to use
            holdings: Portfolio holdings
            name: Configuration name
            description: Configuration description

        Returns:
            Dictionary with configuration parameters

        """
        try:
            # Extract symbols from holdings
            holding_symbols = {holding.symbol for holding in holdings}

            # Adjust template weights to match holdings
            adjusted_weights = self._adjust_template_weights(template.target_weights, holding_symbols)

            # Create configuration parameters
            config_params = {
                "name": name,
                "holdings": holdings,
                "target_weights": adjusted_weights,
                "description": description,
                "strategy_template": template.strategy_type,
                "global_tolerance": template.global_tolerance,
                "rebalancing_method": template.rebalancing_method,
            }

            # Update template usage count
            template.usage_count += 1

            self.logger.info(f"Created configuration from template {template.template_id}")
            return config_params

        except Exception as e:
            self.logger.error(f"Failed to create configuration from template {template.template_id}: {e}")
            raise

    def _adjust_template_weights(self, template_weights: dict[str, float], holding_symbols: set[str]) -> dict[str, float]:
        """
        Adjust template weights to match actual holdings.

        Args:
            template_weights: Original template weights
            holding_symbols: Set of symbols in holdings

        Returns:
            Adjusted weights dictionary

        """
        adjusted_weights = {}
        template_symbols = set(template_weights.keys())

        # Use template weights for matching symbols
        for symbol in holding_symbols:
            if symbol in template_symbols:
                adjusted_weights[symbol] = template_weights[symbol]
            else:
                # Equal weight for new symbols
                adjusted_weights[symbol] = 1.0 / len(holding_symbols)

        # Normalize weights to sum to 1.0
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

        return adjusted_weights

    def build_balanced_portfolio(self, holdings: list[Holding]) -> dict[str, float]:
        """
        Build a balanced portfolio with equal weights.

        Args:
            holdings: Portfolio holdings

        Returns:
            Equal weight allocation

        """
        if not holdings:
            return {}

        equal_weight = 1.0 / len(holdings)
        return {holding.symbol: equal_weight for holding in holdings}

    def build_market_cap_weighted_portfolio(self, holdings: list[Holding]) -> dict[str, float]:
        """
        Build a market cap weighted portfolio.

        Args:
            holdings: Portfolio holdings with market cap data

        Returns:
            Market cap weighted allocation

        """
        if not holdings:
            return {}

        # Calculate total market cap
        total_market_cap = sum(getattr(holding, "market_cap", holding.current_value) for holding in holdings)

        if total_market_cap <= 0:
            # Fallback to equal weights if no market cap data
            return self.build_balanced_portfolio(holdings)

        # Calculate weights based on market cap
        weights = {}
        for holding in holdings:
            market_cap = getattr(holding, "market_cap", holding.current_value)
            weights[holding.symbol] = market_cap / total_market_cap

        return weights

    def build_risk_parity_portfolio(self, holdings: list[Holding], risk_data: dict[str, float] | None = None) -> dict[str, float]:
        """
        Build a risk parity portfolio where each position contributes equally to portfolio risk.

        Args:
            holdings: Portfolio holdings
            risk_data: Dictionary of symbol to risk measure (volatility)

        Returns:
            Risk parity weighted allocation

        """
        if not holdings:
            return {}

        if not risk_data:
            # Fallback to equal weights if no risk data
            return self.build_balanced_portfolio(holdings)

        # Calculate inverse volatility weights
        inv_vol_weights = {}
        for holding in holdings:
            volatility = risk_data.get(holding.symbol, 0.15)  # Default 15% volatility
            if volatility > 0:
                inv_vol_weights[holding.symbol] = 1.0 / volatility
            else:
                inv_vol_weights[holding.symbol] = 1.0

        # Normalize to sum to 1.0
        total_inv_vol = sum(inv_vol_weights.values())
        if total_inv_vol > 0:
            return {symbol: weight / total_inv_vol for symbol, weight in inv_vol_weights.items()}

        return self.build_balanced_portfolio(holdings)


class SystemTemplateManager:
    """Manager for system-provided portfolio templates."""

    def __init__(self) -> None:
        """Initialize system template manager."""
        self.logger = logger

    def get_system_templates(self) -> list[ConfigurationTemplate]:
        """
        Get all system-provided configuration templates.

        Returns:
            List of system templates

        """
        return [
            self._create_balanced_template(),
            self._create_aggressive_growth_template(),
            self._create_conservative_template(),
            self._create_dividend_focused_template(),
            self._create_sector_rotation_template(),
            self._create_equal_weight_template(),
            self._create_market_cap_weighted_template(),
        ]

    def _create_balanced_template(self) -> ConfigurationTemplate:
        """Create balanced portfolio template."""
        return ConfigurationTemplate(
            template_id="balanced_portfolio",
            name="Balanced Portfolio",
            description="Balanced allocation between stocks and bonds with moderate risk",
            strategy_type=StrategyTemplate.BALANCED,
            target_weights={
                "VTI": 0.40,  # Total Stock Market
                "VTIAX": 0.20,  # International Stocks
                "BND": 0.30,  # Total Bond Market
                "VTEB": 0.10,  # Tax-Exempt Bonds
            },
            global_tolerance=0.05,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_aggressive_growth_template(self) -> ConfigurationTemplate:
        """Create aggressive growth portfolio template."""
        return ConfigurationTemplate(
            template_id="aggressive_growth",
            name="Aggressive Growth",
            description="High-growth allocation focused on equities with higher risk/reward",
            strategy_type=StrategyTemplate.AGGRESSIVE_GROWTH,
            target_weights={
                "VTI": 0.50,  # Total Stock Market
                "VTIAX": 0.25,  # International Stocks
                "VBR": 0.15,  # Small-Cap Value
                "VTEB": 0.10,  # Tax-Exempt Bonds (minimal)
            },
            global_tolerance=0.07,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_conservative_template(self) -> ConfigurationTemplate:
        """Create conservative portfolio template."""
        return ConfigurationTemplate(
            template_id="conservative_portfolio",
            name="Conservative Portfolio",
            description="Conservative allocation emphasizing capital preservation and income",
            strategy_type=StrategyTemplate.CONSERVATIVE,
            target_weights={
                "VTI": 0.20,  # Total Stock Market
                "BND": 0.40,  # Total Bond Market
                "VTEB": 0.25,  # Tax-Exempt Bonds
                "VGSH": 0.15,  # Short-Term Treasury
            },
            global_tolerance=0.03,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_dividend_focused_template(self) -> ConfigurationTemplate:
        """Create dividend-focused portfolio template."""
        return ConfigurationTemplate(
            template_id="dividend_focused",
            name="Dividend Focused",
            description="Focus on dividend-paying stocks and REITs for income generation",
            strategy_type=StrategyTemplate.DIVIDEND_FOCUSED,
            target_weights={
                "VYM": 0.35,  # High Dividend Yield
                "VXUS": 0.20,  # International Stocks
                "VNQ": 0.15,  # REITs
                "BND": 0.20,  # Total Bond Market
                "VTEB": 0.10,  # Tax-Exempt Bonds
            },
            global_tolerance=0.05,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_sector_rotation_template(self) -> ConfigurationTemplate:
        """Create sector rotation portfolio template."""
        return ConfigurationTemplate(
            template_id="sector_rotation",
            name="Sector Rotation",
            description="Tactical allocation across different market sectors",
            strategy_type=StrategyTemplate.SECTOR_ROTATION,
            target_weights={
                "XLK": 0.20,  # Technology
                "XLF": 0.15,  # Financial
                "XLV": 0.15,  # Healthcare
                "XLI": 0.12,  # Industrial
                "XLY": 0.12,  # Consumer Discretionary
                "XLE": 0.10,  # Energy
                "XLP": 0.08,  # Consumer Staples
                "XLU": 0.08,  # Utilities
            },
            global_tolerance=0.08,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_equal_weight_template(self) -> ConfigurationTemplate:
        """Create equal weight portfolio template."""
        return ConfigurationTemplate(
            template_id="equal_weight",
            name="Equal Weight",
            description="Equal allocation across all holdings regardless of market cap",
            strategy_type=StrategyTemplate.EQUAL_WEIGHT,
            target_weights={},  # Will be calculated based on holdings
            global_tolerance=0.05,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def _create_market_cap_weighted_template(self) -> ConfigurationTemplate:
        """Create market cap weighted portfolio template."""
        return ConfigurationTemplate(
            template_id="market_cap_weighted",
            name="Market Cap Weighted",
            description="Allocation based on market capitalization weights",
            strategy_type=StrategyTemplate.MARKET_CAP_WEIGHTED,
            target_weights={},  # Will be calculated based on market cap data
            global_tolerance=0.04,
            rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
            is_system_template=True,
        )

    def initialize_templates_in_storage(self, storage_path: Path) -> None:
        """
        Initialize system templates in storage.

        Args:
            storage_path: Path to template storage directory

        """
        import json

        templates_dir = storage_path / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        system_templates = self.get_system_templates()

        for template in system_templates:
            template_file = templates_dir / f"{template.template_id}.json"

            # Only create if doesn't exist to avoid overwriting customizations
            if not template_file.exists():
                try:
                    with template_file.open("w", encoding="utf-8") as f:
                        json.dump(template.model_dump(), f, indent=2, default=str)

                    self.logger.info(f"Initialized system template: {template.template_id}")

                except Exception as e:
                    self.logger.error(f"Failed to initialize template {template.template_id}: {e}")

        self.logger.info(f"Initialized {len(system_templates)} system templates")


class PortfolioOptimizer:
    """Portfolio optimization utilities for weight calculation."""

    def __init__(self) -> None:
        """Initialize portfolio optimizer."""
        self.logger = logger

    def optimize_weights_for_risk_target(self, holdings: list[Holding], _target_risk: float, risk_data: dict[str, float] | None = None) -> dict[str, float]:
        """
        Optimize portfolio weights to achieve a target risk level.

        Args:
            holdings: Portfolio holdings
            target_risk: Target portfolio risk (volatility)
            risk_data: Dictionary of symbol to risk measures

        Returns:
            Optimized weight allocation

        """
        if not holdings or not risk_data:
            # Fallback to equal weights
            equal_weight = 1.0 / len(holdings) if holdings else 0.0
            return {holding.symbol: equal_weight for holding in holdings}

        # Simple risk budgeting approach
        # Allocate inversely to risk, then scale to achieve target risk
        inv_risk_weights = {}
        for holding in holdings:
            risk = risk_data.get(holding.symbol, 0.15)
            inv_risk_weights[holding.symbol] = 1.0 / max(risk, 0.01)

        # Normalize
        total_inv_risk = sum(inv_risk_weights.values())
        if total_inv_risk > 0:
            normalized_weights = {symbol: weight / total_inv_risk for symbol, weight in inv_risk_weights.items()}
        else:
            equal_weight = 1.0 / len(holdings)
            normalized_weights = {holding.symbol: equal_weight for holding in holdings}

        return normalized_weights

    def optimize_weights_for_return_target(self, holdings: list[Holding], target_return: float, return_data: dict[str, float] | None = None) -> dict[str, float]:
        """
        Optimize portfolio weights to achieve a target return.

        Args:
            holdings: Portfolio holdings
            target_return: Target portfolio return
            return_data: Dictionary of symbol to expected returns

        Returns:
            Optimized weight allocation

        """
        if not holdings or not return_data:
            # Fallback to equal weights
            equal_weight = 1.0 / len(holdings) if holdings else 0.0
            return {holding.symbol: equal_weight for holding in holdings}

        # Simple return-weighted approach
        return_weights = {}
        total_return = sum(return_data.get(holding.symbol, 0.08) for holding in holdings)

        for holding in holdings:
            expected_return = return_data.get(holding.symbol, 0.08)
            return_weights[holding.symbol] = expected_return / max(total_return, 0.01)

        # Normalize to sum to 1.0
        total_weight = sum(return_weights.values())
        if total_weight > 0:
            return {symbol: weight / total_weight for symbol, weight in return_weights.items()}

        # Fallback to equal weights
        equal_weight = 1.0 / len(holdings)
        return {holding.symbol: equal_weight for holding in holdings}
