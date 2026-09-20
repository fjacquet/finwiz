"""Median word count per qualitative prose field over enriched analyses.

Usage: uv run python scripts/prose_lengths.py [output]
Compares a run against the budgets the prompt asks for (thesis 150-250 words,
scenarios 80-120, business model 120-180).
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

_SECTIONS = ("sec_insights", "fundamental_context", "technical_strategy", "contextual_risks", "investment_synthesis")


def summarise(paths: Iterable[Path]) -> dict[str, float]:
    words: dict[str, list[int]] = defaultdict(list)
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        qualitative = data.get("qualitative") or {}
        for section in _SECTIONS:
            body = qualitative.get(section) or {}
            for key, value in body.items():
                if isinstance(value, str) and value.strip():
                    words[f"{section}.{key}"].append(len(value.split()))
    return {field: statistics.median(counts) for field, counts in sorted(words.items())}


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path("output")
    medians = summarise(root.glob("**/*_enriched.json"))
    for field, median in medians.items():
        print(f"{field:55s} median words = {median:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
