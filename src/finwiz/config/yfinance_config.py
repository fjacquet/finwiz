"""
YFinance Configuration Module.

This module configures the yfinance library (v1.0+) with centralized settings
including the new retry mechanism for improved reliability.

Usage:
    # Import early in application startup
    from finwiz.config.yfinance_config import configure_yfinance

    # Initialize with default settings
    configure_yfinance()

    # Or with custom settings
    from finwiz.config.settings import get_yfinance_settings
    configure_yfinance(get_yfinance_settings())

Reference: https://ranaroussi.github.io/yfinance/advanced/config.html
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from finwiz.config.settings import YFinanceSettings

logger = logging.getLogger(__name__)

# Track if configuration has been applied
_configured = False


def configure_yfinance(settings: "YFinanceSettings | None" = None) -> bool:
    """
    Configure yfinance library with centralized settings.

    This function applies the yfinance v1.0+ configuration including:
    - Network retry mechanism (exponential backoff)
    - Proxy settings
    - Debug/logging options

    Args:
        settings: Optional YFinanceSettings instance. If None, loads from get_yfinance_settings().

    Returns:
        True if configuration was applied, False if already configured or yfinance unavailable.

    Example:
        >>> from finwiz.config.yfinance_config import configure_yfinance
        >>> configure_yfinance()
        True
        >>> configure_yfinance()  # Already configured
        False
    """
    global _configured

    if _configured:
        logger.debug("yfinance already configured, skipping")
        return False

    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed, skipping configuration")
        return False

    # Check for yfinance 1.0+ config attribute
    if not hasattr(yf, "config"):
        logger.warning(
            "yfinance.config not available (requires yfinance>=1.0). "
            "Retry mechanism not applied. Consider upgrading: pip install yfinance>=1.0"
        )
        return False

    # Load settings if not provided
    if settings is None:
        from finwiz.config.settings import get_yfinance_settings
        settings = get_yfinance_settings()

    # Apply network settings
    yf.config.network.retries = settings.retries
    if settings.proxy:
        yf.config.network.proxy = settings.proxy

    # Apply debug settings
    yf.config.debug.hide_exceptions = settings.hide_exceptions
    yf.config.debug.logging = settings.logging

    _configured = True

    logger.info(
        f"yfinance configured: retries={settings.retries}, "
        f"proxy={settings.proxy or 'None'}, "
        f"logging={settings.logging}"
    )

    return True


def reset_yfinance_config() -> None:
    """
    Reset yfinance configuration state (useful for testing).

    Note: This only resets the tracking flag. The actual yfinance
    settings may need to be reconfigured.
    """
    global _configured
    _configured = False
    logger.debug("yfinance configuration state reset")


def is_yfinance_configured() -> bool:
    """
    Check if yfinance has been configured.

    Returns:
        True if configure_yfinance() has been called successfully.
    """
    return _configured


def get_yfinance_config_status() -> dict[str, object]:
    """
    Get current yfinance configuration status.

    Returns:
        Dictionary with configuration status and current values.

    Example:
        >>> status = get_yfinance_config_status()
        >>> print(status)
        {'configured': True, 'retries': 2, 'proxy': None, 'logging': False}
    """
    try:
        import yfinance as yf

        if not hasattr(yf, "config"):
            return {
                "configured": False,
                "error": "yfinance.config not available (requires yfinance>=1.0)",
            }

        return {
            "configured": _configured,
            "retries": yf.config.network.retries,
            "proxy": yf.config.network.proxy,
            "hide_exceptions": yf.config.debug.hide_exceptions,
            "logging": yf.config.debug.logging,
        }
    except ImportError:
        return {
            "configured": False,
            "error": "yfinance not installed",
        }
