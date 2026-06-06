"""Schema registry for centralized model management."""

from __future__ import annotations

import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SchemaRegistry:
    """
    Centralized registry for Pydantic models used in validation.

    Provides a single point of control for all validation schemas
    and enables dynamic schema lookup by name or crew type.
    """

    def __init__(self) -> None:
        """Initialize the schema registry."""
        self._schemas: dict[str, type[BaseModel]] = {}
        self._crew_schemas: dict[str, dict[str, type[BaseModel]]] = {}
        self._initialize_default_schemas()

    def register_schema(self, name: str, schema_class: type[BaseModel]) -> None:
        """
        Register a Pydantic model schema.

        Args:
            name: Unique name for the schema
            schema_class: Pydantic model class

        """
        if not issubclass(schema_class, BaseModel):
            raise ValueError(f"Schema {name} must be a Pydantic BaseModel subclass")

        self._schemas[name] = schema_class
        logger.debug(f"Registered schema: {name}")

    def register_crew_schema(self, crew_type: str, output_type: str, schema_class: type[BaseModel]) -> None:
        """
        Register a schema for a specific crew output type.

        Args:
            crew_type: Type of crew (e.g., 'stock', 'etf', 'crypto', 'report')
            output_type: Type of output (e.g., 'analysis', 'sentiment', 'risk')
            schema_class: Pydantic model class

        """
        if crew_type not in self._crew_schemas:
            self._crew_schemas[crew_type] = {}

        self._crew_schemas[crew_type][output_type] = schema_class
        logger.debug(f"Registered crew schema: {crew_type}.{output_type}")

    def get_schema(self, name: str) -> type[BaseModel] | None:
        """
        Get a schema by name.

        Args:
            name: Schema name

        Returns:
            Pydantic model class or None if not found

        """
        return self._schemas.get(name)

    def get_crew_schema(self, crew_type: str, output_type: str) -> type[BaseModel] | None:
        """
        Get a schema for a specific crew output type.

        Args:
            crew_type: Type of crew
            output_type: Type of output

        Returns:
            Pydantic model class or None if not found

        """
        crew_schemas = self._crew_schemas.get(crew_type, {})
        return crew_schemas.get(output_type)

    def _initialize_default_schemas(self) -> None:
        """Initialize default schemas from existing finwiz models."""
        try:
            # Import existing schemas
            from finwiz.schemas.common import RiskAssessmentStandardized
            from finwiz.schemas.crypto import CryptoThesis
            from finwiz.schemas.etf import ETFFactsheet, ETFTopHolding
            from finwiz.schemas.report import ReporterInput
            from finwiz.schemas.stock import MarketSentiment, TenKInsight
            from finwiz.schemas.validation import ValidatedTicker

            # Register core schemas
            self.register_schema("ReporterInput", ReporterInput)
            self.register_schema("ValidatedTicker", ValidatedTicker)
            self.register_schema("RiskAssessmentStandardized", RiskAssessmentStandardized)

            # Register individual schemas by name
            self.register_schema("TenKInsight", TenKInsight)
            self.register_schema("MarketSentiment", MarketSentiment)
            self.register_schema("ETFFactsheet", ETFFactsheet)
            self.register_schema("ETFTopHolding", ETFTopHolding)
            self.register_schema("CryptoThesis", CryptoThesis)

            # Register crew-specific schemas
            self.register_crew_schema("stock", "ten_k_insight", TenKInsight)
            self.register_crew_schema("stock", "market_sentiment", MarketSentiment)
            self.register_crew_schema("stock", "risk_assessment", RiskAssessmentStandardized)

            self.register_crew_schema("etf", "factsheet", ETFFactsheet)
            self.register_crew_schema("etf", "top_holding", ETFTopHolding)
            self.register_crew_schema("etf", "risk_assessment", RiskAssessmentStandardized)

            self.register_crew_schema("crypto", "thesis", CryptoThesis)
            self.register_crew_schema("crypto", "risk_assessment", RiskAssessmentStandardized)

            self.register_crew_schema("report", "input", ReporterInput)

            logger.info("Initialized default schemas")

        except ImportError as e:
            logger.warning(f"Could not import some default schemas: {e}")


# Global registry instance
_registry = SchemaRegistry()


def get_registry() -> SchemaRegistry:
    """Get the global schema registry instance."""
    return _registry
