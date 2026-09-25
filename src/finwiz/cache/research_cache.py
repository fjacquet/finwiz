"""On-disk cache of successful web-research results.

Every research call pays OpenRouter's web-search fee plus prompt tokens, and
SWOT, Porter and news answers do not change within hours. Re-running the flow
the same day used to pay for all of them again. This cache lets
``research_with_retry`` return a recent answer without a request.

Storage: ``cache/research/<kind>/<sha256(key)>.json``. The key is hashed so a
caller-built key (ticker, free-text query) can never form a path. An entry
that is too old, unreadable, or no longer validates against the caller's
schema is a miss — the caller simply fetches again.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from finwiz.cache._paths import safe_asset_class
from finwiz.infrastructure.research.openrouter_structured import Citation, ResearchResult

if TYPE_CHECKING:
    from datetime import timedelta

logger = logging.getLogger(__name__)

_DEFAULT_DIR = Path("cache/research")


class ResearchCache:
    """Per-kind, per-key store of :class:`ResearchResult` payloads."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._dir = cache_dir or _DEFAULT_DIR

    def _path(self, kind: str, key: str) -> Path:
        # safe_asset_class's [a-z0-9_] alphabet fits the kind literals (swot, porter, news).
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._dir / safe_asset_class(kind) / f"{digest}.json"

    def get[T: BaseModel](self, kind: str, key: str, schema: type[T], *, max_age: timedelta) -> ResearchResult[T] | None:
        """Return the stored result if younger than ``max_age``, else ``None``.

        A hit costs nothing, so it carries ``cost_usd=0.0`` and zero tokens.
        """
        path = self._path(kind, key)
        if not path.exists():
            return None
        try:
            envelope = json.loads(path.read_text(encoding="utf-8"))
            fetched_at = datetime.fromisoformat(envelope["fetched_at"])
            age = datetime.now(UTC) - fetched_at
            if age > max_age:
                return None
            data = schema.model_validate(envelope["data"])
            citations = tuple(Citation(**c) for c in envelope["citations"])
        except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
            logger.warning(f"research cache entry for {kind} unreadable, refetching: {type(exc).__name__}")
            return None
        logger.info(f"research_{kind}: cache hit (age {age.total_seconds() / 3600:.1f}h)")
        return ResearchResult(data=data, citations=citations, cost_usd=0.0, prompt_tokens=0, completion_tokens=0)

    def put(self, kind: str, key: str, result: ResearchResult[Any]) -> None:
        """Store ``result``. Written to a temp file then renamed: holdings run concurrently."""
        path = self._path(kind, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        envelope = {
            "fetched_at": datetime.now(UTC).isoformat(),
            "key": key,
            "data": result.data.model_dump(mode="json"),
            "citations": [asdict(c) for c in result.citations],
        }
        tmp = path.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(envelope, default=str), encoding="utf-8")
        tmp.replace(path)
