"""
Extraction engine for A+ opportunity data.

This module orchestrates the extraction of A+ investment opportunities from
discovery crew outputs, coordinating data parsing and opportunity extraction.
"""

import json
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
            self.logger.error(f"Failed to extract A+ opportunities: {str(e)}", exc_info=True)
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

    def _extract_market_context(self) -> dict[str, Any] | None:
        """Extract market context from discovery_latest.json."""
        try:
            discovery_file = self.discovery_dir / "discovery_latest.json"
            if not discovery_file.exists():
                return None

            content = discovery_file.read_text(encoding="utf-8")
            # Fix Python-style numeric literals
            content = self.parser.clean_json_content(content)
            data = json.loads(content)

            # Extract market context if available
            market_context: dict[str, Any] = data.get("market_context", {})
            if market_context:
                self.logger.info("Market context extracted from discovery results")
                return market_context

            return None
        except Exception as e:
            self.logger.warning(f"Could not extract market context: {e}")
            return None

    def _extract_backtesting_metrics(self) -> dict[str, Any] | None:
        """Extract backtesting metrics from discovery_latest.json."""
        try:
            discovery_file = self.discovery_dir / "discovery_latest.json"
            if not discovery_file.exists():
                return None

            content = discovery_file.read_text(encoding="utf-8")
            # Fix Python-style numeric literals
            content = self.parser.clean_json_content(content)
            data = json.loads(content)

            # Extract validation results which contain backtesting data
            validation_results = data.get("validation_results", [])
            if validation_results:
                # Aggregate backtesting metrics
                metrics = {
                    "total_candidates_tested": len(validation_results),
                    "candidates_with_backtests": sum(1 for v in validation_results if v.get("backtest_results")),
                    "avg_sharpe_ratio": None,
                    "avg_annual_return": None,
                    "avg_max_drawdown": None,
                }

                # Calculate averages if backtest data exists
                sharpe_ratios = []
                annual_returns = []
                max_drawdowns = []

                for result in validation_results:
                    backtest = result.get("backtest_results", {})
                    if backtest:
                        if "sharpe_ratio" in backtest:
                            sharpe_ratios.append(backtest["sharpe_ratio"])
                        if "annual_return" in backtest:
                            annual_returns.append(backtest["annual_return"])
                        if "max_drawdown" in backtest:
                            max_drawdowns.append(backtest["max_drawdown"])

                if sharpe_ratios:
                    metrics["avg_sharpe_ratio"] = sum(sharpe_ratios) / len(sharpe_ratios)
                if annual_returns:
                    metrics["avg_annual_return"] = sum(annual_returns) / len(annual_returns)
                if max_drawdowns:
                    metrics["avg_max_drawdown"] = sum(max_drawdowns) / len(max_drawdowns)

                self.logger.info(f"Backtesting metrics extracted: {metrics['candidates_with_backtests']} candidates with backtests")
                return metrics

            return None
        except Exception as e:
            self.logger.warning(f"Could not extract backtesting metrics: {e}")
            return None
