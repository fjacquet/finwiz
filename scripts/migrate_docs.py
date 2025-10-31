#!/usr/bin/env python3
"""
Documentation Migration System for FinWiz MkDocs Site

This script migrates existing documentation to the new MkDocs structure
following the Diátaxis framework (tutorials, how-to, reference, explanations).
"""

import hashlib
import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path

import yaml

# Import Pydantic models
from migration_models import (
    CategoryStatistics,
    DiátaxisCategory,
    DocumentMigration,
    MigrationConfig,
    MigrationProgress,
    MigrationReport,
    MigrationSummary,
    ValidationStatus,
)

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Pydantic models are imported from migration_models.py


class DocumentationMigrator:
    """Main class for migrating documentation to MkDocs structure."""

    def __init__(self, config: MigrationConfig):
        """Initialize the migrator with configuration."""
        self.config = config
        self.source_dir = Path(config.source_directory)
        self.target_dir = Path(config.target_directory)
        self.rules_file = Path(config.rules_file)

        # Generate unique migration ID
        self.migration_id = str(uuid.uuid4())

        # Load migration rules
        self.migration_rules = self._load_migration_rules()

        # Initialize tracking
        self.processed_files: set[str] = set()
        self.migration_results: list[DocumentMigration] = []
        self.validation_errors: list[str] = []
        self.start_time = datetime.now()

        # Progress tracking
        self.progress = MigrationProgress(
            migration_id=self.migration_id,
            start_time=self.start_time,
            current_time=self.start_time,
            total_files=0,
            processed_files=0,
            successful_files=0,
            failed_files=0,
            current_stage="initialization",
            progress_percentage=0.0,
        )

        logger.info(f"Initialized migrator: {config.source_directory} -> {config.target_directory}")
        logger.info(f"Migration ID: {self.migration_id}")

    def _load_migration_rules(self) -> dict:
        """Load migration rules from YAML configuration file."""
        try:
            with open(self.rules_file, encoding="utf-8") as f:
                rules = yaml.safe_load(f)
            logger.info(f"Loaded migration rules from {self.rules_file}")
            return rules
        except Exception as e:
            logger.error(f"Failed to load migration rules: {e}")
            raise

    def classify_document(self, doc_path: Path) -> tuple[DiátaxisCategory, float]:
        """
        Classify a document into a Diátaxis category using pattern matching and keyword analysis.

        Returns:
            Tuple of (category, confidence_score)

        """
        doc_content = ""
        try:
            with open(doc_path, encoding="utf-8") as f:
                doc_content = f.read().lower()
        except Exception as e:
            logger.warning(f"Could not read {doc_path}: {e}")
            return DiátaxisCategory.ARCHIVE, 0.0

        # Get relative path for pattern matching
        relative_path = str(doc_path.relative_to(self.source_dir))

        # Score each category
        category_scores = {}

        for category_name, rules in self.migration_rules["classification_rules"].items():
            score = 0.0

            # Pattern matching (high weight)
            for pattern in rules.get("patterns", []):
                if self._match_pattern(relative_path, pattern):
                    score += 3.0
                    logger.debug(f"Pattern match '{pattern}' for {relative_path}")

            # Keyword matching (medium weight)
            for keyword in rules.get("keywords", []):
                if keyword in doc_content:
                    score += 1.0
                    logger.debug(f"Keyword match '{keyword}' in {relative_path}")

            # Content indicator matching (medium weight)
            for indicator in rules.get("content_indicators", []):
                if indicator in doc_content:
                    score += 1.5
                    logger.debug(f"Content indicator match '{indicator}' in {relative_path}")

            category_scores[category_name] = score

        # Find best category
        if not category_scores or max(category_scores.values()) == 0:
            return DiátaxisCategory.ARCHIVE, 0.0

        best_category = max(category_scores, key=category_scores.get)
        confidence = min(category_scores[best_category] / 5.0, 1.0)  # Normalize to 0-1

        logger.info(f"Classified {relative_path} as {best_category} (confidence: {confidence:.2f})")
        return DiátaxisCategory(best_category), confidence

    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a glob-like pattern."""
        import fnmatch

        return fnmatch.fnmatch(path, pattern)

    def transform_content(self, content: str, target_category: DiátaxisCategory, source_path: Path) -> tuple[str, list[str]]:
        """
        Transform content to match target category standards.

        Returns:
            Tuple of (transformed_content, transformations_applied)

        """
        transformations = []

        # Process front matter
        existing_front_matter, body_content = self._extract_existing_front_matter(content)

        if existing_front_matter:
            # Merge with new front matter
            new_front_matter = yaml.safe_load(self._generate_front_matter(source_path, target_category)[4:-4])  # Remove --- markers
            merged_front_matter = self._merge_front_matter(existing_front_matter, new_front_matter)

            # Reconstruct front matter
            front_matter_yaml = yaml.dump(merged_front_matter, default_flow_style=False, allow_unicode=True)
            content = f"---\n{front_matter_yaml}---\n\n{body_content}"
            transformations.append("updated_front_matter")
        else:
            # Add new front matter
            front_matter = self._generate_front_matter(source_path, target_category)
            content = front_matter + "\n\n" + body_content
            transformations.append("added_front_matter")

        # Standardize headers
        content = self._standardize_headers(content)
        transformations.append("standardized_headers")

        # Fix code blocks
        content = self._fix_code_blocks(content)
        transformations.append("fixed_code_blocks")

        # Normalize internal links
        content = self._normalize_links(content)
        transformations.append("normalized_links")

        # Add table of contents for long documents
        if content.count("\n") > 50 and target_category != DiátaxisCategory.REFERENCE:
            content = self._add_toc_placeholder(content)
            transformations.append("added_toc")

        # Clean up whitespace
        content = self._clean_whitespace(content)
        transformations.append("cleaned_whitespace")

        return content, transformations

    def _clean_whitespace(self, content: str) -> str:
        """Clean up excessive whitespace in content."""
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in content.split("\n")]

        # Remove excessive blank lines (max 2 consecutive)
        cleaned_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 2:
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)

        # Ensure file ends with single newline
        content = "\n".join(cleaned_lines).rstrip() + "\n"

        return content

    def _generate_front_matter(self, source_path: Path, category: DiátaxisCategory) -> str:
        """Generate YAML front matter for a document."""
        title = source_path.stem.replace("_", " ").replace("-", " ").title()

        # Clean up common title patterns
        title = re.sub(r"\b(Md|Guide|Documentation|Readme)\b", "", title).strip()

        # Generate description based on category
        descriptions = {
            DiátaxisCategory.TUTORIALS: f"Learn how to use {title} with step-by-step instructions",
            DiátaxisCategory.HOW_TO: f"How to configure and use {title} effectively",
            DiátaxisCategory.REFERENCE: f"Complete reference documentation for {title}",
            DiátaxisCategory.EXPLANATIONS: f"Understanding the concepts and design of {title}",
            DiátaxisCategory.ARCHIVE: f"Archived documentation for {title}",
        }

        description = descriptions.get(category, f"Documentation for {title}")

        # Generate tags based on content and category
        tags = [category.value]

        # Add specific tags based on filename patterns
        filename_lower = source_path.name.lower()
        if "api" in filename_lower:
            tags.append("api")
        if "performance" in filename_lower:
            tags.append("performance")
        if "setup" in filename_lower or "install" in filename_lower:
            tags.append("setup")
        if "config" in filename_lower:
            tags.append("configuration")
        if "test" in filename_lower:
            tags.append("testing")

        # Remove duplicates and sort
        tags = sorted(list(set(tags)))

        front_matter = f"""---
