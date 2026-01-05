"""
Unit tests for template variable validator.

Tests for the TemplateVariableValidator class and related functions.
"""

import pytest
import yaml
from faker import Faker

from finwiz.validation.template import (
    ConfigurationError,
    TemplateVariableValidator,
    validate_template_variables_at_startup,
)


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_should_be_exception(self):
        """Test ConfigurationError is an Exception."""
        error = ConfigurationError("test message")

        assert isinstance(error, Exception)
        assert str(error) == "test message"


class TestTemplateVariableValidator:
    """Tests for TemplateVariableValidator class."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def temp_crews_dir(self, tmp_path):
        """Create temporary crews directory."""
        crews_dir = tmp_path / "crews"
        crews_dir.mkdir()
        return crews_dir

    @pytest.fixture
    def validator(self, temp_crews_dir):
        """Create TemplateVariableValidator instance."""
        return TemplateVariableValidator(crews_dir=temp_crews_dir)

    def test_should_initialize_with_default_dir(self):
        """Test initialization with default crews directory."""
        validator = TemplateVariableValidator()

        assert validator.crews_dir is not None
        assert validator.crews_dir.name == "crews"

    def test_should_initialize_with_custom_dir(self, temp_crews_dir):
        """Test initialization with custom crews directory."""
        validator = TemplateVariableValidator(crews_dir=temp_crews_dir)

        assert validator.crews_dir == temp_crews_dir


class TestScanTaskConfigs:
    """Tests for scan_task_configs method."""

    @pytest.fixture
    def temp_crews_dir(self, tmp_path):
        """Create temporary crews directory."""
        crews_dir = tmp_path / "crews"
        crews_dir.mkdir()
        return crews_dir

    @pytest.fixture
    def validator(self, temp_crews_dir):
        """Create TemplateVariableValidator instance."""
        return TemplateVariableValidator(crews_dir=temp_crews_dir)

    def test_should_extract_single_variable(self, validator, tmp_path):
        """Test extracting single template variable."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_config = {"task1": {"description": "Analyze {ticker} stock"}}
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.scan_task_configs(tasks_file)

        assert "ticker" in result

    def test_should_extract_multiple_variables(self, validator, tmp_path):
        """Test extracting multiple template variables."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_config = {"task1": {"description": "Analyze {ticker} of type {asset_class}"}}
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.scan_task_configs(tasks_file)

        assert "ticker" in result
        assert "asset_class" in result

    def test_should_extract_from_nested_structures(self, validator, tmp_path):
        """Test extracting variables from nested YAML."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_config = {"task1": {"description": "Analyze {ticker}", "nested": {"deep": {"value": "Process {data_type}"}}}}
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.scan_task_configs(tasks_file)

        assert "ticker" in result
        assert "data_type" in result

    def test_should_extract_from_lists(self, validator, tmp_path):
        """Test extracting variables from list items."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_config = {"task1": {"items": ["Process {item1}", "Handle {item2}"]}}
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.scan_task_configs(tasks_file)

        assert "item1" in result
        assert "item2" in result

    def test_should_return_empty_for_no_variables(self, validator, tmp_path):
        """Test returns empty set when no variables found."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_config = {"task1": {"description": "No template variables here"}}
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.scan_task_configs(tasks_file)

        assert result == set()

    def test_should_return_empty_for_empty_file(self, validator, tmp_path):
        """Test returns empty set for empty YAML file."""
        tasks_file = tmp_path / "tasks.yaml"
        tasks_file.write_text("")

        result = validator.scan_task_configs(tasks_file)

        assert result == set()

    def test_should_return_empty_for_nonexistent_file(self, validator, tmp_path):
        """Test returns empty set for nonexistent file."""
        tasks_file = tmp_path / "nonexistent.yaml"

        result = validator.scan_task_configs(tasks_file)

        assert result == set()


class TestDocumentCrew:
    """Tests for document_crew method."""

    @pytest.fixture
    def temp_crews_dir(self, tmp_path):
        """Create temporary crews directory."""
        crews_dir = tmp_path / "crews"
        crews_dir.mkdir()
        return crews_dir

    @pytest.fixture
    def validator(self, temp_crews_dir):
        """Create TemplateVariableValidator instance."""
        return TemplateVariableValidator(crews_dir=temp_crews_dir)

    def test_should_document_crew_with_variables(self, validator, temp_crews_dir):
        """Test documenting crew with template variables."""
        crew_dir = temp_crews_dir / "stock_crew"
        crew_dir.mkdir()
        config_dir = crew_dir / "config"
        config_dir.mkdir()

        tasks_config = {"analysis_task": {"description": "Analyze {ticker} stock"}}
        tasks_file = config_dir / "tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.document_crew(crew_dir)

        assert len(result) == 1
        assert "stock_crew" in result[0]
        assert "ticker" in result[0]

    def test_should_return_empty_for_no_tasks_yaml(self, validator, temp_crews_dir):
        """Test returns empty list when no tasks.yaml exists."""
        crew_dir = temp_crews_dir / "empty_crew"
        crew_dir.mkdir()

        result = validator.document_crew(crew_dir)

        assert result == []

    def test_should_return_empty_for_no_variables(self, validator, temp_crews_dir):
        """Test returns empty list when no template variables."""
        crew_dir = temp_crews_dir / "static_crew"
        crew_dir.mkdir()
        config_dir = crew_dir / "config"
        config_dir.mkdir()

        tasks_config = {"task": {"description": "Static task with no variables"}}
        tasks_file = config_dir / "tasks.yaml"
        with open(tasks_file, "w") as f:
            yaml.dump(tasks_config, f)

        result = validator.document_crew(crew_dir)

        assert result == []


