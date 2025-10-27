"""
MkDocs Schema Documentation Plugin

This plugin processes schema blocks in markdown files and generates interactive
documentation for JSON schemas with examples and validation.

Usage in markdown:
```schema:TenKInsight
Optional description of the schema
```

The plugin will:
1. Find the corresponding JSON schema file
2. Generate interactive documentation
3. Include examples and validation rules
4. Add cross-references to related schemas
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import Page

logger = logging.getLogger(__name__)


class SchemaDocsPlugin(BasePlugin):
    """MkDocs plugin for generating interactive schema documentation."""

    config_scheme = (
        ("schema_dir", config_options.Type(str, default="docs/schemas")),
        ("examples_dir", config_options.Type(str, default="docs/schemas/examples")),
        ("template_dir", config_options.Type(str, default="templates/schema")),
        ("enable_validation", config_options.Type(bool, default=True)),
        ("show_examples", config_options.Type(bool, default=True)),
        ("show_cross_refs", config_options.Type(bool, default=True)),
    )

    def __init__(self):
        super().__init__()
        self.schemas: dict[str, dict] = {}
        self.examples: dict[str, dict] = {}
        self.schema_relationships: dict[str, list[str]] = {}

    def on_config(self, config):
        """Load schemas and examples on configuration."""
        self._load_schemas()
        self._load_examples()
        self._build_relationships()
        return config

    def on_page_markdown(self, markdown: str, page: Page, config, files) -> str:
        """Process schema blocks in markdown content."""
        # Find all schema blocks
        schema_pattern = r"```schema:(\w+)\n?(.*?)\n?```"

        def replace_schema_block(match):
            schema_name = match.group(1)
            description = match.group(2).strip() if match.group(2) else ""

            return self._generate_schema_documentation(schema_name, description)

        # Replace all schema blocks
        processed_markdown = re.sub(schema_pattern, replace_schema_block, markdown, flags=re.DOTALL)

        return processed_markdown

    def _load_schemas(self):
        """Load all JSON schema files."""
        schema_dir = Path(self.config["schema_dir"])

        if not schema_dir.exists():
            logger.warning(f"Schema directory not found: {schema_dir}")
            return

        for schema_file in schema_dir.glob("*.schema.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    schema_data = json.load(f)

                schema_name = schema_file.stem.replace(".schema", "")
                self.schemas[schema_name] = schema_data

                logger.debug(f"Loaded schema: {schema_name}")

            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")

    def _load_examples(self):
        """Load example JSON files."""
        examples_dir = Path(self.config["examples_dir"])

        if not examples_dir.exists():
            logger.warning(f"Examples directory not found: {examples_dir}")
            return

        for example_file in examples_dir.glob("*.example.json"):
            try:
                with open(example_file, encoding="utf-8") as f:
                    example_data = json.load(f)

                # Extract schema name from filename
                # e.g., tenk_insight.example.json -> TenKInsight
                base_name = example_file.stem.replace(".example", "")
                schema_name = self._normalize_schema_name(base_name)

                # Also try exact match with schema names
                if schema_name not in self.schemas:
                    # Try to find matching schema by checking all schema names
                    for existing_schema in self.schemas.keys():
                        if existing_schema.lower() == base_name.lower().replace("_", ""):
                            schema_name = existing_schema
                            break

                if schema_name not in self.examples:
                    self.examples[schema_name] = []

                self.examples[schema_name].append({"name": base_name, "data": example_data})

                logger.debug(f"Loaded example for {schema_name}: {base_name}")

            except Exception as e:
                logger.error(f"Failed to load example {example_file}: {e}")

    def _build_relationships(self):
        """Build relationships between schemas."""
        for schema_name, schema_data in self.schemas.items():
            relationships = []

            # Find references to other schemas
            self._find_schema_references(schema_data, relationships)

            if relationships:
                self.schema_relationships[schema_name] = list(set(relationships))

    def _find_schema_references(self, data: Any, relationships: list[str]):
        """Recursively find schema references in JSON schema."""
        if isinstance(data, dict):
            # Check for $ref references
            if "$ref" in data:
                ref = data["$ref"]
                if ref.startswith("#/definitions/"):
                    schema_name = ref.replace("#/definitions/", "")
                    relationships.append(schema_name)

            # Check for type references in properties
            if "properties" in data:
                for prop_data in data["properties"].values():
                    self._find_schema_references(prop_data, relationships)

            # Check for array items
            if "items" in data:
                self._find_schema_references(data["items"], relationships)

            # Recursively check other dict values
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._find_schema_references(value, relationships)

        elif isinstance(data, list):
            for item in data:
                self._find_schema_references(item, relationships)

    def _generate_schema_documentation(self, schema_name: str, description: str = "") -> str:
        """Generate HTML documentation for a schema."""
        if schema_name not in self.schemas:
            logger.warning(f"Schema not found: {schema_name}")
            return f"<!-- Schema {schema_name} not found -->"

        schema = self.schemas[schema_name]

        # Build the documentation HTML
        html_parts = []

        # Schema header
        html_parts.append(f'<div class="schema-docs" id="schema-{schema_name}">')
        html_parts.append(f'<h3 class="schema-title">📋 {schema_name} Schema</h3>')

        if description:
            html_parts.append(f'<p class="schema-description">{description}</p>')

        # Schema properties
        if "properties" in schema:
            html_parts.append("<h4>Properties</h4>")
            html_parts.append('<div class="schema-properties">')
            html_parts.append(self._generate_properties_table(schema["properties"], schema.get("required", [])))
            html_parts.append("</div>")

        # Examples
        if self.config["show_examples"] and schema_name in self.examples:
            html_parts.append("<h4>Examples</h4>")
            html_parts.append('<div class="schema-examples">')

            for example in self.examples[schema_name]:
                html_parts.append(f"<h5>{example['name']}</h5>")
                html_parts.append('<div class="highlight">')
                html_parts.append('<pre><code class="language-json">')
                html_parts.append(json.dumps(example["data"], indent=2, ensure_ascii=False))
                html_parts.append("</code></pre>")
                html_parts.append("</div>")

            html_parts.append("</div>")

        # Cross-references
        if self.config["show_cross_refs"] and schema_name in self.schema_relationships:
            html_parts.append("<h4>Related Schemas</h4>")
            html_parts.append('<div class="schema-cross-refs">')
            html_parts.append("<ul>")

            for related_schema in self.schema_relationships[schema_name]:
                html_parts.append(f'<li><a href="#schema-{related_schema}">{related_schema}</a></li>')

            html_parts.append("</ul>")
            html_parts.append("</div>")

        # JSON Schema
        html_parts.append('<details class="schema-json">')
        html_parts.append("<summary>View JSON Schema</summary>")
        html_parts.append('<div class="highlight">')
        html_parts.append('<pre><code class="language-json">')
        html_parts.append(json.dumps(schema, indent=2, ensure_ascii=False))
        html_parts.append("</code></pre>")
        html_parts.append("</div>")
        html_parts.append("</details>")

        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _generate_properties_table(self, properties: dict, required: list[str]) -> str:
        """Generate HTML table for schema properties."""
        html_parts = []

        html_parts.append('<table class="schema-properties-table">')
        html_parts.append("<thead>")
        html_parts.append("<tr>")
        html_parts.append("<th>Property</th>")
        html_parts.append("<th>Type</th>")
        html_parts.append("<th>Required</th>")
        html_parts.append("<th>Description</th>")
        html_parts.append("<th>Constraints</th>")
        html_parts.append("</tr>")
        html_parts.append("</thead>")
        html_parts.append("<tbody>")

        for prop_name, prop_data in properties.items():
            html_parts.append("<tr>")

            # Property name
            html_parts.append(f"<td><code>{prop_name}</code></td>")

            # Type
            prop_type = self._get_property_type(prop_data)
            html_parts.append(f"<td><code>{prop_type}</code></td>")

            # Required
            is_required = prop_name in required
            required_badge = (
                '<span class="badge badge-required">Required</span>'
                if is_required
                else '<span class="badge badge-optional">Optional</span>'
            )
            html_parts.append(f"<td>{required_badge}</td>")

            # Description
            description = prop_data.get("description", "")
            html_parts.append(f"<td>{description}</td>")

            # Constraints
            constraints = self._get_property_constraints(prop_data)
            html_parts.append(f"<td>{constraints}</td>")

            html_parts.append("</tr>")

        html_parts.append("</tbody>")
        html_parts.append("</table>")

        return "\n".join(html_parts)

    def _get_property_type(self, prop_data: dict) -> str:
        """Extract property type from schema data."""
        if "type" in prop_data:
            prop_type = prop_data["type"]

            # Handle array types
            if prop_type == "array" and "items" in prop_data:
                items_type = self._get_property_type(prop_data["items"])
                return f"Array[{items_type}]"

            return prop_type.title()

        # Handle $ref
        if "$ref" in prop_data:
            ref = prop_data["$ref"]
            if ref.startswith("#/definitions/"):
                return ref.replace("#/definitions/", "")

        # Handle oneOf, anyOf, allOf
        if "oneOf" in prop_data:
            types = [self._get_property_type(item) for item in prop_data["oneOf"]]
            return " | ".join(types)

        return "Any"

    def _get_property_constraints(self, prop_data: dict) -> str:
        """Extract property constraints from schema data."""
        constraints = []

        # String constraints
        if "minLength" in prop_data:
            constraints.append(f"min length: {prop_data['minLength']}")
        if "maxLength" in prop_data:
            constraints.append(f"max length: {prop_data['maxLength']}")
        if "pattern" in prop_data:
            constraints.append(f"pattern: <code>{prop_data['pattern']}</code>")

        # Number constraints
        if "minimum" in prop_data:
            constraints.append(f"min: {prop_data['minimum']}")
        if "maximum" in prop_data:
            constraints.append(f"max: {prop_data['maximum']}")
        if "exclusiveMinimum" in prop_data:
            constraints.append(f"min: >{prop_data['exclusiveMinimum']}")
        if "exclusiveMaximum" in prop_data:
            constraints.append(f"max: <{prop_data['exclusiveMaximum']}")

        # Enum constraints
        if "enum" in prop_data:
            enum_values = ", ".join([f"<code>{v}</code>" for v in prop_data["enum"]])
            constraints.append(f"enum: {enum_values}")

        # Array constraints
        if "minItems" in prop_data:
            constraints.append(f"min items: {prop_data['minItems']}")
        if "maxItems" in prop_data:
            constraints.append(f"max items: {prop_data['maxItems']}")

        return "<br>".join(constraints) if constraints else ""

    def _normalize_schema_name(self, name: str) -> str:
        """Normalize schema name for consistent matching."""
        # Convert snake_case to PascalCase
        parts = name.split("_")
        normalized = "".join(word.capitalize() for word in parts)

        # Handle special cases
        if normalized == "TenkInsight":
            return "TenKInsight"

        return normalized

    def on_page_content(self, html: str, page: Page, config, files) -> str:
        """Add CSS styles for schema documentation."""
        if '<div class="schema-docs"' in html:
            # Add schema-specific CSS
            css = """
