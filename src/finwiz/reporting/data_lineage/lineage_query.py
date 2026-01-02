"""
Lineage Query Utility for FinWiz.

Provides convenient methods to query and retrieve data lineage information
from analysis results. Enables tracing calculations from raw data to final
results for reproducibility and validation.
"""

import logging
from pathlib import Path
from typing import Any

from finwiz.schemas.data_lineage import CalculationStep, DataLineage, DataSource, Transformation

logger = logging.getLogger(__name__)


class LineageQuery:
    """
    Query interface for data lineage.

    Provides methods to retrieve complete lineage, specific metric lineage,
    score calculation chains, and grade assignment chains.
    """

    def __init__(self, lineage_storage_path: Path | None = None):
        """
        Initialize lineage query interface.

        Args:
            lineage_storage_path: Optional path to lineage storage directory.
                                 If provided, can load lineage from disk.

        """
        self.lineage_storage_path = lineage_storage_path
        self._lineage_cache: dict[str, DataLineage] = {}

    def get_ticker_lineage(self, ticker: str, lineage: DataLineage | None = None) -> DataLineage | None:
        """
        Get complete lineage for a ticker.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load from storage.

        Returns:
            Complete DataLineage object if found, None otherwise

        """
        if lineage is not None:
            return lineage

        # Check cache
        if ticker in self._lineage_cache:
            logger.debug(f"Retrieved lineage for {ticker} from cache")
            return self._lineage_cache[ticker]

        # Try to load from storage
        if self.lineage_storage_path:
            lineage_file = self.lineage_storage_path / f"{ticker}_lineage.json"
            if lineage_file.exists():
                try:
                    with open(lineage_file) as f:
                        lineage_data = DataLineage.model_validate_json(f.read())
                        self._lineage_cache[ticker] = lineage_data
                        logger.debug(f"Loaded lineage for {ticker} from {lineage_file}")
                        return lineage_data
                except Exception as e:
                    logger.error(f"Failed to load lineage for {ticker}: {e}")
                    return None

        logger.warning(f"No lineage found for {ticker}")
        return None

    def get_metric_lineage(self, ticker: str, metric: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
        """
        Get lineage chain for a specific metric.

        Traces the metric from data source through transformations and
        calculations to final value.

        Args:
            ticker: Ticker symbol
            metric: Metric name (e.g., 'volatility', 'max_drawdown', 'beta')
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            Dictionary containing:
                - source: DataSource where metric originated
                - transformations: List of transformations applied
                - calculations: List of calculations using this metric
                - final_value: Final value of metric (if available)

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return None

        # Get lineage chain
        chain = lineage_obj.get_lineage_chain(metric)
        if not chain:
            logger.warning(f"No lineage chain found for {ticker} metric '{metric}'")
            return None

        # Organize chain by type
        result: dict[str, Any] = {
            "ticker": ticker,
            "metric": metric,
            "source": None,
            "transformations": [],
            "calculations": [],
            "final_value": lineage_obj.final_values.get(metric),
        }

        for item in chain:
            if isinstance(item, DataSource):
                result["source"] = item
            elif isinstance(item, Transformation):
                result["transformations"].append(item)
            elif isinstance(item, CalculationStep):
                result["calculations"].append(item)

        logger.debug(f"Retrieved lineage for {ticker} metric '{metric}': {len(result['transformations'])} transformations, {len(result['calculations'])} calculations")

        return result

    def get_score_lineage(self, ticker: str, score_type: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
        """
        Get calculation chain for a specific score.

        Traces how a score was calculated from input metrics.

        Args:
            ticker: Ticker symbol
            score_type: Score type (e.g., 'composite_score', 'risk_score', 'fundamental_score')
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            Dictionary containing:
                - calculation: CalculationStep for the score
                - inputs: Dictionary of input values used
                - formula: Mathematical formula used
                - output: Final score value
                - input_lineages: Lineage chains for each input metric

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return None

        # Find calculation step for this score
        calc_step = lineage_obj.get_calculation_by_name(score_type)
        if not calc_step:
            logger.warning(f"No calculation found for {ticker} score '{score_type}'")
            return None

        # Build result
        result: dict[str, Any] = {
            "ticker": ticker,
            "score_type": score_type,
            "calculation": calc_step,
            "inputs": calc_step.inputs,
            "formula": calc_step.formula,
            "output": calc_step.output,
            "metadata": calc_step.metadata,
            "input_lineages": {},
        }

        # Get lineage for each input metric
        for input_name in calc_step.inputs.keys():
            input_lineage = self.get_metric_lineage(ticker, input_name, lineage_obj)
            if input_lineage:
                result["input_lineages"][input_name] = input_lineage

        logger.debug(f"Retrieved score lineage for {ticker} '{score_type}': {len(result['inputs'])} inputs, formula: {calc_step.formula}")

        return result

    def get_grade_lineage(self, ticker: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
        """
        Get grade assignment chain.

        Traces how the grade was assigned from composite score.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            Dictionary containing:
                - calculation: CalculationStep for grade assignment
                - composite_score: Input composite score
                - grade: Assigned grade
                - grading_scale: Grading scale used (from metadata)
                - score_lineage: Complete lineage for composite_score

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return None

        # Find grade calculation step
        grade_calc = lineage_obj.get_calculation_by_name("grade")
        if not grade_calc:
            logger.warning(f"No grade calculation found for {ticker}")
            return None

        # Get composite score lineage
        score_lineage = self.get_score_lineage(ticker, "composite_score", lineage_obj)

        # Build result
        result: dict[str, Any] = {
            "ticker": ticker,
            "calculation": grade_calc,
            "composite_score": grade_calc.inputs.get("composite_score"),
            "grade": grade_calc.output,
            "grading_scale": grade_calc.metadata.get("grading_scale"),
            "score_lineage": score_lineage,
        }

        logger.debug(f"Retrieved grade lineage for {ticker}: score={result['composite_score']}, grade={result['grade']}")

        return result

    def get_all_sources(self, ticker: str, lineage: DataLineage | None = None) -> list[DataSource]:
        """
        Get all data sources used in analysis.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            List of all DataSource objects

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return []

        return lineage_obj.sources

    def get_all_calculations(self, ticker: str, lineage: DataLineage | None = None) -> list[CalculationStep]:
        """
        Get all calculation steps performed in analysis.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            List of all CalculationStep objects

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return []

        return lineage_obj.calculations

    def get_sources_by_type(self, ticker: str, source_type: str, lineage: DataLineage | None = None) -> list[DataSource]:
        """
        Get all data sources of a specific type.

        Args:
            ticker: Ticker symbol
            source_type: Source type (e.g., 'api', 'cache', 'default')
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            List of DataSource objects matching the type

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return []

        return [source for source in lineage_obj.sources if source.source_type == source_type]

    def get_defaulted_fields(self, ticker: str, lineage: DataLineage | None = None) -> list[str]:
        """
        Get list of fields that used default values.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            List of field names that used defaults

        """
        default_sources = self.get_sources_by_type(ticker, "default", lineage)
        return [source.field_name for source in default_sources]

    def get_lineage_summary(self, ticker: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
        """
        Get summary of lineage for a ticker.

        Args:
            ticker: Ticker symbol
            lineage: Optional lineage object. If not provided, attempts to load.

        Returns:
            Dictionary containing summary statistics:
                - ticker: Ticker symbol
                - asset_class: Asset class
                - analysis_timestamp: When analysis was performed
                - total_sources: Number of data sources
                - sources_by_type: Count of sources by type
                - total_transformations: Number of transformations
                - total_calculations: Number of calculations
                - defaulted_fields: List of fields using defaults
                - completeness: Lineage completeness score
                - final_values: Final calculated values

        """
        lineage_obj = self.get_ticker_lineage(ticker, lineage)
        if not lineage_obj:
            return None

        # Count sources by type
        sources_by_type: dict[str, int] = {}
        for source in lineage_obj.sources:
            sources_by_type[source.source_type] = sources_by_type.get(source.source_type, 0) + 1

        return {
            "ticker": ticker,
            "asset_class": lineage_obj.asset_class,
            "analysis_timestamp": lineage_obj.analysis_timestamp,
            "total_sources": len(lineage_obj.sources),
            "sources_by_type": sources_by_type,
            "total_transformations": len(lineage_obj.transformations),
            "total_calculations": len(lineage_obj.calculations),
            "defaulted_fields": self.get_defaulted_fields(ticker, lineage_obj),
            "completeness": lineage_obj.completeness,
            "final_values": lineage_obj.final_values,
            "scorer_version": lineage_obj.scorer_version,
            "formula_version": lineage_obj.formula_version,
        }


# Convenience functions for direct usage
def get_ticker_lineage(ticker: str, lineage: DataLineage | None = None) -> DataLineage | None:
    """Get complete lineage for a ticker."""
    query = LineageQuery()
    return query.get_ticker_lineage(ticker, lineage)


def get_metric_lineage(ticker: str, metric: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
    """Get lineage chain for a specific metric."""
    query = LineageQuery()
    return query.get_metric_lineage(ticker, metric, lineage)


def get_score_lineage(ticker: str, score_type: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
    """Get calculation chain for a specific score."""
    query = LineageQuery()
    return query.get_score_lineage(ticker, score_type, lineage)


def get_grade_lineage(ticker: str, lineage: DataLineage | None = None) -> dict[str, Any] | None:
    """Get grade assignment chain."""
    query = LineageQuery()
    return query.get_grade_lineage(ticker, lineage)