class TestDocumentAllCrews:
    """Tests for document_all_crews method."""

    @pytest.fixture
    def temp_crews_dir(self, tmp_path):
        """Create temporary crews directory."""
        crews_dir = tmp_path / "crews"
        crews_dir.mkdir()
        return crews_dir

    @pytest.fixture
    def validator(self, temp_crews_dir):
        """Create TemplateVariableValidator instance."""
        return TemplateVariableValidator(crews_dir=temp_crews_dir)

    def test_should_document_all_crews(self, validator, temp_crews_dir):
        """Test documenting all crews in directory."""
        # Create two crew directories
        for crew_name in ["stock_crew", "etf_crew"]:
            crew_dir = temp_crews_dir / crew_name
            crew_dir.mkdir()
            config_dir = crew_dir / "config"
            config_dir.mkdir()

            tasks_config = {"task": {"description": f"Process {{ticker}} for {crew_name}"}}
            tasks_file = config_dir / "tasks.yaml"
            with open(tasks_file, "w") as f:
                yaml.dump(tasks_config, f)

        success, info = validator.document_all_crews()

        assert success is True
        assert len(info) == 2

    def test_should_skip_pycache_directories(self, validator, temp_crews_dir):
        """Test skips __pycache__ directories."""
        # Create __pycache__ directory
        pycache_dir = temp_crews_dir / "__pycache__"
        pycache_dir.mkdir()

        success, info = validator.document_all_crews()

        assert success is True
        assert "__pycache__" not in str(info)

    def test_should_skip_hidden_directories(self, validator, temp_crews_dir):
        """Test skips hidden directories."""
        # Create hidden directory
        hidden_dir = temp_crews_dir / ".hidden"
        hidden_dir.mkdir()

        success, info = validator.document_all_crews()

        assert success is True
        assert ".hidden" not in str(info)

    def test_should_skip_files(self, validator, temp_crews_dir):
        """Test skips regular files."""
        # Create a file
        (temp_crews_dir / "not_a_crew.py").write_text("# file")

        success, info = validator.document_all_crews()

        assert success is True
        assert "not_a_crew" not in str(info)

    def test_should_handle_nonexistent_directory(self, tmp_path):
        """Test handles nonexistent crews directory."""
        validator = TemplateVariableValidator(crews_dir=tmp_path / "nonexistent")

        success, info = validator.document_all_crews()

        assert success is True
        assert info == []


class TestValidateAtStartup:
    """Tests for validate_at_startup method."""

    @pytest.fixture
    def temp_crews_dir(self, tmp_path):
        """Create temporary crews directory."""
        crews_dir = tmp_path / "crews"
        crews_dir.mkdir()
        return crews_dir

    @pytest.fixture
    def validator(self, temp_crews_dir):
        """Create TemplateVariableValidator instance."""
        return TemplateVariableValidator(crews_dir=temp_crews_dir)

    def test_should_log_info_with_crews(self, validator, temp_crews_dir):
        """Test logs info when crews have variables."""
        crew_dir = temp_crews_dir / "stock_crew"
        crew_dir.mkdir()
        config_dir = crew_dir / "config"
        config_dir.mkdir()

        tasks_config = {"task": {"description": "Analyze {ticker}"}}
        with open(config_dir / "tasks.yaml", "w") as f:
            yaml.dump(tasks_config, f)

        # Should not raise
        validator.validate_at_startup()

    def test_should_log_info_without_crews(self, validator):
        """Test logs info when no crews found."""
        # Should not raise
        validator.validate_at_startup()


class TestValidateTemplateVariablesAtStartup:
    """Tests for validate_template_variables_at_startup function."""

    def test_should_run_without_error(self, mocker):
        """Test function runs without error."""
        # Mock the validator to avoid file system access
        mock_validator = mocker.MagicMock()
        mocker.patch(
            "finwiz.validation.template.TemplateVariableValidator",
            return_value=mock_validator,
        )

        # Should not raise
        validate_template_variables_at_startup()

        mock_validator.validate_at_startup.assert_called_once()
