from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import BaseModel

from . import (
    CryptoThesis,
    ETFFactsheet,
    ETFTopHolding,
    MarketSentiment,
    ReporterInput,
    RiskAssessmentStandardized,
    TenKInsight,
    ValidatedTicker,
)


def _models() -> Iterable[type[BaseModel]]:
    yield ReporterInput
    yield TenKInsight
    yield MarketSentiment
    yield RiskAssessmentStandardized  # type: ignore[misc]
    yield ETFFactsheet
    yield ETFTopHolding
    yield CryptoThesis
    yield ValidatedTicker


def export_json_schemas(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for model in _models():
        schema = model.model_json_schema()
        # file name e.g., ReporterInput.schema.json
        fname = f"{model.__name__}.schema.json"
        (out_dir / fname).write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


def main() -> None:
    # default export directory relative to repo root docs/schemas
    # __file__ -> schemas -> finwiz (pkg) -> src -> repo root (parents[3])
    default_out = Path(__file__).resolve().parents[3] / "docs" / "schemas"
    export_json_schemas(default_out)
    print(f"Exported JSON Schemas to {default_out}")


if __name__ == "__main__":
    main()
