"""Enums for quantitative analysis models."""

from enum import StrEnum


class TradeType(StrEnum):
    """Type of trade."""

    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"


class TradeStatus(StrEnum):
    """Status of trade."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class MarketRegimeType(StrEnum):
    """Market regime types."""

    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"


class SignalType(StrEnum):
    """Technical analysis signal types."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"
