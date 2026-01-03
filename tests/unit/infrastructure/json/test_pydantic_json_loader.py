"""
Unit tests for Pydantic JSON loader module.

Tests for loading, validating, and saving JSON data with Pydantic model validation.
"""

import json
import tempfile
from pathlib import Path

import pytest
from faker import Faker
from pydantic import BaseModel, Field, ValidationError

from finwiz.infrastructure.json.pydantic_json_loader import (
    PydanticValidationError,
    load_json_dict_with_validation,
    load_json_string_with_validation,
    load_json_with_validation,
    save_json_with_validation,
    validate_crew_output,
)


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""

    name: str = Field(..., min_length=1)
    value: int = Field(..., ge=0)
    optional_field: str | None = None


class NestedModel(BaseModel):
    """Nested Pydantic model for testing."""

    id: str
    sample: SampleModel


class TestPydanticValidationError:
    """Test PydanticValidationError exception class."""

    def test_should_initialize_with_message_and_errors(self):
        """Test exception initialization with message and validation errors."""
        errors = [{"loc": ("name",), "msg": "required field", "type": "missing"}]
        exception = PydanticValidationError("Validation failed", validation_errors=errors)

        assert str(exception) == "Validation failed"
        assert exception.validation_errors == errors

    def test_should_initialize_with_message_only(self):
        """Test exception initialization with message only."""
        exception = PydanticValidationError("Simple error")

        assert str(exception) == "Simple error"
        assert exception.validation_errors == []


class TestLoadJsonWithValidation:
    """Test load_json_with_validation function."""

    @pytest.fixture
    def fake(self):
        """Provide Faker instance."""
        return Faker()

    @pytest.fixture
    def temp_json_file(self, fake):
        """Create a temporary JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            data = {"name": fake.name(), "value": fake.random_int(min=0, max=100)}
            json.dump(data, f)
            return Path(f.name), data

    def test_should_load_and_validate_json_file(self, temp_json_file):
        """Test loading and validating a valid JSON file."""
        file_path, expected_data = temp_json_file

        result = load_json_with_validation(file_path, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.name == expected_data["name"]
        assert result.value == expected_data["value"]

    def test_should_raise_file_not_found_for_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError, match="JSON file not found"):
            load_json_with_validation("/nonexistent/path.json", SampleModel)

    def test_should_raise_json_decode_error_for_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for malformed JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            load_json_with_validation(invalid_file, SampleModel)

    def test_should_raise_validation_error_in_strict_mode(self, tmp_path):
        """Test that PydanticValidationError is raised for invalid data in strict mode."""
        invalid_file = tmp_path / "invalid_data.json"
        invalid_file.write_text('{"name": "", "value": -1}', encoding="utf-8")

        with pytest.raises(PydanticValidationError, match="Pydantic validation failed"):
            load_json_with_validation(invalid_file, SampleModel, strict=True)

    def test_should_return_model_construct_in_non_strict_mode(self, tmp_path):
        """Test that model_construct is used for invalid data in non-strict mode."""
        invalid_file = tmp_path / "invalid_data.json"
        # Use valid data but with extra fields that would fail strict validation
        invalid_file.write_text('{"name": "", "value": -1}', encoding="utf-8")

        # In non-strict mode, it should use model_construct
        result = load_json_with_validation(invalid_file, SampleModel, strict=False)

        # model_construct bypasses validation
        assert isinstance(result, SampleModel)

    def test_should_accept_string_path(self, temp_json_file):
        """Test that string paths are accepted."""
        file_path, expected_data = temp_json_file

        result = load_json_with_validation(str(file_path), SampleModel)

        assert isinstance(result, SampleModel)
        assert result.name == expected_data["name"]


class TestLoadJsonStringWithValidation:
    """Test load_json_string_with_validation function."""

    def test_should_validate_json_string(self, fake):
        """Test validating a JSON string."""
        fake = Faker()
        json_string = json.dumps({"name": fake.name(), "value": 42})

        result = load_json_string_with_validation(json_string, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.value == 42

    def test_should_raise_for_invalid_json_string(self):
        """Test that JSONDecodeError is raised for invalid JSON string."""
        with pytest.raises(json.JSONDecodeError):
            load_json_string_with_validation("{ invalid }", SampleModel)

    def test_should_raise_validation_error_for_invalid_data(self):
        """Test that PydanticValidationError is raised for invalid data."""
        json_string = '{"name": "", "value": -1}'

        with pytest.raises(PydanticValidationError):
            load_json_string_with_validation(json_string, SampleModel, strict=True)


class TestLoadJsonDictWithValidation:
    """Test load_json_dict_with_validation function."""

    def test_should_validate_dict_data(self, fake):
        """Test validating dictionary data."""
        fake = Faker()
        data = {"name": fake.name(), "value": 50}

        result = load_json_dict_with_validation(data, SampleModel)

        assert isinstance(result, SampleModel)
        assert result.value == 50

    def test_should_raise_validation_error_for_invalid_dict(self):
        """Test that PydanticValidationError is raised for invalid dict."""
        invalid_data = {"name": "", "value": -1}

        with pytest.raises(PydanticValidationError):
            load_json_dict_with_validation(invalid_data, SampleModel, strict=True)

    def test_should_handle_nested_models(self, fake):
        """Test validating nested model data."""
        fake = Faker()
        data = {"id": fake.uuid4(), "sample": {"name": fake.name(), "value": 100}}

        result = load_json_dict_with_validation(data, NestedModel)

        assert isinstance(result, NestedModel)
        assert isinstance(result.sample, SampleModel)
        assert result.sample.value == 100


class TestSaveJsonWithValidation:
    """Test save_json_with_validation function."""

    def test_should_save_validated_model_to_file(self, tmp_path, fake):
        """Test saving a validated model to JSON file."""
        fake = Faker()
        model = SampleModel(name=fake.name(), value=75)
        output_path = tmp_path / "output.json"

        save_json_with_validation(output_path, model)

        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["name"] == model.name
        assert saved_data["value"] == model.value

    def test_should_create_parent_directories(self, tmp_path, fake):
        """Test that parent directories are created if they don't exist."""
        fake = Faker()
        model = SampleModel(name=fake.name(), value=25)
        nested_path = tmp_path / "nested" / "deep" / "output.json"

        save_json_with_validation(nested_path, model)

        assert nested_path.exists()

    def test_should_handle_nested_models_on_save(self, tmp_path, fake):
        """Test saving nested models."""
        fake = Faker()
        model = NestedModel(id=fake.uuid4(), sample=SampleModel(name=fake.name(), value=10))
        output_path = tmp_path / "nested_output.json"

        save_json_with_validation(output_path, model)

        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            saved_data = json.load(f)
        assert "sample" in saved_data
        assert saved_data["sample"]["value"] == 10


