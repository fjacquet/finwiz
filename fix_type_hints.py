#!/usr/bin/env python3
"""Script to systematically fix common type hint issues in the FinWiz codebase."""

import re
import sys
from pathlib import Path


def fix_dict_type_hints(content: str) -> str:
    """Fix missing type parameters for dict."""
    # Pattern: def func(...) -> dict:
    content = re.sub(r"(\bdef\s+\w+\([^)]*\)\s*->\s*)dict(\s*:)", r"\1dict[str, Any]\2", content)

    # Pattern: param: dict = None
    content = re.sub(r"(\w+:\s*)dict(\s*=\s*None)", r"\1dict[str, Any] | None\2", content)

    # Pattern: param: dict)
    content = re.sub(r"(\w+:\s*)dict(\s*\))", r"\1dict[str, Any]\2", content)

    return content


def fix_list_type_hints(content: str) -> str:
    """Fix missing type parameters for list."""
    # Pattern: param: list = None
    content = re.sub(r"(\w+:\s*)list(\s*=\s*None)", r"\1list[Any] | None\2", content)

    # Pattern: param: list)
    content = re.sub(r"(\w+:\s*)list(\s*\))", r"\1list[Any]\2", content)

    # Pattern: -> list:
    content = re.sub(r"(\bdef\s+\w+\([^)]*\)\s*->\s*)list(\s*:)", r"\1list[Any]\2", content)

    return content


def ensure_any_import(content: str) -> str:
    """Ensure 'Any' is imported from typing."""
    # Check if Any is already imported
    if "from typing import" in content and "Any" not in content.split("from typing import")[1].split("\n")[0]:
        # Add Any to existing typing import
        content = re.sub(r"(from typing import )([^Any\n]+)", r"\1Any, \2", content, count=1)
    elif "from typing import" not in content and "import typing" not in content:
        # Add new typing import at the top after docstring
        lines = content.split("\n")
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                else:
                    insert_idx = i + 1
                    break
            elif not in_docstring and line.strip() and not line.startswith("#"):
                insert_idx = i
                break

        if insert_idx > 0:
            lines.insert(insert_idx, "from typing import Any")
            lines.insert(insert_idx + 1, "")
            content = "\n".join(lines)

    return content


def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        content = file_path.read_text()
        original = content

        # Apply fixes
        content = fix_dict_type_hints(content)
        content = fix_list_type_hints(content)

        # Ensure Any is imported if we made changes
        if content != original:
            content = ensure_any_import(content)
            file_path.write_text(content)
            print(f"✓ Fixed: {file_path}")
            return True

        return False
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    src_dir = Path("src/finwiz")

    if not src_dir.exists():
        print(f"Error: {src_dir} not found", file=sys.stderr)
        sys.exit(1)

    python_files = list(src_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")

    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
