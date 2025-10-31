#!/usr/bin/env python3
"""
Build validation script for documentation site.

This script validates the built documentation site for common issues,
performance problems, and deployment readiness.
"""

import json
import re
import sys
from pathlib import Path


class BuildValidator:
    """Validates built documentation site for deployment readiness."""

    def __init__(self, build_dir: str = "site"):
        self.build_dir = Path(build_dir)
        self.validation_results = {"errors": [], "warnings": [], "info": [], "stats": {}}

    def validate_all(self) -> bool:
        """
        Run all validation checks.

        Returns:
            bool: True if validation passes, False if critical errors found

        """
        print("🔍 Starting comprehensive build validation...")

        if not self.build_dir.exists():
            self._add_error(f"Build directory not found: {self.build_dir}")
            return False

        # Run all validation checks
        self._validate_structure()
        self._validate_html_files()
        self._validate_links()
        self._validate_assets()
        self._validate_search()
        self._validate_performance()
        self._validate_accessibility()

        # Generate summary
        self._generate_summary()

        # Return success if no critical errors
        return len(self.validation_results["errors"]) == 0

    def _add_error(self, message: str) -> None:
        """Add error message."""
        self.validation_results["errors"].append(message)
        print(f"❌ ERROR: {message}")

    def _add_warning(self, message: str) -> None:
        """Add warning message."""
        self.validation_results["warnings"].append(message)
        print(f"⚠️  WARNING: {message}")

    def _add_info(self, message: str) -> None:
        """Add info message."""
        self.validation_results["info"].append(message)
        print(f"ℹ️  INFO: {message}")

    def _validate_structure(self) -> None:
        """Validate basic site structure."""
        print("📁 Validating site structure...")

        # Required files
        required_files = ["index.html", "search/search_index.json", "sitemap.xml"]

        for file_path in required_files:
            full_path = self.build_dir / file_path
            if not full_path.exists():
                self._add_error(f"Required file missing: {file_path}")
            else:
                self._add_info(f"Required file found: {file_path}")

        # Count files by type
        html_files = list(self.build_dir.rglob("*.html"))
        css_files = list(self.build_dir.rglob("*.css"))
        js_files = list(self.build_dir.rglob("*.js"))

        self.validation_results["stats"].update({"html_files": len(html_files), "css_files": len(css_files), "js_files": len(js_files)})

        self._add_info(f"Found {len(html_files)} HTML files")
        self._add_info(f"Found {len(css_files)} CSS files")
        self._add_info(f"Found {len(js_files)} JS files")

    def _validate_html_files(self) -> None:
        """Validate HTML file structure and content."""
        print("📄 Validating HTML files...")

        html_files = list(self.build_dir.rglob("*.html"))

        for html_file in html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for DOCTYPE
                if not content.strip().startswith("<!DOCTYPE html>"):
                    self._add_warning(f"Missing DOCTYPE in {html_file.relative_to(self.build_dir)}")

                # Check for basic HTML structure
                if "<html" not in content:
                    self._add_error(f"Missing <html> tag in {html_file.relative_to(self.build_dir)}")

                if "<head>" not in content:
                    self._add_error(f"Missing <head> section in {html_file.relative_to(self.build_dir)}")

                if "<body>" not in content:
                    self._add_error(f"Missing <body> section in {html_file.relative_to(self.build_dir)}")

                # Check for title
                if "<title>" not in content:
                    self._add_warning(f"Missing <title> tag in {html_file.relative_to(self.build_dir)}")

                # Check for meta charset
                if "charset=" not in content:
                    self._add_warning(f"Missing charset declaration in {html_file.relative_to(self.build_dir)}")

                # Check for viewport meta tag (mobile responsiveness)
                if 'name="viewport"' not in content:
                    self._add_warning(f"Missing viewport meta tag in {html_file.relative_to(self.build_dir)}")

            except Exception as e:
                self._add_error(f"Could not read HTML file {html_file.relative_to(self.build_dir)}: {e}")

    def _validate_links(self) -> None:
        """Validate internal links."""
        print("🔗 Validating internal links...")

        html_files = list(self.build_dir.rglob("*.html"))
        all_pages = set()
        broken_links = []

        # Collect all available pages
        for html_file in html_files:
            rel_path = html_file.relative_to(self.build_dir)
            all_pages.add(str(rel_path))

            # Also add without .html extension
            if str(rel_path).endswith(".html"):
                all_pages.add(str(rel_path)[:-5])

        # Check links in each HTML file
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Find all href attributes
                href_pattern = r'href=["\']([^"\']+)["\']'
                links = re.findall(href_pattern, content)

                for link in links:
                    # Skip external links
                    if link.startswith(("http://", "https://", "mailto:", "tel:")):
                        continue

                    # Skip anchors and fragments
                    if link.startswith("#"):
                        continue

                    # Remove fragment from link
                    clean_link = link.split("#")[0]

                    if not clean_link:
                        continue

                    # Check if link exists
                    target_path = self.build_dir / clean_link

                    # Try with .html extension if not found
                    if not target_path.exists() and not clean_link.endswith(".html"):
                        target_path = self.build_dir / f"{clean_link}.html"

                    if not target_path.exists():
                        broken_links.append({"source": str(html_file.relative_to(self.build_dir)), "target": clean_link})

            except Exception as e:
                self._add_warning(f"Could not check links in {html_file.relative_to(self.build_dir)}: {e}")

        # Report broken links
        if broken_links:
            for broken in broken_links:
                self._add_error(f"Broken link in {broken['source']}: {broken['target']}")
        else:
            self._add_info("No broken internal links found")

        self.validation_results["stats"]["broken_links"] = len(broken_links)

    def _validate_assets(self) -> None:
        """Validate CSS, JS, and image assets."""
        print("🎨 Validating assets...")

        # Check CSS files
        css_files = list(self.build_dir.rglob("*.css"))
        large_css_files = []

        for css_file in css_files:
            size_mb = css_file.stat().st_size / (1024 * 1024)
            if size_mb > 1.0:  # Warn if CSS file is larger than 1MB
                large_css_files.append((css_file, size_mb))

        if large_css_files:
            for css_file, size_mb in large_css_files:
                self._add_warning(f"Large CSS file: {css_file.relative_to(self.build_dir)} ({size_mb:.2f}MB)")

        # Check JS files
        js_files = list(self.build_dir.rglob("*.js"))
        large_js_files = []

        for js_file in js_files:
            size_mb = js_file.stat().st_size / (1024 * 1024)
            if size_mb > 2.0:  # Warn if JS file is larger than 2MB
                large_js_files.append((js_file, size_mb))

        if large_js_files:
            for js_file, size_mb in large_js_files:
                self._add_warning(f"Large JS file: {js_file.relative_to(self.build_dir)} ({size_mb:.2f}MB)")

        # Check for compressed versions
        compressible_files = css_files + js_files + list(self.build_dir.rglob("*.html"))
        compressed_count = 0

        for file_path in compressible_files:
            gz_path = Path(f"{file_path}.gz")
            if gz_path.exists():
                compressed_count += 1

        compression_ratio = compressed_count / len(compressible_files) if compressible_files else 0

        if compression_ratio < 0.5:
            self._add_warning(f"Low compression coverage: {compression_ratio:.1%} of files have .gz versions")
        else:
            self._add_info(f"Good compression coverage: {compression_ratio:.1%} of files compressed")

        self.validation_results["stats"]["compression_ratio"] = compression_ratio

    def _validate_search(self) -> None:
        """Validate search functionality."""
        print("🔍 Validating search functionality...")

        search_index_path = self.build_dir / "search" / "search_index.json"

        if not search_index_path.exists():
            self._add_error("Search index not found")
            return

        try:
            with open(search_index_path, encoding="utf-8") as f:
                search_data = json.load(f)

            # Check search index structure
            if not isinstance(search_data, dict):
                self._add_error("Invalid search index format")
                return

            # Count indexed documents
            docs_count = len(search_data.get("docs", []))

            if docs_count == 0:
                self._add_warning("Search index is empty")
            else:
                self._add_info(f"Search index contains {docs_count} documents")

            self.validation_results["stats"]["search_documents"] = docs_count

        except Exception as e:
            self._add_error(f"Could not validate search index: {e}")

    def _validate_performance(self) -> None:
        """Validate performance-related aspects."""
        print("⚡ Validating performance aspects...")

        # Calculate total site size
        total_size = 0
        file_count = 0

        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                file_count += 1

        total_size_mb = total_size / (1024 * 1024)

        # Warn if site is very large
        if total_size_mb > 100:
            self._add_warning(f"Large site size: {total_size_mb:.2f}MB")
        else:
            self._add_info(f"Site size: {total_size_mb:.2f}MB ({file_count} files)")

        # Check for large individual files
        large_files = []
        for file_path in self.build_dir.rglob("*"):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                if size_mb > 5:  # Files larger than 5MB
                    large_files.append((file_path, size_mb))

        if large_files:
            for file_path, size_mb in large_files:
                self._add_warning(f"Large file: {file_path.relative_to(self.build_dir)} ({size_mb:.2f}MB)")

        self.validation_results["stats"].update({"total_size_mb": round(total_size_mb, 2), "file_count": file_count, "large_files": len(large_files)})

    def _validate_accessibility(self) -> None:
        """Validate basic accessibility features."""
        print("♿ Validating accessibility features...")

        html_files = list(self.build_dir.rglob("*.html"))
        accessibility_issues = []

        for html_file in html_files:
            try:
                content = html_file.read_text(encoding="utf-8")

                # Check for alt attributes on images
                img_pattern = r"<img[^>]*>"
                images = re.findall(img_pattern, content)

                for img in images:
                    if "alt=" not in img:
                        accessibility_issues.append(
                            {
                                "file": str(html_file.relative_to(self.build_dir)),
                                "issue": "Image without alt attribute",
                                "element": img[:100] + "..." if len(img) > 100 else img,
                            }
                        )

                # Check for heading structure
                h1_count = len(re.findall(r"<h1[^>]*>", content))
                if h1_count == 0:
                    accessibility_issues.append({"file": str(html_file.relative_to(self.build_dir)), "issue": "No H1 heading found", "element": None})
                elif h1_count > 1:
                    accessibility_issues.append(
                        {
                            "file": str(html_file.relative_to(self.build_dir)),
                            "issue": f"Multiple H1 headings ({h1_count})",
                            "element": None,
                        }
                    )

            except Exception as e:
                self._add_warning(f"Could not check accessibility in {html_file.relative_to(self.build_dir)}: {e}")

        # Report accessibility issues
        for issue in accessibility_issues:
            self._add_warning(f"Accessibility: {issue['issue']} in {issue['file']}")

        self.validation_results["stats"]["accessibility_issues"] = len(accessibility_issues)

    def _generate_summary(self) -> None:
        """Generate validation summary."""
        errors = len(self.validation_results["errors"])
        warnings = len(self.validation_results["warnings"])

        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        if errors == 0:
            print("✅ VALIDATION PASSED")
        else:
            print("❌ VALIDATION FAILED")

        print(f"Errors: {errors}")
        print(f"Warnings: {warnings}")
        print(f"Info messages: {len(self.validation_results['info'])}")

        # Print statistics
        if self.validation_results["stats"]:
            print("\n📈 Statistics:")
            for key, value in self.validation_results["stats"].items():
                print(f"  {key}: {value}")

        # Save detailed report
        report_file = self.build_dir / "validation_report.json"
        with open(report_file, "w") as f:
            json.dump(self.validation_results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")


def main():
    """Main entry point for the validation script."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate built documentation site")
    parser.add_argument("--build-dir", default="site", help="Build directory to validate (default: site)")
    parser.add_argument("--fail-on-warnings", action="store_true", help="Fail validation if warnings are found")

    args = parser.parse_args()

    validator = BuildValidator(build_dir=args.build_dir)
    success = validator.validate_all()

    # Check if we should fail on warnings
    if success and args.fail_on_warnings:
        warnings = len(validator.validation_results["warnings"])
        if warnings > 0:
            print(f"\n❌ Failing due to {warnings} warnings (--fail-on-warnings enabled)")
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
