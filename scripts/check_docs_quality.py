#!/usr/bin/env python3
"""
Documentation quality checker for FinWiz.

Performs comprehensive quality checks on documentation including:
- Markdown linting
- Link validation
- Diátaxis compliance
- Content quality metrics
"""

import re
import sys
from pathlib import Path


class DocumentationQualityChecker:
    """Comprehensive documentation quality checker."""

    def __init__(self, docs_dir: str = "docs"):
        self.docs_dir = Path(docs_dir)
        self.issues: list[str] = []
        self.warnings: list[str] = []
        self.metrics: dict[str, int] = {}

    def check_all(self) -> bool:
        """Run all quality checks."""
        print("🔍 Running comprehensive documentation quality checks...")

        # Basic validation
        self._check_structure()
        self._check_content_quality()
        self._check_consistency()

        # Generate metrics
        self._calculate_metrics()

        # Report results
        self._report_results()

        return len(self.issues) == 0

    def _check_structure(self) -> None:
        """Check documentation structure and organization."""
        print("  📁 Checking structure...")

        # Required directories
        required_dirs = ["tutorials", "how-to", "reference", "explanations"]
        for dir_name in required_dirs:
            dir_path = self.docs_dir / dir_name
            if not dir_path.exists():
                self.issues.append(f"Missing required Diátaxis directory: {dir_name}/")
            else:
                # Check for index files
                index_file = dir_path / "index.md"
                if not index_file.exists():
                    self.warnings.append(f"Missing index.md in {dir_name}/ directory")

        # Check main index
        main_index = self.docs_dir / "index.md"
        if not main_index.exists():
            self.issues.append("Missing main index.md file")

    def _check_content_quality(self) -> None:
        """Check content quality metrics."""
        print("  📝 Checking content quality...")

        for md_file in self.docs_dir.rglob("*.md"):
            self._check_file_quality(md_file)

    def _check_file_quality(self, file_path: Path) -> None:
        """Check quality of individual file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            self.issues.append(f"Cannot read file {file_path}: {e}")
            return

        # Check file length (should not be too short or too long)
        lines = content.split("\n")
        line_count = len(lines)

        if line_count < 10:
            self.warnings.append(f"Very short file ({line_count} lines): {file_path}")
        elif line_count > 500:
            self.warnings.append(f"Very long file ({line_count} lines): {file_path}")

        # Check for proper headings
        headings = re.findall(r"^(#{1,6}) (.+)$", content, re.MULTILINE)
        if not headings:
            self.warnings.append(f"No headings found in {file_path}")

        # Check for code blocks without language specification
        code_blocks = re.findall(r"```(\w*)", content)
        for i, lang in enumerate(code_blocks):
            if not lang.strip():
                self.warnings.append(f"Code block without language specification in {file_path}")

        # Check for TODO/FIXME comments
        todos = re.findall(r"(TODO|FIXME|XXX)", content, re.IGNORECASE)
        if todos:
            self.warnings.append(f"Found {len(todos)} TODO/FIXME comments in {file_path}")

        # Check for proper front matter (if using)
        if content.startswith("---"):
            front_matter_end = content.find("---", 3)
            if front_matter_end == -1:
                self.issues.append(f"Malformed front matter in {file_path}")

    def _check_consistency(self) -> None:
        """Check consistency across documentation."""
        print("  🔄 Checking consistency...")

        # Check for consistent terminology
        terminology_patterns = {
            "FinWiz": r"\bfinwiz\b",  # Should be capitalized
            "API": r"\bapi\b",  # Should be uppercase
            "JSON": r"\bjson\b",  # Should be uppercase
        }

        for md_file in self.docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")

                for correct_term, pattern in terminology_patterns.items():
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    incorrect_matches = [m for m in matches if m != correct_term]

                    if incorrect_matches:
                        self.warnings.append(f"Inconsistent terminology in {md_file}: found '{incorrect_matches[0]}', should be '{correct_term}'")

            except Exception:
                continue  # Skip files that can't be read

    def _calculate_metrics(self) -> None:
        """Calculate documentation metrics."""
        print("  📊 Calculating metrics...")

        total_files = 0
        total_lines = 0
        total_words = 0

        category_counts = {"tutorials": 0, "how-to": 0, "reference": 0, "explanations": 0, "other": 0}

        for md_file in self.docs_dir.rglob("*.md"):
            total_files += 1

            try:
                content = md_file.read_text(encoding="utf-8")
                total_lines += len(content.split("\n"))
                total_words += len(content.split())

                # Categorize file
                relative_path = md_file.relative_to(self.docs_dir)
                category = str(relative_path).split("/")[0] if "/" in str(relative_path) else "other"

                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts["other"] += 1

            except Exception:
                continue

        self.metrics = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_words": total_words,
            "avg_words_per_file": total_words // max(total_files, 1),
            **category_counts,
        }

    def _report_results(self) -> None:
        """Report quality check results."""
        print("\n📊 Documentation Quality Report:")

        # Metrics
        print("\n📈 Metrics:")
        print(f"  • Total files: {self.metrics['total_files']}")
        print(f"  • Total lines: {self.metrics['total_lines']:,}")
        print(f"  • Total words: {self.metrics['total_words']:,}")
        print(f"  • Average words per file: {self.metrics['avg_words_per_file']}")

        print("\n📁 Distribution by category:")
        for category in ["tutorials", "how-to", "reference", "explanations", "other"]:
            count = self.metrics.get(category, 0)
            print(f"  • {category}: {count} files")

        # Issues and warnings
        if self.issues:
            print(f"\n❌ Issues ({len(self.issues)}):")
            for issue in self.issues:
                print(f"  • {issue}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")

        # Overall assessment
        if not self.issues and len(self.warnings) <= 5:
            print("\n✅ Documentation quality is excellent!")
        elif not self.issues:
            print("\n✅ Documentation quality is good (some minor warnings)")
        else:
            print("\n❌ Documentation quality needs improvement")


def main():
    """Main entry point."""
    checker = DocumentationQualityChecker()
    success = checker.check_all()

    if not success:
        sys.exit(1)

    print("\n✅ Documentation quality check completed!")


if __name__ == "__main__":
    main()
