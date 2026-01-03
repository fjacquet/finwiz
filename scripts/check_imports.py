#!/usr/bin/env python
"""Check all imports in the finwiz package before running.

Usage:
    uv run python scripts/check_imports.py
"""

import importlib
import pkgutil
import sys
from pathlib import Path


def check_all_imports(package_name: str = "finwiz") -> tuple[list[str], list[tuple[str, str]]]:
    """Check all imports in a package.

    Returns:
        Tuple of (successful_imports, failed_imports)
        where failed_imports is list of (module_name, error_message)
    """
    successful = []
    failed = []

    # Import the main package first
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        failed.append((package_name, str(e)))
        return successful, failed

    successful.append(package_name)

    # Get the package path
    package_path = Path(package.__file__).parent

    # Walk through all modules
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=[str(package_path)],
        prefix=f"{package_name}.",
    ):
        try:
            importlib.import_module(modname)
            successful.append(modname)
        except Exception as e:
            failed.append((modname, str(e)))

    return successful, failed


def main() -> int:
    """Run import check."""
    print("🔍 Checking all imports in finwiz package...")
    print("=" * 60)

    successful, failed = check_all_imports("finwiz")

    if failed:
        print(f"\n❌ IMPORT ERRORS ({len(failed)} failures):")
        print("-" * 60)
        for module, error in failed:
            print(f"  {module}")
            print(f"    └─ {error}")
        print()

    print(f"\n✅ {len(successful)} modules imported successfully")

    if failed:
        print(f"❌ {len(failed)} modules failed to import")
        return 1

    print("\n✅ All imports OK - safe to run!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
