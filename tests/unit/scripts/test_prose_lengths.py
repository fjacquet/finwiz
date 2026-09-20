from __future__ import annotations

import json
from pathlib import Path

from scripts.prose_lengths import summarise


def test_summarise_returns_median_words_per_prose_field(tmp_path: Path) -> None:
    def write(name: str, thesis: str) -> Path:
        path = tmp_path / f"{name}_enriched.json"
        path.write_text(json.dumps({"qualitative": {"investment_synthesis": {"investment_thesis": thesis, "bull_case": "a b c"}}}, default=str), encoding="utf-8")
        return path

    files = [write("A", "un deux trois"), write("B", "un deux trois quatre cinq"), write("C", "un")]
    medians = summarise(files)
    assert medians["investment_synthesis.investment_thesis"] == 3
    assert medians["investment_synthesis.bull_case"] == 3
