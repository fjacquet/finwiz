#!/usr/bin/env python3
"""
Tier 1 Mypy Fixes - Pure Python, Zero AI

Handles the simplest, most mechanical fixes:
1. [unused-ignore] - Remove unnecessary type: ignore comments
2. [var-annotated] - Add annotations to untyped class variables

Usage:
    python scripts/fix_mypy_tier1.py --dry-run
    python scripts/fix_mypy_tier1.py
"""

import argparse
import ast
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FixStats:
    files_modified: int = 0
    unused_ignore_fixed: int = 0
    var_annotated_fixed: int = 0


def run_mypy() -> str:
    """Run mypy and capture output."""
    result = subprocess.run(["uv", "run", "mypy", "src/finwiz", "--ignore-missing-imports"], capture_output=True, text=True)
    return result.stdout + result.stderr


def parse_errors_by_type(output: str, error_type: str) -> dict[str, list[int]]:
    """Parse mypy output and return errors by file for a specific type."""
    pattern = rf"^(.+?):(\d+): error: .+? \[{re.escape(error_type)}\]$"
    errors = defaultdict(list)

    for line in output.split("\n"):
        match = re.match(pattern, line)
        if match:
            file_path = match.group(1)
            line_num = int(match.group(2))
            errors[file_path].append(line_num)

    return dict(errors)


def fix_unused_ignore(file_path: str, line_nums: list[int], dry_run: bool) -> int:
    """Remove type: ignore comments from specified lines."""
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed = 0

        for line_num in sorted(line_nums, reverse=True):  # Process from bottom up
            idx = line_num - 1
            if idx < len(lines):
                original = lines[idx]
                # Remove type: ignore[...] or type: ignore
                new_line = re.sub(r"\s*#\s*type:\s*ignore(\[[^\]]*\])?\s*(#.*)?$", lambda m: f"  {m.group(2)}" if m.group(2) else "", original)
                if new_line != original:
                    lines[idx] = new_line.rstrip()
                    fixed += 1

        if fixed > 0 and not dry_run:
            Path(file_path).write_text("\n".join(lines), encoding="utf-8")

        return fixed
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def fix_var_annotated(file_path: str, line_nums: list[int], dry_run: bool) -> int:
    """Add type annotations to untyped class variables.

    This is tricky - we need to understand the context.
    For now, only handle simple cases:
    - self.x = {} -> self.x: dict[str, Any] = {}
    - self.x = [] -> self.x: list[Any] = []
    - self.x = None -> self.x: Any = None
    """
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        lines = content.split("\n")
        fixed = 0
        need_any_import = False

        for line_num in sorted(line_nums, reverse=True):
            idx = line_num - 1
            if idx < len(lines):
                original = lines[idx]
                new_line = original

                # Pattern: self.x = {}
                if re.search(r"\bself\.(\w+)\s*=\s*\{\}", original):
                    new_line = re.sub(r"\bself\.(\w+)\s*=\s*\{\}", r"self.\1: dict[str, Any] = {}", original)
                    need_any_import = True

                # Pattern: self.x = []
                elif re.search(r"\bself\.(\w+)\s*=\s*\[\]", original):
                    new_line = re.sub(r"\bself\.(\w+)\s*=\s*\[\]", r"self.\1: list[Any] = []", original)
                    need_any_import = True

                # Pattern: self.x = None
                elif re.search(r"\bself\.(\w+)\s*=\s*None\b", original):
                    new_line = re.sub(r"\bself\.(\w+)\s*=\s*None\b", r"self.\1: Any = None", original)
                    need_any_import = True

                if new_line != original:
                    lines[idx] = new_line
                    fixed += 1

        # Add Any import if needed
        if need_any_import and fixed > 0:
            content_str = "\n".join(lines)
            if "from typing import" in content_str:
                if "Any" not in content_str:
                    lines = content_str.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith("from typing import"):
                            if "Any" not in line:
                                lines[i] = line.replace("from typing import ", "from typing import Any, ")
                            break

        if fixed > 0:
            # Verify syntax
            try:
                ast.parse("\n".join(lines))
            except SyntaxError as e:
                print(f"Syntax error in {file_path}: {e}")
                return 0

            if not dry_run:
                Path(file_path).write_text("\n".join(lines), encoding="utf-8")

        return fixed
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Tier 1 Mypy fixes (Python only)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    args = parser.parse_args()

    stats = FixStats()

    print("Running mypy to identify errors...")
    output = run_mypy()

    # Fix unused-ignore
    print("\n[1/2] Fixing unused-ignore errors...")
    unused_ignore_errors = parse_errors_by_type(output, "unused-ignore")
    for file_path, line_nums in unused_ignore_errors.items():
        fixed = fix_unused_ignore(file_path, line_nums, args.dry_run)
        if fixed > 0:
            stats.files_modified += 1
            stats.unused_ignore_fixed += fixed
            print(f"  {'[DRY RUN] ' if args.dry_run else ''}Fixed {fixed} in {file_path}")

    # Fix var-annotated
    print("\n[2/2] Fixing var-annotated errors...")
    var_errors = parse_errors_by_type(output, "var-annotated")
    for file_path, line_nums in var_errors.items():
        fixed = fix_var_annotated(file_path, line_nums, args.dry_run)
        if fixed > 0:
            if file_path not in unused_ignore_errors:
                stats.files_modified += 1
            stats.var_annotated_fixed += fixed
            print(f"  {'[DRY RUN] ' if args.dry_run else ''}Fixed {fixed} in {file_path}")

    # Summary
    print("\n" + "=" * 60)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}TIER 1 SUMMARY")
    print("=" * 60)
    print(f"Files modified:     {stats.files_modified}")
    print(f"unused-ignore:      {stats.unused_ignore_fixed}")
    print(f"var-annotated:      {stats.var_annotated_fixed}")
    print(f"Total fixes:        {stats.unused_ignore_fixed + stats.var_annotated_fixed}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply fixes")
    else:
        print("\n✅ Fixes applied! Run mypy again to verify.")


if __name__ == "__main__":
    main()
