"""
Storage operations for portfolio configurations.

This module handles low-level storage operations for portfolio
configurations and templates.
"""

import json
from pathlib import Path

from finwiz.tools.logger import get_logger

from .portfolio_config_models import (
    ConfigurationTemplate,
    PortfolioConfigurationVersion,
)

logger = get_logger(__name__)


class PortfolioConfigurationStorage:
    """Handles storage operations for portfolio configurations and templates."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize portfolio configuration storage.

        Args:
            storage_path: Base storage path

        """
        self.storage_path = storage_path
        self.configs_path = storage_path / "configs"
        self.templates_path = storage_path / "templates"
        self.logger = logger

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

            self.logger.info(f"Loaded configuration: {config_id} v{versioned_config.metadata.version}")
            return versioned_config

        except Exception as e:
            self.logger.error(f"Failed to load configuration {config_id}: {e}")
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
            self._save_configuration_version(versioned_config)
            self.logger.info(f"Saved configuration: {versioned_config.metadata.config_id} v{versioned_config.metadata.version}")

        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ValueError(f"Failed to save configuration: {e}") from e

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
            template_file = self.templates_path / f"{template_id}.json"

            if not template_file.exists():
                raise FileNotFoundError(f"Template not found: {template_id}")

            with template_file.open("r", encoding="utf-8") as f:
                template_data = json.load(f)

            return ConfigurationTemplate.model_validate(template_data)

        except Exception as e:
            self.logger.error(f"Failed to load template {template_id}: {e}")
            raise

    def save_template(self, template: ConfigurationTemplate) -> None:
        """
        Save a configuration template.

        Args:
            template: Template to save

        """
        try:
            template_file = self.templates_path / f"{template.template_id}.json"

            with template_file.open("w", encoding="utf-8") as f:
                json.dump(template.model_dump(), f, indent=2, default=str)

            self.logger.info(f"Saved template: {template.template_id}")

        except Exception as e:
            self.logger.error(f"Failed to save template {template.template_id}: {e}")
            raise

    def _save_configuration_version(self, versioned_config: PortfolioConfigurationVersion) -> None:
        """Save a versioned configuration to file."""
        config_id = versioned_config.metadata.config_id
        version = versioned_config.metadata.version

        # Save with version number
        config_file = self._get_config_file_path(config_id, version)

        with config_file.open("w", encoding="utf-8") as f:
            json.dump(versioned_config.model_dump(), f, indent=2, default=str)

        # Also save as latest version (without version suffix)
        latest_file = self.configs_path / f"{config_id}.json"
        with latest_file.open("w", encoding="utf-8") as f:
            json.dump(versioned_config.model_dump(), f, indent=2, default=str)

    def _get_config_file_path(self, config_id: str, version: int | None = None) -> Path:
        """Get file path for configuration."""
        if version is None:
            return self.configs_path / f"{config_id}.json"
        else:
            return self.configs_path / f"{config_id}_v{version}.json"
