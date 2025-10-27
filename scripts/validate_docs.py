#!/usr/bin/env python3
"""
Documentation validation script for FinWiz.

Validates documentation structure, links, and Diátaxis compliance.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse


class DocumentationValidator:
    """Validates documentation structure and content."""

    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> bool:
        """Run all validation checks."""
        print("🔍 Validating documentation structure and content...")

        # Check directory structure
        self._validate_structure()

        # Check markdown files
        self._validate_markdown_files()

        # Check internal links
        self._validate_internal_links()

        # Check Diátaxis compliance
        self._validate_diataxis_compliance()

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def _validate_structure(self) -> None:
        """Validate Diátaxis directory structure."""
        required_dirs = ["tutorials", "how-to", "reference", "explanations"]

        for dir_name in required_dirs:
            dir_path = self.docs_dir / dir_name
            if not dir_path.exists():
                self.errors.append(f"Missing required directory: {dir_path}")
            elif not dir_path.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dir_path}")

        # Check for index.md
        index_file = self.docs_dir / "index.md"
        if not index_file.exists():
            self.errors.append("Missing main index.md file")

    def _validate_markdown_files(self) -> None:
        """Validate markdown file structure."""
        for md_file in self.docs_dir.rglob("*.md"):
            self._validate_markdown_file(md_file)

    def _validate_markdown_file(self, file_path: Path) -> None:
        """Validate individual markdown file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.errors.append(f"Cannot read file {file_path}: {e}")
            return

        # Check for H1 title (should have exactly one)
        h1_matches = re.findall(r"^# (.+)$", content, re.MULTILINE)
        if len(h1_matches) == 0:
            self.warnings.append(f"No H1 title found in {file_path}")
        elif len(h1_matches) > 1:
            self.warnings.append(f"Multiple H1 titles found in {file_path}")

        # Check for empty files
        if len(content.strip()) == 0:
            self.warnings.append(f"Empty file: {file_path}")

        # Check for proper heading hierarchy
        self._validate_heading_hierarchy(file_path, content)

    def _validate_heading_hierarchy(self, file_path: Path, content: str) -> None:
        """Validate heading hierarchy (H1 -> H2 -> H3, etc.)."""
        headings = re.findall(r"^(#{1,6}) (.+)$", content, re.MULTILINE)

        prev_level = 0
        for heading_match in headings:
            level = len(heading_match[0])

            # Skip if this is the first heading or H1
            if prev_level == 0 or level == 1:
                prev_level = level
                continue

            # Check if level jump is too big (more than 1)
            if level > prev_level + 1:
                self.warnings.append(f"Heading hierarchy skip in {file_path}: H{prev_level} -> H{level} (should be sequential)")

            prev_level = level

    def _validate_internal_links(self) -> None:
        """Validate internal markdown links."""
        all_files = set()
        all_links = []

        # Collect all markdown files
        for md_file in self.docs_dir.rglob("*.md"):
            relative_path = md_file.relative_to(self.docs_dir)
            all_files.add(str(relative_path))

            # Extract links from this file
            try:
                content = md_file.read_text(encoding="utf-8")
                file_links = self._extract_internal_links(content, md_file)
                all_links.extend(file_links)
            except Exception as e:
                self.errors.append(f"Cannot read file {md_file}: {e}")

        # Validate each link
        for source_file, link_target in all_links:
            self._validate_internal_link(source_file, link_target, all_files)

    def _extract_internal_links(self, content: str, source_file: Path) -> list[tuple[Path, str]]:
        """Extract internal markdown links from content."""
        links = []

        # Find markdown links [text](url)
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        matches = re.findall(link_pattern, content)

        for text, url in matches:
            # Skip external links
            parsed = urlparse(url)
            if parsed.scheme in ("http", "https", "ftp", "mailto"):
                continue

            # Skip anchors only
            if url.startswith("#"):
                continue

            links.append((source_file, url))

        return links

    def _validate_internal_link(self, source_file: Path, link_target: str, all_files: set[str]) -> None:
        """Validate a single internal link."""
        # Remove anchor if present
        target_path = link_target.split("#")[0]

        # Skip empty targets
        if not target_path:
            return

        # Convert relative path to absolute from docs root
        if target_path.startswith("/"):
            # Absolute path from docs root
            target_path = target_path[1:]
        else:
            # Relative path from source file
            source_dir = source_file.parent
            target_path = str((source_dir / target_path).resolve().relative_to(self.docs_dir.resolve()))

        # Normalize path separators
        target_path = target_path.replace("\\", "/")

        # Check if target exists
        if target_path not in all_files:
            # Try with .md extension if not present
            if not target_path.endswith(".md"):
                target_with_ext = target_path + ".md"
                if target_with_ext in all_files:
                    return

            self.errors.append(f"Broken link in {source_file}: {link_target} -> {target_path}")

    def _validate_diataxis_compliance(self) -> None:
        """Validate Diátaxis framework compliance."""
        diataxis_dirs = {
            "tutorials": {
                "purpose": "learning-oriented",
                "keywords": ["tutorial", "getting started", "walkthrough", "step by step", "learn"],
                "structure": ["prerequisites", "steps", "next steps"],
            },
            "how-to": {
                "purpose": "problem-solving",
                "keywords": ["how to", "guide", "setup", "configure", "install", "deploy"],
                "structure": ["problem", "solution", "steps"],
            },
            "reference": {
                "purpose": "information-oriented",
                "keywords": ["api", "reference", "specification", "schema", "commands"],
                "structure": ["description", "parameters", "examples"],
            },
            "explanations": {
                "purpose": "understanding-oriented",
                "keywords": ["architecture", "concept", "design", "principle", "why"],
                "structure": ["overview", "concepts", "rationale"],
            },
        }

        for dir_name, config in diataxis_dirs.items():
            dir_path = self.docs_dir / dir_name
            if not dir_path.exists():
                continue

            # Check for index file in each category
            index_file = dir_path / "index.md"
            if not index_file.exists():
                self.warnings.append(f"Missing index.md in {dir_name}/ directory")

            # Count files in each category
            md_files = list(dir_path.rglob("*.md"))
            if len(md_files) == 0:
                self.warnings.append(f"No markdown files in {dir_name}/ directory")
                continue

            # Validate content alignment with Diátaxis purpose
            self._validate_diataxis_content(dir_name, md_files, config)

    def _validate_diataxis_content(self, category: str, files: list[Path], config: dict) -> None:
        """Validate that content aligns with Diátaxis category purpose."""
        purpose = config["purpose"]
        keywords = config["keywords"]

        for file_path in files:
            if file_path.name == "index.md":
                continue  # Skip index files

            try:
                content = file_path.read_text(encoding="utf-8").lower()

                # Check if content contains relevant keywords
                keyword_found = any(keyword in content for keyword in keywords)

                # Specific validation by category
                if category == "tutorials":
                    self._validate_tutorial_content(file_path, content)
                elif category == "how-to":
                    self._validate_howto_content(file_path, content)
                elif category == "reference":
                    self._validate_reference_content(file_path, content)
                elif category == "explanations":
                    self._validate_explanation_content(file_path, content)

                if not keyword_found:
                    self.warnings.append(f"Content in {file_path} may not align with {category} purpose ({purpose})")

            except Exception as e:
                self.errors.append(f"Cannot validate Diátaxis compliance for {file_path}: {e}")

    def _validate_tutorial_content(self, file_path: Path, content: str) -> None:
        """Validate tutorial-specific content structure."""
        # Tutorials should be step-by-step and learning-oriented
        step_indicators = ["step", "first", "next", "then", "finally", "1.", "2.", "3."]
        has_steps = any(indicator in content for indicator in step_indicators)

        if not has_steps:
            self.warnings.append(f"Tutorial {file_path} should include step-by-step instructions")

    def _validate_howto_content(self, file_path: Path, content: str) -> None:
        """Validate how-to guide content structure."""
        # How-to guides should be problem-solving oriented
        problem_indicators = ["problem", "issue", "configure", "setup", "install", "deploy"]
        has_problem_focus = any(indicator in content for indicator in problem_indicators)

        if not has_problem_focus:
            self.warnings.append(f"How-to guide {file_path} should focus on solving specific problems")

    def _validate_reference_content(self, file_path: Path, content: str) -> None:
        """Validate reference content structure."""
        # Reference should be information-dense and structured
        reference_indicators = ["parameters", "returns", "example", "usage", "api", "command"]
        has_reference_structure = any(indicator in content for indicator in reference_indicators)

        if not has_reference_structure:
            self.warnings.append(f"Reference {file_path} should include structured information (parameters, examples, etc.)")

    def _validate_explanation_content(self, file_path: Path, content: str) -> None:
        """Validate explanation content structure."""
        # Explanations should focus on understanding and concepts
        explanation_indicators = ["why", "concept", "principle", "architecture", "design", "rationale"]
        has_explanation_focus = any(indicator in content for indicator in explanation_indicators)

        if not has_explanation_focus:
            self.warnings.append(f"Explanation {file_path} should focus on concepts and understanding")

    def _report_results(self) -> None:
        """Report validation results."""
        print("\n📊 Validation Results:")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All validation checks passed!")
        elif not self.errors:
            print("✅ No critical errors found (warnings can be addressed)")
        else:
            print("❌ Validation failed with errors")


def main():
    """Main entry point."""
    validator = DocumentationValidator()
    success = validator.validate_all()

    if not success:
        sys.exit(1)

    print("\n✅ Documentation validation completed successfully!")


if __name__ == "__main__":
    main()
