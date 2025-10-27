#!/usr/bin/env python3
"""
Schema Integration Script

This script processes existing JSON schema files and creates enhanced
documentation with cross-references and relationship mapping.
"""

import json
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchemaIntegrator:
    """Integrates existing JSON schemas with enhanced documentation."""

    def __init__(self, schema_dir: str = "docs/schemas", examples_dir: str = "docs/schemas/examples"):
        self.schema_dir = Path(schema_dir)
        self.examples_dir = Path(examples_dir)
        self.schemas: dict[str, dict] = {}
        self.examples: dict[str, list[dict]] = {}
        self.relationships: dict[str, set[str]] = {}

    def load_schemas(self):
        """Load all JSON schema files."""
        if not self.schema_dir.exists():
            logger.error(f"Schema directory not found: {self.schema_dir}")
            return

        for schema_file in self.schema_dir.glob("*.schema.json"):
            try:
                with open(schema_file, encoding="utf-8") as f:
                    schema_data = json.load(f)

                schema_name = schema_file.stem.replace(".schema", "")
                self.schemas[schema_name] = schema_data

                logger.info(f"Loaded schema: {schema_name}")

            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")

    def load_examples(self):
        """Load example JSON files."""
        if not self.examples_dir.exists():
            logger.warning(f"Examples directory not found: {self.examples_dir}")
            return

        for example_file in self.examples_dir.glob("*.example.json"):
            try:
                with open(example_file, encoding="utf-8") as f:
                    example_data = json.load(f)

                # Extract schema name from filename
                base_name = example_file.stem.replace(".example", "")
                schema_name = self._normalize_schema_name(base_name)

                if schema_name not in self.examples:
                    self.examples[schema_name] = []

                self.examples[schema_name].append({"name": base_name, "file": example_file.name, "data": example_data})

                logger.info(f"Loaded example for {schema_name}: {base_name}")

            except Exception as e:
                logger.error(f"Failed to load example {example_file}: {e}")

    def build_relationships(self):
        """Build relationships between schemas."""
        for schema_name, schema_data in self.schemas.items():
            relationships = set()

            # Find references to other schemas
            self._find_schema_references(schema_data, relationships)

            if relationships:
                self.relationships[schema_name] = relationships
                logger.info(f"Found relationships for {schema_name}: {relationships}")

    def _find_schema_references(self, data: Any, relationships: set[str]):
        """Recursively find schema references in JSON schema."""
        if isinstance(data, dict):
            # Check for $ref references
            if "$ref" in data:
                ref = data["$ref"]
                if ref.startswith("#/definitions/"):
                    schema_name = ref.replace("#/definitions/", "")
                    relationships.add(schema_name)

            # Check for type references that might be other schemas
            if "type" in data and data["type"] == "array" and "items" in data:
                items = data["items"]
                if "$ref" in items:
                    ref = items["$ref"]
                    if ref.startswith("#/definitions/"):
                        schema_name = ref.replace("#/definitions/", "")
                        relationships.add(schema_name)

            # Recursively check other dict values
            for value in data.values():
                if isinstance(value, (dict, list)):
                    self._find_schema_references(value, relationships)

        elif isinstance(data, list):
            for item in data:
                self._find_schema_references(item, relationships)

    def _normalize_schema_name(self, name: str) -> str:
        """Normalize schema name for consistent matching."""
        # Convert snake_case to PascalCase
        parts = name.split("_")
        normalized = "".join(word.capitalize() for word in parts)

        # Handle special cases
        special_cases = {
            "TenkInsight": "TenKInsight",
            "EtfFactsheet": "ETFFactsheet",
            "EtfTopHolding": "ETFTopHolding",
            "AplusDiscoveryResult": "APlusDiscoveryResult",
            "AplusImprovementSuggestion": "APlusImprovementSuggestion",
            "AplusOpportunitySection": "APlusOpportunitySection",
        }

        return special_cases.get(normalized, normalized)

    def generate_schema_index(self) -> str:
        """Generate a comprehensive schema index."""
        lines = []

        lines.append("# Schema Index")
        lines.append("")
        lines.append("Complete index of all FinWiz schemas with relationships and examples.")
        lines.append("")

        # Group schemas by category
        categories = {
            "Analysis Schemas": ["TenKInsight", "ETFFactsheet", "CryptoThesis", "MarketSentiment"],
            "Portfolio Schemas": ["PortfolioReview", "HoldingDecision", "Alternative", "PortfolioImprovement"],
            "Discovery Schemas": ["APlusDiscoveryResult", "InvestmentCandidate", "APlusImprovementSuggestion"],
            "Risk Schemas": ["RiskAssessmentStandardized"],
            "Validation Schemas": ["ValidatedTicker", "ValidationResult"],
            "Utility Schemas": ["ReporterInput", "OptimizationResult"],
        }

        for category, schema_names in categories.items():
            lines.append(f"## {category}")
            lines.append("")

            for schema_name in schema_names:
                if schema_name in self.schemas:
                    schema = self.schemas[schema_name]

                    # Schema title and description
                    title = schema.get("title", schema_name)
                    description = schema.get("description", "No description available")

                    lines.append(f"### {title}")
                    lines.append(f"**Schema Name**: `{schema_name}`")
                    lines.append(f"**Description**: {description}")

                    # Properties count
                    if "properties" in schema:
                        prop_count = len(schema["properties"])
                        required_count = len(schema.get("required", []))
                        lines.append(f"**Properties**: {prop_count} ({required_count} required)")

                    # Examples
                    if schema_name in self.examples:
                        example_count = len(self.examples[schema_name])
                        example_names = [ex["name"] for ex in self.examples[schema_name]]
                        lines.append(f"**Examples**: {example_count} ({', '.join(example_names)})")

                    # Relationships
                    if schema_name in self.relationships:
                        related = list(self.relationships[schema_name])
                        lines.append(f"**Related Schemas**: {', '.join(related)}")

                    lines.append("")

        return "\n".join(lines)

    def generate_relationship_map(self) -> str:
        """Generate a relationship map in Mermaid format."""
        lines = []

        lines.append("# Schema Relationships")
        lines.append("")
        lines.append("```mermaid")
        lines.append("graph TD")

        # Add nodes
        for schema_name in self.schemas.keys():
            lines.append(f"    {schema_name}[{schema_name}]")

        # Add relationships
        for schema_name, related_schemas in self.relationships.items():
            for related in related_schemas:
                if related in self.schemas:
                    lines.append(f"    {schema_name} --> {related}")

        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def validate_examples(self) -> dict[str, list[str]]:
        """Validate examples against their schemas."""
        validation_results = {}

        for schema_name, examples in self.examples.items():
            if schema_name not in self.schemas:
                continue

            schema = self.schemas[schema_name]
            results = []

            for example in examples:
                try:
                    # Basic validation - check required fields
                    required_fields = schema.get("required", [])
                    properties = schema.get("properties", {})

                    missing_fields = []
                    for field in required_fields:
                        if field not in example["data"]:
                            missing_fields.append(field)

                    if missing_fields:
                        results.append(f"❌ {example['name']}: Missing required fields: {missing_fields}")
                    else:
                        results.append(f"✅ {example['name']}: Valid")

                except Exception as e:
                    results.append(f"❌ {example['name']}: Validation error: {e}")

            if results:
                validation_results[schema_name] = results

        return validation_results

    def generate_validation_report(self) -> str:
        """Generate a validation report for all schemas and examples."""
        lines = []

        lines.append("# Schema Validation Report")
        lines.append("")

        # Schema statistics
        lines.append("## Statistics")
        lines.append(f"- **Total Schemas**: {len(self.schemas)}")
        lines.append(f"- **Schemas with Examples**: {len(self.examples)}")
        lines.append(f"- **Schemas with Relationships**: {len(self.relationships)}")
        lines.append("")

        # Validation results
        validation_results = self.validate_examples()

        lines.append("## Example Validation")
        lines.append("")

        for schema_name, results in validation_results.items():
            lines.append(f"### {schema_name}")
            for result in results:
                lines.append(f"- {result}")
            lines.append("")

        # Missing examples
        schemas_without_examples = set(self.schemas.keys()) - set(self.examples.keys())
        if schemas_without_examples:
            lines.append("## Schemas Missing Examples")
            for schema_name in sorted(schemas_without_examples):
                lines.append(f"- {schema_name}")
            lines.append("")

        return "\n".join(lines)

    def run_integration(self):
        """Run the complete schema integration process."""
        logger.info("Starting schema integration...")

        # Load data
        self.load_schemas()
        self.load_examples()
        self.build_relationships()

        # Generate documentation
        schema_index = self.generate_schema_index()
        relationship_map = self.generate_relationship_map()
        validation_report = self.generate_validation_report()

        # Write output files
        output_dir = Path("docs/reference/schemas")
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "index.md", "w") as f:
            f.write(schema_index)

        with open(output_dir / "relationships.md", "w") as f:
            f.write(relationship_map)

        with open(output_dir / "validation_report.md", "w") as f:
            f.write(validation_report)

        logger.info("Schema integration complete!")
        logger.info(f"Generated files in {output_dir}")


def main():
    """Main entry point."""
    integrator = SchemaIntegrator()
    integrator.run_integration()


if __name__ == "__main__":
    main()
