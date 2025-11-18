"""
Pydantic models for Supabase database schemas.

Defines strict validation models for all database tables with proper
type hints, field validation, and timezone handling.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AnalysisRecord(BaseModel):
    """
    Database record for analysis results.

    Represents a stored analysis with complete metadata and results.
    """

    id: str = Field(..., description="Unique analysis identifier (UUID)")
    ticker: str = Field(..., description="Asset ticker symbol (uppercase)")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Composite score 0-1")
    grade: str = Field(..., pattern=r"^[A-F][+-]?$", description="Letter grade (A+ to F)")
    recommendation: str = Field(
        ...,
        pattern=r"^(BUY|HOLD|SELL)$",
        description="Investment recommendation",
    )
    export_json: dict[str, Any] = Field(..., description="Complete analysis export")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "ticker": "AAPL",
                "asset_class": "stock",
                "composite_score": 0.85,
                "grade": "A+",
                "recommendation": "BUY",
                "export_json": {"ticker": "AAPL", "analysis": "..."},
                "created_at": "2025-10-31T12:00:00Z",
                "updated_at": "2025-10-31T12:00:00Z",
            }
        },
    }

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        """Validate and normalize ticker symbol."""
        if not v or not v.strip():
            raise ValueError("Ticker cannot be empty")
        return v.upper().strip()

    @field_validator("asset_class")
    @classmethod
    def validate_asset_class(cls, v: str) -> str:
        """Validate asset class."""
        valid_classes = {"stock", "etf", "crypto"}
        normalized = v.lower().strip()
        if normalized not in valid_classes:
            raise ValueError(f"Asset class must be one of: {valid_classes}")
        return normalized


class PortfolioSnapshot(BaseModel):
    """
    Database record for portfolio snapshot.

    Captures point-in-time state of portfolio holdings and values.
    """

    id: str = Field(..., description="Unique snapshot identifier (UUID)")
    snapshot_date: datetime = Field(..., description="Snapshot timestamp (UTC)")
    total_value: float = Field(..., ge=0.0, description="Total portfolio value")
    holdings: dict[str, Any] = Field(..., description="Portfolio holdings data")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "snapshot_date": "2025-10-31T12:00:00Z",
                "total_value": 100000.0,
                "holdings": {
                    "AAPL": {"quantity": 100, "value": 15000.0, "grade": "A+"},
                    "GOOGL": {"quantity": 50, "value": 7500.0, "grade": "A"},
                },
                "created_at": "2025-10-31T12:00:00Z",
            }
        },
    }

    @field_validator("total_value")
    @classmethod
    def validate_total_value(cls, v: float) -> float:
        """Validate total value is non-negative."""
        if v < 0:
            raise ValueError("Total value cannot be negative")
        return v


class EmbeddingRecord(BaseModel):
    """
    Database record for vector embedding.

    Stores vector embeddings for semantic similarity search.
    """

    id: str = Field(..., description="Unique embedding identifier (UUID)")
    analysis_id: str = Field(..., description="Associated analysis ID (UUID)")
    embedding: list[float] = Field(
        ...,
        min_length=1536,
        max_length=1536,
        description="Vector embedding (1536 dimensions)",
    )
    text: str = Field(..., min_length=1, description="Source text for embedding")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")

    model_config = {
        "str_strip_whitespace": True,
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
                "embedding": [0.1, 0.2, 0.3],  # Truncated for example
                "text": "Apple Inc. shows strong fundamentals...",
                "created_at": "2025-10-31T12:00:00Z",
            }
        },
    }

    @field_validator("embedding")
    @classmethod
    def validate_embedding_dimensions(cls, v: list[float]) -> list[float]:
        """Validate embedding has exactly 1536 dimensions."""
        if len(v) != 1536:
            raise ValueError(f"Embedding must have exactly 1536 dimensions, got {len(v)}")
        return v

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text is not empty."""
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class SupabaseHealthStatus(BaseModel):
    """
    Supabase health status for monitoring.

    Tracks operational metrics including availability, success rates,
    response times, circuit breaker state, and operation counts.

    Attributes:
        is_available: Whether Supabase connectivity test passed
        success_rate: Operation success rate (0.0 to 1.0)
        avg_response_time: Average response time in milliseconds
        circuit_breaker_open: Whether circuit breaker is currently open
        timeout_count: Number of timeout failures
        total_operations: Total number of operations attempted
        successful_operations: Number of successful operations
        failed_operations: Number of failed operations
        last_check_timestamp: Timestamp of last health check
        configuration: Current configuration settings

    """

    is_available: bool = Field(..., description="Whether Supabase connectivity test passed")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Operation success rate (0.0 to 1.0)")
    avg_response_time: float = Field(..., ge=0.0, description="Average response time in milliseconds")
    circuit_breaker_open: bool = Field(..., description="Whether circuit breaker is currently open")
    timeout_count: int = Field(..., ge=0, description="Number of timeout failures")
    total_operations: int = Field(..., ge=0, description="Total number of operations attempted")
    successful_operations: int = Field(..., ge=0, description="Number of successful operations")
    failed_operations: int = Field(..., ge=0, description="Number of failed operations")
    last_check_timestamp: datetime = Field(..., description="Timestamp of last health check")
    configuration: dict[str, str | float | int] = Field(default_factory=dict, description="Current configuration settings")

    model_config = {"frozen": False}
