"""AST static check enforcing stage-contract rules under analysis/stages/.

Run from CI:
    uv run python -m scripts.check_stage_contract src/finwiz/analysis/stages
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Violation:
    file: str
    line: int
    message: str


def check_directory(path: Path) -> list[Violation]:
    """Walk *path* and collect violations in every .py file."""
    violations: list[Violation] = []
    for py in path.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(), filename=str(py))
        except SyntaxError as exc:  # pragma: no cover
            violations.append(Violation(str(py), exc.lineno or 0, f"syntax error: {exc.msg}"))
            continue
        violations.extend(_check_file(py, tree))
    return violations


def _check_file(file: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    is_qualify = file.name == "qualify.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            v = _check_call(file, node, is_qualify)
            if v:
                violations.append(v)
    return violations


def _check_call(file: Path, node: ast.Call, is_qualify: bool) -> Violation | None:
    """Inspect one Call node for known offending patterns."""
    fname = _fully_qualified(node.func)
    # asyncio.gather without return_exceptions=True
    if fname == "asyncio.gather":
        kw = {k.arg: k.value for k in node.keywords if k.arg}
        ret_exc = kw.get("return_exceptions")
        if not (isinstance(ret_exc, ast.Constant) and ret_exc.value is True):
            return Violation(
                str(file),
                node.lineno,
                "asyncio.gather under analysis/stages/ must use return_exceptions=True",
            )
    # @stage(allow_degrade=True) outside qualify.py
    if fname == "stage":
        for kw in node.keywords:
            if kw.arg == "allow_degrade" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                if not is_qualify:
                    return Violation(
                        str(file),
                        node.lineno,
                        "allow_degrade=True forbidden outside qualify.py (only 'qualify' may DEGRADE)",
                    )
    return None


def _fully_qualified(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return f"{_fully_qualified(node.value)}.{node.attr}"
    if isinstance(node, ast.Name):
        return node.id
    return ""


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: check_stage_contract.py <path>", file=sys.stderr)
        return 2
    target = Path(argv[1])
    if not target.exists():
        print(f"path does not exist: {target}", file=sys.stderr)
        return 2
    violations = check_directory(target)
    if not violations:
        print(f"check_stage_contract: {target} clean")
        return 0
    for v in violations:
        print(f"{v.file}:{v.line}: {v.message}", file=sys.stderr)
    print(f"check_stage_contract: {len(violations)} violation(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv))
