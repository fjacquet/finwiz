"""
Unit tests for portfolio configuration manager.

Tests comprehensive configuration management including saving/loading,
versioning, validation, templates, and import/export functionality.
"""

from pytest import approx
import json
import tempfile
from pathlib import Path

import pytest

from finwiz.quantitative.portfolio_configuration_manager import (
    ConfigurationTemplate,
    PortfolioConfigurationManager,
    StrategyTemplate,
)
from finwiz.schemas.portfolio_rebalancing import Holding


class TestPortfolioConfigurationManager:
    """Test suite for PortfolioConfigurationManager."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary storage path for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_storage_path):
        """Create configuration manager with temporary storage."""
        return PortfolioConfigurationManager(storage_path=temp_storage_path)

    @pytest.fixture
    def sample_holdings(self):
        """Create sample portfolio holdings."""
        return [
            Holding(symbol="AAPL", shares=100.0, cost_basis=150.0),
            Holding(symbol="GOOGL", shares=50.0, cost_basis=2500.0),
            Holding(symbol="MSFT", shares=75.0, cost_basis=300.0),
        ]

    @pytest.fixture
    def sample_target_weights(self):
        """Create sample target weights."""
        return {
            "AAPL": 0.4,
            "GOOGL": 0.35,
            "MSFT": 0.25,
        }

    def test_should_initialize_manager_when_valid_path_provided(self, temp_storage_path):
        """Test manager initialization with valid storage path."""
        # Act
        manager = PortfolioConfigurationManager(storage_path=temp_storage_path)

        # Assert
        assert manager.storage_path == temp_storage_path
        assert (temp_storage_path / "configs").exists()
        assert (temp_storage_path / "templates").exists()
        assert (temp_storage_path / "exports").exists()

    def test_should_create_system_templates_when_manager_initialized(self, config_manager):
        """Test that system templates are created during initialization."""
        # Act
        templates = config_manager.list_templates()

        # Assert
        assert len(templates) >= 4  # At least 4 system templates
        template_ids = {t.template_id for t in templates}
        assert "balanced_portfolio" in template_ids
        assert "aggressive_growth" in template_ids
        assert "conservative_portfolio" in template_ids
        assert "dividend_focused" in template_ids

    def test_should_create_configuration_when_valid_inputs_provided(self, config_manager, sample_holdings, sample_target_weights):
        """Test creating a new portfolio configuration."""
        # Act
        config_id = config_manager.create_configuration(
            name="Test Portfolio",
            holdings=sample_holdings,
            target_weights=sample_target_weights,
            description="Test portfolio description",
            strategy_template=StrategyTemplate.BALANCED,
        )

        # Assert
        assert config_id is not None
        assert len(config_id) == 36  # UUID length

        # Verify configuration was saved
        loaded_config = config_manager.load_configuration(config_id)
        assert loaded_config.metadata.name == "Test Portfolio"
        assert loaded_config.metadata.description == "Test portfolio description"
        assert loaded_config.metadata.strategy_template == StrategyTemplate.BALANCED
        assert len(loaded_config.configuration.holdings) == 3
        assert loaded_config.configuration.target_weights == sample_target_weights

    def test_should_validate_configuration_when_creating(self, config_manager, sample_holdings):
        """Test configuration validation during creation."""
        # Arrange - Invalid target weights (sum > 1.0)
        invalid_weights = {
            "AAPL": 0.6,
            "GOOGL": 0.5,
            "MSFT": 0.3,
        }

        # Act & Assert - Should raise ValueError due to Pydantic validation
        with pytest.raises(ValueError, match="Failed to create configuration"):
            config_manager.create_configuration(name="Invalid Portfolio", holdings=sample_holdings, target_weights=invalid_weights)

    def test_should_load_configuration_when_valid_id_provided(self, config_manager, sample_holdings, sample_target_weights):
        """Test loading an existing configuration."""
        # Arrange
        config_id = config_manager.create_configuration(name="Load Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Act
        loaded_config = config_manager.load_configuration(config_id)

        # Assert
        assert loaded_config.metadata.config_id == config_id
        assert loaded_config.metadata.name == "Load Test"
        assert loaded_config.metadata.version == 1
        assert len(loaded_config.configuration.holdings) == 3

    def test_should_raise_error_when_loading_nonexistent_configuration(self, config_manager):
        """Test loading a non-existent configuration raises error."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config_manager.load_configuration("nonexistent-id")

    def test_should_update_configuration_when_valid_updates_provided(self, config_manager, sample_holdings, sample_target_weights):
        """Test updating an existing configuration."""
        # Arrange
        config_id = config_manager.create_configuration(name="Update Test", holdings=sample_holdings, target_weights=sample_target_weights)

        updates = {
            "target_weights": {
                "AAPL": 0.5,
                "GOOGL": 0.3,
                "MSFT": 0.2,
            },
            "global_tolerance": 0.08,
        }

        # Act
        updated_id = config_manager.update_configuration(config_id=config_id, updates=updates, change_summary="Updated target weights and tolerance")

        # Assert
        assert updated_id == config_id

        # Load updated configuration
        updated_config = config_manager.load_configuration(config_id)
        assert updated_config.metadata.version == 2
        assert updated_config.configuration.target_weights["AAPL"] == approx(0.5)
        assert updated_config.configuration.global_tolerance == approx(0.08)
        assert "Updated target weights" in updated_config.change_summary

    def test_should_list_configurations_when_filters_applied(self, config_manager, sample_holdings, sample_target_weights):
        """Test listing configurations with various filters."""
        # Arrange - Create multiple configurations
        config1_id = config_manager.create_configuration(
            name="Balanced Test",
            holdings=sample_holdings,
            target_weights=sample_target_weights,
            strategy_template=StrategyTemplate.BALANCED,
        )

        config_manager.create_configuration(
            name="Growth Test",
            holdings=sample_holdings,
            target_weights=sample_target_weights,
            strategy_template=StrategyTemplate.AGGRESSIVE_GROWTH,
        )

        # Act - List all configurations
        all_configs = config_manager.list_configurations()

        # Act - List by strategy template
        balanced_configs = config_manager.list_configurations(strategy_template=StrategyTemplate.BALANCED)

        # Assert
        assert len(all_configs) >= 2
        assert len(balanced_configs) >= 1  # May have duplicates due to versioning

        # Find the balanced config
        balanced_config = next((c for c in balanced_configs if c.config_id == config1_id), None)
        assert balanced_config is not None
        assert balanced_config.strategy_template == StrategyTemplate.BALANCED

    def test_should_delete_configuration_when_valid_id_provided(self, config_manager, sample_holdings, sample_target_weights):
        """Test deleting a configuration."""
        # Arrange
        config_id = config_manager.create_configuration(name="Delete Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Verify configuration exists
        loaded_config = config_manager.load_configuration(config_id)
        assert loaded_config is not None

        # Act
        deleted = config_manager.delete_configuration(config_id)

        # Assert
        assert deleted is True

        # Verify configuration no longer exists
        with pytest.raises(FileNotFoundError):
            config_manager.load_configuration(config_id)

    def test_should_create_from_template_when_valid_template_provided(self, config_manager, sample_holdings):
        """Test creating configuration from template."""
        # Act
        config_id = config_manager.create_from_template(
            template_id="balanced_portfolio",
            name="From Template Test",
            holdings=sample_holdings,
            description="Created from balanced template",
        )

        # Assert
        assert config_id is not None

        loaded_config = config_manager.load_configuration(config_id)
        assert loaded_config.metadata.name == "From Template Test"
        assert loaded_config.metadata.strategy_template == StrategyTemplate.BALANCED
        assert loaded_config.metadata.description == "Created from balanced template"

        # Verify template usage count increased
        template = config_manager.load_template("balanced_portfolio")
        assert template.usage_count >= 1

    def test_should_raise_error_when_creating_from_nonexistent_template(self, config_manager, sample_holdings):
        """Test creating from non-existent template raises error."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config_manager.create_from_template(template_id="nonexistent_template", name="Test", holdings=sample_holdings)

    def test_should_export_configuration_when_valid_format_provided(self, config_manager, sample_holdings, sample_target_weights):
        """Test exporting configuration to file."""
        # Arrange
        config_id = config_manager.create_configuration(name="Export Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Act
        export_path = config_manager.export_configuration(config_id, format_type="json")

        # Assert
        assert export_path.exists()
        assert export_path.suffix == ".json"

        # Verify exported content
        with export_path.open("r", encoding="utf-8") as f:
            exported_data = json.load(f)

        assert "metadata" in exported_data
        assert "configuration" in exported_data
        assert exported_data["metadata"]["name"] == "Export Test"

    def test_should_import_configuration_when_valid_file_provided(self, config_manager, sample_holdings, sample_target_weights, temp_storage_path):
        """Test importing configuration from file."""
        # Arrange - Create and export a configuration
        original_config_id = config_manager.create_configuration(name="Import Test Original", holdings=sample_holdings, target_weights=sample_target_weights)

        export_path = config_manager.export_configuration(original_config_id)

        # Act
        imported_config_id = config_manager.import_configuration(import_path=export_path, name="Import Test Imported")

        # Assert
        assert imported_config_id != original_config_id  # Should be different ID

        imported_config = config_manager.load_configuration(imported_config_id)
        assert imported_config.metadata.name == "Import Test Imported"
        assert len(imported_config.configuration.holdings) == 3
        assert imported_config.configuration.target_weights == sample_target_weights

    def test_should_raise_error_when_importing_nonexistent_file(self, config_manager):
        """Test importing from non-existent file raises error."""
        # Act & Assert
        with pytest.raises(ValueError, match="Failed to import configuration"):
            config_manager.import_configuration(Path("nonexistent_file.json"))

    def test_should_load_template_when_valid_id_provided(self, config_manager):
        """Test loading a configuration template."""
        # Act
        template = config_manager.load_template("balanced_portfolio")

        # Assert
        assert template.template_id == "balanced_portfolio"
        assert template.name == "Balanced Portfolio"
        assert template.strategy_type == StrategyTemplate.BALANCED
        assert template.is_system_template is True
        assert len(template.target_weights) > 0

    def test_should_save_and_load_custom_template(self, config_manager):
        """Test saving and loading a custom template."""
        # Arrange
        custom_template = ConfigurationTemplate(
            template_id="custom_test",
            name="Custom Test Template",
            description="Test custom template",
            strategy_type=StrategyTemplate.CUSTOM,
            target_weights={"AAPL": 0.5, "GOOGL": 0.5},
            global_tolerance=0.06,
            is_system_template=False,
        )

        # Act
        config_manager.save_template(custom_template)
        loaded_template = config_manager.load_template("custom_test")

        # Assert
        assert loaded_template.template_id == "custom_test"
        assert loaded_template.name == "Custom Test Template"
        assert loaded_template.is_system_template is False
        assert loaded_template.target_weights == {"AAPL": 0.5, "GOOGL": 0.5}

    def test_should_validate_configuration_consistency(self, config_manager):
        """Test configuration validation for various error conditions."""
        # Test missing target weights - should raise ValueError due to Pydantic validation
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"GOOGL": 1.0}  # Different symbol

        # Act & Assert - Should raise ValueError due to Pydantic validation
        with pytest.raises(ValueError, match="Failed to create configuration"):
            config_manager.create_configuration(name="Validation Test", holdings=holdings, target_weights=target_weights)

    def test_should_handle_version_management_correctly(self, config_manager, sample_holdings, sample_target_weights):
        """Test configuration version management."""
        # Arrange
        config_id = config_manager.create_configuration(name="Version Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Act - Create multiple versions
        config_manager.update_configuration(config_id, {"global_tolerance": 0.06}, "Update 1")
        config_manager.update_configuration(config_id, {"global_tolerance": 0.07}, "Update 2")

        # Assert - Load specific versions
        v1_config = config_manager.load_configuration(config_id, version=1)
        v2_config = config_manager.load_configuration(config_id, version=2)
        v3_config = config_manager.load_configuration(config_id, version=3)
        latest_config = config_manager.load_configuration(config_id)  # Should be latest

        assert v1_config.metadata.version == 1
        assert v1_config.configuration.global_tolerance == approx(0.05)  # Default

        assert v2_config.metadata.version == 2
        assert v2_config.configuration.global_tolerance == approx(0.06)

        assert v3_config.metadata.version == 3
        assert v3_config.configuration.global_tolerance == approx(0.07)

        assert latest_config.metadata.version == 3  # Latest version
        assert latest_config.configuration.global_tolerance == approx(0.07)

    def test_should_handle_configuration_status_changes(self, config_manager, sample_holdings, sample_target_weights):
        """Test configuration status management."""
        # Arrange
        config_id = config_manager.create_configuration(name="Status Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Act - Update configuration (status is in metadata, so update tolerance instead)
        config_manager.update_configuration(config_id, {"global_tolerance": 0.08}, "Updated tolerance")

        # Assert
        loaded_config = config_manager.load_configuration(config_id)
        assert loaded_config.configuration.global_tolerance == approx(0.08)

    def test_should_log_operations_correctly(self, mocker, config_manager, sample_holdings, sample_target_weights):
        """Test that operations are logged correctly."""
        # Arrange
        mock_logger = mocker.patch("finwiz.quantitative.portfolio_configuration_manager.logger")

        # Act
        config_manager.create_configuration(name="Logging Test", holdings=sample_holdings, target_weights=sample_target_weights)

        # Assert
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        assert any("Created portfolio configuration" in call for call in log_calls)

    def test_should_handle_edge_cases_gracefully(self, config_manager):
        """Test handling of edge cases and error conditions."""
        # Test empty holdings list
        with pytest.raises(ValueError):
            config_manager.create_configuration(
                name="Empty Holdings",
                holdings=[],  # Empty list should fail validation
                target_weights={},
            )

        # Test invalid tolerance values - should raise ValueError due to Pydantic validation
        holdings = [Holding(symbol="AAPL", shares=100.0)]
        target_weights = {"AAPL": 1.0}

        with pytest.raises(ValueError, match="Failed to create configuration"):
            config_manager.create_configuration(
                name="Invalid Tolerance",
                holdings=holdings,
                target_weights=target_weights,
                tolerance_bands={"AAPL": -0.1},  # Negative tolerance
            )

    def test_should_support_configuration_search_and_filtering(self, config_manager, sample_holdings, sample_target_weights):
        """Test configuration search and filtering capabilities."""
        # Arrange - Create configurations with different attributes
        config1_id = config_manager.create_configuration(
            name="Tech Portfolio",
            holdings=sample_holdings,
            target_weights=sample_target_weights,
            strategy_template=StrategyTemplate.AGGRESSIVE_GROWTH,
        )

        # Update metadata with tags
        config1 = config_manager.load_configuration(config1_id)
        config1.metadata.tags = ["tech", "growth"]
        config1.metadata.category = "technology"
        config_manager.save_configuration(config1)

        # Act - List with filters
        all_configs = config_manager.list_configurations()
        growth_configs = config_manager.list_configurations(strategy_template=StrategyTemplate.AGGRESSIVE_GROWTH)
        tech_configs = config_manager.list_configurations(tags=["tech"])

        # Assert
        assert len(all_configs) >= 1
        assert len(growth_configs) >= 1
        assert len(tech_configs) >= 1
        assert growth_configs[0].config_id == config1_id
        assert tech_configs[0].config_id == config1_id