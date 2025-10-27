#!/usr/bin/env python3
"""
FinWiz Codebase Cleanup Script

Removes temporary files, debug outputs, and one-off verification scripts
while preserving all essential functionality and active development files.
"""

import os
import shutil
from pathlib import Path


def cleanup_temp_files():
    """Remove temporary and debug files from root directory."""
    temp_files = [
        "crewai_flow.html",
        "flow_execution.log",
        "report_only_output.log",
        "report_test.log",
        "mypy_full_output.txt",
        "prompts.txt",
        ".DS_Store",
    ]

    removed_files = []
    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)
            removed_files.append(file)
            print(f"✅ Removed: {file}")

    return removed_files


def cleanup_verification_scripts():
    """Move verification scripts to scripts/archive/ directory."""
    verification_files = [
        "test_crypto_schema_fix.py",
        "test_integration_fixes.sh",
        "test_runtime_fixes.py",
        "verify_batch_config.py",
        "verify_complete_analysis.py",
        "verify_critical_fixes.sh",
        "verify_error_handling.py",
        "verify_final_report_generator.py",
        "verify_metrics_tracking.py",
        "verify_rate_limiter.py",
        "run_report_only.py",
        "run_report_simple.py",
    ]

    # Create archive directory
    archive_dir = Path("scripts/archive")
    archive_dir.mkdir(parents=True, exist_ok=True)

    moved_files = []
    for file in verification_files:
        if os.path.exists(file):
            shutil.move(file, archive_dir / file)
            moved_files.append(file)
            print(f"📁 Moved to scripts/archive/: {file}")

    return moved_files


def cleanup_cache_directories():
    """Clean regenerable cache directories."""
    cache_dirs = [".mypy_cache", ".pytest_cache", ".ruff_cache", "htmlcov"]

    cleaned_dirs = []
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            cleaned_dirs.append(cache_dir)
            print(f"🗂️  Cleaned cache: {cache_dir}")

    return cleaned_dirs


def cleanup_old_output():
    """Remove old output directory."""
    if os.path.exists("output.old"):
        shutil.rmtree("output.old")
        print("🗂️  Removed: output.old/")
        return True
    return False


def main():
    """Execute cleanup operations."""
    print("🧹 Starting FinWiz Codebase Cleanup...")
    print("=" * 50)

    # Cleanup operations
    temp_files = cleanup_temp_files()
    verification_files = cleanup_verification_scripts()
    cache_dirs = cleanup_cache_directories()
    old_output_removed = cleanup_old_output()

    # Summary
    print("\n" + "=" * 50)
    print("✨ Cleanup Summary:")
    print(f"   • Removed {len(temp_files)} temporary files")
    print(f"   • Archived {len(verification_files)} verification scripts")
    print(f"   • Cleaned {len(cache_dirs)} cache directories")
    if old_output_removed:
        print("   • Removed old output directory")

    print("\n🎉 Cleanup completed successfully!")
    print("   • Repository is now cleaner and more organized")
    print("   • All essential functionality preserved")
    print("   • Active development files untouched")


if __name__ == "__main__":
    main()
