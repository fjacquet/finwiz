"""CNN Fear & Greed Index adapter.

Provides market-wide sentiment via the CNN Fear & Greed Index.
No API key required.
"""

from __future__ import annotations

from finwiz.data.adapters.base_adapter import DataAcquisitionError
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def _score_to_label(score: int) -> str:
    """Convert Fear & Greed score (0-100) to classification label."""
    if score <= 25:
        return "Extreme Fear"
    if score <= 45:
        return "Fear"
    if score <= 55:
        return "Neutral"
    if score <= 75:
        return "Greed"
    return "Extreme Greed"


class FearGreedAdapter:
    """CNN Fear & Greed Index adapter.

    Uses fear-and-greed library as primary, with direct HTTP fallback.
    No API key required. Session-level caching.
    """

    def __init__(self, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._cached_value: tuple[int, str] | None = None

    def is_available(self) -> bool:
        """Always available (no API key needed)."""
        return True

    def get_fear_greed(self) -> tuple[int, str]:
        """Get current Fear & Greed index value and label.

        Returns:
            Tuple of (value: 0-100, label: str)

        Raises:
            DataAcquisitionError: If all sources fail.
        """
        if self._cached_value is not None:
            return self._cached_value

        # Primary: fear-and-greed library
        try:
            import fear_and_greed

            result = fear_and_greed.get()
            value = int(result.value)
            label = result.description
            self._cached_value = (value, label)
            logger.info(f"Fear & Greed Index: {value} ({label})")
            return self._cached_value
        except Exception as e:
            logger.warning(f"fear-and-greed library failed: {e}")

        # Fallback: direct HTTP to CNN endpoint
        try:
            import requests

            from finwiz.config.endpoints import FEAR_GREED_BASE

            resp = requests.get(FEAR_GREED_BASE, timeout=self.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
            score = int(data["fear_and_greed"]["score"])
            label = _score_to_label(score)
            self._cached_value = (score, label)
            logger.info(f"Fear & Greed Index (HTTP fallback): {score} ({label})")
            return self._cached_value
        except Exception as e:
            logger.warning(f"Fear & Greed HTTP fallback failed: {e}")
            raise DataAcquisitionError(f"Fear & Greed index unavailable: {e}") from e
