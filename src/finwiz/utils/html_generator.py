"""
Inline HTML generation utilities.

This module provides decorators and utilities to automatically generate HTML
reports whenever JSON files are created or updated.
"""

import functools
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .template_renderer import TemplateRenderer


class HTMLGenerator:
    """Manages inline HTML generation for JSON outputs."""

    def __init__(self):
        self.renderer = TemplateRenderer()
        self.enabled = True

        # File pattern to template type mapping
        self.template_mappings = {
            "backtesting_results": "backtesting_results",
            "portfolio_review": "portfolio_review",
            "a_plus_crypto": "a_plus_discovery",
            "a_plus_etfs": "a_plus_discovery",
            "a_plus_stocks": "a_plus_discovery",
            "deep_analysis_consolidated": "deep_analysis_consolidated",
            "optimization_report": "optimization_report",
            "validation_report": "validation_report",
            "discovery_latest": "discovery_latest",
            "portfolio_processing_summary": "portfolio_processing_summary",
        }

    def get_template_type(self, file_path: Path) -> str | None:
        """Determine template type from file path."""
        file_name = file_path.stem

        # Check exact matches first
        if file_name in self.template_mappings:
            return self.template_mappings[file_name]

        # Check pattern matches
        for pattern, template_type in self.template_mappings.items():
            if pattern in file_name:
                return template_type

        return None

    def generate_html(self, json_path: Path, data: dict[str, Any] = None) -> Path | None:
        """Generate HTML file from JSON path and optional data."""
        if not self.enabled:
            return None

        template_type = self.get_template_type(json_path)
        if not template_type:
            return None

        try:
            if data is not None:
                # Use provided data
                html_content = getattr(self.renderer, f"render_{template_type}")(data)
            else:
                # Load from file
                html_content = self.renderer.render_from_file(json_path, template_type)

            # Generate HTML file path
            html_path = json_path.with_suffix(".html")

            # Write HTML file
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            return html_path

        except Exception as e:
            print(f"⚠️  Failed to generate HTML for {json_path}: {e}")
            return None

    def enable(self):
        """Enable HTML generation."""
        self.enabled = True

    def disable(self):
        """Disable HTML generation."""
        self.enabled = False


# Global HTML generator instance
html_generator = HTMLGenerator()


def save_json_with_html(data: dict[str, Any], file_path: str | Path, template_type: str | None = None) -> tuple[Path, Path | None]:
    """
    Save JSON data and automatically generate HTML.

    Args:
        data: JSON data to save
        file_path: Path to save JSON file
        template_type: Optional template type override

    Returns:
        Tuple of (json_path, html_path)

    """
    json_path = Path(file_path)

    # Ensure directory exists
    json_path.parent.mkdir(parents=True, exist_ok=True)

    # Save JSON file
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    # Generate HTML
    if template_type:
        # Override template type
        original_mapping = html_generator.template_mappings.copy()
        html_generator.template_mappings[json_path.stem] = template_type
        html_path = html_generator.generate_html(json_path, data)
        html_generator.template_mappings = original_mapping
    else:
        html_path = html_generator.generate_html(json_path, data)

    return json_path, html_path


def auto_html(template_type: str | None = None):
    """
    Decorator to automatically generate HTML for functions that save JSON files.

    Args:
        template_type: Template type to use for HTML generation

    Usage:
        @auto_html('portfolio_review')
        def save_portfolio_review(data, output_path):
            # Function saves JSON and returns path
            return json_path

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Call original function
            result = func(*args, **kwargs)

            # Handle different return types
            if isinstance(result, (str, Path)):
                json_path = Path(result)
                if json_path.exists() and json_path.suffix == ".json":
                    html_path = html_generator.generate_html(json_path)
                    if html_path:
                        print(f"📄 Generated HTML: {html_path}")

            return result

        return wrapper

    return decorator


class JSONWriter:
    """Context manager for writing JSON with automatic HTML generation."""

    def __init__(self, file_path: str | Path, template_type: str | None = None):
        self.file_path = Path(file_path)
        self.template_type = template_type
        self.data = {}
        self.json_path = None
        self.html_path = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.data:
            self.json_path, self.html_path = save_json_with_html(self.data, self.file_path, self.template_type)
            if self.html_path:
                print(f"📄 Generated: {self.json_path} + {self.html_path}")
            else:
                print(f"📄 Generated: {self.json_path}")

    def write(self, data: dict[str, Any]):
        """Write data to be saved as JSON."""
        self.data = data

    def update(self, data: dict[str, Any]):
        """Update data dictionary."""
        self.data.update(data)


# Convenience functions for common report types
def save_backtesting_results(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save backtesting results with HTML generation."""
    return save_json_with_html(data, output_path, "backtesting_results")


def save_portfolio_review(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save portfolio review with HTML generation."""
    return save_json_with_html(data, output_path, "portfolio_review")


def save_a_plus_discovery(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save A+ discovery with HTML generation."""
    return save_json_with_html(data, output_path, "a_plus_discovery")


def save_deep_analysis(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save deep analysis with HTML generation."""
    return save_json_with_html(data, output_path, "deep_analysis_consolidated")


def save_optimization_report(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save optimization report with HTML generation."""
    return save_json_with_html(data, output_path, "optimization_report")


def save_validation_report(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save validation report with HTML generation."""
    return save_json_with_html(data, output_path, "validation_report")


def save_discovery_latest(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save discovery latest with HTML generation."""
    return save_json_with_html(data, output_path, "discovery_latest")


def save_processing_summary(data: dict[str, Any], output_path: str | Path) -> tuple[Path, Path | None]:
    """Save processing summary with HTML generation."""
    return save_json_with_html(data, output_path, "portfolio_processing_summary")


# Configuration functions
def enable_html_generation():
    """Enable automatic HTML generation."""
    html_generator.enable()
    print("✅ HTML generation enabled")


def disable_html_generation():
    """Disable automatic HTML generation."""
    html_generator.disable()
    print("⚠️  HTML generation disabled")


def is_html_generation_enabled() -> bool:
    """Check if HTML generation is enabled."""
    return html_generator.enabled
