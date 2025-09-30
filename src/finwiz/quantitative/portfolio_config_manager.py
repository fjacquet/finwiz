"""
Portfolio configuration management utilities.

This module contains utilities for managing portfolio configurations,
including listing, filtering, and deletion operations.
"""

import json
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

from .portfolio_config_models import (
    ConfigurationStatus,
    ConfigurationTemplate,
    PortfolioConfigurationMetadata,
    StrategyTemplate,
)

logger = get_logger(__name__)


class PortfolioConfigurationManager:
    """Manages portfolio configuration operations like listing, filtering, and deletion."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize portfolio configuration manager.

        Args:
            storage_path: Path to configuration storage

        """
        self.storage_path = storage_path
        self.configs_path = storage_path / "configs"
        self.templates_path = storage_path / "templates"
        self.logger = logger

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

            for config_file in self.configs_path.glob("*.json"):
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
                    self.logger.warning(f"Failed to load configuration metadata from {config_file}: {e}")
                    continue

            # Sort by updated_at descending
            configs.sort(key=lambda x: x.updated_at, reverse=True)

            return configs

        except Exception as e:
            self.logger.error(f"Failed to list configurations: {e}")
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
                deleted_count = 0

                for config_file in self.configs_path.glob(f"{config_id}_v*.json"):
                    config_file.unlink()
                    deleted_count += 1

                # Also delete base file if exists
                base_file = self.configs_path / f"{config_id}.json"
                if base_file.exists():
                    base_file.unlink()
                    deleted_count += 1

                self.logger.info(f"Deleted {deleted_count} files for configuration {config_id}")
                return deleted_count > 0
            else:
                # Delete specific version
                config_file = self._get_config_file_path(config_id, version)
                if config_file.exists():
                    config_file.unlink()
                    self.logger.info(f"Deleted configuration {config_id} version {version}")
                    return True
                else:
                    self.logger.warning(f"Configuration {config_id} version {version} not found")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to delete configuration {config_id}: {e}")
            return False

    def list_templates(self) -> list[ConfigurationTemplate]:
        """
        List available configuration templates.

        Returns:
            List of configuration templates

        """
        try:
            templates = []

            for template_file in self.templates_path.glob("*.json"):
                try:
                    with template_file.open("r", encoding="utf-8") as f:
                        template_data = json.load(f)

                    template = ConfigurationTemplate.model_validate(template_data)
                    templates.append(template)

                except Exception as e:
                    self.logger.warning(f"Failed to load template from {template_file}: {e}")
                    continue

            # Sort by usage count descending, then by name
            templates.sort(key=lambda x: (-x.usage_count, x.name))

            return templates

        except Exception as e:
            self.logger.error(f"Failed to list templates: {e}")
            return []

    def get_configuration_statistics(self) -> dict[str, Any]:
        """
        Get statistics about stored configurations.

        Returns:
            Dictionary with configuration statistics

        """
        try:
            stats = {
                "total_configurations": 0,
                "by_status": {},
                "by_strategy": {},
                "total_templates": 0,
                "system_templates": 0,
                "custom_templates": 0,
            }

            # Count configurations
            configs = self.list_configurations()
            stats["total_configurations"] = len(configs)

            # Count by status
            for config in configs:
                status = config.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            # Count by strategy
            for config in configs:
                strategy = config.strategy_template.value
                stats["by_strategy"][strategy] = stats["by_strategy"].get(strategy, 0) + 1

            # Count templates
            templates = self.list_templates()
            stats["total_templates"] = len(templates)
            stats["system_templates"] = sum(1 for t in templates if t.is_system_template)
            stats["custom_templates"] = stats["total_templates"] - stats["system_templates"]

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get configuration statistics: {e}")
            return {}

    def find_configurations_by_name(self, name_pattern: str) -> list[PortfolioConfigurationMetadata]:
        """
        Find configurations by name pattern.

        Args:
            name_pattern: Pattern to match in configuration names

        Returns:
            List of matching configurations

        """
        all_configs = self.list_configurations()
        pattern_lower = name_pattern.lower()

        matching_configs = [config for config in all_configs if pattern_lower in config.name.lower()]

        return matching_configs

    def get_configuration_versions(self, config_id: str) -> list[int]:
        """
        Get all available versions for a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            List of version numbers

        """
        try:
            versions = []

            # Look for versioned files
            for config_file in self.configs_path.glob(f"{config_id}_v*.json"):
                try:
                    version_str = config_file.stem.split("_v")[-1]
                    version = int(version_str)
                    versions.append(version)
                except (ValueError, IndexError):
                    continue

            # Also check for base file (latest version)
            base_file = self.configs_path / f"{config_id}.json"
            if base_file.exists():
                try:
                    with base_file.open("r", encoding="utf-8") as f:
                        config_data = json.load(f)
                    metadata = PortfolioConfigurationMetadata.model_validate(config_data["metadata"])
                    if metadata.version not in versions:
                        versions.append(metadata.version)
                except Exception:
                    pass

            return sorted(versions)

        except Exception as e:
            self.logger.error(f"Failed to get versions for configuration {config_id}: {e}")
            return []

    def cleanup_old_versions(self, config_id: str, keep_versions: int = 5) -> int:
        """
        Clean up old versions of a configuration, keeping only the most recent ones.

        Args:
            config_id: Configuration ID
            keep_versions: Number of versions to keep

        Returns:
            Number of versions deleted

        """
        try:
            versions = self.get_configuration_versions(config_id)

            if len(versions) <= keep_versions:
                return 0

            # Sort versions and keep only the most recent
            versions.sort(reverse=True)
            versions_to_delete = versions[keep_versions:]

            deleted_count = 0
            for version in versions_to_delete:
                if self.delete_configuration(config_id, version):
                    deleted_count += 1

            self.logger.info(f"Cleaned up {deleted_count} old versions for configuration {config_id}")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup versions for configuration {config_id}: {e}")
            return 0

    def _get_config_file_path(self, config_id: str, version: int | None = None) -> Path:
        """Get file path for configuration."""
        if version is None:
            return self.configs_path / f"{config_id}.json"
        else:
            return self.configs_path / f"{config_id}_v{version}.json"
