"""Payload model for the collect stage."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class CollectedData(BaseModel):
    """Wrapper around the dict produced by collect.

    The shape stays a free-form dict because the underlying tools return
    heterogenous structures (price history, fundamentals, sentiment, macro).
    Tightening the schema is out of scope for v5.1.
    """

    data: dict[str, Any]

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
