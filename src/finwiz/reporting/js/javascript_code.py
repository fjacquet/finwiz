"""JavaScript code for rebalancing reports.

The script lives in ../assets/rebalancing_javascript.js.
"""

from functools import cache
from pathlib import Path

_ASSETS = Path(__file__).parent.parent / "assets"


@cache
def get_rebalancing_javascript() -> str:
    """Return JavaScript code for rebalancing reports (read once from assets).

    Returns:
        JavaScript code as string
    """
    return (_ASSETS / "rebalancing_javascript.js").read_text(encoding="utf-8")
