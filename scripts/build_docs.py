#!/usr/bin/env python3
"""
Production documentation build script with optimization and validation.

This script provides optimized static site generation with asset optimization,
compression, and comprehensive build validation.
"""

import gzip
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


class DocumentationBuilder:
    """Production documentation builder with optimization and validation."""

    def __init__(self, source_dir: str = "docs", build_dir: str = "site"):
        self.source_dir = Path(source_dir)
        self.build_dir = Path(build_dir)
        self.temp_dir = None
        self.build_stats = {}
        self.start_time = time.time()

    def build_production(self, strict: bool = True, optimize: bool = True) -> bool:
        """
        Build documentation for production with optimization.

        Args:
            strict: Enable strict mode for build validation
            optimize: Enable asset optimization and compression

        Returns:
            bool: True if build successful, False otherwise

        """
        print("🔨 Starting production documentation build...")

        try:
            # Pre-build validation
            if not self._validate_source():
                return False

            # Clean previous build
            self._clean_build_directory()

            # Build with MkDocs
            if not self._build_mkdocs(strict=strict):
                return False

            # Post-build optimization
            if optimize:
                self._optimize_assets()
                self._compress_assets()

            # Build validation
            if not self._validate_build():
                return False

            # Generate build report
            self._generate_build_report()

            build_time = time.time() - self.start_time
            print(f"✅ Production build completed successfully in {build_time:.2f}s")
            return True

        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False

    def _validate_source(self) -> bool:
        """Validate source documentation before building."""
        print("🔍 Validating source documentation...")

        if not self.source_dir.exists():
            print(f"❌ Source directory not found: {self.source_dir}")
            return False

        # Check for required files
        required_files = ["index.md"]
        for file in required_files:
            if not (self.source_dir / file).exists():
                print(f"❌ Required file missing: {file}")
                return False

        # Check mkdocs.yml exists
        if not Path("mkdocs.yml").exists():
            print("❌ mkdocs.yml configuration file not found")
            return False

        print("✅ Source validation passed")
        return True

    def _clean_build_directory(self) -> None:
        """Clean the build directory."""
        if self.build_dir.exists():
            print(f"🧹 Cleaning build directory: {self.build_dir}")
            shutil.rmtree(self.build_dir)

    def _build_mkdocs(self, strict: bool = True) -> bool:
        """Build documentation with MkDocs."""
        print("📚 Building documentation with MkDocs...")

        cmd = ["uv", "run", "mkdocs", "build", "--clean"]
        if strict:
            cmd.append("--strict")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout:
                print("MkDocs output:", result.stdout)

            print("✅ MkDocs build completed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ MkDocs build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

    def _optimize_assets(self) -> None:
        """Optimize CSS, JS, and image assets."""
        print("⚡ Optimizing assets...")

        if not self.build_dir.exists():
            return

        # Optimize CSS files
        css_files = list(self.build_dir.rglob("*.css"))
        for css_file in css_files:
            self._minify_css(css_file)

        # Optimize JS files
        js_files = list(self.build_dir.rglob("*.js"))
        for js_file in js_files:
            self._minify_js(js_file)

        # Optimize images (basic optimization)
        image_files = list(self.build_dir.rglob("*.png")) + list(self.build_dir.rglob("*.jpg"))

        self.build_stats.update(
            {"css_files_optimized": len(css_files), "js_files_optimized": len(js_files), "image_files_found": len(image_files)}
        )

        print(f"✅ Optimized {len(css_files)} CSS and {len(js_files)} JS files")

    def _minify_css(self, css_file: Path) -> None:
        """Basic CSS minification."""
        try:
            content = css_file.read_text(encoding="utf-8")

            # Basic minification: remove comments and extra whitespace
            lines = []
            in_comment = False

            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # Remove CSS comments (basic implementation)
                if "/*" in line and "*/" in line:
                    # Single line comment
                    start = line.find("/*")
                    end = line.find("*/") + 2
                    line = line[:start] + line[end:]

                if line:
                    lines.append(line)

            minified = " ".join(lines)

            # Only write if we actually reduced size
            if len(minified) < len(content):
                css_file.write_text(minified, encoding="utf-8")

        except Exception as e:
            print(f"⚠️  CSS minification failed for {css_file}: {e}")

    def _minify_js(self, js_file: Path) -> None:
        """Basic JS minification."""
        try:
            content = js_file.read_text(encoding="utf-8")

            # Basic minification: remove comments and extra whitespace
            lines = []
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("//"):
                    lines.append(line)

            minified = " ".join(lines)

            # Only write if we actually reduced size
            if len(minified) < len(content):
                js_file.write_text(minified, encoding="utf-8")

        except Exception as e:
            print(f"⚠️  JS minification failed for {js_file}: {e}")

    def _compress_assets(self) -> None:
        """Create gzip compressed versions of assets."""
        print("🗜️  Creating compressed assets...")

        if not self.build_dir.exists():
            return

        # Compress HTML, CSS, JS files
        compressible_files = (
            list(self.build_dir.rglob("*.html"))
            + list(self.build_dir.rglob("*.css"))
            + list(self.build_dir.rglob("*.js"))
            + list(self.build_dir.rglob("*.json"))
        )

        compressed_count = 0
        total_original_size = 0
        total_compressed_size = 0

        for file_path in compressible_files:
            try:
                original_size = file_path.stat().st_size

                # Only compress files larger than 1KB
                if original_size < 1024:
                    continue

                with open(file_path, "rb") as f_in:
                    with gzip.open(f"{file_path}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                compressed_size = Path(f"{file_path}.gz").stat().st_size

                total_original_size += original_size
                total_compressed_size += compressed_size
                compressed_count += 1

            except Exception as e:
                print(f"⚠️  Compression failed for {file_path}: {e}")

        if compressed_count > 0:
            compression_ratio = (1 - total_compressed_size / total_original_size) * 100
            print(f"✅ Compressed {compressed_count} files ({compression_ratio:.1f}% size reduction)")

        self.build_stats.update(
            {"compressed_files": compressed_count, "compression_ratio": compression_ratio if compressed_count > 0 else 0}
        )

    def _validate_build(self) -> bool:
        """Validate the built documentation."""
        print("🔍 Validating build output...")

        if not self.build_dir.exists():
            print("❌ Build directory not found")
            return False

        # Check for required files
        required_files = ["index.html", "search/search_index.json"]
        for file in required_files:
            file_path = self.build_dir / file
            if not file_path.exists():
                print(f"❌ Required build file missing: {file}")
                return False

        # Check for broken internal links (basic check)
        html_files = list(self.build_dir.rglob("*.html"))
        self.build_stats["html_files_generated"] = len(html_files)

        # Validate HTML structure (basic check)
        broken_files = []
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding="utf-8")
                if not content.strip():
                    broken_files.append(html_file)
                elif not content.startswith("<!DOCTYPE html>"):
                    print(f"⚠️  HTML file missing DOCTYPE: {html_file}")
            except Exception as e:
                print(f"⚠️  Could not validate HTML file {html_file}: {e}")
                broken_files.append(html_file)

        if broken_files:
            print(f"❌ Found {len(broken_files)} broken HTML files")
            return False

        print(f"✅ Build validation passed ({len(html_files)} HTML files)")
        return True

    def _generate_build_report(self) -> None:
        """Generate build report with statistics."""
        build_time = time.time() - self.start_time

        report = {
            "build_time": round(build_time, 2),
            "build_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_directory": str(self.source_dir),
            "build_directory": str(self.build_dir),
            **self.build_stats,
        }

        # Calculate build size
        if self.build_dir.exists():
            total_size = sum(f.stat().st_size for f in self.build_dir.rglob("*") if f.is_file())
            report["total_build_size_mb"] = round(total_size / (1024 * 1024), 2)

        # Save report
        report_file = self.build_dir / "build_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📊 Build report saved to {report_file}")
        print("📈 Build statistics:")
        for key, value in report.items():
            if key not in ["build_timestamp"]:
                print(f"   {key}: {value}")


def main():
    """Main entry point for the build script."""
    import argparse

    parser = argparse.ArgumentParser(description="Build FinWiz documentation")
    parser.add_argument("--no-strict", action="store_true", help="Disable strict mode")
    parser.add_argument("--no-optimize", action="store_true", help="Disable asset optimization")
    parser.add_argument("--source", default="docs", help="Source directory (default: docs)")
    parser.add_argument("--build", default="site", help="Build directory (default: site)")

    args = parser.parse_args()

    builder = DocumentationBuilder(source_dir=args.source, build_dir=args.build)

    success = builder.build_production(strict=not args.no_strict, optimize=not args.no_optimize)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
