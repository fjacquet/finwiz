"""
FinWiz Reporting Module.

Pure Python report generation replacing AI-based reporting for speed and cost efficiency.
"""

from .base_report_generator import BaseReportGenerator
from .crypto_report_generator import CryptoReportGenerator
from .discovery_report_generator import DiscoveryReportGenerator
from .etf_report_generator import ETFReportGenerator
from .python_report_generator import PythonReportGenerator, generate_python_report
from .rebalancing_report_generator import RebalancingReportGenerator
from .stock_report_generator import StockReportGenerator

# Registry mapping crew names to their report generators
CREW_GENERATORS: dict[str, type[BaseReportGenerator]] = {
    "stock_crew": StockReportGenerator,
    "etf_crew": ETFReportGenerator,
    "crypto_crew": CryptoReportGenerator,
    "discovery_crew": DiscoveryReportGenerator,
    "investment_discovery_crew": DiscoveryReportGenerator,
    "rebalancing_crew": RebalancingReportGenerator,
    "portfolio_rebalancing_crew": RebalancingReportGenerator,
}


def get_generator_for_crew(crew_name: str) -> BaseReportGenerator | None:
    """
    Get the appropriate report generator for a crew.

    Args:
        crew_name: Name of the crew (e.g., "stock_crew", "etf_crew")

    Returns:
        Instance of the appropriate report generator, or None if not found

    """
    generator_class = CREW_GENERATORS.get(crew_name)
    if generator_class:
        return generator_class()
    return None


__all__ = [
    "PythonReportGenerator",
    "generate_python_report",
    "BaseReportGenerator",
    "StockReportGenerator",
    "ETFReportGenerator",
    "CryptoReportGenerator",
    "DiscoveryReportGenerator",
    "RebalancingReportGenerator",
    "CREW_GENERATORS",
    "get_generator_for_crew",
]
