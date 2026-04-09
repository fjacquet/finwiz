"""
A+ Opportunity Data Extractor for Discovery Crew Integration.

This module extracts A+ investment opportunities from discovery crew outputs
and structures them for integration into the reporting system.
"""

import logging
from pathlib import Path

from finwiz.orchestrators.extraction.engine import ExtractionEngine
from finwiz.schemas.integration import APlusOpportunityCollection


class APlusDataExtractor:
    """
    Extracts and processes A+ opportunity data from discovery crew outputs.

    This class orchestrates the extraction of A+ opportunities using the
    ExtractionEngine and provides validation capabilities.
    """

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the A+ data extractor.

        Args:
            output_dir: Base output directory containing crew outputs

        """
        self.output_dir = output_dir
        self.discovery_dir = output_dir / "discovery"
        self.logger = logging.getLogger(__name__)
        self.engine = ExtractionEngine(output_dir)

        self.logger.info("APlusDataExtractor initialized", extra={"output_dir": str(output_dir), "discovery_dir": str(self.discovery_dir)})

    def extract_aplus_opportunities(self) -> APlusOpportunityCollection | None:
        """
        Extract A+ opportunities from all discovery crew files.

        Returns:
            APlusOpportunityCollection with extracted opportunities, or None if extraction fails

        """
        return self.engine.extract_aplus_opportunities()

    # Delegation methods for backward compatibility with tests
    def _extract_stock_opportunities(self) -> list[dict]:
        """Extract A+ stock opportunities (delegates to engine)."""
        return self.engine._extract_stock_opportunities()

    def _extract_etf_opportunities(self) -> list[dict]:
        """Extract A+ ETF opportunities (delegates to engine)."""
        return self.engine._extract_etf_opportunities()

    def _extract_crypto_opportunities(self) -> list[dict]:
        """Extract A+ crypto opportunities (delegates to engine)."""
        return self.engine._extract_crypto_opportunities()

    def _generate_discovery_summary(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> str:
        """Generate discovery summary (delegates to engine)."""
        return self.engine.utils.generate_discovery_summary(stocks, etfs, cryptos)

    def _calculate_confidence_score(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> float:
        """Calculate confidence score (delegates to engine)."""
        return self.engine.utils.calculate_confidence_score(stocks, etfs, cryptos)

    def _extract_allocation_recommendations(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> list[dict]:
        """Extract allocation recommendations (delegates to engine)."""
        return self.engine.utils.extract_allocation_recommendations(stocks, etfs, cryptos)

    def _extract_replacement_notes(self, stocks: list[dict], etfs: list[dict], cryptos: list[dict]) -> list[str]:
        """Extract replacement notes (delegates to engine)."""
        return self.engine.utils.extract_replacement_notes(stocks, etfs, cryptos)

    def _extract_moat_info(self, moat_analysis):
        """Extract moat info (delegates to parser)."""
        return self.engine.parser.extract_moat_info(moat_analysis)

    def _extract_diversification_info(self, diversification):
        """Extract diversification info (delegates to parser)."""
        return self.engine.parser.extract_diversification_info(diversification)

    def _extract_technology_info(self, technology):
        """Extract technology info (delegates to parser)."""
        return self.engine.parser.extract_technology_info(technology)

    def validate_aplus_opportunities(self, collection: APlusOpportunityCollection) -> tuple[bool, list[str]]:
        """
        Validate A+ opportunities collection for completeness and quality.

        Args:
            collection: The A+ opportunities collection to validate

        Returns:
            Tuple of (is_valid, list_of_validation_errors)

        """
        errors = []

        try:
            # Check if we have any opportunities
            total_opportunities = len(collection.etf_opportunities) + len(collection.stock_opportunities) + len(collection.crypto_opportunities)

            if total_opportunities == 0:
                errors.append("No A+ opportunities found in any asset class")

            # Check confidence score
            if collection.confidence_score < 0.5:
                errors.append(f"Low confidence score: {collection.confidence_score}")

            # Check discovery summary
            if len(collection.discovery_summary) < 50:
                errors.append("Discovery summary is too brief")

            # Check allocation recommendations
            if not collection.allocation_recommendations:
                errors.append("No allocation recommendations provided")

            # Check for duplicate symbols (extract symbols from APlusOpportunity objects)
            all_symbols = (
                [opp.symbol for opp in collection.stock_opportunities]
                + [opp.symbol for opp in collection.etf_opportunities]
                + [opp.symbol for opp in collection.crypto_opportunities]
            )

            if len(all_symbols) != len(set(all_symbols)):
                errors.append("Duplicate symbols found in opportunities")

            is_valid = len(errors) == 0

            self.logger.info(
                "A+ opportunities validation completed",
                extra={"is_valid": is_valid, "error_count": len(errors), "total_opportunities": total_opportunities},
            )

            return is_valid, errors

        except Exception as e:
            self.logger.error(f"A+ opportunities validation failed: {e!s}", exc_info=True)
            return False, [f"Validation error: {e!s}"]
