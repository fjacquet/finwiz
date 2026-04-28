"""Fact pack cache adapter (v5.2).

Thin wrapper over AnalysisCacheManager with schema-version tagging so v5.2
cache entries can detect schema migrations and force re-fetch.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from finwiz.schemas.hybrid_analysis.fact_pack import FactPack

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "5.2"
_DEFAULT_DIR = Path("cache/fact_packs")
# Mirrors HoldingDecision._TICKER_RE — defense-in-depth against path traversal
# (e.g. "../../etc/passwd") in cache filenames. Tickers always reach this layer
# upper-cased; the regex matches Yahoo / Kraken formats only.
_TICKER_RE = re.compile(r"^[A-Z0-9:.\-^=]{1,15}$")


def _safe_ticker(ticker: str) -> str:
    """Upper-case the ticker and reject anything outside the allowed alphabet.

    Pydantic already validates `HoldingDecision.ticker`, but the cache also
    runs from contexts (manual CLI invocation, future callers) where the
    ticker is a raw string. Validating here keeps the filesystem invariant
    enforced no matter who reaches the cache.
    """
    upper = ticker.upper()
    if not _TICKER_RE.match(upper):
        raise ValueError(f"invalid ticker {ticker!r}: must match {_TICKER_RE.pattern}")
    # `.` is in the allowed alphabet for tickers like BRK.B, but `..` is a
    # path-traversal token even though it satisfies the alphabet — reject it
    # explicitly. (`/` and `\` are already excluded by the alphabet.)
    if ".." in upper:
        raise ValueError(f"invalid ticker {ticker!r}: contains path-traversal sequence '..'")
    return upper


class FactPackCache:
    """Cache for fact packs, version-tagged for safe schema migrations.

    Storage: cache/fact_packs/<TICKER>.json. Each file carries
    `schema_version: "5.2"` — entries with mismatched version trigger silent
    re-fetch (caller's responsibility — `get()` returns None for mismatches).
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir or _DEFAULT_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, ticker: str) -> Path:
        return self._dir / f"{_safe_ticker(ticker)}.json"

    def get(self, ticker: str) -> FactPack | None:
        """Return cached FactPack if valid (any age — caller checks freshness).

        Returns None if file missing, corrupted, or schema version mismatched.
        Returns FactPack even if 7-14d old (marked stale via freshness derivation).
        Returns None if older than 14d (cache invalid).
        """
        path = self._path(ticker)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"fact_pack cache read failed for {ticker}: {e}")
            return None
        if data.get("schema_version") != _SCHEMA_VERSION:
            logger.info(f"fact_pack schema mismatch for {ticker}; forcing re-fetch")
            return None
        try:
            payload = data["payload"]
            # Re-derive freshness on load (so stale entries get marked correctly)
            fetched_at = datetime.fromisoformat(payload["fetched_at"])
            payload["freshness"] = FactPack.derive_freshness(fetched_at)
            return FactPack.model_validate(payload)
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"fact_pack cache entry invalid for {ticker}: {e}")
            return None

    def put(self, ticker: str, fact_pack: FactPack) -> None:
        """Write fact pack to cache with schema version tag."""
        path = self._path(ticker)
        envelope = {
            "schema_version": _SCHEMA_VERSION,
            "cached_at": datetime.now(UTC).isoformat(),
            "payload": fact_pack.model_dump(mode="json"),
        }
        path.write_text(json.dumps(envelope, default=str, indent=2), encoding="utf-8")

    def invalidate(self, ticker: str) -> bool:
        """Remove a single ticker's cache entry. Returns True if file existed."""
        path = self._path(ticker)
        if path.exists():
            path.unlink()
            logger.info(f"invalidated fact_pack cache for {ticker}")
            return True
        return False

    def invalidate_all(self) -> int:
        """Remove all fact pack cache entries. Returns count removed."""
        count = 0
        for path in self._dir.glob("*.json"):
            path.unlink()
            count += 1
        logger.info(f"invalidated {count} fact_pack cache entries")
        return count
