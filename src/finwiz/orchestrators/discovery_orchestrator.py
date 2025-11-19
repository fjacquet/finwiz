"""
Discovery Orchestrator for FinWiz Flow.

This module executes discovery analysis for crypto, stocks, and ETFs:
- Crypto discovery crew execution
- Stock discovery crew execution
- ETF discovery crew execution
- Discovery result consolidation
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from finwiz.flow_state import FinwizState
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DiscoveryOrchestrator:
    """Executes discovery analysis for crypto, stocks, and ETFs."""

    def __init__(self, state: FinwizState, **dependencies: Any) -> None:
        """
        Initialize the DiscoveryOrchestrator.

        Args:
            state: FinwizState instance for accessing workflow state
            **dependencies: Additional dependencies including:
                - availability_tracker: For tracking data source availability

        """
        self.state = state
        self.logger = get_logger(self.__class__.__name__)
        self.availability_tracker = dependencies.get("availability_tracker")

    def check_crypto(self) -> dict[str, Any]:
        """
        Execute crypto discovery crew.

        Uses Python-based analysis to identify promising cryptocurrencies.
        Runs in parallel with check_stock and check_etf.

        Returns:
            dict: Discovery results with keys:
                - crypto_analysis_complete: bool
                - crypto_result: str (summary message)

        """
        self.logger.info("🚀 CRYPTO DISCOVERY: Using Python analysis")

        try:
            # Use Python-based crypto analysis
            from finwiz.scoring.crypto_analyzer import analyze_crypto_opportunities

            session_id = self.state.session_id or "default"
            crypto_results = analyze_crypto_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "crypto_analysis_success": True,
                "crypto_result": crypto_results.get("analysis_summary", "Crypto analysis completed"),
                "crypto_opportunities": crypto_results.get("opportunities", []),
                "crypto_performance_metrics": crypto_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Save results to disk
            self._save_discovery_results("crypto", crypto_results)

            # Track successful Python execution
            if self.availability_tracker:
                self.availability_tracker.track_data_source(
                    source="crypto_crew",
                    status="available",
                    last_updated=datetime.now().isoformat(),
                    record_count=len(crypto_results.get("opportunities", [])),
                )

            self.logger.info(f"✅ Crypto discovery completed: {len(crypto_results.get('opportunities', []))} opportunities found")

            return {"crypto_analysis_complete": True, "crypto_result": result_data.get("crypto_result", "")}

        except Exception as e:
            self.logger.error(f"Crypto Python analysis failed: {e}")

            # Fallback result
            result_data = {
                "crypto_analysis_success": False,
                "crypto_analysis_error": str(e),
                "crypto_result": f"Crypto analysis failed: {e}",
            }

            self._update_state_from_dict(result_data)

            if self.availability_tracker:
                self.availability_tracker.track_data_source(source="crypto_crew", status="unavailable", error_message=str(e))

            return {"crypto_analysis_complete": True, "crypto_result": result_data.get("crypto_result", "")}

    def check_stock(self) -> dict[str, Any]:
        """
        Execute stock discovery crew.

        Uses Python-based analysis to identify promising stocks.
        Runs in parallel with check_crypto and check_etf.

        Returns:
            dict: Discovery results with keys:
                - stock_analysis_complete: bool
                - stock_result: str (summary message)

        """
        self.logger.info("🚀 STOCK DISCOVERY: Using Python analysis")

        try:
            # Use Python-based stock analysis
            from finwiz.scoring.stock_analyzer import analyze_stock_opportunities

            session_id = self.state.session_id or "default"
            stock_results = analyze_stock_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "stock_analysis_success": True,
                "stock_result": stock_results.get("analysis_summary", "Stock analysis completed"),
                "stock_opportunities": stock_results.get("opportunities", []),
                "stock_performance_metrics": stock_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Save results to disk
            self._save_discovery_results("stock", stock_results)

            # Track successful Python execution
            if self.availability_tracker:
                self.availability_tracker.track_data_source(
                    source="stock_crew",
                    status="available",
                    last_updated=datetime.now().isoformat(),
                    record_count=len(stock_results.get("opportunities", [])),
                )

            self.logger.info(f"✅ Stock discovery completed: {len(stock_results.get('opportunities', []))} opportunities found")

            return {"stock_analysis_complete": True, "stock_result": result_data.get("stock_result", "")}

        except Exception as e:
            self.logger.error(f"Stock Python analysis failed: {e}")

            # Fallback result
            result_data = {
                "stock_analysis_success": False,
                "stock_analysis_error": str(e),
                "stock_result": f"Stock analysis failed: {e}",
            }

            self._update_state_from_dict(result_data)

            if self.availability_tracker:
                self.availability_tracker.track_data_source(source="stock_crew", status="unavailable", error_message=str(e))

            return {"stock_analysis_complete": True, "stock_result": result_data.get("stock_result", "")}

    def check_etf(self) -> dict[str, Any]:
        """
        Execute ETF discovery crew.

        Uses Python-based analysis to identify stable ETFs.
        Runs in parallel with check_crypto and check_stock.

        Returns:
            dict: Discovery results with keys:
                - etf_analysis_complete: bool
                - etf_result: str (summary message)

        """
        self.logger.info("🚀 ETF DISCOVERY: Using Python analysis")

        try:
            # Use Python-based ETF analysis
            from finwiz.scoring.etf_analyzer import analyze_etf_opportunities

            session_id = self.state.session_id or "default"
            etf_results = analyze_etf_opportunities(session_id)

            # Update state with Python results
            result_data = {
                "etf_analysis_success": True,
                "etf_result": etf_results.get("analysis_summary", "ETF analysis completed"),
                "etf_opportunities": etf_results.get("opportunities", []),
                "etf_performance_metrics": etf_results.get("performance_metrics", {}),
            }

            self._update_state_from_dict(result_data)

            # Save results to disk
            self._save_discovery_results("etf", etf_results)

            # Track successful Python execution
            if self.availability_tracker:
                self.availability_tracker.track_data_source(
                    source="etf_crew",
                    status="available",
                    last_updated=datetime.now().isoformat(),
                    record_count=len(etf_results.get("opportunities", [])),
                )

            self.logger.info(f"✅ ETF discovery completed: {len(etf_results.get('opportunities', []))} opportunities found")

            return {"etf_analysis_complete": True, "etf_result": result_data.get("etf_result", "")}

        except Exception as e:
            self.logger.error(f"ETF Python analysis failed: {e}")

            # Fallback result
            result_data = {"etf_analysis_success": False, "etf_analysis_error": str(e), "etf_result": f"ETF analysis failed: {e}"}

            self._update_state_from_dict(result_data)

            if self.availability_tracker:
                self.availability_tracker.track_data_source(source="etf_crew", status="unavailable", error_message=str(e))

            return {"etf_analysis_complete": True, "etf_result": result_data.get("etf_result", "")}

    def check_investment_discovery(self) -> dict[str, Any]:
        """
        Consolidate discovery results from all asset classes.

        Consolidates results from discovery crews (crypto, stock, ETF),
        finds A+ grade opportunities across all asset classes, and
        validates opportunities through backtesting.

        Returns:
            dict: Consolidated discovery results with keys:
                - investment_discovery_complete: bool
                - discovery_available: bool
                - validation_error: str (if validation failed)

        """
        self.logger.info("Consolidating discovery results from all asset classes")

        # Consolidate opportunities from all asset classes
        all_opportunities = []

        # Add crypto opportunities
        if hasattr(self.state, "crypto_opportunities") and self.state.crypto_opportunities:
            all_opportunities.extend(self.state.crypto_opportunities)
            self.logger.info(f"Added {len(self.state.crypto_opportunities)} crypto opportunities")

        # Add stock opportunities
        if hasattr(self.state, "stock_opportunities") and self.state.stock_opportunities:
            all_opportunities.extend(self.state.stock_opportunities)
            self.logger.info(f"Added {len(self.state.stock_opportunities)} stock opportunities")

        # Add ETF opportunities
        if hasattr(self.state, "etf_opportunities") and self.state.etf_opportunities:
            all_opportunities.extend(self.state.etf_opportunities)
            self.logger.info(f"Added {len(self.state.etf_opportunities)} ETF opportunities")

        # Update state with consolidated results
        self.state.investment_discovery_available = len(all_opportunities) > 0
        self.state.all_discovery_opportunities = all_opportunities

        # Save consolidated results to discovery directory
        consolidated_results = {
            "timestamp": datetime.now().isoformat(),
            "total_opportunities": len(all_opportunities),
            "opportunities": all_opportunities,
            "by_asset_class": {
                "crypto": len(self.state.crypto_opportunities) if hasattr(self.state, "crypto_opportunities") and self.state.crypto_opportunities else 0,
                "stock": len(self.state.stock_opportunities) if hasattr(self.state, "stock_opportunities") and self.state.stock_opportunities else 0,
                "etf": len(self.state.etf_opportunities) if hasattr(self.state, "etf_opportunities") and self.state.etf_opportunities else 0,
            },
        }
        self._save_discovery_results("discovery", consolidated_results)

        self.logger.info(f"✅ Discovery consolidation complete: {len(all_opportunities)} total opportunities")

        return {
            "investment_discovery_complete": True,
            "discovery_available": self.state.investment_discovery_available,
            "total_opportunities": len(all_opportunities),
        }

    def _update_state_from_dict(self, data: dict[str, Any]) -> None:
        """
        Update state attributes from dictionary.

        Args:
            data: Dictionary of state attributes to update

        """
        for key, value in data.items():
            setattr(self.state, key, value)

    def _save_discovery_results(self, asset_class: str, results: dict[str, Any]) -> None:
        """
        Save discovery results to JSON file in output directory.

        Saves to standardized paths expected by APlusDiscoveryAccessor:
        - output/discovery/a_plus_stocks.json
        - output/discovery/a_plus_etfs.json
        - output/discovery/a_plus_crypto.json

        Args:
            asset_class: Asset class name (stock, etf, crypto, discovery)
            results: Discovery results to save

        """
        try:
            # Create discovery output directory
            discovery_dir = Path("output") / "discovery"
            discovery_dir.mkdir(parents=True, exist_ok=True)

            # Determine filename based on asset class
            if asset_class == "discovery":
                # Consolidated results - save to general discovery file
                output_file = discovery_dir / "consolidated_discovery.json"
            else:
                # Asset-specific A+ results - use standardized naming
                output_file = discovery_dir / f"a_plus_{asset_class}s.json"

            # Also save timestamped backup in asset-specific directory
            asset_dir = Path("output") / asset_class
            asset_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = asset_dir / f"discovery_output_{timestamp}.json"

            # Save to both locations
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2, default=str)

            with open(backup_file, "w") as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info(f"✅ Saved {asset_class} discovery results to {output_file} (backup: {backup_file})")

        except Exception as e:
            self.logger.warning(f"Failed to save {asset_class} discovery results: {e}")
