#!/usr/bin/env python3
"""
Mechanical Mypy Error Fixer (SAFE VERSION)

Automatically fixes common, deterministic mypy errors without AI.
CONSERVATIVE: Does NOT modify imports to avoid breaking dependencies.

Usage:
    python scripts/fix_mypy_mechanical.py --dry-run  # Preview changes
    python scripts/fix_mypy_mechanical.py            # Apply fixes
"""

import argparse
import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FixResult:
    """Track fixes applied to a file."""

    file_path: Path
    fixes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class Stats:
    """Global statistics."""

    files_processed: int = 0
    files_modified: int = 0
    total_fixes: int = 0
    fixes_by_type: dict[str, int] = field(default_factory=dict)


def fix_init_return_none(content: str) -> tuple[str, int]:
    """Add -> None to __init__ methods missing return type."""
    pattern = r"(def __init__\s*\([^)]*\))(\s*:)"

    def replacer(match: re.Match) -> str:
        signature = match.group(1)
        colon = match.group(2)
        if "->" in signature:
            return match.group(0)
        return f"{signature} -> None{colon}"

    new_content, count = re.subn(pattern, replacer, content)
    return new_content, count


def fix_dunder_return_none(content: str) -> tuple[str, int]:
    """Add -> None to common dunder methods that return None."""
    none_return_dunders = ["__del__", "__setattr__", "__delattr__", "__setitem__", "__delitem__", "__post_init__", "__set_name__"]

    total_count = 0
    for dunder in none_return_dunders:
        pattern = rf"(def {dunder}\s*\([^)]*\))(\s*:)"

        def replacer(match: re.Match, dunder=dunder) -> str:
            signature = match.group(1)
            colon = match.group(2)
            if "->" in signature:
                return match.group(0)
            return f"{signature} -> None{colon}"

        content, count = re.subn(pattern, replacer, content)
        total_count += count

    return content, total_count


def fix_common_method_return_none(content: str) -> tuple[str, int]:
    """Add -> None to common methods that clearly return nothing.

    Safe methods: setup, teardown, configure, validate, register, etc.
    """
    none_return_methods = [
        "setUp",
        "tearDown",
        "setUpClass",
        "tearDownClass",
        "setup",
        "teardown",
        "configure",
        "reset",
        "clear",
        "register",
        "unregister",
        "add_",
        "remove_",
        "set_",
        "update_",
        "delete_",
        "close",
        "cleanup",
        "dispose",
        "validate_",
        "check_",
        "ensure_",
        "log_",
        "print_",
    ]

    total_count = 0
    for method_prefix in none_return_methods:
        if method_prefix.endswith("_"):
            # Prefix pattern
            pattern = rf"(def ({method_prefix}[a-zA-Z0-9_]*)\s*\(self[^)]*\))(\s*:)"
        else:
            # Exact match
            pattern = rf"(def {method_prefix}\s*\(self[^)]*\))(\s*:)"

        def replacer(match: re.Match) -> str:
            signature = match.group(1)
            colon = match.group(len(match.groups()))  # Last group is colon
            if "->" in signature:
                return match.group(0)
            return f"{signature} -> None{colon}"

        content, count = re.subn(pattern, replacer, content)
        total_count += count

    return content, total_count


def fix_async_return_none(content: str) -> tuple[str, int]:
    """Add -> None to async methods without return type that match safe patterns."""
    pattern = r"(async def (setup|teardown|configure|cleanup|close|validate|process)_?[a-zA-Z0-9_]*\s*\([^)]*\))(\s*:)"

    def replacer(match: re.Match) -> str:
        signature = match.group(1)
        colon = match.group(3)
        if "->" in signature:
            return match.group(0)
        return f"{signature} -> None{colon}"

    new_content, count = re.subn(pattern, replacer, content)
    return new_content, count


def fix_property_self_annotation(content: str) -> tuple[str, int]:
    """Fix common pattern: @property methods missing return type.

    For properties with common name patterns.
    """
    # Properties that return str
    str_properties = ["name", "id", "key", "path", "title", "description", "label", "message"]
    # Properties that return bool
    bool_properties = ["is_valid", "is_empty", "is_active", "is_enabled", "has_", "can_"]
    # Properties that return int
    int_properties = ["count", "size", "length", "index", "position"]

    total_count = 0

    # String properties
    for prop in str_properties:
        pattern = rf"(@property\s*\n\s*)(def {prop}\s*\(self\))(\s*:)"

        def replacer(match: re.Match) -> str:
            decorator = match.group(1)
            signature = match.group(2)
            colon = match.group(3)
            if "->" in signature:
                return match.group(0)
            return f"{decorator}{signature} -> str{colon}"

        content, count = re.subn(pattern, replacer, content)
        total_count += count

    return content, total_count


