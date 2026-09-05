#!/usr/bin/env python3
"""Re-evaluate a run's summary against the current gate thresholds.

    make gate                       # output/run_summary.json
    uv run python scripts/run_gate.py path/to/run_summary.json

Loads the JSON the flow wrote, re-runs the same pure evaluator with the
thresholds currently in settings (FINWIZ_GATE__*), prints the same block the
flow logged, and exits with the same code: 0 PASS/WARN, 1 FAIL, 2 could not
evaluate. The stored verdict is ignored on purpose -- change a threshold in
.env, run this, see the effect without a 23-minute kickoff.

Imports the schema and the evaluator only. No flow, no state, no network.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from finwiz.analysis.run_gate import evaluate, exit_code_for, format_block, verdict
from finwiz.config.settings import get_settings
from finwiz.schemas.run_summary import RunSummary, Verdict


def main(argv: list[str] | None = None) -> int:
    """Re-evaluate the run summary at ``argv[0]`` (or the default path) and exit accordingly."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("summary", nargs="?", default="output/run_summary.json", help="path to a run_summary.json (default: output/run_summary.json)")
    args = parser.parse_args(argv)

    path = Path(args.summary)
    try:
        summary = RunSummary.model_validate_json(path.read_text())
    except (OSError, ValueError) as exc:
        print(f"run gate: could not read {path}: {exc}", file=sys.stderr)
        return exit_code_for(Verdict.ERROR)

    try:
        thresholds = get_settings().gate
    except ValueError as exc:
        # A threshold outside [0, 1], or one that is not a number at all. The
        # script exists to make a threshold change visible; the typo it invites
        # must read as "could not evaluate", never as the run's own FAIL.
        print(f"run gate: could not load thresholds -- check FINWIZ_GATE__*: {exc}", file=sys.stderr)
        return exit_code_for(Verdict.ERROR)

    checks = evaluate(summary.coverage, summary.valuation, summary.fact_pack, summary.phases, summary.cost, thresholds)
    v = verdict(checks)
    for line in format_block(checks, v, str(path)):
        print(line)
    return exit_code_for(v)


if __name__ == "__main__":
    raise SystemExit(main())
