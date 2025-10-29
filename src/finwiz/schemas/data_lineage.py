"""
Data Lineage Schema for FinWiz.

Tracks the complete audit trail of calculations from raw data sources
through transformations and calculations to final results. Enables
reproducibility, validation, and debugging of all analysis results.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DataSource(BaseModel):
    """
    Record of a data source used in analysis.

    Tracks where data came from, when it was retrieved, and the raw value.
    """

    source_id: str = Field(..., description="Unique identifier for this data source")
    source_type: Literal["api", "cache", "calculation", "user_input", "default"] = Field(..., description="Type of data source")
    source_name: str = Field(..., description="Name of the source (e.g., 'Yahoo Finance API', 'QuantitativeTool')")
    timestamp: str = Field(..., description="When data was retrieved (ISO format)")
    raw_value: Any = Field(..., description="Raw value from source (before any transformations)")
    field_name: str = Field(..., description="Name of the field this source provides (e.g., 'volatility', 'price')")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata (API version, cache key, etc.)")

    model_config = {"extra": "forbid"}


class Transformation(BaseModel):
    """
    Record of a data transformation applied during analysis.

    Tracks operations that convert or normalize data (e.g., type conversion,
    unit conversion, normalization).
    """

    transformation_id: str = Field(..., description="Unique identifier for this transformation")
    operation: str = Field(..., description="Type of operation (e.g., 'type_conversion', 'normalization', 'scaling')")
    input_values: dict[str, Any] = Field(..., description="Input values before transformation")
    output_value: Any = Field(..., description="Output value after transformation")
    formula: str | None = Field(None, description="Formula or description of transformation")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When transformation occurred")

    model_config = {"extra": "forbid"}


class CalculationStep(BaseModel):
    """
    Record of a calculation step in the analysis pipeline.

    Tracks how component scores and final results are calculated from
    input metrics.
    """

    step_id: str = Field(..., description="Unique identifier for this calculation step")
    step_name: str = Field(..., description="Name of calculation (e.g., 'risk_score', 'composite_score', 'grade')")
    inputs: dict[str, Any] = Field(..., description="Input values used in calculation")
    calculation: str = Field(..., description="Description of calculation performed")
    formula: str | None = Field(None, description="Mathematical formula (e.g., '0.4*F + 0.3*T + 0.3*R')")
    output: Any = Field(..., description="Output value from calculation")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When calculation occurred")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata (weights, thresholds, etc.)")

    model_config = {"extra": "forbid"}


class DataLineage(BaseModel):
    """
    Complete data lineage for an analysis result.

    Provides full audit trail from data sources through transformations
    and calculations to final results. Enables reproducibility and validation.
    """

    ticker: str = Field(..., description="Asset ticker symbol")
    asset_class: str = Field(..., description="Asset class (stock, etf, crypto)")
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When analysis was performed")

    # Data sources
    sources: list[DataSource] = Field(default_factory=list, description="All data sources used in analysis")

    # Transformations
    transformations: list[Transformation] = Field(default_factory=list, description="All data transformations applied")

    # Calculations
    calculations: list[CalculationStep] = Field(default_factory=list, description="All calculation steps performed")

    # Final values
    final_values: dict[str, Any] = Field(default_factory=dict, description="Final calculated values (composite_score, grade, etc.)")

    # Metadata
    scorer_version: str | None = Field(None, description="Version of scoring engine used")
    formula_version: str | None = Field(None, description="Version of calculation formulas used")
    completeness: float = Field(default=1.0, ge=0.0, le=1.0, description="Completeness of lineage (1.0 = complete, <1.0 = partial)")

    model_config = {"extra": "forbid"}

    def add_source(
        self,
        source_id: str,
        source_type: Literal["api", "cache", "calculation", "user_input", "default"],
        source_name: str,
        field_name: str,
        raw_value: Any,
        timestamp: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a data source to the lineage.

        Args:
            source_id: Unique identifier for this source
            source_type: Type of data source
            source_name: Name of the source
            field_name: Field name this source provides
            raw_value: Raw value from source
            timestamp: When data was retrieved (defaults to now)
            metadata: Additional metadata

        """
        self.sources.append(
            DataSource(
                source_id=source_id,
                source_type=source_type,
                source_name=source_name,
                field_name=field_name,
                raw_value=raw_value,
                timestamp=timestamp or datetime.now().isoformat(),
                metadata=metadata or {},
            )
        )

    def add_transformation(
        self,
        transformation_id: str,
        operation: str,
        input_values: dict[str, Any],
        output_value: Any,
        formula: str | None = None,
    ) -> None:
        """
        Add a transformation to the lineage.

        Args:
            transformation_id: Unique identifier for this transformation
            operation: Type of operation
            input_values: Input values before transformation
            output_value: Output value after transformation
            formula: Formula or description of transformation

        """
        self.transformations.append(
            Transformation(
                transformation_id=transformation_id,
                operation=operation,
                input_values=input_values,
                output_value=output_value,
                formula=formula,
            )
        )

    def add_calculation(
        self,
        step_id: str,
        step_name: str,
        inputs: dict[str, Any],
        calculation: str,
        output: Any,
        formula: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a calculation step to the lineage.

        Args:
            step_id: Unique identifier for this step
            step_name: Name of calculation
            inputs: Input values used
            calculation: Description of calculation
            output: Output value
            formula: Mathematical formula
            metadata: Additional metadata

        """
        self.calculations.append(
            CalculationStep(
                step_id=step_id,
                step_name=step_name,
                inputs=inputs,
                calculation=calculation,
                formula=formula,
                output=output,
                metadata=metadata or {},
            )
        )

    def get_source_by_field(self, field_name: str) -> DataSource | None:
        """
        Get data source for a specific field.

        Args:
            field_name: Name of field to find source for

        Returns:
            DataSource if found, None otherwise

        """
        for source in self.sources:
            if source.field_name == field_name:
                return source
        return None

    def get_calculation_by_name(self, step_name: str) -> CalculationStep | None:
        """
        Get calculation step by name.

        Args:
            step_name: Name of calculation step

        Returns:
            CalculationStep if found, None otherwise

        """
        for calc in self.calculations:
            if calc.step_name == step_name:
                return calc
        return None

    def get_lineage_chain(self, field_name: str) -> list[DataSource | Transformation | CalculationStep]:
        """
        Get complete lineage chain for a specific field.

        Traces from data source through transformations and calculations
        to final value.

        Args:
            field_name: Name of field to trace

        Returns:
            List of lineage steps in order (source → transformations → calculations)

        """
        chain: list[DataSource | Transformation | CalculationStep] = []

        # Find source
        source = self.get_source_by_field(field_name)
        if source:
            chain.append(source)

        # Find transformations that use this field
        for transform in self.transformations:
            if field_name in transform.input_values:
                chain.append(transform)

        # Find calculations that use this field
        for calc in self.calculations:
            if field_name in calc.inputs:
                chain.append(calc)

        return chain