title: "{title}"
description: "{description}"
category: "{category.value}"
tags:
{chr(10).join(f'  - "{tag}"' for tag in tags)}
date: "{datetime.now().strftime("%Y-%m-%d")}"
source: "{source_path.relative_to(self.source_dir)}"
---"""

        return front_matter

    def _extract_existing_front_matter(self, content: str) -> tuple[dict, str]:
        """Extract existing YAML front matter from content."""
        if not content.startswith("---"):
            return {}, content

        try:
            # Find the end of front matter
            end_marker = content.find("---", 3)
            if end_marker == -1:
                return {}, content

            # Extract and parse YAML
            yaml_content = content[3:end_marker].strip()
            front_matter = yaml.safe_load(yaml_content) or {}

            # Return front matter and remaining content
            remaining_content = content[end_marker + 3 :].lstrip("\n")
            return front_matter, remaining_content

        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML front matter: {e}")
            return {}, content

    def _merge_front_matter(self, existing: dict, new: dict) -> dict:
        """Merge existing front matter with new front matter, preserving important fields."""
        merged = new.copy()

        # Preserve certain fields from existing front matter
        preserve_fields = ["title", "description", "author", "date_created", "custom_tags"]

        for field in preserve_fields:
            if field in existing:
                if field == "custom_tags" and "tags" in merged:
                    # Merge tags
                    existing_tags = existing[field] if isinstance(existing[field], list) else [existing[field]]
                    new_tags = merged["tags"] if isinstance(merged["tags"], list) else [merged["tags"]]
                    merged["tags"] = sorted(list(set(existing_tags + new_tags)))
                else:
                    merged[field] = existing[field]

        return merged

    def _standardize_headers(self, content: str) -> str:
        """Standardize markdown headers."""
        lines = content.split("\n")
        in_code_block = False

        for i, line in enumerate(lines):
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Fix header spacing
            if re.match(r"^#+", line):
                # Ensure single space after #
                lines[i] = re.sub(r"^(#+)\s*", r"\1 ", line)

        return "\n".join(lines)

    def _fix_code_blocks(self, content: str) -> str:
        """Fix and standardize code blocks."""
        # Fix code blocks without language specification
        content = re.sub(r"^```\s*$", "```text", content, flags=re.MULTILINE)

        # Common language mappings
        language_mappings = {"sh": "bash", "shell": "bash", "yml": "yaml", "py": "python"}

        for old_lang, new_lang in language_mappings.items():
            content = re.sub(f"^```{old_lang}", f"```{new_lang}", content, flags=re.MULTILINE)

        return content

    def _normalize_links(self, content: str) -> str:
        """Normalize internal links to work with new structure."""
        # This is a placeholder - would need more sophisticated link rewriting
        # based on the actual migration mapping
        return content

    def _add_toc_placeholder(self, content: str) -> str:
        """Add table of contents placeholder for MkDocs."""
        lines = content.split("\n")

        # Find first H2 header
        for i, line in enumerate(lines):
            if re.match(r"^## ", line):
                lines.insert(i, "[TOC]\n")
                break

        return "\n".join(lines)

    def validate_content(self, content: str, target_path: Path) -> list[str]:
        """Validate transformed content for issues."""
        issues = []

        # Check for broken internal links
        internal_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for link_text, link_url in internal_links:
            if link_url.startswith("./") or link_url.startswith("../"):
                # Check if the referenced file exists (relative to target)
                referenced_file = target_path.parent / link_url
                if not referenced_file.exists():
                    issues.append(f"Broken internal link: {link_url}")

        # Check for missing code block closures
        code_block_count = content.count("```")
        if code_block_count % 2 != 0:
            issues.append("Unmatched code block delimiters")

        # Check for very short content
        if len(content.strip()) < 100:
            issues.append("Content appears to be very short")

        # Check for missing front matter
        if not content.strip().startswith("---"):
            issues.append("Missing YAML front matter")

        # Check for proper heading hierarchy
        headers = re.findall(r"^(#+)\s+(.+)$", content, re.MULTILINE)
        if headers:
            # Should start with H1
            first_header_level = len(headers[0][0])
            if first_header_level != 1:
                issues.append("Document should start with H1 header")

            # Check for skipped header levels
            prev_level = 0
            for header_marks, header_text in headers:
                level = len(header_marks)
                if level > prev_level + 1:
                    issues.append(f"Skipped header level: H{prev_level} to H{level}")
                prev_level = level

        # Check for TODO/FIXME markers
        if re.search(r"\b(TODO|FIXME|XXX)\b", content, re.IGNORECASE):
            issues.append("Contains TODO/FIXME markers")

        # Check for placeholder content
        placeholder_patterns = [r"lorem ipsum", r"placeholder", r"coming soon", r"to be documented"]
        for pattern in placeholder_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"Contains placeholder content: {pattern}")

        return issues

    def migrate_document(self, source_path: Path) -> DocumentMigration:
        """Migrate a single document."""
        start_time = time.time()

        try:
            # Get file size
            file_size = source_path.stat().st_size

            # Classify document
            category, confidence = self.classify_document(source_path)

            # Skip if confidence is too low
            if confidence < self.config.min_confidence_score:
                logger.warning(f"Low confidence ({confidence:.2f}) for {source_path}, moving to archive")
                category = DiátaxisCategory.ARCHIVE

            # Determine target path
            target_path = self._determine_target_path(source_path, category)

            # Read source content
            with open(source_path, encoding="utf-8") as f:
                content = f.read()

            # Transform content
            transformed_content, transformations = self.transform_content(content, category, source_path)

            # Validate content
            issues = self.validate_content(transformed_content, target_path)

            # Determine validation status
            if len(issues) > self.config.max_issues_per_document:
                validation_status = ValidationStatus.FAILED
            elif issues:
                validation_status = ValidationStatus.WARNING
            else:
                validation_status = ValidationStatus.SUCCESS

            # Create target directory
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write transformed content (only if not failed)
            if validation_status != ValidationStatus.FAILED:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(transformed_content)

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Create migration record
            migration = DocumentMigration(
                source_path=str(source_path),
                target_path=str(target_path) if validation_status != ValidationStatus.FAILED else "",
                category=category,
                transformations_applied=transformations,
                validation_status=validation_status,
                issues=issues,
                confidence_score=confidence,
                file_size_bytes=file_size,
                processing_time_ms=processing_time,
            )

            logger.info(f"Migrated {source_path} -> {target_path} ({validation_status.value})")
            return migration

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Failed to migrate {source_path}: {e}")

            return DocumentMigration(
                source_path=str(source_path),
                target_path="",
                category=DiátaxisCategory.ARCHIVE,
                transformations_applied=[],
                validation_status=ValidationStatus.FAILED,
                issues=[str(e)],
                confidence_score=0.0,
                file_size_bytes=source_path.stat().st_size if source_path.exists() else 0,
                processing_time_ms=processing_time,
            )

    def _determine_target_path(self, source_path: Path, category: DiátaxisCategory) -> Path:
        """Determine the target path for a migrated document."""
        relative_path = source_path.relative_to(self.source_dir)

        # Generate appropriate filename
        filename = source_path.name

        # Clean up filename for better organization
        if category == DiátaxisCategory.TUTORIALS:
            if "user_guide" in filename.lower():
                filename = "getting_started.md"
            elif "portfolio_holdings_analysis" in filename.lower():
                filename = "portfolio_analysis.md"

        elif category == DiátaxisCategory.HOW_TO:
            # Normalize how-to guide names
            filename = filename.lower().replace("_", "_")
            if filename.startswith("performance_"):
                filename = "performance_optimization.md"

        # Construct target path
        target_path = self.target_dir / category.value / filename

        # Handle conflicts
        counter = 1
        original_target = target_path
        while target_path.exists():
            stem = original_target.stem
            suffix = original_target.suffix
            target_path = original_target.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        return target_path

    def migrate_all(self) -> MigrationReport:
        """Migrate all documentation following Diátaxis classification."""
        # Find all markdown files
        markdown_files = list(self.source_dir.rglob("*.md"))

        # Update progress tracking
        self.progress.total_files = len(markdown_files)
        self.progress.current_stage = "processing_files"

        logger.info(f"Found {len(markdown_files)} markdown files to process")

        # Process each file
        for i, md_file in enumerate(markdown_files):
            # Update progress
            self.progress.processed_files = i
            self.progress.current_file = str(md_file)
            self.progress.current_time = datetime.now()
            self.progress.progress_percentage = (i / len(markdown_files)) * 100

            # Skip already processed files
            if str(md_file) in self.processed_files:
                continue

            # Skip certain directories/files
            if self._should_skip_file(md_file):
                logger.debug(f"Skipping {md_file}")
                continue

            migration = self.migrate_document(md_file)
            self.migration_results.append(migration)
            self.processed_files.add(str(md_file))

            # Update success/failure counts
            if migration.validation_status == ValidationStatus.FAILED:
                self.progress.failed_files += 1
            else:
                self.progress.successful_files += 1

        # Final progress update
        self.progress.processed_files = len(markdown_files)
        self.progress.progress_percentage = 100.0
        self.progress.current_stage = "generating_report"

        # Generate comprehensive report
        report = self._generate_comprehensive_report()

        logger.info(f"Migration completed in {report.summary.processing_time_seconds:.2f} seconds")
        logger.info(f"Successfully migrated: {report.summary.successful_migrations}")
        logger.info(f"Failed migrations: {report.summary.failed_migrations}")

        return report

    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during migration."""
        relative_path = str(file_path.relative_to(self.source_dir))

        # Skip certain patterns
        skip_patterns = [
            "site/**",  # Generated site files
            "**/node_modules/**",
            "**/.git/**",
            "**/.*",  # Hidden files
        ]

        for pattern in skip_patterns:
            if self._match_pattern(relative_path, pattern):
                return True

        return False

    def _generate_comprehensive_report(self) -> MigrationReport:
        """Generate a comprehensive migration report with detailed statistics."""
        end_time = datetime.now()
        processing_time = (end_time - self.start_time).total_seconds()

        # Separate migrations by status
        successful = [m for m in self.migration_results if m.validation_status != ValidationStatus.FAILED]
        failed = [m for m in self.migration_results if m.validation_status == ValidationStatus.FAILED]
        warnings = [m for m in self.migration_results if m.validation_status == ValidationStatus.WARNING]

        # Calculate category distribution
        category_distribution = {}
        for category in DiátaxisCategory:
            category_distribution[category] = len([m for m in successful if m.category == category])

        # Calculate total size
        total_size = sum(m.file_size_bytes or 0 for m in self.migration_results)

        # Generate summary
        summary = MigrationSummary(
            total_documents=len(self.migration_results),
            successful_migrations=len(successful),
            failed_migrations=len(failed),
            warnings_count=len(warnings),
            total_size_bytes=total_size,
            processing_time_seconds=processing_time,
            avg_processing_time_ms=sum(m.processing_time_ms or 0 for m in self.migration_results) / len(self.migration_results) if self.migration_results else 0,
            category_distribution=category_distribution,
        )

        # Generate category statistics
        category_stats = []
        for category in DiátaxisCategory:
            category_docs = [m for m in successful if m.category == category]
            if category_docs:
                avg_confidence = sum(m.confidence_score for m in category_docs) / len(category_docs)
                total_category_size = sum(m.file_size_bytes or 0 for m in category_docs)
                success_rate = len([m for m in category_docs if m.validation_status == ValidationStatus.SUCCESS]) / len(category_docs)

                # Find common issues
                all_issues = []
                for doc in category_docs:
                    all_issues.extend(doc.issues)
                common_issues = list(set(all_issues))[:5]  # Top 5 unique issues

                category_stats.append(
                    CategoryStatistics(
                        category=category,
                        document_count=len(category_docs),
                        total_size_bytes=total_category_size,
                        avg_confidence_score=avg_confidence,
                        success_rate=success_rate,
                        common_issues=common_issues,
                    )
                )

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics()

        # Generate configuration hash for reproducibility
        config_hash = self._generate_config_hash()

        # Create comprehensive report
        report = MigrationReport(
            migration_id=self.migration_id,
            migration_timestamp=self.start_time,
            source_directory=str(self.source_dir),
            target_directory=str(self.target_dir),
            summary=summary,
            category_statistics=category_stats,
            migrated_documents=successful,
            failed_migrations=failed,
            validation_errors=self.validation_errors,
            quality_metrics=quality_metrics,
            migration_rules_file=str(self.rules_file),
            configuration_hash=config_hash,
        )

        return report

    def _calculate_quality_metrics(self) -> dict[str, float]:
        """Calculate overall quality metrics for the migration."""
        if not self.migration_results:
            return {}

        total_docs = len(self.migration_results)
        successful_docs = len([m for m in self.migration_results if m.validation_status != ValidationStatus.FAILED])

        metrics = {
            "success_rate": successful_docs / total_docs if total_docs > 0 else 0,
            "avg_confidence_score": sum(m.confidence_score for m in self.migration_results) / total_docs,
            "avg_issues_per_document": sum(len(m.issues) for m in self.migration_results) / total_docs,
            "high_confidence_rate": len([m for m in self.migration_results if m.confidence_score >= 0.8]) / total_docs,
            "low_confidence_rate": len([m for m in self.migration_results if m.confidence_score < 0.3]) / total_docs,
        }

        return metrics

    def _generate_config_hash(self) -> str:
        """Generate a hash of the configuration for reproducibility."""
        config_str = json.dumps(
            {
                "rules_file": str(self.rules_file),
                "source_dir": str(self.source_dir),
                "target_dir": str(self.target_dir),
                "min_confidence_score": self.config.min_confidence_score,
                "max_issues_per_document": self.config.max_issues_per_document,
            },
            sort_keys=True,
        )

        return hashlib.md5(config_str.encode()).hexdigest()

    def generate_migration_report(self, report: MigrationReport, output_file: str = None) -> str:
        """Generate a detailed migration report."""
        if output_file is None:
            output_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert report to JSON-serializable format
        report_data = {
            "total_documents": report.total_documents,
            "migration_timestamp": report.migration_timestamp,
            "processing_time": report.processing_time,
            "summary": {k.value: v for k, v in report.summary.items()},
            "migrated_documents": [
                {
                    "source_path": m.source_path,
                    "target_path": m.target_path,
                    "category": m.category.value,
                    "transformations_applied": m.transformations_applied,
                    "validation_status": m.validation_status,
                    "issues": m.issues,
                    "confidence_score": m.confidence_score,
                }
                for m in report.migrated_documents
            ],
            "failed_migrations": [{"source_path": m.source_path, "category": m.category.value, "issues": m.issues} for m in report.failed_migrations],
            "validation_errors": report.validation_errors,
        }

        # Write report
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Migration report saved to {output_file}")
        return output_file


