"""Check that newly added Python files do not exceed 300 lines.

Used by pre-commit hooks and ``make check-file-size``.
Existing files are exempt — only files added in the current commit are checked.

Pass ``--check-all`` to treat every argument as a new file (for CI use).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MAX_LINES = 300


def _get_new_files_from_git() -> set[str]:
    """Return set of file paths that are newly staged (added) in git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return {f.strip() for f in result.stdout.splitlines() if f.strip()}
    except FileNotFoundError:
        pass
    return set()


def main() -> int:
    check_all = "--check-all" in sys.argv
    files = [f for f in sys.argv[1:] if f != "--check-all"]
    if not files:
        return 0

    if check_all:
        targets = set(files)
    else:
        new_files = _get_new_files_from_git()
        if not new_files:
            return 0
        targets = new_files & set(files)

    failures: list[str] = []
    for filepath in targets:
        if not filepath.endswith(".py"):
            continue
        path = Path(filepath)
        if not path.exists():
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            failures.append(f"  {filepath}: {line_count} lines (max {MAX_LINES})")

    if failures:
        print(f"New files exceeding {MAX_LINES}-line limit:")
        for f in failures:
            print(f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
