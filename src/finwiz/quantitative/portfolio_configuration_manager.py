"""
Portfolio configuration management system for FinWiz.

This module provides comprehensive portfolio configuration management including
saving/loading configurations, versioning, validation, and template management
for common investment strategies.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finwiz.schemas.portfolio_rebalancing import Holding, PortfolioConfiguration, RebalancingMethod
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class StrategyTemplate(str, Enum):
    """Pre-defined portfolio strategy templates."""

    BALANCED = "balanced"
    AGGRESSIVE_GROWTH = "aggressive_growth"
    CONSERVATIVE = "conservative"
    DIVIDEND_FOCUSED = "dividend_focused"
    SECTOR_ROTATION = "sector_rotation"
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP_WEIGHTED = "market_cap_weighted"
    CUSTOM = "custom"


class ConfigurationStatus(str, Enum):
    """Portfolio configuration status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


class PortfolioConfigurationMetadata(BaseModel):
    """Metadata for portfolio configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    config_id: str = Field(..., description="Unique configuration identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Configuration name")
    description: str = Field(default="", max_length=500, description="Configuration description")
    strategy_template: StrategyTemplate = Field(default=StrategyTemplate.CUSTOM, description="Strategy template used")
    status: ConfigurationStatus = Field(default=ConfigurationStatus.DRAFT, description="Configuration status")

    # Versioning
    version: int = Field(default=1, ge=1, description="Configuration version number")
    parent_config_id: str | None = Field(None, description="Parent configuration ID for versioning")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    created_by: str = Field(default="system", description="Creator identifier")

    # Tags and categorization
    tags: list[str] = Field(default_factory=list, max_length=10, description="Configuration tags")
    category: str = Field(default="general", description="Configuration category")

    # Performance tracking
    last_rebalanced: datetime | None = Field(None, description="Last rebalancing timestamp")
    performance_notes: str = Field(default="", max_length=1000, description="Performance notes")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate tags format."""
        validated_tags = []
        for tag in v:
            clean_tag = tag.strip().lower()
            if clean_tag and len(clean_tag) <= 20:
                validated_tags.append(clean_tag)
        return validated_tags


class PortfolioConfigurationVersion(BaseModel):
    """Versioned portfolio configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    metadata: PortfolioConfigurationMetadata = Field(..., description="Configuration metadata")
    configuration: PortfolioConfiguration = Field(..., description="Portfolio configuration")
    change_summary: str = Field(default="", description="Summary of changes in this version")
    validation_errors: list[str] = Field(default_factory=list, description="Validation errors if any")


class ConfigurationTemplate(BaseModel):
    """Template for creating portfolio configurations."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    strategy_type: StrategyTemplate = Field(..., description="Strategy type")

    # Template configuration
    target_weights: dict[str, float] = Field(..., description="Default target weights")
    global_tolerance: float = Field(default=0.05, description="Default tolerance")
    rebalancing_method: RebalancingMethod = Field(
        default=RebalancingMethod.MINIMIZE_TRADES, description="Default rebalancing method"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now, description="Template creation date")
    is_system_template: bool = Field(default=False, description="Whether this is a system template")
    usage_count: int = Field(default=0, ge=0, description="Number of times template has been used")


