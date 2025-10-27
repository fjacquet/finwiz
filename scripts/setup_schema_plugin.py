#!/usr/bin/env python3
"""
Setup script for the MkDocs Schema Plugin

This script sets up the schema plugin for use with MkDocs by creating
the necessary package structure and installing it.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def create_plugin_package():
    """Create the plugin package structure."""
    print("📦 Creating schema plugin package...")

    # Create plugin directory
    plugin_dir = Path("mkdocs_plugins/schema_docs")
    plugin_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    (plugin_dir.parent / "__init__.py").touch()
    (plugin_dir / "__init__.py").write_text(
        """
from .plugin import SchemaDocsPlugin

def get_plugin():
    return SchemaDocsPlugin()
""".strip()
    )

    # Copy the plugin file
    shutil.copy("scripts/mkdocs_schema_plugin.py", plugin_dir / "plugin.py")

    # Create setup.py for the plugin
    setup_py = plugin_dir.parent / "setup.py"
    setup_py.write_text(
        """
from setuptools import setup, find_packages

setup(
    name="mkdocs-schema-docs",
    version="1.0.0",
    description="MkDocs plugin for interactive schema documentation",
    packages=find_packages(),
    entry_points={
        'mkdocs.plugins': [
            'schema_docs = schema_docs.plugin:SchemaDocsPlugin',
        ]
    },
    install_requires=[
        'mkdocs>=1.0',
    ],
)
""".strip()
    )

    print("✅ Plugin package created")


def install_plugin():
    """Install the plugin in development mode."""
    print("🔧 Installing schema plugin...")

    try:
        # Install in development mode
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "mkdocs_plugins/"], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Schema plugin installed successfully")
        else:
            print(f"❌ Failed to install plugin: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error installing plugin: {e}")
        return False

    return True


def test_plugin_import():
    """Test that the plugin can be imported."""
    print("🧪 Testing plugin import...")

    try:
        # Add the plugin directory to Python path
        plugin_path = Path("mkdocs_plugins").absolute()
        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))

        # Try to import the plugin
        from schema_docs.plugin import SchemaDocsPlugin

        # Create an instance
        plugin = SchemaDocsPlugin()

        print("✅ Plugin import successful")
        return True

    except Exception as e:
        print(f"❌ Plugin import failed: {e}")
        return False


def create_plugin_documentation():
    """Create documentation for the schema plugin."""
    print("📚 Creating plugin documentation...")

    doc_content = """# Schema Documentation Plugin

The Schema Documentation Plugin automatically generates interactive documentation
for JSON schemas in your MkDocs site.

## Usage

Add schema blocks to your markdown files:

```markdown
```schema:SchemaName
Optional description of the schema
```
```

The plugin will automatically:

1. Find the corresponding JSON schema file
2. Generate a properties table with types and constraints
3. Include examples if available
4. Show relationships to other schemas
5. Provide the complete JSON schema

## Configuration

Add to your `mkdocs.yml`:

```yaml
plugins:
  - schema_docs:
      schema_dir: docs/schemas
      examples_dir: docs/schemas/examples
      enable_validation: true
      show_examples: true
      show_cross_refs: true
```

## Features

- **Interactive Properties Table**: Shows all schema properties with types, constraints, and descriptions
- **Example Integration**: Automatically includes example JSON files
- **Cross-References**: Shows relationships between schemas
- **Dark Theme Support**: Automatically adapts to Material theme dark mode
- **Validation**: Validates examples against schemas

## Schema File Structure

```
docs/
├── schemas/
│   ├── SchemaName.schema.json
│   └── examples/
│       └── schema_name.example.json
```

## Styling

The plugin includes comprehensive CSS styling that adapts to the Material theme,
including support for both light and dark modes.
"""

    doc_file = Path("docs/reference/schema_plugin.md")
    doc_file.write_text(doc_content)

    print("✅ Plugin documentation created")


def main():
    """Main setup function."""
    print("🚀 Setting up MkDocs Schema Plugin\n")

    steps = [
        ("Create Plugin Package", create_plugin_package),
        ("Install Plugin", install_plugin),
        ("Test Plugin Import", test_plugin_import),
        ("Create Documentation", create_plugin_documentation),
    ]

    for step_name, step_func in steps:
        print(f"{'=' * 60}")
        print(f"Step: {step_name}")
        print("=" * 60)

        if not step_func():
            print(f"❌ Setup failed at step: {step_name}")
            return 1

        print()

    print("🎉 Schema plugin setup complete!")
    print("\nNext steps:")
    print("1. Run 'mkdocs serve' to test the plugin")
    print("2. Add schema blocks to your documentation")
    print("3. Verify schemas are rendered correctly")

    return 0


if __name__ == "__main__":
    sys.exit(main())
