from __future__ import annotations

from pathlib import Path

from finwiz.schemas.validate import validate_reporter_input


def test_validate_reporter_input_example() -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / "docs/schemas/examples/reporter_input.example.json"
    assert example.exists(), f"example payload not found: {example}"

    model = validate_reporter_input(example, strictness="error")
    assert model is not None
    # Basic structural sanity checks
    assert model.schema_version == 1
    assert hasattr(model, "ten_k_insights")
    assert hasattr(model, "stock_sentiments")
    assert hasattr(model, "etf_factsheets")
    assert hasattr(model, "crypto_theses")