class PortfolioConfigurationManager:
    """
    Manager for portfolio configurations with versioning, templates, and validation.

    Provides comprehensive configuration management including:
    - Saving and loading configurations
    - Version control and change tracking
    - Template management for common strategies
    - Import/export functionality
    - Validation and consistency checks
    """

    def __init__(self, storage_path: Path | None = None) -> None:
        """
        Initialize portfolio configuration manager.

        Args:
            storage_path: Path to store configuration files (defaults to 'data/portfolio_configs')

        """
        self.storage_path = storage_path or Path("data/portfolio_configs")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize subdirectories
        (self.storage_path / "configs").mkdir(exist_ok=True)
        (self.storage_path / "templates").mkdir(exist_ok=True)
        (self.storage_path / "exports").mkdir(exist_ok=True)

        # Load system templates
        self._initialize_system_templates()

        logger.info(f"Portfolio configuration manager initialized with storage path: {self.storage_path}")

    def create_configuration(
        self,
        name: str,
        holdings: list[Holding],
        target_weights: dict[str, float],
        description: str = "",
        strategy_template: StrategyTemplate = StrategyTemplate.CUSTOM,
        **kwargs: Any,
    ) -> str:
        """
        Create a new portfolio configuration.

        Args:
            name: Configuration name
            holdings: Portfolio holdings
            target_weights: Target allocation weights
            description: Configuration description
            strategy_template: Strategy template used
            **kwargs: Additional configuration parameters

        Returns:
            Configuration ID

        Raises:
            ValueError: If configuration is invalid

        """
        try:
            # Generate unique ID
            config_id = str(uuid.uuid4())

            # Create portfolio configuration
            portfolio_config = PortfolioConfiguration(holdings=holdings, target_weights=target_weights, **kwargs)

            # Create metadata
            metadata = PortfolioConfigurationMetadata(
                config_id=config_id,
                name=name,
                description=description,
                strategy_template=strategy_template,
                status=ConfigurationStatus.DRAFT,
            )

            # Create versioned configuration
            versioned_config = PortfolioConfigurationVersion(
                metadata=metadata, configuration=portfolio_config, change_summary="Initial configuration creation"
            )

            # Validate configuration
            validation_errors = self._validate_configuration(portfolio_config)
            versioned_config.validation_errors = validation_errors

            if validation_errors:
                logger.warning(f"Configuration {config_id} has validation errors: {validation_errors}")

            # Save configuration
            self._save_configuration_version(versioned_config)

            logger.info(f"Created portfolio configuration: {config_id} ({name})")
            return config_id

        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise ValueError(f"Failed to create configuration: {e}") from e

    def load_configuration(self, config_id: str, version: int | None = None) -> PortfolioConfigurationVersion:
        """
        Load a portfolio configuration.

        Args:
            config_id: Configuration ID
            version: Specific version to load (defaults to latest)

        Returns:
            Portfolio configuration version

        Raises:
            FileNotFoundError: If configuration not found
            ValueError: If configuration is invalid

        """
        try:
            config_file = self._get_config_file_path(config_id, version)

            if not config_file.exists():
                raise FileNotFoundError(f"Configuration not found: {config_id}")

            with config_file.open("r", encoding="utf-8") as f:
                config_data = json.load(f)

            versioned_config = PortfolioConfigurationVersion.model_validate(config_data)

            logger.info(f"Loaded configuration: {config_id} v{versioned_config.metadata.version}")
            return versioned_config

        except Exception as e:
            logger.error(f"Failed to load configuration {config_id}: {e}")
            raise

    def save_configuration(self, versioned_config: PortfolioConfigurationVersion) -> None:
        """
        Save a portfolio configuration version.

        Args:
            versioned_config: Configuration version to save

        Raises:
            ValueError: If configuration is invalid

        """
        try:
            # Update timestamp
            versioned_config.metadata.updated_at = datetime.now()

            # Validate configuration
            validation_errors = self._validate_configuration(versioned_config.configuration)
            versioned_config.validation_errors = validation_errors

            # Save configuration
            self._save_configuration_version(versioned_config)

            logger.info(f"Saved configuration: {versioned_config.metadata.config_id} v{versioned_config.metadata.version}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise ValueError(f"Failed to save configuration: {e}") from e

    def update_configuration(self, config_id: str, updates: dict[str, Any], change_summary: str = "") -> str:
        """
        Update an existing configuration, creating a new version.

        Args:
            config_id: Configuration ID to update
            updates: Dictionary of updates to apply
            change_summary: Summary of changes made

        Returns:
            New configuration ID (same as input for version updates)

        Raises:
            FileNotFoundError: If configuration not found
            ValueError: If updates are invalid

        """
        try:
            # Load current configuration
            current_config = self.load_configuration(config_id)

            # Create new version
            new_version = current_config.metadata.version + 1

            # Apply updates to configuration
            config_dict = current_config.configuration.model_dump()
            config_dict.update(updates)

            # Create updated configuration
            updated_config = PortfolioConfiguration.model_validate(config_dict)

            # Update metadata
            new_metadata = current_config.metadata.model_copy()
            new_metadata.version = new_version
            new_metadata.updated_at = datetime.now()
            new_metadata.parent_config_id = config_id

            # Create new versioned configuration
            new_versioned_config = PortfolioConfigurationVersion(
                metadata=new_metadata,
                configuration=updated_config,
                change_summary=change_summary or f"Updated configuration to version {new_version}",
            )

            # Save new version
            self.save_configuration(new_versioned_config)

            logger.info(f"Updated configuration {config_id} to version {new_version}")
            return config_id

        except Exception as e:
            logger.error(f"Failed to update configuration {config_id}: {e}")
            raise

    def list_configurations(
        self,
        status: ConfigurationStatus | None = None,
        strategy_template: StrategyTemplate | None = None,
        tags: list[str] | None = None,
    ) -> list[PortfolioConfigurationMetadata]:
        """
        List available portfolio configurations.

        Args:
            status: Filter by configuration status
            strategy_template: Filter by strategy template
            tags: Filter by tags (any match)

        Returns:
            List of configuration metadata

        """
        try:
            configs = []
            config_dir = self.storage_path / "configs"

            for config_file in config_dir.glob("*.json"):
                try:
                    with config_file.open("r", encoding="utf-8") as f:
                        config_data = json.load(f)

                    metadata = PortfolioConfigurationMetadata.model_validate(config_data["metadata"])

                    # Apply filters
                    if status and metadata.status != status:
                        continue

                    if strategy_template and metadata.strategy_template != strategy_template:
                        continue

                    if tags and not any(tag in metadata.tags for tag in tags):
                        continue

                    configs.append(metadata)

                except Exception as e:
                    logger.warning(f"Failed to load configuration metadata from {config_file}: {e}")
                    continue

            # Sort by updated_at descending
            configs.sort(key=lambda x: x.updated_at, reverse=True)

            return configs

        except Exception as e:
            logger.error(f"Failed to list configurations: {e}")
            return []

    def delete_configuration(self, config_id: str, version: int | None = None) -> bool:
        """
        Delete a portfolio configuration or specific version.

        Args:
            config_id: Configuration ID
            version: Specific version to delete (None deletes all versions)

        Returns:
            True if deletion successful

        """
        try:
            if version is None:
                # Delete all versions
                config_dir = self.storage_path / "configs"
                deleted_count = 0

                for config_file in config_dir.glob(f"{config_id}_v*.json"):
                    config_file.unlink()
                    deleted_count += 1

                # Also delete base file if exists
                base_file = config_dir / f"{config_id}.json"
                if base_file.exists():
                    base_file.unlink()
                    deleted_count += 1

                logger.info(f"Deleted {deleted_count} files for configuration {config_id}")
                return deleted_count > 0
            else:
                # Delete specific version
                config_file = self._get_config_file_path(config_id, version)
                if config_file.exists():
                    config_file.unlink()
                    logger.info(f"Deleted configuration {config_id} version {version}")
                    return True
                else:
                    logger.warning(f"Configuration {config_id} version {version} not found")
                    return False

        except Exception as e:
            logger.error(f"Failed to delete configuration {config_id}: {e}")
            return False

    def create_from_template(self, template_id: str, name: str, holdings: list[Holding], description: str = "") -> str:
        """
        Create a configuration from a template.

        Args:
            template_id: Template ID to use
            name: New configuration name
            holdings: Portfolio holdings
            description: Configuration description

        Returns:
            New configuration ID

        Raises:
            FileNotFoundError: If template not found
            ValueError: If template application fails

        """
        try:
            # Load template
            template = self.load_template(template_id)

            # Extract symbols from holdings
            holding_symbols = {holding.symbol for holding in holdings}

            # Adjust template weights to match holdings
            adjusted_weights = {}
            template_symbols = set(template.target_weights.keys())

            # Use template weights for matching symbols
            for symbol in holding_symbols:
                if symbol in template_symbols:
                    adjusted_weights[symbol] = template.target_weights[symbol]
                else:
                    # Equal weight for new symbols
                    adjusted_weights[symbol] = 1.0 / len(holding_symbols)

            # Normalize weights to sum to 1.0
            total_weight = sum(adjusted_weights.values())
            if total_weight > 0:
                adjusted_weights = {k: v / total_weight for k, v in adjusted_weights.items()}

            # Create configuration
            config_id = self.create_configuration(
                name=name,
                holdings=holdings,
                target_weights=adjusted_weights,
                description=description,
                strategy_template=template.strategy_type,
                global_tolerance=template.global_tolerance,
                rebalancing_method=template.rebalancing_method,
            )

            # Update template usage count
            template.usage_count += 1
            self.save_template(template)

            logger.info(f"Created configuration {config_id} from template {template_id}")
            return config_id

        except Exception as e:
            logger.error(f"Failed to create configuration from template {template_id}: {e}")
            raise

    def export_configuration(self, config_id: str, export_path: Path | None = None, format_type: str = "json") -> Path:
        """
        Export a configuration to file.

        Args:
            config_id: Configuration ID to export
            export_path: Export file path (auto-generated if None)
            format_type: Export format ('json' or 'yaml')

        Returns:
            Path to exported file

        Raises:
            ValueError: If export fails

        """
        try:
            # Load configuration
            config = self.load_configuration(config_id)

            # Generate export path if not provided
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{config.metadata.name}_{timestamp}.{format_type}"
                export_path = self.storage_path / "exports" / filename

            # Export based on format
            if format_type.lower() == "json":
                with export_path.open("w", encoding="utf-8") as f:
                    json.dump(config.model_dump(), f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

            logger.info(f"Exported configuration {config_id} to {export_path}")
            return export_path

        except Exception as e:
            logger.error(f"Failed to export configuration {config_id}: {e}")
            raise ValueError(f"Failed to export configuration: {e}") from e

    def import_configuration(self, import_path: Path, name: str | None = None) -> str:
        """
        Import a configuration from file.

        Args:
            import_path: Path to configuration file
            name: Override configuration name

        Returns:
            New configuration ID

        Raises:
            FileNotFoundError: If import file not found
            ValueError: If import fails

        """
        try:
            if not import_path.exists():
                raise FileNotFoundError(f"Import file not found: {import_path}")

            # Load configuration data
            with import_path.open("r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Parse configuration
            if "metadata" in config_data and "configuration" in config_data:
                # Full versioned configuration
                versioned_config = PortfolioConfigurationVersion.model_validate(config_data)
                portfolio_config = versioned_config.configuration
                original_name = versioned_config.metadata.name
                description = versioned_config.metadata.description
                strategy_template = versioned_config.metadata.strategy_template
            else:
                # Raw portfolio configuration
                portfolio_config = PortfolioConfiguration.model_validate(config_data)
                original_name = import_path.stem
                description = f"Imported from {import_path.name}"
                strategy_template = StrategyTemplate.CUSTOM

            # Create new configuration
            config_id = self.create_configuration(
                name=name or f"{original_name}_imported",
                holdings=portfolio_config.holdings,
                target_weights=portfolio_config.target_weights,
                description=description,
                strategy_template=strategy_template,
                tolerance_bands=portfolio_config.tolerance_bands,
                global_tolerance=portfolio_config.global_tolerance,
                available_capital=portfolio_config.available_capital,
                transaction_cost_rate=portfolio_config.transaction_cost_rate,
                min_trade_size=portfolio_config.min_trade_size,
                rebalancing_method=portfolio_config.rebalancing_method,
            )

            logger.info(f"Imported configuration from {import_path} as {config_id}")
            return config_id

        except Exception as e:
            logger.error(f"Failed to import configuration from {import_path}: {e}")
            raise ValueError(f"Failed to import configuration: {e}") from e

    def load_template(self, template_id: str) -> ConfigurationTemplate:
        """
        Load a configuration template.

        Args:
            template_id: Template ID

        Returns:
            Configuration template

        Raises:
            FileNotFoundError: If template not found

        """
        try:
            template_file = self.storage_path / "templates" / f"{template_id}.json"

            if not template_file.exists():
                raise FileNotFoundError(f"Template not found: {template_id}")

            with template_file.open("r", encoding="utf-8") as f:
                template_data = json.load(f)

            return ConfigurationTemplate.model_validate(template_data)

        except Exception as e:
            logger.error(f"Failed to load template {template_id}: {e}")
            raise

    def save_template(self, template: ConfigurationTemplate) -> None:
        """
        Save a configuration template.

        Args:
            template: Template to save

        """
        try:
            template_file = self.storage_path / "templates" / f"{template.template_id}.json"

            with template_file.open("w", encoding="utf-8") as f:
                json.dump(template.model_dump(), f, indent=2, default=str)

            logger.info(f"Saved template: {template.template_id}")

        except Exception as e:
            logger.error(f"Failed to save template {template.template_id}: {e}")
            raise

    def list_templates(self) -> list[ConfigurationTemplate]:
        """
        List available configuration templates.

        Returns:
            List of configuration templates

        """
        try:
            templates = []
            template_dir = self.storage_path / "templates"

            for template_file in template_dir.glob("*.json"):
                try:
                    with template_file.open("r", encoding="utf-8") as f:
                        template_data = json.load(f)

                    template = ConfigurationTemplate.model_validate(template_data)
                    templates.append(template)

                except Exception as e:
                    logger.warning(f"Failed to load template from {template_file}: {e}")
                    continue

            # Sort by usage count descending, then by name
            templates.sort(key=lambda x: (-x.usage_count, x.name))

            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []

    def _validate_configuration(self, config: PortfolioConfiguration) -> list[str]:
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

            # Check holdings consistency
            holding_symbols = {holding.symbol for holding in config.holdings}
            target_symbols = set(config.target_weights.keys())

            missing_targets = holding_symbols - target_symbols
            if missing_targets:
                errors.append(f"Missing target weights for holdings: {', '.join(missing_targets)}")

            extra_targets = target_symbols - holding_symbols
            if extra_targets:
                errors.append(f"Target weights for non-held symbols: {', '.join(extra_targets)}")

            # Check tolerance bands
            for symbol, tolerance in config.tolerance_bands.items():
                if symbol not in target_symbols:
                    errors.append(f"Tolerance band for non-existent symbol: {symbol}")
                elif tolerance <= 0 or tolerance > 0.5:
                    errors.append(f"Invalid tolerance for {symbol}: {tolerance:.1%}")

            # Check for duplicate holdings
            symbols_seen = set()
            for holding in config.holdings:
                if holding.symbol in symbols_seen:
                    errors.append(f"Duplicate holding for symbol: {holding.symbol}")
                symbols_seen.add(holding.symbol)

            # Check minimum trade size
            if config.min_trade_size <= 0:
                errors.append(f"Minimum trade size must be positive: {config.min_trade_size}")

            # Check transaction cost rate
            if config.transaction_cost_rate < 0 or config.transaction_cost_rate > 0.1:
                errors.append(f"Transaction cost rate should be between 0% and 10%: {config.transaction_cost_rate:.1%}")

        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def _save_configuration_version(self, versioned_config: PortfolioConfigurationVersion) -> None:
        """Save a versioned configuration to file."""
        config_id = versioned_config.metadata.config_id
        version = versioned_config.metadata.version

        # Save with version number
        config_file = self._get_config_file_path(config_id, version)

        with config_file.open("w", encoding="utf-8") as f:
            json.dump(versioned_config.model_dump(), f, indent=2, default=str)

        # Also save as latest version (without version suffix)
        latest_file = self.storage_path / "configs" / f"{config_id}.json"
        with latest_file.open("w", encoding="utf-8") as f:
            json.dump(versioned_config.model_dump(), f, indent=2, default=str)

    def _get_config_file_path(self, config_id: str, version: int | None = None) -> Path:
        """Get file path for configuration."""
        config_dir = self.storage_path / "configs"

        if version is None:
            return config_dir / f"{config_id}.json"
        else:
            return config_dir / f"{config_id}_v{version}.json"

    def _initialize_system_templates(self) -> None:
        """Initialize system-provided configuration templates."""
        system_templates = [
            ConfigurationTemplate(
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
            ),
            ConfigurationTemplate(
                template_id="aggressive_growth",
                name="Aggressive Growth",
                description="High-growth allocation focused on equities with higher risk tolerance",
                strategy_type=StrategyTemplate.AGGRESSIVE_GROWTH,
                target_weights={
                    "VTI": 0.50,  # Total Stock Market
                    "VTIAX": 0.25,  # International Stocks
                    "VB": 0.15,  # Small-Cap
                    "VUG": 0.10,  # Growth Stocks
                },
                global_tolerance=0.08,
                rebalancing_method=RebalancingMethod.MINIMIZE_TRADES,
                is_system_template=True,
            ),
            ConfigurationTemplate(
                template_id="conservative_income",
                name="Conservative Income",
                description="Conservative allocation focused on income generation and capital preservation",
                strategy_type=StrategyTemplate.CONSERVATIVE,
                target_weights={
                    "VTI": 0.20,  # Total Stock Market
                    "BND": 0.40,  # Total Bond Market
                    "VTEB": 0.20,  # Tax-Exempt Bonds
                    "VGIT": 0.20,  # Intermediate-Term Treasury
                },
                global_tolerance=0.03,
                rebalancing_method=RebalancingMethod.MINIMIZE_COSTS,
                is_system_template=True,
            ),
            ConfigurationTemplate(
                template_id="dividend_focused",
                name="Dividend Focused",
                description="Focus on dividend-paying stocks for income generation",
                strategy_type=StrategyTemplate.DIVIDEND_FOCUSED,
                target_weights={
                    "VYM": 0.40,  # High Dividend Yield
                    "VIGI": 0.20,  # International Dividend
                    "VNQ": 0.15,  # Real Estate
                    "BND": 0.25,  # Bonds for stability
                },
                global_tolerance=0.06,
                rebalancing_method=RebalancingMethod.TAX_EFFICIENT,
                is_system_template=True,
            ),
        ]

        # Save system templates if they don't exist
        for template in system_templates:
            template_file = self.storage_path / "templates" / f"{template.template_id}.json"
            if not template_file.exists():
                self.save_template(template)
                logger.info(f"Created system template: {template.template_id}")
