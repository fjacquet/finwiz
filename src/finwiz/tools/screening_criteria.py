"""
Screening criteria definitions and filtering logic for market screening.

This module contains the criteria definitions and filtering logic used to
screen different asset types (ETFs, stocks, cryptocurrencies) for A+ candidates.
"""

from typing import Any, Literal


class ScreeningCriteria:
    """Screening criteria definitions and filtering logic."""

    @staticmethod
    def get_default_criteria(asset_type: Literal["etf", "stock", "crypto"]) -> dict[str, Any]:
        """Get default A+ screening criteria for asset type."""
        if asset_type == "etf":
            return {
                "max_expense_ratio": 0.25,  # 0.25% for specialized, 0.15% for broad market
                "min_aum": 1e9,  # $1B minimum AUM
                "max_tracking_error": 0.002,  # 0.20% tracking error
                "min_history_years": 3,  # 3 years minimum history
                "require_ucits": False,  # UCITS compliance for EU investors
            }
        elif asset_type == "stock":
            return {
                "min_roe": 0.20,  # 20% ROE minimum
                "min_revenue_growth": 0.15,  # 15% annual revenue growth
                "max_debt_to_equity": 0.3,  # 30% max debt-to-equity
                "min_market_cap": 1e9,  # $1B minimum market cap
                "require_positive_fcf": True,  # Positive free cash flow
                "require_growing_fcf": True,  # Growing free cash flow
            }
        elif asset_type == "crypto":
            return {
                "min_market_cap": 10e9,  # $10B minimum market cap
                "min_daily_volume": 500e6,  # $500M minimum daily volume
                "min_age_months": 36,  # 36 months minimum age
                "require_institutional_adoption": False,  # Institutional adoption
                "require_real_utility": False,  # Real utility/use case
            }
        else:
            return {}

    @staticmethod
    def passes_screening_filters(market_data: dict[str, Any], asset_type: str, criteria: dict[str, Any]) -> bool:
        """Check if market data passes screening filters."""
        try:
            if asset_type == "etf":
                return ScreeningCriteria._passes_etf_filters(market_data, criteria)
            elif asset_type == "stock":
                return ScreeningCriteria._passes_stock_filters(market_data, criteria)
            elif asset_type == "crypto":
                return ScreeningCriteria._passes_crypto_filters(market_data, criteria)
            else:
                return False

        except Exception:
            return False

    @staticmethod
    def _passes_etf_filters(data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if ETF passes screening filters."""
        try:
            # Expense ratio check
            if data.get("expense_ratio", 1.0) > criteria.get("max_expense_ratio", 0.25):
                return False

            # AUM check
            if data.get("aum", 0) < criteria.get("min_aum", 1e9):
                return False

            # Tracking error check
            if data.get("tracking_error", 0.01) > criteria.get("max_tracking_error", 0.002):
                return False

            # History check
            if data.get("history_years", 0) < criteria.get("min_history_years", 3):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def _passes_stock_filters(data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if stock passes screening filters."""
        try:
            # ROE check
            if data.get("roe", 0) < criteria.get("min_roe", 0.20):
                return False

            # Revenue growth check
            if data.get("revenue_growth", 0) < criteria.get("min_revenue_growth", 0.15):
                return False

            # Debt-to-equity check
            if data.get("debt_to_equity", 1.0) > criteria.get("max_debt_to_equity", 0.3):
                return False

            # Market cap check
            if data.get("market_cap", 0) < criteria.get("min_market_cap", 1e9):
                return False

            # Free cash flow checks
            if criteria.get("require_positive_fcf", True) and not data.get("fcf_positive", False):
                return False

            if criteria.get("require_growing_fcf", True) and not data.get("fcf_growing", False):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def _passes_crypto_filters(data: dict[str, Any], criteria: dict[str, Any]) -> bool:
        """Check if crypto passes screening filters."""
        try:
            # Market cap check
            if data.get("market_cap", 0) < criteria.get("min_market_cap", 10e9):
                return False

            # Daily volume check
            if data.get("daily_volume", 0) < criteria.get("min_daily_volume", 500e6):
                return False

            # Age check
            if data.get("age_months", 0) < criteria.get("min_age_months", 36):
                return False

            # Institutional adoption check (if required)
            if criteria.get("require_institutional_adoption", False) and not data.get("institutional_adoption", False):
                return False

            # Real utility check (if required)
            if criteria.get("require_real_utility", False) and not data.get("real_utility", False):
                return False

            return True

        except Exception:
            return False
