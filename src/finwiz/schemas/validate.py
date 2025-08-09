from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import ValidationError

from .report import ReporterInput

Strictness = Literal["off", "warn", "error"]


def _get_strictness(env_value: str | None) -> Strictness:
    val = (env_value or "warn").strip().lower()
    if val in {"off", "warn", "error"}:
        return val  # type: ignore[return-value]
    return "warn"


def validate_reporter_input(
    data: dict[str, Any] | str | Path, *, strictness: Strictness | None = None
) -> ReporterInput | None:
    """
    Validate a ReporterInput payload.

    Args:
        data: A dict payload or a path/str to a JSON file.
        strictness: Overrides VALIDATION_STRICTNESS env when provided.

    Returns:
        ReporterInput on success. If strictness is 'off' or 'warn', returns ReporterInput or None accordingly.

    Raises:
        ValidationError when strictness == 'error' and validation fails.

    """
    mode = strictness or _get_strictness(os.getenv("VALIDATION_STRICTNESS"))

    try:
        payload: dict[str, Any]
        if isinstance(data, dict):
            payload = data
        else:
            # Accept path-like inputs
            path = Path(str(data))
            payload = json.loads(path.read_text(encoding="utf-8"))

        return ReporterInput.model_validate(payload)
    except ValidationError as e:
        if mode == "error":
            raise
        if mode == "warn":
            print(f"[validation:warn] ReporterInput validation failed: {e}", file=sys.stderr)
        return None


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print(
            "Usage: python -m finwiz.schemas.validate <reporter_input.json> [off|warn|error]", file=sys.stderr
        )
        return 2
    path = argv[0]
    strict: Strictness | None = None
    if len(argv) > 1:
        strict = _get_strictness(argv[1])

    try:
        model = validate_reporter_input(path, strictness=strict)
        if model is None:
            # warn/off modes with failure already reported to stderr
            return 1
        # On success, echo normalized JSON to stdout
        print(model.model_dump_json(indent=2))
        return 0
    except ValidationError as e:
        print(f"[validation:error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