<style>
.schema-docs {
    border: 1px solid #e1e4e8;
    border-radius: 6px;
    padding: 16px;
    margin: 16px 0;
    background-color: #f6f8fa;
}

.schema-title {
    margin-top: 0;
    color: #24292e;
    border-bottom: 1px solid #e1e4e8;
    padding-bottom: 8px;
}

.schema-description {
    color: #586069;
    font-style: italic;
    margin-bottom: 16px;
}

.schema-properties-table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
}

.schema-properties-table th,
.schema-properties-table td {
    border: 1px solid #e1e4e8;
    padding: 8px 12px;
    text-align: left;
}

.schema-properties-table th {
    background-color: #f1f3f4;
    font-weight: 600;
}

.badge {
    display: inline-block;
    padding: 2px 6px;
    font-size: 11px;
    font-weight: 500;
    border-radius: 3px;
    text-transform: uppercase;
}

.badge-required {
    background-color: #d73a49;
    color: white;
}

.badge-optional {
    background-color: #28a745;
    color: white;
}

.schema-examples {
    margin: 16px 0;
}

.schema-cross-refs ul {
    list-style-type: none;
    padding-left: 0;
}

.schema-cross-refs li {
    display: inline-block;
    margin-right: 12px;
    margin-bottom: 4px;
}

.schema-cross-refs a {
    display: inline-block;
    padding: 4px 8px;
    background-color: #0366d6;
    color: white;
    text-decoration: none;
    border-radius: 3px;
    font-size: 12px;
}

.schema-cross-refs a:hover {
    background-color: #0256cc;
}

.schema-json {
    margin-top: 16px;
}

.schema-json summary {
    cursor: pointer;
    font-weight: 600;
    padding: 8px 0;
}

/* Dark theme support */
[data-md-color-scheme="slate"] .schema-docs {
    background-color: #2d3748;
    border-color: #4a5568;
}

[data-md-color-scheme="slate"] .schema-title {
    color: #e2e8f0;
    border-color: #4a5568;
}

[data-md-color-scheme="slate"] .schema-description {
    color: #a0aec0;
}

[data-md-color-scheme="slate"] .schema-properties-table th {
    background-color: #4a5568;
    color: #e2e8f0;
}

[data-md-color-scheme="slate"] .schema-properties-table th,
[data-md-color-scheme="slate"] .schema-properties-table td {
    border-color: #4a5568;
}
</style>
"""
            html = css + html

        return html


def get_plugin():
    """Entry point for MkDocs plugin system."""
    return SchemaDocsPlugin()
