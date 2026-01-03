"""
Unit tests for YAML configuration loader.

Tests for loading and injecting guidelines into YAML configurations.
"""

import pytest
from pathlib import Path
from finwiz.config.loader import load_yaml_config, load_config_with_guidelines, _get_config_path


class TestGetConfigPath:
    """Test _get_config_path utility function."""

    def test_should_return_valid_path(self):
        """Test that config path is constructed correctly."""
        path = _get_config_path("stock_crew/config/agents.yaml")

        assert isinstance(path, Path)
        assert "stock_crew" in str(path)
        assert "agents.yaml" in str(path)
        assert "crews" in str(path)

    def test_should_handle_nested_paths(self):
        """Test that nested config paths work."""
        path = _get_config_path("stock_crew/config/tasks.yaml")

        assert "stock_crew" in str(path)
        assert "config" in str(path)
        assert "tasks.yaml" in str(path)


class TestLoadYamlConfig:
    """Test loading YAML configuration files."""

    def test_should_load_valid_yaml(self):
        """Test loading a valid YAML configuration file."""
        # Use an actual crew config that exists
        config = load_yaml_config("stock_crew/config/agents.yaml")

        assert isinstance(config, dict)
        assert len(config) > 0

    def test_should_raise_file_not_found_for_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_yaml_config("nonexistent_crew/config/agents.yaml")

        assert "Config file not found" in str(exc_info.value)

    def test_should_raise_value_error_for_empty_file(self, tmp_path, mocker):
        """Test that ValueError is raised for empty YAML files."""
        # Create an empty YAML file
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("", encoding="utf-8")

        # Mock _get_config_path to return our temp file
        mocker.patch(
            "finwiz.config.loader._get_config_path",
            return_value=empty_yaml,
        )

        with pytest.raises(ValueError) as exc_info:
            load_yaml_config("test.yaml")

        assert "empty or not a valid dictionary" in str(exc_info.value)


class TestLoadConfigWithGuidelines:
    """Test loading config with guidelines injection."""

    def test_should_load_and_inject_guidelines(self, mocker, tmp_path):
        """Test that guidelines are injected into agent backstories."""
        # Mock the guidelines file
        guidelines_content = "## Research Guidelines\nAlways verify sources."
        mocker.patch(
            "builtins.open",
            side_effect=[
                # First call: load agents.yaml
                mocker.mock_open(read_data="analyst:\n  backstory: 'Analyze stocks'")(),
                # Second call: load guidelines
                mocker.mock_open(read_data=guidelines_content)(),
            ],
        )

        config = load_config_with_guidelines("stock_crew/config/agents.yaml")

        assert isinstance(config, dict)
        assert "analyst" in config

    def test_should_raise_file_not_found_for_missing_agents(self):
        """Test that FileNotFoundError is raised for missing agent config."""
        with pytest.raises(FileNotFoundError):
            load_config_with_guidelines("nonexistent_crew/config/agents.yaml")
