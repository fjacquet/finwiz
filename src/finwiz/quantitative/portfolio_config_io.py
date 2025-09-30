"""
Import/Export utilities for portfolio configurations.

This module contains utilities for importing and exporting portfolio
configurations to/from various file formats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.schemas.portfolio_rebalancing import PortfolioConfiguration
from finwiz.tools.logger import get_logger

from .portfolio_config_models import (
    ConfigurationTemplate,
    PortfolioConfigurationVersion,
    StrategyTemplate,
)

logger = get_logger(__name__)


class PortfolioConfigurationIO:
    """Handles import/export operations for portfolio configurations."""

    def __init__(self, storage_path: Path) -> None:
        """
        Initialize portfolio configuration I/O handler.

        Args:
            storage_path: Base storage path for configurations

        """
        self.storage_path = storage_path
        self.exports_path = storage_path / "exports"
        self.exports_path.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def export_configuration(
        self, config: PortfolioConfigurationVersion, export_path: Path | None = None, format_type: str = "json"
    ) -> Path:
        """
        Export a configuration to file.

        Args:
            config: Configuration to export
            export_path: Export file path (auto-generated if None)
            format_type: Export format ('json' or 'yaml')

        Returns:
            Path to exported file

        Raises:
            ValueError: If export fails

        """
        try:
            # Generate export path if not provided
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{config.metadata.name}_{timestamp}.{format_type}"
                export_path = self.exports_path / filename

            # Export based on format
            if format_type.lower() == "json":
                with export_path.open("w", encoding="utf-8") as f:
                    json.dump(config.model_dump(), f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

            self.logger.info(f"Exported configuration {config.metadata.config_id} to {export_path}")
            return export_path

        except Exception as e:
            self.logger.error(f"Failed to export configuration {config.metadata.config_id}: {e}")
            raise ValueError(f"Failed to export configuration: {e}") from e

    def import_configuration(self, import_path: Path, name: str | None = None) -> dict[str, Any]:
        """
        Import a configuration from file.

        Args:
            import_path: Path to configuration file
            name: Override configuration name

        Returns:
            Dictionary with configuration parameters for creation

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

            # Create configuration parameters
            config_params = {
                "name": name or f"{original_name}_imported",
                "holdings": portfolio_config.holdings,
                "target_weights": portfolio_config.target_weights,
                "description": description,
                "strategy_template": strategy_template,
                "tolerance_bands": portfolio_config.tolerance_bands,
                "global_tolerance": portfolio_config.global_tolerance,
                "available_capital": portfolio_config.available_capital,
                "transaction_cost_rate": portfolio_config.transaction_cost_rate,
                "min_trade_size": portfolio_config.min_trade_size,
                "rebalancing_method": portfolio_config.rebalancing_method,
            }

            self.logger.info(f"Imported configuration from {import_path}")
            return config_params

        except Exception as e:
            self.logger.error(f"Failed to import configuration from {import_path}: {e}")
            raise ValueError(f"Failed to import configuration: {e}") from e

    def export_template(self, template: ConfigurationTemplate, export_path: Path | None = None) -> Path:
        """
        Export a configuration template to file.

        Args:
            template: Template to export
            export_path: Export file path (auto-generated if None)

        Returns:
            Path to exported file

        """
        try:
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"template_{template.template_id}_{timestamp}.json"
                export_path = self.exports_path / filename

            with export_path.open("w", encoding="utf-8") as f:
                json.dump(template.model_dump(), f, indent=2, default=str)

            self.logger.info(f"Exported template {template.template_id} to {export_path}")
            return export_path

        except Exception as e:
            self.logger.error(f"Failed to export template {template.template_id}: {e}")
            raise ValueError(f"Failed to export template: {e}") from e

    def import_template(self, import_path: Path) -> ConfigurationTemplate:
        """
        Import a configuration template from file.

        Args:
            import_path: Path to template file

        Returns:
            Configuration template

        Raises:
            FileNotFoundError: If import file not found
            ValueError: If import fails

        """
        try:
            if not import_path.exists():
                raise FileNotFoundError(f"Template file not found: {import_path}")

            with import_path.open("r", encoding="utf-8") as f:
                template_data = json.load(f)

            template = ConfigurationTemplate.model_validate(template_data)

            self.logger.info(f"Imported template {template.template_id} from {import_path}")
            return template

        except Exception as e:
            self.logger.error(f"Failed to import template from {import_path}: {e}")
            raise ValueError(f"Failed to import template: {e}") from e

    def bulk_export_configurations(self, configs: list[PortfolioConfigurationVersion], export_dir: Path) -> list[Path]:
        """
        Export multiple configurations to a directory.

        Args:
            configs: List of configurations to export
            export_dir: Directory to export to

        Returns:
            List of exported file paths

        """
        export_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []

        for config in configs:
            try:
                filename = f"{config.metadata.name}_{config.metadata.config_id}.json"
                export_path = export_dir / filename
                exported_path = self.export_configuration(config, export_path)
                exported_files.append(exported_path)
            except Exception as e:
                self.logger.error(f"Failed to export configuration {config.metadata.config_id}: {e}")
                continue

        self.logger.info(f"Bulk exported {len(exported_files)} configurations to {export_dir}")
        return exported_files

    def validate_import_file(self, import_path: Path) -> dict[str, Any]:
        """
        Validate an import file without actually importing it.

        Args:
            import_path: Path to file to validate

        Returns:
            Dictionary with validation results

        """
        validation_result = {
            "is_valid": False,
            "file_type": "unknown",
            "errors": [],
            "warnings": [],
            "metadata": {},
        }

        try:
            if not import_path.exists():
                validation_result["errors"].append("File does not exist")
                return validation_result

            with import_path.open("r", encoding="utf-8") as f:
                config_data = json.load(f)

            # Determine file type
            if "metadata" in config_data and "configuration" in config_data:
                validation_result["file_type"] = "versioned_configuration"
                try:
                    versioned_config = PortfolioConfigurationVersion.model_validate(config_data)
                    validation_result["is_valid"] = True
                    validation_result["metadata"] = {
                        "name": versioned_config.metadata.name,
                        "description": versioned_config.metadata.description,
                        "strategy_template": versioned_config.metadata.strategy_template,
                        "version": versioned_config.metadata.version,
                    }
                except Exception as e:
                    validation_result["errors"].append(f"Invalid versioned configuration: {e}")

            elif "template_id" in config_data:
                validation_result["file_type"] = "template"
                try:
                    template = ConfigurationTemplate.model_validate(config_data)
                    validation_result["is_valid"] = True
                    validation_result["metadata"] = {
                        "template_id": template.template_id,
                        "name": template.name,
                        "strategy_type": template.strategy_type,
                    }
                except Exception as e:
                    validation_result["errors"].append(f"Invalid template: {e}")

            else:
                validation_result["file_type"] = "raw_configuration"
                try:
                    PortfolioConfiguration.model_validate(config_data)
                    validation_result["is_valid"] = True
                    validation_result["metadata"] = {"holdings_count": len(config_data.get("holdings", []))}
                except Exception as e:
                    validation_result["errors"].append(f"Invalid portfolio configuration: {e}")

        except json.JSONDecodeError as e:
            validation_result["errors"].append(f"Invalid JSON format: {e}")
        except Exception as e:
            validation_result["errors"].append(f"Validation error: {e}")

        return validation_result