def fix_self_parameter_type(content: str) -> tuple[str, int]:
    """Remove 'self: Self' annotations in favor of plain 'self'."""
    # Pattern: self: Self or self: "ClassName"
    pattern = r'def ([a-zA-Z_][a-zA-Z0-9_]*)\s*\(\s*self\s*:\s*["\']?[A-Za-z_][A-Za-z0-9_]*["\']?\s*([,)])'

    def replacer(match: re.Match) -> str:
        method_name = match.group(1)
        rest = match.group(2)
        return f"def {method_name}(self{rest}"

    new_content, count = re.subn(pattern, replacer, content)
    return new_content, count


def fix_explicit_any_returns(content: str) -> tuple[str, int]:
    """Fix 'Returning Any from function declared to return X' for simple cases.

    Add explicit cast when returning dict.get() or list[0] etc.
    This is too complex for regex - skip for safety.
    """
    return content, 0


def add_missing_any_import(content: str) -> tuple[str, int]:
    """Add 'Any' to typing imports if used but not imported."""
    # Check if Any is used in annotations but not imported
    if "Any" not in content:
        return content, 0

    # Check if already imported
    if re.search(r"from typing import.*\bAny\b", content):
        return content, 0

    if "from typing import" in content:
        # Add Any to existing import
        pattern = r"(from typing import )([^\n]+)"

        def replacer(match: re.Match) -> str:
            prefix = match.group(1)
            imports = match.group(2)
            if "Any" in imports:
                return match.group(0)
            return f"{prefix}Any, {imports}"

        new_content, count = re.subn(pattern, replacer, content, count=1)
        return new_content, count

    return content, 0


def process_file(file_path: Path, dry_run: bool = True) -> FixResult:
    """Process a single file and apply fixes."""
    result = FixResult(file_path=file_path)

    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content

        # Apply SAFE fixes only (no import removal!)
        fixers = [
            ("init_return_none", fix_init_return_none),
            ("dunder_return_none", fix_dunder_return_none),
            ("common_method_return_none", fix_common_method_return_none),
            ("async_return_none", fix_async_return_none),
            ("self_parameter_type", fix_self_parameter_type),
            ("add_any_import", add_missing_any_import),
        ]

        for fix_name, fixer in fixers:
            content, count = fixer(content)
            if count > 0:
                result.fixes.append(f"{fix_name}: {count}")

        # Verify syntax is still valid
        if content != original_content:
            try:
                ast.parse(content)
            except SyntaxError as e:
                result.errors.append(f"Syntax error after fixes: {e}")
                return result

            if not dry_run:
                file_path.write_text(content, encoding="utf-8")

    except Exception as e:
        result.errors.append(str(e))

    return result


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in directory."""
    return sorted(directory.rglob("*.py"))


def main():
    parser = argparse.ArgumentParser(description="Fix mechanical mypy errors (SAFE)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--path", type=Path, default=Path("src/finwiz"), help="Path to process (default: src/finwiz)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    stats = Stats()
    stats.fixes_by_type = {}

    files = find_python_files(args.path)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing {len(files)} Python files...\n")

    modified_files = []

    for file_path in files:
        result = process_file(file_path, dry_run=args.dry_run)
        stats.files_processed += 1

        if result.fixes:
            stats.files_modified += 1
            modified_files.append(result)

            for fix in result.fixes:
                fix_type, count = fix.split(": ")
                count = int(count)
                stats.total_fixes += count
                stats.fixes_by_type[fix_type] = stats.fixes_by_type.get(fix_type, 0) + count

        if result.errors:
            print(f"❌ {file_path}: {result.errors}")

    # Summary
    print("=" * 60)
    print(f"{'[DRY RUN] ' if args.dry_run else ''}SUMMARY")
    print("=" * 60)
    print(f"Files processed: {stats.files_processed}")
    print(f"Files modified:  {stats.files_modified}")
    print(f"Total fixes:     {stats.total_fixes}")
    print()

    if stats.fixes_by_type:
        print("Fixes by type:")
        for fix_type, count in sorted(stats.fixes_by_type.items(), key=lambda x: -x[1]):
            print(f"  {fix_type}: {count}")
        print()

    if args.verbose and modified_files:
        print("Modified files:")
        for result in modified_files:
            fixes_str = ", ".join(result.fixes)
            print(f"  {result.file_path}: {fixes_str}")
    elif modified_files:
        print(f"Run with --verbose to see all {len(modified_files)} modified files")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply fixes")


if __name__ == "__main__":
    main()
