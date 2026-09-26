#!/usr/bin/env python
"""Static enforcement of the architecture invariants in docs/00-overview.md.

These rules are the reason the design survives contact with a growing codebase.
They are checked by parsing the AST — no imports are executed.

Run: `python scripts/check_architecture.py` (also wired into `make check` / CI).
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "backend" / "app"


@dataclass(frozen=True, slots=True)
class Violation:
    rule: str
    path: Path
    line: int
    message: str

    def render(self) -> str:
        rel = self.path.relative_to(REPO_ROOT)
        return f"  [{self.rule}] {rel}:{self.line} — {self.message}"


@dataclass(frozen=True, slots=True)
class ImportRule:
    """Forbid a package from importing another package."""

    rule: str
    package: str
    forbidden_prefixes: tuple[str, ...]
    reason: str


IMPORT_RULES: tuple[ImportRule, ...] = (
    ImportRule(
        rule="I5",
        package="indicators",
        forbidden_prefixes=("app.ai", "app.ml", "app.services", "app.api", "app.database"),
        reason="Technical analysis must be independent of AI, ML and I/O",
    ),
    ImportRule(
        rule="I6",
        package="risk",
        forbidden_prefixes=("app.ai", "app.api", "app.database", "app.services"),
        reason="Risk management must be independent of AI and I/O",
    ),
    ImportRule(
        rule="I10",
        package="scoring",
        forbidden_prefixes=("app.ai", "app.api", "app.database"),
        reason="Scoring must be a pure function of its inputs",
    ),
    ImportRule(
        rule="I2",
        package="api",
        forbidden_prefixes=("app.models", "sqlalchemy.orm", "app.providers"),
        reason="The API layer must go through services/repositories, not the ORM",
    ),
    ImportRule(
        rule="I2",
        package="domain",
        forbidden_prefixes=("app.models", "app.database", "app.api", "sqlalchemy", "fastapi"),
        reason="The domain layer must not know about persistence or transport",
    ),
    ImportRule(
        rule="I8",
        package="backtesting",
        forbidden_prefixes=("app.collectors", "app.paper_trading"),
        reason="Backtesting must be independent of live collection and paper trading",
    ),
)

#: Modules allowed to read the environment directly (invariant I11).
ENV_ALLOWED = {APP_ROOT / "core" / "config.py"}

#: Modules allowed to call ``datetime.now``/``utcnow`` directly (ADR-009).
CLOCK_ALLOWED = {APP_ROOT / "core" / "clock.py"}


def _iter_python_files(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*.py")) if "__pycache__" not in p.parts]


def _imported_modules(tree: ast.AST) -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append((node.module, node.lineno))
    return found


def check_imports(path: Path, tree: ast.AST) -> list[Violation]:
    try:
        package = path.relative_to(APP_ROOT).parts[0]
    except ValueError:
        return []
    violations: list[Violation] = []
    for rule in IMPORT_RULES:
        if package != rule.package:
            continue
        for module, lineno in _imported_modules(tree):
            if module.startswith(rule.forbidden_prefixes):
                violations.append(
                    Violation(
                        rule.rule,
                        path,
                        lineno,
                        f"'{package}' must not import '{module}'. {rule.reason}.",
                    )
                )
    return violations


def check_env_access(path: Path, tree: ast.AST) -> list[Violation]:
    if path in ENV_ALLOWED:
        return []
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
            and node.attr in {"getenv", "environ"}
        ):
            violations.append(
                Violation(
                    "I11",
                    path,
                    node.lineno,
                    "Read configuration through app.core.config.Settings, not os.environ",
                )
            )
    return violations


def check_clock_usage(path: Path, tree: ast.AST) -> list[Violation]:
    if path in CLOCK_ALLOWED:
        return []
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"now", "utcnow"}:
            continue
        owner = node.func.value
        owner_name = (
            owner.id
            if isinstance(owner, ast.Name)
            else owner.attr
            if isinstance(owner, ast.Attribute)
            else ""
        )
        if owner_name in {"datetime", "date"}:
            violations.append(
                Violation(
                    "ADR-009",
                    path,
                    node.lineno,
                    "Use an injected Clock instead of datetime.now()/utcnow()",
                )
            )
    return violations


def check_mock_isolation(path: Path, tree: ast.AST) -> list[Violation]:
    """I9: production code must not import mock providers."""
    rel = path.relative_to(APP_ROOT)
    if rel.parts[:2] == ("providers", "mock"):
        return []
    violations = []
    for module, lineno in _imported_modules(tree):
        if "providers.mock" in module:
            violations.append(
                Violation(
                    "I9",
                    path,
                    lineno,
                    "Mock providers may only be imported by tests (no fake data in production)",
                )
            )
    return violations


CHECKS = (check_imports, check_env_access, check_clock_usage, check_mock_isolation)


def main() -> int:
    if not APP_ROOT.exists():
        print(f"error: {APP_ROOT} not found", file=sys.stderr)
        return 2

    violations: list[Violation] = []
    files = _iter_python_files(APP_ROOT)
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:  # pragma: no cover
            violations.append(Violation("SYNTAX", path, exc.lineno or 0, str(exc.msg)))
            continue
        for check in CHECKS:
            violations.extend(check(path, tree))

    if violations:
        print(f"Architecture check FAILED — {len(violations)} violation(s):\n")
        for violation in violations:
            print(violation.render())
        print("\nSee docs/00-overview.md §1 for the rationale behind each rule.")
        return 1

    print(f"Architecture check passed ({len(files)} files, {len(IMPORT_RULES)} import rules).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
