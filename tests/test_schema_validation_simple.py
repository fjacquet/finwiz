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


def test_plugin_import():
    """Test that the plugin can be imported."""
    plugin = SchemaDocsPlugin()
    assert plugin is not None


def test_schema_validation_basic():
    """Test basic schema validation functionality."""
    # Create a simple test
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


def test_real_schema_files_valid_json():
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


def test_real_example_files_valid_json():
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


def test_schema_rendering():
    """Test that schema rendering works."""
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
