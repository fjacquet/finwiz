"""Tests for template_validator module."""

from pathlib import Path

import pytest
import yaml


class TestTemplateVariableValidator:
    """Tests for TemplateVariableValidator class."""

    def test_init_default_crews_dir(self, mocker):
        """Test initialization with default crews directory."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        validator = TemplateVariableValidator()
        assert validator.crews_dir.name == "crews"

    def test_init_custom_crews_dir(self, tmp_path):
        """Test initialization with custom crews directory."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        custom_dir = tmp_path / "custom_crews"
        custom_dir.mkdir()
        validator = TemplateVariableValidator(crews_dir=custom_dir)
        assert validator.crews_dir == custom_dir

    def test_scan_task_configs_extracts_variables(self, tmp_path):
        """Test scanning task configs extracts template variables."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        # Create a mock tasks.yaml
        tasks_yaml = tmp_path / "tasks.yaml"
        tasks_content = {
            "analysis_task": {
                "description": "Analyze {ticker} for {asset_class} type",
                "expected_output": "Analysis for {ticker}",
            },
            "report_task": {
                "description": "Generate report for {company_name}",
            },
        }
        tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(tasks_yaml)

        assert "ticker" in variables
        assert "asset_class" in variables
        assert "company_name" in variables
        assert len(variables) == 3

    def test_scan_task_configs_empty_file(self, tmp_path):
        """Test scanning empty task config returns empty set."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        tasks_yaml = tmp_path / "tasks.yaml"
        tasks_yaml.write_text("")

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(tasks_yaml)

        assert variables == set()

    def test_scan_task_configs_no_variables(self, tmp_path):
        """Test scanning task config with no variables."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        tasks_yaml = tmp_path / "tasks.yaml"
        tasks_content = {
            "task": {
                "description": "No template variables here",
            }
        }
        tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(tasks_yaml)

        assert variables == set()

    def test_scan_task_configs_nested_structure(self, tmp_path):
        """Test scanning nested task config structure."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        tasks_yaml = tmp_path / "tasks.yaml"
        tasks_content = {
            "task": {
                "nested": {
                    "deep": {
                        "text": "Find {variable_one} and {variable_two}",
                    }
                },
                "list_items": [
                    "Item with {list_var}",
                    {"nested_list": "Value {nested_list_var}"},
                ],
            }
        }
        tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(tasks_yaml)

        assert "variable_one" in variables
        assert "variable_two" in variables
        assert "list_var" in variables
        assert "nested_list_var" in variables

    def test_scan_task_configs_handles_error(self, tmp_path):
        """Test scanning handles file read errors gracefully."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        non_existent = tmp_path / "nonexistent.yaml"

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(non_existent)

        assert variables == set()

    def test_scan_task_configs_invalid_yaml(self, tmp_path):
        """Test scanning handles invalid YAML gracefully."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        tasks_yaml = tmp_path / "tasks.yaml"
        tasks_yaml.write_text("invalid: yaml: content: [")

        validator = TemplateVariableValidator()
        variables = validator.scan_task_configs(tasks_yaml)

        assert variables == set()

    def test_document_crew_with_variables(self, tmp_path):
        """Test documenting a crew with template variables."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        # Create crew directory structure
        crew_dir = tmp_path / "stock_crew"
        config_dir = crew_dir / "config"
        config_dir.mkdir(parents=True)

        tasks_yaml = config_dir / "tasks.yaml"
        tasks_content = {
            "task": {"description": "Analyze {ticker}"},
        }
        tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator()
        info = validator.document_crew(crew_dir)

        assert len(info) == 1
        assert "stock_crew" in info[0]
        assert "ticker" in info[0]

    def test_document_crew_no_tasks_yaml(self, tmp_path):
        """Test documenting a crew without tasks.yaml."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        crew_dir = tmp_path / "crew_no_tasks"
        crew_dir.mkdir()

        validator = TemplateVariableValidator()
        info = validator.document_crew(crew_dir)

        assert info == []

    def test_document_crew_no_variables(self, tmp_path):
        """Test documenting a crew with no template variables."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        crew_dir = tmp_path / "simple_crew"
        config_dir = crew_dir / "config"
        config_dir.mkdir(parents=True)

        tasks_yaml = config_dir / "tasks.yaml"
        tasks_content = {"task": {"description": "No variables"}}
        tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator()
        info = validator.document_crew(crew_dir)

        assert info == []

    def test_document_all_crews(self, tmp_path):
        """Test documenting all crews in directory."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        # Create two crew directories
        for crew_name in ["crew_a", "crew_b"]:
            crew_dir = tmp_path / crew_name
            config_dir = crew_dir / "config"
            config_dir.mkdir(parents=True)

            tasks_yaml = config_dir / "tasks.yaml"
            tasks_content = {"task": {"description": f"Analyze {{var_{crew_name}}}"}}
            tasks_yaml.write_text(yaml.dump(tasks_content))

        validator = TemplateVariableValidator(crews_dir=tmp_path)
        success, info = validator.document_all_crews()

        assert success is True
        assert len(info) == 2

    def test_document_all_crews_skips_pycache(self, tmp_path):
        """Test documenting crews skips __pycache__ directories."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        # Create pycache and hidden directories
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / ".hidden").mkdir()

        # Create one real crew
        crew_dir = tmp_path / "real_crew"
        config_dir = crew_dir / "config"
        config_dir.mkdir(parents=True)
        tasks_yaml = config_dir / "tasks.yaml"
        tasks_yaml.write_text(yaml.dump({"task": {"desc": "{var}"}}))

        validator = TemplateVariableValidator(crews_dir=tmp_path)
        success, info = validator.document_all_crews()

        assert success is True
        assert len(info) == 1
        assert "real_crew" in info[0]

    def test_document_all_crews_nonexistent_dir(self, tmp_path):
        """Test documenting crews with nonexistent directory."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        nonexistent = tmp_path / "nonexistent"

        validator = TemplateVariableValidator(crews_dir=nonexistent)
        success, info = validator.document_all_crews()

        assert success is True
        assert info == []

    def test_document_all_crews_empty_dir(self, tmp_path):
        """Test documenting crews with empty directory."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        validator = TemplateVariableValidator(crews_dir=tmp_path)
        success, info = validator.document_all_crews()

        assert success is True
        assert info == []

    def test_validate_at_startup(self, tmp_path, mocker):
        """Test validate_at_startup logs information."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        # Create a crew with variables
        crew_dir = tmp_path / "test_crew"
        config_dir = crew_dir / "config"
        config_dir.mkdir(parents=True)
        tasks_yaml = config_dir / "tasks.yaml"
        tasks_yaml.write_text(yaml.dump({"task": {"desc": "{ticker}"}}))

        mock_logger = mocker.patch("finwiz.validation.template_validator.logger")

        validator = TemplateVariableValidator(crews_dir=tmp_path)
        validator.validate_at_startup()

        # Should log scanning message
        mock_logger.info.assert_called()

    def test_validate_at_startup_no_variables(self, tmp_path, mocker):
        """Test validate_at_startup with no variables logs appropriate message."""
        from finwiz.validation.template_validator import TemplateVariableValidator

        mock_logger = mocker.patch("finwiz.validation.template_validator.logger")

        validator = TemplateVariableValidator(crews_dir=tmp_path)
        validator.validate_at_startup()

        # Should log no variables found
        calls = [str(c) for c in mock_logger.info.call_args_list]
        assert any("No template variables" in str(c) for c in calls)


class TestValidateTemplateVariablesAtStartup:
    """Tests for validate_template_variables_at_startup function."""

    def test_validate_template_variables_at_startup(self, mocker):
        """Test the convenience function."""
        from finwiz.validation.template_validator import (
            validate_template_variables_at_startup,
        )

        mock_validator = mocker.patch(
            "finwiz.validation.template_validator.TemplateVariableValidator"
        )

        validate_template_variables_at_startup()

        mock_validator.assert_called_once()
        mock_validator.return_value.validate_at_startup.assert_called_once()


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test ConfigurationError is an Exception."""
        from finwiz.validation.template_validator import ConfigurationError

        error = ConfigurationError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"
