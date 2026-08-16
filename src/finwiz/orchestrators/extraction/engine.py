"""
Extraction engine for A+ opportunity data.

This module orchestrates the extraction of A+ investment opportunities from
discovery crew outputs, coordinating data parsing and opportunity extraction.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.orchestrators.extraction.parsers import DataParser
from finwiz.orchestrators.extraction.utils import ExtractionUtils
from finwiz.schemas.integration import APlusOpportunityCollection


class ExtractionEngine:
    """
    Orchestrates extraction of A+ opportunity data from discovery crew outputs.

    This class coordinates the extraction process, using DataParser for JSON
    parsing and delegating to opportunity extractors for asset-specific logic.
    """

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the extraction engine.

        Args:
            output_dir: Base output directory containing crew outputs

        """
        self.output_dir = output_dir
        self.discovery_dir = output_dir / "discovery"
        self.logger = logging.getLogger(__name__)
        self.parser = DataParser()
        self.utils = ExtractionUtils()

        self.logger.info("ExtractionEngine initialized", extra={"output_dir": str(output_dir), "discovery_dir": str(self.discovery_dir)})

    def extract_aplus_opportunities(self) -> APlusOpportunityCollection | None:
        """
        Extract A+ opportunities from all discovery crew files.

        Returns:
            APlusOpportunityCollection with extracted opportunities, or None if extraction fails

        """
        try:
            # Check if discovery directory exists
            if not self.discovery_dir.exists():
                self.logger.warning(f"Discovery directory not found: {self.discovery_dir}")
                return None

            # Extract opportunities from each asset class
            stock_opportunities = self._extract_stock_opportunities()
            etf_opportunities = self._extract_etf_opportunities()
            crypto_opportunities = self._extract_crypto_opportunities()

            # Generate discovery summary
            discovery_summary = self.utils.generate_discovery_summary(stock_opportunities, etf_opportunities, crypto_opportunities)

            # Calculate confidence score based on data availability
            confidence_score = self.utils.calculate_confidence_score(stock_opportunities, etf_opportunities, crypto_opportunities)

            # Extract allocation recommendations and replacement notes
            allocation_recommendations = self.utils.extract_allocation_recommendations(stock_opportunities, etf_opportunities, crypto_opportunities)
            replacement_notes = self.utils.extract_replacement_notes(stock_opportunities, etf_opportunities, crypto_opportunities)

            # Convert dict opportunities to APlusOpportunity objects
            from finwiz.schemas.integration_models import APlusOpportunity

            etf_opps = [APlusOpportunity(**opp) for opp in etf_opportunities]
            stock_opps = [APlusOpportunity(**opp) for opp in stock_opportunities]
            crypto_opps = [APlusOpportunity(**opp) for opp in crypto_opportunities]

            # Extract market context and backtesting metrics
            market_context = self._extract_market_context()
            backtesting_metrics = self._extract_backtesting_metrics()

            collection = APlusOpportunityCollection(
                etf_opportunities=etf_opps,
                stock_opportunities=stock_opps,
                crypto_opportunities=crypto_opps,
                discovery_summary=discovery_summary,
                confidence_score=confidence_score,
                validation_timestamp=datetime.now(),
                allocation_recommendations=allocation_recommendations,
                replacement_notes=replacement_notes,
                market_context=market_context,
                backtesting_metrics=backtesting_metrics,
            )

            self.logger.info(
                "A+ opportunities extracted successfully",
                extra={
                    "stock_count": len(stock_opportunities),
                    "etf_count": len(etf_opportunities),
                    "crypto_count": len(crypto_opportunities),
                    "confidence_score": confidence_score,
                },
            )

            return collection

        except Exception as e:
            self.logger.error(f"Failed to extract A+ opportunities: {e!s}", exc_info=True)
            return None

    def _extract_stock_opportunities(self) -> list[dict[str, Any]]:
        """Extract A+ stock opportunities from a_plus_stocks.json file."""
        from finwiz.orchestrators.discovery.extractors import StockOpportunityExtractor

        stock_file = self.discovery_dir / "a_plus_stocks.json"

        # Load and parse JSON using parser
        candidates = self.parser.load_and_parse_json(stock_file, "stock")
        if not candidates:
            return []

        # Use stock extractor with Template Method pattern
        extractor = StockOpportunityExtractor()
        opportunities = extractor.extract(candidates)

        self.logger.info(f"Extracted {len(opportunities)} stock A+ opportunities")
        return opportunities

    def _extract_etf_opportunities(self) -> list[dict[str, Any]]:
        """Extract A+ ETF opportunities from a_plus_etfs.json file."""
        from finwiz.orchestrators.discovery.extractors import ETFOpportunityExtractor

        etf_file = self.discovery_dir / "a_plus_etfs.json"

        # Load and parse JSON using parser
        candidates = self.parser.load_and_parse_json(etf_file, "etf")
        if not candidates:
            return []

        # Use ETF extractor with Template Method pattern
        extractor = ETFOpportunityExtractor()
        opportunities = extractor.extract(candidates)

        self.logger.info(f"Extracted {len(opportunities)} ETF A+ opportunities")
        return opportunities

    def _extract_crypto_opportunities(self) -> list[dict[str, Any]]:
        """Extract A+ crypto opportunities from a_plus_crypto.json file."""
        from finwiz.orchestrators.discovery.extractors import CryptoOpportunityExtractor

        crypto_file = self.discovery_dir / "a_plus_crypto.json"

        # Load and parse JSON using parser
        candidates = self.parser.load_and_parse_json(crypto_file, "crypto")
        if not candidates:
            return []

        # Use crypto extractor with Template Method pattern
        extractor = CryptoOpportunityExtractor()
        opportunities = extractor.extract(candidates)

        self.logger.info(f"Extracted {len(opportunities)} crypto A+ opportunities")
        return opportunities

    # `market_context` and `validation_results` were written against the raw
    # CrewAI discovery-crew kickoff shape (a `{"pydantic": {...}}` result). The
    # pipeline actually wired into DiscoveryOrchestrator today is the
    # deterministic NewcomerDiscoveryPipeline, whose only output file
    # (consolidated_discovery.json) never carries either key — there is no
    # file anywhere in this pipeline that has this data (task-11, Ruling 23).
    # Returning None here would be indistinguishable from the "ran and found
    # nothing" meaning None already carries elsewhere in this module, so an
    # explicit, named marker is returned instead: callers can tell "this input
    # does not exist in this pipeline" apart from "this input was empty".
    _NO_PRODUCER_REASON = "no producer emits this field in the current discovery pipeline"

    def _unavailable(self, field_name: str) -> dict[str, Any]:
        """Build the 'no producer for this field' marker and log why."""
        self.logger.info(f"{field_name} extraction skipped: {self._NO_PRODUCER_REASON}.")
        return {"unavailable": True, "field": field_name, "reason": self._NO_PRODUCER_REASON}

    def _extract_market_context(self) -> dict[str, Any] | None:
        """market_context has no producer in the current discovery pipeline."""
        return self._unavailable("market_context")

    def _extract_backtesting_metrics(self) -> dict[str, Any] | None:
        """backtesting_metrics (validation_results) has no producer in the current discovery pipeline."""
        return self._unavailable("backtesting_metrics")
