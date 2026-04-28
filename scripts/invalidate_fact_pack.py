"""CLI to invalidate fact pack cache entries.

Usage:
    uv run python -m scripts.invalidate_fact_pack <TICKER>
    uv run python -m scripts.invalidate_fact_pack --all
"""

from __future__ import annotations

import sys

from finwiz.cache.fact_pack_cache import FactPackCache


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: invalidate_fact_pack.py <TICKER> | --all", file=sys.stderr)
        return 2
    cache = FactPackCache()
    arg = argv[1]
    if arg == "--all":
        n = cache.invalidate_all()
        print(f"invalidated {n} fact pack cache entries")
        return 0
    if cache.invalidate(arg):
        print(f"invalidated fact pack for {arg}")
        return 0
    print(f"no cache entry for {arg}", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv))
