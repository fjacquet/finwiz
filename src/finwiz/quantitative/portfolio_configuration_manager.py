"""
Portfolio configuration management system for FinWiz.

This module provides comprehensive portfolio configuration management including
saving/loading configurations, versioning, validation, and template management
for common investment strategies.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_rebalancing import Holding
from finwiz.tools.logger import get_logger

# Import from extracted modules
from .portfolio_builders import PortfolioBuilder, SystemTemplateManager
from .portfolio_config_io import PortfolioConfigurationIO
from .portfolio_config_manager import PortfolioConfigurationManager as ConfigManager
from .portfolio_config_models import (
    ConfigurationStatus,
    ConfigurationTemplate,
    PortfolioConfigurationMetadata,
    PortfolioConfigurationVersion,
    StrategyTemplate,
)
from .portfolio_config_storage import PortfolioConfigurationStorage
from .portfolio_config_validation import PortfolioConfigurationValidator

logger = get_logger(__name__)


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

        # Initialize extracted modules
        self.validator = PortfolioConfigurationValidator()
        self.builder = PortfolioBuilder(self.storage_path)
        self.template_manager = SystemTemplateManager()
        self.io_handler = PortfolioConfigurationIO(self.storage_path)
        self.config_manager = ConfigManager(self.storage_path)
        self.storage = PortfolioConfigurationStorage(self.storage_path)

        # Load system templates
        self.template_manager.initialize_templates_in_storage(self.storage_path)

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
        """Create a new portfolio configuration."""
        from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration

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
            versioned_config = PortfolioConfigurationVersion(metadata=metadata, configuration=portfolio_config, change_summary="Initial configuration creation")

            # Validate and save
            validation_errors = self.validator.validate_configuration(portfolio_config)
            versioned_config.validation_errors = validation_errors

            if validation_errors:
                logger.warning(f"Configuration {config_id} has validation errors: {validation_errors}")

            self.storage.save_configuration(versioned_config)

            logger.info(f"Created portfolio configuration: {config_id} ({name})")
            return config_id

        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            raise ValueError(f"Failed to create configuration: {e}") from e

    def load_configuration(self, config_id: str, version: int | None = None) -> PortfolioConfigurationVersion:
        """Load a portfolio configuration."""
        return self.storage.load_configuration(config_id, version)

    def save_configuration(self, versioned_config: PortfolioConfigurationVersion) -> None:
        """Save a portfolio configuration version."""
        from datetime import datetime

        # Update timestamp
        versioned_config.metadata.updated_at = datetime.now()

        # Validate configuration
        validation_errors = self.validator.validate_configuration(versioned_config.configuration)
        versioned_config.validation_errors = validation_errors

        # Save configuration
        self.storage.save_configuration(versioned_config)

    def update_configuration(self, config_id: str, updates: dict[str, Any], change_summary: str = "") -> str:
        """Update an existing configuration, creating a new version."""
        from datetime import datetime

        from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration

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
        """List available portfolio configurations."""
        return self.config_manager.list_configurations(status, strategy_template, tags)

    def delete_configuration(self, config_id: str, version: int | None = None) -> bool:
        """Delete a portfolio configuration or specific version."""
        return self.config_manager.delete_configuration(config_id, version)

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

            # Use builder to create configuration from template
            config_params = self.builder.create_from_template(template, holdings, name, description)

            # Create configuration
            config_id = self.create_configuration(**config_params)

            # Save updated template with usage count
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
        config = self.load_configuration(config_id)
        return self.io_handler.export_configuration(config, export_path, format_type)

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
        config_params = self.io_handler.import_configuration(import_path, name)
        return self.create_configuration(**config_params)

    def load_template(self, template_id: str) -> ConfigurationTemplate:
        """Load a configuration template."""
        return self.storage.load_template(template_id)

    def save_template(self, template: ConfigurationTemplate) -> None:
        """Save a configuration template."""
        self.storage.save_template(template)

    def list_templates(self) -> list[ConfigurationTemplate]:
        """List available configuration templates."""
        return self.config_manager.list_templates()
