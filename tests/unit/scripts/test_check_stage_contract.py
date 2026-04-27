from pathlib import Path

from scripts.check_stage_contract import check_directory


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.write_text(src)
    return p


def test_check_passes_clean_source(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ok.py",
        "import asyncio\nasync def f():\n    await asyncio.gather(*[g()], return_exceptions=True)\nasync def g():\n    return 1\n",
    )
    violations = check_directory(tmp_path)
    assert violations == []


def test_check_flags_gather_without_return_exceptions(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "bad.py",
        "import asyncio\nasync def f():\n    await asyncio.gather(*[g()])\nasync def g():\n    return 1\n",
    )
    violations = check_directory(tmp_path)
    assert any("return_exceptions=True" in v.message for v in violations)


def test_check_flags_allow_degrade_outside_qualify(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "collect.py",
        "from finwiz.analysis.stages._resilience import stage\n@stage(name='collect', timeout_s=5, retries=0, allow_degrade=True)\ndef f(ctx): return None\n",
    )
    violations = check_directory(tmp_path)
    assert any("allow_degrade" in v.message and "qualify" in v.message for v in violations)


def test_check_allows_allow_degrade_in_qualify(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "qualify.py",
        "from finwiz.analysis.stages._resilience import stage\n@stage(name='qualify', timeout_s=5, retries=0, allow_degrade=True)\ndef f(ctx): return None\n",
    )
    violations = check_directory(tmp_path)
    assert violations == []
