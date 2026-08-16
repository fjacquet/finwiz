"""The discovery artifact name must be consistent between writer and readers."""

from pathlib import Path

SRC = Path("src/finwiz")


def test_no_source_file_references_the_retired_name():
    offenders = []
    for path in SRC.rglob("*.py"):
        if "discovery_latest.json" in path.read_text(encoding="utf-8"):
            offenders.append(str(path))
    assert offenders == []
