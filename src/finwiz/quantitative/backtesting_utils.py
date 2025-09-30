"""
Utility functions for backtesting operations.

This module contains helper functions for data conversion,
feed creation, and other backtesting utilities.
"""

from typing import Any

import backtrader as bt
import pandas as pd


def create_backtrader_datafeed(data: pd.DataFrame, symbol: str) -> bt.feeds.PandasData:
    """
    Create Backtrader data feed from pandas DataFrame.

    Args:
        data: OHLCV data
        symbol: Symbol name

    Returns:
        Backtrader data feed

    """
    # Ensure proper column mapping
    data_feed = bt.feeds.PandasData(
        dataname=data,
        datetime=None,  # Use index as datetime
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
        openinterest=None,
    )

    # Set name for identification
    data_feed._name = symbol

    return data_feed


def setup_cerebro(config: Any) -> bt.Cerebro:
    """
    Set up and configure a Backtrader Cerebro instance.

    Args:
        config: Backtesting configuration

    Returns:
        Configured Cerebro instance

    """
    cerebro = bt.Cerebro()

    # Set initial capital
    cerebro.broker.setcash(config.initial_capital)

    # Set commission
    cerebro.broker.setcommission(commission=config.commission_pct)

    return cerebro
