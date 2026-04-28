"""
A+ Discovery Data Accessor for Report Integration.

This module provides access to A+ discovery results for integration into
financial reports. It handles checking for discovery results, loading them,
and providing human-readable summaries.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, cast


class APlusDiscoveryAccessor:
    """
    Accessor for A+ discovery results.

    This class provides methods to check for, load, and summarize A+ discovery
    results from the discovery crew outputs. It handles cases where discovery
    hasn't run and provides clear messaging.
    """

    def __init__(self, output_dir: Path = Path("output")) -> None:
        """
        Initialize the A+ discovery accessor.

        Args:
            output_dir: Base output directory containing crew outputs

        """
        self.output_dir = output_dir
        self.discovery_dir = output_dir / "discovery"
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            "APlusDiscoveryAccessor initialized",
            extra={"output_dir": str(output_dir), "discovery_dir": str(self.discovery_dir)},
        )

    def has_discovery_results(self) -> bool:
        """
        Check if discovery results exist.

        Returns:
            True if discovery results are available, False otherwise

        """
        try:
            # Check if discovery directory exists
            if not self.discovery_dir.exists():
                self.logger.info("Discovery directory does not exist")
                return False

            # Check for at least one A+ discovery file
            stock_file = self.discovery_dir / "a_plus_stocks.json"
            etf_file = self.discovery_dir / "a_plus_etfs.json"
            crypto_file = self.discovery_dir / "a_plus_crypto.json"

            has_results = stock_file.exists() or etf_file.exists() or crypto_file.exists()

            self.logger.info(
                "Discovery results check completed",
                extra={
                    "has_results": has_results,
                    "stock_exists": stock_file.exists(),
                    "etf_exists": etf_file.exists(),
                    "crypto_exists": crypto_file.exists(),
                },
            )

            return has_results

        except Exception as e:
            self.logger.error(f"Error checking for discovery results: {e!s}", exc_info=True)
            return False

    def load_discovery_results(self) -> dict | None:
        """
        Load discovery results from JSON files.

        Returns:
            Dictionary containing discovery results, or None if not available

        """
        try:
            if not self.has_discovery_results():
                self.logger.warning("No discovery results available to load")
                return None

            results: dict[str, Any] = {
                "stocks": self._load_stock_results(),
                "etfs": self._load_etf_results(),
                "crypto": self._load_crypto_results(),
                "loaded_at": datetime.now().isoformat(),
            }

            # Count total opportunities
            stocks_data = cast(dict[str, Any], results["stocks"])
            etfs_data = cast(dict[str, Any], results["etfs"])
            crypto_data = cast(dict[str, Any], results["crypto"])
            total_opportunities = len(stocks_data.get("opportunities", [])) + len(etfs_data.get("opportunities", [])) + len(crypto_data.get("opportunities", []))

            results["total_opportunities"] = total_opportunities

            self.logger.info(
                "Discovery results loaded successfully",
                extra={
                    "stock_count": len(stocks_data.get("opportunities", [])),
                    "etf_count": len(etfs_data.get("opportunities", [])),
                    "crypto_count": len(crypto_data.get("opportunities", [])),
                    "total_opportunities": total_opportunities,
                },
            )

            return results

        except Exception as e:
            self.logger.error(f"Failed to load discovery results: {e!s}", exc_info=True)
            return None

    def get_opportunities_summary(self) -> str:
        """
        Get human-readable summary of A+ opportunities.

        Returns:
            Human-readable summary string

        """
        try:
            results = self.load_discovery_results()

            if results is None:
                return "A+ discovery produced no output for this run"

            total_opportunities = results.get("total_opportunities", 0)

            if total_opportunities == 0:
                return "No A+ opportunities found in current analysis"

            # Build detailed summary
            summary_parts = []

            # Stock opportunities
            stock_candidates = results["stocks"].get("opportunities", [])
            if stock_candidates:
                a_plus_stocks = [c for c in stock_candidates if c.get("grade") == "A+"]
                summary_parts.append(f"{len(stock_candidates)} stock opportunities ({len(a_plus_stocks)} A+ grade)")

            # ETF opportunities
            etf_candidates = results["etfs"].get("opportunities", [])
            if etf_candidates:
                a_plus_etfs = [c for c in etf_candidates if c.get("grade") == "A+"]
                summary_parts.append(f"{len(etf_candidates)} ETF opportunities ({len(a_plus_etfs)} A+ grade)")

            # Crypto opportunities
            crypto_candidates = results["crypto"].get("opportunities", [])
            if crypto_candidates:
                a_plus_crypto = [c for c in crypto_candidates if c.get("grade") == "A+"]
                summary_parts.append(f"{len(crypto_candidates)} crypto opportunities ({len(a_plus_crypto)} A+ grade)")

            summary = f"Discovery analysis identified {total_opportunities} high-quality investment opportunities: " + ", ".join(summary_parts)

            self.logger.info("Generated opportunities summary", extra={"total_opportunities": total_opportunities})

            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate opportunities summary: {e!s}", exc_info=True)
            return "Error generating opportunities summary"

    def _load_stock_results(self) -> dict[str, Any]:
        """Load stock discovery results."""
        stock_file = self.discovery_dir / "a_plus_stocks.json"

        if not stock_file.exists():
            self.logger.debug("Stock discovery file not found")
            return {}

        try:
            content = stock_file.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(content)
            self.logger.debug(f"Loaded {len(data.get('opportunities', []))} stock candidates")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load stock results: {e!s}", exc_info=True)
            return {}

    def _load_etf_results(self) -> dict[str, Any]:
        """Load ETF discovery results."""
        etf_file = self.discovery_dir / "a_plus_etfs.json"

        if not etf_file.exists():
            self.logger.debug("ETF discovery file not found")
            return {}

        try:
            content = etf_file.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(content)
            self.logger.debug(f"Loaded {len(data.get('opportunities', []))} ETF candidates")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load ETF results: {e!s}", exc_info=True)
            return {}

    def _load_crypto_results(self) -> dict[str, Any]:
        """Load crypto discovery results."""
        crypto_file = self.discovery_dir / "a_plus_crypto.json"

        if not crypto_file.exists():
            self.logger.debug("Crypto discovery file not found")
            return {}

        try:
            content = crypto_file.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(content)
            self.logger.debug(f"Loaded {len(data.get('opportunities', []))} crypto candidates")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load crypto results: {e!s}", exc_info=True)
            return {}