def main():
    """Main entry point for the migration script."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate FinWiz documentation to MkDocs structure")
    parser.add_argument("--source", default="docs", help="Source documentation directory")
    parser.add_argument("--target", default="docs_migrated", help="Target directory for migrated docs")
    parser.add_argument("--rules", default="scripts/migration_rules.yml", help="Migration rules file")
    parser.add_argument("--report", help="Output file for migration report")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without doing it")

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE - No files will be modified")
        # TODO: Implement dry run functionality
        return

    # Create configuration
    config = MigrationConfig(source_directory=args.source, target_directory=args.target, rules_file=args.rules)

    # Create migrator and run migration
    migrator = DocumentationMigrator(config)
    report = migrator.migrate_all()

    # Generate report
    report_file = migrator.generate_migration_report(report, args.report)

    print("\nMigration Summary:")
    print(f"Migration ID: {report.migration_id}")
    print(f"Total documents processed: {report.summary.total_documents}")
    print(f"Successfully migrated: {report.summary.successful_migrations}")
    print(f"Failed migrations: {report.summary.failed_migrations}")
    print(f"Warnings: {report.summary.warnings_count}")
    print(f"Processing time: {report.summary.processing_time_seconds:.2f} seconds")
    print("\nCategory distribution:")
    for category, count in report.summary.category_distribution.items():
        print(f"  {category.value}: {count}")
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
