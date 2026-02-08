"""
Pydantic models for documentation migration system.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DiátaxisCategory(StrEnum):
    """Diátaxis framework categories for documentation organization."""

    TUTORIALS = "tutorials"
    HOW_TO = "how-to"
    REFERENCE = "reference"
    EXPLANATIONS = "explanations"
    ARCHIVE = "archive"


class ValidationStatus(StrEnum):
    """Status of document validation."""

    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"


class DocumentMigration(BaseModel):
    """Represents a single document migration with validation."""

    source_path: str = Field(..., description="Original file path")
    target_path: str = Field(..., description="Migrated file path")
    category: DiátaxisCategory = Field(..., description="Assigned Diátaxis category")
    transformations_applied: list[str] = Field(default_factory=list, description="List of transformations performed")
    validation_status: ValidationStatus = Field(..., description="Validation result")
    issues: list[str] = Field(default_factory=list, description="Validation issues found")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Classification confidence (0-1)")
    file_size_bytes: int | None = Field(None, description="Original file size in bytes")
    processing_time_ms: float | None = Field(None, description="Processing time in milliseconds")

    class Config:
        use_enum_values = True


class CategoryStatistics(BaseModel):
    """Statistics for a specific Diátaxis category."""

    category: DiátaxisCategory
    document_count: int = Field(ge=0, description="Number of documents in category")
    total_size_bytes: int = Field(ge=0, description="Total size of documents in bytes")
    avg_confidence_score: float = Field(ge=0.0, le=1.0, description="Average classification confidence")
    success_rate: float = Field(ge=0.0, le=1.0, description="Percentage of successful migrations")
    common_issues: list[str] = Field(default_factory=list, description="Most common validation issues")

    class Config:
        use_enum_values = True


class MigrationSummary(BaseModel):
    """Summary statistics for the entire migration."""

    total_documents: int = Field(ge=0, description="Total number of documents processed")
    successful_migrations: int = Field(ge=0, description="Number of successful migrations")
    failed_migrations: int = Field(ge=0, description="Number of failed migrations")
    warnings_count: int = Field(ge=0, description="Number of migrations with warnings")
    total_size_bytes: int = Field(ge=0, description="Total size of all processed documents")
    processing_time_seconds: float = Field(ge=0.0, description="Total processing time")
    avg_processing_time_ms: float = Field(ge=0.0, description="Average processing time per document")
    category_distribution: dict[DiátaxisCategory, int] = Field(default_factory=dict, description="Documents per category")

    class Config:
        use_enum_values = True


class MigrationReport(BaseModel):
    """Complete migration report with detailed results and statistics."""

    migration_id: str = Field(..., description="Unique identifier for this migration")
    migration_timestamp: datetime = Field(..., description="When the migration was performed")
    source_directory: str = Field(..., description="Source documentation directory")
    target_directory: str = Field(..., description="Target documentation directory")

    # Summary statistics
    summary: MigrationSummary = Field(..., description="Overall migration statistics")

    # Category-specific statistics
    category_statistics: list[CategoryStatistics] = Field(default_factory=list, description="Per-category statistics")

    # Detailed migration results
    migrated_documents: list[DocumentMigration] = Field(default_factory=list, description="Successfully migrated documents")
    failed_migrations: list[DocumentMigration] = Field(default_factory=list, description="Failed migration attempts")

    # Validation and quality metrics
    validation_errors: list[str] = Field(default_factory=list, description="Global validation errors")
    quality_metrics: dict[str, float] = Field(default_factory=dict, description="Quality assessment metrics")

    # Configuration used
    migration_rules_file: str | None = Field(None, description="Path to migration rules file used")
    configuration_hash: str | None = Field(None, description="Hash of configuration for reproducibility")

    class Config:
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MigrationConfig(BaseModel):
    """Configuration for the migration process."""

    source_directory: str = Field(..., description="Source documentation directory")
    target_directory: str = Field(..., description="Target documentation directory")
    rules_file: str = Field(default="scripts/migration_rules.yml", description="Migration rules configuration file")

    # Processing options
    backup_original: bool = Field(default=True, description="Create backup of original files")
    create_redirects: bool = Field(default=True, description="Generate redirect files for moved content")
    preserve_git_history: bool = Field(default=True, description="Attempt to preserve git history")
    validate_after_migration: bool = Field(default=True, description="Validate content after migration")

    # Output options
    generate_report: bool = Field(default=True, description="Generate detailed migration report")
    report_format: str = Field(default="json", pattern="^(json|yaml|html)$", description="Report output format")
    verbose_logging: bool = Field(default=False, description="Enable verbose logging")

    # Quality thresholds
    min_confidence_score: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum confidence for auto-classification")
    max_issues_per_document: int = Field(default=10, ge=0, description="Maximum validation issues before marking as failed")

    class Config:
        use_enum_values = True


class LinkValidationResult(BaseModel):
    """Result of link validation for a document."""

    document_path: str = Field(..., description="Path to the document")
    total_links: int = Field(ge=0, description="Total number of links found")
    valid_links: int = Field(ge=0, description="Number of valid links")
    broken_links: list[str] = Field(default_factory=list, description="List of broken link URLs")
    external_links: list[str] = Field(default_factory=list, description="List of external links (not validated)")
    redirect_links: dict[str, str] = Field(default_factory=dict, description="Links that need redirects (old -> new)")


class ContentQualityMetrics(BaseModel):
    """Quality metrics for migrated content."""

    document_path: str = Field(..., description="Path to the document")

    # Content structure metrics
    has_front_matter: bool = Field(..., description="Document has YAML front matter")
    has_title: bool = Field(..., description="Document has a title")
    has_description: bool = Field(..., description="Document has a description")
    header_hierarchy_valid: bool = Field(..., description="Headers follow proper hierarchy")

    # Content quality metrics
    word_count: int = Field(ge=0, description="Total word count")
    code_block_count: int = Field(ge=0, description="Number of code blocks")
    link_count: int = Field(ge=0, description="Number of links")
    image_count: int = Field(ge=0, description="Number of images")

    # Readability metrics
    avg_sentence_length: float = Field(ge=0.0, description="Average sentence length")
    readability_score: float | None = Field(None, ge=0.0, le=100.0, description="Flesch reading ease score")

    # Issues and warnings
    has_todos: bool = Field(default=False, description="Contains TODO/FIXME markers")
    has_placeholders: bool = Field(default=False, description="Contains placeholder content")
    has_broken_links: bool = Field(default=False, description="Contains broken internal links")

    # Overall quality score (0-100)
    quality_score: float = Field(ge=0.0, le=100.0, description="Overall content quality score")


class MigrationProgress(BaseModel):
    """Real-time migration progress tracking."""

    migration_id: str = Field(..., description="Unique identifier for this migration")
    start_time: datetime = Field(..., description="Migration start time")
    current_time: datetime = Field(..., description="Current timestamp")

    # Progress metrics
    total_files: int = Field(ge=0, description="Total files to process")
    processed_files: int = Field(ge=0, description="Files processed so far")
    successful_files: int = Field(ge=0, description="Successfully processed files")
    failed_files: int = Field(ge=0, description="Failed file processing")

    # Current processing
    current_file: str | None = Field(None, description="Currently processing file")
    current_stage: str = Field(..., description="Current processing stage")

    # Estimated completion
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    progress_percentage: float = Field(ge=0.0, le=100.0, description="Completion percentage")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