class TestValidateCrewOutput:
    """Test validate_crew_output function."""

    def test_should_validate_crew_output_dict(self, fake):
        """Test validating crew output from dictionary."""
        fake = Faker()
        crew_output = {"name": fake.name(), "value": 80}

        result = validate_crew_output(crew_output, SampleModel, "test_crew")

        assert isinstance(result, SampleModel)
        assert result.value == 80

    def test_should_validate_crew_output_string(self, fake):
        """Test validating crew output from JSON string."""
        fake = Faker()
        crew_output = json.dumps({"name": fake.name(), "value": 60})

        result = validate_crew_output(crew_output, SampleModel, "test_crew")

        assert isinstance(result, SampleModel)
        assert result.value == 60

    def test_should_handle_pydantic_model_input(self, fake):
        """Test that pydantic model input passes through."""
        fake = Faker()
        model = SampleModel(name=fake.name(), value=45)

        result = validate_crew_output(model, SampleModel, "test_crew")

        # Should return the same model or validate it
        assert isinstance(result, SampleModel)

    def test_should_raise_for_invalid_crew_output(self):
        """Test that PydanticValidationError is raised for invalid crew output."""
        invalid_output = {"name": "", "value": -5}

        with pytest.raises(PydanticValidationError):
            validate_crew_output(invalid_output, SampleModel, "test_crew")

    def test_should_handle_none_values_gracefully(self):
        """Test handling of None values in crew output."""
        # Test with optional field
        crew_output = {"name": "Test", "value": 10, "optional_field": None}

        result = validate_crew_output(crew_output, SampleModel, "test_crew")

        assert result.optional_field is None
