#!/usr/bin/env python3
"""
Test script for the MkDocs Schema Documentation Plugin

This script tests the schema plugin functionality with sample data
to ensure it works correctly before integration with MkDocs.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the scripts directory to the path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mkdocs_schema_plugin import SchemaDocsPlugin


def create_test_schema():
    """Create a test schema file."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "TenKInsight",
        "type": "object",
        "description": "Stock analysis results from SEC filing analysis",
        "properties": {
            "ticker": {"type": "string", "description": "Stock ticker symbol", "pattern": "^[A-Z]{1,5}$"},
            "recommendation": {"type": "string", "description": "Investment recommendation", "enum": ["BUY", "HOLD", "SELL"]},
            "grade": {"type": "string", "description": "Investment grade", "pattern": "^(A\\+|A|B|C|D|F)$"},
            "composite_score": {"type": "number", "description": "Overall composite score", "minimum": 0.0, "maximum": 1.0},
            "confidence": {"type": "number", "description": "Confidence level", "minimum": 0.0, "maximum": 1.0},
            "rationale": {"type": "string", "description": "Detailed reasoning", "minLength": 50},
            "risk_factors": {"type": "array", "description": "List of risk factors", "items": {"type": "string"}},
        },
        "required": ["ticker", "recommendation", "grade", "composite_score", "confidence", "rationale"],
    }
    return schema


def create_test_example():
    """Create a test example file."""
    example = {
        "ticker": "AAPL",
        "recommendation": "BUY",
        "grade": "A+",
        "composite_score": 0.92,
        "confidence": 0.87,
        "rationale": "Strong fundamentals with excellent growth prospects and technical momentum support a buy recommendation.",
        "risk_factors": ["Market volatility", "Regulatory changes"],
    }
    return example


def test_schema_plugin():
    """Test the schema plugin functionality."""
    print("🧪 Testing MkDocs Schema Plugin...")

    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create schema and examples directories
        schema_dir = temp_path / "schemas"
        examples_dir = temp_path / "schemas" / "examples"
        schema_dir.mkdir(parents=True)
        examples_dir.mkdir(parents=True)

        # Create test schema file
        schema_file = schema_dir / "TenKInsight.schema.json"
        with open(schema_file, "w") as f:
            json.dump(create_test_schema(), f, indent=2)

        # Create test example file
        example_file = examples_dir / "tenk_insight.example.json"
        with open(example_file, "w") as f:
            json.dump(create_test_example(), f, indent=2)

        # Initialize plugin
        plugin = SchemaDocsPlugin()
        plugin.config = {
            "schema_dir": str(schema_dir),
            "examples_dir": str(examples_dir),
            "template_dir": "templates/schema",
            "enable_validation": True,
            "show_examples": True,
            "show_cross_refs": True,
        }

        # Load schemas and examples
        plugin._load_schemas()
        plugin._load_examples()
        plugin._build_relationships()

        # Test schema loading
        print(f"✅ Loaded {len(plugin.schemas)} schemas")
        print(f"✅ Loaded examples for {len(plugin.examples)} schemas")

        # Test markdown processing
        test_markdown = """
# Test Document

This is a test document with a schema block.

```schema:TenKInsight
This schema represents stock analysis results from SEC filing analysis.
```

Some more content here.
"""

        # Create a mock page object
        class MockPage:
            def __init__(self):
                self.title = "Test Page"

        processed_markdown = plugin.on_page_markdown(test_markdown, MockPage(), {}, [])

        # Check if schema block was processed
        if '<div class="schema-docs"' in processed_markdown:
            print("✅ Schema block processed successfully")
        else:
            print("❌ Schema block not processed")
            return False

        # Check if properties table was generated
        if '<table class="schema-properties-table">' in processed_markdown:
            print("✅ Properties table generated")
        else:
            print("❌ Properties table not generated")
            return False

        # Check if examples were included
        if "Examples" in processed_markdown and '"ticker": "AAPL"' in processed_markdown:
            print("✅ Examples included")
        else:
            print("❌ Examples not included")
            return False

        # Check if JSON schema is included
        if "View JSON Schema" in processed_markdown:
            print("✅ JSON schema included")
        else:
            print("❌ JSON schema not included")
            return False

        print("\n📋 Generated Documentation Preview:")
        print("=" * 50)
        # Show a portion of the generated HTML
        lines = processed_markdown.split("\n")
        for i, line in enumerate(lines):
            if '<div class="schema-docs"' in line:
                # Show the next 20 lines
                for j in range(i, min(i + 20, len(lines))):
                    print(lines[j])
                break
        print("=" * 50)

        return True


def test_property_type_extraction():
    """Test property type extraction functionality."""
    print("\n🔍 Testing property type extraction...")

    plugin = SchemaDocsPlugin()

    # Test basic types
    test_cases = [
        ({"type": "string"}, "String"),
        ({"type": "number"}, "Number"),
        ({"type": "boolean"}, "Boolean"),
        ({"type": "array", "items": {"type": "string"}}, "Array[String]"),
        ({"$ref": "#/definitions/SomeSchema"}, "SomeSchema"),
        ({"oneOf": [{"type": "string"}, {"type": "number"}]}, "String | Number"),
    ]

    for prop_data, expected in test_cases:
        result = plugin._get_property_type(prop_data)
        if result == expected:
            print(f"✅ {prop_data} -> {result}")
        else:
            print(f"❌ {prop_data} -> {result} (expected {expected})")
            return False

    return True


def test_constraint_extraction():
    """Test property constraint extraction functionality."""
    print("\n📏 Testing constraint extraction...")

    plugin = SchemaDocsPlugin()

    # Test constraints
    test_cases = [
        ({"minLength": 5, "maxLength": 50}, "min length: 5<br>max length: 50"),
        ({"minimum": 0, "maximum": 100}, "min: 0<br>max: 100"),
        ({"pattern": "^[A-Z]+$"}, "pattern: <code>^[A-Z]+$</code>"),
        ({"enum": ["A", "B", "C"]}, "enum: <code>A</code>, <code>B</code>, <code>C</code>"),
        ({}, ""),
    ]

    for prop_data, expected in test_cases:
        result = plugin._get_property_constraints(prop_data)
        if result == expected:
            print(f"✅ {prop_data} -> {result}")
        else:
            print(f"❌ {prop_data} -> {result} (expected {expected})")
            return False

    return True


def main():
    """Run all tests."""
    print("🚀 Starting MkDocs Schema Plugin Tests\n")

    tests = [
        ("Schema Plugin Functionality", test_schema_plugin),
        ("Property Type Extraction", test_property_type_extraction),
        ("Constraint Extraction", test_constraint_extraction),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"Running: {test_name}")
        print("=" * 60)

        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")

    print(f"\n{'=' * 60}")
    print(f"Test Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("🎉 All tests passed! Schema plugin is ready for integration.")
        return 0
    else:
        print("💥 Some tests failed. Please fix issues before integration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
