"""
Models for registry management.

Pydantic models for crew execution results, configuration, and data collections.
"""

from typing import Any

from pydantic import BaseModel, Field


class ExecutionResult(BaseModel):
    """Result of crew execution coordination."""

    success: bool
    executed_crews: list[str] = Field(default_factory=list)
    failed_crews: list[str] = Field(default_factory=list)
    execution_time: float
    errors: list[str] = Field(default_factory=list)


class CrewConfig(BaseModel):
    """Configuration for crew execution."""

    name: str
    dependencies: list[str] = Field(default_factory=list)
    output_schema: str | None = None
    max_age_hours: int = 24


class UpstreamDataCollection(BaseModel):
    """Collection of upstream data available to a crew."""

    available_data: dict[str, Any] = Field(default_factory=dict)
    missing_data: list[str] = Field(default_factory=list)
    stale_data: list[str] = Field(default_factory=list)
