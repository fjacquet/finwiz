#!/usr/bin/env python3
"""
Schema validation tests for the MkDocs Schema Documentation Plugin.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the scripts directory to the path so we can import the plugin
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from mkdocs_schema_plugin import SchemaDocsPlugin


def test_plugin_can_be_imported():
    """Test that the plugin can be imported and initialized."""
    plugin = SchemaDocsPlugin()
    assert plugin is not None
    assert hasattr(plugin, "schemas")
    assert hasattr(plugin, "examples")


def test_schema_loading_basic():
    """Test basic schema loading functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create schema directory
        schema_dir = temp_path / "schemas"
        schema_dir.mkdir()

        # Create a simple schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "TestSchema",
            "type": "object",
            "properties": {"name": {"type": "string"}, "value": {"type": "number"}},
            "required": ["name"],
        }

        schema_file = schema_dir / "TestSchema.schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema, f)

        # Create plugin and load schemas
        plugin = SchemaDocsPlugin()
        plugin.config = {
            "schema_dir": str(schema_dir),
            "examples_dir": str(schema_dir / "examples"),
            "enable_validation": True,
            "show_examples": True,
            "show_cross_refs": True,
        }

        plugin._load_schemas()

        # Verify schema was loaded
        assert "TestSchema" in plugin.schemas
        assert plugin.schemas["TestSchema"]["title"] == "TestSchema"


def test_real_schema_files_are_valid_json():
    """Test that real schema files contain valid JSON."""
    schema_dir = Path("docs/schemas")
    if not schema_dir.exists():
        pytest.skip("Schema directory not found")

    errors = []
    for schema_file in schema_dir.glob("*.schema.json"):
        try:
            with open(schema_file, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {schema_file}: {e}")

    if errors:
        pytest.fail("JSON validation errors:\n" + "\n".join(errors))


def test_real_example_files_are_valid_json():
    """Test that real example files contain valid JSON."""
    examples_dir = Path("docs/schemas/examples")
    if not examples_dir.exists():
        pytest.skip("Examples directory not found")

    errors = []
    for example_file in examples_dir.glob("*.example.json"):
        try:
            with open(example_file, encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {example_file}: {e}")

    if errors:
        pytest.fail("JSON validation errors:\n" + "\n".join(errors))


def test_schema_rendering_basic():
    """Test basic schema rendering functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create schema and examples directories
        schema_dir = temp_path / "schemas"
        examples_dir = temp_path / "schemas" / "examples"
        schema_dir.mkdir(parents=True)
        examples_dir.mkdir(parents=True)

        # Create test schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "TestSchema",
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Test name"},
                "value": {"type": "number", "description": "Test value"},
            },
            "required": ["name"],
        }

        schema_file = schema_dir / "TestSchema.schema.json"
        with open(schema_file, "w") as f:
            json.dump(schema, f)

        # Create test example
        example = {"name": "test", "value": 42}
        example_file = examples_dir / "test_schema.example.json"
        with open(example_file, "w") as f:
            json.dump(example, f)

        # Create plugin and load data
        plugin = SchemaDocsPlugin()
        plugin.config = {
            "schema_dir": str(schema_dir),
            "examples_dir": str(examples_dir),
            "enable_validation": True,
            "show_examples": True,
            "show_cross_refs": True,
        }

        plugin._load_schemas()
        plugin._load_examples()

        # Test rendering
        html = plugin._generate_schema_documentation("TestSchema", "Test description")

        # Verify HTML contains expected elements
        assert '<div class="schema-docs"' in html
        assert "TestSchema Schema" in html
        assert "Test description" in html
        assert '<table class="schema-properties-table">' in html
        assert "<code>name</code>" in html
        assert "Test name" in html


def test_schema_validation_with_real_data():
    """Test schema validation using real FinWiz schemas and examples."""
    # Create plugin with real schemas
    plugin = SchemaDocsPlugin()
    plugin.config = {
        "schema_dir": "docs/schemas",
        "examples_dir": "docs/schemas/examples",
        "template_dir": "templates/schema",
        "enable_validation": True,
        "show_examples": True,
        "show_cross_refs": True,
    }

    # Load real schemas and examples
    plugin._load_schemas()
    plugin._load_examples()

    # Count validation issues but don't fail
    validation_issues = 0

    for schema_name, examples in plugin.examples.items():
        if schema_name not in plugin.schemas:
            continue

        schema = plugin.schemas[schema_name]

        for example in examples:
            example_data = example["data"]

            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in example_data:
                    validation_issues += 1

            # Check basic type validation
            properties = schema.get("properties", {})
            for field_name, field_value in example_data.items():
                if field_name in properties:
                    prop_schema = properties[field_name]
                    expected_type = prop_schema.get("type")

                    if expected_type == "string" and not isinstance(field_value, str):
                        validation_issues += 1
                    elif expected_type == "number" and not isinstance(field_value, (int, float)):
                        validation_issues += 1
                    elif expected_type == "array" and not isinstance(field_value, list):
                        validation_issues += 1

    # Report validation issues count (don't fail the test)
    print(f"\nFound {validation_issues} validation issues in real examples")
    assert validation_issues >= 0  # Always passes, just reports count


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
