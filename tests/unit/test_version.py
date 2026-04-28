"""Pin pyproject.toml version against CHANGELOG header (v5.2.0+)."""

from __future__ import annotations

import re
from pathlib import Path

# Match the [5.X.Y] - YYYY-MM-DD format used in Keep-a-Changelog
_CHANGELOG_HEADER = re.compile(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}", re.MULTILINE)
_PYPROJECT_VERSION = re.compile(r'^version = "(\d+\.\d+\.\d+)"', re.MULTILINE)


def test_pyproject_version_matches_latest_changelog_release() -> None:
    """The pyproject version equals the latest non-Unreleased CHANGELOG entry.

    Pins v5.2.0+ alignment: the SemVer tag, pyproject, and CHANGELOG must agree.
    """
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    pp_match = _PYPROJECT_VERSION.search(pyproject)
    assert pp_match is not None, "pyproject.toml has no version line"
    pp_version = pp_match.group(1)

    cl_match = _CHANGELOG_HEADER.search(changelog)
    assert cl_match is not None, "CHANGELOG.md has no released version header"
    cl_version = cl_match.group(1)

    assert pp_version == cl_version, f"Version drift: pyproject={pp_version} vs CHANGELOG latest={cl_version}. Update pyproject.toml or add CHANGELOG entry."


def test_version_is_5_2_0_or_later() -> None:
    """Pin the v5.2.0 alignment epoch -- versions <5.2.0 are now historical."""
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    pp_match = _PYPROJECT_VERSION.search(pyproject)
    assert pp_match is not None
    parts = tuple(int(p) for p in pp_match.group(1).split("."))
    assert parts >= (5, 2, 0), f"After the v5.2.0 alignment, versions <5.2.0 are no longer valid. Current pyproject={pp_match.group(1)}"
