"""
ETF Expense Ratio Fallback Utility.

Provides fallback expense ratio data when Yahoo Finance doesn't have it.
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Cache for loaded expense ratios
_EXPENSE_RATIOS_CACHE: dict | None = None


def load_expense_ratios() -> dict:
    """
    Load expense ratios from configuration file.

    Returns:
        Dictionary mapping ticker symbols to expense ratio data

    """
    global _EXPENSE_RATIOS_CACHE

    if _EXPENSE_RATIOS_CACHE is not None:
        return _EXPENSE_RATIOS_CACHE

    # Path from src/finwiz/utils/ -> project_root/data/
    # __file__ = .../src/finwiz/utils/etf_expense_fallback.py
    # parent.parent.parent.parent = project_root
    config_path = Path(__file__).parent.parent.parent.parent / "data" / "etf_expense_ratios.yaml"

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)
            _EXPENSE_RATIOS_CACHE = data or {}
            logger.info(f"📋 Loaded {len(_EXPENSE_RATIOS_CACHE)} ETF expense ratios from fallback config")
            return _EXPENSE_RATIOS_CACHE
    except FileNotFoundError:
        logger.warning(f"⚠️ Expense ratio config file not found: {config_path}")
        _EXPENSE_RATIOS_CACHE = {}
        return {}
    except Exception as e:
        logger.error(f"❌ Error loading expense ratio config: {e}")
        _EXPENSE_RATIOS_CACHE = {}
        return {}


def get_fallback_expense_ratio(ticker: str) -> float | None:
    """
    Get fallback expense ratio for a ticker.

    Args:
        ticker: ETF ticker symbol

    Returns:
        Expense ratio as decimal (e.g., 0.0007 for 0.07%) or None if not found

    """
    expense_ratios = load_expense_ratios()

    if ticker in expense_ratios:
        data = expense_ratios[ticker]
        expense_ratio = data.get("expense_ratio")

        if expense_ratio is not None:
            source = data.get("source", "manual config")
            logger.info(f"📋 Using fallback expense ratio for {ticker}: {expense_ratio:.4f} ({expense_ratio * 100:.2f}%) from {source}")
            return expense_ratio

    return None


def has_fallback_data(ticker: str) -> bool:
    """
    Check if fallback data exists for a ticker.

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if fallback data exists, False otherwise

    """
    expense_ratios = load_expense_ratios()
    return ticker in expense_ratios
